import asyncio
import websockets
import json

class Client:
    def __init__(self, uri):
        self.uri = uri

    async def request_files(self, path):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(f"GET_FILES {path}")
            response = await websocket.recv()
            files = json.loads(response)
            return files

    async def request_file_content(self, file_path):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(f"GET_FILE_CONTENT {file_path}")
            response = await websocket.recv()

            try:
                data = json.loads(response)
                if "error" in data:
                    return f"Error: {data['error']}"
                return data.get("content", "")
            except json.JSONDecodeError:
                return response

    async def send_file_content(self, file_path, content):
        async with websockets.connect(self.uri) as websocket:
            message = json.dumps({'file_path': file_path, 'content': content})
            await websocket.send(f"SAVE_CONTENT {message}")
            response = await websocket.recv()
            return response

    async def send_new_file(self, file_path):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(f"NEW_FILE {json.dumps({'file_path': file_path})}")
            response = await websocket.recv()
            return response

    async def delete_file(self, file_path):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(f"DELETE_FILE {json.dumps({'file_path': file_path})}")
            response = await websocket.recv()
            return response