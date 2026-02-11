@echo off
REM Thin wrapper around scripts/setup.py to keep setup logic in one place.

python scripts\setup.py
if errorlevel 1 (
    echo.
    echo ERROR: setup failed.
    exit /b 1
)
