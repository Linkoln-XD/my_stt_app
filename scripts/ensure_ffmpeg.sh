#!/usr/bin/env bash
# Symlink imageio-ffmpeg binary as .tools/ffmpeg/ffmpeg (GigaAM calls bare `ffmpeg`).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN_DIR="$ROOT/.tools/ffmpeg"
VENV_PY="$ROOT/backend/.venv/bin/python"

mkdir -p "$BIN_DIR"
if [[ ! -x "$VENV_PY" ]]; then
  exit 0
fi

EXE="$("$VENV_PY" -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null || true)"
if [[ -z "$EXE" || ! -f "$EXE" ]]; then
  exit 0
fi

ln -sf "$EXE" "$BIN_DIR/ffmpeg"
if [[ -f "$(dirname "$EXE")/ffprobe" ]]; then
  ln -sf "$(dirname "$EXE")/ffprobe" "$BIN_DIR/ffprobe"
fi
