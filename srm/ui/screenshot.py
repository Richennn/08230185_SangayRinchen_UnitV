"""Save a screenshot of a top-level window *including* its title bar."""
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget


def grab_with_frame(widget: QWidget) -> QPixmap:
    """Capture the window as it appears on screen, title bar included.

    QWidget.grab() only paints the inside of the window, so the title bar
    (which the operating system draws) is missing. Here we copy the window's
    frame rectangle from the screen instead. Some Linux Wayland sessions do not
    allow screen capture; then we fall back to the inside-only grab.
    """
    window = widget.window()
    window.raise_()
    window.activateWindow()
    QApplication.processEvents()

    screen = window.screen()
    frame = window.frameGeometry()
    origin = screen.geometry().topLeft()           # grabWindow uses screen-relative coordinates
    pixmap = screen.grabWindow(0, frame.x() - origin.x(), frame.y() - origin.y(),
                               frame.width(), frame.height())
    if pixmap.isNull() or pixmap.width() < 10:
        pixmap = window.grab()
    return pixmap
