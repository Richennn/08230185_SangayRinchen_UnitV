"""Entry point: python main.py

Optional:  python main.py --screenshot shot.png
           (also works on the packaged exe) saves a picture of the window,
           title bar included, then closes the app by itself.
"""
import argparse
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox

from srm import config
from srm.storage import StudentRepository
from srm.ui.main_window import MainWindow
from srm.ui.screenshot import grab_with_frame
from srm.ui.theme import load_stylesheet


def main() -> int:
    parser = argparse.ArgumentParser(description=config.APP_NAME)
    parser.add_argument("--screenshot", metavar="FILE.png",
                        help="save a screenshot of the main window once it is shown")
    args, qt_args = parser.parse_known_args()

    app = QApplication([sys.argv[0], *qt_args])
    app.setApplicationName(config.APP_NAME)
    app.setStyleSheet(load_stylesheet())          # Qt stylesheet = our design-system tokens

    repo = StudentRepository(config.DATA_FILE)
    repo.load()
    window = MainWindow(repo)
    window.show()
    if repo.load_warning:
        QMessageBox.warning(window, "Data file problem", repo.load_warning)

    if args.screenshot:
        def save_shot():
            grab_with_frame(window).save(args.screenshot)
            print(f"Screenshot saved to {args.screenshot}")
            QTimer.singleShot(300, app.quit)      # close by itself so scripts can carry on
        QTimer.singleShot(1500, save_shot)        # wait until the window is fully drawn

    return app.exec()                 # start the Qt event loop


if __name__ == "__main__":
    sys.exit(main())
