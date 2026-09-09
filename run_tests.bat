@echo off
set VENV_PATH=%~dp0.venv
set PYTHON="%VENV_PATH%\Scripts\python.exe"

echo ========================================
echo Running VaultGuard Test Suite
echo ========================================
echo.

echo [Test 1] Testing Cryptography Module...
%PYTHON% -m unittest tests.test_crypto
echo.

echo [Test 2] Testing Argon2 KDF...
%PYTHON% -m unittest tests.test_argon2
echo.

echo [Test 3] Testing MFA/TOTP System...
%PYTHON% -m unittest tests.test_mfa
echo.

echo [Test 4] Testing Vault File Manager...
%PYTHON% -m unittest tests.test_vault
echo.

echo [Test 5] Testing Integration...
%PYTHON% -m unittest tests.test_integration
echo.

echo ========================================
echo Test Suite Complete
echo ========================================
pause
