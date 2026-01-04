from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from utils.config_manager import ConfigManager
from utils.logger import logger


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.setup_ui()
        self.load_current_config()

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("设置")
        self.setFixedWidth(500)
        self.setFixedHeight(600)

        layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()

        self.tab_widget.addTab(self.create_window_tab(), "窗口")
        self.tab_widget.addTab(self.create_progress_bar_tab(), "进度条")
        self.tab_widget.addTab(self.create_label_tab(), "标签")
        self.tab_widget.addTab(self.create_system_monitor_tab(), "系统监控")
        self.tab_widget.addTab(self.create_weather_tab(), "天气")
        self.tab_widget.addTab(self.create_logging_tab(), "日志")

        layout.addWidget(self.tab_widget)

        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_and_close)
        apply_button = QPushButton("应用")
        apply_button.clicked.connect(self.apply_config)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def create_window_tab(self):
        """创建窗口设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(20, 200)
        self.window_width_spin.setSuffix(" px")

        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedWidth(100)
        self.bg_color_button.clicked.connect(self.choose_bg_color)
        self.bg_color_label = QLabel()

        self.border_radius_spin = QSpinBox()
        self.border_radius_spin.setRange(0, 50)
        self.border_radius_spin.setSuffix(" px")

        self.margin_left_spin = QSpinBox()
        self.margin_left_spin.setRange(0, 20)
        self.margin_left_spin.setSuffix(" px")

        self.margin_top_spin = QSpinBox()
        self.margin_top_spin.setRange(0, 20)
        self.margin_top_spin.setSuffix(" px")

        self.margin_right_spin = QSpinBox()
        self.margin_right_spin.setRange(0, 20)
        self.margin_right_spin.setSuffix(" px")

        self.margin_bottom_spin = QSpinBox()
        self.margin_bottom_spin.setRange(0, 20)
        self.margin_bottom_spin.setSuffix(" px")

        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 20)
        self.spacing_spin.setSuffix(" px")

        self.position_x_spin = QSpinBox()
        self.position_x_spin.setRange(0, 4096)
        self.position_x_spin.setSuffix(" px")

        self.position_y_spin = QSpinBox()
        self.position_y_spin.setRange(0, 4096)
        self.position_y_spin.setSuffix(" px")

        layout.addRow("窗口宽度:", self.window_width_spin)
        layout.addRow("背景颜色:", self.bg_color_button)
        layout.addRow("", self.bg_color_label)
        layout.addRow("圆角半径:", self.border_radius_spin)
        layout.addRow("左边距:", self.margin_left_spin)
        layout.addRow("上边距:", self.margin_top_spin)
        layout.addRow("右边距:", self.margin_right_spin)
        layout.addRow("下边距:", self.margin_bottom_spin)
        layout.addRow("间距:", self.spacing_spin)
        layout.addRow("X坐标:", self.position_x_spin)
        layout.addRow("Y坐标:", self.position_y_spin)

        return widget

    def create_progress_bar_tab(self):
        """创建进度条设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.pb_height_spin = QSpinBox()
        self.pb_height_spin.setRange(2, 30)
        self.pb_height_spin.setSuffix(" px")

        self.pb_border_width_spin = QSpinBox()
        self.pb_border_width_spin.setRange(0, 5)
        self.pb_border_width_spin.setSuffix(" px")

        self.pb_border_color_button = QPushButton()
        self.pb_border_color_button.setFixedWidth(100)
        self.pb_border_color_button.clicked.connect(self.choose_pb_border_color)
        self.pb_border_color_label = QLabel()

        self.pb_border_radius_spin = QSpinBox()
        self.pb_border_radius_spin.setRange(0, 10)
        self.pb_border_radius_spin.setSuffix(" px")

        self.pb_chunk_radius_spin = QSpinBox()
        self.pb_chunk_radius_spin.setRange(0, 10)
        self.pb_chunk_radius_spin.setSuffix(" px")

        self.pb_bg_alpha_spin = QSpinBox()
        self.pb_bg_alpha_spin.setRange(0, 255)
        self.pb_bg_alpha_spin.setSuffix(" /255")

        self.cpu_color_button = QPushButton()
        self.cpu_color_button.setFixedWidth(100)
        self.cpu_color_button.clicked.connect(self.choose_cpu_color)
        self.cpu_color_label = QLabel()

        self.memory_color_button = QPushButton()
        self.memory_color_button.setFixedWidth(100)
        self.memory_color_button.clicked.connect(self.choose_memory_color)
        self.memory_color_label = QLabel()

        self.disk_color_button = QPushButton()
        self.disk_color_button.setFixedWidth(100)
        self.disk_color_button.clicked.connect(self.choose_disk_color)
        self.disk_color_label = QLabel()

        layout.addRow("高度:", self.pb_height_spin)
        layout.addRow("边框宽度:", self.pb_border_width_spin)
        layout.addRow("边框颜色:", self.pb_border_color_button)
        layout.addRow("", self.pb_border_color_label)
        layout.addRow("圆角半径:", self.pb_border_radius_spin)
        layout.addRow("分块圆角:", self.pb_chunk_radius_spin)
        layout.addRow("背景透明度:", self.pb_bg_alpha_spin)
        layout.addRow("CPU颜色:", self.cpu_color_button)
        layout.addRow("", self.cpu_color_label)
        layout.addRow("内存颜色:", self.memory_color_button)
        layout.addRow("", self.memory_color_label)
        layout.addRow("磁盘颜色:", self.disk_color_button)
        layout.addRow("", self.disk_color_label)

        return widget

    def create_label_tab(self):
        """创建标签设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.label_font_size_spin = QSpinBox()
        self.label_font_size_spin.setRange(6, 24)
        self.label_font_size_spin.setSuffix(" pt")

        self.label_color_button = QPushButton()
        self.label_color_button.setFixedWidth(100)
        self.label_color_button.clicked.connect(self.choose_label_color)
        self.label_color_label = QLabel()

        layout.addRow("字体大小:", self.label_font_size_spin)
        layout.addRow("文字颜色:", self.label_color_button)
        layout.addRow("", self.label_color_label)

        return widget

    def create_system_monitor_tab(self):
        """创建系统监控设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        interval_layout = QFormLayout()
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(500, 10000)
        self.update_interval_spin.setSingleStep(500)
        self.update_interval_spin.setSuffix(" ms")
        interval_layout.addRow("更新间隔:", self.update_interval_spin)

        disk_group = QGroupBox("监控磁盘")
        disk_layout = QVBoxLayout()

        self.disk_list = QListWidget()
        self.disk_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        disk_button_layout = QHBoxLayout()
        add_disk_button = QPushButton("添加")
        add_disk_button.clicked.connect(self.add_disk)
        remove_disk_button = QPushButton("删除")
        remove_disk_button.clicked.connect(self.remove_disk)
        disk_button_layout.addWidget(add_disk_button)
        disk_button_layout.addWidget(remove_disk_button)

        disk_layout.addWidget(self.disk_list)
        disk_layout.addLayout(disk_button_layout)
        disk_group.setLayout(disk_layout)

        layout.addLayout(interval_layout)
        layout.addWidget(disk_group)

        return widget

    def create_weather_tab(self):
        """创建天气设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.api_host_edit = QLineEdit()
        self.api_key_edit = QLineEdit()
        self.location_edit = QLineEdit()

        self.weather_update_interval_spin = QSpinBox()
        self.weather_update_interval_spin.setRange(60000, 3600000)
        self.weather_update_interval_spin.setSingleStep(60000)
        self.weather_update_interval_spin.setSuffix(" ms")

        layout.addRow("API主机:", self.api_host_edit)
        layout.addRow("API密钥:", self.api_key_edit)
        layout.addRow("位置:", self.location_edit)
        layout.addRow("更新间隔:", self.weather_update_interval_spin)

        return widget

    def create_logging_tab(self):
        """创建日志设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

        self.log_to_file_check = QCheckBox("记录到文件")
        self.log_to_console_check = QCheckBox("记录到控制台")

        layout.addRow("日志级别:", self.log_level_combo)
        layout.addRow("", self.log_to_file_check)
        layout.addRow("", self.log_to_console_check)

        return widget

    def load_current_config(self):
        """加载当前配置"""
        window_config = self.config_manager.get_window_config()
        progress_config = self.config_manager.get_progress_bar_config()
        label_config = self.config_manager.get_label_config()
        system_config = self.config_manager.get_system_monitor_config()
        weather_config = self.config_manager.get_minutely_weather_config()
        logging_config = self.config_manager.get_logging_config()

        self.window_width_spin.setValue(window_config.get("width", 48))

        bg_color = window_config.get("background_color", "rgba(225, 240, 249, 200)")
        self.current_bg_color = self.parse_rgba_color(bg_color)
        self.set_color_button(
            self.bg_color_button, self.bg_color_label, self.current_bg_color
        )

        self.border_radius_spin.setValue(window_config.get("border_radius", 5))

        margin = window_config.get("margin", {})
        self.margin_left_spin.setValue(margin.get("left", 2))
        self.margin_top_spin.setValue(margin.get("top", 2))
        self.margin_right_spin.setValue(margin.get("right", 2))
        self.margin_bottom_spin.setValue(margin.get("bottom", 2))

        self.spacing_spin.setValue(window_config.get("spacing", 3))

        position = window_config.get("position", {"x": 100, "y": 100})
        self.position_x_spin.setValue(position.get("x", 100))
        self.position_y_spin.setValue(position.get("y", 100))

        self.pb_height_spin.setValue(progress_config.get("height", 8))
        self.pb_border_width_spin.setValue(progress_config.get("border_width", 1))
        self.pb_border_radius_spin.setValue(progress_config.get("border_radius", 2))
        self.pb_chunk_radius_spin.setValue(progress_config.get("chunk_radius", 1))
        self.pb_bg_alpha_spin.setValue(progress_config.get("background_alpha", 100))

        border_color = progress_config.get("border_color", "#ccc")
        self.current_pb_border_color = QColor(border_color)
        self.set_color_button(
            self.pb_border_color_button,
            self.pb_border_color_label,
            self.current_pb_border_color,
        )

        colors = progress_config.get("colors", {})
        self.current_cpu_color = QColor(colors.get("cpu", "#FF5722"))
        self.set_color_button(
            self.cpu_color_button, self.cpu_color_label, self.current_cpu_color
        )
        self.current_memory_color = QColor(colors.get("memory", "#2196F3"))
        self.set_color_button(
            self.memory_color_button, self.memory_color_label, self.current_memory_color
        )
        self.current_disk_color = QColor(colors.get("disk", "#4CAF50"))
        self.set_color_button(
            self.disk_color_button, self.disk_color_label, self.current_disk_color
        )

        self.label_font_size_spin.setValue(label_config.get("font_size", 10))
        label_color = label_config.get("color", "black")
        self.current_label_color = QColor(label_color)
        self.set_color_button(
            self.label_color_button, self.label_color_label, self.current_label_color
        )

        self.update_interval_spin.setValue(system_config.get("update_interval", 2000))

        self.disk_list.clear()
        monitored_disks = system_config.get("monitored_disks", [])
        for disk in monitored_disks:
            self.disk_list.addItem(disk)

        self.api_host_edit.setText(weather_config.get("api_host", ""))
        self.api_key_edit.setText(weather_config.get("api_key", ""))
        self.location_edit.setText(weather_config.get("location", ""))
        self.weather_update_interval_spin.setValue(
            weather_config.get("update_interval", 300000)
        )

        self.log_level_combo.setCurrentText(logging_config.get("level", "INFO"))
        self.log_to_file_check.setChecked(logging_config.get("log_to_file", True))
        self.log_to_console_check.setChecked(logging_config.get("log_to_console", True))

    def parse_rgba_color(self, rgba_str):
        """解析RGBA颜色字符串"""
        import re

        rgba_match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", rgba_str)
        if rgba_match:
            r, g, b, a = map(int, rgba_match.groups())
            return QColor(r, g, b, a)
        return QColor(225, 240, 249, 200)

    def set_color_button(self, button, label, color):
        """设置颜色按钮"""
        button.setStyleSheet(f"background-color: {color.name()};")
        label.setText(color.name())

    def choose_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor(self.current_bg_color, self, "选择背景颜色")
        if color.isValid():
            self.current_bg_color = color
            self.set_color_button(self.bg_color_button, self.bg_color_label, color)

    def choose_pb_border_color(self):
        """选择进度条边框颜色"""
        color = QColorDialog.getColor(
            self.current_pb_border_color, self, "选择边框颜色"
        )
        if color.isValid():
            self.current_pb_border_color = color
            self.set_color_button(
                self.pb_border_color_button, self.pb_border_color_label, color
            )

    def choose_cpu_color(self):
        """选择CPU颜色"""
        color = QColorDialog.getColor(self.current_cpu_color, self, "选择CPU颜色")
        if color.isValid():
            self.current_cpu_color = color
            self.set_color_button(self.cpu_color_button, self.cpu_color_label, color)

    def choose_memory_color(self):
        """选择内存颜色"""
        color = QColorDialog.getColor(self.current_memory_color, self, "选择内存颜色")
        if color.isValid():
            self.current_memory_color = color
            self.set_color_button(
                self.memory_color_button, self.memory_color_label, color
            )

    def choose_disk_color(self):
        """选择磁盘颜色"""
        color = QColorDialog.getColor(self.current_disk_color, self, "选择磁盘颜色")
        if color.isValid():
            self.current_disk_color = color
            self.set_color_button(self.disk_color_button, self.disk_color_label, color)

    def choose_label_color(self):
        """选择标签颜色"""
        color = QColorDialog.getColor(self.current_label_color, self, "选择标签颜色")
        if color.isValid():
            self.current_label_color = color
            self.set_color_button(
                self.label_color_button, self.label_color_label, color
            )

    def add_disk(self):
        """添加磁盘"""
        disk, ok = QInputDialog.getText(self, "添加磁盘", "请输入磁盘路径 (例如: E:):")
        if ok and disk:
            self.disk_list.addItem(disk)

    def remove_disk(self):
        """删除选中的磁盘"""
        for item in self.disk_list.selectedItems():
            self.disk_list.takeItem(self.disk_list.row(item))

    def apply_config(self):
        """应用当前配置"""
        self.save_config_to_manager()
        logger.info("配置已应用")
        if self.parent():
            self.parent().window_config = self.config_manager.get_window_config()
            self.parent().setFixedWidth(self.parent().window_config.get("width", 48))
            pos = self.config_manager.get_window_position()
            self.parent().move(pos)

    def save_config_to_manager(self):
        """保存配置到配置管理器"""
        window_config = {
            "width": self.window_width_spin.value(),
            "background_color": f"rgba({self.current_bg_color.red()}, {self.current_bg_color.green()}, {self.current_bg_color.blue()}, {self.current_bg_color.alpha()})",
            "border_radius": self.border_radius_spin.value(),
            "margin": {
                "left": self.margin_left_spin.value(),
                "top": self.margin_top_spin.value(),
                "right": self.margin_right_spin.value(),
                "bottom": self.margin_bottom_spin.value(),
            },
            "spacing": self.spacing_spin.value(),
            "position": {
                "x": self.position_x_spin.value(),
                "y": self.position_y_spin.value(),
            },
        }

        progress_config = {
            "height": self.pb_height_spin.value(),
            "border_width": self.pb_border_width_spin.value(),
            "border_color": self.current_pb_border_color.name(),
            "border_radius": self.pb_border_radius_spin.value(),
            "chunk_radius": self.pb_chunk_radius_spin.value(),
            "background_alpha": self.pb_bg_alpha_spin.value(),
            "colors": {
                "cpu": self.current_cpu_color.name(),
                "memory": self.current_memory_color.name(),
                "disk": self.current_disk_color.name(),
            },
        }

        label_config = {
            "font_size": self.label_font_size_spin.value(),
            "color": self.current_label_color.name(),
        }

        monitored_disks = []
        for i in range(self.disk_list.count()):
            monitored_disks.append(self.disk_list.item(i).text())

        system_config = {
            "update_interval": self.update_interval_spin.value(),
            "monitored_disks": monitored_disks,
        }

        weather_config = {
            "api_host": self.api_host_edit.text(),
            "api_key": self.api_key_edit.text(),
            "location": self.location_edit.text(),
            "update_interval": self.weather_update_interval_spin.value(),
        }

        logging_config = {
            "level": self.log_level_combo.currentText(),
            "log_to_file": self.log_to_file_check.isChecked(),
            "log_to_console": self.log_to_console_check.isChecked(),
        }

        self.config_manager.config["window"] = window_config
        self.config_manager.config["progress_bars"] = progress_config
        self.config_manager.config["labels"] = label_config
        self.config_manager.config["system_monitor"] = system_config
        self.config_manager.config["minutely_weather"] = weather_config
        self.config_manager.config["logging"] = logging_config

        self.config_manager.save_config()

    def save_and_close(self):
        """保存并关闭"""
        self.save_config_to_manager()
        logger.info("配置已保存")
        self.accept()
