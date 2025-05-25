# Network Speed Monitor

A lightweight Python tool that monitors your network upload and download speeds in real-time using `psutil` and `Tkinter`.  
It can be packaged into a standalone Windows executable with PyInstaller for easy distribution.

---

## Features

- Real-time upload and download speed display (in MB/s or Mbps)  
- Total data usage tracking with persistent storage  
- Minimal, always-on-top GUI with drag-and-drop positioning  
- Context menu with options to toggle display, units, reset usage data, and exit  
- Automatic saving and loading of total usage between sessions

---

## Requirements

- Python 3.x  
- [psutil](https://pypi.org/project/psutil/) library  
- `tkinter` (usually included with Python standard library)

---

## Installation

Install the required Python package via pip:

```bash
pip install psutil
````

---

## Usage

Run the script directly:

```bash
python main.py
```

The GUI will appear showing current upload and download speeds.
Right-click on the window to access the menu for options like toggling total usage display or changing speed units.

---

## Building the Executable

To create a standalone Windows executable using PyInstaller, use the command in `pyinstaller_command.txt`.
Typically, it looks like this:

```bash
pyinstaller --onefile --noconsole --name MoniNet --icon moninet.ico --version-file version.txt main.py
```

This generates an `MoniNet.exe` file inside the `dist` folder.

---

## Files in This Project

* `main.py` — main Python script with the network monitor
* `moninet.ico` — icon file for the executable
* `MoniNet.spec` — PyInstaller spec file generated during build
* `pyinstaller_command.txt` — command used for building the executable
* `version.txt` — version details of the executable
* `/build/` — PyInstaller build folder (should be excluded from GitHub)
* `/dist/` — folder containing the `.exe` (usually excluded from GitHub)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Author

Created by \`Concise Coder`
Feel free to contribute or report issues!

---

## Acknowledgments

* Uses the [`psutil`](https://github.com/giampaolo/psutil) library for network stats
* Uses Python's built-in `tkinter` for the GUI
* Inspired by simple desktop network monitors
