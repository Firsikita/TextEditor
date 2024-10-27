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
        self.client_readiness = {}

    async def start(self, host="localhost", port=8765):
        async with websockets.serve(self.echo, host, port):
            print(f"Server started on ws://{host}:{port}")
            await asyncio.Future()

    async def echo(self, websocket, path):
        self.clients.add(websocket)
        self.client_readiness[websocket] = False
        print(f"New client connected: {websocket}. Total users: {len(self.clients)}")
        try:
            async for message in websocket:
                request = Protocol.parse_request(message)
                await self.handle_request(request, websocket)
        except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError) as e:
            print(f"Connection closed: {e}")
        finally:
            self.clients.remove(websocket)
            del self.client_readiness[websocket]
            print(f"Client disconnected: {websocket}. Total users: {len(self.clients)}")

    async def handle_request(self, request, websocket):
        command = request["command"]
        response = None

        if command == "PING":
            return

        elif command == "ACK":
            self.client_readiness[websocket] = True
            print(f"Client {self.user_sessions[websocket] if websocket in self.user_sessions else websocket} is ready.")
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
                if success:
                    self.session_manager.start_session(filename, websocket)
                    self.session_manager.update_content(filename, content)
                    response = Protocol.create_response(
                        "OPEN_FILE", {"status": "success", "content": content}
                    )
                else:
                    response = Protocol.create_response(
                        "ERROR", {"error": content}
                    )
            else:
                content = self.session_manager.open_files[filename]
                response = Protocol.create_response(
                    "OPEN_FILE", {"status": "success", "content": content}
                )

        elif command == "CLOSE_FILE":
            filename = request["data"]["filename"]
            self.session_manager.stop_session(filename, websocket)
            if filename in self.history_changes:
                self.file_manager.save_history(filename, self.history_changes[filename])

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
            current_time = str(datetime.datetime.now())

            self.history_changes[filename] = [user_id, current_time, operation]

            self.session_manager.start_session(filename, websocket)
            self.session_manager.apply_operation(filename, operation)
            content = self.session_manager.get_content(filename)

            self.file_manager.save_file(filename, content)

            await self.session_manager.share_update(filename, operation, websocket)

        elif command == "SAVE_CONTENT":
            filename = request["data"]["filename"]
            content = self.session_manager.get_content(filename)

            success, error = self.file_manager.save_file(filename, content)
            # if success:
            #    response = Protocol.create_response('SAVE_CONTENT',
            #                                        {'status': 'success'})
            # else:
            #    response = Protocol.create_response('SAVE_CONTENT',
            #                                        {'status': 'error',
            #                                         'error': error})

        elif command == "GET_HISTORY":
            filename = request["data"]["filename"]
            try:
                history = self.file_manager.load_history()[filename]
                response = Protocol.create_response(
                    "GET_HISTORY", {"status": "success", "history": history}
                )
            except Exception as e:
                response = Protocol.create_response(
                    "GET_HISTORY", {"status": "error", "error": str(e)}
                )

        else:
            response = Protocol.create_response("ERROR", {"error": "Unknown command"})

        if response:
            if websocket in self.client_readiness and self.client_readiness[websocket]:
                print(f"Ready. Sending response: {response}")
                await websocket.send(json.dumps(response))
                await self.wait_for_ack(websocket)
            else:
                print(f"Client {websocket} is not ready. Message not sent.")

    async def wait_for_ack(self, websocket):
        try:
            ack_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
            ack_request = Protocol.parse_request(ack_msg)
            if ack_request["command"] == "ACK":
                print(f"ACK received from user: {self.user_sessions[websocket]}")
            else:
                print(f"Unexpected message received instead of ACK: {ack_msg}")
        except asyncio.TimeoutError:
            print(
                f"ACK not received from {self.user_sessions[websocket]} within timeout"
            )


if __name__ == "__main__":
    server = Server()
    asyncio.run(server.start())
