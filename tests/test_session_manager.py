from unittest.mock import AsyncMock, Mock
import pytest
from Server.session_manager import SessionManager, safe_list_get


@pytest.fixture
def session_manager():
    return SessionManager()


@pytest.fixture
def mock_websocket():
    return AsyncMock()


@pytest.mark.asyncio
async def test_sessions_and_update_sharing(session_manager, mock_websocket):
    user1_ws = AsyncMock()
    user2_ws = AsyncMock()
    filename = "test_file.txt"
    user1_id = "user1"
    user2_id = "user2"
    operation = {
        "op_type": "insert",
        "start_pos": {"y": 0, "x": 0},
        "end_pos": {"y": 0, "x": 5},
        "text": ["Hello"],
        "user_id": user1_id,
    }

    session_manager.start_session(filename, user1_ws)
    session_manager.start_session(filename, user2_ws)

    session_manager.apply_operation(filename, user2_id, operation, history={})

    await session_manager.share_update(filename, operation, user2_ws, user1_id)

    user1_ws.send.assert_called_once()
    user2_ws.send.assert_not_called()


def test_start_session(session_manager, mock_websocket):
    filename = "test_file.txt"
    session_manager.start_session(filename, mock_websocket)
    assert filename in session_manager.sessions
    assert mock_websocket in session_manager.sessions[filename]
    assert filename in session_manager.open_files
    assert session_manager.open_files[filename] == [""]


def test_stop_session(session_manager, mock_websocket):
    filename = "test_file.txt"
    session_manager.start_session(filename, mock_websocket)
    session_manager.stop_session(filename, mock_websocket)
    assert filename not in session_manager.sessions
    assert filename not in session_manager.open_files


def test_update_content(session_manager, mock_websocket):
    filename = "test_file.txt"
    content = ["Line 1", "Line 2"]
    session_manager.start_session(filename, mock_websocket)
    session_manager.update_content(filename, content)
    assert session_manager.open_files[filename] == content


def test_apply_insert_operation(session_manager):
    filename = "test_file.txt"
    user_id = 1
    operation = {
        "op_type": "insert",
        "start_pos": {"y": 0, "x": 0},
        "text": ["Hello"],
        "end_pos": {"y": 0, "x": 5},
    }
    history = {}
    session_manager.start_session(filename, Mock())
    session_manager.apply_operation(filename, user_id, operation, history)
    assert session_manager.open_files[filename] == ["Hello"]
    assert history[filename][0]["operation"] == operation


@pytest.mark.asyncio
async def test_share_update(session_manager, mock_websocket):
    filename = "test_file.txt"
    operation = {
        "op_type": "insert",
        "start_pos": {"y": 0, "x": 0},
        "text": ["Test"],
    }
    session_manager.start_session(filename, mock_websocket)
    mock_websocket.send = AsyncMock()
    websocket2 = AsyncMock()
    session_manager.sessions[filename].add(websocket2)

    await session_manager.share_update(filename, operation, mock_websocket, 1)
    mock_websocket.send.assert_not_called()
    websocket2.send.assert_called_once()


def test_safe_list_get_with_valid_index():
    lst = [1, 2, 3]
    result = safe_list_get(lst, 1, "default")
    assert result == 2, "Should return the value at the specified index"


def test_safe_list_get_with_invalid_index():
    lst = [1, 2, 3]
    result = safe_list_get(lst, 5, "default")
    assert (
        result == "default"
    ), "Should return the default value when index is out of range"


def test_apply_delete_operation(session_manager):
    filename = "test_file.txt"
    user_id = 1
    session_manager.start_session(filename, Mock())
    session_manager.update_content(filename, ["Hello, world!", "Another line."])
    operation = {
        "op_type": "delete",
        "start_pos": {"y": 0, "x": 7},
        "end_pos": {"y": 1, "x": 8},
        "text": [],
    }
    history = {}
    session_manager.apply_operation(filename, user_id, operation, history)
    assert session_manager.open_files[filename] == ["Hello, line."]
    assert operation["text"] == ["world!", "Another "]


def test_apply_new_line_operation(session_manager):
    filename = "test_file.txt"
    user_id = 1
    session_manager.start_session(filename, Mock())
    session_manager.update_content(filename, ["Hello, world!"])
    operation = {
        "op_type": "new line",
        "start_pos": {"y": 0, "x": 6},
    }
    history = {}
    session_manager.apply_operation(filename, user_id, operation, history)
    assert session_manager.open_files[filename] == ["Hello,", " world!"]
