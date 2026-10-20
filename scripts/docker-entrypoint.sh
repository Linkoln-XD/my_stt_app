#!/usr/bin/env sh
set -eu

DATA="${DATA_DIR:-/app/data}"
mkdir -p "${DATA}/uploads" "${DATA}/processed"

cd /app/backend
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
