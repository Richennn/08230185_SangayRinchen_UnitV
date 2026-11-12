# Student Record Manager (Unit V - PyQt6)

A desktop app to add, edit, search and delete student records and marks, with a summary
tab (class average, pass rate, per-subject bar chart). Data is saved to `data/students.json`.

## Requirements
- Python **3.10 or newer** (tested on 3.12 and 3.13)
- Windows, macOS or Linux

## Install and run
```bash
# 1. create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 2. install pinned dependencies
pip install -r requirements.txt

# 3. run the app
python main.py
```

Before taking screenshots, open `srm/config.py` and set `STUDENT_NAME` and `ROLL_NO`.
They appear in the window title and the Help > About dialog.

## Run the tests
```bash
python -m unittest -v                       # 9 logic/data tests, no GUI needed
python tools/gui_tests_and_screenshots.py   # 15 GUI test cases + screenshots into report/img/
```
The GUI test script works on a temporary copy of `data/students.sample.json` and never touches your real data.

## Screenshots for the report (with title bars)
**Easiest way (Windows):** double-click `MAKE_SCREENSHOTS.bat`. It installs everything, runs the GUI tests,
takes every screenshot, builds the .exe, takes Figure 13 and packs the pictures into `screenshots_for_report.zip`.

`tools/gui_tests_and_screenshots.py` saves every main-window and dialog screenshot into `report/img/`,
title bar included, so the name and roll number in the window title are visible.
Run it on Windows, or on Linux with an X11 session (Wayland blocks screen capture, and the script then
falls back to a capture without the title bar). Keep the window uncovered while it runs.

Hello-world screenshots: run each program in `partA/`, click the button, then press **Alt + Print Screen**
(Windows) to copy just that window, and paste it into `partA/screenshots/`.

Packaged executable (Figure 13): after building with PyInstaller (below), run
```bash
dist\StudentRecordManager.exe --screenshot report\img\09_packaged_exe.png     # Windows
./dist/StudentRecordManager --screenshot report/img/09_packaged_exe.png         # Linux
```
In the packaged build the status bar shows the executable's file name and size, so this picture is
clearly the .exe and not `python main.py`.

## Reset the sample data
Copy `data/students.sample.json` over `data/students.json`.

## Part A hello-world programs
```bash
python partA/hello_pyqt.py
python partA/hello_kivy.py
python partA/hello_tkinter.py   # Tkinter ships with python.org installers; on Ubuntu: sudo apt install python3-tk
```

## Build a stand-alone executable (optional)
```bash
pyinstaller --noconfirm --onefile --windowed --name StudentRecordManager --add-data "srm/ui/theme.qss:srm/ui" --add-data "srm/ui/arrow-down.svg:srm/ui" --add-data "srm/ui/arrow-up.svg:srm/ui" main.py
```
On Windows, replace `:` with `;` inside each `--add-data` value. Put a `data/` folder next to the executable.

## Project layout
```
main.py                 entry point (QApplication + event loop)
srm/config.py           name/roll no, paths, subjects, programmes
srm/models.py           logic layer: Student, validation, grades   (no PyQt)
srm/storage.py          data layer: StudentRepository (JSON, CSV)   (no PyQt)
srm/ui/main_window.py   UI layer: widgets, layouts, signals/slots, dialogs
srm/ui/chart.py         QPainter bar chart
srm/ui/theme.qss        Qt stylesheet (design-system colours)
data/                   students.json (live) + students.sample.json
partA/                  hello-world programs + screenshots
tests/                  unit tests
tools/                  GUI test + screenshot script
report/                 report source, images and PDF
```
