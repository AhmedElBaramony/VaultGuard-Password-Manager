#!/usr/bin/env bash
# Launches the console version: MFA server, mobile authenticator CLI and vault client.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -x "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

echo "[System] Working directory: $ROOT"

SERVER_PID=""
cleanup() {
    [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[System] Launching MFA Server"
"$PYTHON" src/auth/mfa_server.py &
SERVER_PID="$!"

echo "[System] Waiting 5 seconds for server to start"
sleep 5

echo "[System] Launching VaultGuard Client"
echo "[System] Run 'python src/cli/mobile_auth_app.py' in a second terminal for the mobile authenticator."
"$PYTHON" src/cli/main.py
