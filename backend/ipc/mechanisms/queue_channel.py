"""Queue-based IPC helpers using multiprocessing.Queue.

A Queue is a classic producer–consumer channel with internal locking.
"""

from __future__ import annotations

import time
from multiprocessing.queues import Queue
from queue import Empty
from typing import Any


def queue_put(q: Queue, message: dict[str, Any], block: bool = True, timeout: float | None = 1.0) -> dict[str, Any]:
    msg = dict(message)
    t0 = time.perf_counter()
    msg["t_send_start"] = t0
    q.put(msg, block=block, timeout=timeout)
    t1 = time.perf_counter()
    msg["t_send_end"] = t1
    msg["latency_ms"] = (t1 - t0) * 1000.0
    return msg


def queue_get(q: Queue, timeout: float = 0.05) -> dict[str, Any] | None:
    try:
        return q.get(timeout=timeout)
    except Empty:
        return None


def queue_put_nowait(q: Queue, obj: Any) -> bool:
    try:
        q.put_nowait(obj)
        return True
    except Exception:
        return False
