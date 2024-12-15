import pytest
from unittest.mock import AsyncMock, Mock, patch
import asyncio
from Editor.editor import Editor


@pytest.fixture
def editor():
    """Fixture to initialize the Editor instance."""
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    user_id = "test_user"
    return Editor(event_loop, user_id)


@pytest.mark.asyncio
@patch("Editor.editor.Protocol")
async def test_save_content_file(mock_protocol, editor):
    websocket = AsyncMock()
    content = ["Line1", "Line2"]
    filename = "test_file.txt"

    mock_protocol.create_message.return_value = "test_message"

    await editor.save_content_file(filename, content, websocket)

    websocket.send.assert_called_once_with("test_message")
    mock_protocol.create_message.assert_called_once_with(
        "SAVE_CONTENT", {"filename": filename, "content": "Line1Line2"}
    )


@pytest.mark.asyncio
@patch("Editor.editor.Protocol")
async def test_listen_for_update_insert_operation(mock_protocol, editor):
    websocket = AsyncMock()
    stdscr = Mock()
    current_content = ["Hello World"]
    cursor_y = 0
    cursor_x = 0

    message = {
        "data": {
            "operation": {
                "op_type": "insert",
                "start_pos": {"y": 0, "x": 6},
                "text": ["!"],
            }
        }
    }
    mock_protocol.parse_response.return_value = message

    websocket.recv = AsyncMock(side_effect=[message, asyncio.CancelledError()])

    await editor.listen_for_update(
        websocket, stdscr, current_content, cursor_y, cursor_x
    )

    assert current_content == ["Hello !World"]
    stdscr.clear.assert_called()
    stdscr.addstr.assert_called()
    stdscr.move.assert_called()


@patch("Editor.message_sender.MessageSender.send_edit_message", new_callable=AsyncMock)
@patch("Editor.editor.pyperclip.paste", return_value="copied text")
def test_insert_text(mock_paste, mock_send_edit_message, editor):
    websocket = Mock()
    current_content = ["Hello World"]
    cursor_y = 0
    cursor_x = 6
    filename = "test.txt"

    editor.insert_text(
        websocket,
        filename,
        current_content,
        cursor_y,
        cursor_x,
        editor.event_loop,
    )

    assert current_content == ["Hello copied textWorld"]

    mock_send_edit_message.assert_called_once_with(
        websocket,
        filename,
        ["copied text"],
        cursor_y,
        cursor_x,
        editor.event_loop,
        editor.user_id,
    )


def test_insert_enter(editor):
    current_content = ["Hello World"]
    cursor_y = 0
    cursor_x = 5

    editor.insert_enter(current_content, cursor_y, cursor_x)

    assert current_content == ["Hello", " World"]


def test_delete_piece(editor):
    current_content = ["Hello", "World"]
    start_y, start_x = 0, 2
    end_y, end_x = 1, 3

    editor.delete_piece(current_content, start_y, start_x, end_y, end_x)

    assert current_content == ["Held"]


@patch("Editor.editor.curses.wrapper")
@pytest.mark.asyncio
async def test_edit(mock_curses_wrapper, editor):
    content = ["Hello World"]
    filename = "test.txt"
    stop_event = Mock()
    websocket = Mock()

    await editor.edit(content, filename, stop_event, websocket)

    mock_curses_wrapper.assert_called_once()


@patch("Editor.editor.curses")
def test_display_text(mock_curses, editor):
    stdscr = Mock()
    current_content = ["Line1", "Line2"]
    cursor_y = 1
    cursor_x = 3

    editor.display_text(stdscr, current_content, cursor_y, cursor_x)

    stdscr.clear.assert_called_once()
    stdscr.addstr.assert_any_call(0, 0, "Line1")
    stdscr.addstr.assert_any_call(1, 0, "Line2")
    stdscr.move.assert_called_once_with(cursor_y, cursor_x)


@patch("Editor.editor.curses.curs_set")
@patch("Editor.editor.time.time", return_value=1234567890)
def test_curses_editor(mock_time, mock_curs_set, editor):
    stdscr = Mock()
    content = ["Hello"]
    filename = "test.txt"
    websocket = Mock()
    stop_event = Mock()

    stdscr.getch = Mock(
        side_effect=[
            ord("H"),
            ord("e"),
            ord("l"),
            ord("l"),
            ord("o"),
            10,
            27,
        ]
    )

    with patch.object(
        editor, "listen_for_update", return_value=AsyncMock()
    ) as mock_listen_for_update:
        with patch.object(editor, "display_text") as mock_display_text:
            with patch.object(
                editor.sender,
                "send_edit_message",
                new_callable=AsyncMock,
            ) as mock_send_edit_message:
                with patch.object(
                    editor.sender,
                    "send_new_line",
                    new_callable=AsyncMock,
                ) as mock_send_new_line:
                    with patch.object(
                        editor,
                        "save_content_file",
                        new_callable=AsyncMock,
                    ) as mock_save_content:
                        editor.curses_editor(
                            stdscr,
                            content,
                            filename,
                            websocket,
                            editor.event_loop,
                            stop_event,
                        )

                        mock_curs_set.assert_called_once_with(1)
                        mock_display_text.assert_called()
                        mock_send_edit_message.assert_called()
                        mock_send_new_line.assert_called_once()
                        mock_save_content.assert_called_once_with(
                            filename, content, websocket
                        )
                        stop_event.set.assert_called_once()
