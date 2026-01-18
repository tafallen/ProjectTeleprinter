"""
Database manager for SQLite persistence.
"""
import aiosqlite
import asyncio
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connections and schema.
    
    Handles:
    - Database initialization
    - Schema creation and migrations
    - Connection management
    """

    def __init__(self, db_path: Path):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """
        Initialize the database and create tables if they don't exist.
        """
        # Ensure the parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        async with self._lock:
            conn = await aiosqlite.connect(self.db_path)
            try:
                await self._create_tables(conn)
                logger.info("Database initialized", path=str(self.db_path))
            finally:
                await conn.close()

    async def _create_tables(self, conn: aiosqlite.Connection) -> None:
        """
        Create database tables.
        
        Args:
            conn: Database connection
        """
        # Create message_queue table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS message_queue (
                id TEXT PRIMARY KEY,
                priority INTEGER NOT NULL DEFAULT 0,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                CHECK (priority >= 0 AND priority <= 10)
            )
            """
        )

        # Create index on created_at for fast cleanup queries
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_message_queue_created_at
            ON message_queue(created_at)
            """
        )

        # Create index on status for efficient filtering
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_message_queue_status
            ON message_queue(status)
            """
        )

        await conn.commit()
        logger.info("Database tables created")

    async def get_connection(self) -> aiosqlite.Connection:
        """
        Get a database connection.
        
        Returns:
            Database connection
        """
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        return conn

    async def close(self) -> None:
        """
        Close the database manager.
        """
        async with self._lock:
            if self._connection:
                await self._connection.close()
                self._connection = None
        logger.info("Database manager closed")
