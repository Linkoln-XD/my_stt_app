from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.config import settings

ModelTier = Literal["light", "medium", "heavy"]

ALLOWED_DURATION_MINUTES = (5, 10, 15, 30, 45, 60)

_lock = threading.Lock()


class SystemSettings(BaseModel):
    model_tier: ModelTier = "medium"
    max_duration_minutes: int = Field(default=30, ge=1, le=120)


def _settings_path() -> Path:
    return settings.data_dir / "system_settings.json"


def _default_settings() -> SystemSettings:
    default_min = int(settings.max_duration_sec // 60)
    if default_min not in ALLOWED_DURATION_MINUTES:
        default_min = 30
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
            return SystemSettings.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return _default_settings()


def save_system_settings(data: SystemSettings) -> SystemSettings:
    if data.max_duration_minutes not in ALLOWED_DURATION_MINUTES:
        raise ValueError(
            f"max_duration_minutes must be one of {list(ALLOWED_DURATION_MINUTES)}"
        )
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
