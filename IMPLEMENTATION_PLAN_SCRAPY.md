# Scrapy Integration – Implementation Plan

## Overview

Replace the current synchronous `requests` + BeautifulSoup crawler with a **Scrapy-based crawler** integrated into the FastAPI backend. The pipeline remains: scrape → extract text → chunk → embed (SentenceTransformer) → ingest into Qdrant incrementally, with progress tracking and cancellation.

---

## 1. Architecture

```
FastAPI POST /api/scraping/scrape-and-ingest
    → Returns task_id immediately
    → Submits run_scrapy_crawl(url, task_id, collection_name) to ThreadPoolExecutor
        → CrawlerProcess runs in thread with custom settings (task_id, collection_name, obey_robots)
        → WebsiteCrawlerSpider starts from URL, same-domain only, follows links
        → Per page: ScrapedPageItem (url, text) → QdrantIngestionPipeline
            → clean/chunk (reuse create_chunks) → embed → ingest_to_qdrant_incremental
            → update_progress_safely(task_id, ...)
        → Cancellation: pipeline and spider check is_cancellation_requested(task_id)
    → Progress: GET /api/scraping/scraping-progress/{task_id}
    → Cancel: POST /api/scraping/stop-scraping/{task_id}
```

---

## 2. Scrapy Project Layout (inside FastAPI app)

```
app/
  scrapy_crawler/
    __init__.py
    settings.py           # Scrapy settings (concurrency, throttle, robots, pipelines)
    items.py              # ScrapedPageItem
    pipelines.py          # QdrantIngestionPipeline (chunk, embed, ingest, progress)
    middlewares.py        # RotatingUserAgentMiddleware, optional robots override
    spiders/
      __init__.py
      website_crawler.py  # WebsiteCrawlerSpider (start_url, same domain, link following)
  utils/
    scraping_utils.py     # Updated: process_scraping_sync → run_scrapy_crawl
```

No separate `scrapy startproject`; we use `CrawlerProcess(settings)` and import spider by class.

---

## 3. Components

### 3.1 Spider: `WebsiteCrawlerSpider`

- **Start**: Single start URL (passed via `crawl(spider, start_url=..., task_id=..., collection_name=..., obey_robots=...)`).
- **Same domain**: Parse `urlparse(start_url).netloc`, allow only links with same `netloc`.
- **Link extraction**: Use `response.css('a[href]::attr(href)').getall()` and `urljoin(response.url, href)`; filter by domain and `should_skip_url`.
- **Duplicate URLs**: Rely on Scrapy’s `DUPEFILTER` (in-memory set).
- **Text extraction**: Use `response.css()` / `response.xpath()` to get main content (e.g. `article`, `main`, `[role="main"]`, fallback `body`), then `parsel`/selector `getall()` + join and clean (strip, collapse whitespace).
- **Yield**: One `ScrapedPageItem` per page (url, full_text); for each discovered same-domain link, yield `scrapy.Request(url, callback=self.parse, dont_filter=False)`.

### 3.2 Items

- `ScrapedPageItem`: `url`, `text` (raw extracted text from page).

### 3.3 Pipeline: `QdrantIngestionPipeline`

- **Input**: `ScrapedPageItem` with `url`, `text`.
- **task_id / collection_name**: Read from `spider.task_id`, `spider.collection_name` (set in spider `__init__` from crawl kwargs).
- **Flow**:
  1. If `is_cancellation_requested(task_id)`: drop item, return.
  2. Optional light clean of `text` (reuse logic from `clean_text` if needed; spider can already yield cleaned text).
  3. Chunk: `create_chunks(text, chunk_size=1000, overlap=200)` from `app.utils.common`.
  4. If no chunks: return.
  5. Embed: load SentenceTransformer once per pipeline (e.g. in `open_spider` or module-level), `model.encode(chunks).tolist()`.
  6. `ingest_to_qdrant_incremental(collection_name, texts=chunks, embeddings=embeddings, task_id=task_id, progress_callback=...)`.
  7. In `progress_callback`: call `update_progress_safely(task_id, "processing", pages_scraped=..., chunks_created=..., message=...)`.
  8. After each item: `update_progress_safely(task_id, "crawling", pages_scraped=..., chunks_created=...)`.
- **Cancellation**: Before chunking/embedding/ingestion, check `is_cancellation_requested(task_id)`; if true, raise `CancellationException` or stop processing so spider can close cleanly.

### 3.4 Scrapy Settings

- **Concurrency**: `CONCURRENT_REQUESTS = 16`, `CONCURRENT_REQUESTS_PER_DOMAIN = 8`.
- **AutoThrottle**: `AUTOTHROTTLE_ENABLED = True`, `AUTOTHROTTLE_START_DELAY`, `AUTOTHROTTLE_MAX_DELAY`, `AUTOTHROTTLE_TARGET_CONCURRENCY`.
- **Robots**: `ROBOTSTXT_OBEY = True` by default; override via custom setting from request (e.g. `obey_robots=False` in crawl kwargs → settings override).
- **Middleware**: `RotatingUserAgentMiddleware` (rotate User-Agent per request); optional proxy list if needed later.
- **Pipelines**: `QdrantIngestionPipeline` with order 400.

### 3.5 Middlewares

- **RotatingUserAgentMiddleware**: Set `request.headers['User-Agent']` to a random browser string from a list.
- **Robots override**: If custom setting `ROBOTSTXT_OBEY = False`, ensure `RobotsTxtMiddleware` is disabled or bypassed (e.g. by not downloading robots.txt when obey_robots=False).

