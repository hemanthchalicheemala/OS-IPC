"""Race-condition demo: concurrent increments without a Lock.

Without mutual exclusion, read-modify-write on a shared Value is not atomic,
so the final count is often less than N * increments (lost updates).
"""

from __future__ import annotations

import time
from multiprocessing import Process, Value


def _racer(counter: Value, increments: int) -> None:
    for _ in range(increments):
        # Intentionally unsafe: no lock around read-modify-write.
        current = counter.value
        time.sleep(0)  # yield to encourage interleaving on Windows
        counter.value = current + 1


def run_race_demo(
    num_processes: int = 4,
    increments: int = 1000,
    event_callback=None,
) -> dict:
    expected = num_processes * increments
    counter = Value("i", 0)
    procs: list[Process] = []

    if event_callback:
        event_callback(
            {
                "type": "experiment_log",
                "data": {
                    "line": f"Race demo: {num_processes} processes × {increments} increments (NO lock)",
                },
            }
        )

    t0 = time.perf_counter()
    for i in range(num_processes):
        p = Process(target=_racer, args=(counter, increments), name=f"race-{i}")
        p.start()
        procs.append(p)
        if event_callback:
            event_callback(
                {
                    "type": "process_spawned",
                    "process": p.name,
                    "data": {"pid": p.pid, "demo": "race"},
                }
            )

    for p in procs:
        p.join(timeout=30)
        if p.is_alive():
            p.terminate()
            p.join(timeout=2)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    final = int(counter.value)
    result = {
        "experiment": "race_condition",
        "num_processes": num_processes,
        "increments_per_process": increments,
        "expected": expected,
        "final_count": final,
        "lost_updates": expected - final,
        "consistent": final == expected,
        "elapsed_ms": elapsed_ms,
        "explanation": (
            "Without a mutex, concurrent increments race on the shared counter; "
            "lost updates yield a final value below the expected total."
        ),
    }
    if event_callback:
        event_callback({"type": "experiment_result", "data": result})
    return result
