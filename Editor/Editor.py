import curses
import asyncio
import json
import time
import pyperclip
#import pdb

from Shared.protocol import Protocol
from .sender_message import SendMessage
from .cursor_muver import CursorMuver
from .selection import Selection


class Editor:
    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.selection = Selection()
        self.senderMessage = SendMessage()
        self.cursorMuver = CursorMuver()

    async def edit(self, content, filename, stop_event, websocket):
        await asyncio.get_event_loop().run_in_executor(
            None,
            curses.wrapper,
            self.curses_editor,
            content,
            filename,
            websocket,
            asyncio.get_event_loop(),
            stop_event,
        )

    async def save_content_file(self, filename, content, websocket):
        message = Protocol.create_message(
            "SAVE_CONTENT", {"filename": filename, "content": "".join(content)}
        )
        await websocket.send(message)

    async def listen_for_update(
            self, websocket, stdscr, current_content, cursor_y, cursor_x
    ):
        try:
            while True:
                message = await websocket.recv()
                update = json.loads(message)
                operation = update["data"]["operation"]

                if operation["op_type"] == "insert":
                    start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
                    text = operation["text"]
                    current_content[start_y] = current_content[start_y][:start_x] + text + current_content[start_y][
                                                                                           start_x:]
                elif operation["op_type"] == "delete":
                    start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
                    end_y, end_x = operation["end_pos"]["y"], operation["end_pos"]["x"]
                    close_line = current_content[end_y][end_x:]
                    if start_y == end_y:
                        current_content[start_y] = current_content[start_y][:start_x] + close_line
                    else:
                        for i in range(start_y + 1, end_y + 1):
                            current_content.pop(i)
                        current_content[start_y] = current_content[start_y][:start_x] + close_line

                elif operation["op_type"] == "new line":
                    start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
                    new_line = current_content[start_y][start_x:]
                    current_content[start_y] = current_content[start_y][:start_x]
                    current_content.insert(start_y + 1, new_line)

                elif operation["op_type"] == "insert_text":
                    start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
                    insert_text = operation["insert_text"]
                    close_line = current_content[start_y][start_x:]
                    for i in range(len(insert_text)):
                        if i == 0:
                            current_content[start_y] = current_content[start_y][:start_x] + insert_text[i]
                        else:
                            current_content.insert(start_y + i, insert_text[i])
                    current_content[start_y + len(insert_text) - 1] += close_line

                self.display_text(stdscr, current_content, cursor_y, cursor_x)

        except asyncio.CancelledError:
            pass

    def insert_text(self, websocket, filename, current_content, cursor_y, cursor_x, event_loop):
        text = pyperclip.paste()
        text = text.split("\n")
        close_line = current_content[cursor_y][cursor_x:]

        for i in range(len(text)):
            if i == 0:
                current_content[cursor_y] = current_content[cursor_y][:cursor_x] + text[i]
            else:
                current_content.insert(cursor_y + i, text[i])
        current_content[cursor_y + len(text) - 1] = current_content[cursor_y + len(text) - 1] + close_line

        self.senderMessage.send_insert_text(websocket, filename, cursor_y, cursor_x, text, event_loop)

    def input_enter(self, current_content, cursor_y, cursor_x):
        new_line = current_content[cursor_y][cursor_x:]
        current_content[cursor_y] = current_content[cursor_y][:cursor_x]

        current_content.insert(cursor_y + 1, new_line)

    def delite_pie(self, current_content, start_y, start_x, end_y, end_x):
        start_line = current_content[start_y][:start_x]
        close_line = current_content[end_y][end_x:]
        if start_y != end_y:
            for i in range(start_y + 1, end_y + 1):
                current_content.pop(i)

        current_content[start_y] = start_line + close_line


    def display_text(self, stdscr, current_content, cursor_y, cursor_x):
        stdscr.clear()
        for i, line in enumerate(current_content):
            stdscr.addstr(i, 0, line)
        stdscr.move(cursor_y, cursor_x)

    def curses_editor(
            self, stdscr, content, filename, websocket, event_loop, stop_event
    ):
        curses.curs_set(1)
        stdscr.clear()
        stdscr.refresh()
        stdscr.nodelay(True)
        current_content = content
        cursor_y, cursor_x = max(len(content) - 1, 0), len(content[-1]) if len(content) > 0 else 0

        last_input_time = time.time()
        start_y, start_x = None, None
        inserted_text = ""
        count_delite_char = 0
        end_y, end_x = None, None

        def update_line(y):
            stdscr.move(y, 0)
            stdscr.clrtoeol()
            stdscr.addstr(y, 0, current_content[y])
            stdscr.move(cursor_y, cursor_x)
            stdscr.refresh()

        self.display_text(stdscr, current_content, cursor_y, cursor_x)

        update_task = asyncio.run_coroutine_threadsafe(
            self.listen_for_update(
                websocket, stdscr, current_content, cursor_y, cursor_x
            ),
            event_loop,
        )

        while True:
            key = stdscr.getch()

            if key == 27:
                if inserted_text or count_delite_char > 0:
                    self.senderMessage.send_edit_message(websocket, filename, inserted_text, start_y, start_x, event_loop)
                    self.senderMessage.send_delete_message(websocket, filename, end_y, end_x, start_y, start_x, count_delite_char,
                                             event_loop)

                asyncio.run_coroutine_threadsafe(
                    self.save_content_file(
                        filename, "".join(current_content), websocket
                    ),
                    event_loop,
                )
                break

            elif key in (curses.KEY_BACKSPACE, 8, 127):
                if inserted_text:
                    self.senderMessage.send_edit_message(websocket, filename, inserted_text, start_y, start_x, event_loop)
                    start_x, start_y = None, None
                    inserted_text = ""

                if start_y is None and start_x is None:
                    start_y, start_x = cursor_y, cursor_x

                if cursor_x > 0:
                    current_content[cursor_y] = current_content[cursor_y][:cursor_x - 1] + current_content[cursor_y][
                                                                                           cursor_x:]
                    cursor_x -= 1
                    end_x = cursor_x
                    update_line(cursor_y)

                elif cursor_y > 0:
                    prev_line_len = len(current_content[cursor_y - 1])
                    current_content[cursor_y - 1] += current_content[cursor_y]
                    del current_content[cursor_y]
                    cursor_y -= 1
                    cursor_x = prev_line_len
                    self.display_text(stdscr, current_content, cursor_y, cursor_x)

                end_y = cursor_y

                count_delite_char += 1
                last_input_time = time.time()

            elif key == 10:
                self.input_enter(current_content, cursor_y, cursor_x)
                self.senderMessage.send_new_line(websocket, filename, cursor_y, cursor_x, event_loop)

                cursor_y += 1
                cursor_x = 0

                self.display_text(stdscr, current_content, cursor_y, cursor_x)

            elif key == curses.KEY_LEFT:
                cursor_x, cursor_y = self.cursorMuver.left(cursor_x, cursor_y, current_content)
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key == curses.KEY_RIGHT:
                cursor_x, cursor_y = self.cursorMuver.right(cursor_x, cursor_y, current_content)
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key == curses.KEY_UP:
                cursor_x, cursor_y = self.cursorMuver.up(cursor_x, cursor_y, current_content)
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key == curses.KEY_DOWN:
                cursor_x, cursor_y = self.cursorMuver.down(cursor_x, cursor_y, current_content)
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key >= 32:
                if count_delite_char > 0:
                    self.senderMessage.send_delete_message(websocket, filename, end_y, end_x, start_y, start_x, count_delite_char, event_loop)
                    count_delite_char = 0

                if inserted_text == "":
                    start_y, start_x = cursor_y, cursor_x

                while len(current_content) <= cursor_y:
                    current_content.append("")

                current_content[cursor_y] = current_content[cursor_y][:cursor_x] + chr(key) + current_content[cursor_y][cursor_x:]
                cursor_x += 1
                update_line(cursor_y)

                inserted_text += chr(key)
                last_input_time = time.time()

            elif key == 5: #ctrl + e выделение
                self.selection.start_selection(cursor_y, cursor_x)
                while True:
                    key = stdscr.getch()
                    if key == 5:
                        self.selection.clear_selection()
                        self.selection.clear_clipboard()
                        self.selection.clear_container()
                        self.display_text(stdscr, current_content, cursor_y, cursor_x)
                        break

                    elif key == curses.KEY_LEFT:
                        self.selection.selection_left(stdscr, cursor_x, cursor_y, current_content)
                        cursor_x, cursor_y = self.cursorMuver.left(cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key == curses.KEY_RIGHT:
                        self.selection.selection_right(stdscr, cursor_x, cursor_y, current_content)
                        cursor_x, cursor_y = self.cursorMuver.right(cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key == curses.KEY_UP:
                        cursor_x, cursor_y = self.cursorMuver.up(cursor_x, cursor_y, current_content)
                        self.selection.selection_up(stdscr, cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key == curses.KEY_DOWN:
                        cursor_x, cursor_y = self.cursorMuver.down(cursor_x, cursor_y, current_content)
                        self.selection.selection_down(stdscr, cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key in (curses.KEY_BACKSPACE, 8, 127):
                        start_y = self.selection.get_start_selection_y()
                        start_x = self.selection.get_start_selection_x()
                        end_y = self.selection.get_end_selection_y()
                        end_x = self.selection.get_end_selection_x()

                        self.delite_pie(current_content, start_y, start_x, end_y, end_x)
                        self.senderMessage.send_delete_message(websocket, filename, start_y, start_x, end_y, end_x, 1, event_loop)
                        self.display_text(stdscr, current_content, cursor_y, cursor_x)

                    elif key == 21: #ctrl + u копирование
                        text = "\n".join(self.selection.get_clipboard())
                        pyperclip.copy(text)

            elif key == 22: #ctrl + v
                self.insert_text(websocket, filename, current_content, cursor_y, cursor_x, event_loop)
                self.display_text(stdscr, current_content, cursor_y, cursor_x)

            if (time.time() - last_input_time) > 1:
                self.senderMessage.send_edit_message(websocket, filename, inserted_text, start_y, start_x, event_loop)
                self.senderMessage.send_delete_message(websocket, filename, end_y, end_x, start_y, start_x, count_delite_char, event_loop)
                inserted_text = ""
                start_x, start_y = None, None
                count_delite_char = 0

        update_task.cancel()
        stop_event.set()