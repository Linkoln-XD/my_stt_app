#!/usr/bin/env bash
# NVIDIA server image. Extra args are passed to compose, for example: ./scripts/run_docker_gpu.sh -d
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec docker compose -f docker-compose.gpu.yml up --build "$@"
