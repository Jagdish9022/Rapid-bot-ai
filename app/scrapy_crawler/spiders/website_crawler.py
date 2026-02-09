# Website crawler spider: same-domain, recursive, no duplicates
import re
import logging
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.http import Request

from app.scrapy_crawler.items import ScrapedPageItem
from app.utils.common import should_skip_url
from app.db.qdrant import is_cancellation_requested

logger = logging.getLogger(__name__)


def _extract_text_from_body(selector):
    """
    Extract clean text from response using Scrapy selectors.
    Prefer main content (article, main, .content), then fallback to body.
    Excludes script and style via XPath.
    """
    # XPath to get text but exclude script/style
    no_script_style = "//*[not(self::script or self::style)]/text()"

    # Prefer main content regions
    main_selectors = [
        "article",
        "main",
        '[role="main"]',
        ".content",
        ".post",
        ".article",
        "#content",
        "#main",
    ]
    for sel in main_selectors:
        nodes = selector.css(sel)
        if nodes:
            texts = []
            for node in nodes:
                raw = " ".join(node.xpath(no_script_style).getall())
                raw = re.sub(r"\s+", " ", raw).strip()
                if len(raw) > 20:
                    texts.append(raw)
            if texts:
                return "\n".join(texts)

    # Fallback: all text from body (excluding script/style)
    body = selector.css("body")
    if body:
        raw = " ".join(body.xpath(no_script_style).getall())
    else:
        raw = " ".join(selector.xpath(no_script_style).getall())
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


class WebsiteCrawlerSpider(scrapy.Spider):
    name = "website_crawler"
    custom_settings = {}

    def __init__(
        self,
        start_url: str,
        task_id: str,
        collection_name: str,
        obey_robots: bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.start_url = start_url
        self.start_urls = [start_url]
        self.task_id = task_id
        self.collection_name = collection_name
        self.obey_robots = obey_robots
        parsed = urlparse(start_url)
        self.allowed_domain = parsed.netloc
        if not self.allowed_domain:
            self.allowed_domain = parsed.path.split("/")[0] if parsed.path else ""

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse, dont_filter=False)

    def parse(self, response):
        if is_cancellation_requested(self.task_id):
            logger.info(f"Task {self.task_id}: cancellation requested, closing spider")
            return

        # Only process HTML
        ct = response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore")
        if "text/html" not in ct and "application/xhtml" not in ct:
            return

        # Extract text with Scrapy selectors
        text = _extract_text_from_body(response.selector)
        if not text or len(text.strip()) < 20:
            text = ""

        yield ScrapedPageItem(url=response.url, text=text)

        # Same-domain links for further crawling
        if not self.allowed_domain:
            return

        seen = set()
        for href in response.css("a[href]::attr(href)").getall():
            href = (href or "").strip()
            if not href:
                continue
            full_url = urljoin(response.url, href)
            parsed = urlparse(full_url)
            if parsed.netloc != self.allowed_domain:
                continue
            if full_url in seen:
                continue
            if should_skip_url(full_url):
                continue
            seen.add(full_url)
            if is_cancellation_requested(self.task_id):
                return
            yield Request(full_url, callback=self.parse, dont_filter=False)
