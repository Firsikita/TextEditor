import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

from Server.server import Server
from Shared.protocol import Protocol


class TestServer:
    @pytest.fixture
    def setup(self):
        self.server = Server()
        self.websocket_mock = AsyncMock()
        self.user_sessions = {}

    @pytest.mark.asyncio
    async def test_login_success(self, setup):
        user_id = "fake_id"

        request = Protocol.create_message("LOGIN", {"username": user_id})
        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )

        assert self.websocket_mock in self.server.user_sessions
        assert self.server.user_sessions[self.websocket_mock] == user_id

        expected_response = Protocol.create_response(
            "LOGIN", {"status": "success", "user_id": user_id}
        )
        self.websocket_mock.send.assert_called_once_with(
            json.dumps(expected_response))

    @pytest.mark.asyncio
    async def test_get_files(self, setup):
        self.server.file_manager = MagicMock()
        self.server.file_manager.get_files.return_value = ["file1.txt",
                                                           "file2.txt"]

        request = Protocol.create_message("GET_FILES")

        await self.server.handle_request(Protocol.parse_request(request),
                                         self.websocket_mock)
        expected_response = Protocol.create_response(
            "GET_FILES", {"files": ["file1.txt", "file2.txt"]}
        )
        self.websocket_mock.send.assert_called_once_with(
            json.dumps(expected_response))
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

    @pytest.mark.asyncio
    async def test_open_file_error(self, setup):
        self.server.file_manager.open_file = MagicMock(
            return_value=(False, None)
        )
        request = Protocol.create_message(
            "OPEN_FILE", {"filename": "testfile.txt"}
        )
        await self.server.handle_request(
            json.loads(request), self.websocket_mock
        )
        expected_response = Protocol.create_message(
            "ERROR", {"error": "File not found"}
        )
        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_edit_file(self, setup):
        self.server.session_manager = MagicMock()
        self.server.session_manager.get_content = MagicMock(
            return_value="content"
        )
        self.server.session_manager.share_update = AsyncMock()
        self.server.file_manager.save_file = MagicMock()

        request = Protocol.create_message(
            "EDIT_FILE", {"filename": "testfile.txt",
                          "operation": {"op_type": "insert", "pos": 0,
                                        "char": "A"}}
        )

        await self.server.handle_request(Protocol.parse_request(request),
                                         self.websocket_mock)

        self.server.session_manager.apply_operation.assert_called_once_with(
            "testfile.txt", {"op_type": "insert", "pos": 0, "char": "A"}
        )
        self.server.file_manager.save_file.assert_called_once_with(
            "testfile.txt", "content"
        )

        self.server.session_manager.share_update.assert_called_once_with(
            "testfile.txt", {"op_type": "insert", "pos": 0, "char": "A"},
            self.websocket_mock
        )

    @pytest.mark.asyncio
    async def test_create_file_success(self, setup):
        self.server.file_manager = MagicMock()
        self.server.file_manager.create_file.return_value = (True, None)

        request = Protocol.create_message(
            "CREATE_FILE", {"filename": "newfile.txt"}
        )

        await self.server.handle_request(Protocol.parse_request(request),
                                         self.websocket_mock)

        expected_response = Protocol.create_response(
            "CREATE_FILE", {"status": "success"}
        )

        self.websocket_mock.send.assert_called_once_with(
            json.dumps(expected_response))

    @pytest.mark.asyncio
    async def test_create_file_error(self, setup):
        self.server.file_manager = MagicMock()
        self.server.file_manager.create_file.return_value = (False, "File already exists")

        request = Protocol.create_message(
            "CREATE_FILE", {"filename": "newfile.txt"}
        )

        await self.server.handle_request(Protocol.parse_request(request), self.websocket_mock)

        expected_response = Protocol.create_message(
            "CREATE_FILE", {"status": "error", "error": "File already exists"}
        )

        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_delete_file_success(self, setup):
        self.server.file_manager.delete_file = MagicMock(
            return_value=(True, None)
        )

        request = Protocol.create_message(
            "DELETE_FILE", {"filename": "testfile.txt"}
        )

        await self.server.handle_request(Protocol.parse_request(request), self.websocket_mock)

        expected_response = Protocol.create_message(
            "DELETE_FILE", {"status": "success"}
        )

        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_delete_file_error(self, setup):
        self.server.file_manager.delete_file = MagicMock(
            return_value=(False, "File not found")
        )

        request = Protocol.create_message(
            "DELETE_FILE", {"filename": "testfile.txt"}
        )

        await self.server.handle_request(Protocol.parse_request(request), self.websocket_mock)

        expected_response = Protocol.create_message(
            "DELETE_FILE", {"status": "error", "error": "File not found"}
        )

        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_close_file(self, setup):
        self.server.session_manager.stop_session = AsyncMock()

        request = Protocol.create_message(
            "CLOSE_FILE", {"filename": "testfile.txt"}
        )

        await self.server.handle_request(Protocol.parse_request(request), self.websocket_mock)

        self.server.session_manager.stop_session.assert_called_once_with(
            "testfile.txt", self.websocket_mock
        )

    @pytest.mark.asyncio
    async def test_echo_client_connect_and_disconnect(self, setup):
        self.server.handle_request = AsyncMock()

        self.websocket_mock.__aiter__.return_value = iter([Protocol.create_message("test message")])
        await self.server.echo(self.websocket_mock, "test_path")

        self.server.handle_request.assert_called_once_with(
            Protocol.create_response("test message", {}), self.websocket_mock
        )

        assert self.websocket_mock not in self.server.clients
