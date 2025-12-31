from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLayout, QWidget


class PrecipEmojisWidget(QWidget):
    """显示未来两小时降水的界面"""

    def __init__(self):
        super().__init__()
        self.data = []
        self.setup_window()

    def setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)  # 弹出窗口，无边框
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 使用布局添加标签
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(225, 240, 249, 200);
                border-radius: 3px;
            }
        """)

        # 设置布局为最小尺寸
        layout.setSizeConstraint(QLayout.SetFixedSize)

    def update_data(self, precip_data):
        """更新数据并显示emoji"""
        self.data = precip_data

        # 构建emoji字符串
        emoji_str = ""
        for item in precip_data:
            precip = float(item.get("precip", 0))
            # 根据降水量选择emoji
            if precip > 0.2:
                emoji = "⛈️"  # 大雨
            elif precip > 0.0:
                emoji = "🌧️"  # 小雨
            else:
                emoji = "☀️"  # 无雨
            emoji_str += emoji

        self.label.setText(emoji_str)
        self.label.setFont(QFont("Arial", 14))

        # 更新窗口大小以适应内容
        self.adjustSize()

    def show_at_position(self, pos):
        """在指定位置显示"""
        self.move(pos)
        self.show()
