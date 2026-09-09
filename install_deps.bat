@echo off
set VENV_PATH=%~dp0.venv
echo Activating venv...
call "%VENV_PATH%\Scripts\activate.bat"
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
echo Done.
