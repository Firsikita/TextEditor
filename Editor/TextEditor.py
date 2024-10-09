import asyncio
import websockets
import json
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
    else: print(result.get('content', ""))

async def ping(websocket):
    try:
        while True:
            await websocket.send("PING")
            response = await websocket.recv()
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("ping-pong task is cancelled")

async def hendle_message(websocket):
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

        elif command.lower() == "create file":
            file_name = await aioconsole.ainput("Enter new file name: ")
            file_path = directory + "/" + file_name
            await create_file(websocket, file_path)
            await request_files(websocket, directory)

        elif command.lower() == "delite file":
            file_name = await aioconsole.ainput("Enter delite file name: ")
            file_path = directory + "/" + file_name
            await delete_file(websocket, file_path)
            await request_files(websocket, directory)

        elif command.lower() == "open file":
            file_name = await aioconsole.ainput("Enter file name: ")
            file_path = directory + "/" + file_name
            await open_file(websocket, file_path)

async def client():
    async with websockets.connect('ws://192.168.0.100:8765') as websocket:
        print("Text editor start")
        ping_pong = asyncio.create_task(ping(websocket))
        await hendle_message(websocket)
        ping_pong.cancel()


if __name__ == '__main__':
    asyncio.run(client())
