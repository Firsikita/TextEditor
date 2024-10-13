import asyncio
import websockets
import json
import curses
import aioconsole

async def request_files(websocket, folder_name):
    await websocket.send(f"GET_FILES {folder_name}")
    response = await websocket.recv()
    files = json.loads(response)

    if 'error' in files:
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

    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(result.get('content', ""))

async def save_content_file(websocket, file_path, file_content):
    await websocket.send(f"SAVE_CONTENT {json.dumps({'file_path': file_path, 'content': file_content})}")
    response = await websocket.recv()

async def send_edit_operation(websocket, operation):
    await websocket.send(f"EDIT_FILE {json.dumps(operation)}")

def curses_main(stdscr, file_content, file_path, websocket, event_loop, stop_event):
    curses.curs_set(1)
    stdscr.clear()
    stdscr.addstr(0, 0, file_content)
    stdscr.refresh()

    cursor_pos = len(file_content)
    content = list(file_content)

    while True:
        ch = stdscr.getch()

        if ch == 27:  # ESC key
            asyncio.run_coroutine_threadsafe(save_content_file(websocket, file_path, ''.join(content)), event_loop)
            break

        elif ch == 127:  # Backspace key
            if cursor_pos > 0:
                cursor_pos -= 1
                stdscr.move(0, cursor_pos)
                stdscr.delch()
                del content[cursor_pos]

                operation = {
                    "file_path": file_path,
                    "operation": {
                        "type": "delete",
                        "pos": cursor_pos
                    }
                }
                asyncio.run_coroutine_threadsafe(send_edit_operation(websocket, operation), event_loop)

        elif 32 <= ch <= 126:
            content.insert(cursor_pos, chr(ch))
            cursor_pos += 1

            stdscr.clear()
            stdscr.addstr(0, 0, ''.join(content))
            stdscr.move(0, cursor_pos)
            stdscr.refresh()

            operation = {
                "file_path": file_path,
                "operation": {
                    "type": "insert",
                    "pos": cursor_pos - 1,
                    "char": chr(ch)
                }
            }
            asyncio.run_coroutine_threadsafe(send_edit_operation(websocket, operation), event_loop)

        stdscr.move(0, cursor_pos)

    stop_event.set()

async def run_curses(file_content, file_path, websocket, stop_event):
    await asyncio.get_event_loop().run_in_executor(None, curses.wrapper, curses_main, file_content, file_path, websocket, asyncio.get_event_loop(), stop_event)

async def edit_file(websocket, file_path):
    await websocket.send(f"OPEN_FILE {file_path}")
    response = await websocket.recv()
    print(response)
    result = json.loads(response)
    if 'error' in result:
        print(f"Error: {result['error']}")
        return
    file_content = result.get('content', "")

    stop_event = asyncio.Event()
    await run_curses(file_content, file_path, websocket, stop_event)

    await websocket.send(f"CLOSE_FILE {file_path}")

async def ping(websocket):
    try:
        while True:
            await websocket.send("PING")
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("Ping-pong task is cancelled")
        pass

async def handle_message(websocket):
    directory = "server_files"
    while True:
        command = await aioconsole.ainput()

        if command.lower() == 'exit':
            print("Exiting...")
            break

        elif command.lower() == "get files":
            folder_name = await aioconsole.ainput("Enter folder name: ")
            if directory != folder_name:
                directory = directory + "/" + folder_name
            await request_files(websocket, folder_name)

        elif command.lower() == "create":
            file_name = await aioconsole.ainput("Enter new file name: ")
            file_path = directory + "/" + file_name
            await create_file(websocket, file_path)
            await request_files(websocket, directory)

        elif command.lower() == "delete":
            file_name = await aioconsole.ainput("Enter file name to delete: ")
            file_path = directory + "/" + file_name
            await delete_file(websocket, file_path)
            await request_files(websocket, directory)

        elif command.lower() == "open":
            file_name = await aioconsole.ainput("Enter file name: ")
            file_path = directory + "/" + file_name
            await open_file(websocket, file_path)

        elif command.lower() == "edit":
            file_name = await aioconsole.ainput("Enter file name to edit: ")
            file_path = directory + "/" + file_name
            await edit_file(websocket, file_path)

async def client():
    async with websockets.connect('ws://192.168.0.100:8765') as websocket:
        print("Text editor start")
        ping_pong = asyncio.create_task(ping(websocket))
        await handle_message(websocket)
        ping_pong.cancel()

if __name__ == '__main__':
    asyncio.run(client())
