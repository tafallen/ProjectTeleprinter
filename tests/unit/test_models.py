"""
Unit tests for message queue models.
"""
from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from telex.core.models import QueuedMessage, MessageStatus


def test_queued_message_defaults():
    """Test default values for QueuedMessage."""
    msg = QueuedMessage()

    assert isinstance(msg.id, UUID)
    assert msg.priority == 0
    assert msg.payload == {}
    assert isinstance(msg.created_at, datetime)
    assert msg.status == MessageStatus.PENDING


def test_queued_message_with_values():
    """Test creating QueuedMessage with custom values."""
    payload = {"to": "1234", "from": "0001", "content": "Test message"}
    msg = QueuedMessage(priority=5, payload=payload)

    assert msg.priority == 5
    assert msg.payload == payload
    assert msg.status == MessageStatus.PENDING


def test_queued_message_priority_validation():
    """Test priority validation."""
    # Valid priorities
    msg1 = QueuedMessage(priority=0)
    assert msg1.priority == 0

    msg2 = QueuedMessage(priority=10)
    assert msg2.priority == 10

    msg3 = QueuedMessage(priority=5)
    assert msg3.priority == 5

    # Invalid priorities should raise validation error
    with pytest.raises(ValidationError):
        QueuedMessage(priority=-1)

    with pytest.raises(ValidationError):
        QueuedMessage(priority=11)


def test_message_status_enum():
    """Test MessageStatus enum values."""
    assert MessageStatus.PENDING.value == "PENDING"
    assert MessageStatus.SENT.value == "SENT"
    assert MessageStatus.FAILED.value == "FAILED"
    assert MessageStatus.EXPIRED.value == "EXPIRED"


def test_queued_message_json_serialization():
    """Test that QueuedMessage can be serialized."""
    msg = QueuedMessage(
        priority=7,
        payload={"test": "data"},
        status=MessageStatus.PENDING,
    )

    # Test model_dump works
    data = msg.model_dump()
    assert "id" in data
    assert "priority" in data
    assert "payload" in data
    assert "created_at" in data
    assert "status" in data

    # Test model_dump_json works
    json_str = msg.model_dump_json()
    assert isinstance(json_str, str)
    assert "test" in json_str
    assert "PENDING" in json_str
