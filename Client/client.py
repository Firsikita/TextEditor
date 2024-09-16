import asyncio
import websockets
import json

from PyQt6.QtCore import QThread, pyqtSignal

class Client(QThread):
    connected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, uri):
        super().__init__()
        self.uri = uri
        self.websocket = None

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
        except Exception as e:
            print(e)

    async def request_files(self, path):
        await self.websocket.send(f"GET_FILES {path}")
        response = await self.websocket.recv()
        files = json.loads(response)
        return files

    async def request_file_content(self, file_path):
        await self.websocket.send(f"GET_FILE_CONTENT {file_path}")
        response = await self.websocket.recv()

        try:
            data = json.loads(response)
            if "error" in data:
                return f"Error: {data['error']}"
            return data.get("content", "")
        except json.JSONDecodeError:
            return response

    async def send_file_content(self, file_path, content):
        message = json.dumps({'file_path': file_path, 'content': content})
        await self.websocket.send(f"SAVE_CONTENT {message}")
        response = await self.websocket.recv()
        return response

    async def send_new_file(self, file_path):
        await self.websocket.send(f"NEW_FILE {json.dumps({'file_path': file_path})}")
        response = await self.websocket.recv()
        return response

    async def delete_file(self, file_path):
        await self.websocket.send(f"DELETE_FILE {json.dumps({'file_path': file_path})}")
        response = await self.websocket.recv()
        return response

async def main():
    client = Client("ws://192.168.0.100:8765")
    await client.connect()

if __name__ == '__main__':
    asyncio.run(main())
