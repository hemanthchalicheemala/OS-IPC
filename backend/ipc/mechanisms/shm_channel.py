"""SharedMemory IPC helpers (Windows-safe).

SharedMemory alone has no wait/wake, so we pair it with a Lock for mutual
exclusion and a notify Queue so the peer can block until data is ready.
"""

from __future__ import annotations

import json
import struct
import time
from multiprocessing import Lock
from multiprocessing.queues import Queue
from multiprocessing.shared_memory import SharedMemory
from queue import Empty
from typing import Any

# Layout: [4-byte little-endian length][UTF-8 JSON payload...]
HEADER_SIZE = 4
DEFAULT_SHM_SIZE = 65536


def create_shm(name: str | None = None, size: int = DEFAULT_SHM_SIZE) -> SharedMemory:
    return SharedMemory(create=True, size=size, name=name)


def attach_shm(name: str) -> SharedMemory:
    return SharedMemory(name=name, create=False)


def shm_write(
    shm: SharedMemory,
    lock: Lock,
    notify: Queue,
    message: dict[str, Any],
    notify_target: str,
) -> dict[str, Any]:
    """Write message bytes into SharedMemory under Lock, then notify waiter."""
    msg = dict(message)
    payload = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    if HEADER_SIZE + len(payload) > len(shm.buf):
        raise ValueError(f"Message too large for SharedMemory ({len(payload)} bytes)")

    t0 = time.perf_counter()
    msg["t_send_start"] = t0
    with lock:
        shm.buf[0:HEADER_SIZE] = struct.pack("<I", len(payload))
        shm.buf[HEADER_SIZE : HEADER_SIZE + len(payload)] = payload
    notify.put({"target": notify_target, "size": len(payload), "id": msg.get("id")})
    t1 = time.perf_counter()
    msg["t_send_end"] = t1
    msg["latency_ms"] = (t1 - t0) * 1000.0
    return msg


def shm_read(shm: SharedMemory, lock: Lock) -> dict[str, Any] | None:
    with lock:
        length = struct.unpack("<I", bytes(shm.buf[0:HEADER_SIZE]))[0]
        if length == 0 or HEADER_SIZE + length > len(shm.buf):
            return None
        raw = bytes(shm.buf[HEADER_SIZE : HEADER_SIZE + length])
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def shm_wait_notify(notify: Queue, timeout: float = 0.05) -> dict[str, Any] | None:
    try:
        return notify.get(timeout=timeout)
    except Empty:
        return None


def unlink_shm(shm: SharedMemory | None) -> None:
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
