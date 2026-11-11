from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from app.services.system_settings import resolve_whisper_model_name, resolve_whisper_runtime
from app.services.whisper_vad import whisper_vad_filter_enabled

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str], None]

_whisper_model = None
_whisper_loaded_key: tuple[str, str, str] | None = None


class WhisperModelDownloadError(RuntimeError):
    """Raised when Whisper weights cannot be downloaded or loaded from the network."""


def _is_model_download_error(exc: BaseException) -> bool:
    name = type(exc).__name__
    msg = str(exc).lower()
    if name in {"ProxyError", "ConnectError", "ConnectTimeout", "ReadTimeout", "LocalEntryNotFoundError"}:
        return True
    needles = (
        "403",
        "401",
        "forbidden",
        "proxy",
        "huggingface",
        "snapshot_download",
        "failed to establish",
        "connection",
        "timed out",
        "name or service not known",
        "temporary failure in name resolution",
    )
    return any(n in msg for n in needles)


def get_whisper_model(on_progress: ProgressCallback | None = None):
    """Load (or reload) Whisper for the current admin model tier and device."""
    global _whisper_model, _whisper_loaded_key
    model_name = resolve_whisper_model_name()
    device, compute_type = resolve_whisper_runtime()
    key = (model_name, device, compute_type)
    if _whisper_model is None or _whisper_loaded_key != key:
        if on_progress:
            on_progress(
                "model_load",
                f"Загрузка Whisper «{model_name}» ({device})… Первый запуск может скачать веса с Hugging Face.",
            )
        from faster_whisper import WhisperModel

        logger.info(
            "Loading Whisper model %s (device=%s, compute_type=%s)",
            model_name,
            device,
            compute_type,
        )
        try:
            _whisper_model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
            )
        except Exception as exc:
            if _is_model_download_error(exc):
                raise WhisperModelDownloadError(
                    f"Не удалось скачать модель Whisper «{model_name}» (сеть/прокси или нет кэша). "
                    "Скачайте заранее: cd backend && source .venv/bin/activate && "
                    "python scripts/download_models.py --whisper-only "
                    "или проверьте доступ к huggingface.co."
                ) from exc
            raise
        _whisper_loaded_key = key
    return _whisper_model


def run_whisper_asr(
    wav_path: Path,
    on_progress: ProgressCallback | None = None,
) -> tuple[list[tuple[float, float, str]], str | None]:
    model = get_whisper_model(on_progress)
    if on_progress:
        on_progress("asr", "Распознавание речи (на CPU это может занять много времени)…")
    segments_iter, info = model.transcribe(
        str(wav_path),
        language=None,
        vad_filter=whisper_vad_filter_enabled(),
        beam_size=5,
    )
    segments: list[tuple[float, float, str]] = []
    for seg in segments_iter:
        text = (seg.text or "").strip()
        if text:
            segments.append((seg.start, seg.end, text))
    language = getattr(info, "language", None)
    return segments, language
