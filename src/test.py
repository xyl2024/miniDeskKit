import asyncio
from web_crawl.web_crawler import AsyncDocumentationCrawler


async def main():
    crawler = AsyncDocumentationCrawler(
        base_url="https://doc.agentscope.io/zh_CN/index.html",
        output_dir="crawled_docs",
        max_concurrent=1,
        delay=0.2,
        max_pages=100  # 可选：限制爬取页面数量
    )
    
    await crawler.crawl()
    
    stats = crawler.get_crawl_stats()
    print(f"Statistics: {stats}")

if __name__ == "__main__":
    asyncio.run(main())