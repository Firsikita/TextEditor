# Multi-user Text Editor
A collaborative, terminal-based text editor that supports real-time, multi-user editing using websockets. It is inspired by editors like Nano, but with the added ability to collaborate across multiple clients. The project integrates `curses` for the text UI.

# Features
- Real-time, multi-user text editing
- Terminal-based interface with `curses`
- Synchronizes content across multiple clients

## Requirements
- Python 3.8+
- `curses` library (`windows-curses` for Windows)
- `websockets` library
- `asyncio` library
- `pytest` for testing

## Install
1. Clone the repository
`git clone https://github.com/Firsikita/TextEditor`
`cd editordir`
2. `pip install -r requierments.txt`

## Usage
1. Run the server:
`python run_server.py`
2. Run the client:
`python run_client.py`


## Supported Editor commands:
* `ESC`: Save the file and exit the edit mode
* `Backspace`: Delete the char before the cursor
* `Arrow Keys`: Move the cursor around the document
* `Character keys`: Insert characters at the cursor position
* `Ctrl + E`: Start and end selection mode
* `Ctrl + U`: Copy selection
* `Ctrl + V`: Paste from clipboard


## Project Structure
```
├── Client/
│   └── client.py              # Client logic for handling user interaction and communication with the server
├── Server/
│   └── server.py              # Server logic
│   └── session_manager.py     # Logic for handling multiple clients and file synchronization
│   └── file_manager.py        # Managing operations with files
├── Shared/
│   └── protocol.py            # Protocol definitions for consistent message formats between client and server
├── Editor/
│   └── Editor.py              # Core text editor logic using curses for terminal interface
├── tests/
│   └── test_server.py         # Unit tests for the server
│   └── test_client.py         # Unit tests for the client
├── README.md
├── run_server.py              # Module to setup server
├── run_client.py              # Module to connect as a client
└── requirements.txt  
```