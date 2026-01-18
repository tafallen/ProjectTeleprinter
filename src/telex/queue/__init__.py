"""
Message queue module for persistent message storage and retrieval.

This module handles:
- Message persistence using SQLite
- Store-and-forward queue management
- 72-hour TTL enforcement
- Message deduplication
"""

__all__ = ["MessageQueue", "Message", "QueueManager"]
