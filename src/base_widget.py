from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QRegion, QColor
from PySide6.QtWidgets import QWidget

from utils.config_manager import ConfigManager


class BaseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.window_config = self.config_manager.get_window_config()
        self._setup_window()

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

    def _get_border_radius(self) -> int:
        return self.window_config.get("border_radius", 5)

    def _get_background_color(self) -> str:
        return self.window_config.get("background_color", "rgba(225, 240, 249, 200)")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        radius = self._get_border_radius()
        rect = self.rect()
        path.addRoundedRect(rect, radius, radius)

        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

        bg_color = self._get_background_color()
        if bg_color.startswith("rgba"):
            import re

            rgba_match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", bg_color)
            if rgba_match:
                r, g, b, a = map(int, rgba_match.groups())
                painter.fillPath(path, QColor(r, g, b, a))
            else:
                painter.fillPath(path, QColor(225, 240, 249, 200))
        else:
            painter.fillPath(path, QColor(225, 240, 249, 200))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_mouse_press(event)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_mouse_double_click(event)
        super().mouseDoubleClickEvent(event)

    def _on_mouse_press(self, event):
        pass

    def _on_mouse_double_click(self, event):
        pass
