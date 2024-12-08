import pytest
from Editor.cursor_mover import CursorMover

@pytest.fixture
def cursor_mover():
    return CursorMover()

@pytest.mark.parametrize(
    "cursor_x, cursor_y, text, expected",
    [
        (5, 0, ["hello world"], (4, 0)),
        (0, 1, ["hello", "world"], (5, 0)),
        (0, 0, ["hello", "world"], (0, 0)),
        (0, 1, ["", "world"], (0, 0)),
    ],
)
def test_left(cursor_mover, cursor_x, cursor_y, text, expected):
    result = cursor_mover.left(cursor_x, cursor_y, text)
    assert result == expected


@pytest.mark.parametrize(
    "cursor_x, cursor_y, text, expected",
    [
        (4, 0, ["hello world"], (5, 0)),
        (11, 0, ["hello world"], (11, 0)),
        (5, 0, ["hello", "world"], (0, 1)),
        (0, 0, ["", "world"], (0, 1)),
    ],
)
def test_right(cursor_mover, cursor_x, cursor_y, text, expected):
    result = cursor_mover.right(cursor_x, cursor_y, text)
    assert result == expected


@pytest.mark.parametrize(
    "cursor_x, cursor_y, text, expected",
    [
        (3, 1, ["hello", "world"], (3, 0)),
        (6, 1, ["hello", "world"], (5, 0)),
        (3, 0, ["hello", "world"], (3, 0)),
        (0, 2, ["hello", "", "world"], (0, 1)),
    ],
)
def test_up(cursor_mover, cursor_x, cursor_y, text, expected):
    result = cursor_mover.up(cursor_x, cursor_y, text)
    assert result == expected


@pytest.mark.parametrize(
    "cursor_x, cursor_y, text, expected",
    [
        (3, 0, ["hello", "world"], (3, 1)),
        (6, 0, ["hello", "world"], (5, 1)),
        (3, 1, ["hello", "world"], (3, 1)),
        (0, 1, ["hello", "", "world"], (0, 2)),
    ],
)
def test_down(cursor_mover, cursor_x, cursor_y, text, expected):
    result = cursor_mover.down(cursor_x, cursor_y, text)
    assert result == expected

if __name__ == "__main__":
    pytest.main()
