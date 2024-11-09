import os
import json


class FileManager:
    def __init__(self, base_dir="./Server/server_files"):
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

    def get_files(self):
        try:
            return os.listdir(self.base_dir)
        except OSError:
            return []

    def open_file(self, filename: str):
        filepath = os.path.join(self.base_dir, filename)
        print(f"path to file: {filepath}")
        if not os.path.exists(filepath):
            return False, None
        with open(filepath, "r") as f:
            content = [line.strip() for line in f.readlines()]
            return True, content

    def create_file(self, filename: str):
        filepath = os.path.join(self.base_dir, filename)
        if os.path.exists(filepath):
            return False, "File already exists"
        try:
            with open(filepath, "w") as f:
                f.write("")
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_file(self, filename: str):
        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath):
            return False, "File does not exist"
        try:
            os.remove(filepath)
            return True, None
        except Exception as e:
            return False, str(e)

    def save_file(self, filename: str, content: list[str]):
        filepath = os.path.join(self.base_dir, filename)
        try:
            with open(filepath, "w") as f:
                f.writelines(line + "\n" for line in content)
            return True, None
        except Exception as e:
            return False, str(e)

    def save_history(self, filename: str, all_history: dict[str, list[str]]):
        filename = filename.removesuffix(".txt")
        history_file = f"./Server/files_change_history/{filename}.json"

        with open(history_file, 'w') as file:
            json.dump(all_history, file, indent=4)

    def load_history(self, filename: str):
        filename = filename.removesuffix(".txt")
        history_file = f"./Server/files_change_history/{filename}.json"

        if os.path.exists(history_file):
            with open(history_file, 'r') as file:
                try:
                    history = json.load(file)
                    return history
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {history_file}")
                    return {}
        return {}