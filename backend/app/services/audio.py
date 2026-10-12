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
    if configured:
        path = Path(configured)
        if path.is_file():
            return str(path)
        raise AudioError(f"Configured {name} path not found: {configured}")

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

    raise AudioError(
        f"{name} не найден. Установите ffmpeg (brew install ffmpeg) "
        f"или положите бинарник в {settings.bundled_ffmpeg_dir}/{name}"
    )


def _ffmpeg() -> str:
    return _resolve_binary("ffmpeg", settings.ffmpeg_path)


def _ffprobe() -> str:
    return _resolve_binary("ffprobe", settings.ffprobe_path)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _probe_with_ffprobe(path: Path) -> float:
    proc = _run(
        [
            _ffprobe(),
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
    proc = _run([_ffmpeg(), "-i", str(path), "-f", "null", "-"])
    text = (proc.stderr or "") + (proc.stdout or "")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if not match:
        raise AudioError("Could not read audio duration (ffmpeg)")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def probe_duration(path: Path) -> float:
    try:
        return _probe_with_ffprobe(path)
    except AudioError:
        return _probe_with_ffmpeg(path)


def to_mono_wav(source: Path, dest: Path, sample_rate: int = 16000) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = _run(
        [
            _ffmpeg(),
            "-y",
            "-i",
            str(source),
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
        raise AudioError(proc.stderr.strip() or "ffmpeg conversion failed")
