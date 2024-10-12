import asyncio
import json


class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.file_contents = {}

    def start_session(self, filename, websocket):
        print(f"start session in {filename}")
        if filename not in self.sessions:
            self.sessions[filename] = set()
        self.sessions[filename].add(websocket)

        if filename not in self.file_contents:
            self.file_contents[filename] = ""

    def stop_session(self, filename, websocket):
        print(f"stop session in {filename}")
        if filename in self.sessions:
            if websocket in self.sessions[filename]:
                self.sessions[filename].remove(websocket)
            if not self.sessions[filename]:
                del self.sessions[filename]

    def update_content(self, filename, content):
        print(f"update content {filename} : {content}")
        if filename in self.file_contents:
            self.file_contents[filename] = content

    def share_update(self, filename, content):
        if filename in self.sessions:
            for client in self.sessions[filename]:
                try:
                    asyncio.create_task(client.send(json.dumps({
                        'command': 'update',
                        'data': {
                            'content': content
                        }
                    })))
                except Exception as e:
                    print(f"Error sending update to client: {e}")


    def get_content(self, filename):
        return self.file_contents.get(filename, "")