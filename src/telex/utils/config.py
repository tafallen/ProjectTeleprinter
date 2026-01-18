"""
Configuration management for the Telex system.
"""
import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NeighborConfig(BaseModel):
    """Configuration for a neighbor node in the mesh network."""

    node_id: str = Field(description="Neighbor node ID")
    host: str = Field(description="Hostname or IP address of the neighbor")
    port: int = Field(default=8023, description="Port number of the neighbor")


class TelexConfig(BaseSettings):
    """
    Configuration settings for the Telex system.

    Settings can be overridden via environment variables with TELEX_ prefix.
    """

    # Configuration
    model_config = SettingsConfigDict(
        env_prefix="TELEX_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

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

    # Neighbor nodes (for mesh network routing)
    neighbors: List[NeighborConfig] = Field(
        default_factory=list, description="List of neighbor nodes in the mesh network"
    )

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


def load_config(config_file: Optional[str] = None) -> TelexConfig:
    """
    Load configuration from environment, .env file, or JSON file.
    
    Args:
        config_file: Optional path to a JSON configuration file (e.g., /etc/telex/config.json)
    
    Returns:
        TelexConfig instance with loaded configuration
    """
    if config_file and Path(config_file).exists():
        # Load from JSON file
        import json
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        return TelexConfig(**config_data)
    else:
        # Load from environment and .env file
        return TelexConfig()
