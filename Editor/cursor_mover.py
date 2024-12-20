class CursorMover:
    def left(self, cursor_x: int, cursor_y: int, text: list[str]):
        if cursor_x > 0:
            cursor_x -= 1
        elif cursor_y > 0:
            cursor_y -= 1
            cursor_x = len(text[cursor_y]) if text[cursor_y] else 0
        return cursor_x, cursor_y

    def right(self, cursor_x: int, cursor_y: int, text: list[str]):
        if cursor_x < len(text[cursor_y]) if text[cursor_y] else 0:
            cursor_x += 1
        elif cursor_y < len(text) - 1:
            cursor_y += 1
            cursor_x = 0
        return cursor_x, cursor_y

    def up(self, cursor_x: int, cursor_y: int, text: list[str]):
        if cursor_y > 0:
            cursor_y -= 1
            cursor_x = min(cursor_x, len(text[cursor_y]) if text[cursor_y] else 0)
        return cursor_x, cursor_y

    def down(self, cursor_x: int, cursor_y: int, text: list[str]):
        if cursor_y < len(text) - 1:
            cursor_y += 1
            cursor_x = min(cursor_x, len(text[cursor_y]) if text[cursor_y] else 0)
        return cursor_x, cursor_y
