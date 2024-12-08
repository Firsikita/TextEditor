import pytest
import pytest_asyncio
import asyncio
import json
from unittest.mock import AsyncMock, patch
from Client.client import Client
from Shared.protocol import Protocol


@pytest.mark.asyncio
class TestClient:
    @pytest_asyncio.fixture
    async def setup_client(self):
        client = Client("ws://localhost:8765")
        client.console.print = AsyncMock()
        client.editor = AsyncMock()
        return client

    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_connect_and_login_success(self, mock_connect, setup_client):
        client = setup_client
        websocket_mock = AsyncMock()
        mock_connect.return_value = websocket_mock

        websocket_mock.recv.return_value = json.dumps(
            Protocol.create_response("LOGIN", {"status": "success",
                                               "user_id": "fake_id"})
        )

        with patch("aioconsole.ainput", new_callable=AsyncMock) as mock_ainput:
            mock_ainput.return_value = "test_user"
            await client.login(websocket_mock)

            assert client.user_id == "fake_id"
            client.console.print.assert_any_call(
                "test_user logged in successfully", style="#00A6A6")
            websocket_mock.send.assert_any_call(
                json.dumps(Protocol.create_response("LOGIN",
                                                   {"username": "test_user"}))
            )

    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_login_timeout(self, mock_connect, setup_client):
        client = setup_client
        websocket_mock = AsyncMock()
        mock_connect.return_value = websocket_mock

        websocket_mock.recv.side_effect = asyncio.TimeoutError

        with patch("aioconsole.ainput", new_callable=AsyncMock) as mock_ainput:
            mock_ainput.return_value = "test_user"
            await client.login(websocket_mock)

            client.console.print.assert_any_call(
                "Login timed out. Please try again.", style="#F08700"
            )

    @patch("InquirerPy.inquirer.select", new_callable=AsyncMock)
    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_get_files(self, mock_connect, mock_select, setup_client):
        client = setup_client
        websocket_mock = AsyncMock()
        mock_connect.return_value = websocket_mock

        websocket_mock.recv.return_value = json.dumps(
            Protocol.create_response("GET_FILES",
                                     {"files": ["file1.txt", "file2.txt"]})
        )

        await client.get_files(websocket_mock)

        client.console.print.assert_any_call("\nFiles in folder:",
                                             style="#61afef")
        client.console.print.assert_any_call(" 1) file1.txt")
        client.console.print.assert_any_call(" 2) file2.txt")
        websocket_mock.send.assert_any_call(
            Protocol.create_message("GET_FILES"))

    @patch("websockets.connect", new_callable=AsyncMock)
    @patch("InquirerPy.inquirer.select")
    async def test_handle_message_exit(self, mock_select, mock_connect, setup_client):
        client = setup_client
        websocket_mock = AsyncMock()
        mock_connect.return_value = websocket_mock

        mock_select.return_value.execute_async = AsyncMock(return_value="7")

        await client.handle_message(websocket_mock)
        client.console.print.assert_any_call("Exiting...", style="#61afef")

    @patch("aioconsole.ainput", new_callable=AsyncMock)
    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_create_file_success(self, mock_connect, mock_ainput,
                                       setup_client):
        client = setup_client
        websocket_mock = AsyncMock()
        mock_connect.return_value = websocket_mock

        mock_ainput.return_value = "new_file.txt"

        websocket_mock.recv.return_value = json.dumps(
            Protocol.create_response("CREATE_FILE", {"status": "success"})
        )

        await client.create_file(websocket_mock)

        expected_message = Protocol.create_response("CREATE_FILE", {
            "filename": "new_file.txt"})
        websocket_mock.send.assert_any_call(json.dumps(expected_message))
        client.console.print.assert_any_call(
            "File 'new_file.txt' created successfully.", style="#00A6A6")