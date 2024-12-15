import curses
import asyncio
import time
import pyperclip
from Shared.protocol import Protocol

try:
    from message_sender import MessageSender
    from cursor_mover import CursorMover
    from selection import Selection
except ModuleNotFoundError:
    from .message_sender import MessageSender
    from .cursor_mover import CursorMover
    from .selection import Selection


class Editor:
    def __init__(self, event_loop, user_id):
        self.user_id = user_id
        self.event_loop = event_loop
        self.selection = Selection()
        self.sender = MessageSender()
        self.cursor = CursorMover()

    async def edit(self, content: list[str], filename: str, stop_event, websocket):
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

    @staticmethod
    async def save_content_file(filename: str, content: list[str], websocket):
        message = Protocol.create_message(
            "SAVE_CONTENT", {"filename": filename, "content": "".join(content)}
        )
        await websocket.send(message)

    async def listen_for_update(
        self,
        websocket,
        stdscr,
        current_content: list[str],
        cursor_y: int,
        cursor_x: int,
    ):
        try:
            while True:
                message = await websocket.recv()
                update = Protocol.parse_response(message)
                operation = update["data"]["operation"]
                start_y, start_x = (
                    operation["start_pos"]["y"],
                    operation["start_pos"]["x"],
                )

                if operation["op_type"] == "insert":
                    insert_text = operation["text"]
                    close_line = current_content[start_y][start_x:]
                    for i in range(len(insert_text)):
                        if i == 0:
                            current_content[start_y] = (
                                current_content[start_y][:start_x] + insert_text[i]
                            )
                        else:
                            current_content.insert(start_y + i, insert_text[i])
                    current_content[start_y + len(insert_text) - 1] += close_line
                elif operation["op_type"] == "delete":
                    end_y, end_x = (
                        operation["end_pos"]["y"],
                        operation["end_pos"]["x"],
                    )
                    close_line = current_content[end_y][end_x:]
                    if start_y == end_y:
                        current_content[start_y] = (
                            current_content[start_y][:start_x] + close_line
                        )
                    else:
                        for i in range(start_y + 1, end_y + 1):
                            current_content.pop(i)
                        current_content[start_y] = (
                            current_content[start_y][:start_x] + close_line
                        )

                elif operation["op_type"] == "new line":
                    new_line = current_content[start_y][start_x:]
                    current_content[start_y] = current_content[start_y][:start_x]
                    current_content.insert(start_y + 1, new_line)

                elif operation["op_type"] == "insert_text":
                    insert_text = operation["insert_text"]
                    close_line = current_content[start_y][start_x:]
                    for i in range(len(insert_text)):
                        if i == 0:
                            current_content[start_y] = (
                                current_content[start_y][:start_x] + insert_text[i]
                            )
                        else:
                            current_content.insert(start_y + i, insert_text[i])
                    current_content[start_y + len(insert_text) - 1] += close_line

                self.display_text(stdscr, current_content, cursor_y, cursor_x)

        except asyncio.CancelledError:
            pass

    def insert_text(
        self,
        websocket,
        filename: str,
        current_content: list[str],
        cursor_y: int,
        cursor_x: int,
        event_loop,
    ):

        text = pyperclip.paste()
        text = text.split("\n")
        close_line = current_content[cursor_y][cursor_x:]

        for i in range(len(text)):
            if i == 0:
                current_content[cursor_y] = (
                    current_content[cursor_y][:cursor_x] + text[i]
                )
            else:
                current_content.insert(cursor_y + i, text[i])
        current_content[cursor_y + len(text) - 1] = (
            current_content[cursor_y + len(text) - 1] + close_line
        )

        self.sender.send_edit_message(
            websocket,
            filename,
            text,
            cursor_y,
            cursor_x,
            event_loop,
            self.user_id,
        )

    @staticmethod
    def insert_enter(current_content: list[str], cursor_y: int, cursor_x: int):
        new_line = current_content[cursor_y][cursor_x:]
        current_content[cursor_y] = current_content[cursor_y][:cursor_x]

        current_content.insert(cursor_y + 1, new_line)

    @staticmethod
    def delete_piece(
        current_content: list[str],
        start_y: int,
        start_x: int,
        end_y: int,
        end_x: int,
    ):
        start_line = current_content[start_y][:start_x]
        close_line = current_content[end_y][end_x:]
        if start_y != end_y:
            for i in range(start_y + 1, end_y + 1):
                current_content.pop(i)

        current_content[start_y] = start_line + close_line

    @staticmethod
    def display_text(stdscr, current_content: list[str], cursor_y: int, cursor_x: int):
        stdscr.clear()
        for i, line in enumerate(current_content):
            stdscr.addstr(i, 0, line)
        stdscr.move(cursor_y, cursor_x)

    def curses_editor(
        self,
        stdscr,
        content: list[str],
        filename: str,
        websocket,
        event_loop,
        stop_event,
    ):
        import locale

        locale.setlocale(locale.LC_ALL, "")
        curses.curs_set(1)
        stdscr.clear()
        stdscr.refresh()
        stdscr.nodelay(True)
        current_content = content
        cursor_y, cursor_x = max(len(content) - 1, 0), (
            len(content[-1]) if len(content) > 0 else 0
        )

        last_input_time = time.time()
        start_y, start_x = None, None
        inserted_text: list[str] = []
        count_delete_char = 0
        end_y, end_x = None, None

        def update_line(y: int):
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
                if inserted_text or count_delete_char > 0:
                    self.sender.send_edit_message(
                        websocket,
                        filename,
                        inserted_text,
                        start_y,
                        start_x,
                        event_loop,
                        self.user_id,
                    )
                    self.sender.send_delete_message(
                        websocket,
                        filename,
                        end_y,
                        end_x,
                        start_y,
                        start_x,
                        count_delete_char,
                        event_loop,
                        self.user_id,
                    )

                asyncio.run_coroutine_threadsafe(
                    self.save_content_file(filename, current_content, websocket),
                    event_loop,
                )
                break

            elif key in (curses.KEY_BACKSPACE, 8, 127):
                if inserted_text:
                    self.sender.send_edit_message(
                        websocket,
                        filename,
                        inserted_text,
                        start_y,
                        start_x,
                        event_loop,
                        self.user_id,
                    )
                    start_x, start_y = None, None
                    inserted_text.clear()

                if start_y is None and start_x is None:
                    start_y, start_x = cursor_y, cursor_x

                if cursor_x > 0:
                    current_content[cursor_y] = (
                        current_content[cursor_y][: cursor_x - 1]
                        + current_content[cursor_y][cursor_x:]
                    )
                    cursor_x -= 1
                    end_x = cursor_x
                    update_line(cursor_y)

                elif cursor_y > 0:
                    prev_line_len = len(current_content[cursor_y - 1])
                    current_content[cursor_y - 1] += current_content[cursor_y]
                    del current_content[cursor_y]
                    cursor_y -= 1
                    cursor_x = prev_line_len
                    end_x = cursor_x
                    self.display_text(stdscr, current_content, cursor_y, cursor_x)

                end_y = cursor_y

                count_delete_char += 1
                last_input_time = time.time()

            elif key == 10:
                self.insert_enter(current_content, cursor_y, cursor_x)
                self.sender.send_new_line(
                    websocket,
                    filename,
                    cursor_y,
                    cursor_x,
                    event_loop,
                    self.user_id,
                )

                cursor_y += 1
                cursor_x = 0

                self.display_text(stdscr, current_content, cursor_y, cursor_x)

            elif key == curses.KEY_LEFT:
                cursor_x, cursor_y = self.cursor.left(
                    cursor_x, cursor_y, current_content
                )
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key == curses.KEY_RIGHT:
                cursor_x, cursor_y = self.cursor.right(
                    cursor_x, cursor_y, current_content
                )
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key == curses.KEY_UP:
                cursor_x, cursor_y = self.cursor.up(cursor_x, cursor_y, current_content)
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key == curses.KEY_DOWN:
                cursor_x, cursor_y = self.cursor.down(
                    cursor_x, cursor_y, current_content
                )
                stdscr.move(cursor_y, cursor_x)
                stdscr.refresh()

            elif key >= 32:
                if count_delete_char > 0:
                    self.sender.send_delete_message(
                        websocket,
                        filename,
                        end_y,
                        end_x,
                        start_y,
                        start_x,
                        count_delete_char,
                        event_loop,
                        self.user_id,
                    )
                    count_delete_char = 0

                if not inserted_text:
                    start_y, start_x = cursor_y, cursor_x

                while len(current_content) <= cursor_y:
                    current_content.append("")

                current_content[cursor_y] = (
                    current_content[cursor_y][:cursor_x]
                    + chr(key)
                    + current_content[cursor_y][cursor_x:]
                )
                cursor_x += 1
                update_line(cursor_y)

                if not inserted_text:
                    inserted_text.append(chr(key))
                else:
                    inserted_text[0] += chr(key)

                last_input_time = time.time()

            elif key == 5:  # ctrl + e выделение
                self.selection.start(cursor_y, cursor_x)
                while True:
                    key = stdscr.getch()
                    if key == 5:
                        self.selection.clear_selection()
                        self.selection.clear_clipboard()
                        self.selection.clear_container()
                        self.display_text(stdscr, current_content, cursor_y, cursor_x)
                        break

                    elif key == curses.KEY_LEFT:
                        if cursor_x - 1 >= 0:
                            cursor_x, cursor_y = self.cursor.left(
                                cursor_x, cursor_y, current_content
                            )
                            self.selection.left(
                                stdscr, cursor_x, cursor_y, current_content
                            )
                            stdscr.move(cursor_y, cursor_x)
                            stdscr.refresh()

                    elif key == curses.KEY_RIGHT:
                        if cursor_x + 1 <= len(current_content[cursor_y]):
                            self.selection.right(
                                stdscr, cursor_x, cursor_y, current_content
                            )
                            cursor_x, cursor_y = self.cursor.right(
                                cursor_x, cursor_y, current_content
                            )
                            stdscr.move(cursor_y, cursor_x)
                            stdscr.refresh()

                    elif key == curses.KEY_UP:
                        cursor_x, cursor_y = self.cursor.up(
                            cursor_x, cursor_y, current_content
                        )
                        self.selection.up(stdscr, cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key == curses.KEY_DOWN:
                        cursor_x, cursor_y = self.cursor.down(
                            cursor_x, cursor_y, current_content
                        )
                        self.selection.down(stdscr, cursor_x, cursor_y, current_content)
                        stdscr.move(cursor_y, cursor_x)
                        stdscr.refresh()

                    elif key in (curses.KEY_BACKSPACE, 8, 127):
                        start_y = self.selection.get_start_selection_y()
                        start_x = self.selection.get_start_selection_x()
                        end_y = self.selection.get_end_selection_y()
                        end_x = self.selection.get_end_selection_x()

                        self.delete_piece(
                            current_content, start_y, start_x, end_y, end_x
                        )
                        self.sender.send_delete_message(
                            websocket,
                            filename,
                            start_y,
                            start_x,
                            end_y,
                            end_x,
                            1,
                            event_loop,
                            self.user_id,
                        )
                        self.display_text(stdscr, current_content, cursor_y, cursor_x)

                    elif key == 21:  # ctrl + u копирование
                        text = "\n".join(self.selection.get_clipboard())
                        pyperclip.copy(text)

            elif key == 22:  # ctrl + v вставка
                self.insert_text(
                    websocket,
                    filename,
                    current_content,
                    cursor_y,
                    cursor_x,
                    event_loop,
                )
                self.display_text(stdscr, current_content, cursor_y, cursor_x)

            elif key == 24:  # ctrl + x отмена действия
                self.sender.cancel_changes(
                    websocket, filename, event_loop, self.user_id
                )

            if (time.time() - last_input_time) > 1:
                self.sender.send_edit_message(
                    websocket,
                    filename,
                    inserted_text,
                    start_y,
                    start_x,
                    event_loop,
                    self.user_id,
                )
                self.sender.send_delete_message(
                    websocket,
                    filename,
                    end_y,
                    end_x,
                    start_y,
                    start_x,
                    count_delete_char,
                    event_loop,
                    self.user_id,
                )
                inserted_text.clear()
                start_x, start_y = None, None
                count_delete_char = 0

        update_task.cancel()
        stop_event.set()
