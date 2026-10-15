"""Collect real per-PID CPU, memory, and thread counts via psutil."""

from __future__ import annotations

from typing import Any

import psutil


def collect_pid_stats(pid: int) -> dict[str, Any] | None:
    try:
        p = psutil.Process(pid)
        with p.oneshot():
            mem = p.memory_info()
            return {
                "pid": pid,
                "name": p.name(),
                "status": p.status(),
                "cpu_percent": p.cpu_percent(interval=None),
                "memory_rss": mem.rss,
                "memory_rss_mb": mem.rss / (1024 * 1024),
                "num_threads": p.num_threads(),
                "create_time": p.create_time(),
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def collect_managed_stats(name_to_pid: dict[str, int]) -> dict[str, Any]:
    processes: dict[str, Any] = {}
    for name, pid in name_to_pid.items():
        stats = collect_pid_stats(pid)
        if stats is not None:
            # Prime cpu_percent: first call often returns 0.0
            try:
                psutil.Process(pid).cpu_percent(interval=0.0)
            except Exception:
                pass
            processes[name] = stats
        else:
            processes[name] = {"pid": pid, "status": "not_found"}
    vm = psutil.virtual_memory()
    return {
        "processes": processes,
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "cpu_count": psutil.cpu_count(),
            "memory_total": vm.total,
            "memory_available": vm.available,
            "memory_percent": vm.percent,
        },
    }
