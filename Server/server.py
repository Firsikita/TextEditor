import asyncio
import websockets
import signal
import os
import json

clients = set()
server = None


async def handle_message(websocket, message):
    if message.startswith("PING"):
        #print("Pong")
        await websocket.send("PONG")
        return

    print("get files")
    if message.startswith("GET_FILES"):
        path = message[len("GET_FILES "):]
        if os.path.isdir(path):
            files = os.listdir(path)
            print("start send")
            await websocket.send(json.dumps(files))
            print(files)
        else:
            await websocket.send(json.dumps({"error": "Invalid path"}))

    elif message.startswith("GET_FILE_CONTENT"):
        file_path = message[len("GET_FILE_CONTENT "):]
        try:
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                await websocket.send(json.dumps({"content": content}))
            else:
                await websocket.send(json.dumps({"error": "File not found"}))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))

    elif message.startswith("SAVE_CONTENT"):
        try:
            data = json.loads(message[len("SAVE_CONTENT "):])
            file_path = data["file_path"]
            content = data["content"]

            if os.path.isfile(file_path):
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                    print("Content saved")
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

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    try:
        await asyncio.Future()  # Бесконечная задача
    finally:
        await stop_server()

async def stop_server():
    if server:
        server.close()
        await server.wait_closed()
        print("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
