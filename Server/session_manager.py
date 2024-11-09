import datetime
import asyncio

from Shared.protocol import Protocol


def safe_list_get(l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default


class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.open_files: dict[str, list[str]] = {}

    def start_session(self, filename: str, websocket):
        if filename not in self.sessions:
            print(f"start session in {filename}")
            self.sessions[filename] = set()
        self.sessions[filename].add(websocket)
        print(self.sessions)

        if filename not in self.open_files:
            self.open_files[filename] = [""]

    def stop_session(self, filename: str, websocket):
        if filename in self.open_files:
            if websocket in self.sessions[filename]:
                print(
                    f"disconnect websocket {websocket} from session {filename}"
                )
                self.sessions[filename].discard(websocket)
                if not self.sessions[filename]:
                    del self.sessions[filename]
                    self.open_files.pop(filename)

    def update_content(self, filename: str, content: list[str]):
        if filename in self.open_files:
            self.open_files[filename] = content

    def apply_operation(self, filename: str, user_id, operation, history):
        print(f"apply operation {operation['op_type']} in file: {filename}")
        current_time = str(datetime.datetime.now())

        if filename in self.open_files:
            if operation["op_type"] == "cancal_changes":
                last_change = history[filename].pop()
                print(last_change)
                return self.cancaling_changes(last_change, filename)
            start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
            while len(self.open_files[filename]) <= start_y:
                self.open_files[filename].append("")

            if operation["op_type"] == "insert":
                start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
                insert_text = operation["text"]
                end_y = start_y
                end_x = start_x + len(insert_text[0])
                close_line = self.open_files[filename][start_y][start_x:]

                for i in range(len(insert_text)):
                    if i == 0:
                        self.open_files[filename][start_y] = self.open_files[filename][start_y][:start_x] + insert_text[
                            i]
                    else:
                        self.open_files[filename].insert(start_y + i, insert_text[i])
                        end_y += 1

                self.open_files[filename][start_y + len(insert_text) - 1] = self.open_files[filename][start_y + len(
                    insert_text) - 1] + close_line

                if end_y != start_y:
                    end_x = len(insert_text[-1])

                operation["end_pos"]["y"] = end_y
                operation["end_pos"]["x"] = end_x

                self.history_maker(filename, history, user_id, current_time, operation)

            elif operation["op_type"] == "delete":
                end_y, end_x = operation["end_pos"]["y"], operation["end_pos"]['x']
                deleted_text = []

                print(
                    f"send_delete_message:\nstart_x={start_x}\nstart_y={start_y}\nend_x={end_x}\nend_y={end_y}\n")

                if start_y == end_y:
                    deleted_text.append(self.open_files[filename][start_y][start_x:end_x])
                    self.open_files[filename][start_y] = (
                        self.open_files[filename][start_y][:start_x]
                        + self.open_files[filename][start_y][end_x:]
                    )
                else:
                    close_line = self.open_files[filename][end_y][end_x:]
                    for i in range(end_y, start_y, -1):
                        if safe_list_get(self.open_files[filename], i, 0) != 0:
                            deleted_text.append(self.open_files[filename][i])
                            self.open_files[filename].pop(i)
                    deleted_text.reverse()

                    self.open_files[filename][start_y] = self.open_files[filename][start_y][:start_x] + close_line

                operation["deleted_text"] = deleted_text
                self.history_maker(filename, history, user_id, current_time, operation)

            elif operation["op_type"] == "new line":
                start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
                new_line = self.open_files[filename][start_y][start_x:]
                self.open_files[filename][start_y] = self.open_files[filename][start_y][:start_x]
                self.open_files[filename].insert(start_y + 1, new_line)

    def history_maker(self, filename: str, history, user_id, current_time, operation):
        if history[filename]:
            history[filename].append({"user_id": user_id, "current_time": current_time, "operation": operation})
        else:
            history[filename] = [{"user_id": user_id, "current_time": current_time, "operation": operation}]

    def cancaling_changes(self, last_change, filename: str):
        operation = last_change["operation"]

        if operation["op_type"] == "insert":
            start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
            end_y, end_x = operation["end_pos"]["y"], operation["end_pos"]["x"]

            close_line = self.open_files[filename][end_y][end_x:]

            if start_y != end_y:
                for i in range(end_y, start_y, -1):
                    self.open_files[filename].pop(i)
            self.open_files[filename][start_y] = self.open_files[filename][start_y][:start_x] + close_line

            return {
                "op_type": "delete",
                "start_pos": {"y": start_y, "x": start_x},
                "end_pos": {"y": end_y, "x": end_x}
                             }

        elif operation["op_type"] == "delete":
            start_y, start_x = operation["start_pos"]["y"], operation["start_pos"]["x"]
            deleted_text = operation["deleted_text"]
            end_y = 0
            close_line = self.open_files[filename][start_y][start_x:]

            for i in range(len(deleted_text)):
                end_y = i
                if i == 0:
                    self.open_files[filename][start_y] = self.open_files[filename][start_y][:start_x] + deleted_text[i]
                else: self.open_files[filename].insert(start_y + i, deleted_text[i])

            self.open_files[filename][start_y + end_y] = self.open_files[filename][start_y + end_y] + close_line
            return {
                "op_type": "insert_text",
                "start_pos": {"y": start_y, "x": start_x},
                "insert_text": deleted_text
            }


    async def share_update(self, filename: str, operation, websocket):
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
                    elif operation["op_type"] == "new line":
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
                    elif operation["op_type"] == "insert_text":
                        message = Protocol.create_message(
                            "EDIT_FILE",
                            {
                                "operation": {
                                    "op_type": operation["op_type"],
                                    "start_pos": {"y": operation["start_pos"]["y"], "x": operation["start_pos"]["x"]},
                                    "insert_text": operation["insert_text"]
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
