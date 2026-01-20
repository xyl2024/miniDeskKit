from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from utils.logger import logger

from github_trending.trending_service import (
    TrendingOptions,
    fetch_and_cache_daily,
    load_cached_items,
)


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
            items, updated_any = fetch_and_cache_daily(options=self.options)
            for since in ("daily", "weekly", "monthly"):
                if since == self.options.since:
                    continue
                try:
                    _, updated = fetch_and_cache_daily(
                        options=TrendingOptions(since=since, language=self.options.language)
                    )
                    updated_any = updated_any or updated
                except Exception as e:
                    logger.warning(f"预取 GitHub Trending 失败: since={since} ({e})")

            items = load_cached_items(options=self.options) or items or []
            logger.info(
                f"获取 GitHub Trending 完成: count={len(items)}, updated={updated_any}"
            )
            self.items_ready.emit(items, updated_any)
        except Exception as e:
            msg = f"获取 GitHub Trending 失败: {e}"
            logger.error(msg)
            self.error_occurred.emit(msg)
