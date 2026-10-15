"""Bounded producer–consumer demo using multiprocessing.Queue(maxsize=N).

Producers block when the queue is full; consumers block when empty. Queue size
over time illustrates backpressure.
"""

from __future__ import annotations

import time
from multiprocessing import Process, Queue


def _producer(q: Queue, producer_id: int, count: int, event_queue) -> None:
    for i in range(count):
        item = {"producer": producer_id, "seq": i, "ts": time.time()}
        q.put(item)
        if event_queue is not None:
            event_queue.put(
                {
                    "type": "pc_produce",
                    "process": f"producer-{producer_id}",
                    "timestamp": time.time(),
                    "data": {"seq": i, "approx_qsize": q.qsize()},
                }
            )
        time.sleep(0.01)


def _consumer(q: Queue, consumer_id: int, total_expected: int, event_queue, consumed_counter) -> None:
    got = 0
    while got < total_expected:
        try:
            item = q.get(timeout=2.0)
        except Exception:
            break
        got += 1
        with consumed_counter.get_lock():
            consumed_counter.value += 1
        if event_queue is not None:
            event_queue.put(
                {
                    "type": "pc_consume",
                    "process": f"consumer-{consumer_id}",
                    "timestamp": time.time(),
                    "data": {
                        "seq": item.get("seq"),
                        "from_producer": item.get("producer"),
                        "approx_qsize": q.qsize(),
                    },
                }
            )
        time.sleep(0.015)


def run_producer_consumer_demo(
    num_producers: int = 2,
    num_consumers: int = 2,
    items_per_producer: int = 20,
    maxsize: int = 5,
    event_queue=None,
    event_callback=None,
) -> dict:
    from multiprocessing import Value

    q: Queue = Queue(maxsize=maxsize)
    consumed = Value("i", 0)
    procs: list[Process] = []
    total = num_producers * items_per_producer
    # Split expected consumption roughly across consumers
    per_consumer = (total + num_consumers - 1) // num_consumers

    if event_callback:
        event_callback(
            {
                "type": "experiment_log",
                "data": {
                    "line": (
                        f"Producer-consumer: {num_producers}P/{num_consumers}C, "
                        f"bounded Queue(maxsize={maxsize}), items={total}"
                    ),
                },
            }
        )

    t0 = time.perf_counter()
    for i in range(num_producers):
        p = Process(
            target=_producer,
            args=(q, i, items_per_producer, event_queue),
            name=f"producer-{i}",
        )
        p.start()
        procs.append(p)

    for i in range(num_consumers):
        p = Process(
            target=_consumer,
            args=(q, i, per_consumer, event_queue, consumed),
            name=f"consumer-{i}",
        )
        p.start()
        procs.append(p)

    deadline = time.time() + 45
    while event_queue is not None and event_callback is not None and time.time() < deadline:
        alive = any(p.is_alive() for p in procs)
        try:
            while True:
                event_callback(event_queue.get_nowait())
        except Exception:
            pass
        if not alive:
            break
        time.sleep(0.05)

    for p in procs:
        p.join(timeout=15)
        if p.is_alive():
            p.terminate()
            p.join(timeout=2)

    if event_queue is not None and event_callback is not None:
        try:
            while True:
                event_callback(event_queue.get_nowait())
        except Exception:
            pass

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    result = {
        "experiment": "producer_consumer",
        "num_producers": num_producers,
        "num_consumers": num_consumers,
        "items_per_producer": items_per_producer,
        "maxsize": maxsize,
        "total_produced": total,
        "total_consumed": int(consumed.value),
        "elapsed_ms": elapsed_ms,
        "explanation": (
            "A bounded Queue applies backpressure: producers block when full, "
            "consumers block when empty—classic OS producer–consumer sync."
        ),
    }
    if event_callback:
        event_callback({"type": "experiment_result", "data": result})
    return result
