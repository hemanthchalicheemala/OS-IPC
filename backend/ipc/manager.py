"""IPCManager — owns real child processes and IPC primitives (singleton)."""

from __future__ import annotations

import multiprocessing as mp
import threading
import time
import uuid
from typing import Any, Callable

from backend import MANAGED_PROCESSES, MECHANISMS, MODELS_DIR, WORKER_NAMES
from backend.ipc.broker import broker_main
from backend.ipc.events import make_event, make_message_payload
from backend.ipc.mechanisms.shm_channel import DEFAULT_SHM_SIZE, create_shm, unlink_shm
from backend.monitoring.metrics import MetricsAggregator
from backend.processes.cleanup import terminate_many, terminate_process
from backend.processes.registry import ProcessRegistry
from backend.processes.worker import ml_analyzer_main, worker_main

EventCallback = Callable[[dict[str, Any]], None]

_MECH_TO_CODE = {"pipe": 0, "queue": 1, "shared_memory": 2}
_CODE_TO_MECH = {v: k for k, v in _MECH_TO_CODE.items()}


class IPCManager:
    """Spawns broker + workers + ml_analyzer; switches IPC mechanisms live."""

    _instance: IPCManager | None = None

    def __init__(self) -> None:
        self.registry = ProcessRegistry(MANAGED_PROCESSES)
        self.metrics = MetricsAggregator()
        self._callbacks: list[EventCallback] = []
        self._lock = threading.RLock()
        self._started = False

        self._ctx = mp.get_context("spawn")
        self._event_queue = self._ctx.Queue()
        # Integer code is more reliable across Windows spawn than Array('c').
        self._mechanism = self._ctx.Value("i", _MECH_TO_CODE["pipe"])

        self._control: dict[str, Any] = {}
        self._processes: dict[str, mp.Process] = {}

        # Pipe ends: parent keeps nothing; broker gets broker ends, workers get worker ends
        self._worker_pipe_broker_ends: dict[str, Any] = {}
        self._worker_pipe_worker_ends: dict[str, Any] = {}

        self._to_broker_queue = self._ctx.Queue()
        self._worker_inboxes: dict[str, Any] = {}
        self._ml_inbox = self._ctx.Queue()

        self._shm = None
        self._shm_name = f"ipc_chat_shm_{uuid.uuid4().hex[:12]}"
        self._shm_lock = self._ctx.Lock()
        self._shm_notify_broker = self._ctx.Queue()
        self._worker_shm_notifies: dict[str, Any] = {}

        self._poll_thread: threading.Thread | None = None
        self._stop_poll = threading.Event()
        self._recent_messages: list[dict[str, Any]] = []
        self._message_index: dict[str, dict[str, Any]] = {}

    @classmethod
    def instance(cls) -> IPCManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance is not None:
            try:
                cls._instance.shutdown()
            except Exception:
                pass
        cls._instance = None

    def add_callback(self, cb: EventCallback) -> None:
        with self._lock:
            if cb not in self._callbacks:
                self._callbacks.append(cb)

    def remove_callback(self, cb: EventCallback) -> None:
        with self._lock:
            if cb in self._callbacks:
                self._callbacks.remove(cb)

    def _emit(self, event: dict[str, Any]) -> None:
        self._ingest_event(event)
        with self._lock:
            callbacks = list(self._callbacks)
        for cb in callbacks:
            try:
                cb(event)
            except Exception:
                pass

    def get_mechanism(self) -> str:
        return _CODE_TO_MECH.get(int(self._mechanism.value), "pipe")

    def set_mechanism(self, mechanism: str) -> str:
        mechanism = mechanism.lower().strip()
        if mechanism not in MECHANISMS:
            raise ValueError(f"mechanism must be one of {MECHANISMS}")
        with self._lock:
            self._mechanism.value = _MECH_TO_CODE[mechanism]
        self._emit(make_event("mechanism_changed", data={"mechanism": mechanism}))
        return mechanism

    def start_all(self) -> None:
        with self._lock:
            if self._started:
                return
            self._create_ipc_resources()
            for name in MANAGED_PROCESSES:
                self._spawn_one(name)
            self._started = True
            self._stop_poll.clear()
            self._poll_thread = threading.Thread(target=self._poll_events, name="ipc-event-poll", daemon=True)
            self._poll_thread.start()
        self._emit(make_event("manager_started", data={"processes": list(MANAGED_PROCESSES)}))

    def _create_ipc_resources(self) -> None:
        for name in WORKER_NAMES:
            broker_end, worker_end = self._ctx.Pipe(duplex=True)
            self._worker_pipe_broker_ends[name] = broker_end
            self._worker_pipe_worker_ends[name] = worker_end
            self._worker_inboxes[name] = self._ctx.Queue()
            self._worker_shm_notifies[name] = self._ctx.Queue()
            self._control[name] = self._ctx.Queue()

        self._control["broker"] = self._ctx.Queue()
        self._control["ml_analyzer"] = self._ctx.Queue()

        if self._shm is None:
            self._shm = create_shm(name=self._shm_name, size=DEFAULT_SHM_SIZE)

    def _spawn_one(self, name: str) -> None:
        name = name.lower()
        if name not in MANAGED_PROCESSES:
            raise ValueError(f"Not a managed process: {name}")
        existing = self._processes.get(name)
        if existing is not None and existing.is_alive():
            return

        self.registry.mark_starting(name)
        model_path = str(MODELS_DIR / "message_clf.joblib")

        if name == "broker":
            proc = self._ctx.Process(
                target=broker_main,
                name="broker",
                args=(
                    self._control["broker"],
                    self._event_queue,
                    self._mechanism,
                    self._worker_pipe_broker_ends,
                    self._to_broker_queue,
                    self._worker_inboxes,
                    self._shm_name,
                    self._shm_lock,
                    self._shm_notify_broker,
                    self._worker_shm_notifies,
                    self._ml_inbox,
                ),
            )
        elif name == "ml_analyzer":
            proc = self._ctx.Process(
                target=ml_analyzer_main,
                name="ml_analyzer",
                args=(
                    self._control["ml_analyzer"],
                    self._event_queue,
                    self._ml_inbox,
                    model_path,
                ),
            )
        else:
            proc = self._ctx.Process(
                target=worker_main,
                name=name,
                args=(
                    name,
                    self._control[name],
                    self._event_queue,
                    self._mechanism,
                    self._worker_pipe_worker_ends[name],
                    self._to_broker_queue,
                    self._worker_inboxes[name],
                    self._shm_name,
                    self._shm_lock,
                    self._shm_notify_broker,
                    self._worker_shm_notifies[name],
                ),
            )

        proc.start()
        self._processes[name] = proc
        if proc.pid:
            self.registry.mark_running(name, proc.pid)
        self._emit(
            make_event(
                "process_started",
                process=name,
                data={"pid": proc.pid, "status": "running"},
            )
        )

    def stop_process(self, name: str) -> None:
        name = name.lower()
        if not self.registry.is_managed(name):
            raise ValueError(f"Refusing to manage unknown process: {name}")
        with self._lock:
            self.registry.mark_stopping(name)
            ctrl = self._control.get(name)
            if ctrl is not None:
                try:
                    ctrl.put({"action": "shutdown"})
                except Exception:
                    pass
            proc = self._processes.get(name)
            terminate_process(proc, grace_seconds=2.0)
            self._processes[name] = proc  # type: ignore
            self.registry.mark_stopped(name)
        self._emit(make_event("process_stopped", process=name, data={"status": "stopped"}))

    def start_process(self, name: str) -> dict[str, Any]:
        name = name.lower()
        if not self.registry.is_managed(name):
            raise ValueError(f"Refusing to manage unknown process: {name}")
        with self._lock:
            if not self._started:
                self._create_ipc_resources()
                self._started = True
                if self._poll_thread is None or not self._poll_thread.is_alive():
                    self._stop_poll.clear()
                    self._poll_thread = threading.Thread(
                        target=self._poll_events, name="ipc-event-poll", daemon=True
                    )
                    self._poll_thread.start()
            # Ensure control queue exists for late starts
            if name not in self._control:
                self._control[name] = self._ctx.Queue()
            if name in WORKER_NAMES:
                if name not in self._worker_pipe_worker_ends:
                    broker_end, worker_end = self._ctx.Pipe(duplex=True)
                    self._worker_pipe_broker_ends[name] = broker_end
                    self._worker_pipe_worker_ends[name] = worker_end
                    self._worker_inboxes[name] = self._ctx.Queue()
                    self._worker_shm_notifies[name] = self._ctx.Queue()
                # Restarting a worker while broker holds old pipe end is unsafe;
                # require broker restart for new pipe pair — recreate pair and note broker must be restarted.
            self._spawn_one(name)
        info = self.registry.get(name)
        return info.to_dict() if info else {"name": name}

    def restart_process(self, name: str) -> dict[str, Any]:
        """Restart a managed process.

        Worker pipe ends are owned by the broker process args. After recreating
        a worker's Pipe pair we must also restart the broker so it holds the
        new endpoints (Windows spawn cannot hot-swap pipe handles).
        """
        name = name.lower()
        if not self.registry.is_managed(name):
            raise ValueError(f"Refusing to manage unknown process: {name}")
        self.stop_process(name)
        time.sleep(0.15)

        if name in WORKER_NAMES:
            with self._lock:
                broker_end, worker_end = self._ctx.Pipe(duplex=True)
                self._worker_pipe_broker_ends[name] = broker_end
                self._worker_pipe_worker_ends[name] = worker_end
                self._worker_inboxes[name] = self._ctx.Queue()
                self._worker_shm_notifies[name] = self._ctx.Queue()
                self._control[name] = self._ctx.Queue()
            broker = self.registry.get("broker")
            if broker and broker.status == "running":
                self.stop_process("broker")
                time.sleep(0.1)
                self.start_process("broker")
                time.sleep(0.2)

        return self.start_process(name)

    def send_message(
        self,
        sender: str,
        receiver: str,
        content: str,
        mechanism: str | None = None,
    ) -> dict[str, Any]:
        sender = sender.lower().strip()
        receiver = receiver.lower().strip()
        if sender not in WORKER_NAMES:
            raise ValueError(f"sender must be one of {WORKER_NAMES}")
        if receiver not in WORKER_NAMES:
            raise ValueError(f"receiver must be one of {WORKER_NAMES}")
        if sender == receiver:
            raise ValueError("sender and receiver must differ")
        if not content or not str(content).strip():
            raise ValueError("content must be non-empty")
        if len(content) > 8000:
            raise ValueError("content too large (max 8000 chars)")

        mech = (mechanism or self.get_mechanism()).lower()
        if mech not in MECHANISMS:
            raise ValueError(f"mechanism must be one of {MECHANISMS}")

        sender_info = self.registry.get(sender)
        if not sender_info or sender_info.status != "running":
            raise RuntimeError(f"Sender process '{sender}' is not running")
        receiver_info = self.registry.get(receiver)
        if not receiver_info or receiver_info.status != "running":
            raise RuntimeError(f"Receiver process '{receiver}' is not running")
        broker_info = self.registry.get("broker")
        if not broker_info or broker_info.status != "running":
            raise RuntimeError("Broker process is not running")

        payload = make_message_payload(
            sender=sender,
            receiver=receiver,
            content=str(content),
            mechanism=mech,
        )
        with self._lock:
            stored = dict(payload)
            self._message_index[payload["id"]] = stored
            self._recent_messages.append(stored)
            if len(self._recent_messages) > 500:
                self._recent_messages = self._recent_messages[-500:]

        self._control[sender].put({"action": "send_message", "message": payload})
        self._emit(
            make_event(
                "message_queued",
                process=sender,
                message_id=payload["id"],
                data={"message": payload},
            )
        )
        return payload

    def list_messages(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._recent_messages)

    def get_message(self, message_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._message_index.get(message_id)

    def status(self) -> dict[str, Any]:
        return {
            "mechanism": self.get_mechanism(),
            "started": self._started,
            "processes": self.registry.list_all(),
            "shm_name": self._shm_name if self._shm else None,
        }

    def _poll_events(self) -> None:
        while not self._stop_poll.is_set():
            try:
                event = self._event_queue.get(timeout=0.2)
            except Exception:
                continue
            if event:
                self._emit(event)

    def _ingest_event(self, event: dict[str, Any]) -> None:
        et = event.get("type")
        data = event.get("data") or {}
        if et == "message_sent":
            msg = data.get("message") or {}
            latency = data.get("latency_ms") or msg.get("latency_ms")
            mech = data.get("mechanism") or msg.get("mechanism") or self.get_mechanism()
            self.metrics.record_send(mech, latency_ms=latency, success=True)
            mid = msg.get("id") or event.get("message_id")
            if mid and mid in self._message_index:
                self._message_index[mid].update(msg)
        elif et == "message_failed":
            msg = data.get("message") or {}
            mech = msg.get("mechanism") or self.get_mechanism()
            self.metrics.record_send(mech, latency_ms=None, success=False)
        elif et == "message_received":
            msg = data.get("message") or {}
            mid = msg.get("id") or event.get("message_id")
            if mid and mid in self._message_index:
                self._message_index[mid]["delivered"] = True
                self._message_index[mid]["received_at"] = event.get("timestamp")

    def shutdown(self) -> None:
        self._stop_poll.set()
        with self._lock:
            for name in list(self._control.keys()):
                try:
                    self._control[name].put({"action": "shutdown"})
                except Exception:
                    pass
            terminate_many(self._processes.values(), grace_seconds=2.5)
            self._processes.clear()
            for name in MANAGED_PROCESSES:
                self.registry.mark_stopped(name)
            unlink_shm(self._shm)
            self._shm = None
            self._started = False
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=2.0)
        self._emit(make_event("manager_stopped", data={}))
