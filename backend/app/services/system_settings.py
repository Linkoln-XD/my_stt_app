from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.config import settings
from app.services.device_info import GpuBackend, detect_gpu_backend, gpu_available

ModelTier = Literal["light", "medium", "heavy"]
InferenceDevice = Literal["cpu", "gpu"]

MIN_DURATION_MINUTES = 10
MAX_DURATION_MINUTES = 120

# Admin UI tiers → faster-whisper model ids
TIER_TO_WHISPER: dict[ModelTier, str] = {
    "light": "small",
    "medium": "medium",
    "heavy": "large-v3",
}

_lock = threading.Lock()


class SystemSettings(BaseModel):
    model_tier: ModelTier = "medium"
    inference_device: InferenceDevice = "cpu"
    max_duration_minutes: int = Field(default=30, ge=MIN_DURATION_MINUTES, le=MAX_DURATION_MINUTES)


def _clamp_duration_minutes(minutes: int) -> int:
    return max(MIN_DURATION_MINUTES, min(MAX_DURATION_MINUTES, minutes))


def _normalize_settings(data: SystemSettings) -> SystemSettings:
    updates: dict = {}
    clamped = _clamp_duration_minutes(data.max_duration_minutes)
    if clamped != data.max_duration_minutes:
        updates["max_duration_minutes"] = clamped
    # GPU selection only sticks when a backend is actually available.
    if data.inference_device == "gpu" and not gpu_available():
        updates["inference_device"] = "cpu"
    if updates:
        return data.model_copy(update=updates)
    return data


def _settings_path() -> Path:
    return settings.data_dir / "system_settings.json"


def _default_settings() -> SystemSettings:
    default_min = _clamp_duration_minutes(int(settings.max_duration_sec // 60))
    return SystemSettings(
        model_tier="medium",
        inference_device="cpu",
        max_duration_minutes=default_min,
    )


def load_system_settings() -> SystemSettings:
    path = _settings_path()
    with _lock:
        if not path.is_file():
            data = _default_settings()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data.model_dump_json(indent=2), encoding="utf-8")
            return data
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and "max_duration_minutes" in payload:
                payload["max_duration_minutes"] = _clamp_duration_minutes(
                    int(payload["max_duration_minutes"]),
                )
            raw = SystemSettings.model_validate(payload)
            return _normalize_settings(raw)
        except Exception:
            return _default_settings()


def save_system_settings(data: SystemSettings) -> SystemSettings:
    data = _normalize_settings(data)
    path = _settings_path()
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data.model_dump_json(indent=2), encoding="utf-8")
    return data


def get_max_duration_sec() -> float:
    return float(load_system_settings().max_duration_minutes * 60)


def resolve_whisper_model_name() -> str:
    """Whisper model id for the current admin model_tier (light/medium/heavy)."""
    tier = load_system_settings().model_tier
    return TIER_TO_WHISPER.get(tier, TIER_TO_WHISPER["medium"])


def resolve_whisper_runtime() -> tuple[str, str]:
    """
    Return (device, compute_type) for faster-whisper.

    CTranslate2 supports cpu/cuda only — on Apple MPS Whisper stays on CPU.
    """
    s = load_system_settings()
    if s.inference_device != "gpu":
        return "cpu", settings.whisper_compute_type

    backend = detect_gpu_backend()
    if backend == "cuda":
        return "cuda", "float16"
    # mps or none: Whisper cannot use Metal via faster-whisper
    return "cpu", settings.whisper_compute_type


def resolve_diarization_torch_device() -> str:
    """Torch device string for pyannote (cpu / cuda / mps)."""
    s = load_system_settings()
    if s.inference_device != "gpu":
        return "cpu"

    backend = detect_gpu_backend()
    if backend == "cuda":
        return "cuda"
    if backend == "mps":
        return "mps"
    return "cpu"


def public_gpu_info() -> tuple[bool, GpuBackend]:
    backend = detect_gpu_backend()
    return backend != "none", backend
