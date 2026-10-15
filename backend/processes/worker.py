"""Chat worker process target (Alice / Bob / Charlie).

Each worker is a real OS process. It receives control commands on a Queue and
exchanges chat payloads with the broker via Pipe, Queue, or SharedMemory.
"""

from __future__ import annotations

import os
import time
from typing import Any

from backend.ipc.events import make_event
from backend.ipc.mechanisms.pipe_channel import pipe_recv, pipe_send
from backend.ipc.mechanisms.queue_channel import queue_get, queue_put
from backend.ipc.mechanisms.shm_channel import attach_shm, shm_read, shm_wait_notify, shm_write

_CODE_TO_MECH = {0: "pipe", 1: "queue", 2: "shared_memory"}


def _read_mechanism(mechanism_value) -> str:
    try:
        return _CODE_TO_MECH.get(int(mechanism_value.value), "pipe")
    except Exception:
        return "pipe"


def _emit(event_queue, event: dict[str, Any]) -> None:
    try:
        event_queue.put(event)
    except Exception:
        pass


def worker_main(
    name: str,
    control_queue,
    event_queue,
    mechanism_value,
    pipe_conn,
    to_broker_queue,
    inbox_queue,
    shm_name: str,
    shm_lock,
    shm_notify_broker,
    shm_notify_self,
) -> None:
    """Entry point for a chat worker child process (spawn-safe)."""
    name = name.lower()
    shm = None
    try:
        shm = attach_shm(shm_name)
    except Exception as exc:
        _emit(
            event_queue,
            make_event("error", process=name, data={"error": f"SHM attach failed: {exc}"}),
        )

    _emit(
        event_queue,
        make_event(
            "status",
            process=name,
            data={"status": "running", "pid": os.getpid()},
        ),
    )

    last_heartbeat = 0.0
    running = True

    while running:
        # Heartbeat ~1s
        now = time.time()
        if now - last_heartbeat >= 1.0:
            _emit(
                event_queue,
                make_event("heartbeat", process=name, data={"pid": os.getpid()}),
            )
            last_heartbeat = now

        # Control commands from IPCManager
        cmd = queue_get(control_queue, timeout=0.01)
        if cmd:
            action = (cmd.get("action") or "").lower()
            if action == "shutdown":
                running = False
                break
            if action == "send_message":
                _handle_send(
                    name=name,
                    cmd=cmd,
                    mechanism_value=mechanism_value,
                    pipe_conn=pipe_conn,
                    to_broker_queue=to_broker_queue,
                    shm=shm,
                    shm_lock=shm_lock,
                    shm_notify_broker=shm_notify_broker,
                    event_queue=event_queue,
                )

        mechanism = _read_mechanism(mechanism_value)

        # Receive path depends on active mechanism
        if mechanism == "pipe":
            msg = pipe_recv(pipe_conn, timeout=0.02)
            if msg and isinstance(msg, dict) and msg.get("type") != "control":
                _on_receive(name, msg, event_queue)
        elif mechanism == "queue":
            msg = queue_get(inbox_queue, timeout=0.02)
            if msg:
                _on_receive(name, msg, event_queue)
        elif mechanism == "shared_memory":
            note = shm_wait_notify(shm_notify_self, timeout=0.02)
            if note and shm is not None:
                msg = shm_read(shm, shm_lock)
                if msg and msg.get("receiver", "").lower() == name:
                    _on_receive(name, msg, event_queue)

    _emit(event_queue, make_event("status", process=name, data={"status": "stopped", "pid": os.getpid()}))
    if shm is not None:
        try:
            shm.close()
        except Exception:
            pass


def _handle_send(
    *,
    name: str,
    cmd: dict[str, Any],
    mechanism_value,
    pipe_conn,
    to_broker_queue,
    shm,
    shm_lock,
    shm_notify_broker,
    event_queue,
) -> None:
    message = cmd.get("message") or {}
    mechanism = message.get("mechanism") or _read_mechanism(mechanism_value)
    message = dict(message)
    message["mechanism"] = mechanism
    message["sender"] = name

    try:
        if mechanism == "pipe":
            sent = pipe_send(pipe_conn, message)
        elif mechanism == "queue":
            sent = queue_put(to_broker_queue, message)
        elif mechanism == "shared_memory":
            if shm is None:
                raise RuntimeError("SharedMemory not attached")
            sent = shm_write(shm, shm_lock, shm_notify_broker, message, notify_target="broker")
        else:
            raise ValueError(f"Unknown mechanism: {mechanism}")

        _emit(
            event_queue,
            make_event(
                "message_sent",
                process=name,
                message_id=sent.get("id"),
                data={
                    "message": sent,
                    "latency_ms": sent.get("latency_ms"),
                    "mechanism": mechanism,
                },
            ),
        )
    except Exception as exc:
        _emit(
            event_queue,
            make_event(
                "message_failed",
                process=name,
                message_id=message.get("id"),
                data={"error": str(exc), "message": message},
            ),
        )


def _on_receive(name: str, msg: dict[str, Any], event_queue) -> None:
    if msg.get("receiver", "").lower() != name:
        return
    _emit(
        event_queue,
        make_event(
            "message_received",
            process=name,
            message_id=msg.get("id"),
            data={"message": msg, "mechanism": msg.get("mechanism")},
        ),
    )


def ml_analyzer_main(control_queue, event_queue, ml_inbox, model_path: str) -> None:
    """Optional ML worker: classify texts pushed to ml_inbox."""
    import os

    from backend.ml.classifier import MessageClassifier
    from backend.ml.sentiment import SentimentAnalyzer

    clf = None
    sent = SentimentAnalyzer()
    try:
        clf = MessageClassifier(model_path)
        clf.load()
    except Exception as exc:
        _emit(event_queue, make_event("error", process="ml_analyzer", data={"error": str(exc)}))

    _emit(
        event_queue,
        make_event("status", process="ml_analyzer", data={"status": "running", "pid": os.getpid()}),
    )

    last_heartbeat = 0.0
    running = True
    while running:
        now = time.time()
        if now - last_heartbeat >= 1.0:
            _emit(event_queue, make_event("heartbeat", process="ml_analyzer", data={"pid": os.getpid()}))
            last_heartbeat = now

        cmd = queue_get(control_queue, timeout=0.01)
        if cmd and (cmd.get("action") or "").lower() == "shutdown":
            running = False
            break

        job = queue_get(ml_inbox, timeout=0.05)
        if not job:
            continue
        text = job.get("text", "")
        message_id = job.get("message_id")
        try:
            label_info = clf.predict(text) if clf else {"label": "unknown", "confidence": 0.0}
            sentiment = sent.analyze(text)
            _emit(
                event_queue,
                make_event(
                    "ml_prediction",
                    process="ml_analyzer",
                    message_id=message_id,
                    data={"text": text, "classification": label_info, "sentiment": sentiment},
                ),
            )
        except Exception as exc:
            _emit(
                event_queue,
                make_event("error", process="ml_analyzer", data={"error": str(exc), "message_id": message_id}),
            )

    _emit(event_queue, make_event("status", process="ml_analyzer", data={"status": "stopped"}))
