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
        self.server.client_readiness = {}
        self.server.file_manager = MagicMock()
        self.server.session_manager = MagicMock()

    @staticmethod
    async def ready(websocket):
        await websocket.send(Protocol.create_message("ACK", None))

    async def send_and_ack(self, message):
        self.websocket_mock.reset_mock()
        self.server.client_readiness[self.websocket_mock] = True
        await self.server.handle_request(
            Protocol.parse_request(message), self.websocket_mock
        )
        self.websocket_mock.recv.return_value = json.dumps(
            Protocol.create_message("ACK")
        )
        self.websocket_mock.send.assert_any_call(
            Protocol.create_message("ACK", None))

    @pytest.mark.asyncio
    async def test_login_success(self, setup):
        with patch(
                "Shared.protocol.Protocol.create_response") as mock_response:
            mock_response.return_value = {"command": "LOGIN",
                                          "data": {"status": "success",
                                                   "user_id": "test_user"}}

            request = {"command": "LOGIN", "data": {"username": "test_user"}}
            await self.server.handle_request(request, self.websocket_mock)

            self.websocket_mock.send.assert_called_once_with(
                json.dumps(mock_response.return_value))


    @pytest.mark.asyncio
    async def test_get_files(self, setup):
        self.server.file_manager = MagicMock()
        self.server.file_manager.get_files.return_value = ["file1.txt", "file2.txt"]

        request = Protocol.create_message("GET_FILES")

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )
        expected_response = Protocol.create_response(
            "GET_FILES", {"files": ["file1.txt", "file2.txt"]}
        )
        self.websocket_mock.send.assert_called_once_with(json.dumps(expected_response))
        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_open_file_success(self, setup):
        self.server.file_manager.open_file = MagicMock(return_value=(True, "A"))
        request = Protocol.create_message("OPEN_FILE", {"filename": "testfile.txt"})
        await self.server.handle_request(json.loads(request), self.websocket_mock)

        expected_response = Protocol.create_message(
            "OPEN_FILE", {"status": "success", "content": "A"}
        )
        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_open_file_error(self, setup):
        self.server.file_manager.open_file = MagicMock(return_value=(False, None))
        request = Protocol.create_message("OPEN_FILE", {"filename": "testfile.txt"})
        await self.server.handle_request(json.loads(request), self.websocket_mock)
        expected_response = Protocol.create_message(
            "ERROR", {"error": "File not found"}
        )
        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_edit_file(self, setup):
        self.server.session_manager = MagicMock()
        self.server.session_manager.get_content = MagicMock(return_value="content")
        self.server.session_manager.share_update = AsyncMock()
        self.server.file_manager.save_file = MagicMock()

        request = Protocol.create_message(
            "EDIT_FILE",
            {
                "filename": "testfile.txt",
                "operation": {"op_type": "insert", "pos": 0, "char": "A"},
            },
        )

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )

        self.server.session_manager.apply_operation.assert_called_once_with(
            "testfile.txt", {"op_type": "insert", "pos": 0, "char": "A"}
        )
        self.server.file_manager.save_file.assert_called_once_with(
            "testfile.txt", "content"
        )

        self.server.session_manager.share_update.assert_called_once_with(
            "testfile.txt",
            {"op_type": "insert", "pos": 0, "char": "A"},
            self.websocket_mock,
        )

    @pytest.mark.asyncio
    async def test_create_file_success(self, setup):
        self.server.file_manager = MagicMock()
        self.server.file_manager.create_file.return_value = (True, None)

        request = Protocol.create_message("CREATE_FILE", {"filename": "newfile.txt"})

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )

        expected_response = Protocol.create_response(
            "CREATE_FILE", {"status": "success"}
        )

        self.websocket_mock.send.assert_called_once_with(json.dumps(expected_response))

    @pytest.mark.asyncio
    async def test_create_file_error(self, setup):
        self.server.file_manager = MagicMock()
        self.server.file_manager.create_file.return_value = (
            False,
            "File already exists",
        )

        request = Protocol.create_message("CREATE_FILE", {"filename": "newfile.txt"})

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )

        expected_response = Protocol.create_message(
            "CREATE_FILE", {"status": "error", "error": "File already exists"}
        )

        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_delete_file_success(self, setup):
        self.server.file_manager.delete_file = MagicMock(return_value=(True, None))

        request = Protocol.create_message("DELETE_FILE", {"filename": "testfile.txt"})

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )

        expected_response = Protocol.create_message(
            "DELETE_FILE", {"status": "success"}
        )

        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_delete_file_error(self, setup):
        self.server.file_manager.delete_file = MagicMock(
            return_value=(False, "File not found")
        )

        request = Protocol.create_message("DELETE_FILE", {"filename": "testfile.txt"})

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )

        expected_response = Protocol.create_message(
            "DELETE_FILE", {"status": "error", "error": "File not found"}
        )

        self.websocket_mock.send.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_close_file(self, setup):
        self.server.session_manager.stop_session = AsyncMock()

        request = Protocol.create_message("CLOSE_FILE", {"filename": "testfile.txt"})

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )

        self.server.session_manager.stop_session.assert_called_once_with(
            "testfile.txt", self.websocket_mock
        )

    @pytest.mark.asyncio
    async def test_echo_client_connect_and_disconnect(self, setup):
        self.server.handle_request = AsyncMock()

        self.websocket_mock.__aiter__.return_value = iter(
            [Protocol.create_message("test message")]
        )
        await self.server.echo(self.websocket_mock, "test_path")

        self.server.handle_request.assert_called_once_with(
            Protocol.create_response("test message", {}), self.websocket_mock
        )

        assert self.websocket_mock not in self.server.clients
