@echo off
set VENV_PATH=%~dp0.venv
set PYTHON="%VENV_PATH%\Scripts\python.exe"

echo [System] Checking for CustomTkinter...
%PYTHON% -c "import customtkinter" 2>NUL
if %errorlevel% neq 0 (
    echo [Error] CustomTkinter not found! 
    echo [Action] Please run 'install_deps.bat' first.
    pause
    exit /b
)

echo [System] Launching MFA Server...
start "MFA Server (Do Not Close)" %PYTHON% src\auth\mfa_server.py

echo [System] Launching Mobile Authenticator...
start "VaultGuard Mobile" %PYTHON% src\gui\mobile_auth_gui.py

echo [System] Waiting for server...
timeout /t 3 > NUL

echo [System] Launching VaultGuard Client...
start "VaultGuard Client" %PYTHON% src\gui\vault_gui.py

echo [Success] System is running!
pause
