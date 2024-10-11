import asyncio
import json


class SessionManager:
    def __init__(self):
        self.sessions = {}

    def start_session(self, filename, websocket):
        print(f"start session in {filename}")
        if filename not in self.sessions:
            self.sessions[filename] = {
                'clients': set(),
                'content': None
            }
        self.sessions[filename]['clients'].add(websocket)

    def stop_session(self, filename, websocket):
        print(f"stop session in {filename}")
        if filename in self.sessions:
            self.sessions[filename]['clients'].discard(websocket)
            if not self.sessions[filename]['clients']:
                del self.sessions[filename]

    def update_content(self, filename, content):
        print(f"update content {filename} : {content}")
        if filename in self.sessions:
            self.sessions[filename]['content'] = content

    def share_update(self, filename, content):
        if filename in self.sessions:
            for client in self.sessions[filename]['clients']:
                asyncio.create_task(client.send(json.dumps({
                    'command': 'UPDATE_FILE',
                    'data': {
                        'filename': filename,
                        'content': content
                    }
                })))

    def get_content(self, filename):
        if filename in self.sessions:
            return self.sessions[filename]['content']
        return None