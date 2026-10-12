#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  PY=python3.12
  command -v "$PY" >/dev/null || PY=python3.11
  command -v "$PY" >/dev/null || PY=python3
  "$PY" -m venv .venv
  .venv/bin/pip install -U pip
  .venv/bin/pip install -r requirements.txt
fi
exec .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
