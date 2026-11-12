"""App-wide settings. EDIT STUDENT_NAME and ROLL_NO before taking screenshots."""
import sys
from pathlib import Path

STUDENT_NAME = "Sangay Rinchen"
ROLL_NO = "08230185"

APP_NAME = "Student Record Manager"
WINDOW_TITLE = f"{APP_NAME} - {STUDENT_NAME} ({ROLL_NO})"

# Paths are relative to the project folder, never hard-coded absolute paths.
IS_FROZEN = getattr(sys, "frozen", False)          # True when running as a PyInstaller .exe
EXE_PATH = Path(sys.executable).resolve()
if IS_FROZEN:
    PROJECT_DIR = EXE_PATH.parent
else:
    PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "students.json"

SUBJECTS = ["Programming", "Mathematics", "Databases", "English"]
PROGRAMMES = ["BSc IT", "BSc CS", "BE Software Eng.", "BBA", "BA English"]
PASS_MARK = 40
