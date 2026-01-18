"""
Main entry point for the Telex server application.
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

import structlog


# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class TelexServer:
    """Main Telex server class that coordinates all components."""

    def __init__(self):
        self.running = False
        self.tasks: list[asyncio.Task] = []

    async def start(self):
        """Start the Telex server and all its components."""
        logger.info("Starting Telex server", version="0.1.0")
        self.running = True

        try:
            # TODO: Initialize database
            # TODO: Initialize message queue
            # TODO: Initialize routing engine
            # TODO: Start network listener
            # TODO: Initialize hardware interface (if available)

            logger.info("Telex server started successfully")

            # Keep running until shutdown
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error("Error in Telex server", error=str(e), exc_info=True)
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the Telex server and cleanup resources."""
        logger.info("Stopping Telex server")
        self.running = False

        # Cancel all running tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        # TODO: Close database connections
        # TODO: Flush message queue
        # TODO: Close network connections
        # TODO: Cleanup hardware interface

        logger.info("Telex server stopped")


def handle_signal(server: TelexServer):
    """Signal handler for graceful shutdown."""

    def _handler(signum, frame):
        logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(server.stop())

    return _handler


async def async_main():
    """Async main function."""
    server = TelexServer()

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal(server))
    signal.signal(signal.SIGTERM, handle_signal(server))

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Fatal error in server", error=str(e), exc_info=True)
        return 1

    return 0


def main():
    """Main entry point for the application."""
    try:
        exit_code = asyncio.run(async_main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
