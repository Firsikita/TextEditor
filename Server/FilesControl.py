import os

mainDir = "server_files"


def create_directories(directory_name):

    if not os.path.exists(mainDir):
        os.makedirs(mainDir)

    dir_path = os.path.join(mainDir, directory_name)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def create_files(file_name, content):
    file_path = os.path.join(mainDir, file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as file:
        file.write(content)


def load_files(file_name):
    file_path = os.path.join(mainDir, file_name)

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return file.read()
    return None
