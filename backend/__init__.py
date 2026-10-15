"""Intelligent IPC Chat Application — backend package."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = DATA_DIR / "models"
DB_PATH = DATA_DIR / "ipc_chat.db"

MANAGED_PROCESSES = ("broker", "alice", "bob", "charlie", "ml_analyzer")
WORKER_NAMES = ("alice", "bob", "charlie")
MECHANISMS = ("pipe", "queue", "shared_memory")
