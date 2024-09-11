import sys
import asyncio
import websockets
import json

from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QSplitter, QTreeView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Multiplayer Text Editor')
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Создание основного вертикального layout
        layout = QVBoxLayout(central_widget)

        # Создание QSplitter для разделения на две зоны
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Создание QTreeView для отображения директорий и файлов
        self.file_tree = QTreeView()
        self.file_tree.setRootIsDecorated(True)
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setSortingEnabled(True)

        # Создание модели для QTreeView
        self.file_model = QStandardItemModel()
        self.file_tree.setModel(self.file_model)

        # Создание текстового редактора
        right_editor = QTextEdit()
        right_editor.setPlaceholderText("Правая зона (текст 2)")

        # Добавляем виджеты в splitter
        splitter.addWidget(self.file_tree)
        splitter.addWidget(right_editor)

        # Устанавливаем начальные размеры зон
        splitter.setSizes([200, 800])

        # Добавляем splitter в основной layout
        layout.addWidget(splitter)

        # Запрос списка файлов и отображение их в QTreeView
        asyncio.run(self.update_file_tree('server_files'))

    async def request_files(self, path):
        uri = "ws://192.168.0.100:8765"
        async with websockets.connect(uri) as websocket:
            await websocket.send(f"GET_FILES {path}")
            response = await websocket.recv()
            files = json.loads(response)
            return files

    async def update_file_tree(self, path):
        files = await self.request_files(path)
        self.update_tree_view(files)

    def update_tree_view(self, files):
        self.file_model.clear()
        for file_name in files:
            item = QStandardItem(file_name)
            self.file_model.appendRow(item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec())
