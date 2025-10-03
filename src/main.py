import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QRegion, QColor, QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QVBoxLayout, QWidget

from utils.logger import logger
from utils.config_manager import ConfigManager



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.window_config = self.config_manager.get_window_config()
        self.setup_window()
        self.setup_inner_widgets()
        self.setup_system_tray()

    def setup_inner_widgets(self):
        """设置内部组件, 后续可以增加设置功能, 在这里按需加载哪些部件"""
        self.create_main_layout()
        
        from weather.precip_widget import PrecipWidget
        self.minutely_weather_widget = PrecipWidget()
        self.add_widget(self.minutely_weather_widget)

        from music.music_player_widget import MusicPlayerWidget
        self.music_player = MusicPlayerWidget()
        self.add_widget(self.music_player)

        from system_monitor.system_monitor_widget import SystemMonitorWidget
        self.system_monitor = SystemMonitorWidget()
        self.add_widget(self.system_monitor)

    def setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle(self.window_config.get("title", "桌面小部件"))
        self.setFixedWidth(self.window_config.get("width", 48))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.move(self.config_manager.get_window_position())

    def create_main_layout(self):
        """创建主布局"""
        self.main_layout = QVBoxLayout(self)
        margin_config = self.window_config.get("margin", {})
        self.main_layout.setContentsMargins(
            margin_config.get("left", 2),
            margin_config.get("top", 2),
            margin_config.get("right", 2),
            margin_config.get("bottom", 2),
        )
        self.main_layout.setSpacing(self.window_config.get("spacing", 3))

    def add_widget(self, widget):
        """添加组件到主布局"""
        self.main_layout.addWidget(widget)

    def remove_widget(self, widget):
        """从主布局移除组件"""
        self.main_layout.removeWidget(widget)

    def paintEvent(self, event):
        """绘制圆角窗口"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        radius = self.window_config.get("border_radius", 5)
        rect = self.rect()
        path.addRoundedRect(rect, radius, radius)

        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

        bg_color = self.window_config.get(
            "background_color", "rgba(225, 240, 249, 200)"
        )
        # 解析颜色字符串
        if bg_color.startswith("rgba"):
            # 提取 rgba 值
            import re

            rgba_match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", bg_color)
            if rgba_match:
                r, g, b, a = map(int, rgba_match.groups())
                painter.fillPath(path, QColor(r, g, b, a))
            else:
                painter.fillPath(path, QColor(225, 240, 249, 200))
        else:
            painter.fillPath(path, QColor(225, 240, 249, 200))

    def setup_system_tray(self):
        """设置系统托盘"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            icon = QIcon("configs/icon.ico")
            self.tray_icon.setIcon(icon)
            self.tray_icon.setToolTip(self.window_config.get("title", "桌面小部件"))

            # 创建右键菜单
            self.tray_menu = QMenu()
            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.quit_app)
            self.tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(self.tray_menu)
            self.tray_icon.activated.connect(self.on_tray_icon_activated)

            self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.hide() if self.isVisible() else self.show()

    def quit_app(self):
        """退出应用"""
        logger.info("退出应用")
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        self.close()
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
