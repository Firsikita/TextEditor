class CursorMuver:
    def left(self, cursor_x, cursor_y, text):
        if cursor_x > 0:
            cursor_x -= 1
        elif cursor_y > 0:
            cursor_y -= 1
            cursor_x = len(text[cursor_y])
        return cursor_x, cursor_y

    def right(self, cursor_x, cursor_y, text):
        if cursor_x < len(text[cursor_y]):
            cursor_x += 1
        elif cursor_y < len(text) - 1:
            cursor_y += 1
            cursor_x = 0
        return cursor_x, cursor_y

    def up(self, cursor_x, cursor_y, text):
        if cursor_y > 0:
            cursor_y -= 1
            cursor_x = min(cursor_x, len(text[cursor_y]))
        return cursor_x, cursor_y

    def down(self, cursor_x, cursor_y, text):
        if cursor_y < len(text) - 1:
            cursor_y += 1
            cursor_x = min(cursor_x, len(text[cursor_y]))
        return cursor_x, cursor_y