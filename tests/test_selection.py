import curses
from unittest import mock

import pytest
from unittest.mock import Mock, patch
from Editor.selection import Selection
from Editor.container import Container


@pytest.fixture
def selection():
    selection = Selection()
    selection.container_x = Mock()
    selection.container_y = Mock()
    return selection


@pytest.mark.parametrize(
    "start_y, start_x, expected_start_y, expected_start_x",
    [
        (5, 3, 5, 3),
        (0, 0, 0, 0),
    ],
)
def test_start(selection, start_y, start_x, expected_start_y, expected_start_x):
    selection.start(start_y, start_x)
    assert selection.start_selection_y == expected_start_y
    assert selection.start_selection_x == expected_start_x


def test_clear_clipboard(selection):
    selection.clipboard = ["data"]
    selection.clipboard_y = 5
    selection.clear_clipboard()
    assert selection.clipboard == []
    assert selection.clipboard_y == 0


def test_clear_selection(selection):
    selection.start_selection_y, selection.start_selection_x = 5, 3
    selection.end_selection_y, selection.end_selection_x = 10, 6
    selection.clear_selection()
    assert selection.start_selection_y is None
    assert selection.start_selection_x is None
    assert selection.end_selection_y is None
    assert selection.end_selection_x is None


def test_clear_container(selection):
    selection.clear_container()
    selection.container_y.clear.assert_called_once()
    selection.container_x.clear.assert_called_once()


def test_get_clipboard(selection):
    selection.clipboard = ["item1", "item2"]
    assert selection.get_clipboard() == ["item1", "item2"]


@pytest.mark.parametrize(
    "start_y, start_x, end_y, end_x, expected",
    [
        (2, 3, 5, 6, 2),  # Start selection above end selection
        (6, 3, 5, 6, 5),  # Start selection below end selection
    ],
)
def test_get_start_selection_y(selection, start_y, start_x, end_y, end_x, expected):
    selection.start_selection_y = start_y
    selection.start_selection_x = start_x
    selection.end_selection_y = end_y
    selection.end_selection_x = end_x
    assert selection.get_start_selection_y() == expected


@pytest.mark.parametrize(
    "start_y, start_x, end_y, end_x, expected",
    [
        (5, 2, 2, 3, 2),  # Start selection to the right of end selection
        (2, 3, 5, 6, 3),  # Start selection to the left of end selection
    ],
)
def test_get_start_selection_x(selection, start_y, start_x, end_y, end_x, expected):
    selection.start_selection_y = start_y
    selection.start_selection_x = start_x
    selection.end_selection_y = end_y
    selection.end_selection_x = end_x
    assert selection.get_start_selection_x() == expected


@pytest.mark.parametrize(
    "start_y, start_x, end_y, end_x, expected",
    [
        (2, 3, 5, 6, 5),  # End selection below start selection
        (6, 3, 5, 6, 6),  # End selection above start selection
    ],
)
def test_get_end_selection_y(selection, start_y, start_x, end_y, end_x, expected):
    selection.start_selection_y = start_y
    selection.start_selection_x = start_x
    selection.end_selection_y = end_y
    selection.end_selection_x = end_x
    assert selection.get_end_selection_y() == expected


@pytest.mark.parametrize(
    "start_y, start_x, end_y, end_x, expected",
    [
        (5, 2, 2, 3, 2),  # End selection to the right of start selection
        (2, 3, 5, 6, 6),  # End selection to the left of start selection
    ],
)
def test_get_end_selection_x(selection, start_y, start_x, end_y, end_x, expected):
    selection.start_selection_y = start_y
    selection.start_selection_x = start_x
    selection.end_selection_y = end_y
    selection.end_selection_x = end_x
    assert selection.get_end_selection_x() == expected


def test_left_with_empty_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 0
    text = ["abc", "def"]

    selection.container_x.is_empty.return_value = True
    selection.container_y.is_empty.return_value = True
    selection.left(stdscr, cursor_x, cursor_y, text)

    stdscr.addch.assert_called_once_with(
        cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE
    )
    assert selection.clipboard == ["b"]


