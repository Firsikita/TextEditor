import unittest
from unittest.mock import AsyncMock, Mock, MagicMock
import pytest
from Server.session_manager import SessionManager, safe_list_get

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.session_manager = SessionManager()
        self.mock_websocket = Mock()
        self.history = {}

        self.user1_ws = MagicMock()
        self.user2_ws = MagicMock()

        self.user1_id = 'user1'
        self.user2_id = 'user2'

        self.filename = "test_file.txt"
        self.operation = {
            'op_type': 'insert',
            'start_pos': {'y': 0, 'x': 0},
            "end_pos": {"y": 0, "x": 5},
            'text': ['Hello'],
            'user_id': self.user1_id,
        }

    def test_start_session(self):
        filename = "test_file.txt"
        self.session_manager.start_session(filename, self.mock_websocket)
        self.assertIn(filename, self.session_manager.sessions)
        self.assertIn(self.mock_websocket, self.session_manager.sessions[filename])
        self.assertIn(filename, self.session_manager.open_files)
        self.assertEqual(self.session_manager.open_files[filename], [""])

    async def test_sessions_and_update_sharing(self):
        self.session_manager.start_session(self.filename, self.user1_ws)
        self.session_manager.start_session(self.filename, self.user2_ws)

        self.assertIn(self.user1_ws,
                      self.session_manager.sessions[self.filename])
        self.assertIn(self.user2_ws,
                      self.session_manager.sessions[self.filename])

        self.session_manager.apply_operation(self.filename, self.user2_id,
                                             self.operation, history={})

        await self.session_manager.share_update(self.filename, self.operation,
                                                self.user2_ws, self.user1_id)

        self.user1_ws.send.assert_called_with(
            AsyncMock())
        self.user2_ws.send.assert_not_called()

    def test_stop_session(self):
        filename = "test_file.txt"
        self.session_manager.start_session(filename, self.mock_websocket)
        self.session_manager.stop_session(filename, self.mock_websocket)
        self.assertNotIn(filename, self.session_manager.sessions)
        self.assertNotIn(filename, self.session_manager.open_files)

    def test_session_removal(self):
        self.session_manager.start_session(self.filename, self.user1_ws)
        self.session_manager.start_session(self.filename, self.user2_ws)
        self.assertIn(self.user1_ws, self.session_manager.sessions[self.filename])

        self.session_manager.stop_session(self.filename, self.user1_ws)

        self.assertNotIn(self.user1_ws, self.session_manager.sessions[self.filename])
        self.assertIn(self.user2_ws, self.session_manager.sessions[self.filename])

    def test_update_content(self):
        filename = "test_file.txt"
        content = ["Line 1", "Line 2"]
        self.session_manager.start_session(filename, self.mock_websocket)
        self.session_manager.update_content(filename, content)
        self.assertEqual(self.session_manager.open_files[filename], content)

    def test_apply_insert_operation(self):
        filename = "test_file.txt"
        user_id = 1
        operation = {
            "op_type": "insert",
            "start_pos": {"y": 0, "x": 0},
            "text": ["Hello"],
            "end_pos": {"y": 0, "x": 5},
        }
        self.session_manager.start_session(filename, self.mock_websocket)
        self.session_manager.apply_operation(filename, user_id, operation,
                                     self.history)
        self.assertEqual(self.session_manager.open_files[filename], ["Hello"])
        self.assertEqual(self.history[filename][0]["operation"], operation)

    def test_apply_delete_operation(self):
        filename = "test_file.txt"
        user_id = 1
        self.session_manager.start_session(filename, self.mock_websocket)
        self.session_manager.update_content(filename, ["Hello, World!"])
        operation = {
            "op_type": "delete",
            "start_pos": {"y": 0, "x": 6},
            "end_pos": {"y": 0, "x": 12},
            "text": [],
        }
        self.session_manager.apply_operation(filename, user_id, operation,
                                     self.history)
        self.assertEqual(self.session_manager.open_files[filename], ["Hello,!"])
        self.assertEqual(self.history[filename][0]["operation"], operation)

    def test_apply_new_line_operation(self):
        filename = "test_file.txt"
        user_id = 1
        self.session_manager.start_session(filename, self.mock_websocket)
        self.session_manager.update_content(filename, ["Hello, World!"])
        operation = {
            "op_type": "new line",
            "start_pos": {"y": 0, "x": 7},
        }
        self.session_manager.apply_operation(filename, user_id, operation,
                                     self.history)
        self.assertEqual(self.session_manager.open_files[filename],
                         ["Hello, ", "World!"])

    def test_cancel_change(self):
        filename = "test_file.txt"
        self.session_manager.start_session(filename, self.mock_websocket)
        operation = {
            "op_type": "insert",
            "start_pos": {"y": 0, "x": 0},
            "end_pos": {"y": 0, "x": 5},
            "text": ["Hello"],
        }
        self.history[filename] = [
            {"user_id": 1, "time": "now", "operation": operation}]
        self.session_manager.update_content(filename, ["Hello"])
        self.session_manager.cancel_change(self.history[filename].pop(), filename)
        self.assertEqual(self.session_manager.open_files[filename], [""])

    def test_share_update(self):
        filename = "test_file.txt"
        operation = {
            "op_type": "insert",
            "start_pos": {"y": 0, "x": 0},
            "text": ["Test"],
        }
        self.session_manager.start_session(filename, self.mock_websocket)
        self.mock_websocket.send = AsyncMock()
        websocket2 = Mock()
        self.session_manager.sessions[filename].add(websocket2)

        self.session_manager.share_update(filename, operation, self.mock_websocket, 1)
        self.mock_websocket.send.assert_not_called()

    def test_get_clients(self):
        self.session_manager.start_session("file1.txt", self.mock_websocket)
        clients = list(self.session_manager.get_clients())
        self.assertEqual(clients, ["file1.txt"])

    def test_get_content(self):
        filename = "test_file.txt"
        self.session_manager.start_session(filename, self.mock_websocket)
        self.session_manager.update_content(filename, ["Hello"])
        self.assertEqual(self.session_manager.get_content(filename), ["Hello"])
        self.assertIsNone(self.session_manager.get_content("non_existent.txt"))

    async def test_multiple_operations(self):
        self.session_manager.start_session(self.filename, self.user1_ws)
        self.session_manager.start_session(self.filename, self.user2_ws)

        operations_user1 = [
            {'op_type': 'insert', 'start_pos': {'y': 0, 'x': 0},
             'text': ['First']},
            {'op_type': 'insert', 'start_pos': {'y': 1, 'x': 0},
             'text': ['Line']}
        ]
        operations_user2 = [
            {'op_type': 'insert', 'start_pos': {'y': 0, 'x': 5},
             'text': ['Hello']},
            {'op_type': 'insert', 'start_pos': {'y': 1, 'x': 4},
             'text': ['World']}
        ]

        for op in operations_user1:
            self.session_manager.apply_operation(self.filename, self.user1_id,
                                                 op, history={})
        for op in operations_user2:
            self.session_manager.apply_operation(self.filename, self.user2_id,
                                                 op, history={})

        await self.session_manager.share_update(self.filename,
                                                operations_user1[0],
                                                self.user1_ws, self.user1_id)
        await self.session_manager.share_update(self.filename,
                                                operations_user2[0],
                                                self.user2_ws, self.user2_id)

        self.user1_ws.send.assert_called_with(AsyncMock())
        self.user2_ws.send.assert_called_with(AsyncMock())

    def test_cancel_change_delete_operation(self):
        filename = "test_file.txt"
        self.session_manager.open_files[filename] = ["Hello, world!", "Another line"]

        last_change = {
            "operation": {
                "op_type": "delete",
                "start_pos": {"y": 0, "x": 7},
                "end_pos": {"y": 0, "x": 12},
                "text": ["world!"]
            }
        }

        result = self.session_manager.cancel_change(last_change, filename)

        assert self.session_manager.open_files[filename] == ["Hello, world!",
                                                "Another line"]
        assert result == {
            "op_type": "insert",
            "start_pos": {"y": 0, "x": 7},
            "text": ["world!"]
        }

    @pytest.mark.asyncio
    async def test_share_update_delete_operation(self):
        filename = "test_file.txt"
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()
        user_id = "user1"

        self.session_manager.sessions[filename] = {websocket1, websocket2}

        operation = {
            "op_type": "delete",
            "start_pos": {"y": 0, "x": 0},
            "end_pos": {"y": 0, "x": 5},
        }

        await self.session_manager.share_update(filename, operation, websocket1, user_id)

        websocket2.send.assert_called_once()
        assert "EDIT_FILE" in websocket2.send.call_args[0][0]

    async def test_update_on_new_user(self):
        self.session_manager.start_session(self.filename, self.user1_ws)
        self.session_manager.start_session(self.filename, self.user2_ws)

        operation = {
            'op_type': 'insert',
            'start_pos': {'y': 0, 'x': 0},
            'text': ['World'],
            'end_pos': {'y': 0, 'x': 5},
        }
        self.session_manager.apply_operation(self.filename, self.user1_id,
                                             operation, history={})

        await self.session_manager.share_update(self.filename, operation,
                                                self.user1_ws, self.user1_id)

        self.user1_ws.send.assert_called_with(AsyncMock())
        self.user2_ws.send.assert_not_called()

class TestSafeListGet(unittest.TestCase):
    def test_safe_list_get_with_valid_index(self):
        lst = [1, 2, 3]
        result = safe_list_get(lst, 1, "default")
        assert result == 2, "Should return the value at the specified index"

    def test_safe_list_get_with_invalid_index(self):
        lst = [1, 2, 3]
        result = safe_list_get(lst, 5, "default")
        assert result == "default", "Should return the default value when index is out of range"

if __name__ == "__main__":
    unittest.main()