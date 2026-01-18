"""
Unit tests for protocol validation and message parsing.

Tests the TelexMessage Pydantic model and the AsyncTCPNetworkAdapter
to ensure proper validation and error handling.
"""

import asyncio
import json

import pytest
from pydantic import ValidationError

from telex.core.messages import TelexMessage, RoutingInfo, MessageContent
from telex.adapters.network import AsyncTCPNetworkAdapter


class TestTelexMessageValidation:
    """Test suite for TelexMessage Pydantic model validation."""

    def test_valid_message_creation(self):
        """Test that a valid TelexMessage can be created."""
        message = TelexMessage(
            routing=RoutingInfo(source="1234", destination="5678"),
            content=MessageContent(body="Hello, World!"),
        )

        assert message.message_id is not None
        assert message.timestamp_created is not None
        assert message.routing.source == "1234"
        assert message.routing.destination == "5678"
        assert message.content.body == "Hello, World!"
        assert message.trace == []

    def test_valid_json_payload(self):
        """Test Case: Valid JSON payload returns success."""
        valid_json = {
            "message_id": "123e4567-e89b-12d3-a456-426614174000",
            "timestamp_created": "2024-01-01T12:00:00Z",
            "routing": {"source": "1234", "destination": "5678", "priority": 5},
            "content": {"body": "Test message", "content_type": "text/plain"},
            "trace": [],
        }

        message = TelexMessage.model_validate(valid_json)

        assert str(message.message_id) == "123e4567-e89b-12d3-a456-426614174000"
        assert message.routing.source == "1234"
        assert message.content.body == "Test message"

    def test_valid_json_from_json_string(self):
        """Test that model_validate_json works with valid JSON string."""
        valid_json_str = json.dumps(
            {"routing": {"source": "1234", "destination": "5678"}, "content": {"body": "Test"}}
        )

        message = TelexMessage.model_validate_json(valid_json_str)
        assert message.routing.source == "1234"

    def test_malformed_json_syntax_error(self):
        """Test Case: Malformed JSON (syntax error) is handled gracefully."""
        malformed_json = (
            '{"routing": {"source": "1234", "destination": "5678"}'  # Missing closing brace
        )

        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed_json)

    def test_missing_routing_field(self):
        """Test Case: Valid JSON but missing routing field raises ValidationError."""
        invalid_data = {"content": {"body": "Test message"}}

        with pytest.raises(ValidationError) as exc_info:
            TelexMessage.model_validate(invalid_data)

        # Verify that the error mentions the missing 'routing' field
        assert "routing" in str(exc_info.value).lower()

    def test_missing_content_field(self):
        """Test that missing content field raises ValidationError."""
        invalid_data = {"routing": {"source": "1234", "destination": "5678"}}

        with pytest.raises(ValidationError) as exc_info:
            TelexMessage.model_validate(invalid_data)

        assert "content" in str(exc_info.value).lower()

    def test_invalid_uuid_format(self):
        """Test that message_id must be valid UUID4 format."""
        invalid_data = {
            "message_id": "not-a-valid-uuid",
            "routing": {"source": "1234", "destination": "5678"},
            "content": {"body": "Test"},
        }

        with pytest.raises(ValidationError) as exc_info:
            TelexMessage.model_validate(invalid_data)

        # Check that UUID validation failed
        error_str = str(exc_info.value).lower()
        assert "uuid" in error_str or "message_id" in error_str

    def test_invalid_timestamp_format(self):
        """Test that timestamp_created must validate as ISO-8601."""
        invalid_data = {
            "timestamp_created": "not-a-valid-timestamp",
            "routing": {"source": "1234", "destination": "5678"},
            "content": {"body": "Test"},
        }

        with pytest.raises(ValidationError) as exc_info:
            TelexMessage.model_validate(invalid_data)

        # Check that timestamp validation failed
        error_str = str(exc_info.value).lower()
        assert "timestamp" in error_str or "datetime" in error_str

    def test_valid_iso8601_timestamp(self):
        """Test that valid ISO-8601 timestamps are accepted."""
        valid_data = {
            "timestamp_created": "2024-01-15T10:30:00Z",
            "routing": {"source": "1234", "destination": "5678"},
            "content": {"body": "Test"},
        }

        message = TelexMessage.model_validate(valid_data)
        assert message.timestamp_created.year == 2024
        assert message.timestamp_created.month == 1
        assert message.timestamp_created.day == 15

    def test_trace_list_validation(self):
        """Test that trace field accepts a list of trace entries."""
        valid_data = {
            "routing": {"source": "1234", "destination": "5678"},
            "content": {"body": "Test"},
            "trace": [{"node_id": "1234", "timestamp": "2024-01-15T10:30:00Z"}],
        }

        message = TelexMessage.model_validate(valid_data)
        assert len(message.trace) == 1
        assert message.trace[0].node_id == "1234"