def test_left_with_right_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 0
    text = ["abc", "def"]
    clipboard = ["a"]

    selection.container_x.is_empty.return_value = False
    selection.container_y.is_empty.return_value = True
    selection.container_x.get_last.return_value = "Right"
    with patch.object(selection, "clipboard", clipboard):
        selection.left(stdscr, cursor_x, cursor_y, text)

    stdscr.addch.assert_called_once_with(cursor_y, cursor_x, text[cursor_y][cursor_x])
    assert clipboard == [""]


def test_left_with_left_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 0
    text = ["abc", "def"]
    clipboard = ["b"]

    selection.container_x.is_empty.return_value = False
    selection.container_y.is_empty.return_value = True
    selection.container_x.get_last.return_value = "Left"
    with patch.object(selection, "clipboard", clipboard):
        selection.left(stdscr, cursor_x - 1, cursor_y, text)

    stdscr.addch.assert_called_once_with(
        cursor_y, cursor_x - 1, text[cursor_y][cursor_x - 1], curses.A_REVERSE
    )
    assert clipboard == ["ab"]


def test_left_with_up_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 0
    text = ["abc", "def"]
    clipboard = ["bc", "d"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Up"
    with patch.object(selection, "clipboard", clipboard):
        selection.left(stdscr, cursor_x - 1, cursor_y, text)

    stdscr.addch.assert_called_once_with(
        cursor_y, cursor_x - 1, text[cursor_y][cursor_x - 1], curses.A_REVERSE
    )
    assert clipboard == ["abc", "d"]


def test_left_with_down_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 1
    text = ["abc", "def"]
    clipboard = ["bc", "d"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Down"
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "clipboard_y", 1
    ):
        selection.left(stdscr, cursor_x, cursor_y, text)

    stdscr.addch.assert_called_once_with(cursor_y, cursor_x, text[cursor_y][cursor_x])
    assert clipboard == ["bc", ""]


def test_right_with_empty_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 0, 0
    text = ["abc", "def"]

    selection.container_x.is_empty.return_value = True
    selection.container_y.is_empty.return_value = True
    selection.right(stdscr, cursor_x, cursor_y, text)

    stdscr.addch.assert_called_once_with(
        cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE
    )
    assert selection.clipboard == ["a"]


def test_right_with_right_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 0
    text = ["abc", "def"]
    clipboard = ["a"]

    selection.container_x.is_empty.return_value = False
    selection.container_y.is_empty.return_value = True
    selection.container_x.get_last.return_value = "Right"
    with patch.object(selection, "clipboard", clipboard):
        selection.right(stdscr, cursor_x, cursor_y, text)

    stdscr.addch.assert_called_once_with(
        cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE
    )
    assert clipboard == ["ab"]


def test_right_with_left_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 0, 0
    text = ["abc", "def"]
    clipboard = ["a"]

    selection.container_x.is_empty.return_value = False
    selection.container_y.is_empty.return_value = True
    selection.container_x.get_last.return_value = "Left"
    with patch.object(selection, "clipboard", clipboard):
        selection.right(stdscr, cursor_x, cursor_y, text)

    stdscr.addch.assert_called_once_with(cursor_y, cursor_x, text[cursor_y][cursor_x])
    assert clipboard == [""]


def test_right_with_up_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 0, 0
    text = ["abc", "def"]
    clipboard = ["abc"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Up"
    with patch.object(selection, "clipboard", clipboard):
        selection.right(stdscr, cursor_x, cursor_y, text)

    stdscr.addch.assert_called_once_with(cursor_y, cursor_x, text[cursor_y][cursor_x])
    assert clipboard == ["bc"]


def test_right_with_down_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 1
    text = ["abc", "def"]
    clipboard = ["bc", "d"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Down"
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "clipboard_y", 1
    ):
        selection.right(stdscr, cursor_x, cursor_y, text)

    stdscr.addch.assert_called_once_with(
        cursor_y, cursor_x, text[cursor_y][cursor_x], curses.A_REVERSE
    )
    assert clipboard == ["bc", "de"]


def test_up_with_empty_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 0, 1
    text = ["abc", "def"]
    clipboard = []

    selection.container_x.is_empty.return_value = True
    selection.container_y.is_empty.return_value = True
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "start_selection_y", 1
    ), patch.object(selection, "start_selection_x", 0):
        selection.up(stdscr, cursor_x, cursor_y - 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(
                cursor_y - 1,
                cursor_x,
                text[cursor_y - 1][cursor_x:],
                curses.A_REVERSE,
            ),
            mock.call(1, 0, text[1][:0], curses.A_REVERSE),
        ]
    )
    assert clipboard == ["abc", ""]


