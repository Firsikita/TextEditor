import asyncio
import websockets
import signal

clients = set()
server = None


async def echo(websocket, path):
    # Добавляем клиента
    clients.add(websocket)
    print(f'New client connected. Total users: {len(clients)}')

    try:
        async for message in websocket:
            # Рассылаем сообщение всем подключенным клиентам
            for client in clients:
                if client != websocket:
                    await client.send(message)
    except websockets.ConnectionClosed:
        print("User disconnected.")
    finally:
        # Удаляем клиента
        clients.remove(websocket)
        print(f"User disconnected. Total users: {len(clients)}")


async def main():
    global server
    server = await websockets.serve(echo, "192.168.0.100", 8765)  # Замените на нужный IP
    print("Server started")

    # Ждем сигнала для остановки сервера
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("Signal received, stopping server...")
        stop_event.set()

    loop.add_signal_handler(signal.SIGINT, signal_handler, signal.SIGINT, None)
    loop.add_signal_handler(signal.SIGTERM, signal_handler, signal.SIGTERM, None)

    await stop_event.wait()
    server.close()
    await server.wait_closed()
    print("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
