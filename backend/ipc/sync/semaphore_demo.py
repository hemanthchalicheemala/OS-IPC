"""Semaphore demo: at most K processes in the critical section.

Semaphore(2) allows two concurrent holders; others wait. We emit ACCESS and
WAITING events so the UI can show contention live.
"""

from __future__ import annotations

import time
from multiprocessing import Process, Semaphore


def _worker(sem: Semaphore, worker_id: int, hold_seconds: float, event_queue) -> None:
    name = f"sem-{worker_id}"
    if event_queue is not None:
        event_queue.put(
            {
                "type": "semaphore_waiting",
                "process": name,
                "timestamp": time.time(),
                "data": {"state": "WAITING"},
            }
        )
    sem.acquire()
    try:
        if event_queue is not None:
            event_queue.put(
                {
                    "type": "semaphore_access",
                    "process": name,
                    "timestamp": time.time(),
                    "data": {"state": "ACCESS", "hold_seconds": hold_seconds},
                }
            )
        time.sleep(hold_seconds)
    finally:
        sem.release()
        if event_queue is not None:
            event_queue.put(
                {
                    "type": "semaphore_release",
                    "process": name,
                    "timestamp": time.time(),
                    "data": {"state": "RELEASED"},
                }
            )


def run_semaphore_demo(
    num_processes: int = 5,
    limit: int = 2,
    hold_seconds: float = 0.25,
    event_queue=None,
    event_callback=None,
) -> dict:
    sem = Semaphore(limit)
    procs: list[Process] = []

    if event_callback:
        event_callback(
            {
                "type": "experiment_log",
                "data": {
                    "line": f"Semaphore({limit}): {num_processes} workers, hold={hold_seconds}s",
                },
            }
        )

    t0 = time.perf_counter()
    for i in range(num_processes):
        p = Process(
            target=_worker,
            args=(sem, i, hold_seconds, event_queue),
            name=f"sem-{i}",
        )
        p.start()
        procs.append(p)

    deadline = time.time() + 30
    while event_queue is not None and event_callback is not None and time.time() < deadline:
        alive = any(p.is_alive() for p in procs)
        try:
            while True:
                evt = event_queue.get_nowait()
                event_callback(evt)
        except Exception:
            pass
        if not alive:
            break
        time.sleep(0.05)

    for p in procs:
        p.join(timeout=30)
        if p.is_alive():
            p.terminate()
            p.join(timeout=2)

    if event_queue is not None and event_callback is not None:
        try:
            while True:
                event_callback(event_queue.get_nowait())
        except Exception:
            pass

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    result = {
        "experiment": "semaphore_synchronization",
        "num_processes": num_processes,
        "limit": limit,
        "hold_seconds": hold_seconds,
        "elapsed_ms": elapsed_ms,
        "explanation": (
            f"Semaphore({limit}) caps concurrent critical-section holders; "
            "extra processes block (WAITING) until a permit is released."
        ),
    }
    if event_callback:
        event_callback({"type": "experiment_result", "data": result})
    return result
