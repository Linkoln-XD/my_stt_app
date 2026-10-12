from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    hf_token: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"),
    )
    diarization_backend: str = "auto"  # auto | pyannote | resemblyzer
    diarization_device: str = "cpu"  # pyannote: cpu recommended on Mac
    whisper_model: str = "medium"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    max_duration_sec: float = 30 * 60
    max_upload_bytes: int = 500 * 1024 * 1024
    ffmpeg_path: Optional[str] = None
    ffprobe_path: Optional[str] = None

    @property
    def bundled_ffmpeg_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / ".tools" / "ffmpeg"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "jobs.db"


settings = Settings()
