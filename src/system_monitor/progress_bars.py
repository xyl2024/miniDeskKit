from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressBar

from system_monitor.style_manager import StyleManager


class SystemProgressBar(QProgressBar):
    """系统进度条基类"""

    def __init__(self, color, config, disk_name=None):
        super().__init__()
        self.setOrientation(Qt.Horizontal)
        self.setFixedHeight(config.get("height", 8))
        self.setTextVisible(False)
        self.disk_name = disk_name
        self.setStyleSheet(StyleManager.get_progress_bar_style(color, config))


class DiskProgressBar(SystemProgressBar):
    """磁盘进度条"""

    def __init__(self, disk_name, config):
        super().__init__(
            config.get("colors", {}).get("disk", "#4CAF50"), config, disk_name
        )


class CPUProgressBar(SystemProgressBar):
    """CPU进度条"""

    def __init__(self, config):
        super().__init__(config.get("colors", {}).get("cpu", "#FF5722"), config)


class MemoryProgressBar(SystemProgressBar):
    """内存进度条"""

    def __init__(self, config):
        super().__init__(config.get("colors", {}).get("memory", "#2196F3"), config)
