import json
import logging
import threading
from pathlib import Path

from app.config import settings
from app.db import JobRow, get_session
from app.services.transcription import transcribe_file

logger = logging.getLogger(__name__)

_lock = threading.Lock()


def _update_job(job_id: str, **fields) -> None:
    with get_session() as session:
        row = session.get(JobRow, job_id)
        if not row:
            return
        for key, value in fields.items():
            setattr(row, key, value)
        session.commit()


def process_job(job_id: str) -> None:
    with _lock:
        _process_job_unlocked(job_id)


def _process_job_unlocked(job_id: str) -> None:
    with get_session() as session:
        row = session.get(JobRow, job_id)
        if not row:
            return
        upload_path = Path(row.upload_path)
        upload_path_str = row.upload_path
        work_dir = settings.processed_dir / job_id

    def on_progress(stage: str, message: str) -> None:
        _update_job(job_id, status="processing", stage=stage, message=message)

    try:
        _update_job(job_id, status="processing", stage="queued", message="Starting…")
        work_dir.mkdir(parents=True, exist_ok=True)
        result = transcribe_file(upload_path, work_dir, on_progress=on_progress)
        audio_wav = work_dir / "audio_16k.wav"
        _update_job(
            job_id,
            status="done",
            stage="done",
            message="Complete",
            audio_path=str(audio_wav) if audio_wav.exists() else upload_path_str,
            result_json=result.model_dump_json(),
            error=None,
        )
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _update_job(
            job_id,
            status="failed",
            stage="error",
            message="Failed",
            error=str(exc),
        )
