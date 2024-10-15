from Shared.protocol import Protocol


class SessionManager:
    def __init__(self):
        self.open_files = {}

    def update_content(self, filename, content):
        print(f"CLIENT: update content {filename} : {content}")
        if filename in self.open_files:
            self.open_files[filename] = content
        else:
            self.open_files[filename] = ""

    def apply_operation(self, filename, operation):
        print(f"CLIENT: apply operation {operation['op_type']} in file: {filename}")
        if filename in self.open_files:
            if operation['op_type'] == 'insert':
                pos = operation['pos']
                char = operation['char']
                self.open_files[filename] = self.open_files[filename][
                                            :pos] + char + self.open_files[
                                                               filename][pos:]
            elif operation['op_type'] == 'delete':
                pos = operation['pos']
                self.open_files[filename] = self.open_files[filename][:pos] + \
                                            self.open_files[filename][pos + 1:]

    def get_content(self, filename):
        return self.open_files[filename]

    def close_file(self, filename):
        del self.open_files[filename]