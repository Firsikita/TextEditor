import asyncio
import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from Server.server import Server
from Shared.protocol import Protocol


class TestServer:
    @pytest.fixture
    def setup(self):
        self.server = Server()
        self.websocket_mock = AsyncMock()
        self.user_sessions = {}

    @pytest.fixture
    def event_loop(self):
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()

    @pytest.fixture
    def server(self):
        server = Server()
        server.file_manager = Mock()
        server.session_manager = Mock()
        server.user_sessions = {}
        server.clients = set()
        return server

    @pytest.mark.asyncio
    @patch("Server.server.Protocol")
    @patch("Server.server.websockets")
    async def test_login_command(self, mock_websockets, mock_protocol, server):
        websocket_mock = AsyncMock()

        mock_protocol.parse_request.return_value = {
            "command": "LOGIN",
            "data": {"username": "test_user"},
        }
        mock_protocol.create_response.return_value = {
            "type": "LOGIN",
            "data": {"status": "success", "user_id": "test_user"},
        }

        server.file_manager.append_user = Mock()
        await server.handle_request(
            {"command": "LOGIN", "data": {"username": "test_user"}},
            websocket_mock
        )

        assert websocket_mock in server.user_sessions
        assert server.user_sessions[websocket_mock] == "test_user"
        server.file_manager.append_user.assert_called_with("test_user")
        websocket_mock.send.assert_called_with(
            '{"type": "LOGIN", "data": {"status": "success", "user_id": "test_user"}}'
        )

    @pytest.mark.asyncio
    @patch("Server.server.Protocol")
    @patch("Server.server.websockets")
    async def test_get_files_command(self, mock_websockets, mock_protocol, server):
        websocket_mock = AsyncMock()

        mock_protocol.parse_request.return_value = {
            "command": "GET_FILES",
            "data": {},
        }
        mock_protocol.create_response.return_value = {
            "type": "GET_FILES",
            "data": {"files": ["file1.txt", "file2.txt"]},
        }

        server.file_manager.get_files.return_value = ["file1.txt", "file2.txt"]
        server.user_sessions[websocket_mock] = "test_user"
        await server.handle_request({"command": "GET_FILES", "data": {}},
                                    websocket_mock)

        server.file_manager.get_files.assert_called_with("test_user")
        websocket_mock.send.assert_called_with(
            '{"type": "GET_FILES", "data": {"files": ["file1.txt", "file2.txt"]}}'
        )

    @pytest.mark.asyncio
    async def test_get_files(self, setup):
        self.server.file_manager = MagicMock()
        self.server.file_manager.get_files.return_value = [
            "file1.txt",
            "file2.txt",
        ]

        request = Protocol.create_message("GET_FILES")

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )
        expected_response = Protocol.create_response(
            "GET_FILES", {"files": ["file1.txt", "file2.txt"]}
        )
        self.websocket_mock.send.assert_called_once_with(
            json.dumps(expected_response)
        )


    @pytest.mark.asyncio
    @patch("Server.server.Protocol")
    @patch("Server.server.websockets")
    async def test_invalid_command(self, mock_websockets, mock_protocol, server):
        websocket_mock = AsyncMock()

        # Mock request parsing and error response creation
        mock_protocol.parse_request.return_value = {"command": "INVALID"}
        mock_protocol.create_response.return_value = {
            "type": "ERROR",
            "data": {"error": "Unknown command"},
        }

        await server.handle_request({"command": "INVALID"}, websocket_mock)

        websocket_mock.send.assert_called_with(
            '{"type": "ERROR", "data": {"error": "Unknown command"}}'
        )


    @pytest.mark.asyncio
    async def test_client_connection_and_disconnection(self, server):
        websocket_mock = AsyncMock()

        await server.echo(websocket_mock)
        assert websocket_mock in server.clients

        await websocket_mock.close()
        assert websocket_mock not in server.clients


    @pytest.mark.asyncio
    async def test_open_file_success(self, setup):
        self.server.file_manager.open_file = MagicMock(
            return_value=(True, "A")
        )
        request = Protocol.create_message(
            "OPEN_FILE", {"filename": "testfile.txt", "user_id": "user1", "host_id": "user2"}
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
        self.server.user_sessions[self.websocket_mock] = "fake_id"
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

        request = Protocol.create_message(
            "CREATE_FILE", {"filename": "newfile.txt"}
        )

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )

        expected_response = Protocol.create_response(
            "CREATE_FILE", {"status": "success"}
        )

        self.websocket_mock.send.assert_called_once_with(
            json.dumps(expected_response)
        )

    @pytest.mark.asyncio
    async def test_create_file_error(self, setup):
        self.server.file_manager = MagicMock()
        self.server.file_manager.create_file.return_value = (
            False,
            "File already exists",
        )

        request = Protocol.create_message(
            "CREATE_FILE", {"filename": "newfile.txt"}
        )

        await self.server.handle_request(
            Protocol.parse_request(request), self.websocket_mock
        )

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

        request = Protocol.create_message(
            "DELETE_FILE", {"filename": "testfile.txt"}
        )

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

        request = Protocol.create_message(
            "CLOSE_FILE", {"filename": "testfile.txt"}
        )

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
        await self.server.echo(self.websocket_mock)

        self.server.handle_request.assert_called_once_with(
            Protocol.create_response("test message", {}), self.websocket_mock
        )

        assert self.websocket_mock not in self.server.clients

    @pytest.mark.asyncio
    @patch("Server.server.Protocol")
    async def test_grant_access_command(self, mock_protocol, server):
        websocket_mock = AsyncMock()

        mock_protocol.parse_request.return_value = {
            "command": "GRANT_ACCESS",
            "data": {"user": "host_user", "filename": "file1.txt"},
        }
        mock_protocol.create_response.return_value = {
            "type": "GRANT_ACCESS",
            "data": {"answer": "Access granted"},
        }

        server.file_manager.grant_access.return_value = "Access granted"

        server.user_sessions[websocket_mock] = "test_user"
        await server.handle_request(
            {"command": "GRANT_ACCESS",
             "data": {"user": "host_user", "filename": "file1.txt"}},
            websocket_mock,
        )

        server.file_manager.grant_access.assert_called_with("host_user",
                                                            "test_user",
                                                            "file1.txt")
        websocket_mock.send.assert_called_with(
            '{"type": "GRANT_ACCESS", "data": {"answer": "Access granted"}}'
        )

    @pytest.mark.asyncio
    @patch("Server.server.Protocol")
    async def test_remove_access_command(self, mock_protocol, server):
        websocket_mock = AsyncMock()

        mock_protocol.parse_request.return_value = {
            "command": "REMOVE_ACCESS",
            "data": {"user": "host_user", "filename": "file1.txt"},
        }
        mock_protocol.create_response.return_value = {
            "type": "REMOVE_ACCESS",
            "data": {"answer": "Access removed"},
        }

        server.file_manager.remove_access.return_value = "Access removed"

        server.user_sessions[websocket_mock] = "test_user"
        await server.handle_request(
            {"command": "REMOVE_ACCESS",
             "data": {"user": "host_user", "filename": "file1.txt"}},
            websocket_mock,
        )

        server.file_manager.remove_access.assert_called_with("host_user",
                                                             "test_user",
                                                             "file1.txt")
        websocket_mock.send.assert_called_with(
            '{"type": "REMOVE_ACCESS", "data": {"answer": "Access removed"}}'
        )


    @pytest.mark.asyncio
    @patch("Server.server.Protocol")
    async def test_create_file_command(self, mock_protocol, server):
        websocket_mock = AsyncMock()

        mock_protocol.parse_request.return_value = {
            "command": "CREATE_FILE",
            "data": {"filename": "new_file.txt"},
        }
        mock_protocol.create_response.return_value = {
            "type": "CREATE_FILE",
            "data": {"status": "success"},
        }

        server.file_manager.create_file.return_value = (True, None)

        server.user_sessions[websocket_mock] = "test_user"
        await server.handle_request(
            {"command": "CREATE_FILE", "data": {"filename": "new_file.txt"}},
            websocket_mock
        )

        server.file_manager.create_file.assert_called_with("test_user",
                                                           "new_file.txt")
        websocket_mock.send.assert_called_with(
            '{"type": "CREATE_FILE", "data": {"status": "success"}}'
        )

if __name__ == "__main__":
    pytest.main()