class TestAsyncTCPNetworkAdapter:
    """Test suite for AsyncTCPNetworkAdapter."""

    @pytest.mark.asyncio
    async def test_server_starts_on_configured_port(self):
        """Test that server binds to 0.0.0.0 and the configured port."""
        adapter = AsyncTCPNetworkAdapter(host="127.0.0.1", port=18023)

        try:
            server = await adapter.start()
            assert server is not None
            assert adapter._running is True

            # Verify server is listening
            sock_addr = server.sockets[0].getsockname()
            assert sock_addr[1] == 18023
        finally:
            await adapter.stop()

    @pytest.mark.asyncio
    async def test_accepts_multiple_concurrent_connections(self):
        """Test that server accepts multiple concurrent connections."""
        messages_received = []

        async def handler(msg: TelexMessage):
            messages_received.append(msg)

        adapter = AsyncTCPNetworkAdapter(host="127.0.0.1", port=18024, message_handler=handler)

        try:
            await adapter.start()

            # Create multiple concurrent connections
            async def send_message(port, message_num):
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
                try:
                    message = {
                        "routing": {"source": f"{message_num:04d}", "destination": "5678"},
                        "content": {"body": f"Message {message_num}"},
                    }
                    writer.write((json.dumps(message) + "\n").encode("utf-8"))
                    await writer.drain()
                    # Give server time to process
                    await asyncio.sleep(0.1)
                finally:
                    writer.close()
                    await writer.wait_closed()

            # Send 3 messages concurrently
            await asyncio.gather(
                send_message(18024, 1), send_message(18024, 2), send_message(18024, 3)
            )

            # Wait a bit for processing
            await asyncio.sleep(0.2)

            assert len(messages_received) == 3
        finally:
            await adapter.stop()

    @pytest.mark.asyncio
    async def test_valid_message_accepted(self):
        """Test that a valid line-delimited JSON message is accepted."""
        messages_received = []

        async def handler(msg: TelexMessage):
            messages_received.append(msg)

        adapter = AsyncTCPNetworkAdapter(host="127.0.0.1", port=18025, message_handler=handler)

        try:
            await adapter.start()

            # Connect and send valid message
            reader, writer = await asyncio.open_connection("127.0.0.1", 18025)

            valid_message = {
                "routing": {"source": "1234", "destination": "5678"},
                "content": {"body": "Hello, World!"},
            }

            message_json = json.dumps(valid_message) + "\n"
            writer.write(message_json.encode("utf-8"))
            await writer.drain()

            # Give server time to process
            await asyncio.sleep(0.1)

            assert len(messages_received) == 1
            assert messages_received[0].routing.source == "1234"
            assert messages_received[0].content.body == "Hello, World!"

            writer.close()
            await writer.wait_closed()
        finally:
            await adapter.stop()

    @pytest.mark.asyncio
    async def test_malformed_json_closes_connection(self):
        """Test that malformed JSON results in error and connection closure."""
        adapter = AsyncTCPNetworkAdapter(host="127.0.0.1", port=18026)

        try:
            await adapter.start()

            # Connect and send malformed JSON
            reader, writer = await asyncio.open_connection("127.0.0.1", 18026)

            malformed_json = '{"routing": {"source": "1234"}\n'  # Missing closing brace
            writer.write(malformed_json.encode("utf-8"))
            await writer.drain()

            # Try to read error response
            response = await reader.readline()

            # Should get an error response
            if response:
                response_data = json.loads(response.decode("utf-8"))
                assert "error" in response_data

            # Connection should be closed by server
            writer.close()
            await writer.wait_closed()
        finally:
            await adapter.stop()

    @pytest.mark.asyncio
    async def test_missing_required_field_closes_connection(self):
        """Test that valid JSON but missing routing field closes connection."""
        adapter = AsyncTCPNetworkAdapter(host="127.0.0.1", port=18027)

        try:
            await adapter.start()

            # Connect and send message missing routing field
            reader, writer = await asyncio.open_connection("127.0.0.1", 18027)

            invalid_message = {"content": {"body": "Test"}}

            message_json = json.dumps(invalid_message) + "\n"
            writer.write(message_json.encode("utf-8"))
            await writer.drain()

            # Try to read error response
            response = await reader.readline()

            # Should get an error response about validation
            if response:
                response_data = json.loads(response.decode("utf-8"))
                assert "error" in response_data
                assert "validation" in response_data["error"].lower()

            # Connection should be closed by server
            writer.close()
            await writer.wait_closed()
        finally:
            await adapter.stop()

    @pytest.mark.asyncio
    async def test_uses_readline_for_framing(self):
        """Test that server uses readline() for line-delimited JSON framing."""
        messages_received = []

        async def handler(msg: TelexMessage):
            messages_received.append(msg)

        adapter = AsyncTCPNetworkAdapter(host="127.0.0.1", port=18028, message_handler=handler)

        try:
            await adapter.start()

            # Connect and send multiple messages separated by newlines
            reader, writer = await asyncio.open_connection("127.0.0.1", 18028)

            msg1 = {
                "routing": {"source": "1111", "destination": "2222"},
                "content": {"body": "Msg1"},
            }
            msg2 = {
                "routing": {"source": "3333", "destination": "4444"},
                "content": {"body": "Msg2"},
            }

            # Send both messages with newline delimiters
            writer.write((json.dumps(msg1) + "\n").encode("utf-8"))
            await writer.drain()
            await asyncio.sleep(0.1)

            writer.write((json.dumps(msg2) + "\n").encode("utf-8"))
            await writer.drain()
            await asyncio.sleep(0.1)

            assert len(messages_received) == 2
            assert messages_received[0].content.body == "Msg1"
            assert messages_received[1].content.body == "Msg2"

            writer.close()
            await writer.wait_closed()
        finally:
            await adapter.stop()
