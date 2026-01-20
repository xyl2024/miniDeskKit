from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from utils.logger import logger

from github_trending.trending_service import TrendingOptions, fetch_and_cache_daily


class TrendingWorker(QThread):
    items_ready = Signal(list, bool)
    error_occurred = Signal(str)

    def __init__(self, options: TrendingOptions | None = None):
        super().__init__()
        self.options = options or TrendingOptions()

    def run(self):
        try:
            logger.info(
                f"开始获取 GitHub Trending: since={self.options.since}, language={self.options.language}"
            )
            items, updated = fetch_and_cache_daily(options=self.options)
            logger.info(
                f"获取 GitHub Trending 完成: count={len(items)}, updated={updated}"
            )
            self.items_ready.emit(items, updated)
        except Exception as e:
            msg = f"获取 GitHub Trending 失败: {e}"
            logger.error(msg)
            self.error_occurred.emit(msg)
