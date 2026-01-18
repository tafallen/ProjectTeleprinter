"""
Database adapter module for SQLite persistence.

This module provides async database management and deduplication functionality
using aiosqlite to prevent blocking the AsyncIO event loop.
"""
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite
import structlog

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connection and schema initialization.
    
    This class handles the lifecycle of the database connection and ensures
    the schema is properly initialized in an idempotent manner.
    """

    def __init__(self, db_path: str = "telex.db"):
        """
        Initialize the DatabaseManager.

        Args:
            db_path: Path to the SQLite database file. Defaults to "telex.db".
        """
        self.db_path = Path(db_path)
        self._connection: Optional[aiosqlite.Connection] = None
        logger.info("DatabaseManager initialized", db_path=str(self.db_path))

    async def initialize_db(self) -> None:
        """
        Initialize the database schema.

        Creates the seen_messages table if it doesn't exist. This operation
        is idempotent - running it multiple times will not cause errors.

        Schema:
            - id (TEXT PRIMARY KEY): The unique message ID
            - received_at (TEXT): ISO timestamp when message was first seen
        """
        conn = await self.get_connection()
        
        # Create seen_messages table with idempotent schema
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_messages (
                id TEXT PRIMARY KEY,
                received_at TEXT NOT NULL
            )
        """)
        
        # Create index on received_at for potential cleanup operations
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_received_at 
            ON seen_messages(received_at)
        """)
        
        await conn.commit()
        logger.info("Database schema initialized", db_path=str(self.db_path))

    async def get_connection(self) -> aiosqlite.Connection:
        """
        Get or create a database connection.

        Returns:
            An aiosqlite.Connection instance.
        """
        if self._connection is None:
            self._connection = await aiosqlite.connect(str(self.db_path))
            logger.debug("Database connection established", db_path=str(self.db_path))
        return self._connection

    async def close(self) -> None:
        """
        Close the database connection gracefully.
        """
        if self._connection is not None:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed", db_path=str(self.db_path))

    async def __aenter__(self):
        """Support for async context manager (with statement)."""
        await self.initialize_db()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support for async context manager (with statement)."""
        await self.close()


class DeduplicationDAO:
    """
    Data Access Object for message deduplication operations.
    
    This class provides high-performance checks for duplicate messages using
    parameterized queries to prevent SQL injection.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the DeduplicationDAO.

        Args:
            db_manager: The DatabaseManager instance to use for database operations.
        """
        self.db_manager = db_manager
        logger.debug("DeduplicationDAO initialized")

    async def exists(self, message_id: str) -> bool:
        """
        Check if a message ID has been seen before.

        This operation is optimized for speed and should complete in under 10ms
        for typical databases due to the PRIMARY KEY index on the id column.

        Args:
            message_id: The unique message identifier to check.

        Returns:
            True if the message has been seen before, False otherwise.
        """
        conn = await self.db_manager.get_connection()
        
        # Use parameterized query to prevent SQL injection
        cursor = await conn.execute(
            "SELECT 1 FROM seen_messages WHERE id = ? LIMIT 1",
            (message_id,)
        )
        
        result = await cursor.fetchone()
        await cursor.close()
        
        exists = result is not None
        logger.debug("Message ID lookup", message_id=message_id, exists=exists)
        return exists

    async def save(self, message_id: str) -> None:
        """
        Save a message ID to the database as seen.

        This method uses parameterized queries to prevent SQL injection.
        If the message ID already exists, this operation will fail silently
        (due to PRIMARY KEY constraint) but not raise an error.

        Args:
            message_id: The unique message identifier to save.
        """
        conn = await self.db_manager.get_connection()
        
        # Get current timestamp in ISO format
        received_at = datetime.now(timezone.utc).isoformat()
        
        try:
            # Use parameterized query to prevent SQL injection
            await conn.execute(
                "INSERT OR IGNORE INTO seen_messages (id, received_at) VALUES (?, ?)",
                (message_id, received_at)
            )
            await conn.commit()
            logger.debug("Message ID saved", message_id=message_id, received_at=received_at)
        except Exception as e:
            logger.error("Failed to save message ID", message_id=message_id, error=str(e))
            raise
