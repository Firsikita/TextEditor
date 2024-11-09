import json
import websockets
import asyncio
import datetime

from .file_manager import FileManager
from .session_manager import SessionManager
from Shared.protocol import Protocol


class Server:
    def __init__(self):
        self.file_manager = FileManager()
        self.session_manager = SessionManager()
        self.clients = set()
        self.user_sessions = {}
        self.history_changes = {}

    async def start(self, host="localhost", port=8765):
        async with websockets.serve(self.echo, host, port):
            print(f"Server started on ws://{host}:{port}")
            await asyncio.Future()

    async def echo(self, websocket, path):
        self.clients.add(websocket)
        print(
            f"New client connected: {websocket}. Total users: {len(self.clients)}"
        )
        try:
            async for message in websocket:
                request = Protocol.parse_request(message)
                await self.handle_request(request, websocket)
        except websockets.exceptions.ConnectionClosed:
            print("User disconnected.")
        finally:
            self.clients.remove(websocket)
            print(
                f"Client disconnected: {websocket}. Total users: {len(self.clients)}"
            )

    async def handle_request(self, request, websocket):
        # print(f"Received request: {request}")

        command = request["command"]
        response = None

        if command == "PING":
            return

        elif command == "LOGIN":
            username = request["data"]["username"]
            user_id = username
            self.user_sessions[websocket] = user_id
            print(f"Client {username} logged in with user_id: {user_id}")

            response = Protocol.create_response(
                "LOGIN", {"status": "success", "user_id": user_id}
            )

        elif command == "GET_FILES":
            files = self.file_manager.get_files()
            response = Protocol.create_response("GET_FILES", {"files": files})

        elif command == "OPEN_FILE":
            filename = request["data"]["filename"]
            if filename not in self.session_manager.open_files:
                success, content = self.file_manager.open_file(filename)
                self.history_changes[filename] = self.file_manager.load_history(filename)

                print(f"AAA ---- {content}")
                if success:
                    self.session_manager.start_session(filename, websocket)
                    self.session_manager.update_content(filename, content)
                    response = Protocol.create_response(
                        "OPEN_FILE", {"status": "success", "content": content}
                    )
                else:
                    response = Protocol.create_response(
                        "ERROR", {"error": "File not found"}
                    )
            else:
                content = self.session_manager.open_files[filename]
                print(f"BBB --- {content}")
                response = Protocol.create_response(
                    "OPEN_FILE", {"status": "success", "content": content}
                )

        elif command == "CLOSE_FILE":
            filename = request["data"]["filename"]
            self.session_manager.stop_session(filename, websocket)
            if filename in self.history_changes:
                self.file_manager.save_history(filename, self.history_changes[filename])
                self.history_changes.pop(filename)

        elif command == "CREATE_FILE":
            filename = request["data"]["filename"]
            success, error = self.file_manager.create_file(filename)
            if success:
                response = Protocol.create_response(
                    "CREATE_FILE", {"status": "success"}
                )
            else:
                response = Protocol.create_response(
                    "CREATE_FILE", {"status": "error", "error": error}
                )

        elif command == "DELETE_FILE":
            filename = request["data"]["filename"]
            self.session_manager.stop_session(request["data"]["filename"], websocket)
            success, error = self.file_manager.delete_file(filename)
            if success:
                response = Protocol.create_response(
                    "DELETE_FILE", {"status": "success"}
                )
            else:
                response = Protocol.create_response(
                    "DELETE_FILE", {"status": "error", "error": error}
                )

        elif command == "EDIT_FILE":
            user_id = self.user_sessions[websocket]
            filename = request["data"]["filename"]
            operation = request["data"]["operation"]

            self.session_manager.start_session(filename, websocket)
            new_operation = self.session_manager.apply_operation(filename, user_id, operation, self.history_changes)
            print(f"AAA ---- new operation{new_operation}")
            content = self.session_manager.get_content(filename)

            self.file_manager.save_file(
                filename, content
            )

            if new_operation is None:
                await self.session_manager.share_update(
                    filename, operation, websocket
                )
            else:
                await self.session_manager.share_update(
                    filename, new_operation, websocket=None
                )


        elif command == "SAVE_CONTENT":
            filename = request["data"]["filename"]
            content = self.session_manager.get_content(filename)

            self.file_manager.save_file(filename, content)

        elif command == "update":
            response = Protocol.create_response(
                "update", {"status": "success"}
            )

        else:
            response = Protocol.create_response(
                "ERROR", {"error": "Unknown command"}
            )

        if response:
            await websocket.send(json.dumps(response))


if __name__ == "__main__":
    server = Server()
    asyncio.run(server.start())
