#!/usr/bin/env bash
# Creates a virtual environment in .venv and installs the project dependencies.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"

if [ ! -d "$VENV" ]; then
    echo "[Setup] Creating virtual environment at $VENV"
    python3 -m venv "$VENV"
fi

echo "[Setup] Installing dependencies from requirements.txt"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"

echo "[Setup] Done. Activate with: source .venv/bin/activate"
