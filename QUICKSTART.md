# Quick Start Guide

This guide will help you get Project Telex up and running quickly.

## Prerequisites

- Python 3.10 or higher
- pip (usually comes with Python)
- Git (for cloning the repository)

## Installation

### Option 1: Using Setup Scripts (Recommended)

#### Linux/macOS:
```bash
git clone https://github.com/tafallen/ProjectTeleprinter.git
cd ProjectTeleprinter
./scripts/setup.sh
```

#### Windows:
```cmd
git clone https://github.com/tafallen/ProjectTeleprinter.git
cd ProjectTeleprinter
scripts\setup.bat
```

### Option 2: Manual Installation

1. **Clone the repository:**
```bash
git clone https://github.com/tafallen/ProjectTeleprinter.git
cd ProjectTeleprinter
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv

# Activate it:
source venv/bin/activate      # Linux/macOS
# or
venv\Scripts\activate         # Windows
```

3. **Install dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .
```

4. **Create configuration file:**
```bash
cp .env.example .env
```

## Verify Installation

Run the test suite to verify everything is working:

```bash
pytest
```

You should see all tests passing:
```
============ 12 passed in 0.11s ============
```

## Running the Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the server
telex-server
```

## Configuration

Edit the `.env` file to customize your node:

```bash
# Node Identification
TELEX_NODE_ID=0001
TELEX_LOCATION_CODE=000
TELEX_MACHINE_ID=1

# Network Settings
TELEX_LISTEN_HOST=0.0.0.0
TELEX_LISTEN_PORT=8023
```

## Development Workflow

1. **Activate the virtual environment:**
```bash
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

2. **Make your changes**

3. **Run tests:**
```bash
pytest
```

4. **Format code:**
```bash
black src/ tests/
```

5. **Check code quality:**
```bash
flake8 src/ tests/
mypy src/
```

## Common Tasks

### Running Tests with Coverage
```bash
pytest --cov=src/telex --cov-report=html
# View coverage report in htmlcov/index.html
```

### Running Specific Tests
```bash
pytest tests/unit/test_config.py
pytest tests/unit/test_hardware.py
pytest tests/unit/test_config.py::test_default_config
```

### Updating Dependencies
```bash
pip install -r requirements-dev.txt --upgrade
```

## Project Structure

```
ProjectTeleprinter/
├── src/telex/           # Main application code
│   ├── network/         # TCP/IP networking
│   ├── queue/           # Message queue & persistence
│   ├── routing/         # XXXY routing logic
│   ├── hardware/        # Teletype hardware interface
│   └── utils/           # Configuration and utilities
├── tests/               # Test suite
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── scripts/             # Setup and utility scripts
└── docs/                # Documentation
```

## Next Steps

- Read the [README.md](README.md) for detailed information
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Explore the code in `src/telex/`
- Write additional tests in `tests/`

## Troubleshooting

### Import Errors
If you see import errors, make sure:
1. Virtual environment is activated
2. Package is installed: `pip install -e .`

### Test Failures
If tests fail:
1. Check Python version: `python --version` (should be 3.10+)
2. Update dependencies: `pip install -r requirements-dev.txt --upgrade`
3. Reinstall package: `pip install -e . --force-reinstall`

### Permission Errors (Linux/macOS)
If setup script won't run:
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## Getting Help

- Open an issue on GitHub
- Check existing issues for similar problems
- Read the documentation in `docs/`

Happy coding!
