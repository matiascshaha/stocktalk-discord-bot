#!/bin/bash
# Linux/macOS shell script for easy setup
# This script creates venv, installs dependencies, and sets up the project

echo ""
echo "============================================================"
echo "  Discord Stock Monitor - Setup Script"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Step 1: Create virtual environment
echo ""
echo "Step 1: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
    read -p "Do you want to recreate it? (y/N): " RECREATE
    if [[ "$RECREATE" =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    else
        echo "Using existing virtual environment."
        SKIP_VENV=true
    fi
fi

if [ "$SKIP_VENV" != "true" ]; then
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "Virtual environment created successfully."
fi

# Step 2: Install dependencies
echo ""
echo "Step 2: Installing dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
pip install -e .
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install project in editable mode"
    exit 1
fi
echo "Dependencies installed successfully."

# Step 3: Setup environment file
echo ""
echo "Step 3: Setting up environment file..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env file from .env.example"
        echo "IMPORTANT: Edit .env file and add your credentials!"
    else
        echo "WARNING: .env.example not found"
    fi
else
    echo ".env file already exists"
fi

# Step 4: Create data directory
echo ""
echo "Step 4: Creating data directory..."
if [ ! -d "data" ]; then
    mkdir -p data
    touch data/.gitkeep
    echo "Data directory created."
else
    echo "Data directory already exists."
fi

echo ""
echo "============================================================"
echo "  Setup Complete!"
echo "============================================================"
echo ""
echo "Next Steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Edit .env file with your credentials"
echo "   See docs/CREDENTIALS_SETUP.md for instructions"
echo "3. Test credentials: python -m scripts.test_credentials"
echo "4. Run monitor: python -m src.main"
echo ""
