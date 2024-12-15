import json
import os
from unittest.mock import patch, mock_open, MagicMock
import pytest
from Server.file_manager import FileManager


@pytest.fixture
def file_manager():
    return FileManager(base_dir=".\Server\server_files")


def teardown_test_dir():
    """Clean up test directory."""
    if os.path.exists("./test_dir"):
        for root, dirs, files in os.walk("./test_dir", topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir("./test_dir")


@patch("os.listdir", return_value=["file1.txt", "file2.txt"])
@patch.object(FileManager, "load_user_information", return_value={})
def test_get_files(mock_load_user_info, mock_listdir, file_manager):
    files = file_manager.get_files("user1")
    assert files == ["file1.txt", "file2.txt"]


@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="line1\nline2\n")
def test_open_file_success(mock_open, mock_exists, file_manager):
    success, content = file_manager.open_file("user1", "file1.txt")
    assert success
    assert content == ["line1", "line2"]


@patch("os.path.exists", return_value=False)
def test_open_file_not_exists(mock_exists, file_manager):
    success, content = file_manager.open_file("user1", "file1.txt")
    assert not success
    assert content is None


@patch("os.makedirs")
@patch("os.path.exists", return_value=False)
@patch("builtins.open", new_callable=mock_open)
def test_create_file(mock_open, mock_exists, mock_makedirs, file_manager):
    success, error = file_manager.create_file("user1", "new_file.txt")
    assert success
    assert error is None


@patch("os.remove")
@patch("os.path.exists", return_value=True)
def test_delete_file_success(mock_exists, mock_remove, file_manager):
    success, error = file_manager.delete_file("user1", "file1.txt")
    assert success
    assert error is None


@patch("os.path.exists", return_value=False)
def test_delete_file_not_exists(mock_exists, file_manager):
    success, error = file_manager.delete_file("user1", "file1.txt")
    assert not success
    assert error == "File does not exist"


@patch("builtins.open", new_callable=mock_open)
def test_save_file(mock_open, file_manager):
    content = ["line1", "line2"]
    success, error = file_manager.save_file("user1", "file1.txt", content)
    assert success
    assert error is None
    expected_path = os.path.join(
        ".\Server", "server_files", "user1's_files", "file1.txt"
    )
    mock_open.assert_called_once_with(expected_path, "w")


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps({"key": "value"}),
)
@patch("os.path.exists", return_value=True)
def test_load_user_information(mock_exists, mock_open, file_manager):
    data = file_manager.load_user_information()
    assert data == {"key": "value"}


@patch("os.remove")
def test_delete_history(mock_remove, file_manager):
    file_manager.delete_history("history_file.txt")
    mock_remove.assert_called_once_with(
        "./Server/files_change_history/history_file.json"
    )


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps({"history": "data"}),
)
@patch("os.path.exists", return_value=True)
def test_load_history(mock_exists, mock_open, file_manager):
    history = file_manager.load_history("history_file.txt")
    assert history == {"history": "data"}


def test_validate_access_granted(file_manager):
    user_id = "user1"
    host_id = "host1"
    filename = "test.txt"

    user_info = {
        "user1": {
            "host_access": {
                "host1": {"files": ["test.txt"]},
            }
        }
    }

    with patch.object(file_manager, "load_user_information", return_value=user_info):
        success, filepath, msg = file_manager.validate_access(
            user_id, host_id, filename
        )

    assert success is True
    assert filepath == os.path.join(
        file_manager.base_dir, f"{host_id}'s_files", filename
    )
    assert msg is None


def test_validate_access_denied(file_manager):
    user_id = "user1"
    host_id = "host1"
    filename = "test.txt"

    user_info = {
        "user1": {
            "host_access": {
                "host2": {"files": ["other.txt"]},
            }
        }
    }

    with patch.object(file_manager, "load_user_information", return_value=user_info):
        success, filepath, msg = file_manager.validate_access(
            user_id, host_id, filename
        )

    assert success is False
    assert filepath is None
    assert msg == f"You do not have access to the file '{filename}' of host {host_id}."


def test_grant_access_success(file_manager):
    user_id = "user1"
    host_id = "host1"
    filename = "test.txt"

    clients_base = [{"User ID": user_id}, {"User ID": host_id}]
    user_info = {}
    host_files = ["test.txt"]

    with patch.object(
        file_manager, "load_json", return_value=clients_base
    ), patch.object(
        file_manager, "load_user_information", return_value=user_info
    ), patch.object(
        file_manager, "get_files", return_value=host_files
    ), patch(
        "builtins.open", mock_open()
    ):
        result = file_manager.grant_access(user_id, host_id, filename)

    assert result == f'Access granted to file "{filename}" for user: {user_id}'


def test_grant_access_file_not_found(file_manager):
    user_id = "user1"
    host_id = "host1"
    filename = "test.txt"

    clients_base = [{"User ID": user_id}, {"User ID": host_id}]
    user_info = {}
    host_files = ["other.txt"]

    with patch.object(
        file_manager, "load_json", return_value=clients_base
    ), patch.object(
        file_manager, "load_user_information", return_value=user_info
    ), patch.object(
        file_manager, "get_files", return_value=host_files
    ):
        result = file_manager.grant_access(user_id, host_id, filename)

    assert result == f"File {filename} does not exist for these hosts: {host_id}"


@pytest.fixture
def mock_instance(file_manager):
    file_manager.load_user_information = MagicMock()
    file_manager.save_user_information = MagicMock()
    return file_manager


def test_remove_access_success(mock_instance):
    mock_instance.load_user_information.return_value = {
        "1": {"host_access": {"2": {"files": ["file1.txt", "file2.txt"]}}}
    }
    result = mock_instance.remove_access("1", "2", "file1.txt")

    expected_user_info = {"1": {"host_access": {"2": {"files": ["file2.txt"]}}}}
    mock_instance.save_user_information.assert_called_once_with(expected_user_info)
    assert result == 'Access to file "file1.txt" for user 1 from host 2 removed.'


def test_remove_access_user_not_found(mock_instance):
    mock_instance.load_user_information.return_value = {}

    result = mock_instance.remove_access("1", "2", "file1.txt")

    assert result == "User 1 does not have any access records."
    mock_instance.save_user_information.assert_not_called()


def test_remove_access_host_not_found(mock_instance):
    mock_instance.load_user_information.return_value = {"1": {"host_access": {}}}

    result = mock_instance.remove_access("1", "2", "file1.txt")

    assert result == "User 1 does not have access to any files from host 2."
    mock_instance.save_user_information.assert_not_called()


def test_remove_access_file_not_found(mock_instance):
    # Mock user information
    mock_instance.load_user_information.return_value = {
        "1": {"host_access": {"2": {"files": ["file2.txt"]}}}
    }

    result = mock_instance.remove_access("1", "2", "file1.txt")

    assert result == 'User 1 does not have access to file "file1.txt" from host 2.'
    mock_instance.save_user_information.assert_not_called()


def test_remove_access_remove_host_after_last_file(mock_instance):
    mock_instance.load_user_information.return_value = {
        "1": {"host_access": {"2": {"files": ["file1.txt"]}}}
    }

    result = mock_instance.remove_access("1", "2", "file1.txt")

    expected_user_info = {"1": {"host_access": {}}}
    mock_instance.save_user_information.assert_called_once_with(expected_user_info)
    assert result == 'Access to file "file1.txt" for user 1 from host 2 removed.'
