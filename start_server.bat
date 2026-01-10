@echo off
cd /d "%~dp0"
echo Starting Server...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please check setup.
    pause
    exit /b
)

python web_app.py
pause