### 3.6 FastAPI Integration

- **Endpoint**: Keep `POST /api/scraping/scrape-and-ingest`; body unchanged (`ScrapeRequest`: url, collection_name).
- **Optional**: Extend `ScrapeRequest` with `obey_robots: Optional[bool] = True`.
- **Flow**:
  1. Generate `task_id` (same as now).
  2. Initialize progress with `update_progress_safely` / `scraping_progress[task_id] = {...}`.
  3. Submit `run_scrapy_crawl(req.url, task_id, collection_name, obey_robots=getattr(req, 'obey_robots', True))` to existing `ThreadPoolExecutor`.
  4. Return `{ "task_id", "status": "queued", "collection_name", "message": "..." }`.
- **run_scrapy_crawl** (in `scraping_utils.py` or new `app/scrapy_crawler/runner.py`):
  - Build settings dict: base from `scrapy_crawler.settings`, override with `SCRAPY_TASK_ID`, `SCRAPY_COLLECTION_NAME`, `ROBOTSTXT_OBEY`.
  - `CrawlerProcess(settings).crawl(WebsiteCrawlerSpider, start_url=url, task_id=task_id, collection_name=collection_name, obey_robots=obey_robots)`.
  - `process.start()` (blocking; runs in thread).
  - On finish: set final progress (completed/cancelled/error) if not already set by pipeline/signals.

### 3.7 Progress and Cancellation

- **Progress**: Pipeline calls `update_progress_safely(task_id, status, pages_scraped, chunks_created, message)` after each page and in ingestion callback.
- **Signals**: Use `spider_closed` to set final status (e.g. "completed") and total pages/chunks; on `CancellationException` or cancellation flag, set "cancelled".
- **Cancellation**: Crawler doesn’t poll HTTP; cancellation is checked in pipeline and in a custom download middleware or spider (e.g. before yielding requests). Simplest: check only in pipeline; when cancellation is requested, pipeline raises and spider eventually closes. Optionally add a periodic check in spider (e.g. in parse) via `is_cancellation_requested(spider.task_id)` and close spider.

### 3.8 Replace BeautifulSoup with Scrapy Selectors

- In spider: use only `response.css()` and `response.xpath()` for links and text.
- Text: e.g. `response.css('article, main, [role="main"], .content, .post').getall()` or `response.xpath('//article//text() | //main//text() | //p//text()').getall()`, then join and clean.
- Reuse `should_skip_url` from `app.utils.common` for link filtering.

---

## 4. File Checklist

| File | Purpose |
|------|--------|
| `requirements.txt` | Add `scrapy` |
| `app/scrapy_crawler/__init__.py` | Package init |
| `app/scrapy_crawler/settings.py` | Scrapy settings |
| `app/scrapy_crawler/items.py` | ScrapedPageItem |
| `app/scrapy_crawler/pipelines.py` | QdrantIngestionPipeline |
| `app/scrapy_crawler/middlewares.py` | User-Agent rotation, robots override |
| `app/scrapy_crawler/spiders/__init__.py` | Spiders package |
| `app/scrapy_crawler/spiders/website_crawler.py` | WebsiteCrawlerSpider |
| `app/scrapy_crawler/runner.py` | run_scrapy_crawl() for use from FastAPI |
| `app/utils/scraping_utils.py` | Switch to run_scrapy_crawl instead of sync loop |
| `app/api/routes/scraping.py` | No change to endpoint contract; internal call to new runner |
| `app/schema/scrap_schema.py` | Optional: add obey_robots |
| Tests | Unit tests for spider (link/text extraction), pipeline (chunk+ingest flow) |

---

## 5. Run Example

**From FastAPI (automatic):**  
POST `/api/scraping/scrape-and-ingest` with `{"url": "https://example.com", "collection_name": "my_collection"}` returns `task_id`. Then poll GET `/api/scraping/scraping-progress/{task_id}` or cancel with POST `/api/scraping/stop-scraping/{task_id}`.

**Standalone script (same as FastAPI does in a thread):**
```bash
# From project root
python -m scripts.run_crawl_example
```
Or in code:
```python
from app.scrapy_crawler.runner import run_scrapy_crawl
run_scrapy_crawl(
    url="https://example.com",
    task_id="abc123",
    collection_name="my_collection",
    obey_robots=True,
)
# Progress: GET /api/scraping/scraping-progress/abc123
# Cancel: POST /api/scraping/stop-scraping/abc123
```

**Progress updates:** Implemented in `QdrantIngestionPipeline.process_item()` via `update_progress_safely(task_id, "crawling" | "processing", pages_scraped=..., chunks_created=..., message=...)`. No extra Scrapy signals required for progress; cancellation is handled by `CloseSpider(reason="cancelled")` when `is_cancellation_requested(task_id)` is True.

---

## 6. Unit Tests

- **Spider**: Test that from a mock response (same-domain and external links), only same-domain links are requested; test that text is extracted from body/article.
- **Pipeline**: Test that an item with `url` and `text` results in chunks and a call to `ingest_to_qdrant_incremental` (mock Qdrant and embeddings); test cancellation (mock `is_cancellation_requested` True, assert no ingestion).

This plan keeps the existing ingestion and progress APIs unchanged while making the crawler fast, scalable, and maintainable with Scrapy.
