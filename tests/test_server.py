import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from Server.server import Server
from Shared.protocol import Protocol


class TestServer:
    @pytest.fixture
    def setup(self):
        self.server = Server()
        self.websocket_mock = AsyncMock()

    @pytest.mark.asyncio
    async def test_login_success(self, setup):
        user_id = "fake_id"

        request = Protocol.create_message("LOGIN", {"username": user_id})
        await self.server.handle_request(
            json.loads(request), self.websocket_mock
        )

        expected_response = Protocol.create_message(
            "LOGIN", {"status": "success", "user_id": user_id}
        )
        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_open_file_success(self, setup):
        self.server.file_manager.open_file = MagicMock(
            return_value=(True, "A")
        )
        request = Protocol.create_message(
            "OPEN_FILE", {"filename": "testfile.txt"}
        )
        await self.server.handle_request(
            json.loads(request), self.websocket_mock
        )

        expected_response = Protocol.create_message(
            "OPEN_FILE", {"status": "success", "content": "A"}
        )
        self.websocket_mock.send.assert_called_once_with(expected_response)
