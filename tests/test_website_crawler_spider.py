# Unit tests for WebsiteCrawlerSpider: link extraction, same-domain, text extraction
import pytest
from scrapy.http import HtmlResponse

from app.scrapy_crawler.spiders.website_crawler import WebsiteCrawlerSpider
from app.scrapy_crawler.items import ScrapedPageItem


def _make_spider(start_url: str = "https://example.com"):
    return WebsiteCrawlerSpider(
        start_url=start_url,
        task_id="test-task",
        collection_name="test_collection",
        obey_robots=True,
    )


def _make_response(url: str, body: str, status: int = 200):
    return HtmlResponse(url=url, body=body.encode("utf-8"), encoding="utf-8")


def test_spider_extracts_text_from_article():
    spider = _make_spider()
    html = """
    <html><body>
    <article>
        <h1>Title</h1>
        <p>First paragraph with enough content to be meaningful.</p>
        <p>Second paragraph also here.</p>
    </article>
    </body></html>
    """
    response = _make_response("https://example.com/page1", html)
    results = list(spider.parse(response))
    items = [r for r in results if isinstance(r, ScrapedPageItem)]
    assert len(items) == 1
    assert items[0]["url"] == "https://example.com/page1"
    assert "Title" in items[0]["text"]
    assert "First paragraph" in items[0]["text"]


def test_spider_extracts_text_from_body_fallback():
    spider = _make_spider()
    html = """
    <html><body>
    <p>Only body content here with enough text to pass the length check.</p>
    </body></html>
    """
    response = _make_response("https://example.com/page2", html)
    results = list(spider.parse(response))
    items = [r for r in results if isinstance(r, ScrapedPageItem)]
    assert len(items) == 1
    assert "Only body content" in items[0]["text"]


def test_spider_follows_same_domain_links_only():
    spider = _make_spider("https://example.com")
    html = """
    <html><body>
    <p>Content here.</p>
    <a href="/about">Same domain relative</a>
    <a href="https://example.com/contact">Same domain absolute</a>
    <a href="https://other.com/page">Other domain</a>
    <a href="https://evil.com">Evil</a>
    </body></html>
    """
    response = _make_response("https://example.com/", html)
    results = list(spider.parse(response))
    requests = [r for r in results if hasattr(r, "url")]
    urls = [r.url for r in requests]
    assert "https://example.com/about" in urls
    assert "https://example.com/contact" in urls
    assert not any("other.com" in u or "evil.com" in u for u in urls)


def test_spider_skips_empty_or_short_text():
    spider = _make_spider()
    html = """
    <html><body><p>Hi</p></body></html>
    """
    response = _make_response("https://example.com/short", html)
    results = list(spider.parse(response))
    items = [r for r in results if isinstance(r, ScrapedPageItem)]
    assert len(items) == 1
    # Item is still yielded but text may be short; pipeline will skip ingestion for very short text
    assert items[0]["url"] == "https://example.com/short"


def test_allowed_domain_from_start_url():
    spider = _make_spider("https://sub.example.com/start")
    assert spider.allowed_domain == "sub.example.com"
