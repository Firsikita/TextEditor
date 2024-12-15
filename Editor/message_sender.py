import asyncio
from Shared.protocol import Protocol


class MessageSender:
    @staticmethod
    def send_edit_message(
        websocket,
        filename: str,
        inserted_text: list[str],
        start_y: int,
        start_x: int,
        event_loop,
        user_id: str,
    ):
        if inserted_text:
            message = Protocol.create_message(
                "EDIT_FILE",
                {
                    "filename": filename,
                    "operation": {
                        "op_type": "insert",
                        "start_pos": {"y": start_y, "x": start_x},
                        "length": len(inserted_text),
                        "text": inserted_text,
                        "end_pos": {"y": None, "x": None},
                        "user_id": user_id,
                    },
                    "user_id": user_id,
                },
            )
            asyncio.run_coroutine_threadsafe(websocket.send(message), event_loop)

    @staticmethod
    def send_delete_message(
        websocket,
        filename: str,
        start_y: int,
        start_x: int,
        end_y: int,
        end_x: int,
        count: int,
        event_loop,
        user_id: str,
    ):
        if count > 0:
            message = Protocol.create_message(
                "EDIT_FILE",
                {
                    "filename": filename,
                    "operation": {
                        "op_type": "delete",
                        "start_pos": {"y": start_y, "x": start_x},
                        "end_pos": {"y": end_y, "x": end_x},
                        "text": None,
                    },
                    "user_id": user_id,
                },
            )
            asyncio.run_coroutine_threadsafe(websocket.send(message), event_loop)

    @staticmethod
    def send_new_line(
        websocket,
        filename: str,
        start_y: int,
        start_x: int,
        event_loop,
        user_id: str,
    ):
        message = Protocol.create_message(
            "EDIT_FILE",
            {
                "filename": filename,
                "operation": {
                    "op_type": "new line",
                    "start_pos": {"y": start_y, "x": start_x},
                },
                "user_id": user_id,
            },
        )
        asyncio.run_coroutine_threadsafe(websocket.send(message), event_loop)

    @staticmethod
    def cancel_changes(websocket, filename: str, event_loop, user_id: str):
        message = Protocol.create_message(
            "EDIT_FILE",
            {
                "filename": filename,
                "operation": {
                    "op_type": "cancel_changes",
                    "start_pos": {"y": 0, "x": 0},
                },
                "user_id": user_id,
            },
        )
        asyncio.run_coroutine_threadsafe(websocket.send(message), event_loop)
