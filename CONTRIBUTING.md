# Contributing to Project Telex

Thank you for considering contributing to Project Telex! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see README.md)
4. Create a new branch for your feature or bugfix

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ProjectTeleprinter.git
cd ProjectTeleprinter

# Run the setup script
./scripts/setup.sh  # On Linux/Mac
# or
scripts\setup.bat   # On Windows

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows
```

## Making Changes

### Code Style

- Follow PEP 8 style guidelines
- Use Black for code formatting (line length: 100)
- Include type hints for function signatures
- Write docstrings in Google style format

### Before Submitting

1. **Format your code**:
```bash
black src/ tests/
```

2. **Run linters**:
```bash
flake8 src/ tests/
mypy src/
```

3. **Run tests**:
```bash
pytest
```

4. **Check coverage**:
```bash
pytest --cov=src/telex --cov-report=html
```

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage
- Use pytest fixtures for common setup
- Test edge cases and error conditions
- Use `pytest-asyncio` for async code testing

Example test structure:
```python
"""
Test module description.
"""
import pytest

def test_feature():
    """Test description."""
    # Arrange
    # Act
    # Assert
```

### Commit Messages

Write clear, concise commit messages:
- Use present tense ("Add feature" not "Added feature")
- Start with a capital letter
- Keep first line under 50 characters
- Add detailed description if needed

Example:
```
Add message deduplication to queue

- Implement hash-based deduplication
- Add SQLite table for tracking seen messages
- Include unit tests for edge cases
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md if applicable
5. Create a Pull Request with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to any related issues

## Code Review

- Be patient and respectful
- Respond to feedback constructively
- Make requested changes promptly
- Ask questions if something is unclear

## Project Structure

```
src/telex/
├── network/      # TCP/IP networking
├── queue/        # Message queue and persistence
├── routing/      # Routing algorithms
├── hardware/     # Hardware interface
└── utils/        # Utilities and configuration
```

## Areas for Contribution

- **Network Layer**: TCP server/client implementation
- **Message Queue**: SQLite-based persistent queue
- **Routing**: XXXY address routing logic
- **Hardware Interface**: Teletype device drivers
- **Testing**: Unit and integration tests
- **Documentation**: User guides, API docs
- **Examples**: Sample configurations, use cases

## Questions?

Open an issue on GitHub with the "question" label.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Assume positive intent

Thank you for contributing to Project Telex!
