import time
from os import times


#
# class Char:
#     def __init__(self, value, position, user_id, timestamp):
#         self.value = value
#         self.position = position
#         self.user_id = user_id
#         self.timestamp = timestamp
#
#     def __lt__(self, other):
#         if self.position == other.position:
#             if self.user_id == other.user_id:
#                 return self.timestamp < other.timestamp
#             return self.user_id < other.user_id
#         return self.position < other.position


class Editor:
    def __init__(self):
        self.doc = []
        self.deleted = set()

    def initialize_doc(self, content):
        for i, ch in enumerate(content):
            self.doc.append((ch, i, 'initial', time.time()))

    def insert(self, pos, char, user_id):
        timestamp = time.time()
        new_char = (char, pos, user_id, timestamp)
        self.doc.insert(pos, new_char)

        for i in range(pos + 1, len(self.doc)):
            self.doc[i] = (self.doc[i][0], i, self.doc[i][2], self.doc[i][3])

    def delete(self, pos, user_id):
        if pos < len(self.doc) and pos not in self.deleted:
            self.deleted.add(pos)
            self.doc[pos] = (self.doc[pos][0], pos, user_id, time.time(), 'deleted')
        self.doc = [ch for ch in self.doc if not(ch.position == pos and ch.user_id == user_id)]

    def apply_operation(self, operation):
        op_type = operation['op_type']
        pos = operation['pos']
        char = operation['char']
        user_id = operation['user_id']
        timestamp = operation['timestamp']

        if op_type == 'insert':
            self.insert(pos, char, user_id)
        elif op_type == 'delete':
            self.delete(pos, user_id)

    def get_content(self):
        return [ch[0] for ch in self.doc if 'deleted' not in ch]


    def get_timestamp(self):
        return time.time()