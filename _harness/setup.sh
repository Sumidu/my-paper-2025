#!/usr/bin/env bash
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$HARNESS_DIR/.venv"
ROOT="$(dirname "$HARNESS_DIR")"

echo "==> Setting up paperharness environment"

# Python 3.10+
PYTHON=""
for py in python3.11 python3.10 python3; do
  if command -v "$py" &>/dev/null; then
    candidate="$py"
    PY_VERSION=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -gt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 10 ]); then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "ERROR: python3 not found. Install Python 3.10+ from https://python.org"
  exit 1
fi

PY_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "    Using Python $PY_VERSION"

# Virtual environment
if [ ! -d "$VENV" ]; then
  echo "==> Creating virtualenv at _harness/.venv"
  "$PYTHON" -m venv "$VENV"
fi

echo "==> Installing Python dependencies"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$HARNESS_DIR/requirements.txt"

# Pandoc
if ! command -v pandoc &>/dev/null; then
  echo "WARNING: pandoc not found. Install with: brew install pandoc"
else
  echo "    pandoc $(pandoc --version | head -1 | awk '{print $2}') OK"
fi

# pandoc-crossref
if ! command -v pandoc-crossref &>/dev/null; then
  echo "WARNING: pandoc-crossref not found. Install with: brew install pandoc-crossref"
else
  echo "    pandoc-crossref OK"
fi

# .env file
if [ ! -f "$ROOT/.env" ]; then
  if [ -f "$ROOT/.env.example" ]; then
    cp "$ROOT/.env.example" "$ROOT/.env"
    echo "==> Created .env from .env.example"
    echo "    Edit .env and add your Semantic Scholar API key"
    echo "    (Get one free at https://www.semanticscholar.org/product/api)"
  fi
fi

echo ""
echo "Setup complete. To verify:"
echo "  cd _harness && .venv/bin/pytest tests/ -v"
