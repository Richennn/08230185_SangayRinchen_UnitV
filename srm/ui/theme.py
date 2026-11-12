"""Loads theme.qss and fills in the {UI_DIR} placeholder (so no absolute path is hard-coded)."""
from pathlib import Path

UI_DIR = Path(__file__).resolve().parent


def load_stylesheet() -> str:
    qss = (UI_DIR / "theme.qss").read_text(encoding="utf-8")
    return qss.replace("{UI_DIR}", UI_DIR.as_posix())
