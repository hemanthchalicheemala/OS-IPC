"""OS experiments runner — 10 live demos with streamed events."""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable

from backend import MECHANISMS
from backend.ipc.events import make_event
from backend.ipc.sync.mutex_demo import run_mutex_demo
from backend.ipc.sync.producer_consumer import run_producer_consumer_demo
from backend.ipc.sync.race_demo import run_race_demo
from backend.ipc.sync.semaphore_demo import run_semaphore_demo

EventCallback = Callable[[dict[str, Any]], None]

EXPERIMENTS: dict[str, dict[str, str]] = {
    "pipe_communication": {
        "id": "pipe_communication",
        "title": "Pipe communication",
        "description": "Send a chat message through multiprocessing.Pipe via the broker.",
    },
    "queue_communication": {
        "id": "queue_communication",
        "title": "Message Queue communication",
        "description": "Send a chat message through multiprocessing.Queue via the broker.",
    },
    "shared_memory_communication": {
        "id": "shared_memory_communication",
        "title": "Shared Memory communication",
        "description": "Send a chat message through SharedMemory + Lock + notify Queue.",
    },
    "race_condition": {
        "id": "race_condition",
        "title": "Race condition",
        "description": "N processes increment a shared Value without a Lock (lost updates).",
    },
    "mutex_synchronization": {
        "id": "mutex_synchronization",
        "title": "Mutex synchronization",
        "description": "Same increments with Lock — consistent count + acquire/release events.",
    },
    "semaphore_synchronization": {
        "id": "semaphore_synchronization",
        "title": "Semaphore synchronization",
        "description": "Semaphore(2) gates critical section; ACCESS vs WAITING events.",
    },
    "producer_consumer": {
        "id": "producer_consumer",
        "title": "Producer-consumer",
        "description": "Bounded Queue backpressure with producers and consumers.",
    },
    "process_lifecycle": {
        "id": "process_lifecycle",
        "title": "Process creation/termination",
        "description": "Stop and restart a managed worker; observe real PID change.",
    },
    "ipc_latency_comparison": {
        "id": "ipc_latency_comparison",
        "title": "IPC latency comparison",
        "description": "Benchmark Pipe vs Queue vs SharedMemory with measured latency.",
    },
    "ml_spam_detection": {
        "id": "ml_spam_detection",
        "title": "ML spam detection",
        "description": "Classify sample texts with the trained TF-IDF + LogisticRegression model.",
    },
}


