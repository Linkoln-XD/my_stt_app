#!/usr/bin/env python3
"""Download Whisper and pyannote weights (run once while online)."""

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import settings  # noqa: E402


def main() -> None:
    token = settings.hf_token or os.environ.get("HF_TOKEN")
    if not token:
        print(
            "Set HF_TOKEN in backend/.env (Hugging Face token with access to pyannote models).\n"
            "Accept licenses at:\n"
            "  https://huggingface.co/pyannote/speaker-diarization-3.1\n"
            "  https://huggingface.co/pyannote/segmentation-3.0",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Downloading Whisper model: {settings.whisper_model} …")
    from faster_whisper import WhisperModel

    WhisperModel(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )
    print("Whisper ready.")

    print("Downloading pyannote speaker-diarization-3.1 …")
    from pyannote.audio import Pipeline

    Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", token=token)
    print("Diarization pipeline ready.")
    print("All models cached. You can run offline after this.")


if __name__ == "__main__":
    main()
