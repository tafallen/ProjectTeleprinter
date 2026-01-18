"""
Adapters package for external integrations and persistence.
"""
from .database import DatabaseManager, DeduplicationDAO

__all__ = ["DatabaseManager", "DeduplicationDAO"]
