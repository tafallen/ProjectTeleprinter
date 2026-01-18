"""
Project Telex - A Modern Distributed Telex System

This package implements a federated mesh network telex system with:
- Store-and-forward messaging
- XXXY routing (XXX = Location Node, Y = Machine ID)
- Persistent message queuing with SQLite
- 72-hour TTL for messages
- Local failover capabilities
- Support for physical teletype hardware interface
"""

__version__ = "0.1.0"
__author__ = "Project Telex Team"
