#!/usr/bin/env bash
set -euo pipefail
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite.*5173" 2>/dev/null || true
echo "Stopped STT backend and frontend (if they were running)."
