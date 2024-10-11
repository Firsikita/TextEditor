import asyncio
from curses import wrapper

from Client.client import Client


async def run_client(stdscr):
    server_uri = "ws://localhost:8765"
    client = Client(server_uri, stdscr)
    await client.connect()


if __name__ == "__main__":
    try:
        wrapper(lambda stdscr: asyncio.run(run_client(stdscr)))
    except KeyboardInterrupt:
        print("Client disconnected.")
