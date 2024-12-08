class Container:
    def __init__(self):
        self.container = []

    def add(self, item):
        self.container.append(item)

    def pop_last(self):
        self.container.pop(-1)

    def get_last(self):
        return self.container[-1]

    def is_empty(self):
        return len(self.container) == 0

    def clear(self):
        self.container = []