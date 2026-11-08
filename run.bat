@echo off
cd /d "%~dp0"

if not exist "src\main.py" (
    echo Stage 1 is not implemented yet.
    pause
    exit /b 0
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m src.main
) else (
    python -m src.main
)
