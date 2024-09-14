import sys
import asyncio
import websockets
import json
import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QSplitter, QTreeView, QPushButton, QHBoxLayout, QInputDialog, QMenu, QWidgetAction
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from Client.client import Client

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = Client("ws://192.168.0.28:8765")
        self.init_ui()
        self.current_file = None

    def init_ui(self):
        self.setWindowTitle('Multiplayer Text Editor')
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.file_tree = QTreeView()
        self.file_tree.setRootIsDecorated(True)
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setSortingEnabled(True)

        self.file_model = QStandardItemModel()
        self.file_tree.setModel(self.file_model)
        self.file_tree.clicked.connect(self.on_file_selected)

        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.on_tree_context_menu)

        self.right_editor = QTextEdit()
        self.right_editor.setPlaceholderText("Правая зона (текст 2)")

        splitter.addWidget(self.file_tree)
        splitter.addWidget(self.right_editor)

        splitter.setSizes([200, 800])

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_file_content)

        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)

        main_layout.addWidget(splitter)
        main_layout.addLayout(button_layout)

        asyncio.run(self.update_file_tree('server_files'))

    def on_tree_context_menu(self, position):
        menu = QMenu()

        new_file_button = QPushButton("Создать новый файл")
        rename_button = QPushButton("Переименовать")
        delite_button = QPushButton("Удалить")

        new_file_action = QWidgetAction(self)
        new_file_action.setDefaultWidget(new_file_button)

        rename_action = QWidgetAction(self)
        rename_action.setDefaultWidget(rename_button)

        delite_action = QWidgetAction(self)
        delite_action.setDefaultWidget(delite_button)

        menu.addAction(new_file_action)
        menu.addAction(rename_action)
        menu.addAction(delite_action)

        new_file_button.clicked.connect(self.create_new_file)
        #rename_button.clicked.conect(self.rename_file)
        delite_button.clicked.connect(self.delite_file)

        menu.exec(self.file_tree.viewport().mapToGlobal(position))

    async def update_file_tree(self, path):
        files = await self.client.request_files(path)
        self.update_tree_view(files)

    def update_tree_view(self, files):
        self.file_model.clear()

        file_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)
        folder_icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)

        for file_name in files:
            item = QStandardItem(file_name)

            if 'txt' in file_name:
                item.setIcon(file_icon)
            else: item.setIcon(folder_icon)

            self.file_model.appendRow(item)

    def on_file_selected(self, index):
        item = self.file_model.itemFromIndex(index)
        file_name = item.text()
        self.current_file = file_name

        asyncio.run(self.load_file_content(file_name))

    def create_new_file(self):
        file_name, ok = QInputDialog.getText(self, 'Создание нового файла', 'Введите имя файла:')
        full_path = os.path.join('server_files', file_name)
        if ok and file_name:
            asyncio.run(self.client.send_new_file(full_path))
            asyncio.run(self.update_file_tree('server_files'))

    def delite_file(self):
        if self.current_file:
            full_path = os.path.join('server_files', self.current_file)
            asyncio.run(self.client.delete_file(full_path))
            asyncio.run(self.update_file_tree('server_files'))

    async def load_file_content(self, file_name):
        full_path = os.path.join('server_files', file_name)
        content = await self.client.request_file_content(full_path)
        self.right_editor.setPlainText(content)

    async def save_file_content(self):
        if self.current_file:
            content = self.right_editor.toPlainText()
            file_path = os.path.join('server_files', self.current_file)
            await self.client.send_file_content(file_path, content)
        else:
            print("No file selected to save.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec())
