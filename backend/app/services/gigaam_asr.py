from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from pathlib import Path

from app.config import settings
from app.services.asr_errors import GigaamModelDownloadError, GigaamRequiresTokenError
from app.services.gigaam_patch import apply_gigaam_patches
from app.services.system_settings import GIGAAM_MODEL_ID, resolve_gigaam_torch_device

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str], None]

_gigaam_model = None
_gigaam_loaded_key: str | None = None

# GigaAM refuses single-shot transcribe above ~25 s of audio.
GIGAAM_SHORT_MAX_SEC = 25.0


def _is_model_download_error(exc: BaseException) -> bool:
    name = type(exc).__name__
    msg = str(exc).lower()
    if name in {"ProxyError", "ConnectError", "ConnectTimeout", "ReadTimeout", "LocalEntryNotFoundError"}:
        return True
    needles = (
        "download",
        "403",
        "401",
        "forbidden",
        "connection",
        "timed out",
        "checksum",
        "ssl",
        "certificate",
    )
    return any(n in msg for n in needles)


def _ensure_hf_token_for_longform(duration_sec: float) -> None:
    if duration_sec <= GIGAAM_SHORT_MAX_SEC:
        return
    token = settings.hf_token or os.environ.get("HF_TOKEN")
    if not token:
        raise GigaamRequiresTokenError(
            "Для длинных файлов GigaAM нужен HF_TOKEN и доступ к pyannote/segmentation-3.0 "
            "(сегментация речи). Установите HF_TOKEN в .env или используйте Whisper."
        )
    os.environ.setdefault("HF_TOKEN", token)


def get_gigaam_model(on_progress: ProgressCallback | None = None):
    global _gigaam_model, _gigaam_loaded_key
    device = resolve_gigaam_torch_device()
    if _gigaam_model is None or _gigaam_loaded_key != device:
        try:
            import gigaam
        except ImportError as exc:
            import sys

            if sys.version_info < (3, 10):
                raise GigaamModelDownloadError(
                    "GigaAM v3 требует Python 3.10 или новее. Сейчас "
                    f"{sys.version_info.major}.{sys.version_info.minor}. "
                    "Установите Python 3.12 (brew install python@3.12), удалите backend/.venv "
                    "и снова запустите ./scripts/run_backend.sh — или выберите Whisper в админке."
                ) from exc
            raise GigaamModelDownloadError(
                "Пакет gigaam не установлен: pip install -r requirements-gigaam.txt "
                "или пересоберите Docker-образ."
            ) from exc
        apply_gigaam_patches()
        logger.info("Loading GigaAM %s (device=%s)", GIGAAM_MODEL_ID, device)
        stop = threading.Event()

        def _pulse() -> None:
            while not stop.wait(12.0):
                if on_progress:
                    on_progress(
                        "model_load",
                        "Скачивание или загрузка GigaAM… Первый запуск на CPU может занять 10–20 минут.",
                    )

        pulse = threading.Thread(target=_pulse, name="gigaam-load-pulse", daemon=True)
        try:
            if on_progress:
                on_progress(
                    "model_load",
                    f"Загрузка GigaAM ({GIGAAM_MODEL_ID}, {device})… Первый запуск скачивает веса.",
                )
            pulse.start()
            fp16 = device == "cuda"
            _gigaam_model = gigaam.load_model(
                GIGAAM_MODEL_ID,
                device=device,
                fp16_encoder=fp16,
                use_flash=False,
            )
        except Exception as exc:
            msg = str(exc)
            if "not found" in msg.lower() and "available model names" in msg.lower():
                raise GigaamModelDownloadError(
                    f"Установлен устаревший пакет gigaam (нет {GIGAAM_MODEL_ID}). "
                    "Переустановите: pip install -r requirements.txt "
                    "или пересоберите Docker-образ."
                ) from exc
            if _is_model_download_error(exc):
                hint = (
                    "Проверьте сеть и кэш: python scripts/download_models.py --gigaam"
                )
                if "certificate" in msg.lower():
                    hint = (
                        "CDN Сбера (cdn.chatwm.opensmodel.sberdevices.ru) отдаёт просроченный SSL-сертификат; "
                        "обычно помогает повторить задачу (в приложении включён обход только для этого CDN) "
                        "или: python scripts/download_models.py --gigaam"
                    )
                raise GigaamModelDownloadError(
                    f"Не удалось скачать или загрузить GigaAM ({GIGAAM_MODEL_ID}). {hint}"
                ) from exc
            raise
        finally:
            stop.set()
            pulse.join(timeout=0.2)
        _gigaam_loaded_key = device
    return _gigaam_model


def run_gigaam_asr(
    wav_path: Path,
    duration_sec: float,
    on_progress: ProgressCallback | None = None,
) -> tuple[list[tuple[float, float, str]], str | None]:
    apply_gigaam_patches()
    _ensure_hf_token_for_longform(duration_sec)
    model = get_gigaam_model(on_progress)
    if on_progress:
        on_progress(
            "asr",
            "Распознавание речи GigaAM v3 (русский, с пунктуацией)…",
        )
    try:
        if duration_sec <= GIGAAM_SHORT_MAX_SEC:
            result = model.transcribe(str(wav_path))
            text = (getattr(result, "text", None) or "").strip()
            if not text:
                return [], "ru"
            end = duration_sec if duration_sec > 0 else GIGAAM_SHORT_MAX_SEC
            return [(0.0, end, text)], "ru"

        longform = model.transcribe_longform(str(wav_path))
        segments: list[tuple[float, float, str]] = []
        for seg in longform.segments:
            text = (getattr(seg, "text", None) or "").strip()
            if text:
                segments.append((float(seg.start), float(seg.end), text))
        return segments, "ru"
    except GigaamRequiresTokenError:
        raise
    except Exception as exc:
        msg = str(exc).lower()
        if "hf_token" in msg or "segmentation" in msg:
            raise GigaamRequiresTokenError(
                "Для GigaAM на длинных файлах нужен HF_TOKEN и модель pyannote/segmentation-3.0."
            ) from exc
        if _is_model_download_error(exc):
            raise GigaamModelDownloadError(str(exc)) from exc
        raise
