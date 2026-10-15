"""Generate Intelligent IPC Chat Application project report PDF."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Intelligent_IPC_Chat_Project_Report.pdf"


class ReportPDF(FPDF):
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 100, 110)
        self.cell(0, 8, "Intelligent IPC Chat Application - Project Report", align="L")
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 130)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title: str) -> None:
        self.ln(4)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(8, 145, 178)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(8, 145, 178)
        self.set_line_width(0.4)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.set_xy(self.l_margin, y + 4)
        self.set_text_color(30, 30, 35)

    def sub_title(self, title: str) -> None:
        self.ln(2)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 50)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(30, 30, 35)

    def body(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 48)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 48)
        self.multi_cell(0, 5.5, f"- {text}")

    def numbered(self, n: int, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 48)
        self.multi_cell(0, 5.5, f"{n}. {text}")


def build() -> Path:
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ----- Cover -----
    pdf.ln(28)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(8, 145, 178)
    pdf.multi_cell(0, 10, "Intelligent IPC Chat Application", align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(60, 60, 70)
    pdf.multi_cell(0, 7, "BTech Operating Systems Project Report", align="C")
    pdf.ln(8)
    pdf.set_draw_color(8, 145, 178)
    pdf.set_line_width(0.6)
    mid = pdf.w / 2
    pdf.line(mid - 35, pdf.get_y(), mid + 35, pdf.get_y())
    pdf.ln(12)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 60)
    for line in [
        "Real-time chat using Inter-Process Communication",
        "Pipe | Message Queue | Shared Memory",
        "Process management | Synchronization | ML analysis",
        "",
        "Platform: Local Windows PC",
        "Stack: React + FastAPI + Python multiprocessing",
    ]:
        pdf.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(110, 110, 120)
    pdf.multi_cell(
        0,
        5,
        "This document describes the project aim, features, architecture, "
        "OS concepts demonstrated, and how to run and present the system.",
        align="C",
    )

    # ----- 1. Aim -----
    pdf.add_page()
    pdf.section_title("1. Project Aim")
    pdf.body(
        "The aim of this project is to design and implement a complete, "
        "demonstration-ready Operating Systems application that shows how "
        "independent processes communicate on a real computer using Inter-Process "
        "Communication (IPC) mechanisms."
    )
    pdf.body(
        "Unlike a frontend-only simulation, this application creates real OS "
        "processes (with real Process IDs), exchanges messages through Pipe, "
        "Message Queue, and Shared Memory, measures real latency, and displays "
        "live CPU/memory statistics. A polished control-center UI helps explain "
        "these concepts clearly during a viva or lab presentation."
    )

    pdf.section_title("2. Problem Statement")
    pdf.body(
        "Operating Systems courses teach IPC, synchronization, and process "
        "management as abstract topics. Students often struggle to see how these "
        "ideas appear in real software. This project bridges that gap by building "
        "a chat-style application in which Alice, Bob, and Charlie are separate "
        "processes that talk through selectable IPC channels, while the user "
        "observes PIDs, latency, locks, and ML message analysis in real time."
    )

    pdf.section_title("3. Objectives")
    for item in [
        "Create and manage independent OS processes with real PIDs.",
        "Implement at least three IPC mechanisms: Pipe, Message Queue, Shared Memory.",
        "Demonstrate race conditions and safe synchronization using Mutex and Semaphore.",
        "Measure real IPC latency, throughput, CPU, and memory usage.",
        "Classify messages with a local machine-learning model (TF-IDF + Logistic Regression).",
        "Provide a professional UI suitable for academic demonstration.",
        "Persist messages, metrics, and experiment results in SQLite.",
    ]:
        pdf.bullet(item)

    # ----- What it does -----
    pdf.section_title("4. What the Project Does")
    pdf.body(
        "The Intelligent IPC Chat Application is a local control center for "
        "inter-process messaging:"
    )
    for item in [
        "Starts managed processes: IPC Broker, Alice, Bob, Charlie, and an ML Analyzer.",
        "Lets the user send chat messages from one process to another.",
        "Routes each message through the selected IPC mechanism.",
        "Shows delivery status, latency, message size, and mechanism used.",
        "Animates the path Alice -> IPC -> Bob on the visualizer.",
        "Displays live process stats (PID, CPU%, RAM, threads) via psutil.",
        "Runs OS experiments (race vs mutex, semaphore, producer-consumer, benchmarks).",
        "Classifies message text as normal, spam, toxic, or urgent using a local model.",
        "Stores history and experiment results in a local SQLite database.",
    ]:
        pdf.bullet(item)

    pdf.sub_title("Important note")
    pdf.body(
        "The React frontend does not fake IPC. It only sends commands to the "
        "FastAPI backend. Actual communication happens between Python "
        "multiprocessing processes using OS-level IPC primitives."
    )

    # ----- Features -----
    pdf.section_title("5. Main Features")
    features = [
        ("Chat System", "Alice/Bob/Charlie messaging with timestamps, status, and inspector."),
        ("IPC Engine", "Switchable Pipe, Message Queue, and Shared Memory channels."),
        ("Process Manager", "Start, stop, restart managed processes; show real PIDs."),
        ("Synchronization Demos", "Race condition, Mutex, Semaphore, Producer-Consumer."),
        ("IPC Monitoring Dashboard", "CPU, RAM, latency, messages/sec, activity feed."),
        ("IPC Visualizer", "Animated process -> mechanism -> process path."),
        ("IPC Comparison", "Benchmark latency across mechanisms from real runs."),
        ("ML Message Analysis", "TF-IDF + Logistic Regression classification + sentiment."),
        ("Anomaly Hints", "Isolation Forest warnings on unusual resource patterns."),
        ("OS Experiments Panel", "Ten runnable labs with live output and explanations."),
        ("Message History", "SQLite-backed history of past transmissions."),
        ("OS Concepts Panel", "Viva-ready definitions linked to project usage."),
    ]
    for title, desc in features:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5.5, desc)
        pdf.ln(1)

    # ----- How it works -----
    pdf.add_page()
    pdf.section_title("6. How It Works (Architecture)")
    pdf.body("High-level data flow:")
    pdf.set_font("Courier", "", 9)
    pdf.set_fill_color(245, 247, 250)
    pdf.multi_cell(
        0,
        5,
        "  React UI  -->  FastAPI (REST + WebSocket)\n"
        "                     |\n"
        "                 IPC Manager\n"
        "           /        |         \\\n"
        "      Alice      Broker      Bob / Charlie\n"
        "           \\        |         /\n"
        "            Pipe / Queue / Shared Memory\n"
        "                     |\n"
        "               ML Analyzer Process",
        fill=True,
    )
    pdf.ln(3)
    pdf.body(
        "When the user clicks Send on the Chat page, the UI calls the backend API. "
        "The IPC Manager places a send command on the sender process control channel. "
        "The sender process writes the message using the selected IPC mechanism. "
        "The broker (for Pipe/Queue hub routing) or shared-memory path delivers it "
        "to the receiver. Events and measured latency are streamed back over "
        "WebSocket so the UI updates live."
    )

    pdf.sub_title("6.1 Technology Stack")
    for item in [
        "Frontend: React, TypeScript, Vite, Tailwind CSS, Recharts, Framer Motion, Lucide.",
        "Backend: Python, FastAPI, Uvicorn, SQLAlchemy, SQLite.",
        "OS/IPC: multiprocessing.Pipe, Queue, SharedMemory, Lock, Semaphore; psutil.",
        "ML: scikit-learn (TF-IDF + Logistic Regression), Isolation Forest.",
    ]:
        pdf.bullet(item)

    pdf.sub_title("6.2 IPC Mechanisms")
    pdf.body(
        "Pipe: Each worker has a duplex Pipe to the broker. Path: Alice <-> Pipe <-> "
        "Broker <-> Pipe <-> Bob."
    )
    pdf.body(
        "Message Queue: Workers put messages into a multiprocessing.Queue. The "
        "broker forwards to receiver inboxes (classic producer-consumer)."
    )
    pdf.body(
        "Shared Memory: A SharedMemory buffer holds the payload. A Lock prevents "
        "races. A notify Queue wakes the peer (Windows-compatible wait/wake)."
    )

    pdf.sub_title("6.3 Synchronization")
    pdf.body(
        "Race demo: multiple processes increment a shared counter without a lock, "
        "often producing a final count below the expected total (lost updates)."
    )
    pdf.body(
        "Mutex demo: the same increments protected by a Lock produce a consistent "
        "final count. Semaphore demo limits concurrent access (e.g., 2 permits)."
    )

    pdf.sub_title("6.4 Machine Learning")
    pdf.body(
        "A small labeled dataset trains a local TF-IDF + Logistic Regression model "
        "to classify messages as normal, spam, toxic, or urgent. Sentiment is also "
        "estimated. Predictions run on the local machine - not a cloud API."
    )

    # ----- Modules / pages -----
    pdf.section_title("7. Application Modules (UI Menus)")
    menus = [
        ("Dashboard", "Live CPU/RAM, latency, throughput, and activity feed."),
        ("Chat", "Compose and send messages; watch live delivery and visualizer."),
        ("Processes", "Table of managed processes with start/stop/restart."),
        ("IPC", "Detailed path visualizer and per-mechanism metrics."),
        ("Comparison", "Benchmark charts comparing Pipe vs Queue vs Shared Memory."),
        ("ML Analysis", "Paste text and view classification, confidence, sentiment."),
        ("Experiments", "Run OS labs with live results and explanations."),
        ("History", "Persisted message history from SQLite."),
        ("Concepts", "OS concept definitions for viva preparation."),
        ("Settings", "Theme and connection status."),
    ]
    for name, desc in menus:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, name, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5.5, desc)
        pdf.ln(1)

    # ----- OS concepts -----
    pdf.add_page()
    pdf.section_title("8. OS Concepts Demonstrated")
    concepts = [
        ("Process", "Independent program in execution with its own PID and address space."),
        ("IPC", "Mechanisms that allow processes to exchange data safely."),
        ("Pipe", "Byte stream channel between process endpoints."),
        ("Message Queue", "Buffered producer-consumer messaging."),
        ("Shared Memory", "Common memory region mapped into multiple processes."),
        ("Mutex / Lock", "Mutual exclusion for critical sections."),
        ("Semaphore", "Counting permit for limited concurrent access."),
        ("Race Condition", "Incorrect results due to unsynchronized concurrent updates."),
        ("Producer-Consumer", "Producers fill a buffer; consumers drain it."),
        ("Resource Monitoring", "Observing CPU, memory, and threads of managed processes."),
    ]
    for name, desc in concepts:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, name, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5.5, desc)
        pdf.ln(0.5)

    # ----- How to run -----
    pdf.section_title("9. How to Run")
    pdf.body("Requirements: Windows PC, Python 3.11+, Node.js/npm.")
    pdf.sub_title("Install (first time)")
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(
        0,
        4.5,
        "cd \"...\\OS IPC\"\n"
        "python -m venv .venv\n"
        ".\\.venv\\Scripts\\pip.exe install -r requirements.txt\n"
        "cd frontend\n"
        "npm install",
    )
    pdf.ln(2)
    pdf.sub_title("Start backend (Terminal 1)")
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(
        0,
        4.5,
        "cd \"...\\OS IPC\"\n"
        "$env:PYTHONPATH = (Get-Location).Path\n"
        ".\\.venv\\Scripts\\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000",
    )
    pdf.ln(2)
    pdf.body("Do not use --reload on Windows with multiprocessing.")
    pdf.sub_title("Start frontend (Terminal 2)")
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(
        0,
        4.5,
        "cd \"...\\OS IPC\\frontend\"\n"
        "npm run dev",
    )
    pdf.ln(2)
    pdf.body("Open http://127.0.0.1:5173/  |  API docs: http://127.0.0.1:8000/docs")

    pdf.section_title("10. Suggested Demo Flow (Viva)")
    for i, step in enumerate(
        [
            "Open Processes - show real PIDs matching Task Manager.",
            "Open Chat - send Alice -> Bob using Pipe, then Queue, then Shared Memory.",
            "Watch the IPC visualizer animate the message path.",
            "Open Experiments - run Race Condition (unsafe count), then Mutex (safe count).",
            "Open ML Analysis - classify a spam string vs a normal message.",
            "Open Dashboard / Comparison - show measured latency charts.",
            "Open Concepts - briefly define IPC, Mutex, and Shared Memory.",
        ],
        start=1,
    ):
        pdf.numbered(i, step)

    pdf.section_title("11. Results & Outcomes")
    for item in [
        "Real processes are created and managed with authentic OS PIDs.",
        "Messages are delivered through real IPC channels with measured latency.",
        "Race conditions produce inconsistent counters; locks restore consistency.",
        "Local ML model classifies messages without cloud dependency.",
        "The UI presents OS concepts in a form suitable for academic evaluation.",
    ]:
        pdf.bullet(item)

    pdf.section_title("12. Limitations")
    for item in [
        "Runs locally on Windows; not a networked multi-machine chat system.",
        "Shared Memory uses a notify Queue for wait/wake (Windows-friendly design).",
        "ML dataset is educational-scale, not production spam filtering.",
        "Anomaly detection warns only; it does not auto-kill processes.",
    ]:
        pdf.bullet(item)

    pdf.section_title("13. Future Enhancements")
    for item in [
        "Export experiment reports as PDF for lab submission.",
        "Named Windows pipe comparison panel.",
        "Stronger online anomaly training window.",
        "Multi-session chat rooms with persisted transcripts.",
    ]:
        pdf.bullet(item)

    pdf.section_title("14. Conclusion")
    pdf.body(
        "The Intelligent IPC Chat Application successfully demonstrates core "
        "Operating Systems concepts-process management, IPC, synchronization, "
        "monitoring, and lightweight ML-on a real Windows PC. By combining a "
        "professional control-center UI with genuine multiprocessing IPC, the "
        "project makes abstract OS theory concrete, measurable, and easy to "
        "present in a viva."
    )

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(110, 110, 120)
    pdf.multi_cell(
        0,
        5,
        "End of report. Source code: backend/ (FastAPI + IPC runtime), "
        "frontend/ (React UI), docs/os-concepts.md (viva notes).",
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote: {path}")
