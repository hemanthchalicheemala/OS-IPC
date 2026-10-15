"""Smoke test for real IPC manager (Windows spawn)."""

from __future__ import annotations

import multiprocessing as mp
import sys
import time


def main() -> None:
    mp.freeze_support()
    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        pass

    print("importing manager...", flush=True)
    from backend.ipc.manager import IPCManager

    mgr = IPCManager.instance()
    events: list[str] = []
    mgr.add_callback(lambda e: events.append(str(e.get("type"))))
    print("starting processes...", flush=True)
    mgr.start_all()
    time.sleep(2.0)
    print("status:", mgr.status(), flush=True)

    print("send pipe...", flush=True)
    msg = mgr.send_message("alice", "bob", "hello pipe", "pipe")
    time.sleep(1.2)
    print("pipe stored:", mgr.get_message(msg["id"]), flush=True)

    mgr.set_mechanism("queue")
    print("send queue...", flush=True)
    msg2 = mgr.send_message("bob", "alice", "hello queue", "queue")
    time.sleep(1.2)
    print("queue stored:", mgr.get_message(msg2["id"]), flush=True)

    mgr.set_mechanism("shared_memory")
    print("send shm...", flush=True)
    msg3 = mgr.send_message("alice", "charlie", "hello shm", "shared_memory")
    time.sleep(1.2)
    print("shm stored:", mgr.get_message(msg3["id"]), flush=True)

    print("metrics:", mgr.metrics.snapshot(), flush=True)
    print("recent events:", events[-20:], flush=True)
    print("shutting down...", flush=True)
    mgr.shutdown()
    print("done", flush=True)


if __name__ == "__main__":
    main()
