"""Typed IPC / process event helpers for WebSocket broadcasting."""

from __future__ import annotations

import time
import uuid
from typing import Any


def make_event(
    event_type: str,
    *,
    process: str | None = None,
    data: dict[str, Any] | None = None,
    message_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "process": process,
        "message_id": message_id,
        "timestamp": time.time(),
        "data": data or {},
    }


def make_message_payload(
    *,
    sender: str,
    receiver: str,
    content: str,
    mechanism: str,
    message_id: str | None = None,
) -> dict[str, Any]:
    payload = content.encode("utf-8")
    return {
        "id": message_id or str(uuid.uuid4()),
        "sender": sender,
        "receiver": receiver,
        "content": content,
        "mechanism": mechanism,
        "timestamp": time.time(),
        "size_bytes": len(payload),
        "t_send_start": None,
        "t_send_end": None,
        "latency_ms": None,
    }
