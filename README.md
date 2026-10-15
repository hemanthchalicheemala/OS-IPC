# Intelligent IPC Chat Application

A BTech Operating Systems project: a **real-time chat UI** backed by **real Windows OS processes** that communicate with **Pipe**, **Message Queue**, and **Shared Memory**, plus mutex/semaphore demos, live metrics, and local ML message classification.

> This is not a frontend simulation. Alice/Bob/Charlie are real processes with real PIDs, and message latency is measured on every send.

## Problem statement

Demonstrate Inter-Process Communication, process management, synchronization, and monitoring on a local PC using a visually clear chat and dashboard application suitable for an OS viva.

## Objectives

- Create and manage independent OS processes
- Exchange messages using Pipe, Queue, and Shared Memory
- Prevent race conditions with Lock / Semaphore
- Measure real IPC latency and process CPU/RAM
- Classify messages with a local TF-IDF + Logistic Regression model
- Present everything in a professional developer-tool UI

## Features

- Chat between Alice, Bob, Charlie over selectable IPC mechanisms
- Process table with live PID, CPU, memory, threads (via `psutil`)
- IPC visualizer and latency comparison
- Race / Mutex / Semaphore / Producer–Consumer experiments
- ML spam/toxic/urgent/normal classification + sentiment
- Isolation Forest anomaly warnings (warn-only)
- SQLite history for messages, metrics, experiments, logs
- OS Concepts panel for viva prep

## Architecture

```
React (Vite)  →  FastAPI + WebSocket  →  IPC Manager
                                         ├─ Broker process
                                         ├─ Alice / Bob / Charlie
                                         └─ ML analyzer
                                              ↕
                                    Pipe | Queue | SharedMemory
```

Chat path: **UI → API → sender process → real IPC → peer process → WebSocket update**.

## OS concepts used

Process, Thread, IPC, Pipe, Message Queue, Shared Memory, Mutex, Semaphore, Race Condition, Critical Section, Producer–Consumer, Scheduling (observed), Resource cleanup.

See [docs/os-concepts.md](docs/os-concepts.md) and the in-app **Concepts** page.

## IPC mechanisms

| Mechanism | Implementation | Path |
|-----------|----------------|------|
| Pipe | `multiprocessing.Pipe` | Worker ⇄ Broker ⇄ Worker |
| Message Queue | `multiprocessing.Queue` | Worker → Queue → Broker → inbox |
| Shared Memory | `SharedMemory` + `Lock` + notify Queue | Worker → SHM → Worker |

## ML methodology

- Dataset: labeled normal / spam / toxic / urgent samples
- Model: TF-IDF vectorizer + Logistic Regression (`scikit-learn`)
- Sentiment: local Positive / Neutral / Negative classifier
- Anomaly: Isolation Forest on CPU, memory, threads, message rate
- Models stored under `data/models/` and trained on first backend start if missing

## Technology stack

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Recharts, Framer Motion, Lucide
- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **OS/IPC:** `multiprocessing` (Pipe, Queue, SharedMemory, Lock, Semaphore), `psutil`
- **ML:** scikit-learn, pandas, NumPy, joblib

## Installation (Windows)

```powershell
cd "c:\Users\heman\OneDrive\Desktop\OS IPC"

# Python
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

## How to run

Use **two terminals**. Do **not** use `uvicorn --reload` on Windows with multiprocessing (child respawn issues).

**Terminal 1 — backend**

```powershell
cd "c:\Users\heman\OneDrive\Desktop\OS IPC"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend**

```powershell
cd "c:\Users\heman\OneDrive\Desktop\OS IPC\frontend"
npm run dev
```

Open http://127.0.0.1:5173 — API docs at http://127.0.0.1:8000/docs

## How to test

```powershell
cd "c:\Users\heman\OneDrive\Desktop\OS IPC"
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe scripts\smoke_ipc.py
```

Manual demo checklist:

1. Open Processes — confirm real PIDs match Task Manager
2. Chat — send Alice → Bob over Pipe, then Queue, then Shared Memory
3. Experiments — run Race (unsafe count) then Mutex (safe count)
4. ML Analysis — paste a spam string and check SPAM label
5. Dashboard — watch live CPU/RAM and latency charts change

## Project structure

```
project/
├── backend/          # FastAPI + IPC runtime
├── frontend/         # React UI
├── data/             # SQLite DB + ML models
├── docs/             # OS concept notes
├── scripts/          # Smoke tests
├── tests/            # Automated tests
├── requirements.txt
└── README.md
```

## Screenshots

Add presentation screenshots here after your demo run (Dashboard, Chat, Processes, Experiments).

## Experiments

1. Pipe communication  
2. Message Queue communication  
3. Shared Memory communication  
4. Race condition  
5. Mutex synchronization  
6. Semaphore synchronization  
7. Producer–consumer  
8. Process creation/termination  
9. IPC latency comparison  
10. ML spam detection  

## Limitations

- Local Windows only; not a networked multi-machine chat
- Shared Memory uses a notify Queue for wait/wake (Windows has no POSIX `sem_wait` on raw SHM alone)
- Anomaly detection warns only; it never auto-kills processes
- Small educational ML dataset — not production spam filtering

## Future enhancements

- Named Windows pipes (`win32pipe`) comparison panel
- Persistent multi-session chat rooms
- Export experiment reports to PDF for lab submission
- Stronger online anomaly training window

## Safety

- UI cannot run arbitrary shell commands
- Start/stop/restart only apply to processes registered by this app
- Shutdown unlinks Shared Memory and terminates managed children
"# OS-IPC" 
