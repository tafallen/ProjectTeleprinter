"""
Data Access Object for message queue operations.
"""
import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import structlog

from telex.core.database import DatabaseManager
from telex.core.models import QueuedMessage, MessageStatus

logger = structlog.get_logger(__name__)


class MessageQueueDAO:
    """
    Data Access Object for message queue operations.
    
    Provides CRUD operations for the message_queue table.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the DAO.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    async def enqueue(self, msg: QueuedMessage) -> None:
        """
        Enqueue a message for persistent storage.
        
        Serializes the Pydantic model to JSON and inserts into the database.
        
        Args:
            msg: Message to enqueue
        """
        conn = await self.db_manager.get_connection()
        try:
            # Serialize payload to JSON
            payload_json = json.dumps(msg.payload)

            await conn.execute(
                """
                INSERT INTO message_queue (id, priority, payload, created_at, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(msg.id),
                    msg.priority,
                    payload_json,
                    msg.created_at.isoformat(),
                    msg.status.value,
                ),
            )
            await conn.commit()
            logger.info(
                "Message enqueued",
                message_id=str(msg.id),
                priority=msg.priority,
                status=msg.status.value,
            )
        finally:
            await conn.close()

    async def get_next_batch(self, limit: int = 10) -> List[QueuedMessage]:
        """
        Get the next batch of pending messages.
        
        Returns oldest PENDING messages in FIFO order (ordered by created_at ASC).
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of queued messages
        """
        conn = await self.db_manager.get_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT id, priority, payload, created_at, status
                FROM message_queue
                WHERE status = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (MessageStatus.PENDING.value, limit),
            )
            rows = await cursor.fetchall()

            messages = []
            for row in rows:
                try:
                    msg = QueuedMessage(
                        id=UUID(row["id"]),
                        priority=row["priority"],
                        payload=json.loads(row["payload"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        status=MessageStatus(row["status"]),
                    )
                    messages.append(msg)
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.error(
                        "Error parsing message from database",
                        message_id=row["id"],
                        error=str(e),
                    )

            logger.debug("Retrieved message batch", count=len(messages), limit=limit)
            return messages
        finally:
            await conn.close()

    async def delete(self, message_id: UUID) -> bool:
        """
        Delete a message from the queue.
        
        Typically called after successful send.
        
        Args:
            message_id: ID of the message to delete
            
        Returns:
            True if message was deleted, False if not found
        """
        conn = await self.db_manager.get_connection()
        try:
            cursor = await conn.execute(
                """
                DELETE FROM message_queue
                WHERE id = ?
                """,
                (str(message_id),),
            )
            await conn.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("Message deleted", message_id=str(message_id))
            else:
                logger.warning("Message not found for deletion", message_id=str(message_id))

            return deleted
        finally:
            await conn.close()

    async def update_status(self, message_id: UUID, status: MessageStatus) -> bool:
        """
        Update the status of a message.
        
        Args:
            message_id: ID of the message to update
            status: New status
            
        Returns:
            True if message was updated, False if not found
        """
        conn = await self.db_manager.get_connection()
        try:
            cursor = await conn.execute(
                """
                UPDATE message_queue
                SET status = ?
                WHERE id = ?
                """,
                (status.value, str(message_id)),
            )
            await conn.commit()

            updated = cursor.rowcount > 0
            if updated:
                logger.info(
                    "Message status updated",
                    message_id=str(message_id),
                    status=status.value,
                )
            else:
                logger.warning(
                    "Message not found for status update", message_id=str(message_id)
                )

            return updated
        finally:
            await conn.close()

    async def get_by_id(self, message_id: UUID) -> Optional[QueuedMessage]:
        """
        Get a message by ID.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            Message if found, None otherwise
        """
        conn = await self.db_manager.get_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT id, priority, payload, created_at, status
                FROM message_queue
                WHERE id = ?
                """,
                (str(message_id),),
            )
            row = await cursor.fetchone()

            if row:
                return QueuedMessage(
                    id=UUID(row["id"]),
                    priority=row["priority"],
                    payload=json.loads(row["payload"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    status=MessageStatus(row["status"]),
                )
            return None
        finally:
            await conn.close()
