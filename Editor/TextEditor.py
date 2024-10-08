import asyncio
import websockets
import json

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


async def client():
    directory = "server_files"
    async with websockets.connect('ws://192.168.0.100:8765') as websocket:
        print("Text editor start")
        while True:
            command = input("")

            if command.lower() == 'exit':
                print("Exiting...")
                break

            elif command.lower() == "get files":
                folder_name = input("Enter folder name: ")
                if directory != folder_name:
                    directory = directory + "/" + folder_name
                await request_files(websocket, folder_name)

            elif command.lower() == "create file":
                file_name = input("Enter new file name: ")
                file_path = directory + "/" + file_name
                await create_file(websocket, file_path)
                await request_files(websocket, directory)

            elif command.lower() == "delite file":
                file_name = input("Enter delite file name: ")
                file_path = directory + "/" + file_name
                await delete_file(websocket, file_path)
                await request_files(websocket, directory)

            elif command.lower() == "open file":
                file_name = input("Enter file name: ")
                file_path = directory + "/" + file_name
                await open_file(websocket, file_path)


if __name__ == '__main__':
    asyncio.run(client())
