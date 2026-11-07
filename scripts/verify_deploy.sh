#!/usr/bin/env bash
# Checks after the container is up. Run from anywhere; the script cds to the repo root.
# CPU image:  ./scripts/verify_deploy.sh
# GPU image:  ./scripts/verify_deploy.sh --gpu
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

GPU=0
COMPOSE_FILE="docker-compose.yml"
if [[ "${1:-}" == "--gpu" ]]; then
  GPU=1
  COMPOSE_FILE="docker-compose.gpu.yml"
elif [[ -n "${1:-}" ]]; then
  echo "Usage: ./scripts/verify_deploy.sh [--gpu]" >&2
  exit 2
fi

PORT="${STT_PORT:-8080}"
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
  PORT="${STT_PORT:-8080}"
fi

fail=0
warn() { echo "⚠ $*"; }
ok() { echo "✓ $*"; }
bad() { echo "✗ $*"; fail=1; }

command -v docker >/dev/null && ok "docker installed" || bad "docker not found"
docker compose version >/dev/null 2>&1 && ok "docker compose available" || bad "docker compose not found"

if [[ "$GPU" -eq 1 ]]; then
  [[ -f Dockerfile.gpu && -f docker-compose.gpu.yml ]] && ok "GPU compose files present" || bad "GPU compose files missing"
fi

if [[ -f backend/.env ]]; then
  ok "backend/.env exists"
  admin_pass="$(
    awk -F= '
      /^[[:space:]]*ADMIN_PASSWORD=/ {
        val = $0
        sub(/^[^=]*=/, "", val)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", val)
        gsub(/^["'\'']|["'\'']$/, "", val)
        print val
        exit
      }
    ' backend/.env
  )"
  if [[ -z "$admin_pass" || "$admin_pass" == "admin" ]]; then
    bad "ADMIN_PASSWORD in backend/.env is still the default. Set a real password, then: docker compose -f ${COMPOSE_FILE} up -d --force-recreate"
  else
    ok "ADMIN_PASSWORD is not the default"
  fi
else
  bad "missing backend/.env (cp backend/.env.example backend/.env and set ADMIN_PASSWORD)"
fi

if [[ -f .env ]]; then
  ok "root .env exists (STT_PORT=${PORT})"
else
  warn "no root .env — using STT_PORT=8080 (cp compose.env.example .env)"
fi

HF="${STT_HF_CACHE_HOST:-$ROOT/docker-bundled-models/huggingface}"
if [[ -d "$HF/hub/models--Systran--faster-whisper-medium" ]]; then
  ok "Whisper medium cache present at $HF"
else
  warn "Whisper cache not found — the first transcription downloads the model (needs internet)"
  mkdir -p "$HF"
fi

if docker compose -f "$COMPOSE_FILE" ps --status running 2>/dev/null | grep -q stt; then
  ok "container is running"
  if curl -sf "http://127.0.0.1:${PORT}/api/health" | grep -q '"ok"'; then
    ok "health OK → http://127.0.0.1:${PORT}/"
  else
    bad "health check failed on port ${PORT}"
  fi
  if [[ "$GPU" -eq 1 ]]; then
    body="$(curl -sf "http://127.0.0.1:${PORT}/api/settings/public" || true)"
    if [[ -z "$body" ]]; then
      bad "GET /api/settings/public failed"
    elif gpu_report="$(BODY="$body" python3 - <<'PY'
import json, os, sys
try:
    data = json.loads(os.environ["BODY"])
except json.JSONDecodeError as exc:
    print(f"invalid json: {exc}")
    sys.exit(2)
available = data.get("gpu_available") is True
backend = data.get("gpu_backend")
device = data.get("inference_device")
if not available or backend != "cuda":
    print(f"gpu_available={data.get('gpu_available')} gpu_backend={backend} inference_device={device}")
    sys.exit(1)
print(device or "")
PY
)"; then
      ok "NVIDIA CUDA is visible in the container"
      if [[ "$gpu_report" == "gpu" ]]; then
        ok "inference device is gpu"
      else
        warn "CUDA видна, но inference_device сейчас «${gpu_report}». Уже сохранённый system_settings.json не перезаписывается. Включите GPU в админке, если расшифровка должна идти на видеокарте."
      fi
    else
      bad "GPU-образ запущен, но CUDA в контейнере не видна (${gpu_report}). Проверьте драйвер, nvidia-container-toolkit и docker compose logs."
    fi
  fi
else
  bad "container not running — start with: docker compose -f ${COMPOSE_FILE} up --build -d"
fi

exit "$fail"
