"""
Hardware interface module for physical teletype equipment.

This module provides abstraction for:
- Serial communication with teletype hardware
- GPIO control (Raspberry Pi specific)
- Platform-independent interface design to prevent import errors on Windows/Mac

The HardwareInterface class gracefully handles missing hardware/libraries.
"""

__all__ = ["HardwareInterface", "TeletypeDevice"]
