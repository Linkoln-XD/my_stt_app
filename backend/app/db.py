from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    stage: Mapped[str] = mapped_column(String(64), default="queued")
    message: Mapped[str] = mapped_column(String(512), default="")
    original_filename: Mapped[str] = mapped_column(String(512), default="")
    upload_path: Mapped[str] = mapped_column(String(1024), default="")
    audio_path: Mapped[str] = mapped_column(String(1024), default="")
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


def _bootstrap_db():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{settings.db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return engine


_engine = _bootstrap_db()
SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def new_job_id() -> str:
    return str(uuid4())


def get_session() -> Session:
    return SessionLocal()


def job_to_dict(row: JobRow) -> dict:
    result = None
    if row.result_json:
        result = json.loads(row.result_json)
    return {
        "id": row.id,
        "status": row.status,
        "stage": row.stage,
        "message": row.message,
        "original_filename": row.original_filename,
        "error": row.error,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "result": result,
    }


def list_jobs(limit: int = 50) -> list[dict]:
    with get_session() as session:
        rows = session.scalars(select(JobRow).order_by(JobRow.created_at.desc()).limit(limit)).all()
        return [job_to_dict(r) for r in rows]
