import asyncio
import websockets
import aioconsole

from Shared.protocol import Protocol
from Editor.Editor import Editor


class Client:
    def __init__(self, server_uri):
        self.editor = None
        self.server_uri = server_uri
        self.current_content = ''
        self.filename = None
        self.user_id = None

    @staticmethod
    async def ping(websocket):
        try:
            while True:
                await websocket.send(Protocol.create_message("PING", None))
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("Ping-pong task is cancelled")
            pass

    async def connect(self):
        async with websockets.connect(self.server_uri) as websocket:
            print("Text editor start")

            self.editor = Editor(asyncio.get_event_loop())

            ping_pong = asyncio.create_task(self.ping(websocket))

            await self.login(websocket)
            await self.handle_message(websocket)

            ping_pong.cancel()

    async def login(self, websocket):
        print("Started login")
        username = await aioconsole.ainput("Enter username: ")

        await websocket.send(
            Protocol.create_message("LOGIN", {"username": username})
        )

        response = await websocket.recv()
        result = Protocol.parse_response(response)

        if result["data"]["status"] == "success":
            self.user_id = result["data"]["user_id"]
            print(f"{username} logged successful with {self.user_id}")
        else:
            print(f"Login failed with {self.user_id}")

    async def handle_message(self, websocket):
        while True:
            await aioconsole.aprint(
                "\nChoose the command:",
                "1. List files",
                "2. Open file",
                "3. Create file",
                "4. Edit file",
                "5. Delete file",
                "6. Get access",
                "7. Exit",
                sep="\n",
            )
            command = await aioconsole.ainput()

            if command == "1":
                await self.get_files(websocket)
            if command == "2":
                await self.open_file(websocket)
            if command == "3":
                await self.create_file(websocket)
                await self.get_files(websocket)
            if command == "4":
                await self.edit_file(websocket)
            if command == "5":
                await self.delete_file(websocket)
                await self.get_files(websocket)
            if command == "6":
                await self.get_access(websocket)
            if command == "7":
                print("Exiting")
                break

    @staticmethod
    async def get_files(websocket):
        await websocket.send(Protocol.create_message("GET_FILES"))
        response = await websocket.recv()
        print(response)
        file_list = Protocol.parse_response(response)["data"]["files"]
        print("\nFiles in folder: ")
        for i, file in enumerate(file_list, start=1):
            print(" " + str(i), file, sep=") ")

    async def open_file(self, websocket):
        filename = await aioconsole.ainput("Enter file name: ")
        await websocket.send(
            Protocol.create_message("OPEN_FILE", {"filename": filename})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        print(f"response: {result}")

        if result["data"].get("status") == "success":
            self.filename = filename
            content = result["data"].get("content", "")
            self.current_content = content
            for line in self.current_content:
                print(line)
        else:
            print(f"Error: {result['data']['error']}")

    @staticmethod
    async def create_file(websocket):
        filename = await aioconsole.ainput("Enter new file name: ")
        await websocket.send(
            Protocol.create_message("CREATE_FILE", {"filename": filename})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        if result["data"]["status"] == "success":
            print(f"File {filename} created successfully.")
        else:
            print(
                f"Error creating file {filename}: {result['data']['error']}."
            )

    @staticmethod
    async def delete_file(websocket):
        filename = await aioconsole.ainput("Enter file name: ")
        await websocket.send(
            Protocol.create_message("DELETE_FILE", {"filename": filename})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        if result["data"]["status"] == "success":
            print(f"File {filename} deleted successfully.")
        else:
            print(
                f"Error deleting file {filename}: {result['data']['error']}."
            )

    async def get_access(self, websocket):
        host_id = await aioconsole.ainput("Enter host id: ")
        filename = await aioconsole.ainput("Enter file name: ")
        await websocket.send(
            Protocol.create_message("GET_ACCESS", {"host_user": host_id, "filename": filename})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        print(result["data"]["answer"])

    async def edit_file(self, websocket):
        filename = await aioconsole.ainput("Enter file name to edit: ")

        await websocket.send(
            Protocol.create_message("OPEN_FILE", {"filename": filename})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)

        if result["data"].get("status", "") == "success":
            self.filename = filename
            content = result["data"]["content"]
            self.current_content = content
            print(f"Content: {self.current_content}")

            stop_event = asyncio.Event()
            await self.editor.edit(
                self.current_content, filename, stop_event, websocket
            )

            await websocket.send(
                Protocol.create_message("CLOSE_FILE", {"filename": filename})
            )
        else:
            print(f"Error editing file {filename}: {result['data']['error']}")


if __name__ == "__main__":
    client = Client("ws://localhost:8765")
    asyncio.run(client.connect())
