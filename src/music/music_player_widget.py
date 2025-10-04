from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QToolTip,
    QVBoxLayout,
    QPushButton,
    QSlider,
    QLayout,
)
from PySide6.QtCore import Qt, QUrl, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PySide6.QtGui import QFont, QPalette
import os
import random
from pathlib import Path

from utils.config_manager import ConfigManager
from utils.logger import logger

from music.music_detail_widget import MusicDetailWidget


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

        # 添加动画相关属性
        self.animation = None
        self.animation_group = None

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

        # 创建音乐详情界面
        self.detail_widget = MusicDetailWidget(self)
        # 设置初始透明度为0（完全透明/隐藏）
        self.detail_widget.setWindowOpacity(0.0)

    def setup_player(self):
        """设置音频播放器"""
        try:
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

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

                # 更新音乐详情界面的歌曲信息
                self.detail_widget.update_song_info(music_file)
            except Exception as e:
                logger.error(f"播放音乐失败: {e}")
        else:
            logger.error("音频播放器未初始化")

    def play_next_music(self):
        """播放下一首音乐"""
        if not self.playlist:
            logger.warning("没有找到音乐文件")
            return

        # 选择下一首（循环播放）
        self.current_index = (self.current_index + 1) % len(self.playlist)
        music_file = self.playlist[self.current_index]

        if self.player:
            try:
                url = QUrl.fromLocalFile(music_file)
                self.player.setSource(url)
                self.player.play()
                self.is_playing = True
                logger.info(f"开始播放: {os.path.basename(music_file)}")

                # 更新音乐详情界面的歌曲信息
                self.detail_widget.update_song_info(music_file)
            except Exception as e:
                logger.error(f"播放音乐失败: {e}")
        else:
            logger.error("音频播放器未初始化")

    def play_prev_music(self):
        """播放上一首音乐"""
        if not self.playlist:
            logger.warning("没有找到音乐文件")
            return

        # 选择上一首（循环播放）
        self.current_index = (self.current_index - 1) % len(self.playlist)
        music_file = self.playlist[self.current_index]

        if self.player:
            try:
                url = QUrl.fromLocalFile(music_file)
                self.player.setSource(url)
                self.player.play()
                self.is_playing = True
                logger.info(f"开始播放: {os.path.basename(music_file)}")

                # 更新音乐详情界面的歌曲信息
                self.detail_widget.update_song_info(music_file)
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
        from PySide6.QtMultimedia import QMediaPlayer

        if status == QMediaPlayer.EndOfMedia:
            # 播放结束，播放下一首随机音乐
            if self.playlist:
                self.play_next_music()

    def label_mouse_press_event(self, event):
        """鼠标点击事件 - 显示/隐藏音乐详情界面"""
        if event.button() == Qt.LeftButton:
            if self.detail_widget.isVisible():
                # 隐藏动画：从完全不透明到完全透明
                self.start_hide_animation()
            else:
                # 显示动画：从完全透明到完全不透明
                self.start_show_animation()
        super(type(self.music_label), self.music_label).mousePressEvent(event)

    def start_show_animation(self):
        """开始显示动画"""
        # 设置初始透明度为0
        self.detail_widget.setWindowOpacity(0.0)
        # 计算详情窗口的位置（相对于主窗口）
        pos = self.mapToGlobal(self.rect().topRight())
        # 向右偏移一点距离
        pos.setX(pos.x() + 5)
        self.detail_widget.move(pos)
        self.detail_widget.show()

        # 创建透明度动画
        self.animation = QPropertyAnimation(self.detail_widget, b"windowOpacity")
        self.animation.setDuration(300)  # 动画持续时间300ms
        self.animation.setStartValue(0.0)  # 开始值：完全透明
        self.animation.setEndValue(1.0)    # 结束值：完全不透明
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)  # 使用平滑的缓动曲线

        # 动画开始前的设置
        self.animation.finished.connect(self.on_show_animation_finished)
        self.animation.start()

        # 更新播放/暂停按钮状态
        if self.is_playing:
            self.detail_widget.play_pause_button.setText("⏸️")
        else:
            self.detail_widget.play_pause_button.setText("▶️")

    def start_hide_animation(self):
        """开始隐藏动画"""
        # 创建透明度动画
        self.animation = QPropertyAnimation(self.detail_widget, b"windowOpacity")
        self.animation.setDuration(300)  # 动画持续时间300ms
        self.animation.setStartValue(1.0)  # 开始值：完全不透明
        self.animation.setEndValue(0.0)    # 结束值：完全透明
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)  # 使用平滑的缓动曲线

        # 动画结束后隐藏窗口
        self.animation.finished.connect(self.on_hide_animation_finished)
        self.animation.start()

    def on_show_animation_finished(self):
        """显示动画完成后的回调"""
        # 确保最终透明度为1.0
        self.detail_widget.setWindowOpacity(1.0)

    def on_hide_animation_finished(self):
        """隐藏动画完成后的回调"""
        # 动画完成后隐藏窗口
        self.detail_widget.hide()
        # 重置透明度为1.0，为下次显示做准备
        self.detail_widget.setWindowOpacity(1.0)

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
        if self.timer:
            self.timer.stop()
        if self.player:
            self.player.stop()
            self.player = None
        if self.detail_widget:
            self.detail_widget.close()
        event.accept()