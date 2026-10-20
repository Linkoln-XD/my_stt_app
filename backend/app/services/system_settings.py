from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.config import settings

ModelTier = Literal["light", "medium", "heavy"]

MIN_DURATION_MINUTES = 10
MAX_DURATION_MINUTES = 120

_lock = threading.Lock()


class SystemSettings(BaseModel):
    model_tier: ModelTier = "medium"
    max_duration_minutes: int = Field(default=30, ge=MIN_DURATION_MINUTES, le=MAX_DURATION_MINUTES)


def _clamp_duration_minutes(minutes: int) -> int:
    return max(MIN_DURATION_MINUTES, min(MAX_DURATION_MINUTES, minutes))


def _normalize_settings(data: SystemSettings) -> SystemSettings:
    clamped = _clamp_duration_minutes(data.max_duration_minutes)
    if clamped != data.max_duration_minutes:
        return data.model_copy(update={"max_duration_minutes": clamped})
    return data


def _settings_path() -> Path:
    return settings.data_dir / "system_settings.json"


def _default_settings() -> SystemSettings:
    default_min = _clamp_duration_minutes(int(settings.max_duration_sec // 60))
    return SystemSettings(model_tier="medium", max_duration_minutes=default_min)


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
    """Formal tier in UI; actual Whisper weights stay on configured default (medium)."""
    _ = load_system_settings().model_tier
    return settings.whisper_model
