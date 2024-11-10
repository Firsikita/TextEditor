import os
import json


class FileManager:
    def __init__(self, base_dir="./Server/server_files"):
        self.base_dir = base_dir
        self.user_info_dir = "./Server/clients_information/clients_info.json"
        self.clients_base_dir = "./Server/clients_information/clients_base.json"
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

    def get_files(self, user_id):
        user_folder = user_id + "'s_files"
        files = []
        directory = os.path.join(self.base_dir, user_folder)

        additional_files = self.load_user_information(user_id)

        file_host_pairs = []
        for user, user_data in additional_files.items():
            for host, host_data in user_data['host_access'].items():
                for file_name in host_data['files']:
                    file_host_pairs.append((file_name, host))

        try:
            files = os.listdir(directory)
        except OSError:
            return files + file_host_pairs

        return files + file_host_pairs

    def open_file(self, user_id, filename: str):
        user_folder = user_id + "'s_files"
        filepath = os.path.join(self.base_dir, user_folder, filename)
        print(f"path to file: {filepath}")
        if not os.path.exists(filepath):
            return False, None
        with open(filepath, "r") as f:
            content = [line.strip() for line in f.readlines()]
            return True, content

    def create_file(self, user_id, filename: str):
        user_folder = user_id + "'s_files"
        filepath = os.path.join(self.base_dir, user_folder, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        if os.path.exists(filepath):
            return False, "File already exists"
        try:
            with open(filepath, "w") as f:
                f.write("")
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_file(self, user_id, filename: str):
        user_folder = user_id + "'s_files"
        filepath = os.path.join(self.base_dir, user_folder, filename)
        if not os.path.exists(filepath):
            return False, "File does not exist"
        try:
            os.remove(filepath)
            return True, None
        except Exception as e:
            return False, str(e)

    def save_file(self, user_id, filename: str, content: list[str]):
        user_folder = user_id + "'s_files"
        filepath = os.path.join(self.base_dir, user_folder, filename)
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

    def load_user_information(self, user_id: str):
        if os.path.exists(self.user_info_dir):
            data = self.load_json(self.user_info_dir)
            if isinstance(data, dict):
                return data
            else:
                return {}
        return {}

    def get_access(self, user_id, host_id, filename):
        clients_base = self.load_json(self.clients_base_dir)
        user_info = self.load_user_information(user_id)
        host_files = self.get_files(host_id)

        if not any(user.get("User ID") == host_id for user in clients_base):
            return f"File does not exist hosts: {host_id}"

        if filename not in host_files:
            return f"File does not exist in this hosts: {host_id}, file: {filename}"

        if str(user_id) not in user_info:
            user_info[str(user_id)] = {"host_access": {}}

        if str(host_id) not in user_info[str(user_id)]["host_access"]:
            user_info[str(user_id)]["host_access"][str(host_id)] = {"files": []}

        if filename not in user_info[str(user_id)]["host_access"][str(host_id)]["files"]:
            user_info[str(user_id)]["host_access"][str(host_id)]["files"].append(filename)

        self.save_user_information(user_info)

        return f"Access granted to file: {filename} for user: {user_id}"

    def save_user_information(self, user_info):
        with open(self.user_info_dir, "w") as f:
            json.dump(user_info, f, indent=4)


    def append_user(self, user_id):
        user_base = []
        user_base = self.load_json(self.clients_base_dir)

        if not any(user.get("User ID") == user_id for user in user_base):
            user_base.append({"User ID": user_id})

        with open(self.clients_base_dir, "w") as f:
            json.dump(user_base, f, indent=4)

    def load_json(self, dir):
        with open(dir, "r") as f:
            try:
                info = json.load(f)
                return info
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {dir}")
        return []