from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from app.config import settings


class AudioError(Exception):
    pass


def _resolve_binary(name: str, configured: Optional[str]) -> str:
    path = _find_binary(name, configured)
    if path:
        return path
    raise AudioError(
        f"{name} не найден. Установите ffmpeg (brew install ffmpeg) "
        f"или положите бинарник в {settings.bundled_ffmpeg_dir}/{name}"
    )


def _find_binary(name: str, configured: Optional[str]) -> Optional[str]:
    if configured:
        path = Path(configured)
        if path.is_file():
            return str(path)
        return None

    bundled = settings.bundled_ffmpeg_dir / name
    if bundled.is_file():
        return str(bundled)

    found = shutil.which(name)
    if found:
        return found

    if name == "ffmpeg":
        try:
            import imageio_ffmpeg

            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if Path(exe).is_file():
                return exe
        except ImportError:
            pass

    if name == "ffprobe":
        ffmpeg_path = _find_binary("ffmpeg", settings.ffmpeg_path)
        if ffmpeg_path:
            sibling = Path(ffmpeg_path).parent / "ffprobe"
            if sibling.is_file():
                return str(sibling)

    return None


def _ffmpeg() -> str:
    return _resolve_binary("ffmpeg", settings.ffmpeg_path)


def _ffprobe_optional() -> Optional[str]:
    return _find_binary("ffprobe", settings.ffprobe_path)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _ffmpeg_probe_text(path: Path) -> str:
    proc = _run([_ffmpeg(), "-i", str(path), "-f", "null", "-"])
    return (proc.stderr or "") + (proc.stdout or "")


def _probe_with_ffprobe(path: Path, ffprobe: str) -> float:
    proc = _run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ]
    )
    if proc.returncode != 0:
        raise AudioError(proc.stderr.strip() or "ffprobe failed")
    try:
        data = json.loads(proc.stdout)
        return float(data["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AudioError("Could not read audio duration") from exc


def _probe_with_ffmpeg(path: Path) -> float:
    text = _ffmpeg_probe_text(path)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if not match:
        raise AudioError("Не удалось определить длительность файла")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def probe_duration(path: Path) -> float:
    ffprobe = _ffprobe_optional()
    if ffprobe:
        try:
            return _probe_with_ffprobe(path, ffprobe)
        except AudioError:
            pass
    return _probe_with_ffmpeg(path)


_AUDIO_STREAM_RE = re.compile(r"Stream\s+#\d+:\d+[^\n]*:\s*Audio:", re.IGNORECASE)


def _assert_has_audio_ffprobe(path: Path, ffprobe: str) -> None:
    proc = _run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ]
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise AudioError(
            "В файле не найдена аудиодорожка. Загрузите файл с записью звука "
            "(аудио или видео с аудио: AVI, MKV, MP4 и т.д.)."
        )


def _assert_has_audio_ffmpeg(path: Path) -> None:
    text = _ffmpeg_probe_text(path)
    if _AUDIO_STREAM_RE.search(text):
        return
    raise AudioError(
        "В файле не найдена аудиодорожка. Загрузите файл с записью звука "
        "(аудио или видео с аудио: AVI, MKV, MP4 и т.д.)."
    )


def assert_has_audio(path: Path) -> None:
    """Reject containers without an audio stream (e.g. silent video)."""
    ffprobe = _ffprobe_optional()
    if ffprobe:
        _assert_has_audio_ffprobe(path, ffprobe)
    else:
        _assert_has_audio_ffmpeg(path)


def to_mono_wav(source: Path, dest: Path, sample_rate: int = 16000) -> None:
    """Extract first audio stream; works for audio and video containers (AVI, MKV, …)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = _run(
        [
            _ffmpeg(),
            "-y",
            "-i",
            str(source),
            "-vn",
            "-map",
            "0:a:0?",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )
    if proc.returncode != 0:
        err = proc.stderr.strip() or "ffmpeg conversion failed"
        if "does not contain any stream" in err or "Stream map" in err:
            raise AudioError(
                "Не удалось извлечь аудио. Проверьте, что в файле есть звуковая дорожка."
            ) from None
        raise AudioError(err)
