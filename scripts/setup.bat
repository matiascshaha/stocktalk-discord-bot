@echo off
REM Windows batch script for easy setup
REM This script creates venv, installs dependencies, and sets up the project

echo.
echo ============================================================
echo   Discord Stock Monitor - Windows Setup Script
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo Step 1: Creating virtual environment...
if exist venv (
    echo Virtual environment already exists.
    set /p RECREATE="Do you want to recreate it? (y/N): "
    if /i "%RECREATE%"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q venv
    ) else (
        echo Using existing virtual environment.
        goto :install
    )
)

python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created successfully.

:install
echo.
echo Step 2: Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install project in editable mode
    pause
    exit /b 1
)
echo Dependencies installed successfully.

echo.
echo Step 3: Setting up environment file...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo Created .env file from .env.example
        echo IMPORTANT: Edit .env file and add your credentials!
    ) else (
        echo WARNING: .env.example not found
    )
) else (
    echo .env file already exists
)

echo.
echo Step 4: Creating data directory...
if not exist data (
    mkdir data
    echo. > data\.gitkeep
    echo Data directory created.
) else (
    echo Data directory already exists.
)

echo.
echo ============================================================
echo   Setup Complete!
echo ============================================================
echo.
echo Next Steps:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Edit .env file with your credentials
echo    See docs\CREDENTIALS_SETUP.md for instructions
echo 3. Test credentials: python -m scripts.test_credentials
echo 4. Run monitor: python -m src.main
echo.
pause
