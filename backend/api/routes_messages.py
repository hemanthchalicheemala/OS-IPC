"""Message send / history routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.deps import get_ipc_manager
from backend.database.models import Message
from backend.database.session import get_db
from backend.ipc.manager import IPCManager

router = APIRouter(prefix="/messages", tags=["messages"])


class SendMessageBody(BaseModel):
    sender: str = Field(..., min_length=1, max_length=32)
    receiver: str = Field(..., min_length=1, max_length=32)
    content: str = Field(..., min_length=1, max_length=8000)
    mechanism: str | None = Field(default=None, max_length=32)


@router.post("/send")
def send_message(
    body: SendMessageBody,
    manager: IPCManager = Depends(get_ipc_manager),
    db: Session = Depends(get_db),
):
    try:
        payload = manager.send_message(
            sender=body.sender,
            receiver=body.receiver,
            content=body.content,
            mechanism=body.mechanism,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    row = Message(
        message_uid=payload["id"],
        sender=payload["sender"],
        receiver=payload["receiver"],
        content=payload["content"],
        mechanism=payload["mechanism"],
        size_bytes=payload.get("size_bytes") or 0,
        latency_ms=payload.get("latency_ms"),
        delivered=False,
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    return {"ok": True, "message": payload}


@router.get("")
def list_messages(
    manager: IPCManager = Depends(get_ipc_manager),
    db: Session = Depends(get_db),
):
    live = manager.list_messages()
    db_rows = db.query(Message).order_by(Message.id.desc()).limit(200).all()
    persisted = [
        {
            "id": r.message_uid,
            "sender": r.sender,
            "receiver": r.receiver,
            "content": r.content,
            "mechanism": r.mechanism,
            "size_bytes": r.size_bytes,
            "latency_ms": r.latency_ms,
            "delivered": r.delivered,
            "timestamp": r.created_at.isoformat() if r.created_at else None,
        }
        for r in db_rows
    ]
    return {"messages": live, "persisted": persisted}


@router.get("/{message_id}")
def get_message(
    message_id: str,
    manager: IPCManager = Depends(get_ipc_manager),
    db: Session = Depends(get_db),
):
    live = manager.get_message(message_id)
    if live:
        return {"message": live}
    row = db.query(Message).filter(Message.message_uid == message_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")
    return {
        "message": {
            "id": row.message_uid,
            "sender": row.sender,
            "receiver": row.receiver,
            "content": row.content,
            "mechanism": row.mechanism,
            "size_bytes": row.size_bytes,
            "latency_ms": row.latency_ms,
            "delivered": row.delivered,
        }
    }
