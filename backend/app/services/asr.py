from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.services.asr_errors import AsrLanguageUnsupportedError
from app.services.gigaam_asr import run_gigaam_asr
from app.services.language_probe import probe_speech_language
from app.services.system_settings import load_system_settings
from app.services.whisper_asr import run_whisper_asr

ProgressCallback = Callable[[str, str], None]


def run_asr(
    wav_path: Path,
    duration_sec: float,
    on_progress: ProgressCallback | None = None,
) -> tuple[list[tuple[float, float, str]], str | None]:
    engine = load_system_settings().asr_engine
    if engine == "gigaam":
        if on_progress:
            on_progress("asr", "Проверка языка (короткий анализ)…")
        detected = probe_speech_language(wav_path)
        if detected and detected != "ru":
            raise AsrLanguageUnsupportedError(
                f"GigaAM поддерживает только русский язык (обнаружено: {detected}). "
                "Переключите движок на Whisper в настройках администратора."
            )
        return run_gigaam_asr(wav_path, duration_sec, on_progress)
    return run_whisper_asr(wav_path, on_progress)
