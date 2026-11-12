@echo off
title Student Record Manager - making screenshots
cd /d "%~dp0"
echo.
echo  ============================================================
echo   This takes all report screenshots and builds the .exe.
echo   It needs internet the first time (to install PyQt6).
echo   Please do NOT touch the mouse or keyboard until it says DONE.
echo  ============================================================
echo.

where python >nul 2>nul || goto :nopython

echo [1/5] Setting up Python (first time takes a few minutes)...
if not exist .venv\Scripts\python.exe (
    python -m venv .venv || goto :fail
)
call .venv\Scripts\activate.bat || goto :fail
python -m pip install --upgrade pip >nul 2>nul
pip install -r requirements.txt || goto :fail

echo.
echo [2/5] Running the 15 GUI tests and taking the app screenshots...
python tools\gui_tests_and_screenshots.py || goto :fail

echo.
echo [3/5] Building StudentRecordManager.exe (1-2 minutes)...
pyinstaller --noconfirm --onefile --windowed --name StudentRecordManager --add-data "srm/ui/theme.qss;srm/ui" --add-data "srm/ui/arrow-down.svg;srm/ui" --add-data "srm/ui/arrow-up.svg;srm/ui" main.py || goto :fail
xcopy data dist\data\ /E /I /Y >nul

echo.
echo [4/5] Opening the .exe to take Figure 13 (it closes by itself)...
start "" /wait "dist\StudentRecordManager.exe" --screenshot "%cd%\report\img\09_packaged_exe.png"

echo.
echo [5/5] Packing the screenshots into one zip file...
if exist screenshots_for_report.zip del screenshots_for_report.zip
powershell -NoProfile -Command "Compress-Archive -Path 'report\img\*' -DestinationPath 'screenshots_for_report.zip' -Force" || goto :fail

echo.
echo  ============================================================
echo   DONE!
echo   Upload this file to Claude:
echo   %cd%\screenshots_for_report.zip
echo  ============================================================
explorer /select,"%cd%\screenshots_for_report.zip"
pause
exit /b 0

:nopython
echo.
echo  Python is not installed (or not on PATH).
echo  1. Download Python 3.12 from https://www.python.org/downloads/
echo  2. During setup, TICK the box "Add python.exe to PATH".
echo  3. Then double-click this file again.
pause
exit /b 1

:fail
echo.
echo  Something went wrong. Take a photo or screenshot of this window
echo  and send it to Claude.
pause
exit /b 1
