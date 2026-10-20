#!/usr/bin/env bash
# Copy local Hugging Face cache (Whisper etc.) into docker-bundled-models/ for Docker build.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-${HF_HOME:-$HOME/.cache/huggingface}}"
DEST="$ROOT/docker-bundled-models/huggingface"

if [[ ! -d "$SRC" ]]; then
  echo "HF cache not found: $SRC" >&2
  echo "Run a local transcription once, or set HF_HOME." >&2
  exit 1
fi

mkdir -p "$DEST"
echo "Copying $SRC -> $DEST (this may take a few minutes)…"
if command -v rsync >/dev/null; then
  rsync -a --delete "${SRC}/" "${DEST}/"
else
  rm -rf "${DEST:?}/"*
  cp -a "${SRC}/." "${DEST}/"
fi
du -sh "$DEST"
echo "Done. Start or restart: docker compose up -d"
