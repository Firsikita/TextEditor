import asyncio

from Shared.protocol import Protocol

class SendMessage:
    def send_edit_message(self, websocket, filename, inserted_text, start_y, start_x, event_loop):
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
                    },
                },
            )
            asyncio.run_coroutine_threadsafe(
                websocket.send(message), event_loop
            )

    def send_delete_message(self, websocket, filename, start_y, start_x, end_y, end_x, count, event_loop):
        if count > 0:
            message = Protocol.create_message(
                "EDIT_FILE",
                {
                    "filename": filename,
                    "operation": {
                        "op_type": "delete",
                        "start_pos": {"y": start_y, "x": start_x},
                        "end_pos": {"y": end_y, "x": end_x}
                    },
                },
            )
            asyncio.run_coroutine_threadsafe(
                websocket.send(message), event_loop
            )

    def send_new_line(self, websocket, filename, start_y, start_x, event_loop):
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

    def send_insert_text(self, websocket, filename, start_y, start_x, insert_text, event_loop):
        message = Protocol.create_message(
            "EDIT_FILE",
            {
                "filename": filename,
                "operation": {
                    "op_type": "insert_text",
                    "start_pos": {"y": start_y, "x": start_x},
                    "insert_text": insert_text,
                },
            },
        )
        asyncio.run_coroutine_threadsafe(
            websocket.send(message), event_loop
        )