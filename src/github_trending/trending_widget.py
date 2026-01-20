from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QSize, QRect, Signal
from PySide6.QtGui import QFont, QPixmap, QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from github_trending.trending_service import (
    TrendingOptions,
    has_success_cache_all_periods,
    load_cached_items,
    load_latest_cached_items,
    summaries_complete,
)
from github_trending.trending_worker import TrendingWorker
from utils.config_manager import ConfigManager
from utils.logger import logger


class GithubTrendingPopup(QWidget):
    period_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.items = []
        self.since = "daily"
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

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)

        filter_label = QLabel("Period:")
        filter_layout.addWidget(filter_label)

        self.period_combo = QComboBox()
        self.period_combo.addItem("Today", "daily")
        self.period_combo.addItem("This week", "weekly")
        self.period_combo.addItem("This month", "monthly")
        self.period_combo.setCurrentIndex(0)
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        filter_layout.addWidget(self.period_combo, 1)
        layout.addLayout(filter_layout)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        self.repo_list = QListWidget()
        self.repo_list.setFixedWidth(180)
        self.repo_list.currentRowChanged.connect(self.on_repo_changed)
        self.repo_list.setAutoFillBackground(False)
        self.repo_list.setAttribute(Qt.WA_TranslucentBackground)
        self.repo_list.viewport().setAutoFillBackground(False)
        self.repo_list.viewport().setAttribute(Qt.WA_TranslucentBackground)
        content_layout.addWidget(self.repo_list)

        self.readme_view = QTextBrowser()
        self.readme_view.setOpenExternalLinks(True)
        self.readme_view.setFont(QFont("Consolas", 9))
        self.readme_view.setAutoFillBackground(False)
        self.readme_view.setAttribute(Qt.WA_TranslucentBackground)
        self.readme_view.viewport().setAutoFillBackground(False)
        self.readme_view.viewport().setAttribute(Qt.WA_TranslucentBackground)
        content_layout.addWidget(self.readme_view, 1)

        layout.addLayout(content_layout, 1)

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

    def on_period_changed(self, _index: int):
        since = self.period_combo.currentData()
        if isinstance(since, str) and since:
            self.since = since
            self.period_changed.emit(since)

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
        self.readme_view.setMarkdown(self._build_display_markdown(item))

    def _load_text(self, path_str: str) -> str | None:
        try:
            p = Path(path_str)
            if not p.exists():
                return None
            return p.read_text(encoding="utf-8")
        except Exception:
            return None

    def _build_display_markdown(self, item: dict) -> str:
        full_name = str(item.get("full_name") or "")
        url = str(item.get("url") or "")
        description = str(item.get("description") or "")
        language = str(item.get("language") or "")
        stars = item.get("stars")
        forks = item.get("forks")
        stars_today = item.get("stars_today")

        readme_content: str | None = None
        summary_path = item.get("readme_path")
        if isinstance(summary_path, str) and summary_path:
            readme_content = self._load_text(summary_path)
        if not (isinstance(readme_content, str) and readme_content.strip()):
            readme_md = item.get("readme_md")
            if isinstance(readme_md, str) and readme_md.strip():
                readme_content = readme_md

        if not (isinstance(readme_content, str) and readme_content.strip()):
            raw_path = item.get("readme_raw_path")
            if isinstance(raw_path, str) and raw_path:
                try:
                    raw_p = Path(raw_path)
                    date_dir = raw_p.parent.name
                    base = raw_p.parents[2]
                    guessed_summary = base / "readme_summary" / date_dir / raw_p.name
                    readme_content = self._load_text(str(guessed_summary))
                except Exception:
                    readme_content = None
                if not (isinstance(readme_content, str) and readme_content.strip()):
                    readme_content = self._load_text(raw_path)

        if not (isinstance(readme_content, str) and readme_content.strip()):
            legacy = item.get("readme")
            if isinstance(legacy, str) and legacy.strip():
                return legacy
            readme_content = ""

        lines: list[str] = []
        if full_name:
            lines.append(f"# {full_name}")
        if url:
            lines.append(url)
            lines.append("")

        meta_parts: list[str] = []
        if language:
            meta_parts.append(f"Language: {language}")
        if isinstance(stars, int):
            meta_parts.append(f"Stars: {stars:,}")
        if isinstance(forks, int):
            meta_parts.append(f"Forks: {forks:,}")
        if isinstance(stars_today, int):
            meta_parts.append(f"Stars today: {stars_today:,}")
        if meta_parts:
            lines.append(" - " + "\n - ".join(meta_parts))
            lines.append("")
        if description:
            lines.append(description)
            lines.append("")

        lines.append("## README")
        lines.append("")
        if readme_content.strip():
            lines.append(readme_content.strip())
            lines.append("")
        else:
            lines.append("_README 未获取到（可能是无 README / 触发了 GitHub API 限流 / 网络错误）_")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def show_at_position(self, pos):
        self.move(pos)
        self.show()


class GithubTrendingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.popup = GithubTrendingPopup()
        self.popup.period_changed.connect(self.on_popup_period_changed)
        self.popup_visible = False
        self.worker = None
        self.options = TrendingOptions(since=self.popup.since)
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
        items = load_cached_items(options=self.options) or load_latest_cached_items()
        if items:
            self.popup.set_items(items)
            return

        self.popup.set_items([self._placeholder_item()])

    def _placeholder_item(self, message: str | None = None) -> dict:
        since = self.options.since
        period_map = {"daily": "Today", "weekly": "This week", "monthly": "This month"}
        period = period_map.get(since, since)
        tip = message or "尚未缓存 Trending 数据，首次打开时将自动抓取。"
        return {
            "full_name": "GitHub Trending",
            "url": "https://github.com/trending",
            "language": "",
            "stars": "",
            "description": tip,
            "readme": f"# GitHub Trending ({period})\n\n{tip}\n",
        }

    def trigger_mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            if self.popup_visible:
                self.hide_popup()
            else:
                self.show_popup()
        super(type(self.trigger), self.trigger).mousePressEvent(event)

    def show_popup(self):
        anchor = self.mapToGlobal(self.rect().center())
        screen = QGuiApplication.screenAt(anchor) or QGuiApplication.primaryScreen()
        available: QRect = screen.availableGeometry()

        window_config = self.config_manager.get_window_config()
        margin_config = window_config.get("margin", {})
        left_margin = margin_config.get("left", 2)

        popup_size = self.popup.size()
        popup_w = popup_size.width() or self.popup.width()
        popup_h = popup_size.height() or self.popup.height()

        x = available.left() + left_margin
        y = available.top() + max(0, (available.height() - popup_h) // 2)

        max_x = available.right() - popup_w + 1
        max_y = available.bottom() - popup_h + 1
        x = max(available.left(), min(x, max_x))
        y = max(available.top(), min(y, max_y))

        self.popup.show_at_position(QPoint(x, y))
        self.popup_visible = True
        self.refresh_if_needed()

    def refresh_if_needed(self):
        cached = load_cached_items(options=self.options)
        if cached is not None:
            self.popup.set_items(cached)

        all_cached = has_success_cache_all_periods(language=self.options.language)
        all_summaries = True
        for since in ("daily", "weekly", "monthly"):
            if not summaries_complete(options=TrendingOptions(since=since, language=self.options.language)):
                all_summaries = False
                break
        if all_cached and all_summaries:
            logger.info("GitHub Trending: 今日缓存已全部存在且总结完成，跳过抓取")
            return
        if self.worker and self.worker.isRunning():
            logger.info("GitHub Trending: 抓取线程运行中，跳过重复启动")
            return

        logger.info("GitHub Trending: 今日缓存不完整或总结未完成，开始后台处理（daily/weekly/monthly）")
        self.worker = TrendingWorker(options=self.options)
        self.worker.items_ready.connect(self.on_items_ready)
        self.worker.error_occurred.connect(self.on_fetch_error)
        self.worker.start()

    def on_items_ready(self, items, updated: bool):
        sender = self.sender()
        sender_options = getattr(sender, "options", None)
        if isinstance(sender_options, TrendingOptions) and sender_options != self.options:
            self.refresh_if_needed()
            return
        logger.info(
            f"GitHub Trending: UI 刷新 items={len(items)}, updated={updated}, since={self.options.since}"
        )
        self.popup.set_items(items)

    def on_fetch_error(self, message: str):
        sender = self.sender()
        sender_options = getattr(sender, "options", None)
        if isinstance(sender_options, TrendingOptions) and sender_options != self.options:
            self.refresh_if_needed()
            return
        logger.error(f"GitHub Trending: {message}")
        if (
            self.popup.items
            and not (
                len(self.popup.items) == 1
                and (self.popup.items[0].get("full_name") or "") == "GitHub Trending"
            )
        ):
            return
        self.popup.set_items([self._placeholder_item(message=message)])

    def on_popup_period_changed(self, since: str):
        self.options = TrendingOptions(since=since)
        cached = load_cached_items(options=self.options)
        if cached is not None:
            self.popup.set_items(cached)
        else:
            self.popup.set_items([self._placeholder_item()])
        self.refresh_if_needed()

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

