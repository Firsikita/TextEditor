import curses
import asyncio
import json
import time
import pyperclip
#import pdb

from Shared.protocol import Protocol


class Editor:
    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.clipboard = []
        self.start_selection_y, self.start_selection_x = None, None
        self.end_selection_y, self.end_selection_x = None, None

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

    def selection_left(self, stdscr, cursor_x, cursor_y, text):
        if self.end_selection_x is None:
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
            self.clipboard.append(text[cursor_y][cursor_x])
        elif cursor_x <= self.end_selection_x <= self.start_selection_x: #выделение влево
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
            self.clipboard[0] = text[cursor_y][cursor_x] + self.clipboard[0]
        elif self.end_selection_x >= cursor_x and self.end_selection_x > self.start_selection_x: #отмена выделения вправо
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
            self.clipboard[0] = self.clipboard[0][:-1]


        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    def selection_right(self, stdscr, cursor_x, cursor_y, text):
        if cursor_y == self.start_selection_y:
            if self.end_selection_x is None:
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
                self.clipboard.append(text[cursor_y][cursor_x])
            elif self.end_selection_x <= cursor_x and cursor_x >= self.start_selection_x:  # выделение вправо
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
                self.clipboard[0] += text[cursor_y][cursor_x]
            elif self.end_selection_x <= cursor_x and self.end_selection_x <= self.start_selection_x: #отмена выделения влево
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
                self.clipboard[0] = self.clipboard[0][0:]

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    def selection_up(self, stdscr, cursor_x, cursor_y, text):
        if len(self.clipboard) == 0:
            stdscr.addstr(cursor_y, cursor_x, text[cursor_y][cursor_x:], curses.A_REVERSE)
            stdscr.addstr(self.start_selection_y, 0, text[self.start_selection_y][:self.start_selection_x], curses.A_REVERSE)
            self.clipboard.append(text[cursor_y][cursor_x:])
            self.clipboard.append(text[self.start_selection_y][:self.start_selection_x])
        else:
            stdscr.addstr(cursor_y, cursor_x, text[cursor_y][cursor_x:], curses.A_REVERSE)
            stdscr.addstr(self.end_selection_y, 0, text[self.end_selection_y][:self.end_selection_x], curses.A_REVERSE)
            self.clipboard.append(text[cursor_y][cursor_x:])
            self.clipboard.append(text[self.end_selection_y][:self.end_selection_x])

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    def selection_down(self, stdscr, cursor_x, cursor_y, text):
        if len(self.clipboard) == 0:
            stdscr.addstr(self.start_selection_y, self.start_selection_x, text[self.start_selection_y][self.start_selection_x:], curses.A_REVERSE)
            stdscr.addstr(cursor_y, 0, text[cursor_y][:cursor_x], curses.A_REVERSE)
            self.clipboard.append(text[self.start_selection_y][self.start_selection_x:])
            self.clipboard.append(text[cursor_y][:cursor_x])
        else:
            stdscr.addstr(self.end_selection_y, self.end_selection_x, text[self.end_selection_y][self.end_selection_x:], curses.A_REVERSE)
            stdscr.addstr(cursor_y, 0, text[cursor_y][:cursor_x], curses.A_REVERSE)
            self.clipboard.append(text[self.end_selection_y][self.end_selection_x:])
            self.clipboard.append(text[cursor_y][:cursor_x])

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

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

        self.send_insert_text(websocket, filename, cursor_y, cursor_x, text, event_loop)

    def move_cursor_left(self, cursor_x, cursor_y, text):
        if cursor_x > 0:
            cursor_x -= 1
        elif cursor_y > 0:
            cursor_y -= 1
            cursor_x = len(text[cursor_y])
        return cursor_x, cursor_y

    def move_cursor_right(self, cursor_x, cursor_y, text):
        if cursor_x < len(text[cursor_y]):
            cursor_x += 1
        elif cursor_y < len(text) - 1:
            cursor_y += 1
            cursor_x = 0
        return cursor_x, cursor_y

    def move_cursor_up(self, cursor_x, cursor_y, text):
        if cursor_y > 0:
            cursor_y -= 1
            cursor_x = min(cursor_x, len(text[cursor_y]))
        return cursor_x, cursor_y

    def move_cursor_down(self, cursor_x, cursor_y, text):
        if cursor_y < len(text) - 1:
            cursor_y += 1
            cursor_x = min(cursor_x, len(text[cursor_y]))
        return cursor_x, cursor_y

    def input_enter(self, current_content, cursor_y, cursor_x):
        new_line = current_content[cursor_y][cursor_x:]
        current_content[cursor_y] = current_content[cursor_y][:cursor_x]

        current_content.insert(cursor_y + 1, new_line)

    def display_text(self, stdscr, current_content, cursor_y, cursor_x):
        stdscr.clear()
        for i, line in enumerate(current_content):
            stdscr.addstr(i, 0, line)
        stdscr.move(cursor_y, cursor_x)

    def send_edit_message(self, websocket, filename, inserted_text, start_y, start_x, event_loop):
        if inserted_text:
            message = Protocol.create_message(
                "EDIT_FILE",
                {
                    "filename": filename,
                    "operation": {
                        "op_type": "insert",
                        "start_pos": {"y": start_y, "x": start_x},
                        "length": len(inserted_text),
                        "text": inserted_text,
                    },
                },
            )
            asyncio.run_coroutine_threadsafe(
                websocket.send(message), event_loop
            )

    def send_delete_message(self, websocket, filename, start_y, start_x, end_y, end_x, count, event_loop):
        if count > 0:
            message = Protocol.create_message(
                "EDIT_FILE",
                {
                    "filename": filename,
                    "operation": {
                        "op_type": "delete",
                        "start_pos": {"y": start_y, "x": start_x},
                        "end_pos": {"y": end_y, "x": end_x}
                    },
                },
            )
            asyncio.run_coroutine_threadsafe(
                websocket.send(message), event_loop
            )

    def send_new_line(self, websocket, filename, start_y, start_x, event_loop):
        message = Protocol.create_message(
            "EDIT_FILE",
            {
                "filename": filename,
                "operation": {
                    "op_type": "new line",
                    "start_pos": {"y": start_y, "x": start_x},
                },
            },
        )
        asyncio.run_coroutine_threadsafe(
            websocket.send(message), event_loop
        )

    def send_insert_text(self, websocket, filename, start_y, start_x, insert_text, event_loop):
        message = Protocol.create_message(
            "EDIT_FILE",
            {
                "filename": filename,
                "operation": {
                    "op_type": "insert_text",
                    "start_pos": {"y": start_y, "x": start_x},
                    "insert_text": insert_text,
                },
            },
        )
        asyncio.run_coroutine_threadsafe(
            websocket.send(message), event_loop
        )

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
                    self.send_edit_message(websocket, filename, inserted_text, start_y, start_x, event_loop)
                    self.send_delete_message(websocket, filename, end_y, end_x, start_y, start_x, count_delite_char,
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
                    self.send_edit_message(websocket, filename, inserted_text, start_y, start_x, event_loop)
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
                self.send_new_line(websocket, filename, cursor_y, cursor_x, event_loop)

                cursor_y += 1
                cursor_x = 0

                self.display_text(stdscr, current_content, cursor_y, cursor_x)

            elif key == curses.KEY_LEFT:
                cursor_x, cursor_y = self.move_cursor_left(cursor_x, cursor_y, current_content)
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key == curses.KEY_RIGHT:
                cursor_x, cursor_y = self.move_cursor_right(cursor_x, cursor_y, current_content)
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key == curses.KEY_UP:
                cursor_x, cursor_y = self.move_cursor_up(cursor_x, cursor_y, current_content)
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key == curses.KEY_DOWN:
                cursor_x, cursor_y = self.move_cursor_down(cursor_x, cursor_y, current_content)
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key >= 32:
                if count_delite_char > 0:
                    self.send_delete_message(websocket, filename, end_y, end_x, start_y, start_x, count_delite_char, event_loop)
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
                self.start_selection_y, self.start_selection_x = cursor_y, cursor_x
                while True:
                    key = stdscr.getch()
                    if key == 5:
                        self.start_selection_y, self.start_selection_x = None, None
                        self.end_selection_y, self.end_selection_x = None, None
                        self.display_text(stdscr, current_content, cursor_y, cursor_x)
                        break

                    elif key == curses.KEY_LEFT:
                        self.selection_left(stdscr, cursor_x, cursor_y, current_content)
                        cursor_x, cursor_y = self.move_cursor_left(cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key == curses.KEY_RIGHT:
                        self.selection_right(stdscr, cursor_x, cursor_y, current_content)
                        cursor_x, cursor_y = self.move_cursor_right(cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key == curses.KEY_UP:
                        cursor_x, cursor_y = self.move_cursor_up(cursor_x, cursor_y, current_content)
                        self.selection_up(stdscr, cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key == curses.KEY_DOWN:
                        cursor_x, cursor_y = self.move_cursor_down(cursor_x, cursor_y, current_content)
                        self.selection_down(stdscr, cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key == 21: #ctrl + u копирование
                        text = "\n".join(self.clipboard)
                        self.clipboard = []
                        pyperclip.copy(text)

            elif key == 22: #ctrl + v
                self.insert_text(websocket, filename, current_content, cursor_y, cursor_x, event_loop)
                self.display_text(stdscr, current_content, cursor_y, cursor_x)

            if (time.time() - last_input_time) > 1:
                self.send_edit_message(websocket, filename, inserted_text, start_y, start_x, event_loop)
                self.send_delete_message(websocket, filename, end_y, end_x, start_y, start_x, count_delite_char, event_loop)
                inserted_text = ""
                start_x, start_y = None, None
                count_delite_char = 0

        update_task.cancel()
        stop_event.set()