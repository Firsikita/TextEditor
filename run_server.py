import asyncio
import websockets
from Server.server import Server


async def run_server():
    server = Server()
    async with websockets.serve(server.echo, "localhost", 8765):
        print("Server started on ws://localhost:8765")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("Server stopped.")
