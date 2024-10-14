import asyncio
import websockets
import aioconsole

from Editor.TextEditor import request_files, create_file, delete_file, open_file, edit_file

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
    async with websockets.connect('ws://10.249.25.87:8765') as websocket:
        print("Text editor start")
        ping_pong = asyncio.create_task(ping(websocket))
        await handle_message(websocket)
        ping_pong.cancel()

if __name__ == '__main__':
    asyncio.run(client())