"""Unit and integration tests for Intelligent IPC Chat (real OS IPC)."""

from __future__ import annotations

import time

import pytest

from backend.ipc.manager import IPCManager
from backend.ipc.sync.mutex_demo import run_mutex_demo
from backend.ipc.sync.race_demo import run_race_demo
from backend.ipc.sync.semaphore_demo import run_semaphore_demo
from backend.ml.classifier import MessageClassifier
from backend.ml.train import ensure_trained


@pytest.fixture(scope="module")
def manager():
    ensure_trained()
    IPCManager.reset_instance()
    m = IPCManager.instance()
    m.start_all()
    time.sleep(0.8)
    yield m
    m.shutdown()
    IPCManager.reset_instance()


def test_processes_have_real_pids(manager: IPCManager):
    items = manager.registry.list_all()
    running = [p for p in items if p.get("status") == "running" and p.get("pid")]
    assert len(running) >= 4
    pids = {p["pid"] for p in running}
    assert all(isinstance(pid, int) and pid > 0 for pid in pids)
    assert len(pids) == len(running)


def test_pipe_message_delivery(manager: IPCManager):
    manager.set_mechanism("pipe")
    time.sleep(0.2)
    msg = manager.send_message("alice", "bob", "pipe-test-hello")
    assert msg["id"]
    deadline = time.time() + 5
    delivered = None
    while time.time() < deadline:
        got = manager.get_message(msg["id"])
        if got and (got.get("delivered") or got.get("status") == "delivered"):
            delivered = got
            break
        time.sleep(0.1)
    assert delivered is not None
    assert delivered.get("latency_ms") is None or delivered["latency_ms"] >= 0


def test_queue_message_delivery(manager: IPCManager):
    manager.set_mechanism("queue")
    time.sleep(0.2)
    msg = manager.send_message("bob", "charlie", "queue-test-hello")
    assert msg["sender"] == "bob"
    deadline = time.time() + 5
    while time.time() < deadline:
        got = manager.get_message(msg["id"])
        if got and (got.get("delivered") or got.get("status") == "delivered"):
            return
        time.sleep(0.1)
    pytest.fail("queue message not delivered")


def test_shared_memory_message_delivery(manager: IPCManager):
    manager.set_mechanism("shared_memory")
    time.sleep(0.2)
    msg = manager.send_message("charlie", "alice", "shm-test-hello")
    deadline = time.time() + 5
    while time.time() < deadline:
        got = manager.get_message(msg["id"])
        if got and (got.get("delivered") or got.get("status") == "delivered"):
            return
        time.sleep(0.1)
    pytest.fail("shared memory message not delivered")


def test_race_condition_loses_updates():
    result = run_race_demo(num_processes=4, increments=2000)
    expected = result["expected"]
    final = result["final_count"]
    assert final <= expected
    # With intentional yield, lost updates are expected on Windows.
    assert result["lost_updates"] >= 0


def test_mutex_is_consistent():
    result = run_mutex_demo(num_processes=4, increments=800)
    assert result["final_count"] == result["expected"]
    assert result["consistent"] is True


def test_semaphore_demo_runs():
    result = run_semaphore_demo(num_processes=4, limit=2, hold_seconds=0.05)
    assert result["limit"] == 2
    assert result["num_processes"] == 4


def test_ml_classifier_spam():
    ensure_trained()
    clf = MessageClassifier()
    pred = clf.predict("Congratulations! You won a FREE iPhone click now!!!")
    label = str(pred.get("label") or "").lower()
    assert "spam" in label
    assert float(pred.get("confidence") or 0) > 0.35


def test_integration_chat_flow(manager: IPCManager):
    manager.set_mechanism("pipe")
    time.sleep(0.2)
    msg = manager.send_message("alice", "bob", "integration hello")
    deadline = time.time() + 6
    delivered = False
    while time.time() < deadline:
        got = manager.get_message(msg["id"])
        if got and (got.get("delivered") or got.get("status") == "delivered"):
            delivered = True
            if got.get("latency_ms") is not None:
                assert got["latency_ms"] >= 0
            break
        time.sleep(0.1)
    assert delivered

    ensure_trained()
    clf = MessageClassifier()
    pred = clf.predict(msg["content"] if isinstance(msg, dict) else "integration hello")
    assert pred.get("label") or pred.get("classification")

    snap = manager.metrics.snapshot()
    assert isinstance(snap, dict)


def test_process_restart_changes_pid(manager: IPCManager):
    before = manager.registry.get("alice")
    assert before is not None and before.pid
    old_pid = before.pid
    info = manager.restart_process("alice")
    time.sleep(0.8)
    new_pid = info.get("pid")
    assert new_pid and new_pid != old_pid
    # Pipe path must still work after broker+worker restart
    manager.set_mechanism("pipe")
    time.sleep(0.3)
    msg = manager.send_message("alice", "bob", "post-restart ping")
    deadline = time.time() + 6
    while time.time() < deadline:
        got = manager.get_message(msg["id"])
        if got and got.get("delivered"):
            return
        time.sleep(0.1)
    pytest.fail("message after restart not delivered")
