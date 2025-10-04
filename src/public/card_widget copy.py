import re
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QRegion, QColor

class CardWidget(QWidget):
    def __init__(
        self,
        bg_color="rgba(225, 240, 249, 200)",
        border_radius=5,
        is_fixed_size=True,
        width=200,
        height=150,
        parent=None,
    ):
        super().__init__(parent)
        
        self.bg_color = bg_color
        self.border_radius = border_radius
        self.is_fixed_size = is_fixed_size
        self.width = width
        self.height = height
        
        # 解析颜色
        self._bg_qcolor = self._parse_color(bg_color)
        
        self.__setup__()
        
    def __setup__(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        if self.is_fixed_size:
            self.setFixedSize(self.width, self.height)
        
        # 在初始化时设置一次蒙版，而不是在paintEvent中
        self._update_mask()
    
    def _parse_color(self, color_str):
        """解析颜色字符串"""
        if color_str.startswith("rgba"):
            rgba_match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", color_str)
            if rgba_match:
                r, g, b, a = map(int, rgba_match.groups())
                # 验证颜色值范围
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                a = max(0, min(255, a))
                return QColor(r, g, b, a)
        
        # 默认颜色
        return QColor(225, 240, 249, 200)
    
    def _update_mask(self):
        """更新窗口蒙版"""
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, self.border_radius, self.border_radius)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
    
    def resizeEvent(self, event):
        """重写resize事件，更新蒙版"""
        super().resizeEvent(event)
        self._update_mask()
    
    def paintEvent(self, event):
        """重绘窗口"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, self.border_radius, self.border_radius)

        painter.fillPath(path, self._bg_qcolor)