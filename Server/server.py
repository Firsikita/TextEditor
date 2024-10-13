import asyncio
import websockets
import signal
import os
import json

clients = set()
server = None
open_files = {}
file_users = {}

async def notify_client(file_name, operation):
    if file_name in file_users:
        for client in file_users[file_name]:
            if client in clients:
                message = json.dumps({"file_name": file_name, "operation": operation})
                await client.send(message)

async def handle_message(websocket, message):
    if message.startswith("PING"):
        print("PONG")
        return

    if message.startswith("GET_FILES"):
        path = message[len("GET_FILES "):]
        if os.path.isdir(path):
            files = os.listdir(path)
            await websocket.send(json.dumps(files))
        else:
            await websocket.send(json.dumps({"error": "Invalid path"}))

    elif message.startswith("OPEN_FILE"):
        file_path = message[len("OPEN_FILE "):]
        try:
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    open_files[file_path] = content
                await websocket.send(json.dumps({"content": content}))

                if file_path not in file_users:
                    file_users[file_path] = set()
                file_users[file_path].add(websocket)
            else:
                await websocket.send(json.dumps({"error": "File not found"}))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))
        print(open_files)
        print(file_users)

    elif message.startswith("CLOSE_FILE"):
        file_path = message[len("CLOSE_FILE "):]
        open_files.pop(file_path, None)
        if file_path in file_users:
            file_users[file_path].discard(websocket)
            if not file_users[file_path]:
                del file_users[file_path]

    elif message.startswith("SAVE_CONTENT"):
        try:
            data = json.loads(message[len("SAVE_CONTENT "):])
            file_path = data["file_path"]
            content = data["content"]

            if os.path.isfile(file_path):
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                await websocket.send(json.dumps({"status": "success", "message": "File saved"}))
            else:
                await websocket.send(json.dumps({"error": "File not found"}))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))

    elif message.startswith("NEW_FILE"):
        try:
            data = json.loads(message[len("NEW_FILE "):])
            file_path = data["file_path"]

            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write("")
                await websocket.send(json.dumps({"status": "success", "message": "File created"}))
            else:
                await websocket.send(json.dumps({"error": "File already exists"}))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))

    elif message.startswith("DELETE_FILE"):
        try:
            data = json.loads(message[len("DELETE_FILE "):])
            file_path = data["file_path"]
            os.remove(file_path)
            await websocket.send(json.dumps({"status": "success", "message": "File deleted"}))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))

    elif message.startswith("EDIT_FILE"):
        try:
            data = json.loads(message[len("EDIT_FILE "):])
            file_path = data["file_path"]
            operation = data["operation"]

            if file_path in open_files:
                if operation["type"] == "insert":
                    pos = operation["pos"]
                    char = operation["char"]
                    open_files[file_path] = open_files[file_path][:pos] + char + open_files[file_path][pos:]
                elif operation["type"] == "delete":
                    pos = operation["pos"]
                    open_files[file_path] = open_files[file_path][:pos] + open_files[file_path][pos + 1:]

                await notify_client(file_path, operation)
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))

async def echo(websocket, path):
    clients.add(websocket)
    print(f'New client connected. Total users: {len(clients)}')

    try:
        async for message in websocket:
            await handle_message(websocket, message)
    except websockets.ConnectionClosed:
        print("User disconnected.")
    finally:
        clients.remove(websocket)
        print(f"User disconnected. Total users: {len(clients)}")

async def main():
    global server
    server = await websockets.serve(echo, "192.168.0.100", 8765)
    print("Server started")
    try:
        await asyncio.Future()
    finally:
        await stop_server()

async def stop_server():
    if server:
        server.close()
        await server.wait_closed()
        print("Server stopped")

if __name__ == "__main__":
    asyncio.run(main())
