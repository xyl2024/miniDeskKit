from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolTip, QWidget

from utils.config_manager import ConfigManager
from utils.logger import logger
from weather.precip_emojis_widget import PrecipEmojisWidget
from weather.precip_worker import PrecipWorker


class PrecipWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.weather_config = self.config_manager.get_minutely_weather_config()
        self.data = None
        self.precip_summary = ""
        self.precip_worker = None

        self.setup_ui()
        self.setup_emojis_widget()
        if self._check_hefeng_api_config():
            self.setup_worker()
        self.update_precip_label([])

    def setup_ui(self):
        """设置UI布局和组件"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.precip_label = QLabel()
        self.precip_label.setAlignment(Qt.AlignCenter)
        self.precip_label.setFixedSize(22, 22)
        self.precip_label.setFont(QFont("Arial", 16))

        # 启用鼠标跟踪和工具提示
        self.precip_label.setMouseTracking(True)
        self.precip_label.enterEvent = self.label_enter_event
        self.precip_label.leaveEvent = self.label_leave_event
        self.precip_label.mousePressEvent = self.label_mouse_press_event

        layout.addWidget(self.precip_label)

    def setup_emojis_widget(self):
        """设置降水数据Emojis组件"""
        self.emojis_widget = PrecipEmojisWidget()
        self.emojis_visible = False

    def label_mouse_press_event(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            if self.emojis_visible:
                self.hide_emojis()
            else:
                self.show_emojis()
        super(type(self.precip_label), self.precip_label).mousePressEvent(event)

    def show_emojis(self):
        """显示降水数据Emojis"""
        if self.data:
            self.emojis_widget.update_data(self.data)

        widget_pos = self.mapToGlobal(self.rect().topRight())

        # 获取主窗口的边距配置
        window_config = self.config_manager.get_window_config()
        margin_config = window_config.get("margin", {})
        right_margin = margin_config.get("right", 2)

        # 向右移动一定距离（包括边距和一些额外间距）
        offset_x = right_margin + 5  # 额外5像素间距
        emojis_pos = widget_pos + QPoint(offset_x, 0)

        self.emojis_widget.show_at_position(emojis_pos)
        self.emojis_visible = True

    def hide_emojis(self):
        """隐藏降水数据Emojis"""
        self.emojis_widget.hide()
        self.emojis_visible = False

    def label_enter_event(self, event):
        """鼠标进入标签事件"""
        if self.precip_summary:
            QToolTip.showText(
                self.precip_label.mapToGlobal(self.precip_label.rect().center()),
                self.precip_summary,
                self.precip_label,
            )
        super(type(self.precip_label), self.precip_label).enterEvent(event)

    def label_leave_event(self, event):
        """鼠标离开标签事件"""
        QToolTip.hideText()
        super(type(self.precip_label), self.precip_label).leaveEvent(event)

    def _check_hefeng_api_config(self):
        api_host = self.weather_config.get("api_host")
        api_key = self.weather_config.get("api_key")
        location = self.weather_config.get("location")
        return all([api_host, api_key, location])

    def setup_worker(self):
        self.precip_worker = PrecipWorker(
            api_host=self.weather_config.get("api_host"),
            api_key=self.weather_config.get("api_key"),
            location=self.weather_config.get("location"),
            update_interval=self.weather_config.get("update_interval", 300000),
        )

        self.precip_worker.precip_data.connect(self.update_precip_label)
        self.precip_worker.precip_summary.connect(self.update_precip_summary)
        self.precip_worker.error_occurred.connect(self.on_weather_error)
        self.precip_worker.start()

    def update_precip_label(self, precip_data):
        """根据获取到的降水数据更新UI显示"""
        self.data = precip_data
        total_precip = 0.0

        for i in precip_data:
            precip = float(i.get("precip", 0))
            total_precip += precip

        icon_name, fallback_emoji = self.get_precip_icon(total_precip)
        icon_path = Path(__file__).resolve().parent / icon_name
        pixmap = QPixmap(str(icon_path))
        if pixmap.isNull():
            self.precip_label.setPixmap(QPixmap())
            self.precip_label.setText(fallback_emoji)
        else:
            scaled = pixmap.scaled(
                QSize(18, 18),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.precip_label.setText("")
            self.precip_label.setPixmap(scaled)

        # 如果降水数据Emojis当前正在显示, 则更新降水数据Emojis数据
        if self.emojis_visible and self.data:
            self.emojis_widget.update_data(self.data)

    def update_precip_summary(self, summary):
        """更新天气摘要"""
        self.precip_summary = summary
        if (
            self.precip_label.underMouse()
            and self.precip_summary
            and not self.emojis_visible
        ):
            QToolTip.hideText()
            QToolTip.showText(
                self.precip_label.mapToGlobal(self.precip_label.rect().center()),
                self.precip_summary,
                self.precip_label,
            )

    def get_precip_icon(self, total_precip):
        threshold = 0.0

        if total_precip > threshold:
            return "rainy.png", "🌧️"
        return "sunny.png", "🌤️"

    def on_weather_error(self, error_msg):
        """处理天气组件错误"""
        logger.error(f"天气组件错误: {error_msg}")

    def hideEvent(self, event):
        """窗口隐藏事件"""
        self.hide_emojis()
        super().hideEvent(event)

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.hide_emojis()
        if self.precip_worker:
            self.precip_worker.stop()
            self.precip_worker.wait()
        if event:
            event.accept()
