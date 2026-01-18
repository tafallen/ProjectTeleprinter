#!/usr/bin/env bash
# Setup script for Project Telex development environment

set -e

echo "Setting up Project Telex development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "Installing dependencies..."
pip install -r requirements-dev.txt

# Install package in development mode
echo "Installing package in development mode..."
pip install -e .

# Create data directory
echo "Creating data directories..."
mkdir -p telex_data

# Copy .env.example if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
else
    echo ".env file already exists"
fi

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  venv\\Scripts\\activate"
else
    echo "  source venv/bin/activate"
fi
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
echo "To start the server:"
echo "  telex-server"
