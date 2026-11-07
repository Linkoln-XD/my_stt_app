#!/usr/bin/env bash
# CPU image for a local Docker check. The NVIDIA server uses ./scripts/run_docker_gpu.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec docker compose up --build "$@"
