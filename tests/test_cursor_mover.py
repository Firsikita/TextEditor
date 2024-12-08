import pytest
from Editor.cursor_mover import CursorMover  # Assuming the class is in a file named cursor_mover.py

@pytest.fixture
def cursor_mover():
    """Fixture to initialize the CursorMover instance."""
    return CursorMover()

@pytest.mark.parametrize(
    "cursor_x, cursor_y, text, expected",
    [
        (5, 0, ["hello world"], (4, 0)),  # Move left within the same line
        (0, 1, ["hello", "world"], (5, 0)),  # Move left to the end of the previous line
        (0, 0, ["hello", "world"], (0, 0)),  # Move left at the start of the first line
        (0, 1, ["", "world"], (0, 0)),  # Move left to an empty previous line
    ],
)
def test_left(cursor_mover, cursor_x, cursor_y, text, expected):
    result = cursor_mover.left(cursor_x, cursor_y, text)
    assert result == expected


@pytest.mark.parametrize(
    "cursor_x, cursor_y, text, expected",
    [
        (4, 0, ["hello world"], (5, 0)),  # Move right within the same line
        (11, 0, ["hello world"], (11, 0)),  # Move right at the end of a line
        (5, 0, ["hello", "world"], (0, 1)),  # Move right to the start of the next line
        (0, 0, ["", "world"], (0, 1)),  # Move right from an empty line
    ],
)
def test_right(cursor_mover, cursor_x, cursor_y, text, expected):
    result = cursor_mover.right(cursor_x, cursor_y, text)
    assert result == expected


@pytest.mark.parametrize(
    "cursor_x, cursor_y, text, expected",
    [
        (3, 1, ["hello", "world"], (3, 0)),  # Move up within bounds
        (6, 1, ["hello", "world"], (5, 0)),  # Move up, cursor_x adjusts to the previous line length
        (3, 0, ["hello", "world"], (3, 0)),  # Move up at the first line
        (0, 2, ["hello", "", "world"], (0, 1)),  # Move up to an empty line
    ],
)
def test_up(cursor_mover, cursor_x, cursor_y, text, expected):
    result = cursor_mover.up(cursor_x, cursor_y, text)
    assert result == expected


@pytest.mark.parametrize(
    "cursor_x, cursor_y, text, expected",
    [
        (3, 0, ["hello", "world"], (3, 1)),  # Move down within bounds
        (6, 0, ["hello", "world"], (5, 1)),  # Move down, cursor_x adjusts to the next line length
        (3, 1, ["hello", "world"], (3, 1)),  # Move down at the last line
        (0, 1, ["hello", "", "world"], (0, 2)),  # Move down from an empty line
    ],
)
def test_down(cursor_mover, cursor_x, cursor_y, text, expected):
    result = cursor_mover.down(cursor_x, cursor_y, text)
    assert result == expected

if __name__ == "__main__":
    pytest.main()
