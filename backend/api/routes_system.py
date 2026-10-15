"""System stats and OS concepts (viva) routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.deps import get_ipc_manager
from backend.ipc.manager import IPCManager
from backend.ml.anomaly import AnomalyDetector
from backend.monitoring.psutil_collector import collect_managed_stats

router = APIRouter(tags=["system"])

_anomaly = AnomalyDetector()


OS_CONCEPTS = {
    "title": "Operating System Concepts — Intelligent IPC Chat",
    "concepts": [
        {
            "id": "process",
            "name": "Process",
            "summary": "An independent program in execution with its own address space and PID.",
            "in_project": "Alice, Bob, Charlie, broker, and ml_analyzer are real multiprocessing.Process instances.",
        },
        {
            "id": "ipc",
            "name": "Inter-Process Communication",
            "summary": "Mechanisms that let processes exchange data safely across address spaces.",
            "in_project": "Chat traffic uses Pipe, Queue, or SharedMemory via a broker hub.",
        },
        {
            "id": "pipe",
            "name": "Pipe",
            "summary": "A duplex byte stream between two endpoints.",
            "in_project": "Each worker has a Pipe to the broker; broker forwards to the peer Pipe.",
        },
        {
            "id": "message_queue",
            "name": "Message Queue",
            "summary": "Producer–consumer channel with internal synchronization.",
            "in_project": "Workers put to a broker ingress Queue; broker puts to receiver inboxes.",
        },
        {
            "id": "shared_memory",
            "name": "Shared Memory",
            "summary": "Memory region mapped into multiple processes for fast exchange.",
            "in_project": "SharedMemory buffer + Lock + notify Queue (Windows-safe wait/wake).",
        },
        {
            "id": "mutex",
            "name": "Mutex / Lock",
            "summary": "Mutual exclusion: only one holder of the critical section at a time.",
            "in_project": "mutex_demo wraps counter increments; SHM writes also take a Lock.",
        },
        {
            "id": "semaphore",
            "name": "Semaphore",
            "summary": "Counting permit for limited concurrent access.",
            "in_project": "semaphore_demo uses Semaphore(2) with ACCESS/WAITING events.",
        },
        {
            "id": "race_condition",
            "name": "Race Condition",
            "summary": "Outcome depends on unpredictable scheduling of concurrent accesses.",
            "in_project": "race_demo increments a shared Value without a lock → lost updates.",
        },
        {
            "id": "producer_consumer",
            "name": "Producer–Consumer",
            "summary": "Producers generate items; consumers process them; a buffer decouples rates.",
            "in_project": "Bounded Queue demo shows backpressure when maxsize is reached.",
        },
        {
            "id": "scheduling",
            "name": "Scheduling / PIDs",
            "summary": "OS assigns PIDs and schedules ready processes on CPUs.",
            "in_project": "psutil reads live CPU%, RSS, and threads for each managed PID.",
        },
    ],
}


@router.get("/system/stats")
def system_stats(manager: IPCManager = Depends(get_ipc_manager)):
    pids = manager.registry.running_pids()
    # Prime CPU counters (first sample is often 0)
    collect_managed_stats(pids)
    stats = collect_managed_stats(pids)
    msg_rate = manager.metrics.msgs_per_sec()
    anomalies = {}
    for name, proc_stats in (stats.get("processes") or {}).items():
        if not isinstance(proc_stats, dict) or "cpu_percent" not in proc_stats:
            continue
        anomalies[name] = _anomaly.update_and_score(
            cpu_percent=float(proc_stats.get("cpu_percent") or 0.0),
            memory_mb=float(proc_stats.get("memory_rss_mb") or 0.0),
            num_threads=float(proc_stats.get("num_threads") or 0.0),
            msg_rate=float(msg_rate),
        )
    return {
        **stats,
        "mechanism": manager.get_mechanism(),
        "ipc_metrics": manager.metrics.snapshot(),
        "anomalies": anomalies,
    }


@router.get("/concepts")
def concepts():
    return OS_CONCEPTS
