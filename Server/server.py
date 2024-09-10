import asyncio
import websockets

clients = set()

async def echo(websocket, path):

    clients.add(websocket)
    print(f'New client connected. Total users: {len(clients)}')

    try:
        async for message in websocket:
            await websocket.send(message)
    except websockets.ConnectionClosed:
         print("User disconnected.")

    finally:
        # Удаляем пользователя при отключении
        clients.remove(websocket)
        print(f"User disconnected. Total users: {len(clients)}")

async def main():
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())