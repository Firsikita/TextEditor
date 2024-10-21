import asyncio
import os
import threading

import websockets
import json
import aioconsole
import curses

# HOST = "192.168.0.100"
HOST = "localhost"


async def request_files(websocket, folder_name):
    await websocket.send(f"GET_FILES {folder_name}")
    response = await websocket.recv()
    files = json.loads(response)

    if "error" in files:
        print(f"Error: {files['error']}")
    else:
        print(f"Files in folder '{folder_name}':")
        for file in files:
            print(f"- {file}")


async def create_file(websocket, file_path):
    await websocket.send(f"NEW_FILE {json.dumps({'file_path': file_path})}")
    response = await websocket.recv()
    print(response)


async def delete_file(websocket, file_path):
    await websocket.send(f"DELETE_FILE {json.dumps({'file_path': file_path})}")
    response = await websocket.recv()
    print(response)


async def open_file(websocket, file_path):
    await websocket.send(f"GET_FILE_CONTENT {file_path}")
    response = await websocket.recv()
    result = json.loads(response)

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(result.get("content", ""))


async def save_content_file(websocket, file_path, file_content):
    await websocket.send(
        f"SAVE_CONTENT {json.dumps({'file_path': file_path, 'content': file_content})}"
    )
    response = await websocket.recv()


async def send_edit_operation(websocket, operation):
    await websocket.send(f"EDIT_FILE {json.dumps(operation)}")


def curses_main(stdscr, file_content, file_path, websocket, event_loop):
    curses.curs_set(1)
    stdscr.clear()
    stdscr.addstr(0, 0, file_content)
    stdscr.refresh()

    # Start editing
    cursor_pos = len(file_content)
    content = list(file_content)

    while True:
        ch = stdscr.getch()

        # Exit (Esc key)
        if ch == 27:  # ESC key
            asyncio.run_coroutine_threadsafe(
                save_content_file(websocket, file_path, "".join(content)),
                event_loop,
            )
            break

        elif ch == 127:  # Backspace key
            if cursor_pos > 0:
                cursor_pos -= 1
                stdscr.move(0, cursor_pos)
                stdscr.delch()
                del content[cursor_pos]

                operation = {
                    "file_path": file_path,
                    "operation": {"type": "delete", "pos": cursor_pos},
                }
                asyncio.run_coroutine_threadsafe(
                    send_edit_operation(websocket, operation), event_loop
                )

        elif 32 <= ch <= 126:
            stdscr.insch(cursor_pos, ch)
            stdscr.refresh()
            content.insert(cursor_pos, chr(ch))
            cursor_pos += 1

            operation = {
                "file_path": file_path,
                "operation": {
                    "type": "insert",
                    "pos": cursor_pos - 1,
                    "char": chr(ch),
                },
            }
            asyncio.run_coroutine_threadsafe(
                send_edit_operation(websocket, operation), event_loop
            )

        stdscr.move(0, cursor_pos)


def run_event_loop(event_loop):
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()


def start_curses_in_thread(websocket, file_path, file_content):
    event_loop = asyncio.new_event_loop()
    loop_thread = threading.Thread(target=run_event_loop, args=(event_loop,))
    loop_thread.start()

    def run_curses():
        asyncio.set_event_loop(event_loop)
        curses.wrapper(
            curses_main, file_content, file_path, websocket, event_loop
        )

    curser_thread = threading.Thread(target=run_curses)
    curser_thread.start()

    return curser_thread


async def edit_file(websocket, file_path):
    file_content = ""

    await websocket.send(f"GET_FILE_CONTENT {file_path}")
    response = await websocket.recv()
    result = json.loads(response)
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    file_content = result.get("content", "")

    start_curses_in_thread(websocket, file_path, file_content)


async def ping(websocket):
    try:
        while True:
            await websocket.send("PING")
            response = await websocket.recv()
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("Ping-pong task is cancelled")
        pass


async def handle_message(websocket):
    directory = os.getcwd() + "/Server/server_files"
    while True:
        command = await aioconsole.ainput()

        if command.lower() == "exit":
            print("Exiting...")
            break

        elif command.lower() == "get files":
            folder_name = await aioconsole.ainput("Enter folder name: ")
            if directory != folder_name:
                directory = directory + "/" + folder_name
            await request_files(websocket, folder_name)

        elif command.lower() == "create file":
            file_name = await aioconsole.ainput("Enter new file name: ")
            file_path = directory + "/" + file_name
            await create_file(websocket, file_path)
            await request_files(websocket, directory)

        elif command.lower() == "delete file":
            file_name = await aioconsole.ainput("Enter file name to delete: ")
            file_path = directory + "/" + file_name
            await delete_file(websocket, file_path)
            await request_files(websocket, directory)

        elif command.lower() == "open file":
            print(directory)
            file_name = await aioconsole.ainput("Enter file name: ")
            file_path = directory + "/" + file_name
            await open_file(websocket, file_path)

        elif command.lower() == "edit file":
            file_name = await aioconsole.ainput("Enter file name to edit: ")
            file_path = directory + "/" + file_name
            await edit_file(websocket, file_path)


async def client():
    async with websockets.connect(f"ws://{HOST}:8765") as websocket:
        print("Text editor start")
        ping_pong = asyncio.create_task(ping(websocket))
        await handle_message(websocket)
        ping_pong.cancel()


if __name__ == "__main__":
    asyncio.run(client())
