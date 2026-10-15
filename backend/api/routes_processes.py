"""Process management routes — only registry-managed names."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend import MANAGED_PROCESSES
from backend.api.deps import get_ipc_manager
from backend.ipc.manager import IPCManager
from backend.monitoring.psutil_collector import collect_pid_stats

router = APIRouter(prefix="/processes", tags=["processes"])


@router.get("")
def list_processes(manager: IPCManager = Depends(get_ipc_manager)):
    items = manager.registry.list_all()
    for item in items:
        pid = item.get("pid")
        if pid:
            stats = collect_pid_stats(pid)
            item["stats"] = stats
    return {"processes": items, "managed": list(MANAGED_PROCESSES)}


@router.post("/{name}/start")
def start_process(name: str, manager: IPCManager = Depends(get_ipc_manager)):
    name = name.lower()
    if not manager.registry.is_managed(name):
        raise HTTPException(status_code=400, detail=f"Not a managed process: {name}")
    try:
        info = manager.start_process(name)
        return {"ok": True, "process": info}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{name}/stop")
def stop_process(name: str, manager: IPCManager = Depends(get_ipc_manager)):
    name = name.lower()
    if not manager.registry.is_managed(name):
        raise HTTPException(status_code=400, detail=f"Not a managed process: {name}")
    try:
        manager.stop_process(name)
        return {"ok": True, "process": manager.registry.get(name).to_dict()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{name}/restart")
def restart_process(name: str, manager: IPCManager = Depends(get_ipc_manager)):
    name = name.lower()
    if not manager.registry.is_managed(name):
        raise HTTPException(status_code=400, detail=f"Not a managed process: {name}")
    try:
        info = manager.restart_process(name)
        return {"ok": True, "process": info}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