def test_up_with_not_empty_x_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 0, 1
    text = ["abc", "def"]
    clipboard = ["de"]

    selection.container_x.is_empty.return_value = False
    selection.container_y.is_empty.return_value = True
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "start_selection_y", 1
    ), patch.object(selection, "start_selection_x", 2):
        selection.up(stdscr, cursor_x, cursor_y - 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(
                cursor_y - 1,
                cursor_x,
                text[cursor_y - 1][cursor_x:],
                curses.A_REVERSE,
            ),
            mock.call(1, 0, text[1][:2], curses.A_REVERSE),
        ]
    )
    assert clipboard == ["abc", "de"]


def test_up_with_up_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 3, 1
    text = ["abc", "def"]
    clipboard = [""]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Up"
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "end_selection_y", 1
    ), patch.object(selection, "end_selection_x", 3):
        selection.up(stdscr, cursor_x, cursor_y - 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(
                cursor_y - 1,
                cursor_x,
                text[cursor_y - 1][cursor_x:],
                curses.A_REVERSE,
            ),
            mock.call(1, 0, text[1][:3], curses.A_REVERSE),
        ]
    )
    assert clipboard == ["", "def"]


def test_up_with_down_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 0, 1
    text = ["abc", "def"]
    clipboard = ["abc", ""]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Down"
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "end_selection_y", 0
    ), patch.object(selection, "end_selection_x", 3), patch.object(
        selection, "start_selection_x", 0
    ):
        selection.up(stdscr, cursor_x, cursor_y - 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(0, 0, text[0]),
            mock.call(cursor_y - 1, cursor_x, text[cursor_y - 1][cursor_x:]),
        ]
    )
    assert clipboard == [""]


def test_up_with_down_container_on_middle(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 2, 1
    text = ["abc", "def"]
    clipboard = ["abc", "de"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Down"
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "end_selection_y", 1
    ), patch.object(selection, "end_selection_x", 2), patch.object(
        selection, "start_selection_x", 0
    ):
        selection.up(stdscr, cursor_x, cursor_y - 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(1, 0, text[1]),
            mock.call(cursor_y - 1, cursor_x, text[cursor_y - 1][cursor_x:]),
        ]
    )
    assert clipboard == ["ab"]


def test_up_with_down_container_on_end(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 3, 1
    text = ["abc", "def"]
    clipboard = ["", "def"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Down"
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "end_selection_y", 1
    ), patch.object(selection, "end_selection_x", 3), patch.object(
        selection, "start_selection_x", 3
    ):
        selection.up(stdscr, cursor_x, cursor_y - 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(1, 0, text[1]),
            mock.call(cursor_y - 1, cursor_x, text[cursor_y - 1][cursor_x:]),
        ]
    )
    assert clipboard == [""]


def test_down_with_empty_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 0
    text = ["abc", "def"]
    clipboard = []
    cursor_y += 1

    selection.container_x.is_empty.return_value = True
    selection.container_y.is_empty.return_value = True
    with (
        patch.object(selection, "clipboard", clipboard),
        patch.object(selection, "start_selection_y", 0),
        patch.object(selection, "start_selection_x", 1),
    ):
        selection.down(stdscr, cursor_x, cursor_y, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(0, 1, text[0][1:], curses.A_REVERSE),
            mock.call(
                cursor_y,
                0,
                text[cursor_y][:cursor_x],
                curses.A_REVERSE,
            ),
        ]
    )
    assert clipboard == ["bc", "d"]


def test_down_with_not_empty_x_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 0
    cursor_y += 1
    text = ["abc", "def"]
    clipboard = ["a"]

    selection.container_x.is_empty.return_value = False
    selection.container_y.is_empty.return_value = True
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "start_selection_y", 0
    ), patch.object(selection, "start_selection_x", 0):
        selection.down(stdscr, cursor_x, cursor_y, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(0, 0, text[0][0:], curses.A_REVERSE),
            mock.call(
                cursor_y,
                0,
                text[cursor_y][:cursor_x],
                curses.A_REVERSE,
            ),
        ]
    )
    assert clipboard == ["abc", "d"]


