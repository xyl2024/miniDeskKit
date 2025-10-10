import re
from urllib.parse import urljoin, urlparse
from typing import Set, Optional
import asyncio
from pathlib import Path


def is_same_domain(url: str, base_url: str) -> bool:
    """判断URL是否与基础URL同域"""
    base_domain = urlparse(base_url).netloc
    target_domain = urlparse(url).netloc
    return base_domain == target_domain


def normalize_url(url: str) -> str:
    """标准化URL，移除锚点和查询参数"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def extract_links(html_content: str, base_url: str) -> Set[str]:
    """从HTML内容中提取所有链接"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")
    links = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(base_url, href)
        if is_same_domain(full_url, base_url):
            normalized_url = normalize_url(full_url)
            if normalized_url != base_url:  # 排除当前页面的链接
                links.add(normalized_url)

    return links


def clean_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, "_", filename)[:200]  # 限制长度