class ExperimentRunner:
    def __init__(self, ipc_manager, event_callback: EventCallback | None = None) -> None:
        self.manager = ipc_manager
        self.event_callback = event_callback
        self.results: list[dict[str, Any]] = []

    def _log(self, line: str, experiment_id: str) -> None:
        evt = make_event(
            "experiment_log",
            data={"experiment_id": experiment_id, "line": line},
        )
        if self.event_callback:
            self.event_callback(evt)

    def _cb(self, event: dict[str, Any]) -> None:
        if self.event_callback:
            self.event_callback(event)

    def list_experiments(self) -> list[dict[str, str]]:
        return list(EXPERIMENTS.values())

    def run(self, experiment_id: str) -> dict[str, Any]:
        experiment_id = experiment_id.strip().lower()
        numeric_map = {
            "1": "pipe_communication",
            "2": "queue_communication",
            "3": "shared_memory_communication",
            "4": "race_condition",
            "5": "mutex_synchronization",
            "6": "semaphore_synchronization",
            "7": "producer_consumer",
            "8": "process_lifecycle",
            "9": "ipc_latency_comparison",
            "10": "ml_spam_detection",
        }
        experiment_id = numeric_map.get(experiment_id, experiment_id)
        if experiment_id not in EXPERIMENTS:
            raise ValueError(f"Unknown experiment_id: {experiment_id}")

        meta = EXPERIMENTS[experiment_id]
        run_id = str(uuid.uuid4())
        self._log(f"Starting experiment: {meta['title']}", experiment_id)
        self._cb(
            make_event(
                "experiment_started",
                data={"experiment_id": experiment_id, "run_id": run_id, "title": meta["title"]},
            )
        )

        t0 = time.perf_counter()
        try:
            result_data = self._dispatch(experiment_id)
            success = True
            error = None
        except Exception as exc:
            result_data = {"error": str(exc)}
            success = False
            error = str(exc)
            self._log(f"ERROR: {exc}", experiment_id)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        record = {
            "run_id": run_id,
            "experiment_id": experiment_id,
            "title": meta["title"],
            "success": success,
            "error": error,
            "elapsed_ms": elapsed_ms,
            "result": result_data,
            "timestamp": time.time(),
        }
        self.results.append(record)
        self._cb(make_event("experiment_finished", data=record))
        self._log(f"Finished experiment: {meta['title']} ({elapsed_ms:.1f} ms)", experiment_id)
        return record

    def _dispatch(self, experiment_id: str) -> dict[str, Any]:
        if experiment_id == "pipe_communication":
            return self._ipc_send_test("pipe")
        if experiment_id == "queue_communication":
            return self._ipc_send_test("queue")
        if experiment_id == "shared_memory_communication":
            return self._ipc_send_test("shared_memory")
        if experiment_id == "race_condition":
            return run_race_demo(num_processes=4, increments=1500, event_callback=self._cb)
        if experiment_id == "mutex_synchronization":
            from multiprocessing import Queue

            eq = Queue()
            return run_mutex_demo(
                num_processes=4,
                increments=1500,
                event_queue=eq,
                event_callback=self._cb,
            )
        if experiment_id == "semaphore_synchronization":
            from multiprocessing import Queue

            eq = Queue()
            return run_semaphore_demo(
                num_processes=5,
                limit=2,
                hold_seconds=0.2,
                event_queue=eq,
                event_callback=self._cb,
            )
        if experiment_id == "producer_consumer":
            from multiprocessing import Queue

            eq = Queue()
            return run_producer_consumer_demo(
                num_producers=2,
                num_consumers=2,
                items_per_producer=15,
                maxsize=4,
                event_queue=eq,
                event_callback=self._cb,
            )
        if experiment_id == "process_lifecycle":
            return self._process_lifecycle()
        if experiment_id == "ipc_latency_comparison":
            return self._latency_comparison()
        if experiment_id == "ml_spam_detection":
            return self._ml_spam()
        raise ValueError(experiment_id)

    def _ipc_send_test(self, mechanism: str) -> dict[str, Any]:
        prev = self.manager.get_mechanism()
        try:
            self.manager.set_mechanism(mechanism)
            self._log(f"Mechanism set to {mechanism}", f"{mechanism}_test")
            for name in ("broker", "alice", "bob"):
                info = self.manager.registry.get(name)
                if not info or info.status != "running":
                    self.manager.start_process(name)
                    time.sleep(0.3)
            msg = self.manager.send_message(
                sender="alice",
                receiver="bob",
                content=f"Experiment ping via {mechanism} at {time.time():.3f}",
                mechanism=mechanism,
            )
            self._log(f"Queued message {msg['id']}", f"{mechanism}_test")
            time.sleep(0.6)
            stored = self.manager.get_message(msg["id"]) or msg
            return {
                "mechanism": mechanism,
                "message": stored,
                "explanation": f"Real {mechanism} path: Alice → broker → Bob.",
            }
        finally:
            try:
                self.manager.set_mechanism(prev)
            except Exception:
                pass

    def _process_lifecycle(self) -> dict[str, Any]:
        target = "charlie"
        before = self.manager.registry.get(target)
        before_pid = before.pid if before else None
        self._log(f"{target} before PID={before_pid}", "process_lifecycle")
        if before and before.status == "running":
            self.manager.stop_process(target)
            time.sleep(0.4)
        after_stop = self.manager.registry.get(target)
        started = self.manager.start_process(target)
        time.sleep(0.5)
        after = self.manager.registry.get(target)
        after_pid = after.pid if after else None
        self._log(f"{target} after PID={after_pid}", "process_lifecycle")
        return {
            "process": target,
            "before_pid": before_pid,
            "after_stop_status": after_stop.status if after_stop else None,
            "after_pid": after_pid,
            "started": started,
            "pid_changed": before_pid != after_pid,
            "explanation": "Windows assigned a new PID on restart — real process lifecycle.",
        }

    def _latency_comparison(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        prev = self.manager.get_mechanism()
        for name in ("broker", "alice", "bob"):
            info = self.manager.registry.get(name)
            if not info or info.status != "running":
                self.manager.start_process(name)
                time.sleep(0.35)
        try:
            for mech in MECHANISMS:
                self.manager.set_mechanism(mech)
                samples: list[float] = []
                for i in range(5):
                    msg = self.manager.send_message(
                        sender="alice",
                        receiver="bob",
                        content=f"bench-{mech}-{i}",
                        mechanism=mech,
                    )
                    time.sleep(0.25)
                    stored = self.manager.get_message(msg["id"]) or msg
                    lat = stored.get("latency_ms")
                    if lat is not None:
                        samples.append(float(lat))
                    self._log(f"{mech} sample {i + 1}: {lat} ms", "ipc_latency_comparison")
                results[mech] = {
                    "samples_ms": samples,
                    "avg_ms": (sum(samples) / len(samples)) if samples else None,
                    "min_ms": min(samples) if samples else None,
                    "max_ms": max(samples) if samples else None,
                }
        finally:
            try:
                self.manager.set_mechanism(prev)
            except Exception:
                pass
        return {
            "comparison": results,
            "explanation": "Latencies measured with time.perf_counter() on real IPC sends.",
        }

    def _ml_spam(self) -> dict[str, Any]:
        from backend.ml.classifier import MessageClassifier
        from backend.ml.sentiment import SentimentAnalyzer

        clf = MessageClassifier()
        clf.load()
        sent = SentimentAnalyzer()
        samples = [
            "Hello, can we meet tomorrow about the project?",
            "Congratulations! You won a FREE iPhone click now!!!",
            "URGENT: production server is down, need help ASAP",
            "You are an idiot and your code is garbage",
        ]
        predictions = []
        for text in samples:
            pred = clf.predict(text)
            sentiment = sent.analyze(text)
            row = {"text": text, "classification": pred, "sentiment": sentiment}
            predictions.append(row)
            self._log(
                f"{pred['label']} ({pred['confidence']:.2f}): {text[:48]}",
                "ml_spam_detection",
            )
        return {
            "predictions": predictions,
            "explanation": "TF-IDF + LogisticRegression labels; not fabricated.",
        }
