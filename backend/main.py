"""FastAPI entrypoint for Intelligent IPC Chat Application."""

from __future__ import annotations

import asyncio
import multiprocessing as mp
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import DATA_DIR, MODELS_DIR
from backend.api import (
    routes_experiments,
    routes_ipc,
    routes_logs,
    routes_messages,
    routes_ml,
    routes_processes,
    routes_system,
)
from backend.api.routes_logs import append_log
from backend.api.websocket import install_ipc_bridge, router as ws_router
from backend.database import session as db_session
from backend.experiments.runner import ExperimentRunner
from backend.ipc.manager import IPCManager
from backend.ml.train import ensure_trained


def _ensure_spawn() -> None:
    if sys.platform.startswith("win"):
        try:
            mp.set_start_method("spawn", force=True)
        except RuntimeError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    db_session.get_engine()
    db_session.init_db()
    model_paths = ensure_trained()

    manager = IPCManager.instance()
    app.state.ipc_manager = manager
    app.state.ws_loop = asyncio.get_running_loop()
    install_ipc_bridge(app)

    def _bridge(event: dict) -> None:
        loop = getattr(app.state, "ws_loop", None)
        hub = getattr(app.state, "ws_manager", None)
        if loop is None or hub is None:
            return
        try:
            asyncio.run_coroutine_threadsafe(hub.broadcast(event), loop)
        except Exception:
            pass

    manager.add_callback(_bridge)
    app.state.experiment_runner = ExperimentRunner(manager, event_callback=_bridge)

    manager.start_all()
    # Give child processes a moment to attach SharedMemory / enter loops
    import time

    time.sleep(0.5)

    SessionLocal = db_session.SessionLocal
    if SessionLocal is None:
        raise RuntimeError("Database SessionLocal failed to initialize")
    with SessionLocal() as db:
        append_log("INFO", "lifespan", f"IPC manager started; models={model_paths}", db=db)

    yield

    with SessionLocal() as db:
        append_log("INFO", "lifespan", "Shutting down IPC manager", db=db)
    manager.shutdown()
    IPCManager.reset_instance()


def create_app() -> FastAPI:
    _ensure_spawn()
    application = FastAPI(
        title="Intelligent IPC Chat Application",
        description="Real multiprocessing IPC (Pipe / Queue / SharedMemory) on Windows",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_prefix = "/api"
    application.include_router(routes_processes.router, prefix=api_prefix)
    application.include_router(routes_messages.router, prefix=api_prefix)
    application.include_router(routes_ipc.router, prefix=api_prefix)
    application.include_router(routes_experiments.router, prefix=api_prefix)
    application.include_router(routes_ml.router, prefix=api_prefix)
    application.include_router(routes_system.router, prefix=api_prefix)
    application.include_router(routes_logs.router, prefix=api_prefix)
    application.include_router(ws_router)

    @application.get("/")
    def root():
        return {
            "name": "Intelligent IPC Chat Application",
            "docs": "/docs",
            "ws": "/ws",
            "api": "/api",
        }

    @application.get("/api/health")
    def health():
        return {"status": "ok"}

    return application


mp.freeze_support()
app = create_app()


if __name__ == "__main__":
    import uvicorn

    mp.freeze_support()
    _ensure_spawn()
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
