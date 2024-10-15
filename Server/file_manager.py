import os

class FileManager:
    def __init__(self, base_dir='./Server/server_files'):
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

    def get_files(self):
        try:
            return os.listdir(self.base_dir)
        except OSError:
            return []

    def open_file(self, filename):
        filepath = os.path.join(self.base_dir, filename)
        print(f"path to file: {filepath}")
        if not os.path.exists(filepath):
            return False, None
        with open(filepath, 'r') as f:
            return True, f.read()

    def create_file(self, filename):
        filepath = os.path.join(self.base_dir, filename)
        if os.path.exists(filepath):
            return False, "File already exists"
        try:
            with open(filepath, 'w') as f:
                f.write("")
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_file(self, filename):
        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath):
            return False, "File does not exist"
        try:
            os.remove(filepath)
            return True, None
        except Exception as e:
            return False, str(e)

    def save_file(self, filename, content):
        filepath = os.path.join(self.base_dir, filename)
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            return True, None
        except Exception as e:
            return False, str(e)
