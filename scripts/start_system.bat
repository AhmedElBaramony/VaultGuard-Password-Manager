@echo off
cd /d "%~dp0.."
set VENV_PATH=%CD%\.venv
set PYTHON="%VENV_PATH%\Scripts\python.exe"

echo [System] Working Directory: %CD%

echo [System] Launching MFA Server...
start "MFA Server (Do Not Close)" %PYTHON% src\auth\mfa_server.py

echo [System] Launching Mobile App Simulator...
start "Mobile App" %PYTHON% src\cli\mobile_auth_app.py

echo [System] Waiting 5 seconds for server to start...
timeout /t 5 > NUL

echo [System] Launching VaultGuard Client...
%PYTHON% src\cli\main.py
pause
