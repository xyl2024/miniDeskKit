import psutil
import string
import subprocess
from utils.logger import logger


class Utils:
    """工具函数"""

    @staticmethod
    def disk_exists(disk_path):
        """检查磁盘是否存在"""
        try:
            psutil.disk_usage(disk_path)
            return True
        except Exception:
            return False

    @staticmethod
    def get_all_available_drives():
        """获取所有可用的磁盘驱动器"""
        available_drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:"
            if Utils.disk_exists(drive):
                available_drives.append(drive)
        logger.info(f"当前可用的磁盘：{available_drives}")
        return available_drives

    @staticmethod
    def open_task_manager():
        """打开任务管理器"""
        subprocess.Popen(["taskmgr.exe"])
        logger.info("启动任务管理器")
