"""Database session and initialization."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend import DATA_DIR, DB_PATH
from backend.database.models import Base, User

_engine = None
SessionLocal = None


def get_engine():
    global _engine, SessionLocal
    if _engine is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{DB_PATH.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    assert SessionLocal is not None
    with SessionLocal() as db:
        existing = {u.name for u in db.query(User).all()}
        for name in ("alice", "bob", "charlie"):
            if name not in existing:
                db.add(User(name=name, role="worker"))
        db.commit()


def get_db() -> Generator[Session, None, None]:
    get_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
