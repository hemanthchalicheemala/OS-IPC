"""Aggregate IPC latency and throughput metrics per mechanism."""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any


class MetricsAggregator:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latencies: dict[str, list[float]] = defaultdict(list)
        self._success: dict[str, int] = defaultdict(int)
        self._fail: dict[str, int] = defaultdict(int)
        self._bytes: dict[str, int] = defaultdict(int)
        self._timestamps: list[float] = []

    def record_send(
        self,
        mechanism: str,
        latency_ms: float | None,
        success: bool = True,
        size_bytes: int = 0,
    ) -> None:
        with self._lock:
            if success:
                self._success[mechanism] += 1
                if latency_ms is not None:
                    self._latencies[mechanism].append(float(latency_ms))
                    if len(self._latencies[mechanism]) > 1000:
                        self._latencies[mechanism] = self._latencies[mechanism][-1000:]
            else:
                self._fail[mechanism] += 1
            self._bytes[mechanism] += int(size_bytes or 0)
            now = time.time()
            self._timestamps.append(now)
            self._timestamps = [t for t in self._timestamps if now - t <= 10.0]

    def msgs_per_sec(self, window: float = 5.0) -> float:
        with self._lock:
            return self._msgs_per_sec_unlocked(window)

    def _msgs_per_sec_unlocked(self, window: float = 5.0) -> float:
        now = time.time()
        recent = [t for t in self._timestamps if now - t <= window]
        if window <= 0:
            return 0.0
        return len(recent) / window

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            per_mech: dict[str, Any] = {}
            keys = set(self._latencies) | set(self._success) | set(self._fail)
            for mech in keys:
                lats = list(self._latencies.get(mech, []))
                per_mech[mech] = {
                    "count_success": self._success.get(mech, 0),
                    "count_fail": self._fail.get(mech, 0),
                    "total_bytes": self._bytes.get(mech, 0),
                    "latency_ms": {
                        "min": min(lats) if lats else None,
                        "max": max(lats) if lats else None,
                        "avg": (sum(lats) / len(lats)) if lats else None,
                        "samples": len(lats),
                    },
                }
            return {
                "per_mechanism": per_mech,
                "msgs_per_sec": self._msgs_per_sec_unlocked(),
                "total_success": sum(self._success.values()),
                "total_fail": sum(self._fail.values()),
            }
