from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from system_monitor.progress_bars import (
    CPUProgressBar,
    DiskProgressBar,
    MemoryProgressBar,
)
from system_monitor.status_widgets import CPULabel, DiskLabel, MemoryLabel
from system_monitor.system_info_worker import SystemInfoWorker
from utils.config_manager import ConfigManager
from utils.utils import Utils


class SystemMonitorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.progress_config = self.config_manager.get_progress_bar_config()
        self.label_config = self.config_manager.get_label_config()
        self.system_config = self.config_manager.get_system_monitor_config()
        self.monitored_disks = self.system_config.get(
            "monitored_disks", Utils.get_all_available_drives()
        )
        self.disk_labels = {}
        self.disk_progress_bars = {}

        self.worker = None
        self.setup_layout()
        self.create_widgets()
        self.setup_worker()
        self.update_initial_info()

    def setup_layout(self):
        """设置布局"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

    def create_widgets(self):
        """创建所有组件"""
        # CPU组件
        self.cpu_label = CPULabel(self.label_config)
        self.cpu_progress = CPUProgressBar(self.progress_config)
        self.cpu_progress.setMaximum(100)

        # 内存组件
        self.memory_label = MemoryLabel(self.label_config)
        self.memory_progress = MemoryProgressBar(self.progress_config)
        self.memory_progress.setMaximum(100)

        # 磁盘组件
        for disk in self.monitored_disks:
            disk_name = f"{disk[:-1]}盘"
            disk_label = DiskLabel(disk_name, self.label_config)
            disk_progress = DiskProgressBar(disk, self.progress_config)
            disk_progress.setMaximum(100)
            self.disk_labels[disk] = disk_label
            self.disk_progress_bars[disk] = disk_progress

        # 添加到布局
        self.layout.addWidget(self.cpu_label)
        self.layout.addWidget(self.cpu_progress)
        self.layout.addWidget(self.memory_label)
        self.layout.addWidget(self.memory_progress)
        for disk in sorted(self.monitored_disks):
            self.layout.addWidget(self.disk_labels[disk])
            self.layout.addWidget(self.disk_progress_bars[disk])

    def setup_worker(self):
        """设置工作线程"""
        self.worker = SystemInfoWorker(
            self.system_config.get("update_interval", 2000), self.monitored_disks
        )
        self.worker.system_percent_updated.connect(self.update_all_system_info)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def update_initial_info(self):
        """更新初始信息"""
        pass

    def update_all_system_info(self, cpu_percent, memory_percent, disk_info):
        """更新所有系统信息"""
        # 更新CPU信息
        self.cpu_progress.setValue(int(cpu_percent))
        self.cpu_label.setText(f"CPU:{cpu_percent:.0f}%")

        # 更新内存信息
        self.memory_progress.setValue(int(memory_percent))
        self.memory_label.setText(f"内存:{memory_percent:.0f}%")

        # 更新磁盘信息
        for disk, percent in disk_info.items():
            if disk in self.disk_labels and disk in self.disk_progress_bars:
                self.disk_progress_bars[disk].setValue(int(percent))
                disk_name = f"{disk[:-1]}盘"
                self.disk_labels[disk].setText(f"{disk_name}:{percent:.0f}%")

    def handle_error(self, error_msg):
        """处理错误"""
        print(f"系统信息获取错误: {error_msg}")

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if event.button() == Qt.LeftButton:
            Utils.open_task_manager()
        super().mouseDoubleClickEvent(event)

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        event.accept()
