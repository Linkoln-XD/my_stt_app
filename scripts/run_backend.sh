#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

BUNDLED_PY="$ROOT/.tools/python312/python/bin/python3.12"

resolve_python() {
  if [[ -x "$BUNDLED_PY" ]]; then
    echo "$BUNDLED_PY"
    return 0
  fi
  for PY in python3.12 python3.11 python3.10; do
    if command -v "$PY" >/dev/null 2>&1; then
      if "$PY" -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        echo "$PY"
        return 0
      fi
    fi
  done
  return 1
}

if ! PY="$(resolve_python)"; then
  echo "GigaAM нужен Python 3.10+. Скачиваем portable CPython 3.12 в .tools/ …" >&2
  "$ROOT/scripts/ensure_python312.sh" --version >/dev/null
  PY="$BUNDLED_PY"
fi

PY_VERSION="$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

if [[ -d .venv ]]; then
  VENV_VER="$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  VENV_OK="$(.venv/bin/python -c 'import sys; print(int(sys.version_info >= (3, 10)))')"
  SELECTED_OK="$("$PY" -c 'import sys; print(int(sys.version_info >= (3, 10)))')"
  if [[ "$VENV_OK" == "0" && "$SELECTED_OK" == "1" ]]; then
    echo "Пересоздаём backend/.venv: было Python $VENV_VER, для GigaAM нужен >= 3.10."
    rm -rf .venv
  fi
fi

if [[ ! -d .venv ]]; then
  echo "Создаём venv на Python $PY_VERSION ($PY)"
  "$PY" -m venv .venv
  .venv/bin/pip install -U pip setuptools
  .venv/bin/pip install -r requirements.txt
  .venv/bin/pip install -r requirements-gigaam.txt
fi

if ! .venv/bin/python -c 'import gigaam' 2>/dev/null; then
  .venv/bin/pip install -r requirements-gigaam.txt
fi

"$ROOT/scripts/ensure_ffmpeg.sh"
export PATH="$ROOT/.tools/ffmpeg:${PATH:-}"

exec .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
