"""FastAPI dependency helpers."""

from __future__ import annotations

from fastapi import HTTPException, Request

from backend.ipc.manager import IPCManager


def get_ipc_manager(request: Request) -> IPCManager:
    manager = getattr(request.app.state, "ipc_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="IPC manager not initialized")
    return manager


def get_experiment_runner(request: Request):
    runner = getattr(request.app.state, "experiment_runner", None)
    if runner is None:
        raise HTTPException(status_code=503, detail="Experiment runner not initialized")
    return runner
