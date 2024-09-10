import asyncio
import websockets

async def connect_to_server():
    uri = "ws://192.168.0.100:8765"

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server.")

            while True:
                # Получаем сообщение от пользователя
                message = input("Enter message to send to the server: ")

                if message.lower() == "exit":
                    print("Exiting...")
                    break

                # Отправляем сообщение на сервер
                await websocket.send(message)

                # Получаем ответ от сервера
                try:
                    response = await websocket.recv()
                    print(f"Received from server: {response}")
                except websockets.ConnectionClosed:
                    print("Server has been stopped or closed the connection.")
                    break  # Выходим из цикла при закрытии соединения

    except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidURI):
        print("Unable to connect to the server. It may be down or the URI may be incorrect.")

asyncio.get_event_loop().run_until_complete(connect_to_server())
