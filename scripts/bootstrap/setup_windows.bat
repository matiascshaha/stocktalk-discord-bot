@echo off
REM Thin wrapper around scripts/bootstrap/project_setup.py to keep setup logic in one place.

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.11 scripts\bootstrap\project_setup.py
    if %errorlevel%==0 (
        exit /b 0
    )
)

python scripts\bootstrap\project_setup.py
if errorlevel 1 (
    echo.
    echo ERROR: setup failed.
    exit /b 1
)
