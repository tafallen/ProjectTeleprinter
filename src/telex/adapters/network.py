"""
Network adapter for async TCP communication.

Implements the AsyncTCPNetworkAdapter which listens on a TCP port,
receives line-delimited JSON messages, and parses them into TelexMessage objects.
"""

import asyncio
import json
from typing import Awaitable, Callable, Optional

import structlog
from pydantic import ValidationError

from telex.core.messages import TelexMessage

logger = structlog.get_logger(__name__)


class AsyncTCPNetworkAdapter:
    """
    Async TCP Network Adapter for the Telex system.

    This adapter:
    - Starts a TCP server on a specified host and port
    - Accepts multiple concurrent connections (non-blocking)
    - Uses line-delimited JSON framing (messages end with \\n)
    - Parses and validates incoming data into TelexMessage objects
    - Handles errors gracefully (invalid JSON, validation errors)
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8023,
        message_handler: Optional[Callable[[TelexMessage], Awaitable[None]]] = None,
    ):
        """
        Initialize the AsyncTCPNetworkAdapter.

        Args:
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
            port: Port to bind to (default: 8023)
            message_handler: Optional async callback to handle valid messages
        """
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self.server: Optional[asyncio.Server] = None
        self._running = False

    async def start(self):
        """Start the TCP server."""
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        self._running = True

        addrs = ", ".join(str(sock.getsockname()) for sock in self.server.sockets)
        logger.info("TCP server started", addresses=addrs)

        return self.server

    async def stop(self):
        """Stop the TCP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self._running = False
            logger.info("TCP server stopped")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handle an incoming client connection.

        Args:
            reader: StreamReader for reading data from client
            writer: StreamWriter for writing data to client
        """
        addr = writer.get_extra_info("peername")
        logger.info("Client connected", address=addr)

        try:
            while self._running:
                # Read until newline delimiter (line-delimited JSON)
                line = await reader.readline()

                if not line:
                    # Connection closed by client
                    logger.info("Client disconnected", address=addr)
                    break

                # Decode the line
                try:
                    line_str = line.decode("utf-8").strip()
                except UnicodeDecodeError as e:
                    logger.error("Invalid UTF-8 encoding", address=addr, error=str(e))
                    await self._send_error(writer, "Invalid UTF-8 encoding")
                    writer.close()
                    await writer.wait_closed()
                    break

                if not line_str:
                    continue

                # Parse JSON and validate as TelexMessage
                try:
                    # Parse JSON
                    message_data = json.loads(line_str)

                    # Validate with Pydantic model
                    message = TelexMessage.model_validate(message_data)

                    logger.info(
                        "Valid message received", address=addr, message_id=str(message.message_id)
                    )

                    # Call the message handler if provided
                    if self.message_handler:
                        await self.message_handler(message)

                except json.JSONDecodeError as e:
                    logger.error(
                        "Malformed JSON",
                        address=addr,
                        error=str(e),
                        line=line_str[:100],  # Log first 100 chars
                    )
                    await self._send_error(writer, f"Malformed JSON: {str(e)}")
                    writer.close()
                    await writer.wait_closed()
                    break

                except ValidationError as e:
                    logger.error(
                        "Message validation failed",
                        address=addr,
                        error=str(e),
                        line=line_str[:100],  # Log first 100 chars
                    )
                    await self._send_error(writer, f"Validation error: {str(e)}")
                    writer.close()
                    await writer.wait_closed()
                    break

        except Exception as e:
            logger.error(
                "Unexpected error handling client", address=addr, error=str(e), exc_info=True
            )
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _send_error(self, writer: asyncio.StreamWriter, error_message: str):
        """
        Send an error message to the client.

        Args:
            writer: StreamWriter to send error to
            error_message: Error message to send
        """
        try:
            error_response = json.dumps({"error": error_message}) + "\n"
            writer.write(error_response.encode("utf-8"))
            await writer.drain()
        except Exception as e:
            logger.error("Failed to send error response", error=str(e))
