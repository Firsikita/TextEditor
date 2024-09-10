
import asyncio
import websockets

async def connect_to_server():
    uri = "ws://localhost:8765"  # URL вашего WebSocket-сервера
    async with websockets.connect(uri) as websocket:
        print("Connected to server.")

        # Бесконечный цикл для общения с сервером
        while True:
            # Получаем сообщение от пользователя
            message = input("Enter message to send to the server: ")

            if message.lower() == "exit":
                print("Exiting...")
                break  # Выходим из цикла и закрываем соединение

            # Отправляем сообщение на сервер
            await websocket.send(message)

            # Получаем ответ от сервера
            response = await websocket.recv()
            print(f"Received from server: {response}")


# Запуск асинхронного клиента
asyncio.get_event_loop().run_until_complete(connect_to_server())
