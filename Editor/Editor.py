import curses
import asyncio
import json
from Shared.protocol import Protocol


class Editor:
    def __init__(self, event_loop):
        self.event_loop = event_loop

    async def edit(self, content, filename, stop_event, websocket):
        await asyncio.get_event_loop().run_in_executor(None, curses.wrapper,
                                                       self.curses_editor,
                                                       content, filename, websocket, asyncio.get_event_loop(),
                                                       stop_event)

    async def save_content_file(self, filename, content, websocket):
        message = Protocol.create_message("SAVE_CONTENT", {
            'filename': filename,
            'content': "".join(content)
        })
        await websocket.send(message)
        #response = await self.websocket.recv()

    async def listen_for_update(self, websocket, stdscr, current_content):
        try:
            while True:
                message = await websocket.recv()
                update = json.loads(message)
                operation = update['data']["operation"]

                if operation["op_type"] == "insert":
                    pos = operation["pos"]
                    char = operation["char"]
                    current_content.insert(pos, char)
                elif operation["op_type"] == "delete":
                    pos = operation["pos"]
                    del current_content[pos]

                stdscr.clear()
                stdscr.addstr(0, 0, ''.join(current_content))
                stdscr.refresh()
        except asyncio.CancelledError:
            pass

    def curses_editor(self, stdscr, content, filename, websocket, event_loop, stop_event):
        curses.curs_set(1)
        stdscr.clear()
        stdscr.addstr(0, 0, content)
        stdscr.refresh()
        current_content = list(content)

        asyncio.run_coroutine_threadsafe(self.listen_for_update(websocket, stdscr, current_content), event_loop)
        cursor_pos = len(current_content)

        while True:
            key = stdscr.getch()

            if key == 27:
                asyncio.run_coroutine_threadsafe(
                    self.save_content_file(filename, "".join(current_content), websocket), event_loop)
                break

            elif key == 127 or key == curses.KEY_BACKSPACE:
                if cursor_pos > 0:
                    cursor_pos -= 1
                    stdscr.move(0, cursor_pos)
                    stdscr.delch()
                    del current_content[cursor_pos]

                    message = Protocol.create_message("EDIT_FILE", {
                        'filename': filename,
                        'operation': {
                            'op_type': 'delete',
                            'pos': cursor_pos,
                        }
                    })
                    asyncio.run_coroutine_threadsafe(
                        websocket.send(message), event_loop)

            elif 32 <= key <= 126:
                ch = chr(key)
                current_content.insert(cursor_pos, ch)
                cursor_pos += 1

                stdscr.clear()
                stdscr.addstr(0, 0, "".join(current_content))
                stdscr.move(0, cursor_pos)
                stdscr.refresh()

                message = Protocol.create_message("EDIT_FILE", {
                    'filename': filename,
                    'operation': {
                        'op_type': 'insert',
                        'pos': cursor_pos - 1,
                        'char': ch
                    }
                })
                asyncio.run_coroutine_threadsafe(
                    websocket.send(message), event_loop)

            stdscr.move(0, cursor_pos)
        stop_event.set()