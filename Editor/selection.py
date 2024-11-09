import curses

from .container import Container

class Selection:
    def __init__(self):
        self.container_x = Container()
        self.container_y = Container()
        self.clipboard = []
        self.start_selection_y, self.start_selection_x = None, None
        self.end_selection_y, self.end_selection_x = None, None

    def start_selection(self, start_y, start_x):
        self.start_selection_y = start_y
        self.start_selection_x = start_x

    def clear_clipboard(self):
        self.clipboard = []

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
        return self.start_selection_x if (self.start_selection_y < self.end_selection_y or
                                          self.end_selection_x > self.start_selection_x) \
            else self.end_selection_x

    def get_end_selection_y(self):
        return self.start_selection_y if self.start_selection_y > self.end_selection_y else self.end_selection_y

    def get_end_selection_x(self):
        return self.start_selection_x if (self.start_selection_y > self.end_selection_y or
                                          self.end_selection_x < self.start_selection_x)\
            else self.end_selection_x

    def selection_left(self, stdscr, cursor_x: int, cursor_y: int, text: list[str]):
        if self.container_y.is_empty():
            if self.container_x.is_empty():
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
                self.clipboard.append(text[cursor_y][cursor_x])
                self.container_x.add("Left")

            elif self.container_x.get_last() == "Left": #выделение влево
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
                self.clipboard[0] = text[cursor_y][cursor_x] + self.clipboard[0]
                self.container_x.add("Left")

            elif self.container_x.get_last() == "Right": #отмена выделения вправо
                self.container_x.pop_last()
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
                self.clipboard[0] = self.clipboard[0][:-1]

        elif self.container_y.get_last() == "Up":
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
            self.clipboard[0] = text[cursor_y][cursor_x] + self.clipboard[0]

        elif self.container_y.get_last() == "Down":
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
            self.clipboard[0] = self.clipboard[0][:-1]

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    def selection_right(self, stdscr, cursor_x: int, cursor_y: int, text: list[str]):
        if self.container_y.is_empty():
            if self.container_x.is_empty():
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
                self.clipboard.append(text[cursor_y][cursor_x])
                self.container_x.add("Right")

            elif self.container_x.get_last() == "Right": # выделение вправо
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
                self.clipboard[0] += text[cursor_y][cursor_x]
                self.container_x.add("Right")

            elif self.container_x.get_last() == "Left": #отмена выделения влево
                self.container_x.pop_last()
                stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
                self.clipboard[0] = self.clipboard[0][1:]

        elif self.container_y.get_last() == "Up":
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x])
            self.clipboard[0] = self.clipboard[0][1:]

        elif self.container_y.get_last() == "Down":
            stdscr.addch(cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE)
            self.clipboard[0] += text[cursor_y][cursor_x]

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    def selection_up(self, stdscr, cursor_x: int, cursor_y: int, text: list[str]):
        if self.container_y.is_empty():
            stdscr.addstr(cursor_y, cursor_x, text[cursor_y][cursor_x:], curses.A_REVERSE)
            stdscr.addstr(self.start_selection_y, 0, text[self.start_selection_y][:self.start_selection_x], curses.A_REVERSE)
            self.clipboard.append(text[cursor_y][cursor_x:])
            self.clipboard.append(text[self.start_selection_y][:self.start_selection_x])
            self.container_y.add("Up")

        elif self.container_y.get_last() == "Up":
            stdscr.addstr(cursor_y, cursor_x, text[cursor_y][cursor_x:], curses.A_REVERSE)
            stdscr.addstr(self.end_selection_y, 0, text[self.end_selection_y][:self.end_selection_x], curses.A_REVERSE)
            self.clipboard[0] = text[self.end_selection_y][:self.end_selection_x] + self.clipboard[0]
            self.clipboard.insert(0, text[cursor_y][cursor_x:])
            self.container_y.add("Up")

        elif self.container_y.get_last() == "Down":
            self.container_y.pop_last()
            stdscr.addstr(self.end_selection_y, 0, text[self.end_selection_y])
            stdscr.addstr(cursor_y, cursor_x, text[cursor_y][cursor_x:])
            self.clipboard.pop(-1)
            self.clipboard[-1] = text[cursor_y][:cursor_x]

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x

    def selection_down(self, stdscr, cursor_x: int, cursor_y: int, text: list[str]):
        if self.container_y.is_empty():
            stdscr.addstr(self.start_selection_y, self.start_selection_x, text[self.start_selection_y][self.start_selection_x:], curses.A_REVERSE)
            stdscr.addstr(cursor_y, 0, text[cursor_y][:cursor_x], curses.A_REVERSE)
            self.clipboard.append(text[self.start_selection_y][self.start_selection_x:])
            self.clipboard.append(text[cursor_y][:cursor_x])
            self.container_y.add("Down")

        elif self.container_y.get_last() == "Down":
            stdscr.addstr(self.end_selection_y, self.end_selection_x, text[self.end_selection_y][self.end_selection_x:], curses.A_REVERSE)
            stdscr.addstr(cursor_y, 0, text[cursor_y][:cursor_x], curses.A_REVERSE)
            self.clipboard[-1] += (text[self.end_selection_y][self.end_selection_x:])
            self.clipboard.append(text[cursor_y][:cursor_x])
            self.container_y.add("Down")

        elif self.container_y.get_last() == "Up":
            self.container_y.pop_last()
            stdscr.addstr(self.end_selection_y, 0, text[self.end_selection_y])
            stdscr.addstr(cursor_y, 0, text[cursor_y][:cursor_x])
            self.clipboard.pop(0)
            self.clipboard[0] = text[cursor_y][cursor_x:]

        self.end_selection_y, self.end_selection_x = cursor_y, cursor_x