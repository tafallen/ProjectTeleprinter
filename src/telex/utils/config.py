"""
Configuration management for the Telex system.
"""
import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class TelexConfig(BaseSettings):
    """
    Configuration settings for the Telex system.

    Settings can be overridden via environment variables with TELEX_ prefix.
    """

    # Node identification
    node_id: str = Field(
        default="0001", description="Node ID in XXXY format (this is the XXXY address)"
    )
    location_code: str = Field(
        default="000", description="Location code (XXX part of XXXY)"
    )
    machine_id: str = Field(default="1", description="Machine ID (Y part of XXXY)")

    # Network settings
    listen_host: str = Field(default="0.0.0.0", description="Host to bind server to")
    listen_port: int = Field(default=8023, description="Port to bind server to")
    max_connections: int = Field(default=100, description="Maximum concurrent connections")

    # Message settings
    message_ttl_hours: int = Field(
        default=72, description="Message time-to-live in hours"
    )
    max_message_size: int = Field(
        default=65536, description="Maximum message size in bytes"
    )

    # Database settings
    database_path: Path = Field(
        default=Path("telex_data/messages.db"), description="Path to SQLite database"
    )
    dedup_db_path: Path = Field(
        default=Path("telex_data/dedup.db"),
        description="Path to deduplication database",
    )

    # Hardware settings
    hardware_enabled: bool = Field(
        default=False, description="Enable hardware teletype interface"
    )
    serial_port: Optional[str] = Field(
        default=None, description="Serial port for teletype (e.g., /dev/ttyUSB0)"
    )
    gpio_pin: Optional[int] = Field(default=None, description="GPIO pin for control")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    class Config:
        env_prefix = "TELEX_"
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config() -> TelexConfig:
    """Load configuration from environment and .env file."""
    return TelexConfig()
