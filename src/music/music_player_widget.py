from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolTip
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

import os
import random
from pathlib import Path

from utils.config_manager import ConfigManager
from utils.logger import logger


class MusicPlayerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.music_config = self.config_manager.get_music_player_config()

        self.player = None
        self.audio_output = None
        self.playlist = []
        self.current_index = -1
        self.is_playing = False

        self.setup_ui()
        self.setup_player()
        self.scan_music_directory()

        if self.music_config.get("auto_play", False) and self.playlist:
            self.play_random_music()

    def setup_ui(self):
        """设置UI布局和组件"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建音乐播放label
        self.music_label = QLabel("🎵")
        self.music_label.setAlignment(Qt.AlignCenter)
        self.music_label.setFont(QFont("Arial", 16))

        # 启用鼠标跟踪和工具提示
        self.music_label.setMouseTracking(True)
        self.music_label.enterEvent = self.label_enter_event
        self.music_label.leaveEvent = self.label_leave_event
        self.music_label.mousePressEvent = self.label_mouse_press_event

        layout.addWidget(self.music_label)

    def setup_player(self):
        """设置音频播放器"""
        try:
            self.audio_output = QAudioOutput()
            self.player = QMediaPlayer()
            self.player.setAudioOutput(self.audio_output)

            # 设置音量
            volume = self.music_config.get("volume", 50)
            self.audio_output.setVolume(volume / 100.0)

            # 连接播放结束信号
            self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        except Exception as e:
            logger.error(f"初始化音频播放器失败: {e}")
            self.player = None

    def scan_music_directory(self):
        """扫描音乐目录"""
        music_dir = self.music_config.get("music_directory", "")
        if not music_dir or not os.path.exists(music_dir):
            logger.warning(f"音乐目录不存在: {music_dir}")
            return

        # 支持的音频格式
        audio_extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}

        music_dir_path = Path(music_dir)
        self.playlist = []

        for file_path in music_dir_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                self.playlist.append(str(file_path))

        logger.info(f"扫描到 {len(self.playlist)} 首音乐文件")
        if self.playlist:
            logger.debug(f"音乐列表: {self.playlist}")

    def play_random_music(self):
        """随机播放一首音乐"""
        if not self.playlist:
            logger.warning("没有找到音乐文件")
            return

        # 随机选择一首音乐
        self.current_index = random.randint(0, len(self.playlist) - 1)
        music_file = self.playlist[self.current_index]

        if self.player:
            try:
                url = QUrl.fromLocalFile(music_file)
                self.player.setSource(url)
                self.player.play()
                self.is_playing = True
                logger.info(f"开始播放: {os.path.basename(music_file)}")
            except Exception as e:
                logger.error(f"播放音乐失败: {e}")
        else:
            logger.error("音频播放器未初始化")

    def toggle_play_pause(self):
        """播放/暂停切换"""
        if not self.playlist:
            logger.warning("没有音乐文件可播放")
            return

        if not self.player:
            logger.error("音频播放器未初始化")
            return

        if self.is_playing:
            # 暂停播放
            self.player.pause()
            self.is_playing = False
            logger.info("音乐已暂停")
        else:
            # 继续播放或开始播放
            if self.current_index == -1:
                # 如果没有当前播放的音乐，随机播放一首
                self.play_random_music()
            else:
                # 继续播放当前音乐
                self.player.play()
                self.is_playing = True
                logger.info("继续播放音乐")

    def on_media_status_changed(self, status):
        """媒体状态变化处理"""
        if status == QMediaPlayer.EndOfMedia:
            # 播放结束，播放下一首随机音乐
            if self.playlist:
                self.play_random_music()

    def label_mouse_press_event(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.toggle_play_pause()
            # 更新UI状态（可以添加不同状态的emoji）
            if self.is_playing:
                self.music_label.setText("⏸️")  # 暂停状态
            else:
                self.music_label.setText("🎵")  # 播放状态
        super(type(self.music_label), self.music_label).mousePressEvent(event)

    def label_enter_event(self, event):
        """鼠标进入标签事件"""
        tooltip_text = "音乐播放器"
        if self.playlist:
            tooltip_text += f"\n当前目录: {len(self.playlist)} 首音乐"
        else:
            tooltip_text += "\n未配置音乐目录或无音乐文件"

        QToolTip.showText(
            self.music_label.mapToGlobal(self.music_label.rect().center()),
            tooltip_text,
            self.music_label,
        )
        super(type(self.music_label), self.music_label).enterEvent(event)

    def label_leave_event(self, event):
        """鼠标离开标签事件"""
        QToolTip.hideText()
        super(type(self.music_label), self.music_label).leaveEvent(event)

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.player:
            self.player.stop()
            self.player = None
        event.accept()
