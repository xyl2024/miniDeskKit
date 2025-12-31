import json
import os
from PySide6.QtCore import QPoint


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file="configs/window_config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return self.get_default_config()
        return self.get_default_config()

    def get_default_config(self):
        """获取默认配置"""
        return {
            "window": {
                "position": {"x": 4, "y": 548},
                "width": 48,
                "title": "桌面小部件",
                "background_color": "rgba(225, 240, 249, 200)",
                "border_radius": 5,
                "margin": {"left": 2, "top": 2, "right": 2, "bottom": 2},
                "spacing": 3,
            },
            "progress_bars": {
                "height": 8,
                "border_width": 1,
                "border_color": "#ccc",
                "border_radius": 2,
                "background_alpha": 100,
                "chunk_radius": 1,
                "colors": {"cpu": "#FF5722", "memory": "#2196F3", "disk": "#4CAF50"},
            },
            "labels": {
                "font_size": 10,
                "color": "black",
                "padding": 1,
                "background_transparent": True,
            },
            "system_monitor": {
                "update_interval": 2000,  # 毫秒
                "monitored_disks": [
                    "C:",
                    "D:",
                ],  # 要监控的磁盘列表，如果为空则自动检测所有磁盘
            },
            "audio_visualizer": {
                "height": 30,
                "line_color": "#FF5722",  # 橙红色，类似心电图
                "line_width": 2,
                "background_color": "#00000000",  # 透明
                "wave_height": 20,
                "speed": 2,
            },
            "logging": {
                "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
                "max_file_size": 10485760,  # 10MB
                "backup_count": 5,
                "log_to_file": True,
                "log_to_console": True,
            },
            "minutely_weather": {  # 和风天气API
                "api_host": "",
                "api_key": "",
                "location": "",
                "update_interval": 300000,  # 更新间隔，单位毫秒 (例如5分钟)
            },
        }

    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def get_window_position(self):
        """获取窗口位置"""
        pos = self.config.get("window", {}).get("position", {"x": 100, "y": 100})
        return QPoint(pos["x"], pos["y"])

    def set_window_position(self, x, y):
        """设置窗口位置"""
        self.config["window"]["position"] = {"x": x, "y": y}
        self.save_config()

    def get_window_config(self):
        """获取窗口配置"""
        return self.config.get("window", {})

    def get_progress_bar_config(self):
        """获取进度条配置"""
        return self.config.get("progress_bars", {})

    def get_label_config(self):
        """获取标签配置"""
        return self.config.get("labels", {})

    def get_system_monitor_config(self):
        """获取系统监控配置"""
        return self.config.get("system_monitor", {})

    def get_audio_visualizer_config(self):
        """获取音频可视化配置"""
        return self.config.get("audio_visualizer", {})

    def get_logging_config(self):
        """获取日志配置"""
        return self.config.get("logging", {})

    def get_minutely_weather_config(self):
        """获取分钟级天气组件配置"""
        return self.config.get("minutely_weather", {})
