import re
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

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
        
        # 验证并标准化颜色
        self._validated_color = self._validate_color(bg_color)
        
        self.__setup__()
        
    def __setup__(self):
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建内容框架（使用QFrame实现圆角和背景）
        self.content_frame = QFrame()
        main_layout.addWidget(self.content_frame)
        
        # 应用样式表
        self._apply_styles()
        
        # 设置固定大小
        if self.is_fixed_size:
            self.setFixedSize(self.width, self.height)
            self.content_frame.setFixedSize(self.width, self.height)
        
        # 内容布局（用于添加子组件）
        self.content_layout = QVBoxLayout(self.content_frame)
        # 设置内边距，避免内容贴边
        margin = self.border_radius
        self.content_layout.setContentsMargins(margin, margin, margin, margin)
    
    def _validate_color(self, color_str):
        """验证并标准化颜色字符串"""
        if color_str.startswith("rgba"):
            rgba_match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", color_str)
            if rgba_match:
                r, g, b, a = map(int, rgba_match.groups())
                # 验证颜色值范围
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                a = max(0, min(255, a))
                return f"rgba({r}, {g}, {b}, {a})"
        
        # 默认颜色
        return "rgba(225, 240, 249, 200)"
    
    def _apply_styles(self):
        """应用样式表"""
        style = f"""
            QFrame {{
                background-color: {self._validated_color};
                border-radius: {self.border_radius}px;
                border: none;
            }}
        """
        self.content_frame.setStyleSheet(style)
    
    def add_widget(self, widget):
        """添加内部组件"""
        self.content_layout.addWidget(widget)
        
    def add_layout(self, layout):
        """添加布局"""
        self.content_layout.addLayout(layout)
    
    def remove_widget(self, widget):
        """移除内部组件"""
        self.content_layout.removeWidget(widget)
    
    def set_background_color(self, color):
        """动态设置背景色"""
        self._validated_color = self._validate_color(color)
        self._apply_styles()
    
    def set_border_radius(self, radius):
        """动态设置圆角半径"""
        self.border_radius = radius
        self._apply_styles()
        # 更新内容布局的边距
        margin = self.border_radius
        self.content_layout.setContentsMargins(margin, margin, margin, margin)