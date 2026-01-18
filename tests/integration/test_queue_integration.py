"""
Integration test for persistent queue and TTL logic.
"""
import asyncio
from datetime import datetime, timedelta, UTC
from pathlib import Path
import tempfile

import pytest

from telex.core import DatabaseManager, MessageQueueDAO, GarbageCollector, QueuedMessage


@pytest.mark.asyncio
async def test_full_queue_lifecycle():
    """Test the complete lifecycle of messages through the queue system."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Initialize components
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)
        gc = GarbageCollector(db_manager, ttl_hours=1, interval_seconds=5)

        # Start garbage collector
        await gc.start()

        try:
            # 1. Enqueue some messages
            msg1 = QueuedMessage(
                priority=5,
                payload={"to": "1234", "from": "0001", "content": "Message 1"},
            )
            msg2 = QueuedMessage(
                priority=3,
                payload={"to": "5678", "from": "0001", "content": "Message 2"},
            )

            await dao.enqueue(msg1)
            await dao.enqueue(msg2)

            # 2. Retrieve messages
            batch = await dao.get_next_batch(limit=10)
            assert len(batch) == 2

            # 3. Delete one message (simulating successful send)
            await dao.delete(msg1.id)

            batch = await dao.get_next_batch(limit=10)
            assert len(batch) == 1
            assert batch[0].id == msg2.id

            # 4. Add an old message (to be cleaned up)
            old_msg = QueuedMessage(
                priority=1,
                payload={"old": True},
                created_at=datetime.now(UTC) - timedelta(hours=2),
            )
            await dao.enqueue(old_msg)

            # 5. Wait for garbage collector to clean up
            await asyncio.sleep(6)

            # Old message should be gone
            retrieved = await dao.get_by_id(old_msg.id)
            assert retrieved is None

            # Recent message should still exist
            retrieved = await dao.get_by_id(msg2.id)
            assert retrieved is not None

        finally:
            # Cleanup
            await gc.stop()
            await db_manager.close()


@pytest.mark.asyncio
async def test_message_priority_ordering():
    """Test that messages are ordered correctly by created_at (FIFO)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()

        dao = MessageQueueDAO(db_manager)

        # Create messages with different timestamps
        messages = []
        for i in range(3):
            msg = QueuedMessage(
                priority=i,
                payload={"order": i},
                created_at=datetime.now(UTC) - timedelta(minutes=10 - i),
            )
            messages.append(msg)
            await dao.enqueue(msg)
            # Small delay to ensure timestamps are different
            await asyncio.sleep(0.01)

        # Get batch - should be ordered by created_at ASC (FIFO)
        batch = await dao.get_next_batch(limit=10)
        assert len(batch) == 3

        # Should be ordered oldest first (FIFO)
        assert batch[0].payload["order"] == 0
        assert batch[1].payload["order"] == 1
        assert batch[2].payload["order"] == 2

        await db_manager.close()
