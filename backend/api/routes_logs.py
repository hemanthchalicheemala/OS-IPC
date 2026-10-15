"""Log listing routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.models import LogEntry
from backend.database.session import get_db

router = APIRouter(prefix="/logs", tags=["logs"])

# In-memory ring buffer for recent runtime logs (also mirrored to DB when posted)
_MEMORY_LOGS: list[dict] = []


def append_log(level: str, source: str, message: str, db: Session | None = None) -> dict:
    entry = {
        "level": level,
        "source": source,
        "message": message,
        "created_at": datetime.utcnow().isoformat(),
    }
    _MEMORY_LOGS.append(entry)
    if len(_MEMORY_LOGS) > 500:
        del _MEMORY_LOGS[: len(_MEMORY_LOGS) - 500]
    if db is not None:
        db.add(
            LogEntry(
                level=level,
                source=source,
                message=message,
                created_at=datetime.utcnow(),
            )
        )
        db.commit()
    return entry


class LogBody(BaseModel):
    level: str = Field(default="INFO", max_length=16)
    source: str = Field(default="api", max_length=64)
    message: str = Field(..., min_length=1, max_length=4000)


@router.get("")
def list_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rows = db.query(LogEntry).order_by(LogEntry.id.desc()).limit(limit).all()
    persisted = [
        {
            "id": r.id,
            "level": r.level,
            "source": r.source,
            "message": r.message,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return {"logs": list(reversed(_MEMORY_LOGS[-limit:])), "persisted": persisted}


@router.post("")
def add_log(body: LogBody, db: Session = Depends(get_db)):
    entry = append_log(body.level.upper(), body.source, body.message, db=db)
    return {"ok": True, "entry": entry}
