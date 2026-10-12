#!/usr/bin/env python3
"""CLI: transcribe a local audio file (same pipeline as the API)."""

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root: python backend/scripts/transcribe_cli.py
ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services.export import export_txt  # noqa: E402
from app.models.schemas import TranscriptResult  # noqa: E402
from app.services.transcription import transcribe_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe audio with speaker diarization")
    parser.add_argument("audio", type=Path, help="Path to audio file")
    parser.add_argument("-o", "--output", type=Path, help="Write JSON result here")
    parser.add_argument("--txt", type=Path, help="Write plain text export here")
    parser.add_argument(
        "--format",
        choices=("dialogue", "timestamps"),
        default="dialogue",
        help="TXT export format",
    )
    args = parser.parse_args()

    if not args.audio.is_file():
        print(f"File not found: {args.audio}", file=sys.stderr)
        sys.exit(1)

    work = ROOT / "data" / "cli_runs" / args.audio.stem

    def on_progress(stage: str, message: str) -> None:
        print(f"[{stage}] {message}", flush=True)

    result = transcribe_file(args.audio, work, on_progress=on_progress)
    payload = result.model_dump()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote JSON: {args.output}")

    if args.txt:
        txt = export_txt(TranscriptResult.model_validate(payload), args.format)
        args.txt.write_text(txt, encoding="utf-8")
        print(f"Wrote TXT: {args.txt}")

    if not args.output and not args.txt:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
