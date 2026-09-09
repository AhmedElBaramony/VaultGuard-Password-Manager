#!/usr/bin/env bash
# Runs the VaultGuard command-line client.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -x "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

echo "[Launcher] Using Python at: $PYTHON"
echo "[Launcher] Starting VaultGuard"
exec "$PYTHON" src/cli/main.py
