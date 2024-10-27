from Shared.protocol import Protocol


def safe_list_get(l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default


class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.open_files: dict[list[str]] = {}

    def start_session(self, filename, websocket):
        if filename not in self.sessions:
            print(f"start session in {filename}")
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
        if filename in self.open_files:
            self.open_files[filename] = content

    def apply_operation(self, filename, operation):
        print(f"apply operation {operation['op_type']} in file: {filename}")
        if filename in self.open_files:
            start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
            while len(self.open_files[filename]) <= start_y:
                self.open_files[filename].append("")
            if operation["op_type"] == "insert":
                text = operation["text"]
                self.open_files[filename][start_y] = (
                    self.open_files[filename][start_y][:start_x]
                    + text
                    + self.open_files[filename][start_y][start_x:]
                )
            elif operation["op_type"] == "delete":
                end_y, end_x = operation["end_pos"]["y"], operation["end_pos"]['x']
                print(
                    f"send_delete_message:\nstart_x={start_x}\nstart_y={start_y}\nend_x={end_x}\nend_y={end_y}\n")
                if start_y == end_y:
                    self.open_files[filename][start_y] = (
                        self.open_files[filename][start_y][:start_x]
                        + self.open_files[filename][start_y][end_x:]
                    )
                else:
                    close_line = self.open_files[filename][end_y][end_x:]
                    for i in range(end_y, start_y, -1):
                        if safe_list_get(self.open_files[filename], i, 0) != 0:
                            self.open_files[filename].pop(i)

                    self.open_files[filename][start_y] = self.open_files[filename][start_y][:start_x] + close_line

            elif operation["op_type"] == "new line":
                start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
                new_line = self.open_files[filename][start_y][start_x:]
                self.open_files[filename][start_y] = self.open_files[filename][start_y][:start_x]
                self.open_files[filename].insert(start_y + 1, new_line)

    async def share_update(self, filename, operation, websocket):
        try:
            if filename not in self.sessions:
                raise Exception(f"file {filename} is not in current sessions")
            for client in self.sessions[filename]:
                if client != websocket:
                    message = ""
                    if operation["op_type"] == "insert":
                        message = Protocol.create_message(
                            "EDIT_FILE",
                            {
                                "operation": {
                                    "op_type": "insert",
                                    "start_pos": {"y": operation["start_pos"]["y"], "x": operation["start_pos"]["x"]},
                                    "text": operation["text"],
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
                                    "start_pos": {"y": operation["start_pos"]["y"], "x": operation["start_pos"]["x"]},
                                    "end_pos": {"y": operation["end_pos"]["y"], "x": operation["end_pos"]["x"]},
                                },
                                "filename": filename,
                            },
                        )
                    elif operation['op_type'] == "new line":
                        message = Protocol.create_message(
                            "EDIT_FILE",
                            {
                                "operation": {
                                    "op_type": operation["op_type"],
                                    "start_pos": {"y": operation["start_pos"]["y"],
                                                  "x": operation["start_pos"]["x"]}
                                }
                            }
                        )
                    await client.send(message)
        except Exception as e:
            print(f"Error sending update to client: {e}")

    def get_clients(self):
        return self.sessions.keys()

    def get_content(self, filename):
        if filename in self.open_files:
            return self.open_files[filename]
        return None
