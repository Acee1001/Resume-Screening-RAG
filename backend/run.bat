@echo off
setlocal
REM Always run relative to this file's directory (backend/)
cd /d "%~dp0"

if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
REM Default port is 8001 (matches frontend dev proxy). Override: set BACKEND_PORT=8000
if "%BACKEND_PORT%"=="" set BACKEND_PORT=8001
python -m uvicorn main:app --reload --host 0.0.0.0 --port %BACKEND_PORT%
