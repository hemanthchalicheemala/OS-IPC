"""Mutex demo: same increments as race_demo but protected by Lock.

A mutex (Lock) serializes the critical section so the final count matches
the expected total. Acquire/release events are streamed for the UI.
"""

from __future__ import annotations

import time
from multiprocessing import Lock, Process, Value


def _safe_increment(counter: Value, lock: Lock, increments: int, worker_id: int, event_queue) -> None:
    for i in range(increments):
        if event_queue is not None and i % max(1, increments // 5) == 0:
            event_queue.put(
                {
                    "type": "lock_acquire",
                    "process": f"mutex-{worker_id}",
                    "timestamp": time.time(),
                    "data": {"iteration": i},
                }
            )
        with lock:
            current = counter.value
            time.sleep(0)
            counter.value = current + 1
        if event_queue is not None and i % max(1, increments // 5) == 0:
            event_queue.put(
                {
                    "type": "lock_release",
                    "process": f"mutex-{worker_id}",
                    "timestamp": time.time(),
                    "data": {"iteration": i},
                }
            )


def run_mutex_demo(
    num_processes: int = 4,
    increments: int = 1000,
    event_queue=None,
    event_callback=None,
) -> dict:
    expected = num_processes * increments
    counter = Value("i", 0)
    lock = Lock()
    procs: list[Process] = []

    if event_callback:
        event_callback(
            {
                "type": "experiment_log",
                "data": {
                    "line": f"Mutex demo: {num_processes} processes × {increments} with Lock",
                },
            }
        )

    t0 = time.perf_counter()
    for i in range(num_processes):
        p = Process(
            target=_safe_increment,
            args=(counter, lock, increments, i, event_queue),
            name=f"mutex-{i}",
        )
        p.start()
        procs.append(p)

    for p in procs:
        p.join(timeout=60)
        if p.is_alive():
            p.terminate()
            p.join(timeout=2)

    # Drain child lock events if a queue was provided
    if event_queue is not None and event_callback is not None:
        try:
            while True:
                evt = event_queue.get_nowait()
                event_callback(evt)
        except Exception:
            pass

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    final = int(counter.value)
    result = {
        "experiment": "mutex_synchronization",
        "num_processes": num_processes,
        "increments_per_process": increments,
        "expected": expected,
        "final_count": final,
        "lost_updates": expected - final,
        "consistent": final == expected,
        "elapsed_ms": elapsed_ms,
        "explanation": (
            "With a mutex around the critical section, increments are serialized "
            "and the final count equals the expected total."
        ),
    }
    if event_callback:
        event_callback({"type": "experiment_result", "data": result})
    return result
