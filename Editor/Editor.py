import curses
import asyncio
from Shared.protocol import Protocol


class Editor:
    def __init__(self, websocket, event_loop):
        self.websocket = websocket
        self.event_loop = event_loop

    async def edit(self, content, filename, stop_event):
        await asyncio.get_event_loop().run_in_executor(None, curses.wrapper,
                                                       self.curses_editor,
                                                       content, filename,
                                                       stop_event)

    async def save_content_file(self, filename, content):
        message = Protocol.create_message("SAVE_CONTENT", {
            'filename': filename,
            'content': "".join(content)
        })
        await self.websocket.send(message)
        response = await self.websocket.recv()

    def curses_editor(self, stdscr, content, filename, stop_event):
        curses.curs_set(1)
        stdscr.clear()
        stdscr.addstr(0, 0, content)
        stdscr.refresh()

        cursor_pos = len(content)
        current_content = list(content)

        while not stop_event.is_set():
            key = stdscr.getch()

            if key == 27:
                asyncio.run_coroutine_threadsafe(
                    self.save_content_file(filename, "".join(current_content)),
                    self.event_loop)
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
                        self.websocket.send(message), self.event_loop)

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
                    self.websocket.send(message), self.event_loop)

            stdscr.move(0, cursor_pos)