def test_down_with_up_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 1, 0
    text = ["abc", "def"]
    clipboard = ["bc", "d"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Up"
    with (
        patch.object(selection, "clipboard", clipboard),
        patch.object(selection, "end_selection_y", 0),
        patch.object(selection, "end_selection_x", 1),
        patch.object(selection, "start_selection_y", 1),
        patch.object(selection, "start_selection_x", 1),
    ):
        selection.down(stdscr, cursor_x, cursor_y + 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(0, 0, text[0]),
            mock.call(cursor_y + 1, 0, text[cursor_y + 1][:cursor_x]),
        ]
    )
    assert clipboard == [""]


def test_down_with_down_container(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 3, 0
    text = ["abc", "def"]
    clipboard = ["abc"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Down"
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "end_selection_y", 0
    ), patch.object(selection, "end_selection_x", 3), patch.object(
        selection, "start_selection_x", 0
    ):
        selection.down(stdscr, cursor_x, cursor_y + 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(0, 3, text[0][3:], curses.A_REVERSE),
            mock.call(cursor_y + 1, 0, text[cursor_y + 1][:cursor_x], curses.A_REVERSE),
        ]
    )
    assert clipboard == ["abc", "def"]


def test_down_with_up_container_on_middle(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 2, 0
    text = ["abc", "def"]
    clipboard = ["c", "de"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Up"
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "end_selection_y", 0
    ), patch.object(selection, "end_selection_x", 2), patch.object(
        selection, "start_selection_x", 2
    ):
        selection.down(stdscr, cursor_x, cursor_y + 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(0, 0, text[0]),
            mock.call(cursor_y + 1, 0, text[cursor_y + 1][:cursor_x]),
        ]
    )
    assert clipboard == [""]


def test_down_with_up_container_on_end(selection):
    stdscr = Mock()
    cursor_x, cursor_y = 3, 0
    text = ["abc", "def"]
    clipboard = ["", "def"]

    selection.container_y.is_empty.return_value = False
    selection.container_y.get_last.return_value = "Up"
    with patch.object(selection, "clipboard", clipboard), patch.object(
        selection, "end_selection_y", 0
    ), patch.object(selection, "end_selection_x", 3), patch.object(
        selection, "start_selection_x", 3
    ):
        selection.down(stdscr, cursor_x, cursor_y + 1, text)

    stdscr.addstr.assert_has_calls(
        [
            mock.call(0, 0, text[0]),
            mock.call(cursor_y + 1, 0, text[cursor_y + 1][:cursor_x]),
        ]
    )
    assert clipboard == [""]


def test_validate_horizontal_left(selection):
    cursor_x, cursor_y = 0, 1
    text = ["abc", "def"]

    new_x, new_y = selection.validate_horizontal(True, cursor_x, cursor_y, text)
    assert new_x == 2
    assert new_y == 0


def test_validate_horizontal_right(selection):
    cursor_x, cursor_y = 3, 0
    text = ["abc", "def"]

    new_x, new_y = selection.validate_horizontal(False, cursor_x, cursor_y, text)

    assert new_x == 0
    assert new_y == 1


def test_validate_vertical_up(selection):
    cursor_x, cursor_y = 1, 1
    text = ["abc", "def"]

    new_x, new_y = selection.validate_vertical(True, cursor_x, cursor_y, text)
    assert new_x == 1
    assert new_y == 0


def test_validate_vertical_down(selection):
    cursor_x, cursor_y = 1, 0
    text = ["abc", "def"]

    new_x, new_y = selection.validate_vertical(False, cursor_x, cursor_y, text)
    assert new_x == 1
    assert new_y == 1


@pytest.fixture
def container():
    return Container()


def test_add_item(container):
    container.add("item1")
    assert container.container == ["item1"]


def test_pop_last(container):
    container.add("item1")
    container.add("item2")
    container.pop_last()
    assert container.container == ["item1"]


def test_get_last(container):
    container.add("item1")
    container.add("item2")
    assert container.get_last() == "item2"


def test_is_empty(container):
    assert container.is_empty()
    container.add("item1")
    assert not container.is_empty()


def test_clear(container):
    container.add("item1")
    container.add("item2")
    container.clear()
    assert container.container == []


if __name__ == "__main__":
    pytest.main()
