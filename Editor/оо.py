import curses
import curses.ascii


def main(stdscr):
    # Инициализация окна curses
    curses.curs_set(1)  # Показываем курсор
    stdscr.clear()
    stdscr.refresh()

    # Устанавливаем начальную позицию курсора
    cursor_x, cursor_y = 0, 0

    # Текущий текст, который будем редактировать
    text = [
        "This is a simple text editor.",
        "You can edit multiple lines.",
        "Use arrow keys to navigate.",
        "Press Ctrl-G to exit."
    ]

    # Отображение всего текста
    def display_text():
        for i, line in enumerate(text):
            stdscr.addstr(i, 0, line)
        stdscr.move(cursor_y, cursor_x)
        stdscr.refresh()

    # Отображение только одной строки
    def update_line(y):
        stdscr.move(y, 0)
        stdscr.clrtoeol()  # Очистка текущей строки
        stdscr.addstr(y, 0, text[y])
        stdscr.move(cursor_y, cursor_x)
        stdscr.refresh()

    display_text()

    while True:
        key = stdscr.getch()

        if key == curses.KEY_UP:
            # Перемещаем курсор вверх, если это возможно
            if cursor_y > 0:
                cursor_y -= 1
                cursor_x = min(cursor_x, len(text[cursor_y]))

        elif key == curses.KEY_DOWN:
            # Перемещаем курсор вниз, если это возможно
            if cursor_y < len(text) - 1:
                cursor_y += 1
                cursor_x = min(cursor_x, len(text[cursor_y]))

        elif key == curses.KEY_LEFT:
            # Перемещаем курсор влево, если это возможно
            if cursor_x > 0:
                cursor_x -= 1
            elif cursor_y > 0:
                cursor_y -= 1
                cursor_x = len(text[cursor_y])

        elif key == curses.KEY_RIGHT:
            # Перемещаем курсор вправо, если это возможно
            if cursor_x < len(text[cursor_y]):
                cursor_x += 1
            elif cursor_y < len(text) - 1:
                cursor_y += 1
                cursor_x = 0

        elif key == curses.KEY_BACKSPACE or key == 127:
            # Удаление символа
            if cursor_x > 0:
                text[cursor_y] = text[cursor_y][:cursor_x - 1] + text[cursor_y][cursor_x:]
                cursor_x -= 1
                update_line(cursor_y)
            elif cursor_y > 0:
                prev_line_len = len(text[cursor_y - 1])
                text[cursor_y - 1] += text[cursor_y]
                del text[cursor_y]
                cursor_y -= 1
                cursor_x = prev_line_len
                display_text()  # Перерисовываем весь текст, так как изменились несколько строк

        elif key == ord('\n'):
            # Разделение строки
            new_line = text[cursor_y][cursor_x:]
            text[cursor_y] = text[cursor_y][:cursor_x]
            text.insert(cursor_y + 1, new_line)
            cursor_y += 1
            cursor_x = 0
            display_text()  # Перерисовываем весь текст, так как изменились несколько строк

        elif key == curses.ascii.ctrl('g'):
            # Выход из программы
            break

        elif curses.ascii.isprint(key):
            # Ввод букв и других печатаемых символов
            text[cursor_y] = text[cursor_y][:cursor_x] + chr(key) + text[cursor_y][cursor_x:]
            cursor_x += 1
            update_line(cursor_y)

        elif key == 21:
            if cursor_y < len(text) - 1:
                cursor_y += 1
                cursor_x = min(cursor_x, len(text[cursor_y]))


        # Перемещаем курсор на новую позицию
        stdscr.move(cursor_y, cursor_x)

# Запуск программы в curses
curses.wrapper(main)