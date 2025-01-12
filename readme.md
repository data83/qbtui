# qBittorrent TUI

qBittorrent TUI is a terminal-based application written in Python that provides a user interface for interacting with the qBittorrent Web API. It allows you to perform operations such as removing trackers from multiple torrents, all from the command line.

This program was created with the assistance of AI. **Use at your own risk.**

---

## Features

- **Terminal-based User Interface**: Uses Python's `curses` library for a console-based interactive UI.
- **Login to qBittorrent Web API**: Authenticate using a username and password.
- **Remove Trackers**: View and select trackers to remove from multiple torrents.
- **Add Trackers**: View and select trackers to add to multiple torrents. 🆕🆕🆕
- **Scrollable Lists**: Navigate through large lists of trackers using keyboard controls.
- **Progress Bars**: Visual progress updates for tracker-related operations.

---

## Prerequisites

To run the program, ensure the following:

1. Python 3.8 or later is installed on your system.
2. The following Python libraries are installed:
   - `requests`
   - `curses`
3. A working qBittorrent Web API instance is available (e.g., running on `http://localhost:8080`).

Install the required libraries with:
```bash
pip install requests
```

---

## How to Run

1. Clone or download the program's source code.
2. Run the script from the terminal:
```bash
python your_program.py
```

---

## Using PyInstaller to Create an Executable

To package this program into a standalone `.exe` file, follow these steps:

1. **Install PyInstaller**:
```bash
pip install pyinstaller
```

2. **Generate the Executable**:
   Run the following command in the directory containing your script:
```bash
pyinstaller --onefile --console your_program.py
```
   - `--onefile`: Packages everything into a single `.exe` file.
   - `--console`: Ensures the program runs in the console.

3. **Locate the Executable**:
   The generated `.exe` file will be located in the `dist` folder.

4. **Test the Executable**:
   Run the executable to ensure it works as expected:
```bash
./dist/your_program.exe
```

---

## How to Use the Program

1. **Login**:
   - Enter the qBittorrent Web API URL (e.g., `http://localhost:8080`).
   - Provide your username and password.

2. **Main Menu**:
   - **Option 1**: Remove a tracker.
   - **Option 2**: Add a tracker.
   - **Option 3**: Exit the program.

3. **Remove Tracker**:
   - The program aggregates trackers from all torrents.
   - Use the scrollable list to navigate through available trackers.
   - Select a tracker to remove using the arrow keys and press `Enter`.
   - Confirm the removal when prompted.

4. **Add Tracker**
   - The program aggregates trackers from all torrents.
   - Use the scrollable list to navigate to choose an existing tracker you want to add a mirror to.
   - Type in the URL of the mirror you want to add
   - Confirm the the new tracker is being added to the chosen existing tracker
---

## Disclaimer

This program was created with the assistance of AI. **Use at your own risk.** The author and AI bear no responsibility for any issues or damages resulting from its use.

