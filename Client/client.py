import asyncio
import json

import websockets
import curses

from Shared.protocol import Protocol
from Editor.Editor import Editor

class Client:
    def __init__(self, server_uri, stdscr):
        self.server_uri = server_uri
        self.stdscr = stdscr
        self.current_content = ""
        self.filename = None
        self.lock = asyncio.Lock()

        self.user_id = None

        self.editor = Editor()

    async def connect(self):
        async with websockets.connect(self.server_uri) as websocket:
            print("Text editor start")

            await self.login(websocket)

            asyncio.create_task(self.listen_for_updates(websocket))
            await self.handle_message(websocket)

    async def login(self, websocket):
        username = self.get_user_input("Enter username: ")
        password = self.get_user_input("Enter password: ")

        await websocket.send(Protocol.create_message('LOGIN', {'username': username, 'password': password}))
        response = await websocket.recv()
        result = Protocol.parse_response(response)

        if result['data']['status'] == 'success':
            self.user_id = result['data']['user_id']
            self.stdscr.addstr(3,0,f"Login successful with {self.user_id}")
        else:
            self.stdscr.addstr(3,0,"Login failed")
        self.stdscr.refresh()

    async def handle_message(self, websocket):
        self.stdscr.clear()
        while True:
            self.stdscr.addstr(0, 0,
                               "1. List files\n2. Open file\n3. Create file\n4. Delete file\n5. Exit")
            command = self.get_user_input("Choose a command: ")
            if command == "1":
                await self.get_files(websocket)
            if command == "2":
                await self.open_file(websocket)
            if command == "3":
                await self.create_file(websocket)
            if command == "4":
                await self.delete_file(websocket)
            if command == "5":
                break

    def get_user_input(self, prompt):
        self.stdscr.addstr(10, 0, prompt)
        self.stdscr.refresh()
        curses.echo()
        user_input = self.stdscr.getstr(11, 0, 20).decode('utf-8')
        curses.noecho()
        return user_input

    async def get_files(self, websocket):
        await websocket.send(Protocol.create_message('GET_FILES'))
        response = await websocket.recv()
        file_list = Protocol.parse_response(response)
        print(file_list)
        self.stdscr.clear()
        self.stdscr.addstr(11, 0, f"Files in folder: ")
        for i, file in enumerate(file_list['data']['files'], start=1):
            self.stdscr.addstr(12 + i, 0, f"- {file}")
        self.stdscr.refresh()

    async def open_file(self, websocket):
        filename = self.get_user_input("Enter file name: ")
        await websocket.send(
            Protocol.create_message('OPEN_FILE', {'filename': filename}))
        response = await websocket.recv()
        file_content = Protocol.parse_response(response)
        self.filename = filename
        self.current_content = file_content['data']['content']

        self.editor.initialize_doc(self.current_content)
        await self.edit_file(websocket)

    async def create_file(self, websocket):
        filename = self.get_user_input("Enter new file name: ")
        await websocket.send(
            Protocol.create_message('CREATE_FILE', {'filename': filename}))
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        if result['data']['status'] == 'success':
            self.stdscr.addstr(2, 0, f"File {filename} created successfully.")
        else:
            self.stdscr.addstr(2, 0,
                               f"Error creating file {filename}: {result['data']['error']}.")
        self.stdscr.refresh()

    async def delete_file(self, websocket):
        filename = self.get_user_input("Enter file name: ")
        await websocket.send(
            Protocol.create_message('DELETE_FILE', {'filename': filename}))
        response = await websocket.recv()
        result = Protocol.parse_response(response)
        if result['data']['status'] == 'success':
            self.stdscr.addstr(2, 0, f"File {filename} deleted successfully.")
        else:
            self.stdscr.addstr(2, 0,
                               f"Error deleting file {filename}: {result['data']['error']}.")
        self.stdscr.refresh()

    async def edit_file(self, websocket):
        self.render_editor()

        cursor_pos = len(self.current_content)

        while True:
            key = self.stdscr.getch()

            if key == 27:
                await self.save_file(websocket)
                break

            elif key == 127 or key == curses.KEY_BACKSPACE:
                cursor_pos = max(0, cursor_pos - 1)
                self.editor.delete(cursor_pos, self.user_id)
                await self.send_update(websocket, 'delete', cursor_pos)

            else:
                ch = chr(key)
                self.editor.insert(cursor_pos, ch, self.user_id)
                await self.send_update(websocket, 'insert', cursor_pos, ch)
                cursor_pos+=1

            self.render_editor()

    async def save_file(self, websocket):
        if self.filename and self.current_content:
            await websocket.send(Protocol.create_message('EDIT_FILE',
                                                         {
                                                             'filename': self.filename,
                                                             'content': self.current_content
                                                         }))
            response = await websocket.recv()
            result = Protocol.parse_response(response)
            if result['data']['status'] == 'success':
                self.stdscr.addstr(3, 0, "File saved successfully.")
            else:
                self.stdscr.addstr(3, 0,
                                   f"Error saving file {self.filename}: {result['data']['error']}.")
            self.stdscr.refresh()

    async def listen_for_updates(self, websocket):
        while True:
            try:
                update_message = await websocket.recv()
                operation = Protocol.parse_response(update_message)

                if operation['type'] == 'update':
                    self.editor.apply_operation(operation['data'])
                    self.render_editor()
                #
                #
                # if response['command'] == 'UPDATE_FILE':
                #     filename = response['data']['filename']
                #     content = response['data']['content']
                #
                #     if filename == self.filename:
                #         async with self.lock:
                #             self.current_content = content
                #             self.render_editor()
            except websocket.ConnectionClosed:
                print("Connection closed")
                break

    def render_editor(self):
        self.stdscr.clear()
        content = self.editor.get_content()
        self.stdscr.addstr(0, 0,
                           f"Editing file {self.filename} (Press ESC to save)")
        self.stdscr.addstr(1, 0, "".join(content))
        self.stdscr.refresh()

    # async def recieve_messages(self, websocket):
    #     while True:
    #         try:
    #             message = await websocket.recv()
    #             await self.message_queue.put(message)
    #         except websocket.ConnectionClosed:
    #             print("Connection closed")
    #             break
    #
    #
    # async def process_messages(self):
    #     while True:
    #         message = await self.message_queue.get()
    async def send_update(self, websocket, op_type, pos, ch=None):
        operation = {
            'command': 'update',
            'data': {
                'op_type': op_type,
                'pos': pos,
                'char': ch,
                'user_id': self.user_id,
                'timestamp': self.editor.get_timestamp()
            }
        }

        await websocket.send(json.dumps(operation))


def main(stdscr):
    client = Client("ws://localhost:8765", stdscr)
    asyncio.run(client.connect())


if __name__ == '__main__':
    curses.wrapper(main)
