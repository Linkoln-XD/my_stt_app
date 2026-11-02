#!/usr/bin/env python3
"""Download Whisper (all admin tiers) and optional pyannote weights (run once while online)."""

import argparse
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import settings  # noqa: E402
from app.services.system_settings import TIER_TO_WHISPER  # noqa: E402


def _download_whisper(model_name: str) -> None:
    from faster_whisper import WhisperModel

    print(f"Downloading Whisper model: {model_name} …")
    WhisperModel(
        model_name,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )
    print(f"Whisper {model_name} ready.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--whisper-only",
        action="store_true",
        help="Skip pyannote (no HF_TOKEN required).",
    )
    parser.add_argument(
        "--tiers",
        nargs="+",
        choices=sorted(TIER_TO_WHISPER.keys()),
        default=sorted(TIER_TO_WHISPER.keys()),
        help="Admin tiers to cache (default: all).",
    )
    args = parser.parse_args()

    seen: set[str] = set()
    for tier in args.tiers:
        name = TIER_TO_WHISPER[tier]
        if name in seen:
            continue
        seen.add(name)
        _download_whisper(name)

    # Also cache WHISPER_MODEL from .env if it differs (CLI / legacy).
    if settings.whisper_model not in seen:
        _download_whisper(settings.whisper_model)

    if args.whisper_only:
        print("Whisper models cached. You can run offline for ASR.")
        return

    token = settings.hf_token or os.environ.get("HF_TOKEN")
    if not token:
        print(
            "HF_TOKEN not set — skipping pyannote.\n"
            "Whisper is ready. For pyannote later: set HF_TOKEN, accept licenses, re-run without --whisper-only.\n"
            "  https://huggingface.co/pyannote/speaker-diarization-3.1\n"
            "  https://huggingface.co/pyannote/segmentation-3.0",
            file=sys.stderr,
        )
        return

    print("Downloading pyannote speaker-diarization-3.1 …")
    from pyannote.audio import Pipeline

    Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", token=token)
    print("Diarization pipeline ready.")
    print("All models cached. You can run offline after this.")


if __name__ == "__main__":
    main()
