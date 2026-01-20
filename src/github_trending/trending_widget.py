from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QSize, QRect
from PySide6.QtGui import QFont, QPixmap, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextBrowser,
    QWidget,
)

from github_trending.trending_service import has_success_cache, load_cached_items, load_latest_cached_items
from github_trending.trending_worker import TrendingWorker
from utils.config_manager import ConfigManager
from utils.logger import logger


class GithubTrendingPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.items = []
        self.setup_window()
        self.setup_ui()

    def setup_window(self):
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setup_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.frame = QFrame()
        self.frame.setObjectName("popupFrame")
        root_layout.addWidget(self.frame)

        layout = QHBoxLayout(self.frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.repo_list = QListWidget()
        self.repo_list.setFixedWidth(180)
        self.repo_list.currentRowChanged.connect(self.on_repo_changed)
        self.repo_list.setAutoFillBackground(False)
        self.repo_list.setAttribute(Qt.WA_TranslucentBackground)
        self.repo_list.viewport().setAutoFillBackground(False)
        self.repo_list.viewport().setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(self.repo_list)

        self.readme_view = QTextBrowser()
        self.readme_view.setOpenExternalLinks(True)
        self.readme_view.setFont(QFont("Consolas", 9))
        self.readme_view.setAutoFillBackground(False)
        self.readme_view.setAttribute(Qt.WA_TranslucentBackground)
        self.readme_view.viewport().setAutoFillBackground(False)
        self.readme_view.viewport().setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(self.readme_view, 1)

        self.setStyleSheet(
            """
            QFrame#popupFrame {
                background-color: rgba(225, 240, 249, 230);
                border-radius: 6px;
            }
            QListWidget {
                background: transparent;
                border: 1px solid rgba(0, 0, 0, 25);
                border-radius: 4px;
                padding: 4px;
                outline: 0;
            }
            QListWidget::viewport {
                background: transparent;
            }
            QListWidget::item {
                padding: 6px 6px;
                border-radius: 3px;
            }
            QListWidget::item:focus {
                outline: none;
            }
            QListWidget::item:selected {
                background: rgba(60, 120, 220, 55);
            }
            QTextBrowser {
                background: transparent;
                border: 1px solid rgba(0, 0, 0, 25);
                border-radius: 4px;
                padding: 6px;
            }
            QTextBrowser::viewport {
                background: transparent;
            }
            """
        )

        self.setFixedSize(720, 420)

    def set_items(self, items):
        self.items = list(items or [])
        self.repo_list.clear()
        for item in self.items:
            full_name = item.get("full_name") or ""
            name = item.get("name") or ""
            text = name or (full_name.split("/")[-1] if "/" in full_name else full_name) or "unknown"
            self.repo_list.addItem(QListWidgetItem(text))
        if self.items:
            self.repo_list.setCurrentRow(0)
        else:
            self.on_repo_changed(-1)

    def on_repo_changed(self, row: int):
        if row < 0 or row >= len(self.items):
            self.readme_view.setPlainText("")
            return

        item = self.items[row]
        readme = item.get("readme") or ""
        self.readme_view.setMarkdown(readme)

    def show_at_position(self, pos):
        self.move(pos)
        self.show()


class GithubTrendingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.popup = GithubTrendingPopup()
        self.popup_visible = False
        self.worker = None
        self.setup_ui()
        self.load_cached_or_placeholder_data()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.trigger = QLabel()
        self.trigger.setAlignment(Qt.AlignCenter)
        self.trigger.setFixedSize(22, 22)
        self.trigger.setMouseTracking(True)
        self.trigger.mousePressEvent = self.trigger_mouse_press_event
        layout.addWidget(self.trigger)
        self.update_trigger_icon()

    def update_trigger_icon(self):
        icon_path = Path(__file__).resolve().parent / "github.png"
        pixmap = QPixmap(str(icon_path))
        if pixmap.isNull():
            self.trigger.setText("🔥")
            self.trigger.setFont(QFont("Arial", 16))
            return

        scaled = pixmap.scaled(
            QSize(18, 18),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.trigger.setPixmap(scaled)

    def load_cached_or_placeholder_data(self):
        items = load_cached_items() or load_latest_cached_items()
        if items:
            self.popup.set_items(items)
            return

        self.popup.set_items(
            [
                {
                    "full_name": "GitHub Trending",
                    "url": "https://github.com/trending",
                    "language": "",
                    "stars": "",
                    "description": "尚未缓存 Trending 数据，首次打开时将自动抓取。",
                    "readme": "# GitHub Trending\n\n首次抓取成功后，将按日期把数据保存为 Markdown。\n",
                }
            ]
        )

    def trigger_mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            if self.popup_visible:
                self.hide_popup()
            else:
                self.show_popup()
        super(type(self.trigger), self.trigger).mousePressEvent(event)

    def show_popup(self):
        widget_top_right = self.mapToGlobal(self.rect().topRight())
        widget_top_left = self.mapToGlobal(self.rect().topLeft())

        window_config = self.config_manager.get_window_config()
        margin_config = window_config.get("margin", {})
        right_margin = margin_config.get("right", 2)
        gap = right_margin + 5

        popup_pos = widget_top_right + QPoint(gap, 0)
        popup_pos = self.adjust_popup_pos(
            popup_pos,
            anchor_left_x=widget_top_left.x(),
            anchor_right_x=widget_top_right.x(),
            gap=gap,
            popup_size=self.popup.size(),
        )
        self.popup.show_at_position(popup_pos)
        self.popup_visible = True
        self.refresh_if_needed()

    def refresh_if_needed(self):
        if has_success_cache():
            logger.info("GitHub Trending: 今日缓存已存在，跳过抓取")
            return
        if self.worker and self.worker.isRunning():
            logger.info("GitHub Trending: 抓取线程运行中，跳过重复启动")
            return

        logger.info("GitHub Trending: 今日无缓存，开始后台抓取")
        self.worker = TrendingWorker()
        self.worker.items_ready.connect(self.on_items_ready)
        self.worker.error_occurred.connect(self.on_fetch_error)
        self.worker.start()

    def on_items_ready(self, items, updated: bool):
        logger.info(f"GitHub Trending: UI 刷新 items={len(items)}, updated={updated}")
        self.popup.set_items(items)

    def on_fetch_error(self, message: str):
        logger.error(f"GitHub Trending: {message}")
        if (
            self.popup.items
            and not (
                len(self.popup.items) == 1
                and (self.popup.items[0].get("full_name") or "") == "GitHub Trending"
            )
        ):
            return
        self.popup.set_items(
            [
                {
                    "full_name": "GitHub Trending",
                    "url": "https://github.com/trending",
                    "language": "",
                    "stars": "",
                    "description": "抓取失败",
                    "readme": f"# 抓取失败\n\n{message}\n",
                }
            ]
        )

    def adjust_popup_pos(
        self,
        preferred_pos: QPoint,
        anchor_left_x: int,
        anchor_right_x: int,
        gap: int,
        popup_size: QSize,
    ) -> QPoint:
        screen = QGuiApplication.screenAt(preferred_pos)
        if not screen:
            screen = QGuiApplication.primaryScreen()

        available: QRect = screen.availableGeometry()

        popup_w = popup_size.width() or self.popup.width()
        popup_h = popup_size.height() or self.popup.height()

        x = preferred_pos.x()
        y = preferred_pos.y()

        if x + popup_w > available.right() + 1:
            x = anchor_right_x - gap - popup_w

        min_x = available.left()
        max_x = available.right() - popup_w + 1
        x = max(min_x, min(x, max_x))

        min_y = available.top()
        max_y = available.bottom() - popup_h + 1
        y = max(min_y, min(y, max_y))

        return QPoint(x, y)

    def hide_popup(self):
        self.popup.hide()
        self.popup_visible = False

    def hideEvent(self, event):
        self.hide_popup()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.hide_popup()
        if event:
            event.accept()

