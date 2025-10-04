from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QSlider,
    QLayout,
)
from PySide6.QtCore import Qt
import os


class MusicDetailWidget(QWidget):
    """音乐详情界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setup_ui()
        self.hide()  # 初始隐藏

    def setup_ui(self):
        """设置UI布局"""
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)  # 弹出窗口，无边框
        # self.setAttribute(Qt.WA_TranslucentBackground)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # 歌名
        self.song_name_label = QLabel("歌名: 未知")
        self.song_name_label.setAlignment(Qt.AlignCenter)
        self.song_name_label.setStyleSheet("font-size: 12px;")
        self.song_name_label.setAttribute(Qt.WA_TranslucentBackground)
        main_layout.addWidget(self.song_name_label)

        # 作者
        self.artist_label = QLabel("作者: 未知")
        self.artist_label.setAlignment(Qt.AlignCenter)
        self.artist_label.setStyleSheet("font-size: 12px;")
        self.artist_label.setAttribute(Qt.WA_TranslucentBackground)
        main_layout.addWidget(self.artist_label)

        # 控制按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # 上一首按钮
        self.prev_button = QPushButton("⏮️")
        self.prev_button.setFixedSize(30, 30)
        self.prev_button.clicked.connect(self.on_prev_clicked)
        self.prev_button.setAttribute(Qt.WA_TranslucentBackground)
        button_layout.addWidget(self.prev_button)

        # 播放/暂停按钮
        self.play_pause_button = QPushButton("⏸️")
        self.play_pause_button.setFixedSize(30, 30)
        self.play_pause_button.clicked.connect(self.on_play_pause_clicked)
        self.play_pause_button.setAttribute(Qt.WA_TranslucentBackground)
        button_layout.addWidget(self.play_pause_button)

        # 下一首按钮
        self.next_button = QPushButton("⏭️")
        self.next_button.setFixedSize(30, 30)
        self.next_button.clicked.connect(self.on_next_clicked)
        self.next_button.setAttribute(Qt.WA_TranslucentBackground)
        button_layout.addWidget(self.next_button)

        main_layout.addLayout(button_layout)

        # 应用整体样式
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(225, 240, 249, 200);
                border-radius: 3px;
            }
        """)

        main_layout.setSizeConstraint(QLayout.SetFixedSize)

    def on_prev_clicked(self):
        """上一首按钮点击事件"""
        if self.parent_widget:
            self.parent_widget.play_prev_music()

    def on_play_pause_clicked(self):
        """播放/暂停按钮点击事件"""
        if self.parent_widget:
            self.parent_widget.toggle_play_pause()
            # 更新按钮文本
            if self.parent_widget.is_playing:
                self.play_pause_button.setText("⏸️")
            else:
                self.play_pause_button.setText("▶️")

    def on_next_clicked(self):
        """下一首按钮点击事件"""
        if self.parent_widget:
            self.parent_widget.play_next_music()

    def update_song_info(self, song_path):
        """更新歌曲信息"""
        if song_path:
            filename = os.path.basename(song_path)
            # 简单解析文件名，移除扩展名
            name_parts = os.path.splitext(filename)[0].split(" - ")
            if len(name_parts) >= 2:
                artist = name_parts[0]
                title = name_parts[1]
            else:
                artist = "未知"
                title = name_parts[0]

            self.song_name_label.setText(f"歌名: {title}")
            self.artist_label.setText(f"作者: {artist}")
        else:
            self.song_name_label.setText("歌名: 未知")
            self.artist_label.setText("作者: 未知")

    def update_time_info(self, position, duration):
        """更新时间信息"""
        pos_str = self.format_time(position)
        dur_str = self.format_time(duration)
        self.time_label.setText(f"{pos_str} / {dur_str}")

    def format_time(self, seconds):
        """格式化时间为 mm:ss"""
        if seconds < 0:
            return "00:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
