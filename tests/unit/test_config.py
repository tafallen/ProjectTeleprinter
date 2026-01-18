"""
Unit tests for configuration module.
"""
import os
from pathlib import Path

import pytest

from telex.utils.config import TelexConfig, load_config


def test_default_config():
    """Test that default configuration loads successfully."""
    config = TelexConfig()

    assert config.node_id == "0001"
    assert config.location_code == "000"
    assert config.machine_id == "1"
    assert config.listen_host == "0.0.0.0"
    assert config.listen_port == 8023
    assert config.message_ttl_hours == 72
    assert config.hardware_enabled is False


def test_config_from_env(monkeypatch):
    """Test configuration can be overridden by environment variables."""
    monkeypatch.setenv("TELEX_NODE_ID", "1234")
    monkeypatch.setenv("TELEX_LISTEN_PORT", "9999")
    monkeypatch.setenv("TELEX_MESSAGE_TTL_HOURS", "48")

    config = TelexConfig()

    assert config.node_id == "1234"
    assert config.listen_port == 9999
    assert config.message_ttl_hours == 48


def test_load_config():
    """Test load_config function."""
    config = load_config()

    assert isinstance(config, TelexConfig)
    assert config.node_id is not None
