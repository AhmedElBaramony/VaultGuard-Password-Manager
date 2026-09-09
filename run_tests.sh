#!/usr/bin/env bash
# Runs the full VaultGuard test suite.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [ -x "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

echo "========================================"
echo "Running VaultGuard Test Suite"
echo "Interpreter: $PYTHON"
echo "========================================"

STATUS=0
for suite in test_crypto test_argon2 test_mfa test_vault test_integration; do
    echo
    echo "[Suite] tests.$suite"
    "$PYTHON" -m unittest "tests.$suite" || STATUS=1
done

echo
echo "========================================"
if [ "$STATUS" -eq 0 ]; then
    echo "Test Suite Complete: all suites passed"
else
    echo "Test Suite Complete: one or more suites failed"
fi
echo "========================================"
exit "$STATUS"
