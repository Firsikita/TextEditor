import asyncio
import websockets
import aioconsole
from InquirerPy import inquirer
from rich.console import Console
from rich.table import Table
from Shared.protocol import Protocol
from Editor.Editor import Editor


class Client:
    def __init__(self, server_uri):
        self.editor = None
        self.server_uri = server_uri
        self.current_content = ""
        self.filename = None
        self.user_id = None
        self.console = Console()

    @staticmethod
    async def ping(websocket):
        try:
            while True:
                await websocket.send(Protocol.create_message("PING", None))
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass

    async def connect(self):
        async with websockets.connect(self.server_uri) as websocket:
            self.console.print("Text Editor", style="#61afef")
            self.editor = Editor(asyncio.get_event_loop(), self.user_id)
            ping_pong = asyncio.create_task(self.ping(websocket))
            await self.login(websocket)
            await self.handle_message(websocket)
            ping_pong.cancel()

    async def login(self, websocket):
        username = await aioconsole.ainput("Enter username: ")
        await websocket.send(
            Protocol.create_message("LOGIN", {"username": username})
        )
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            result = Protocol.parse_response(response)
            if result["data"]["status"] == "success":
                self.user_id = result["data"]["user_id"]
                self.console.print(
                    f"{username} logged in successfully with {self.user_id}", style="#00A6A6"
                )
            else:
                self.console.print(f"Login failed with {self.user_id}", style="#F08700")

        except asyncio.TimeoutError:
            self.console.print(
                f"Login timed out. Please try again.", style="#F08700"
            )
        except Exception as e:
            print(f"An error occurred: {e}")

    async def handle_message(self, websocket):
        while True:
            print("\n")
            command = await inquirer.select(
                message="Choose a command:",
                choices=[
                    {"name": "List files", "value": "1"},
                    {"name": "Show file content", "value": "2"},
                    {"name": "Create new file", "value": "3"},
                    {"name": "Edit file", "value": "4"},
                    {"name": "Delete file", "value": "5"},
                    {"name": "View change history", "value": "6"},
                    {"name": "Grant access to file", "value": "7"},
                    {"name": "Remove access to file", "value": "8"},
                    {"name": "Exit", "value": "9"},
                ],
                default="1",
            ).execute_async()

            if command == "1":
                file_list = await self.get_files(websocket)
                self.console.print("\nFiles in folder:", style="#61afef")
                for i, file in enumerate(file_list, start=1):
                    self.console.print(f" {i}) {file}")
            if command == "2":
                file_list = await self.get_files(websocket)
                await self.open_file(websocket, file_list)
            if command == "3":
                await self.create_file(websocket)
            if command == "4":
                file_list = await self.get_files(websocket)
                await self.edit_file(websocket, file_list)
            if command == "5":
                file_list = await self.get_files(websocket)
                await self.delete_file(websocket, file_list)
            if command == "6":
                file_list = await self.get_files(websocket)
                await self.get_history(websocket, file_list)
            if command == "7":
                file_list = await self.get_files(websocket)
                await self.grant_access(websocket, file_list)
            if command == "8":
                file_list = await self.get_files(websocket)
                await self.remove_access(websocket, file_list)
            if command == "9":
                self.console.print("Exiting...", style="#61afef")
                break

    async def get_files(self, websocket):
        await websocket.send(Protocol.create_message("GET_FILES"))
        response = await websocket.recv()
        print("Response is:", response)
        file_list = Protocol.parse_response(response)["data"].get("files")
        print("file list is:", file_list)
        if not file_list:
            self.console.print("No files found in the folder.",
                               style="#F08700")
            return None
        return file_list

    async def open_file(self, websocket, file_list):
        selected_file = await inquirer.select(
            message="Choose a file to open:",
            choices=[{"name": file, "value": file} for file in file_list],
        ).execute_async()

        user_id = self.user_id
        host_id = user_id

        if isinstance(selected_file, list):
            filename = selected_file[0]
            host_id = selected_file[1]
        else:
            filename = selected_file

        await websocket.send(
            Protocol.create_message("OPEN_FILE", {"filename": filename, "user_id": user_id, "host_id": host_id})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)

        if result["data"].get("status") == "success":
            self.filename = filename
            content = result["data"].get("content", "")
            self.current_content = content
            self.console.print("\nFile content:", style="#61afef")
            for line in content:
                self.console.print(line)
        else:
            self.console.print(
                f"Error: {result['data']['error']}", style="#F08700"
            )
        await websocket.send(
            Protocol.create_message("CLOSE_FILE", {"filename": filename})
        )

    async def create_file(self, websocket):
        filename = await aioconsole.ainput("Enter new file name: ")
        await websocket.send(
            Protocol.create_message("CREATE_FILE", {"filename": filename})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        if result["data"]["status"] == "success":
            self.console.print(
                f"File '{filename}' created successfully.", style="#00A6A6"
            )
        else:
            self.console.print(
                f"Error creating file '{filename}': {result['data']['error']}.",
                style="#F08700",
            )

    async def delete_file(self, websocket, file_list):
        selected_file = await inquirer.select(
            message="Choose a file to delete: ",
            choices=[{"name": file, "value": file} for file in file_list],
        ).execute_async()

        if isinstance(selected_file, list):
            filename = selected_file[0]
        else:
            filename = selected_file

        await websocket.send(
            Protocol.create_message("DELETE_FILE", {"filename": filename})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        if result["data"]["status"] == "success":
            self.console.print(
                f"File {filename} deleted successfully.", style="#00A6A6"
            )
        else:
            self.console.print(
                f"Error deleting file {filename}: {result['data']['error']}.",
                style="#F08700",
            )
        await websocket.send(
            Protocol.create_message("DELETE_HISTORY", {"filename": filename})
        )

    async def get_user(self, websocket):
        await websocket.send(Protocol.create_message("GET_REGISTERED_USERS"))
        response = await websocket.recv()
        result = Protocol.parse_response(response)

        if result["data"]["status"] == "success":
            users = result["data"]["users"]
            if not users:
                self.console.print("No users found.", style="#F08700")
                return None

            user = await inquirer.select(
                message="Select a user: ",
                choices=[{"name": user_id, "value": user_id} for user_id in users],
            ).execute_async()

            return user
        else:
            self.console.print(f'Error fetching users: {result["data"].get("error", "Unknown error")}.", style="#F08700')
            return None

    async def grant_access(self, websocket, file_list):
        user = await self.get_user(websocket)
        if not user:
            return

        selected_file = await inquirer.select(
            message=f"Choose a file to grant access to {user}:",
            choices=[{"name": file, "value": file} for file in file_list],
        ).execute_async()

        if isinstance(selected_file, list):
            filename = selected_file[0]
        else:
            filename = selected_file

        await websocket.send(
            Protocol.create_message("GRANT_ACCESS", {"user": user, "filename": filename})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        self.console.print(result["data"]["answer"])

    async def remove_access(self, websocket, file_list):
        if not file_list:
            self.console.print("You don't have any files.",
                               style="#F08700")
            return

        selected_file = await inquirer.select(
            message="Choose a file to remove access: ",
            choices=[{"name": file, "value": file} for file in file_list],
        ).execute_async()

        if isinstance(selected_file, list):
            filename = selected_file[0]
        else:
            filename = selected_file

        user = await self.get_user(websocket)
        if not user:
            return

        await websocket.send(Protocol.create_message("REMOVE_ACCESS", {"filename": filename, "user": user}))
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        self.console.print(result["data"]["answer"])

    async def edit_file(self, websocket, file_list):
        selected_file = await inquirer.select(
            message=f"Choose a file to edit: ",
            choices=[{"name": file, "value": file} for file in file_list],
        ).execute_async()

        user_id = self.user_id
        host_id = user_id

        if isinstance(selected_file, list):
            filename = selected_file[0]
            host_id = selected_file[1]
        else:
            filename = selected_file

        print("host_id:", host_id)

        await websocket.send(
            Protocol.create_message("OPEN_FILE", {"filename": filename, "user_id": user_id, "host_id": host_id})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)

        if result["data"].get("status", "") == "success":
            self.filename = filename
            content = result["data"]["content"]
            self.current_content = content

            stop_event = asyncio.Event()
            await self.editor.edit(
                self.current_content, filename, stop_event, websocket
            )

            await websocket.send(
                Protocol.create_message("CLOSE_FILE", {"filename": filename})
            )
        else:
            self.console.print(
                f"Error editing file {filename}: {result['data']['error']}",
                style="#F08700",
            )

    async def get_history(self, websocket, file_list):
        selected_file = await inquirer.select(
            message="Choose a file to view history: ",
            choices=[{"name": file, "value": file} for file in file_list],
        ).execute_async()

        if isinstance(selected_file, list):
            filename = selected_file[0]
        else:
            filename = selected_file

        await websocket.send(
            Protocol.create_message("GET_HISTORY", {"filename": filename})
        )
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        if result["data"]["status"] == "success":
            history = result["data"].get("history", [])
            self.display_history(history)
        else:
            self.console.print(
                "No history found for this file.", style="#EFCA08"
            )

    def display_history(self, history):
        table = Table(
            title="Changes history", show_header=True
        )
        table.add_column("User ID", style="white")
        table.add_column("Time", style="white")
        table.add_column("Operation", style="white")
        table.add_column("Text", style="white")

        for entry in history:
            user_id = entry["user_id"]
            time = entry["time"]
            op_type = entry["operation"]["op_type"]
            text = entry["operation"].get("text", "")

            if op_type == "insert":
                op_display = "[#00A6A6]Insert[/#00A6A6]"
            elif op_type == "delete":
                op_display = "[#F08700]Delete[/#F08700]"
            else:
                op_display = op_type

            table.add_row(user_id, time, op_display, "".join(text))

        self.console.print("\n", table)


if __name__ == "__main__":
    client = Client("ws://localhost:8765")
    asyncio.run(client.connect())
