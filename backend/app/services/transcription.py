from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.services.system_settings import get_max_duration_sec, resolve_whisper_model_name
from app.models.schemas import TranscriptResult, TranscriptSegment
from app.services.audio import assert_has_audio, probe_duration, to_mono_wav
from app.services.diarization import diarize_by_segments_resemblyzer, run_pyannote

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str], None]

_whisper_model = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        model_name = resolve_whisper_model_name()
        _whisper_model = WhisperModel(
            model_name,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    return _whisper_model


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def _assign_speakers(
    asr_segments: list[tuple[float, float, str]],
    diarization_turns: list[tuple[float, float, str]],
) -> list[tuple[float, float, str, str]]:
    assigned: list[tuple[float, float, str, str]] = []
    for start, end, text in asr_segments:
        mid = (start + end) / 2.0
        best_speaker: str | None = None
        best_overlap = 0.0

        for d_start, d_end, speaker in diarization_turns:
            ov = _overlap(start, end, d_start, d_end)
            if ov > best_overlap:
                best_overlap = ov
                best_speaker = speaker

        if best_speaker is None or best_overlap == 0.0:
            for d_start, d_end, speaker in diarization_turns:
                if d_start <= mid <= d_end:
                    best_speaker = speaker
                    break

        if best_speaker is None and diarization_turns:
            nearest = min(
                diarization_turns,
                key=lambda t: abs((t[0] + t[1]) / 2.0 - mid),
            )
            best_speaker = nearest[2]

        assigned.append((start, end, text, best_speaker or "SPEAKER_00"))
    return assigned


def _run_asr(wav_path: Path) -> tuple[list[tuple[float, float, str]], str | None]:
    model = _get_whisper()
    segments_iter, info = model.transcribe(
        str(wav_path),
        language=None,
        vad_filter=True,
        beam_size=5,
    )
    segments: list[tuple[float, float, str]] = []
    for seg in segments_iter:
        text = (seg.text or "").strip()
        if text:
            segments.append((seg.start, seg.end, text))
    language = getattr(info, "language", None)
    return segments, language


def diarize_segments(
    wav_path: Path,
    asr_segments: list[tuple[float, float, str]],
) -> tuple[list[tuple[float, float, str, str]], str, str | None]:
    """
    Returns (assigned segments, engine name, optional user-facing note).
    """
    backend = settings.diarization_backend.lower()
    pyannote_error: str | None = None

    if backend in ("auto", "pyannote") and settings.hf_token:
        try:
            turns = run_pyannote(wav_path)
            if turns:
                assigned = _assign_speakers(asr_segments, turns)
                speakers = {row[3] for row in assigned}
                if len(speakers) >= 2:
                    return assigned, "pyannote", None
                pyannote_error = "pyannote detected only one speaker"
            else:
                pyannote_error = "pyannote returned no speaker turns"
        except Exception as exc:
            pyannote_error = str(exc)
            logger.warning("Pyannote diarization failed: %s", exc)

    if backend in ("auto", "resemblyzer"):
        assigned = diarize_by_segments_resemblyzer(wav_path, asr_segments)
        speakers = {row[3] for row in assigned}
        note = None
        if len(speakers) < 2:
            note = "Обнаружен один спикер"
        if pyannote_error and backend == "auto":
            note = (
                f"Pyannote unavailable ({pyannote_error}). "
                "Used local Resemblyzer clustering."
            )
        return assigned, "resemblyzer", note

    note = pyannote_error or "Configure HF_TOKEN for pyannote or set DIARIZATION_BACKEND=resemblyzer."
    return [(s, e, t, "SPEAKER_00") for s, e, t in asr_segments], "none", note


def _build_result(
    assigned: list[tuple[float, float, str, str]],
    duration_sec: float,
    language: str | None,
    diarization_engine: str,
    diarization_note: str | None,
) -> TranscriptResult:
    speaker_ids = sorted({row[3] for row in assigned})
    speakers = {sid: f"Спикер {idx + 1}" for idx, sid in enumerate(speaker_ids)}
    segments = [
        TranscriptSegment(
            id=str(uuid4()),
            speaker_id=speaker_id,
            start=start,
            end=end,
            text=text,
        )
        for start, end, text, speaker_id in assigned
    ]
    return TranscriptResult(
        duration_sec=duration_sec,
        language=language,
        speakers=speakers,
        segments=segments,
        diarization_engine=diarization_engine,
        diarization_note=diarization_note,
    )


def transcribe_file(
    source_path: Path,
    work_dir: Path,
    on_progress: ProgressCallback | None = None,
) -> TranscriptResult:
    def progress(stage: str, message: str) -> None:
        if on_progress:
            on_progress(stage, message)

    progress("prepare", "Checking audio…")
    assert_has_audio(source_path)
    duration = probe_duration(source_path)
    max_sec = get_max_duration_sec()
    if duration > max_sec:
        raise ValueError(
            f"Audio is too long ({duration / 60:.1f} min). Maximum is {max_sec / 60:.0f} min."
        )

    wav_path = work_dir / "audio_16k.wav"
    progress("prepare", "Converting audio to 16 kHz mono…")
    to_mono_wav(source_path, wav_path)

    progress("asr", "Recognizing speech (this may take a while)…")
    asr_segments, language = _run_asr(wav_path)
    if not asr_segments:
        return TranscriptResult(
            duration_sec=duration,
            language=language,
            speakers={},
            segments=[],
            diarization_engine="none",
            diarization_note=None,
        )

    progress("diarization", "Detecting speakers…")
    assigned, engine, note = diarize_segments(wav_path, asr_segments)
    if note:
        progress("diarization", note)

    progress("merge", "Building transcript…")
    return _build_result(assigned, duration, language, engine, note)
