# Operating System Concepts

Short viva-ready explanations of concepts used in this project.

## Process

**Definition:** A process is a program in execution with its own address space, PID, and resources.

**In this project:** Alice, Bob, Charlie, the IPC broker, and the ML analyzer are real `multiprocessing.Process` instances. The Processes page shows live OS PIDs from `psutil`.

**Real world:** Chrome tabs, background services, and terminal shells are separate processes.

## Thread

**Definition:** A thread is a lightweight unit of execution within a process sharing the same address space.

**In this project:** Each managed process may have multiple threads; we display `num_threads` via `psutil`. The FastAPI server also uses a background poll thread for IPC events.

**Real world:** A browser process uses threads for networking, rendering, and JS.

## Inter-Process Communication (IPC)

**Definition:** Mechanisms that allow processes to exchange data across separate address spaces.

**In this project:** Chat messages travel through Pipe, Message Queue, or Shared Memory — selected in the UI and executed by real OS primitives.

**Real world:** Desktop apps talking to a system service, or microservices over local sockets.

## Pipe

**Definition:** A duplex byte stream connecting two endpoints.

**In this project:** Each worker has a `multiprocessing.Pipe` to the broker. Path: Alice ⇄ Pipe ⇄ Broker ⇄ Pipe ⇄ Bob.

**Real world:** Shell pipelines (`cmd1 | cmd2`) and parent–child process channels.

## Message Queue

**Definition:** A producer–consumer buffer where messages are enqueued and dequeued with internal synchronization.

**In this project:** Workers put messages on a broker ingress `multiprocessing.Queue`; the broker forwards to receiver inboxes.

**Real world:** Job queues, print spoolers, and message brokers.

## Shared Memory

**Definition:** A memory region mapped into multiple processes for fast data exchange.

**In this project:** A `SharedMemory` buffer holds the payload; a `Lock` prevents races; a notify `Queue` wakes the peer (Windows-safe wait/wake).

**Real world:** High-performance graphics buffers and shared caches between processes.

## Mutex / Lock

**Definition:** Mutual exclusion — only one holder may enter the critical section at a time.

**In this project:** Mutex demo wraps counter increments; Shared Memory writes also take a Lock.

**Real world:** Protecting a bank balance update in concurrent software.

## Semaphore

**Definition:** A counting permit that limits how many processes may access a resource concurrently.

**In this project:** Semaphore demo uses `Semaphore(2)` and streams ACCESS vs WAITING events to the UI.

**Real world:** Limiting concurrent database connections or parking spots.

## Race Condition

**Definition:** Outcome depends on unpredictable interleaving of concurrent accesses to shared state.

**In this project:** The race experiment increments a shared counter without a lock and usually ends below the expected total (lost updates).

**Real world:** Two threads updating the same inventory count without synchronization.

## Critical Section

**Definition:** The code region that accesses shared resources and must not run concurrently unsafely.

**In this project:** Counter increments and Shared Memory writes are critical sections guarded by locks when synchronization is enabled.

**Real world:** Updating a shared configuration file.

## Producer–Consumer Problem

**Definition:** Producers generate items; consumers process them; a bounded buffer decouples production and consumption rates.

**In this project:** Bounded Queue demo shows backpressure when the queue is full.

**Real world:** Video streaming buffers and print queues.

## Process Scheduling

**Definition:** The OS decides which ready process runs on which CPU and for how long.

**In this project:** We do not implement a scheduler; we observe scheduling effects via live CPU% and nondeterministic race outcomes.

**Real world:** Multitasking on a multi-core laptop.

## Resource Management

**Definition:** Tracking and reclaiming CPU, memory, file handles, and IPC objects.

**In this project:** On shutdown we terminate managed children and unlink Shared Memory names to avoid orphans.

**Real world:** OS reclaiming memory after an app exits.
