#!/usr/bin/env bash
# Launches the MFA server, the mobile authenticator and the VaultGuard client.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [ -x "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

if ! "$PYTHON" -c "import tkinter" >/dev/null 2>&1; then
    echo "[Error] This interpreter was built without Tk, so the GUIs cannot start."
    echo "[Action] Install Tk support for your Python (on macOS: brew install python-tk),"
    echo "         or build the virtual environment with an interpreter that has it."
    exit 1
fi

if ! "$PYTHON" -c "import customtkinter" >/dev/null 2>&1; then
    echo "[Error] CustomTkinter is not installed."
    echo "[Action] Run ./install_deps.sh first."
    exit 1
fi

if lsof -nP -iTCP:5000 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "[Warning] Port 5000 is already in use. On macOS this is usually the AirPlay"
    echo "          Receiver; turn it off under System Settings > General > AirDrop & Handoff."
fi

PIDS=()
cleanup() {
    for pid in "${PIDS[@]:-}"; do
        kill "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT INT TERM

echo "[System] Launching MFA Server (HTTPS, port 5000)"
"$PYTHON" src/auth/mfa_server.py &
PIDS+=("$!")

echo "[System] Waiting for server"
sleep 3

echo "[System] Launching Mobile Authenticator"
"$PYTHON" src/gui/mobile_auth_gui.py &
PIDS+=("$!")

echo "[System] Launching VaultGuard Client"
"$PYTHON" src/gui/vault_gui.py

echo "[System] Client closed, shutting down."
