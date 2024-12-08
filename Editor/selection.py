import curses

from .container import Container


class Selection:
    def __init__(self):
        self.container_x = Container()
        self.container_y = Container()
        self.clipboard = []
        self.clipboard_y = 0
        self.start_selection_y, self.start_selection_x = None, None
        self.end_selection_y, self.end_selection_x = None, None

    def start(self, start_y, start_x):
        self.start_selection_y = start_y
        self.start_selection_x = start_x

    def clear_clipboard(self):
        self.clipboard = []
        self.clipboard_y = 0

    def clear_selection(self):
        self.start_selection_y, self.start_selection_x = None, None
        self.end_selection_y, self.end_selection_x = None, None

    def clear_container(self):
        self.container_y.clear()
        self.container_x.clear()

    def get_clipboard(self):
        return self.clipboard

    def get_start_selection_y(self):
        return self.start_selection_y if self.start_selection_y <= self.end_selection_y else self.end_selection_y

    def get_start_selection_x(self):
        return self.start_selection_x if (
                self.start_selection_y < self.end_selection_y or
                self.end_selection_x > self.start_selection_x) \
            else self.end_selection_x

    def get_end_selection_y(self):
        return self.start_selection_y if self.start_selection_y > self.end_selection_y else self.end_selection_y

    def get_end_selection_x(self):
        return self.start_selection_x if (
                self.start_selection_y > self.end_selection_y or
                self.end_selection_x < self.start_selection_x) \
            else self.end_selection_x

    def left(self, stdscr, cursor_x: int, cursor_y: int, text: list[str]):
        if self.container_y.is_empty():
            if self.container_x.is_empty():
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x],
                             curses.A_REVERSE)
                self.clipboard.append(text[cursor_y][cursor_x])
                self.container_x.add("Left")

            elif self.container_x.get_last() == "Left":  # Continue selecting left
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x],
                             curses.A_REVERSE)
                self.clipboard[self.clipboard_y] = text[cursor_y][cursor_x] + \
                                    self.clipboard[self.clipboard_y]
                self.container_x.add("Left")

            elif self.container_x.get_last() == "Right":  # Undo selection right
                self.container_x.pop_last()
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
                self.clipboard[self.clipboard_y] = self.clipboard[self.clipboard_y][:-1]

        elif self.container_y.get_last() == "Up":
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x],
                         curses.A_REVERSE)
            self.clipboard[self.clipboard_y] = text[cursor_y][cursor_x] + self.clipboard[
                self.clipboard_y]

        elif self.container_y.get_last() == "Down":
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
            self.clipboard[self.clipboard_y] = self.clipboard[self.clipboard_y][:-1]
        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    def right(self, stdscr, cursor_x: int, cursor_y: int, text: list[str]):
        if self.container_y.is_empty():
            if self.container_x.is_empty():
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x],
                             curses.A_REVERSE)
                self.clipboard.append(text[cursor_y][cursor_x])
                self.container_x.add("Right")

            elif self.container_x.get_last() == "Right":  # выделение вправо
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x],
                             curses.A_REVERSE)
                self.clipboard[self.clipboard_y] += text[cursor_y][cursor_x]
                self.container_x.add("Right")

            elif self.container_x.get_last() == "Left":  # отмена выделения влево
                self.container_x.pop_last()
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
                self.clipboard[self.clipboard_y] = self.clipboard[self.clipboard_y][1:]

        elif self.container_y.get_last() == "Up":
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
            self.clipboard[self.clipboard_y] = self.clipboard[self.clipboard_y][1:]

        elif self.container_y.get_last() == "Down":
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x],
                         curses.A_REVERSE)
            self.clipboard[self.clipboard_y] += text[cursor_y][cursor_x]

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    def up(self, stdscr, cursor_x: int, cursor_y: int, text: list[str]):
        if self.container_y.is_empty():
            stdscr.addstr(cursor_y, cursor_x, text[cursor_y][cursor_x:],
                          curses.A_REVERSE)
            stdscr.addstr(self.start_selection_y, 0,
                          text[self.start_selection_y][
                          :self.start_selection_x], curses.A_REVERSE)

            if self.container_x.is_empty():
                self.clipboard.append(text[cursor_y][cursor_x:])
            if not self.container_x.is_empty():
                self.clipboard[0] = text[cursor_y][cursor_x:]

            self.clipboard.append(
                text[self.start_selection_y][:self.start_selection_x])
            self.container_y.add("Up")

        elif self.container_y.get_last() == "Up":
            stdscr.addstr(cursor_y, cursor_x, text[cursor_y][cursor_x:],
                          curses.A_REVERSE)
            stdscr.addstr(self.end_selection_y, 0,
                          text[self.end_selection_y][:self.end_selection_x],
                          curses.A_REVERSE)
            self.clipboard[0] = text[self.end_selection_y][
                                :self.end_selection_x] + self.clipboard[0]
            self.clipboard.insert(0, text[cursor_y][cursor_x:])
            self.container_y.add("Up")

        elif self.container_y.get_last() == "Down":
            self.container_y.pop_last()
            stdscr.addstr(self.end_selection_y, 0, text[self.end_selection_y])
            stdscr.addstr(cursor_y, cursor_x, text[cursor_y][cursor_x:])
            self.clipboard.pop(-1)
            self.clipboard[-1] = text[cursor_y][:cursor_x]
            self.clipboard_y -= 1

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    def down(self, stdscr, cursor_x: int, cursor_y: int, text: list[str]):
        if self.container_y.is_empty():
            stdscr.addstr(self.start_selection_y, self.start_selection_x,
                          text[self.start_selection_y][
                          self.start_selection_x:], curses.A_REVERSE)
            stdscr.addstr(cursor_y, 0, text[cursor_y][:cursor_x],
                          curses.A_REVERSE)

            if self.container_x.is_empty():
                self.clipboard.append(
                    text[self.start_selection_y][self.start_selection_x:])
            if not self.container_x.is_empty():
                self.clipboard[0] = text[self.start_selection_y][self.start_selection_x:]

            self.clipboard.append(text[cursor_y][:cursor_x])
            self.container_y.add("Down")
            self.clipboard_y += 1

        elif self.container_y.get_last() == "Down":
            stdscr.addstr(self.end_selection_y, self.end_selection_x,
                          text[self.end_selection_y][self.end_selection_x:],
                          curses.A_REVERSE)
            stdscr.addstr(cursor_y, 0, text[cursor_y][:cursor_x],
                          curses.A_REVERSE)
            self.clipboard[-1] += (
                text[self.end_selection_y][self.end_selection_x:])
            self.clipboard.append(text[cursor_y][:cursor_x])
            self.container_y.add("Down")
            self.clipboard += 1

        elif self.container_y.get_last() == "Up":
            self.container_y.pop_last()
            stdscr.addstr(self.end_selection_y, 0, text[self.end_selection_y])
            stdscr.addstr(cursor_y, 0, text[cursor_y][:cursor_x])
            self.clipboard.pop(0)
            self.clipboard[0] = text[cursor_y][cursor_x:]

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    @staticmethod
    def validate_horizontal(is_left, cursor_x, cursor_y, text):
        if cursor_y < 0 or cursor_y >= len(text):
            raise IndexError

        if is_left:
            if cursor_x <= 0:  # Переход на предыдущую строку
                if cursor_y > 0:
                    cursor_y -= 1
                    cursor_x = len(text[cursor_y]) - 1
                else:
                    raise IndexError
            else:
                cursor_x -= 1
        else:
            if cursor_x >= len(text[cursor_y]):  # Переход на следующую строку
                if cursor_y < len(text) - 1:
                    cursor_y += 1
                    cursor_x = 0
                else:
                    raise IndexError
            else:
                cursor_x += 1

        return cursor_x, cursor_y

    @staticmethod
    def validate_vertical(is_up, cursor_x, cursor_y, text):
        if is_up:
            if cursor_y <= 0:  # Нет строки выше
                raise IndexError
            cursor_y -= 1
        else:
            if cursor_y >= len(text) - 1:  # Нет строки ниже
                raise IndexError
            cursor_y += 1

        if cursor_x >= len(
                text[cursor_y]):
            cursor_x = len(text[cursor_y]) - 1

        return cursor_x, cursor_y
