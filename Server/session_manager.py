from Shared.protocol import Protocol


class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.open_files = {}

    def start_session(self, filename, websocket):
        print(f"start session in {filename}")
        if filename not in self.sessions:
            self.sessions[filename] = set()
        self.sessions[filename].add(websocket)
        print(self.sessions)

        if filename not in self.open_files:
            self.open_files[filename] = ""

    def stop_session(self, filename, websocket):
        if filename in self.open_files:
            if websocket in self.sessions[filename]:
                print(
                    f"disconnect websocket {websocket} from session {filename}"
                )
                self.sessions[filename].discard(websocket)
                if not self.sessions[filename]:
                    del self.sessions[filename]
                    self.open_files.pop(filename)

    def update_content(self, filename, content):
        print(f"SERVER: update content {filename} : {content}")
        if filename in self.open_files:
            self.open_files[filename] = content

    def apply_operation(self, filename, operation):
        print(f"apply operation {operation['op_type']} in file: {filename}")
        if filename in self.open_files:
            if operation["op_type"] == "insert":
                pos = operation["pos"]
                char = operation["char"]
                self.open_files[filename] = (
                    self.open_files[filename][:pos]
                    + char
                    + self.open_files[filename][pos:]
                )
            elif operation["op_type"] == "delete":
                pos = operation["pos"]
                self.open_files[filename] = (
                    self.open_files[filename][:pos]
                    + self.open_files[filename][pos + 1 :]
                )

    async def share_update(self, filename, operation, websocket):
        try:
            if filename in self.sessions:
                for client in self.sessions[filename]:
                    if client != websocket:
                        if operation["op_type"] == "insert":
                            message = Protocol.create_message(
                                "EDIT_FILE",
                                {
                                    "operation": {
                                        "op_type": "insert",
                                        "pos": operation["pos"],
                                        "char": operation["char"],
                                    },
                                    "filename": filename,
                                },
                            )
                        elif operation["op_type"] == "delete":
                            message = Protocol.create_message(
                                "EDIT_FILE",
                                {
                                    "operation": {
                                        "op_type": operation["op_type"],
                                        "pos": operation["pos"],
                                    },
                                    "filename": filename,
                                },
                            )
                        print(message)
                        await client.send(message)
        except Exception as e:
            print(f"Error sending update to client: {e}")

    def get_clients(self):
        return self.sessions.keys()

    def get_content(self, filename):
        if filename in self.open_files:
            return self.open_files[filename]
        return None
