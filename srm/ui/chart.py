"""A small bar-chart widget drawn with QPainter (no extra chart library needed)."""
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget

INK, MUTED, BORDER, ACCENT = "#1f2a30", "#56626b", "#cfc9bd", "#e0a82e"


class BarChart(QWidget):
    """Draws one bar per (label, value) pair on a 0-100 scale."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict[str, float] = {}
        self.setMinimumHeight(220)

    def set_data(self, data: dict[str, float]) -> None:
        self._data = data
        self.update()                       # schedule a repaint -> paintEvent

    def paintEvent(self, event):            # called by Qt's event loop
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        left, bottom, top = 40, 28, 12
        plot_h = h - bottom - top
        p.setFont(QFont(self.font().family(), 9))
        for v in (0, 50, 100):              # gridlines + y labels
            y = top + plot_h * (1 - v / 100)
            p.setPen(QColor(BORDER)); p.drawLine(left, int(y), w - 8, int(y))
            p.setPen(QColor(MUTED)); p.drawText(QRectF(0, y - 8, left - 6, 16),
                                                Qt.AlignmentFlag.AlignRight, str(v))
        if not self._data:
            return
        slot = (w - left - 8) / len(self._data)
        bar_w = min(56, slot * 0.6)
        for i, (label, value) in enumerate(self._data.items()):
            x = left + i * slot + (slot - bar_w) / 2
            bar_h = plot_h * value / 100
            p.fillRect(QRectF(x, top + plot_h - bar_h, bar_w, bar_h), QColor(ACCENT))
            p.setPen(QColor(INK))
            p.drawText(QRectF(x - 20, top + plot_h - bar_h - 18, bar_w + 40, 16),
                       Qt.AlignmentFlag.AlignCenter, f"{value:.1f}")
            p.drawText(QRectF(left + i * slot, h - bottom + 6, slot, 18),
                       Qt.AlignmentFlag.AlignCenter, label)
