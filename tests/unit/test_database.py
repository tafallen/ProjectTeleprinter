"""
Unit tests for database manager.
"""
import asyncio
from pathlib import Path
import tempfile

import pytest

from telex.core.database import DatabaseManager


@pytest.mark.asyncio
async def test_database_initialization():
    """Test that database initializes with proper schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)

        await db_manager.initialize()

        # Verify database file was created
        assert db_path.exists()

        # Verify tables exist
        conn = await db_manager.get_connection()
        try:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='message_queue'"
            )
            result = await cursor.fetchone()
            assert result is not None
            assert result[0] == "message_queue"

            # Verify indexes exist
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_message_queue_created_at'"
            )
            result = await cursor.fetchone()
            assert result is not None
        finally:
            await conn.close()


@pytest.mark.asyncio
async def test_database_get_connection():
    """Test getting a database connection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)

        await db_manager.initialize()

        conn = await db_manager.get_connection()
        assert conn is not None

        # Test that connection works
        cursor = await conn.execute("SELECT 1")
        result = await cursor.fetchone()
        assert result[0] == 1

        await conn.close()


@pytest.mark.asyncio
async def test_database_close():
    """Test closing database manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)

        await db_manager.initialize()
        await db_manager.close()

        # Should be able to close multiple times without error
        await db_manager.close()
