#!/usr/bin/env bash
# Quick checks after docker compose up (run from repo root).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT="${STT_PORT:-8080}"
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
  PORT="${STT_PORT:-8080}"
fi

fail=0
warn() { echo "⚠ $*"; }
ok() { echo "✓ $*"; }
bad() { echo "✗ $*"; fail=1; }

command -v docker >/dev/null && ok "docker installed" || bad "docker not found"
docker compose version >/dev/null 2>&1 && ok "docker compose available" || bad "docker compose not found"

[[ -f backend/.env ]] && ok "backend/.env exists" || bad "missing backend/.env (cp backend/.env.example backend/.env)"

if [[ -f .env ]]; then
  ok "root .env exists (STT_PORT=${PORT})"
else
  warn "no root .env — using default STT_PORT=8080 (cp compose.env.example .env)"
fi

HF="${STT_HF_CACHE_HOST:-$ROOT/docker-bundled-models/huggingface}"
if [[ -d "$HF/hub/models--Systran--faster-whisper-medium" ]]; then
  ok "Whisper medium cache present at $HF"
else
  warn "Whisper cache not found — first transcription will download ~1.5 GB (needs internet)"
  mkdir -p "$HF"
fi

if docker compose ps --status running 2>/dev/null | grep -q stt; then
  ok "container is running"
  if curl -sf "http://127.0.0.1:${PORT}/api/health" | grep -q '"ok"'; then
    ok "health OK → http://127.0.0.1:${PORT}/"
  else
    bad "health check failed on port ${PORT}"
  fi
else
  warn "container not running — start with: docker compose up -d"
fi

exit "$fail"
