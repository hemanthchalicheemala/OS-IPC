"""Process registry — only PIDs spawned by this app may be managed."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessInfo:
    name: str
    pid: int | None = None
    status: str = "stopped"
    started_at: float | None = None
    role: str = "worker"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pid": self.pid,
            "status": self.status,
            "started_at": self.started_at,
            "role": self.role,
            "extra": self.extra,
        }


class ProcessRegistry:
    """Tracks managed process names and their live PIDs."""

    def __init__(self, names: tuple[str, ...]):
        self._entries: dict[str, ProcessInfo] = {}
        for n in names:
            role = "broker" if n == "broker" else ("ml" if n == "ml_analyzer" else "worker")
            self._entries[n.lower()] = ProcessInfo(name=n.lower(), role=role)

    def names(self) -> list[str]:
        return list(self._entries.keys())

    def is_managed(self, name: str) -> bool:
        return name.lower() in self._entries

    def get(self, name: str) -> ProcessInfo | None:
        return self._entries.get(name.lower())

    def mark_starting(self, name: str) -> None:
        info = self._entries[name.lower()]
        info.status = "starting"
        info.pid = None

    def mark_running(self, name: str, pid: int) -> None:
        info = self._entries[name.lower()]
        info.status = "running"
        info.pid = pid
        info.started_at = time.time()

    def mark_stopping(self, name: str) -> None:
        info = self._entries[name.lower()]
        info.status = "stopping"

    def mark_stopped(self, name: str) -> None:
        info = self._entries[name.lower()]
        info.status = "stopped"
        info.pid = None
        info.extra.pop("error", None)

    def mark_error(self, name: str, error: str) -> None:
        info = self._entries[name.lower()]
        info.status = "error"
        info.extra["error"] = error

    def list_all(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._entries.values()]

    def running_pids(self) -> dict[str, int]:
        return {n: e.pid for n, e in self._entries.items() if e.pid and e.status == "running"}
