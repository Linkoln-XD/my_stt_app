#!/usr/bin/env bash
# Portable CPython 3.12 for macOS (GigaAM needs Python >= 3.10). No Homebrew required.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/.tools/python312"
MARKER="$TOOLS/python/bin/python3.12"

if [[ -x "$MARKER" ]]; then
  exec "$MARKER" "$@"
fi

ARCH="$(uname -m)"
case "$ARCH" in
  arm64) ARCH_TAG="aarch64-apple-darwin" ;;
  x86_64) ARCH_TAG="x86_64-apple-darwin" ;;
  *)
    echo "Unsupported architecture: $ARCH" >&2
    exit 1
    ;;
esac

RELEASE_TAG="${PYTHON_STANDALONE_RELEASE:-20261026}"
PY_TAG="${PYTHON_STANDALONE_BUILD:-cpython-3.12.16+20261026}"
TARBALL="${PY_TAG}-${ARCH_TAG}-install_only.tar.gz"
URL="https://github.com/astral-sh/python-build-standalone/releases/download/${RELEASE_TAG}/${TARBALL}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading $PY_TAG for $ARCH_TAG (first run may take a minute)…"
curl -fL --retry 3 --retry-delay 2 -o "$TMP/python.tar.gz" "$URL"
mkdir -p "$TOOLS"
rm -rf "$TOOLS/python"
tar -xzf "$TMP/python.tar.gz" -C "$TOOLS"
chmod +x "$MARKER"

echo "Python installed at $MARKER"
"$MARKER" --version
