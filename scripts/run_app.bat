@echo off
cd /d "%~dp0.."
set VENV_PATH=%CD%\.venv
set PYTHON="%VENV_PATH%\Scripts\python.exe"

echo [Launcher] Using Python at: %PYTHON%
echo [Launcher] Starting VaultGuard...
%PYTHON% src\cli\main.py
pause
