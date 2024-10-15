import asyncio

from Client.client import Client


async def run_client():
    server_uri = "ws://localhost:8765"
    client = Client(server_uri)
    await client.connect()


if __name__ == "__main__":
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        print("Client disconnected.")
