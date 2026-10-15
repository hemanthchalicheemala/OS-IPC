"""Pipe-based IPC helpers using multiprocessing.Connection.

Pipes are duplex byte streams between two endpoints. On Windows they are
implemented with named-pipe-like OS primitives under multiprocessing.
"""

from __future__ import annotations

import json
import time
from multiprocessing.connection import Connection
from typing import Any


def pipe_send(conn: Connection, message: dict[str, Any]) -> dict[str, Any]:
    """Send a JSON-serializable message over a Pipe; attach latency fields."""
    msg = dict(message)
    t0 = time.perf_counter()
    msg["t_send_start"] = t0
    conn.send(msg)
    t1 = time.perf_counter()
    msg["t_send_end"] = t1
    msg["latency_ms"] = (t1 - t0) * 1000.0
    return msg


def pipe_recv(conn: Connection, timeout: float | None = 0.05) -> dict[str, Any] | None:
    """Non-blocking-ish receive; returns None on timeout/empty."""
    if timeout is None:
        if conn.poll():
            return conn.recv()
        return None
    if conn.poll(timeout):
        return conn.recv()
    return None


def pipe_send_raw(conn: Connection, obj: Any) -> None:
    conn.send(obj)


def encode_payload(message: dict[str, Any]) -> bytes:
    return json.dumps(message, separators=(",", ":")).encode("utf-8")
