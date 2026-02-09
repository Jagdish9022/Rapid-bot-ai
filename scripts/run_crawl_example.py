"""
Minimal example: run Scrapy crawl from Python (same as FastAPI does in a thread).

Usage (from project root):
  python -m scripts.run_crawl_example

Requires: task_id and collection_name to be set; progress is stored in
app.utils.task_management.scraping_progress[task_id].
"""
import hashlib
from datetime import datetime

from app.utils.task_management import scraping_progress, progress_lock, update_progress_safely
from app.scrapy_crawler.runner import run_scrapy_crawl


def main():
    url = "https://example.com"
    collection_name = "example_crawl"
    task_id = hashlib.md5(f"{url}_{collection_name}_{datetime.now().timestamp()}".encode()).hexdigest()

    with progress_lock:
        scraping_progress[task_id] = {
            "status": "queued",
            "start_time": datetime.now(),
            "last_update": datetime.now(),
            "pages_scraped": 0,
            "chunks_created": 0,
            "error": None,
            "is_completed": False,
            "collection_name": collection_name,
            "url": url,
        }

    print(f"Starting crawl: {url} -> collection {collection_name}, task_id={task_id}")
    run_scrapy_crawl(url=url, task_id=task_id, collection_name=collection_name, obey_robots=True)
    progress = scraping_progress.get(task_id, {})
    print(f"Done: status={progress.get('status')}, pages={progress.get('pages_scraped')}, chunks={progress.get('chunks_created')}")


if __name__ == "__main__":
    main()
