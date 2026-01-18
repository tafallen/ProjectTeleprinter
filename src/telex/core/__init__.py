"""
Core module for Project Telex.

This module contains:
- Database management
- Data Access Objects (DAOs)
- Background services (garbage collection)
"""

from telex.core.database import DatabaseManager
from telex.core.dao import MessageQueueDAO
from telex.core.garbage_collector import GarbageCollector
from telex.core.models import QueuedMessage, MessageStatus

__all__ = [
    "DatabaseManager",
    "MessageQueueDAO",
    "GarbageCollector",
    "QueuedMessage",
    "MessageStatus",
]
