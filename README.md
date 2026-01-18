# Project Telex

A modern replica of a distributed, store-and-forward telex system running on a federated mesh network over TCP/IP.

## Overview

Project Telex implements a resilient messaging system with the following features:

- **Federated Mesh Network**: Nodes connect to neighbors; messages hop to their destination
- **XXXY Routing**: XXX = Location Node, Y = Specific Machine
- **Store-and-Forward**: Persistent message queuing with 72-hour TTL
- **Local Failover**: If target machine (Y) is offline, delivers to any available machine at location (XXX)
- **Hardware Interface**: Designed to interface with antique physical teletype hardware

## Architecture

### Technology Stack

- **Language**: Python 3.15+
- **Async I/O**: asyncio for non-blocking TCP network operations
- **Database**: SQLite for message queue persistence and deduplication
- **Testing**: pytest with pytest-asyncio
- **Serial Communication**: pyserial for hardware interface
- **Configuration**: pydantic for settings management

### Target Platforms

- **Production**: Raspberry Pi (Raspberry Pi OS / Debian)
- **Development**: Windows 11, macOS, Linux (Debian/Ubuntu)

## Installation

### Prerequisites

- Python 3.15 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/tafallen/ProjectTeleprinter.git
cd ProjectTeleprinter
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
# For production
pip install -r requirements.txt

# For development (includes testing and linting tools)
pip install -r requirements-dev.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` to configure your node:
```bash
# Node Identification
TELEX_NODE_ID=0001
TELEX_LOCATION_CODE=000
TELEX_MACHINE_ID=1

# Network Settings
TELEX_LISTEN_HOST=0.0.0.0
TELEX_LISTEN_PORT=8023

# Enable hardware interface (Raspberry Pi only)
TELEX_HARDWARE_ENABLED=false
# TELEX_SERIAL_PORT=/dev/ttyUSB0
```

## Usage

### Running the Server

```bash
# Using the installed command
telex-server

# Or directly with Python
python -m telex.main
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/telex --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

## Project Structure

```
ProjectTeleprinter/
├── src/
│   └── telex/
│       ├── __init__.py
│       ├── main.py              # Main entry point
│       ├── network/             # TCP/IP networking
│       ├── queue/               # Message queue & persistence
│       ├── routing/             # XXXY routing logic
│       ├── hardware/            # Teletype hardware interface
│       └── utils/               # Configuration and utilities
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── conftest.py              # Test configuration
├── docs/                        # Documentation
├── scripts/                     # Utility scripts
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml              # Project configuration
├── .env.example                # Example environment configuration
└── README.md                   # This file
```

## Development

### Setting Up Development Environment

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Install pre-commit hooks (if configured):
```bash
pre-commit install
```

### Code Style

This project follows these conventions:
- **Line Length**: 100 characters (Black formatter)
- **Style Guide**: PEP 8
- **Docstrings**: Google style
- **Type Hints**: Encouraged for public APIs

### Adding New Features

1. Create a new branch
2. Implement the feature with tests
3. Run tests and linters
4. Submit a pull request

## Hardware Interface

The hardware interface is designed to work with physical teletype machines via:
- **Serial Communication**: Using pyserial for RS-232/USB serial connections
- **GPIO Control**: Using RPi.GPIO for Raspberry Pi (when available)

The system gracefully handles platforms where hardware is not available (Windows/Mac development).

## Message Format

Messages in the Telex system use the XXXY addressing format:
- **XXX**: Location Node (000-999)
- **Y**: Machine ID at location (0-9)

Example: `1234` routes to Location 123, Machine 4

## Contributing

Contributions are welcome! Please ensure:
1. All tests pass
2. Code is formatted with Black
3. No linting errors from flake8
4. Type hints are included where appropriate

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.