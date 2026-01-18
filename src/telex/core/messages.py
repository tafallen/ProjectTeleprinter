"""
Message models for the Telex system.

Defines the TelexMessage Pydantic model for strict validation of incoming
and outgoing messages in the mesh network.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TraceEntry(BaseModel):
    """A single entry in the message trace (hop record)."""

    node_id: str = Field(description="Node ID that processed this message")
    timestamp: datetime = Field(description="ISO-8601 timestamp when node processed message")

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        """Validate and parse ISO-8601 timestamp."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class RoutingInfo(BaseModel):
    """Routing information for a telex message."""

    source: str = Field(description="Source address in XXXY format")
    destination: str = Field(description="Destination address in XXXY format")
    priority: int = Field(default=5, ge=1, le=9, description="Message priority (1=highest, 9=lowest)")


class MessageContent(BaseModel):
    """The actual message content/body."""

    subject: Optional[str] = Field(default=None, description="Message subject line")
    body: str = Field(description="Message body text")
    content_type: str = Field(default="text/plain", description="MIME type of content")


class TelexMessage(BaseModel):
    """
    A Telex message in the mesh network.
    
    This model enforces strict validation of all message fields including:
    - UUID4 format for message_id
    - ISO-8601 format for timestamps
    - Required routing and content fields
    - Optional trace list for hop recording
    """

    message_id: UUID = Field(
        default_factory=uuid4,
        description="Unique message identifier (UUID4 format)"
    )
    timestamp_created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO-8601 timestamp when message was created"
    )
    routing: RoutingInfo = Field(description="Routing information")
    content: MessageContent = Field(description="Message content")
    trace: List[TraceEntry] = Field(
        default_factory=list,
        description="List of nodes this message has passed through"
    )

    @field_validator("timestamp_created", mode="before")
    @classmethod
    def validate_timestamp_created(cls, v):
        """Validate and parse ISO-8601 timestamp for timestamp_created."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp_created": "2024-01-01T12:00:00Z",
                "routing": {
                    "source": "1234",
                    "destination": "5678",
                    "priority": 5
                },
                "content": {
                    "subject": "Test Message",
                    "body": "Hello, World!",
                    "content_type": "text/plain"
                },
                "trace": []
            }
        }
    )
