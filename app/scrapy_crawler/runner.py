# Run Scrapy crawl from FastAPI (blocking; call from thread)
import logging
from scrapy.crawler import CrawlerProcess

from app.scrapy_crawler.spiders.website_crawler import WebsiteCrawlerSpider
from app.utils.task_management import get_progress_safely, update_progress_safely
from app.db.qdrant import is_cancellation_requested, clear_cancellation_request, CancellationException

logger = logging.getLogger(__name__)


def _get_scrapy_settings(task_id: str, collection_name: str, obey_robots: bool):
    """Build Scrapy settings dict with task/collection and optional robots override."""
    settings = {
        "BOT_NAME": "baap_ai_crawler",
        "ROBOTSTXT_OBEY": obey_robots,
        "CONCURRENT_REQUESTS": 16,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "DOWNLOAD_DELAY": 0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 3.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 4.0,
        "DOWNLOAD_TIMEOUT": 15,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 2,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "ITEM_PIPELINES": {
            "app.scrapy_crawler.pipelines.QdrantIngestionPipeline": 400,
        },
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware": 100,
            "app.scrapy_crawler.middlewares.RotatingUserAgentMiddleware": 400,
            "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
            "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
        },
        "LOG_LEVEL": "INFO",
        "SCRAPY_TASK_ID": task_id,
        "SCRAPY_COLLECTION_NAME": collection_name,
        "SCRAPY_OBEY_ROBOTS": obey_robots,
    }
    return settings


def run_scrapy_crawl(
    url: str,
    task_id: str,
    collection_name: str,
    obey_robots: bool = True,
):
    """
    Run Scrapy crawl for one site; blocking. Call from thread (e.g. FastAPI executor).
    Sets final progress on completion/cancellation/error.
    """
    try:
        update_progress_safely(task_id, "starting", message="Initializing Scrapy crawler...")
        settings = _get_scrapy_settings(task_id, collection_name, obey_robots)
        process = CrawlerProcess(settings)

        process.crawl(
            WebsiteCrawlerSpider,
            start_url=url,
            task_id=task_id,
            collection_name=collection_name,
            obey_robots=obey_robots,
        )

        # Scrapy reactor runs until all requests are done
        process.start()

        # After reactor stops, set final progress from spider stats if available
        # (We don't have direct access to spider here; pipeline updates progress as it goes.
        # So final pages/chunks are already in scraping_progress. We just set status.)
        if is_cancellation_requested(task_id):
            update_progress_safely(
                task_id,
                "cancelled",
                message="Scraping cancelled by user",
                is_completed=True,
            )
            clear_cancellation_request(task_id)
        else:
            progress = get_progress_safely(task_id)
            update_progress_safely(
                task_id,
                "completed",
                message="Scraping completed",
                is_completed=True,
                result={
                    "status": "completed",
                    "collection_name": collection_name,
                    "total_pages": progress.get("pages_scraped", 0),
                    "total_chunks": progress.get("chunks_created", 0),
                },
            )
        logger.info(f"Task {task_id}: Scrapy crawl finished")

    except CancellationException:
        logger.info(f"Task {task_id} cancelled during crawl")
        update_progress_safely(
            task_id,
            "cancelled",
            message="Task cancelled by user",
            is_completed=True,
        )
        try:
            clear_cancellation_request(task_id)
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"Task {task_id}: Scrapy crawl error: {e}")
        update_progress_safely(
            task_id,
            "error",
            error=str(e),
            is_completed=True,
        )
