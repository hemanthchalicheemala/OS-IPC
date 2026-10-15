"""IPC status / metrics / mechanism routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend import MECHANISMS
from backend.api.deps import get_ipc_manager
from backend.ipc.manager import IPCManager

router = APIRouter(prefix="/ipc", tags=["ipc"])


class MechanismBody(BaseModel):
    mechanism: str = Field(..., min_length=1, max_length=32)


@router.get("/status")
def ipc_status(manager: IPCManager = Depends(get_ipc_manager)):
    return manager.status()


@router.get("/metrics")
def ipc_metrics(manager: IPCManager = Depends(get_ipc_manager)):
    return manager.metrics.snapshot()


@router.post("/mechanism")
def set_mechanism(body: MechanismBody, manager: IPCManager = Depends(get_ipc_manager)):
    mech = body.mechanism.lower().strip()
    if mech not in MECHANISMS:
        raise HTTPException(status_code=400, detail=f"mechanism must be one of {list(MECHANISMS)}")
    try:
        current = manager.set_mechanism(mech)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "mechanism": current, "allowed": list(MECHANISMS)}
