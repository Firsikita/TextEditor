import asyncio

from Shared.protocol import Protocol

class SendMessage:
    def send_edit_message(self, websocket, filename: str, inserted_text: list[str], start_y: int, start_x: int, event_loop):
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
                    },
                },
            )
            asyncio.run_coroutine_threadsafe(
                websocket.send(message), event_loop
            )

    def send_delete_message(self, websocket, filename: str, start_y: int, start_x: int, end_y: int, end_x: int,
                            count: int, event_loop):
        if count > 0:
            message = Protocol.create_message(
                "EDIT_FILE",
                {
                    "filename": filename,
                    "operation": {
                        "op_type": "delete",
                        "start_pos": {"y": start_y, "x": start_x},
                        "end_pos": {"y": end_y, "x": end_x},
                        "deleted_text": None
                    },
                },
            )
            asyncio.run_coroutine_threadsafe(
                websocket.send(message), event_loop
            )

    def send_new_line(self, websocket, filename: str, start_y: int, start_x: int, event_loop):
        message = Protocol.create_message(
            "EDIT_FILE",
            {
                "filename": filename,
                "operation": {
                    "op_type": "new line",
                    "start_pos": {"y": start_y, "x": start_x},
                },
            },
        )
        asyncio.run_coroutine_threadsafe(
            websocket.send(message), event_loop
        )

    def cancaling_changes(self, websocket, filename: str, event_loop):
        message = Protocol.create_message(
            "EDIT_FILE",
            {
                "filename": filename,
                "operation": {
                    "op_type": "cancal_changes",
                    "start_pos": {"y": 0, "x": 0},
                }
            }
        )
        asyncio.run_coroutine_threadsafe(
            websocket.send(message), event_loop
        )