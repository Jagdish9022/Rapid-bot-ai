# Scraping entry point: delegates to Scrapy-based crawler
import logging

from app.scrapy_crawler.runner import run_scrapy_crawl

logger = logging.getLogger(__name__)


def process_scraping_sync(url: str, task_id: str, collection_name: str, obey_robots: bool = True):
    """
    Process scraping with Scrapy: crawl same-domain pages, chunk, embed, ingest to Qdrant.
    Runs in thread; progress and cancellation are handled inside run_scrapy_crawl.
    """
    run_scrapy_crawl(
        url=url,
        task_id=task_id,
        collection_name=collection_name,
        obey_robots=obey_robots,
    )
