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
        print("getting files in", user_folder)
        files = []
        directory = os.path.join(self.base_dir, user_folder)

        additional_files = self.load_user_information()

        file_host_pairs = set()
        for user, user_data in additional_files.items():
            for host, host_data in user_data["host_access"].items():
                for file_name in host_data["files"]:
                    file_host_pairs.add((file_name, host))

        try:
            files = os.listdir(directory)
        except OSError:
            return files + list(file_host_pairs)

        return files + list(file_host_pairs)

    def open_file(self, user_id, filename: str):
        user_folder = user_id + "'s_files"
        filepath = os.path.join(self.base_dir, user_folder, filename)
        print(f"path to file: {filepath}")
        if not os.path.exists(filepath):
            return False, None
        try:
            with open(filepath, "r") as f:
                content = [line.strip() for line in f.readlines()]
                return True, content
        except Exception as e:
            return False, str(e)

    def create_file(self, user_id, filename: str):
        user_folder = user_id + "'s_files"
        filepath = os.path.join(self.base_dir, user_folder, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        print("USER_FOLDER=", user_folder)
        print("FILEPATH=", filepath)

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
        user_info = self.load_user_information()
        user_folder = user_id + "'s_files"
        filepath = os.path.join(self.base_dir, user_folder, filename)

        for host_id, host_data in (
            user_info.get(str(user_id), {}).get("host_access", {}).items()
        ):
            if filename in host_data["files"]:
                host_folder = host_id + "'s_files"
                filepath = os.path.join(self.base_dir, host_folder, filename)
                break

        try:
            with open(filepath, "w") as f:
                f.writelines(line + "\n" for line in content)
            return True, None
        except Exception as e:
            return False, str(e)

    def load_user_information(self):
        if os.path.exists(self.user_info_dir):
            data = self.load_json(self.user_info_dir)
            if isinstance(data, dict):
                return data
            else:
                return {}
        return {}

    def validate_access(self, user_id, host_id, filename):
        user_info = self.load_user_information()
        host_access = user_info.get(str(user_id), {}).get("host_access", {})
        if (
            str(host_id) not in host_access
            or filename not in host_access[str(host_id)]["files"]
        ):
            return (
                False,
                None,
                f"You do not have access to the file '{filename}' of host {host_id}.",
            )

        host_folder = host_id + "'s_files"
        filepath = os.path.join(self.base_dir, host_folder, filename)
        return True, filepath, None

    def remove_access(self, user_id, host_id, filename):
        user_info = self.load_user_information()

        if str(user_id) not in user_info:
            return f"User {user_id} does not have any access records."

        if str(host_id) not in user_info[str(user_id)]["host_access"]:
            return (
                f"User {user_id} does not have access to any files from host {host_id}."
            )

        if (
            filename
            not in user_info[str(user_id)]["host_access"][str(host_id)]["files"]
        ):
            return f'User {user_id} does not have access to file "{filename}" from host {host_id}.'

        user_info[str(user_id)]["host_access"][str(host_id)]["files"].remove(filename)

        if not user_info[str(user_id)]["host_access"][str(host_id)]["files"]:
            del user_info[str(user_id)]["host_access"][str(host_id)]

        self.save_user_information(user_info)

        return f'Access to file "{filename}" for user {user_id} from host {host_id} removed.'

    def grant_access(self, user_id, host_id, filename):
        clients_base = self.load_json(self.clients_base_dir)
        user_info = self.load_user_information()
        host_files = self.get_files(host_id)

        if not any(user.get("User ID") == host_id for user in clients_base):
            return f"File does not exist for host: {host_id}"

        if filename not in host_files:
            return f"File {filename} does not exist for these hosts: {host_id}"

        if str(user_id) not in user_info:
            user_info[str(user_id)] = {"host_access": {}}

        if str(host_id) not in user_info[str(user_id)]["host_access"]:
            user_info[str(user_id)]["host_access"][str(host_id)] = {"files": []}

        if (
            filename
            not in user_info[str(user_id)]["host_access"][str(host_id)]["files"]
        ):
            user_info[str(user_id)]["host_access"][str(host_id)]["files"].append(
                filename
            )

        self.save_user_information(user_info)

        return f'Access granted to file "{filename}" for user: {user_id}'

    def save_user_information(self, user_info):
        with open(self.user_info_dir, "w") as f:
            json.dump(user_info, f, indent=4)

    def append_user(self, user_id):
        user_base = self.load_json(self.clients_base_dir)

        if not any(user.get("User ID") == user_id for user in user_base):
            user_base.append({"User ID": user_id})

        with open(self.clients_base_dir, "w") as f:
            json.dump(user_base, f, indent=4)

    @staticmethod
    def load_json(filepath):
        with open(filepath, "r") as f:
            try:
                info = json.load(f)
                return info
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {filepath}")
        return []

    @staticmethod
    def save_history(filename: str, all_history: dict[str, list[str]]):
        filename = filename.removesuffix(".txt")
        history_file = f"./Server/files_change_history/{filename}.json"

        with open(history_file, "w") as file:
            json.dump(all_history, file, indent=4)

    @staticmethod
    def load_history(filename: str):
        filename = filename.removesuffix(".txt")
        history_file = f"./Server/files_change_history/{filename}.json"

        if os.path.exists(history_file):
            with open(history_file, "r") as file:
                try:
                    history = json.load(file)
                    return history
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {history_file}")
                    return {}
        return {}

    @staticmethod
    def delete_history(filename: str):
        filename = filename.removesuffix(".txt")
        history_file = f"./Server/files_change_history/{filename}.json"

        try:
            os.remove(history_file)
        except FileNotFoundError:
            pass

    def get_all_registered_users(self):
        if not os.path.exists(self.clients_base_dir):
            print(f"Clients base file not found at {self.clients_base_dir}")
            return []
        try:
            with open(self.clients_base_dir, "r") as file:
                data = json.load(file)

            user_ids = [user.get("User ID") for user in data if "User ID" in user]
            return user_ids
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading file {self.clients_base_dir}: {e}")
            return []
