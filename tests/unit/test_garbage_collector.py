"""
Unit tests for garbage collector service.
"""
import asyncio
from datetime import datetime, timedelta, UTC
from pathlib import Path
import tempfile

import pytest

from telex.core.database import DatabaseManager
from telex.core.dao import MessageQueueDAO
from telex.core.garbage_collector import GarbageCollector
from telex.core.models import QueuedMessage, MessageStatus


@pytest.mark.asyncio
async def test_garbage_collector_cleanup():
    """Test that garbage collector deletes expired messages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)
        gc = GarbageCollector(db_manager, ttl_hours=1)

        # Create old and new messages
        old_msg = QueuedMessage(
            priority=1,
            payload={"old": True},
            created_at=datetime.now(UTC) - timedelta(hours=2),
        )
        new_msg = QueuedMessage(
            priority=1,
            payload={"old": False},
            created_at=datetime.now(UTC),
        )

        await dao.enqueue(old_msg)
        await dao.enqueue(new_msg)

        # Run cleanup
        deleted = await gc.cleanup_now()

        # Should have deleted 1 message
        assert deleted == 1

        # Verify old message is gone, new message remains
        old_retrieved = await dao.get_by_id(old_msg.id)
        assert old_retrieved is None

        new_retrieved = await dao.get_by_id(new_msg.id)
        assert new_retrieved is not None


@pytest.mark.asyncio
async def test_garbage_collector_no_expired():
    """Test garbage collector when no messages are expired."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)
        gc = GarbageCollector(db_manager, ttl_hours=72)

        # Create recent message
        msg = QueuedMessage(
            priority=1,
            payload={"test": "data"},
            created_at=datetime.now(UTC),
        )
        await dao.enqueue(msg)

        # Run cleanup
        deleted = await gc.cleanup_now()

        # Should not delete anything
        assert deleted == 0

        # Verify message still exists
        retrieved = await dao.get_by_id(msg.id)
        assert retrieved is not None


@pytest.mark.asyncio
async def test_garbage_collector_start_stop():
    """Test starting and stopping garbage collector."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        gc = GarbageCollector(db_manager, ttl_hours=72, interval_seconds=1)

        # Start the collector
        await gc.start()
        assert gc._running is True

        # Wait a bit
        await asyncio.sleep(0.1)

        # Stop the collector
        await gc.stop()
        assert gc._running is False

        # Should be able to stop again without error
        await gc.stop()


@pytest.mark.asyncio
async def test_garbage_collector_periodic_cleanup():
    """Test that garbage collector runs periodically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)
        gc = GarbageCollector(db_manager, ttl_hours=1, interval_seconds=1)

        # Create an expired message
        old_msg = QueuedMessage(
            priority=1,
            payload={"old": True},
            created_at=datetime.now(UTC) - timedelta(hours=2),
        )
        await dao.enqueue(old_msg)

        # Start collector
        await gc.start()

        # Wait for at least one cleanup cycle
        await asyncio.sleep(1.5)

        # Stop collector
        await gc.stop()

        # Message should be deleted
        retrieved = await dao.get_by_id(old_msg.id)
        assert retrieved is None


@pytest.mark.asyncio
async def test_garbage_collector_default_ttl():
    """Test garbage collector with default 72 hour TTL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)
        gc = GarbageCollector(db_manager)  # Default ttl_hours=72

        # Create message that's 73 hours old
        old_msg = QueuedMessage(
            priority=1,
            payload={"old": True},
            created_at=datetime.now(UTC) - timedelta(hours=73),
        )

        # Create message that's 71 hours old
        recent_msg = QueuedMessage(
            priority=1,
            payload={"recent": True},
            created_at=datetime.now(UTC) - timedelta(hours=71),
        )

        await dao.enqueue(old_msg)
        await dao.enqueue(recent_msg)

        # Run cleanup
        deleted = await gc.cleanup_now()

        # Should delete only the 73-hour-old message
        assert deleted == 1

        old_retrieved = await dao.get_by_id(old_msg.id)
        assert old_retrieved is None

        recent_retrieved = await dao.get_by_id(recent_msg.id)
        assert recent_retrieved is not None
