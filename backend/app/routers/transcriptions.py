from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.db import JobRow, get_session, job_to_dict, list_jobs, new_job_id
from app.models.schemas import (
    ExportFormat,
    JobResponse,
    TranscriptResult,
    TranscriptSegment,
    UpdateTranscriptRequest,
)
from app.services.audio import AudioError, probe_duration
from app.services.export import export_txt
from app.services.transcription import diarize_segments
from app.worker import process_job

router = APIRouter(prefix="/api/transcriptions", tags=["transcriptions"])


class ExportBody(BaseModel):
    format: ExportFormat = "dialogue"
    merge_adjacent: bool = True


def _get_job_row(job_id: str) -> JobRow:
    with get_session() as session:
        row = session.get(JobRow, job_id)
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return row


@router.get("", response_model=list[JobResponse])
def get_jobs():
    return list_jobs()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    row = _get_job_row(job_id)
    return job_to_dict(row)


@router.get("/{job_id}/events")
async def job_events(job_id: str):
    _get_job_row(job_id)

    async def event_stream():
        last_payload = ""
        while True:
            row = _get_job_row(job_id)
            payload = json.dumps(
                {
                    "status": row.status,
                    "stage": row.stage,
                    "message": row.message,
                    "error": row.error,
                },
                ensure_ascii=False,
            )
            if payload != last_payload:
                yield f"data: {payload}\n\n"
                last_payload = payload
            if row.status in ("done", "failed"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("", response_model=JobResponse, status_code=201)
async def create_transcription(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    job_id = new_job_id()
    dest_dir = settings.uploads_dir / job_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename

    size = 0
    with dest_path.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="File too large")
            out.write(chunk)

    try:
        duration = probe_duration(dest_path)
    except AudioError as exc:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if duration > settings.max_duration_sec:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Audio too long ({duration / 60:.1f} min). Max is 30 minutes.",
        )

    with get_session() as session:
        row = JobRow(
            id=job_id,
            status="pending",
            stage="queued",
            message="Queued",
            original_filename=file.filename,
            upload_path=str(dest_path),
        )
        session.add(row)
        session.commit()

    asyncio.get_running_loop().run_in_executor(None, process_job, job_id)
    return job_to_dict(_get_job_row(job_id))


@router.patch("/{job_id}", response_model=JobResponse)
def update_transcription(job_id: str, body: UpdateTranscriptRequest):
    row = _get_job_row(job_id)
    if row.status != "done" or not row.result_json:
        raise HTTPException(status_code=400, detail="Transcript not ready")

    data = TranscriptResult.model_validate_json(row.result_json)
    if body.speakers is not None:
        data.speakers = body.speakers
    if body.segments is not None:
        data.segments = body.segments

    with get_session() as session:
        db_row = session.get(JobRow, job_id)
        assert db_row is not None
        db_row.result_json = data.model_dump_json()
        session.commit()

    return job_to_dict(_get_job_row(job_id))


@router.post("/{job_id}/export.txt")
def export_transcription(job_id: str, body: ExportBody):
    row = _get_job_row(job_id)
    if not row.result_json:
        raise HTTPException(status_code=400, detail="No transcript")
    result = TranscriptResult.model_validate_json(row.result_json)
    text = export_txt(result, body.format, merge_adjacent=body.merge_adjacent)
    return PlainTextResponse(text, media_type="text/plain; charset=utf-8")


@router.get("/{job_id}/audio")
def get_job_audio(job_id: str):
    row = _get_job_row(job_id)
    path_str = row.audio_path or row.upload_path
    path = Path(path_str)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Audio not found")
    media = "audio/wav" if path.suffix.lower() == ".wav" else "application/octet-stream"
    return FileResponse(path, media_type=media, filename=path.name)


@router.post("/{job_id}/rediarize", response_model=JobResponse)
def rediarize(job_id: str):
    """Re-run speaker detection on an existing transcript (keeps edited text)."""
    row = _get_job_row(job_id)
    if not row.result_json:
        raise HTTPException(status_code=400, detail="No transcript to rediarize")

    data = TranscriptResult.model_validate_json(row.result_json)
    if not data.segments:
        raise HTTPException(status_code=400, detail="Empty transcript")

    wav_path = Path(row.audio_path) if row.audio_path else None
    if not wav_path or not wav_path.is_file():
        wav_path = settings.processed_dir / job_id / "audio_16k.wav"
    if not wav_path.is_file():
        raise HTTPException(status_code=400, detail="Processed audio not found")

    asr_segments = [(s.start, s.end, s.text) for s in data.segments]
    assigned, engine, note = diarize_segments(wav_path, asr_segments)

    old_speakers = data.speakers
    new_segments = []
    for seg, (_, _, _, speaker_id) in zip(data.segments, assigned):
        new_segments.append(
            {
                **seg.model_dump(),
                "speaker_id": speaker_id,
            }
        )

    speaker_ids = sorted({s["speaker_id"] for s in new_segments})
    speakers = {}
    for sid in speaker_ids:
        speakers[sid] = old_speakers.get(sid) or f"Спикер {speaker_ids.index(sid) + 1}"

    updated = TranscriptResult(
        duration_sec=data.duration_sec,
        language=data.language,
        speakers=speakers,
        segments=[TranscriptSegment.model_validate(s) for s in new_segments],
        diarization_engine=engine,
        diarization_note=note,
    )

    with get_session() as session:
        db_row = session.get(JobRow, job_id)
        assert db_row is not None
        db_row.result_json = updated.model_dump_json()
        session.commit()

    return job_to_dict(_get_job_row(job_id))


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str):
    row = _get_job_row(job_id)
    with get_session() as session:
        db_row = session.get(JobRow, job_id)
        if db_row:
            session.delete(db_row)
            session.commit()
    for p in [Path(row.upload_path), Path(row.audio_path) if row.audio_path else None]:
        if p and p.is_file():
            p.unlink(missing_ok=True)
    import shutil

    processed = settings.processed_dir / job_id
    if processed.is_dir():
        shutil.rmtree(processed, ignore_errors=True)
