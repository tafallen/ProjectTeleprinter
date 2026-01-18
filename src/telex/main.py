"""
Main entry point for the Telex server application.
"""
import asyncio
import logging
import os
import signal
import sys
from typing import Optional

import structlog

from telex.utils.config import load_config
from telex.core import DatabaseManager, MessageQueueDAO, GarbageCollector


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

    def __init__(self, config_file: Optional[str] = None):
        self.running = False
        self.tasks: list[asyncio.Task] = []
        self.tcp_server: Optional[asyncio.Server] = None
        
        # Load configuration
        self.config = load_config(config_file)
        logger.info("Configuration loaded", node_id=self.config.node_id)

        # Initialize core components (will be started in start())
        self.db_manager: Optional[DatabaseManager] = None
        self.message_dao: Optional[MessageQueueDAO] = None
        self.garbage_collector: Optional[GarbageCollector] = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming client connections."""
        addr = writer.get_extra_info('peername')
        logger.info("Connection received", address=addr)
        print("Connection Received")
        
        try:
            # Close the connection immediately after acknowledgment
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logger.error("Error closing connection", error=str(e))

    async def start(self):
        """Start the Telex server and all its components."""
        logger.info("Starting Telex server", version="0.1.0")
        self.running = True

        try:
            # Initialize database
            self.db_manager = DatabaseManager(self.config.database_path)
            await self.db_manager.initialize()
            logger.info("Database initialized", path=str(self.config.database_path))

            # Initialize message queue DAO
            self.message_dao = MessageQueueDAO(self.db_manager)
            logger.info("Message queue DAO initialized")

            # Start garbage collector
            self.garbage_collector = GarbageCollector(
                self.db_manager,
                ttl_hours=self.config.message_ttl_hours,
                interval_seconds=60,
            )
            await self.garbage_collector.start()
            logger.info("Garbage collector started")

            # TODO: Initialize routing engine
            
            # Start network listener
            self.tcp_server = await asyncio.start_server(
                self.handle_client,
                self.config.listen_host,
                self.config.listen_port
            )
            
            addrs = ', '.join(str(sock.getsockname()) for sock in self.tcp_server.sockets)
            logger.info("TCP server listening", addresses=addrs)
            print(f"TCP server listening on {addrs}")
            
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

        # Stop garbage collector
        if self.garbage_collector:
            await self.garbage_collector.stop()
            logger.info("Garbage collector stopped")

        # Close TCP server
        if self.tcp_server:
            self.tcp_server.close()
            await self.tcp_server.wait_closed()
            logger.info("TCP server closed")

        # Cancel all running tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        # Close database connections
        if self.db_manager:
            await self.db_manager.close()
            logger.info("Database closed")

        # TODO: Flush message queue
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
    # Check for config file (e.g., mounted in Docker at /etc/telex/config.json)
    config_file = os.environ.get('TELEX_CONFIG_FILE', '/etc/telex/config.json')
    if not os.path.exists(config_file):
        config_file = None
    
    server = TelexServer(config_file=config_file)

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
