import asyncio
import websockets
import json

from .file_manager import FileManager
from .session_manager import SessionManager
from Shared.protocol import Protocol

class Server:
    def __init__(self):
        self.file_manager = FileManager()
        self.session_manager = SessionManager()
        self.clients = set()

    async def start(self, host="localhost", port=8765):
        async with websockets.serve(self.echo, host, port):
            print(f"Server started on ws://{host}:{port}")
            await asyncio.Future()

    async def echo(self, websocket, path):
        self.clients.add(websocket)
        print(f"New client connected: {websocket}. Total users: {len(self.clients)}")
        try:
            async for message in websocket:
                request = Protocol.parse_request(message)
                response = await self.handle_request(request, websocket)
                await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            print("User disconnected.")
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected: {websocket}. Total users: {len(self.clients)}")

    async def handle_request(self, request, websocket):
        command = request['command']
        if command == 'PING':
            print("Pong")
            return

        elif command == 'GET_FILES':
            print('command: get files')
            files = self.file_manager.get_files()
            return Protocol.create_response('GET_FILES', {'files': files})

        elif command == 'OPEN_FILE':
            print('command: open file')
            filename = request['data']['filename']
            self.session_manager.start_session(filename, websocket)
            content = self.file_manager.open_file(filename)
            # if content is None:
            #     return Protocol.create_response('ERROR', {'message': 'File not found'})
            self.session_manager.update_content(filename, content)
            return Protocol.create_response('OPEN_FILE', {'content': content})

        elif command == 'CREATE_FILE':
            print('command: create file')
            filename = request['data']['filename']
            success, error = await self.file_manager.create_file(filename)
            if success:
                return Protocol.create_response('CREATE_FILE', {'status': 'success'})
            else:
                return Protocol.create_response('CREATE_FILE', {'status': 'error', 'error': error})

        elif command == 'DELETE_FILE':
            print('command: delete file')
            filename = request['data']['filename']
            success, error = await self.file_manager.delete_file(filename)
            if success:
                return Protocol.create_response('DELETE_FILE', {'status': 'success'})
            else:
                return Protocol.create_response('DELETE_FILE', {'status': 'error', 'error': error})

        elif command == 'EDIT_FILE':
            print('command: edit file')
            filename = request['data']['filename']
            content = request['data']['content']
            success, error = await self.file_manager.save_file(filename, content)
            if success:
                self.session_manager.update_content(filename, content)
                self.session_manager.share_update(filename, content)
                return Protocol.create_response('EDIT_FILE', {'status': 'success'})
            else:
                return Protocol.create_response('EDIT_FILE', {'status': 'error', 'error': error})

        else:
            return Protocol.create_response('ERROR', {'message': 'Unknown command'})


if __name__ == "__main__":
    server = Server()
    asyncio.run(server.start())
