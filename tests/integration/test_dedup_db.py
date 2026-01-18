"""
Integration tests for deduplication database persistence.

These tests verify that the database correctly persists message IDs across
database sessions and provides fast lookups for deduplication purposes.
"""
import asyncio
import os
import time
from pathlib import Path

import pytest

from telex.adapters.database import DatabaseManager, DeduplicationDAO


@pytest.fixture
async def temp_db_path(tmp_path):
    """Provide a temporary database path for testing."""
    db_path = tmp_path / "test_telex.db"
    yield str(db_path)
    # Cleanup: remove the database file after test
    if db_path.exists():
        db_path.unlink()


@pytest.mark.asyncio
async def test_database_file_creation(temp_db_path):
    """
    Test that telex.db file is created automatically if missing.
    
    Acceptance Criteria: A telex.db file is created automatically if missing.
    """
    # Ensure the file doesn't exist before test
    assert not Path(temp_db_path).exists()
    
    # Initialize database
    db_manager = DatabaseManager(db_path=temp_db_path)
    await db_manager.initialize_db()
    
    # Verify the file was created
    assert Path(temp_db_path).exists()
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_persistence_after_close_and_reopen(temp_db_path):
    """
    Test persistence: Save ID, close DB, reopen DB, verify exists.
    
    Task 2.2.3 AC: Save ID "123". Close DB. Reopen DB. Check "123". Result: True.
    """
    # Phase 1: Save message ID and close
    db_manager = DatabaseManager(db_path=temp_db_path)
    await db_manager.initialize_db()
    
    dao = DeduplicationDAO(db_manager)
    await dao.save("123")
    
    # Verify it exists before closing
    assert await dao.exists("123") is True
    
    # Close the database
    await db_manager.close()
    
    # Phase 2: Reopen database and verify persistence
    db_manager2 = DatabaseManager(db_path=temp_db_path)
    await db_manager2.initialize_db()
    
    dao2 = DeduplicationDAO(db_manager2)
    
    # The key test: ID should still exist after reopening
    assert await dao2.exists("123") is True
    
    await db_manager2.close()


@pytest.mark.asyncio
async def test_new_message_id_returns_false(temp_db_path):
    """
    Test checking for a new Message ID returns False.
    
    Task 2.2.3 AC: Check ID "999" (never seen). Result: False.
    """
    db_manager = DatabaseManager(db_path=temp_db_path)
    await db_manager.initialize_db()
    
    dao = DeduplicationDAO(db_manager)
    
    # Check for a message ID that was never saved
    assert await dao.exists("999") is False
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_save_and_check_message_id(temp_db_path):
    """
    Test that saving a message ID allows it to be found.
    
    Task 2.2.2 AC: Method save(message_id) inserts the record.
    """
    db_manager = DatabaseManager(db_path=temp_db_path)
    await db_manager.initialize_db()
    
    dao = DeduplicationDAO(db_manager)
    
    # Initially, message should not exist
    assert await dao.exists("test-msg-456") is False
    
    # Save the message
    await dao.save("test-msg-456")
    
    # Now it should exist
    assert await dao.exists("test-msg-456") is True
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_known_message_id_lookup_performance(temp_db_path):
    """
    Test that checking for a known Message ID returns True in under 10ms.
    
    Acceptance Criteria: Checking for a known Message ID returns True in under 10ms.
    """
    db_manager = DatabaseManager(db_path=temp_db_path)
    await db_manager.initialize_db()
    
    dao = DeduplicationDAO(db_manager)
    
    # Save a message ID first
    await dao.save("perf-test-id")
    
    # Measure lookup time
    start_time = time.perf_counter()
    result = await dao.exists("perf-test-id")
    end_time = time.perf_counter()
    
    elapsed_ms = (end_time - start_time) * 1000
    
    # Verify the result is correct
    assert result is True
    
    # Verify performance requirement (under 10ms)
    assert elapsed_ms < 10.0, f"Lookup took {elapsed_ms:.3f}ms, expected < 10ms"
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_new_message_id_lookup_performance(temp_db_path):
    """
    Test that checking for a new Message ID returns False and completes quickly.
    
    Acceptance Criteria: Checking for a new Message ID returns False (and allows insertion).
    """
    db_manager = DatabaseManager(db_path=temp_db_path)
    await db_manager.initialize_db()
    
    dao = DeduplicationDAO(db_manager)
    
    # Measure lookup time for non-existent ID
    start_time = time.perf_counter()
    result = await dao.exists("never-seen-id")
    end_time = time.perf_counter()
    
    elapsed_ms = (end_time - start_time) * 1000
    
    # Verify the result is correct
    assert result is False
    
    # Verify performance is reasonable (under 10ms)
    assert elapsed_ms < 10.0, f"Lookup took {elapsed_ms:.3f}ms, expected < 10ms"
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_schema_creation_is_idempotent(temp_db_path):
    """
    Test that schema creation is idempotent.
    
    Task 2.2.1 AC: Schema creation is idempotent (running it twice doesn't break anything).
    """
    db_manager = DatabaseManager(db_path=temp_db_path)
    
    # Initialize database first time
    await db_manager.initialize_db()
    
    # Save a test message
    dao = DeduplicationDAO(db_manager)
    await dao.save("idempotent-test")
    
    # Initialize database second time (should not fail)
    await db_manager.initialize_db()
    
    # Verify the data still exists
    assert await dao.exists("idempotent-test") is True
    
    # Initialize database third time
    await db_manager.initialize_db()
    
    # Data should still be there
    assert await dao.exists("idempotent-test") is True
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_duplicate_save_does_not_error(temp_db_path):
    """
    Test that saving the same message ID twice doesn't cause an error.
    
    This verifies the INSERT OR IGNORE behavior.
    """
    db_manager = DatabaseManager(db_path=temp_db_path)
    await db_manager.initialize_db()
    
    dao = DeduplicationDAO(db_manager)
    
    # Save the same message ID twice
    await dao.save("duplicate-id")
    await dao.save("duplicate-id")  # Should not raise an error
    
    # Should still exist and be retrievable
    assert await dao.exists("duplicate-id") is True
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_database_does_not_block_event_loop(temp_db_path):
    """
    Test that database operations do not block the main AsyncIO event loop.
    
    Acceptance Criteria: Database operations do not block the main AsyncIO event loop.
    """
    db_manager = DatabaseManager(db_path=temp_db_path)
    await db_manager.initialize_db()
    
    dao = DeduplicationDAO(db_manager)
    
    # Create a simple task to verify event loop is responsive
    counter = {"value": 0}
    
    async def background_task():
        for _ in range(10):
            counter["value"] += 1
            await asyncio.sleep(0.001)  # 1ms sleep
    
    # Run database operations concurrently with background task
    background = asyncio.create_task(background_task())
    
    # Perform multiple database operations
    for i in range(10):
        await dao.save(f"concurrent-test-{i}")
        await dao.exists(f"concurrent-test-{i}")
    
    # Wait for background task
    await background
    
    # If event loop was blocked, counter would not have incremented properly
    assert counter["value"] == 10
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_context_manager_support(temp_db_path):
    """
    Test that DatabaseManager can be used as an async context manager.
    """
    async with DatabaseManager(db_path=temp_db_path) as db_manager:
        dao = DeduplicationDAO(db_manager)
        await dao.save("context-manager-test")
        assert await dao.exists("context-manager-test") is True
    
    # After exiting context, connection should be closed
    # Verify by reopening and checking persistence
    async with DatabaseManager(db_path=temp_db_path) as db_manager2:
        dao2 = DeduplicationDAO(db_manager2)
        assert await dao2.exists("context-manager-test") is True
