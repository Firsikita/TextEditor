import json
import websockets
import asyncio
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

    async def echo(self, websocket):
        self.clients.add(websocket)
        print(
            f"New client connected: {websocket}. Total users: {len(self.clients)}"
        )
        try:
            async for message in websocket:
                request = Protocol.parse_request(message)
                await self.handle_request(request, websocket)
        except (
            websockets.ConnectionClosedOK,
            websockets.ConnectionClosedError,
        ) as e:
            print(f"Connection closed: {e}")
        finally:
            self.clients.remove(websocket)
            print(
                f"Client disconnected: {websocket}. Total users: {len(self.clients)}"
            )

    async def handle_request(self, request, websocket):
        user_id = self.user_sessions[websocket] if websocket in self.user_sessions else None
        command = request["command"]
        response = None

        if command == "PING":
            return

        elif command == "LOGIN":
            username = request["data"]["username"]
            user_id = username
            self.user_sessions[websocket] = user_id
            self.file_manager.append_user(user_id)
            print(f"Client {username} logged in with user_id: {user_id}")

            response = Protocol.create_response(
                "LOGIN", {"status": "success", "user_id": user_id}
            )

        elif command == "GET_FILES":
            files = self.file_manager.get_files(user_id)
            if not files:
                files = ["No files to show."]
            response = Protocol.create_response("GET_FILES", {"files": files})

        elif command == "GRANT_ACCESS":
            host_id = request["data"]["user"]
            filename = request["data"]["filename"]
            answer = self.file_manager.grant_access(host_id, user_id, filename)
            response = Protocol.create_response("GRANT_ACCESS", {"answer": answer})

        elif command == "REMOVE_ACCESS":
            host_id = request["data"]["user"]
            filename = request["data"]["filename"]
            answer = self.file_manager.remove_access(host_id, user_id, filename)
            response = Protocol.create_response("REMOVE_ACCESS", {"answer": answer})

        elif command == "OPEN_FILE":
            filename = request["data"]["filename"]
            user_id = request["data"]["user_id"]
            host_id = request["data"]["host_id"]
            print(f"opening file for user {user_id} and host {host_id}")

            if user_id != host_id:
                success, host_path, error = self.file_manager.validate_access(user_id, host_id, filename)
                print(f"validation for {user_id} and host {host_id}: status - {success}, error - {error}")
                if not success:
                    return await websocket.send(json.dumps(Protocol.create_response("ERROR", {"error": error})))

            if filename not in self.session_manager.open_files:
                success, content = self.file_manager.open_file(host_id, filename)
                self.history_changes[filename] = self.file_manager.load_history(filename)

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
                self.session_manager.start_session(filename, websocket)
                self.session_manager.update_content(filename, content)
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
            success, error = self.file_manager.create_file(user_id, filename)
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
            self.session_manager.stop_session(
                request["data"]["filename"], websocket
            )
            success, error = self.file_manager.delete_file(user_id, filename)
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
            content = self.session_manager.get_content(filename)

            self.file_manager.save_file(
                user_id, filename, content
            )

            if new_operation is None:
                await self.session_manager.share_update(
                    filename, operation, websocket, user_id
                )
            else:
                await self.session_manager.share_update(
                    filename, new_operation, websocket=None, user_id=user_id
                )

        elif command == "SAVE_CONTENT":
            filename = request["data"]["filename"]
            content = self.session_manager.get_content(filename)

            self.file_manager.save_file(user_id, filename, content)

        elif command == "GET_HISTORY":
            filename = request["data"]["filename"]
            try:
                history = self.file_manager.load_history(filename)
                response = Protocol.create_response(
                    "GET_HISTORY", {"status": "success", "history": history}
                )
            except Exception as e:
                response = Protocol.create_response(
                    "GET_HISTORY", {"status": "error", "error": str(e)}
                )

        elif command == "DELETE_HISTORY":
            filename = request["data"]["filename"]
            self.file_manager.delete_history(filename)

        elif command == "GET_REGISTERED_USERS":
            try:
                users = self.file_manager.get_all_registered_users()
                response = Protocol.create_response("GET_REGISTERED_USERS", {"status": "success", "users": users})
            except Exception as e:
                response = Protocol.create_response("GET_REGISTERED_USERS", {"status": "error", "error": str(e)})

        else:
            response = Protocol.create_response(
                "ERROR", {"error": "Unknown command"}
            )

        if response:
            await websocket.send(json.dumps(response))


if __name__ == "__main__":
    server = Server()
    asyncio.run(server.start())
