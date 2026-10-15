"""IPC Broker process — hub-and-spoke router for Pipe / Queue / SharedMemory.

Workers do not talk peer-to-peer for pipe/queue; the broker receives a message
and forwards it to the destination worker over the same mechanism family.
"""

from __future__ import annotations

import os
import time
from typing import Any

from backend.ipc.events import make_event
from backend.ipc.mechanisms.pipe_channel import pipe_recv, pipe_send
from backend.ipc.mechanisms.queue_channel import queue_get, queue_put
from backend.ipc.mechanisms.shm_channel import attach_shm, shm_read, shm_wait_notify, shm_write


def _emit(event_queue, event: dict[str, Any]) -> None:
    try:
        event_queue.put(event)
    except Exception:
        pass


_CODE_TO_MECH = {0: "pipe", 1: "queue", 2: "shared_memory"}


def _mechanism_str(mechanism_value) -> str:
    try:
        return _CODE_TO_MECH.get(int(mechanism_value.value), "pipe")
    except Exception:
        return "pipe"


def broker_main(
    control_queue,
    event_queue,
    mechanism_value,
    worker_pipes: dict,
    to_broker_queue,
    worker_inboxes: dict,
    shm_name: str,
    shm_lock,
    shm_notify_broker,
    worker_shm_notifies: dict,
    ml_inbox,
) -> None:
    """Broker entry point (spawn-safe module-level function)."""
    shm = None
    try:
        shm = attach_shm(shm_name)
    except Exception as exc:
        _emit(event_queue, make_event("error", process="broker", data={"error": f"SHM attach failed: {exc}"}))

    _emit(
        event_queue,
        make_event("status", process="broker", data={"status": "running", "pid": os.getpid()}),
    )

    last_heartbeat = 0.0
    running = True

    while running:
        now = time.time()
        if now - last_heartbeat >= 1.0:
            _emit(event_queue, make_event("heartbeat", process="broker", data={"pid": os.getpid()}))
            last_heartbeat = now

        cmd = queue_get(control_queue, timeout=0.01)
        if cmd and (cmd.get("action") or "").lower() == "shutdown":
            running = False
            break

        mechanism = _mechanism_str(mechanism_value)

        # Pipe: poll each worker connection
        if mechanism == "pipe":
            for worker_name, conn in worker_pipes.items():
                msg = pipe_recv(conn, timeout=0.0)
                if msg:
                    _route(
                        msg,
                        mechanism="pipe",
                        event_queue=event_queue,
                        worker_pipes=worker_pipes,
                        worker_inboxes=worker_inboxes,
                        shm=shm,
                        shm_lock=shm_lock,
                        worker_shm_notifies=worker_shm_notifies,
                        ml_inbox=ml_inbox,
                    )

        # Queue: drain broker ingress
        if mechanism == "queue":
            msg = queue_get(to_broker_queue, timeout=0.02)
            if msg:
                _route(
                    msg,
                    mechanism="queue",
                    event_queue=event_queue,
                    worker_pipes=worker_pipes,
                    worker_inboxes=worker_inboxes,
                    shm=shm,
                    shm_lock=shm_lock,
                    worker_shm_notifies=worker_shm_notifies,
                    ml_inbox=ml_inbox,
                )

        # SharedMemory: wait for notify from a writer
        if mechanism == "shared_memory":
            note = shm_wait_notify(shm_notify_broker, timeout=0.02)
            if note and shm is not None:
                msg = shm_read(shm, shm_lock)
                if msg:
                    _route(
                        msg,
                        mechanism="shared_memory",
                        event_queue=event_queue,
                        worker_pipes=worker_pipes,
                        worker_inboxes=worker_inboxes,
                        shm=shm,
                        shm_lock=shm_lock,
                        worker_shm_notifies=worker_shm_notifies,
                        ml_inbox=ml_inbox,
                    )

    _emit(event_queue, make_event("status", process="broker", data={"status": "stopped"}))
    if shm is not None:
        try:
            shm.close()
        except Exception:
            pass


def _route(
    msg: dict[str, Any],
    *,
    mechanism: str,
    event_queue,
    worker_pipes: dict,
    worker_inboxes: dict,
    shm,
    shm_lock,
    worker_shm_notifies: dict,
    ml_inbox,
) -> None:
    receiver = (msg.get("receiver") or "").lower()
    sender = (msg.get("sender") or "").lower()
    msg = dict(msg)
    msg["mechanism"] = mechanism

    _emit(
        event_queue,
        make_event(
            "broker_route",
            process="broker",
            message_id=msg.get("id"),
            data={"sender": sender, "receiver": receiver, "mechanism": mechanism},
        ),
    )

    if receiver not in worker_pipes and receiver not in worker_inboxes:
        _emit(
            event_queue,
            make_event(
                "message_failed",
                process="broker",
                message_id=msg.get("id"),
                data={"error": f"Unknown receiver: {receiver}", "message": msg},
            ),
        )
        return

    try:
        if mechanism == "pipe":
            conn = worker_pipes[receiver]
            pipe_send(conn, msg)
        elif mechanism == "queue":
            queue_put(worker_inboxes[receiver], msg)
        elif mechanism == "shared_memory":
            # Re-write payload so the receiver observes a real SHM read.
            notify_q = worker_shm_notifies[receiver]
            shm_write(shm, shm_lock, notify_q, msg, notify_target=receiver)
        else:
            raise ValueError(f"Unknown mechanism: {mechanism}")

        # Push to ML analyzer for side-channel classification
        try:
            ml_inbox.put_nowait({"text": msg.get("content", ""), "message_id": msg.get("id")})
        except Exception:
            pass

        _emit(
            event_queue,
            make_event(
                "message_delivered",
                process="broker",
                message_id=msg.get("id"),
                data={"message": msg, "mechanism": mechanism},
            ),
        )
    except Exception as exc:
        _emit(
            event_queue,
            make_event(
                "message_failed",
                process="broker",
                message_id=msg.get("id"),
                data={"error": str(exc), "message": msg},
            ),
        )
