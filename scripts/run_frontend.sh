#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_NODE="$ROOT/.tools/node/bin"
if [[ -d "$TOOLS_NODE" ]]; then
  export PATH="$TOOLS_NODE:$PATH"
fi
cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm install
fi
exec npm run dev -- --host 127.0.0.1 --port 5173
