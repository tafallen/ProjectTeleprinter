@echo off
REM Setup script for Project Telex development environment (Windows)

echo Setting up Project Telex development environment...

REM Check Python version
python --version
if errorlevel 1 (
    echo Python not found. Please install Python 3.15 or higher.
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install development dependencies
echo Installing dependencies...
pip install -r requirements-dev.txt

REM Install package in development mode
echo Installing package in development mode...
pip install -e .

REM Create data directory
echo Creating data directories...
if not exist "telex_data" mkdir telex_data

REM Copy .env.example if .env doesn't exist
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
) else (
    echo .env file already exists
)

echo.
echo Setup complete!
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate
echo.
echo To run tests:
echo   pytest
echo.
echo To start the server:
echo   telex-server
