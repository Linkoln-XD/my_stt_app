from __future__ import annotations

import logging
from pathlib import Path

from app.services.whisper_vad import whisper_vad_filter_enabled

logger = logging.getLogger(__name__)

_probe_model = None


def _get_probe_model():
    global _probe_model
    if _probe_model is None:
        from faster_whisper import WhisperModel

        _probe_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _probe_model


def probe_speech_language(wav_path: Path, max_seconds: float = 60.0) -> str | None:
    """Detect language on a short prefix via Whisper tiny (CPU)."""
    model = _get_probe_model()
    try:
        _segments, info = model.transcribe(
            str(wav_path),
            language=None,
            vad_filter=whisper_vad_filter_enabled(),
            beam_size=1,
            duration=max_seconds,
        )
        # Consume iterator so detection runs.
        for _ in _segments:
            break
    except Exception as exc:
        logger.warning("Language probe failed: %s", exc)
        return None
    lang = getattr(info, "language", None)
    if isinstance(lang, str) and lang.strip():
        return lang.strip().lower()
    return None
