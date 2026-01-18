"""
Unit tests for MessageQueueDAO.
"""
import asyncio
from datetime import datetime, timedelta, UTC
from pathlib import Path
import tempfile
from uuid import uuid4

import pytest

from telex.core.database import DatabaseManager
from telex.core.dao import MessageQueueDAO
from telex.core.models import QueuedMessage, MessageStatus


@pytest.mark.asyncio
async def test_enqueue_message():
    """Test enqueuing a message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)

        # Create a test message
        msg = QueuedMessage(
            priority=5,
            payload={"to": "1234", "from": "0001", "content": "Test message"},
        )

        await dao.enqueue(msg)

        # Verify message was inserted
        retrieved = await dao.get_by_id(msg.id)
        assert retrieved is not None
        assert retrieved.id == msg.id
        assert retrieved.priority == msg.priority
        assert retrieved.payload == msg.payload
        assert retrieved.status == MessageStatus.PENDING


@pytest.mark.asyncio
async def test_get_next_batch():
    """Test getting next batch of messages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)

        # Create multiple test messages
        messages = []
        for i in range(5):
            msg = QueuedMessage(
                priority=i,
                payload={"index": i},
                created_at=datetime.now(UTC) - timedelta(minutes=5 - i),
            )
            messages.append(msg)
            await dao.enqueue(msg)

        # Get batch
        batch = await dao.get_next_batch(limit=3)
        assert len(batch) == 3

        # Should be ordered by created_at ASC (oldest first)
        assert batch[0].payload["index"] == 0
        assert batch[1].payload["index"] == 1
        assert batch[2].payload["index"] == 2


@pytest.mark.asyncio
async def test_get_next_batch_only_pending():
    """Test that get_next_batch only returns PENDING messages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)

        # Create messages with different statuses
        msg1 = QueuedMessage(priority=1, payload={"id": 1}, status=MessageStatus.PENDING)
        msg2 = QueuedMessage(priority=2, payload={"id": 2}, status=MessageStatus.SENT)
        msg3 = QueuedMessage(priority=3, payload={"id": 3}, status=MessageStatus.PENDING)

        await dao.enqueue(msg1)
        await dao.enqueue(msg2)
        await dao.enqueue(msg3)

        # Get batch should only return PENDING messages
        batch = await dao.get_next_batch(limit=10)
        assert len(batch) == 2
        assert all(msg.status == MessageStatus.PENDING for msg in batch)


@pytest.mark.asyncio
async def test_delete_message():
    """Test deleting a message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)

        # Create and enqueue a message
        msg = QueuedMessage(priority=1, payload={"test": "data"})
        await dao.enqueue(msg)

        # Delete the message
        result = await dao.delete(msg.id)
        assert result is True

        # Verify message is gone
        retrieved = await dao.get_by_id(msg.id)
        assert retrieved is None


@pytest.mark.asyncio
async def test_delete_nonexistent_message():
    """Test deleting a non-existent message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)

        # Try to delete a non-existent message
        result = await dao.delete(uuid4())
        assert result is False


@pytest.mark.asyncio
async def test_update_status():
    """Test updating message status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)

        # Create and enqueue a message
        msg = QueuedMessage(priority=1, payload={"test": "data"})
        await dao.enqueue(msg)

        # Update status
        result = await dao.update_status(msg.id, MessageStatus.SENT)
        assert result is True

        # Verify status was updated
        retrieved = await dao.get_by_id(msg.id)
        assert retrieved is not None
        assert retrieved.status == MessageStatus.SENT


@pytest.mark.asyncio
async def test_get_by_id():
    """Test retrieving a message by ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)

        # Create and enqueue a message
        msg = QueuedMessage(
            priority=7,
            payload={"to": "5678", "content": "Test"},
        )
        await dao.enqueue(msg)

        # Retrieve by ID
        retrieved = await dao.get_by_id(msg.id)
        assert retrieved is not None
        assert retrieved.id == msg.id
        assert retrieved.priority == msg.priority
        assert retrieved.payload == msg.payload

        # Try to get non-existent message
        not_found = await dao.get_by_id(uuid4())
        assert not_found is None
