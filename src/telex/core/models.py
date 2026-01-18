"""
Data models for the message queue system.
"""
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class MessageStatus(str, Enum):
    """Status of a message in the queue."""

    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class QueuedMessage(BaseModel):
    """
    Represents a message in the persistent queue.
    
    Attributes:
        id: Unique identifier for the message
        priority: Message priority (higher = more important)
        payload: Message content as JSON-serializable dict
        created_at: When the message was queued
        status: Current status of the message
    """

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )

    id: UUID = Field(default_factory=uuid4)
    priority: int = Field(default=0, ge=0, le=10)
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: MessageStatus = Field(default=MessageStatus.PENDING)
