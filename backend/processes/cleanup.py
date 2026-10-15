"""Cleanup helpers for child processes and SharedMemory on Windows."""

from __future__ import annotations

import time
from multiprocessing import Process
from multiprocessing.shared_memory import SharedMemory
from typing import Iterable


def terminate_process(proc: Process | None, grace_seconds: float = 2.0) -> None:
    if proc is None:
        return
    if not proc.is_alive():
        try:
            proc.join(timeout=0.5)
        except Exception:
            pass
        return
    try:
        proc.terminate()
    except Exception:
        pass
    proc.join(timeout=grace_seconds)
    if proc.is_alive():
        try:
            proc.kill()
        except Exception:
            pass
        proc.join(timeout=1.0)


def terminate_many(procs: Iterable[Process | None], grace_seconds: float = 2.0) -> None:
    items = list(procs)
    for p in items:
        if p is None:
            continue
        if p.is_alive():
            try:
                p.terminate()
            except Exception:
                pass
    deadline = time.time() + grace_seconds
    for p in items:
        if p is None:
            continue
        remaining = max(0.1, deadline - time.time())
        p.join(timeout=remaining)
    for p in items:
        if p is None:
            continue
        if p.is_alive():
            try:
                p.kill()
            except Exception:
                pass
            p.join(timeout=1.0)


def close_unlink_shm(shm: SharedMemory | None) -> None:
    if shm is None:
        return
    try:
        shm.close()
    except Exception:
        pass
    try:
        shm.unlink()
    except Exception:
        pass
