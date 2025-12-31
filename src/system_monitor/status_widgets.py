from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from system_monitor.style_manager import StyleManager
from utils.config_manager import ConfigManager


class StatusLabel(QLabel):
    """状态标签"""

    def __init__(self, text="", config=None):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        if config is None:
            config = ConfigManager().get_label_config()
        self.setStyleSheet(StyleManager.get_label_style(config))


class CPULabel(StatusLabel):
    def __init__(self, config=None):
        super().__init__("CPU: 0%", config)


class MemoryLabel(StatusLabel):
    def __init__(self, config=None):
        super().__init__("内存: 0%", config)


class DiskLabel(StatusLabel):
    def __init__(self, disk_name, config=None):
        super().__init__(f"{disk_name}: 0%", config)
