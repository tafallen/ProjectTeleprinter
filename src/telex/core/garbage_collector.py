"""
Garbage collector service for cleaning up expired messages.
"""
import asyncio
from datetime import datetime, timedelta, UTC
from typing import Optional

import structlog

from telex.core.database import DatabaseManager
from telex.core.models import MessageStatus

logger = structlog.get_logger(__name__)


class GarbageCollector:
    """
    Background service that deletes messages older than TTL.
    
    Runs periodically to cleanup expired messages from the queue.
    """

    def __init__(
        self, db_manager: DatabaseManager, ttl_hours: int = 72, interval_seconds: int = 60
    ):
        """
        Initialize the garbage collector.
        
        Args:
            db_manager: Database manager instance
            ttl_hours: Time-to-live in hours (default: 72)
            interval_seconds: How often to run cleanup (default: 60)
        """
        self.db_manager = db_manager
        self.ttl_hours = ttl_hours
        self.interval_seconds = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """
        Start the garbage collector background task.
        """
        if self._running:
            logger.warning("Garbage collector already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "Garbage collector started",
            ttl_hours=self.ttl_hours,
            interval_seconds=self.interval_seconds,
        )

    async def stop(self) -> None:
        """
        Stop the garbage collector background task.
        """
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Garbage collector stopped")

    async def _run_loop(self) -> None:
        """
        Main loop that runs cleanup periodically.
        """
        while self._running:
            try:
                await self._cleanup_expired()
            except Exception as e:
                logger.error("Error during garbage collection", error=str(e), exc_info=True)

            # Wait for next interval
            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break

    async def _cleanup_expired(self) -> None:
        """
        Delete messages older than TTL.
        """
        # Calculate cutoff time
        cutoff_time = datetime.now(UTC) - timedelta(hours=self.ttl_hours)
        cutoff_str = cutoff_time.isoformat()

        conn = await self.db_manager.get_connection()
        try:
            # Delete expired messages and count them
            cursor = await conn.execute(
                """
                DELETE FROM message_queue
                WHERE created_at < ?
                """,
                (cutoff_str,),
            )
            await conn.commit()

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                logger.info(
                    "TTL Expired - Garbage collection completed",
                    deleted_count=deleted_count,
                    cutoff_time=cutoff_str,
                    ttl_hours=self.ttl_hours,
                )
            else:
                logger.debug("No expired messages to clean up", cutoff_time=cutoff_str)

        finally:
            await conn.close()

    async def cleanup_now(self) -> int:
        """
        Trigger an immediate cleanup (for testing/manual use).
        
        Returns:
            Number of messages deleted
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=self.ttl_hours)
        cutoff_str = cutoff_time.isoformat()

        conn = await self.db_manager.get_connection()
        try:
            cursor = await conn.execute(
                """
                DELETE FROM message_queue
                WHERE created_at < ?
                """,
                (cutoff_str,),
            )
            await conn.commit()

            deleted_count = cursor.rowcount
            logger.info(
                "Manual garbage collection completed",
                deleted_count=deleted_count,
                cutoff_time=cutoff_str,
            )
            return deleted_count
        finally:
            await conn.close()
