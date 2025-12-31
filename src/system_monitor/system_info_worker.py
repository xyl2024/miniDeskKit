import psutil
from PySide6.QtCore import QThread, Signal

from utils.logger import logger
from utils.utils import Utils


class SystemInfoWorker(QThread):
    """系统信息获取工作线程"""

    # cpu_percent, memory_percent, disk_percent_dict
    system_percent_updated = Signal(float, float, dict)
    error_occurred = Signal(str)

    def __init__(self, update_interval=2000, monitored_disks=None):
        super().__init__()
        self._running = True
        self.update_interval = update_interval
        self.monitored_disks = (
            monitored_disks if monitored_disks else Utils.get_all_available_drives()
        )

    def run(self):
        """在线程中获取系统信息"""
        while self._running:
            try:
                self.msleep(100)  # 短暂休眠
                if not self._running:
                    break

                # 获取CPU、内存、磁盘百分比信息
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                disk_info = {}
                for disk in self.monitored_disks:
                    try:
                        disk_usage = psutil.disk_usage(disk)
                        percent = (disk_usage.used / disk_usage.total) * 100
                        disk_info[disk] = percent
                    except Exception:
                        disk_info[disk] = 0  # 磁盘不可用时设为0
                self.system_percent_updated.emit(cpu_percent, memory.percent, disk_info)

            except Exception as e:
                self.error_occurred.emit(str(e))

            # 休眠指定时间
            self.msleep(self.update_interval)

        logger.info("关闭 System Info Worker 线程")

    def stop(self):
        """停止线程"""
        self._running = False
