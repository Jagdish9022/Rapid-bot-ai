# Scrapy items for website crawler
import scrapy


class ScrapedPageItem(scrapy.Item):
    """Item representing a scraped page for Qdrant ingestion."""
    url = scrapy.Field()
    text = scrapy.Field()
