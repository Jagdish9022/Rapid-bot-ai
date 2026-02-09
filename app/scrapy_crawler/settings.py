# Scrapy settings for app.scrapy_crawler
# Used when running via CrawlerProcess with optional overrides (task_id, collection_name, robots)

BOT_NAME = "baap_ai_crawler"

SPIDER_MODULES = ["app.scrapy_crawler.spiders"]
NEWSPIDER_MODULE = "app.scrapy_crawler.spiders"

# Obey robots.txt by default; override via custom settings when starting crawl
ROBOTSTXT_OBEY = True

# Concurrency: fast but respectful
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 0
RANDOMIZE_DOWNLOAD_DELAY = True

# AutoThrottle for adaptive speed and politeness
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 3.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

# Timeouts and retries
DOWNLOAD_TIMEOUT = 15
RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Request fingerprinting for duplicate filtering (same URL = duplicate)
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
DUPEFILTER_DEBUG = False

# Pipelines (order matters)
ITEM_PIPELINES = {
    "app.scrapy_crawler.pipelines.QdrantIngestionPipeline": 400,
}

# Middleware order: our custom ones + Scrapy defaults
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware": 100,
    "app.scrapy_crawler.middlewares.RotatingUserAgentMiddleware": 400,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
}

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

# Custom keys passed when starting crawl (set in runner, read in spider/pipeline)
SCRAPY_TASK_ID = None
SCRAPY_COLLECTION_NAME = None
SCRAPY_OBEY_ROBOTS = True
