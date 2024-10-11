import asyncio
import json
from contextlib import aclosing

import websockets
import curses

from Shared.protocol import Protocol
from Server.file_manager import FileManager


class Client:
    def __init__(self, server_uri, stdscr):
        self.server_uri = server_uri
        self.stdscr = stdscr
        self.file_manager = FileManager()
        self.current_content = ""
        self.filename = None
        self.lock = asyncio.Lock()

    async def connect(self):
        async with websockets.connect(self.server_uri) as websocket:
            print("Text editor start")
            # ping_pong = asyncio.create_task(self.ping(websocket))
            asyncio.create_task(self.listen_for_updates(websocket))
            await self.handle_message(websocket)

    async def ping(self, websocket):
        try:
            while True:
                await websocket.send("PING")
                response = await websocket.recv()
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("Ping-pong task is cancelled")
            pass

    async def handle_message(self, websocket):
        self.stdscr.clear()
        while True:
            self.stdscr.addstr(0, 0,
                               "1. List files\n2. Open file\n3. Create file\n4. Delete file\n5. Exit")
            # command = await aioconsole.ainput()
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
        self.edit_file(websocket)

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

    def edit_file(self, websocket):
        self.render_editor()

        cursor_pos = len(self.current_content)
        content = list(self.current_content)

        curses.echo()
        while True:
            key = self.stdscr.getch()
            if key == 27:
                asyncio.run_coroutine_threadsafe(self.save_file(websocket),
                                                 asyncio.get_event_loop())
                break
            elif key == 127:
                if cursor_pos > 0:
                    cursor_pos -= 1
                    self.stdscr.move(0, cursor_pos)
                    self.stdscr.delch()
                    del content[cursor_pos]

                    asyncio.run_coroutine_threadsafe(self.save_file(websocket), asyncio.get_event_loop())
            else:
                ch = chr(key)
                self.current_content += ch
                self.stdscr.addstr(1, 0, self.current_content)
                self.stdscr.refresh()
        curses.noecho()

        asyncio.run_coroutine_threadsafe(self.save_file(websocket),
                                         asyncio.get_event_loop())

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
                response = Protocol.parse_response(update_message)

                if response['command'] == 'UPDATE_FILE':
                    filename = response['data']['filename']
                    content = response['data']['content']

                    if filename == self.filename:
                        async with self.lock:
                            self.current_content = content
                            self.render_editor()
            except websocket.ConnectionClosed:
                break

    def render_editor(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0,
                           f"Editing file {self.filename} (Press ESC to save)")
        self.stdscr.addstr(1, 0, self.current_content)
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


def main(stdscr):
    client = Client("ws://localhost:8765", stdscr)
    asyncio.run(client.connect())


if __name__ == '__main__':
    curses.wrapper(main)
