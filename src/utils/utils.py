import psutil
import string


class Utils:
    """工具函数"""

    @staticmethod
    def disk_exists(disk_path):
        """检查磁盘是否存在"""
        try:
            psutil.disk_usage(disk_path)
            return True
        except:
            return False

    @staticmethod
    def get_all_available_drives():
        """获取所有可用的磁盘驱动器"""
        available_drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:"
            if Utils.disk_exists(drive):
                available_drives.append(drive)
        return available_drives
