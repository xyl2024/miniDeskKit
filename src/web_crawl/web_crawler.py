import asyncio
import logging
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json
import hashlib
from typing import Set, Dict, Optional, List
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser
import re

@dataclass
class PageData:
    url: str
    title: str
    content: str
    links: List[str]
    timestamp: float

class AsyncDocumentationCrawler:
    def __init__(
        self,
        base_url: str,
        output_dir: str = "crawled_docs",
        max_concurrent: int = 10,
        delay: float = 0.1,
        max_pages: Optional[int] = None
    ):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.max_pages = max_pages
        
        self.visited_urls: Set[str] = set()
        self.to_visit: asyncio.Queue = asyncio.Queue()
        self.browser: Optional[Browser] = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _is_valid_url(self, url: str) -> bool:
        """检查URL是否有效且属于同一域名"""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc == self.base_domain and
                parsed.scheme in ['http', 'https'] and
                not any(ext in url.lower() for ext in ['.pdf', '.zip', '.exe', '.jpg', '.png', '.gif', '.css', '.js'])
            )
        except:
            return False

    def _normalize_url(self, url: str) -> str:
        """标准化URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{'?' + parsed.query if parsed.query else ''}"

    def _extract_links(self, page_content: str, current_url: str) -> List[str]:
        """从页面内容中提取所有链接"""
        # 简单的正则表达式提取链接
        link_pattern = r'<a\s+[^>]*href=["\']([^"\']*)["\'][^>]*>'
        matches = re.findall(link_pattern, page_content, re.IGNORECASE)
        
        links = []
        for match in matches:
            absolute_url = urljoin(current_url, match)
            if self._is_valid_url(absolute_url):
                normalized_url = self._normalize_url(absolute_url)
                links.append(normalized_url)
        
        return list(set(links))  # 去重

    async def _get_page_content(self, page: Page, url: str) -> Optional[PageData]:
        """获取页面内容"""
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 等待页面加载完成
            await page.wait_for_load_state("domcontentloaded")
            
            # 获取页面标题
            title = await page.title()
            
            # 获取页面HTML内容
            content = await page.content()
            
            # 提取链接
            links = self._extract_links(content, url)
            
            # 尝试提取主要内容区域（根据常见文档结构）
            main_content = await self._extract_main_content(page)
            
            return PageData(
                url=url,
                title=title,
                content=main_content or content,
                links=links,
                timestamp=asyncio.get_event_loop().time()
            )
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    async def _extract_main_content(self, page: Page) -> Optional[str]:
        """尝试提取页面主要内容"""
        # 常见的文档内容选择器
        selectors = [
            "main",
            "[role='main']",
            ".content",
            ".documentation",
            ".doc-content",
            ".main-content",
            "#content",
            ".container",
            "article"
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    content = await element.inner_html()
                    if content and len(content.strip()) > 100:  # 确保内容有意义
                        return content
            except:
                continue
        
        # 如果常见选择器都失败，返回body内容
        try:
            body_content = await page.inner_html("body")
            return body_content
        except:
            return None

    async def _save_page(self, page_data: PageData):
        """保存页面内容到文件"""
        # 创建基于URL路径的文件结构
        parsed_url = urlparse(page_data.url)
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        if not path_parts:
            path_parts = ['index']
        
        # 确保文件名安全
        safe_parts = []
        for part in path_parts:
            safe_part = re.sub(r'[<>:"/\\|?*]', '_', part)
            if safe_part:  # 避免空字符串
                safe_parts.append(safe_part)
        
        if not safe_parts:
            safe_parts = ['index']
        
        file_path = self.output_dir / Path(*safe_parts)
        
        # 如果是目录，添加index.html
        if file_path.suffix == '':
            file_path = file_path / "index.html"
        elif not file_path.suffix:
            file_path = file_path.with_suffix(".html")
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Title: {page_data.title} -->\n")
            f.write(f"<!-- URL: {page_data.url} -->\n")
            f.write(page_data.content)
        
        # 保存元数据
        meta_path = file_path.with_suffix('.json')
        meta_data = {
            "url": page_data.url,
            "title": page_data.title,
            "timestamp": page_data.timestamp,
            "links_count": len(page_data.links)
        }
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

    async def _crawl_page(self, url: str):
        """爬取单个页面"""
        async with self.semaphore:
            if url in self.visited_urls:
                return
            
            self.visited_urls.add(url)
            self.logger.info(f"Crawling: {url} (Total: {len(self.visited_urls)})")
            
            if not self.browser:
                return
            
            page = await self.browser.new_page()
            try:
                page_data = await self._get_page_content(page, url)
                if page_data:
                    await self._save_page(page_data)
                    
                    # 将新发现的链接加入队列
                    for link in page_data.links:
                        if link not in self.visited_urls:
                            await self.to_visit.put(link)
                
                await asyncio.sleep(self.delay)  # 避免过于频繁的请求
            finally:
                await page.close()

    async def _worker(self):
        """工作协程"""
        while True:
            try:
                url = await asyncio.wait_for(self.to_visit.get(), timeout=5.0)
                await self._crawl_page(url)
                self.to_visit.task_done()
            except asyncio.TimeoutError:
                break
            except Exception as e:
                self.logger.error(f"Worker error: {e}")

    async def crawl(self):
        """开始爬取"""
        async with async_playwright() as p:
            # 启动浏览器
            self.browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            try:
                # 添加起始URL
                await self.to_visit.put(self.base_url)
                
                # 创建工作协程
                workers = []
                for _ in range(self.max_concurrent):
                    worker = asyncio.create_task(self._worker())
                    workers.append(worker)
                
                # 等待队列完成或达到最大页面数
                while not self.to_visit.empty() and (self.max_pages is None or len(self.visited_urls) < self.max_pages):
                    await asyncio.sleep(0.1)
                
                # 等待所有任务完成
                await self.to_visit.join()
                
                # 取消工作协程
                for worker in workers:
                    worker.cancel()
                
                self.logger.info(f"Crawling completed. Total pages: {len(self.visited_urls)}")
                
            finally:
                await self.browser.close()

    def get_visited_urls(self) -> Set[str]:
        """获取已访问的URL集合"""
        return self.visited_urls.copy()

    def get_crawl_stats(self) -> Dict:
        """获取爬取统计信息"""
        return {
            "total_pages": len(self.visited_urls),
            "output_directory": str(self.output_dir.absolute()),
            "base_url": self.base_url
        }
