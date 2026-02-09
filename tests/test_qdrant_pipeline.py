# Unit tests for QdrantIngestionPipeline (mocked Qdrant and embeddings)
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.scrapy_crawler.pipelines import QdrantIngestionPipeline
from app.scrapy_crawler.items import ScrapedPageItem


@pytest.fixture
def spider():
    s = Mock()
    s.task_id = "test-task"
    s.collection_name = "test_collection"
    s.pipeline_pages_processed = 0
    s.pipeline_chunks_created = 0
    return s


@pytest.fixture
def pipeline():
    return QdrantIngestionPipeline()


def test_pipeline_opens_spider_sets_counters(spider, pipeline):
    pipeline.open_spider(spider)
    assert spider.pipeline_pages_processed == 0
    assert spider.pipeline_chunks_created == 0


def test_pipeline_skips_item_when_no_task_id(pipeline, spider):
    spider.task_id = None
    pipeline.open_spider(spider)
    item = ScrapedPageItem(url="https://example.com", text="Some long enough text here for chunking.")
    out = pipeline.process_item(item, spider)
    assert out == item
    assert spider.pipeline_pages_processed == 0


@patch("app.scrapy_crawler.pipelines.ingest_to_qdrant_incremental")
@patch("app.scrapy_crawler.pipelines._get_embedding_model")
@patch("app.scrapy_crawler.pipelines.is_cancellation_requested")
def test_pipeline_ingests_chunks_when_text_long_enough(
    mock_cancel, mock_model, mock_ingest, pipeline, spider
):
    mock_cancel.return_value = False
    # encode() returns array-like with .tolist()
    emb = MagicMock()
    emb.tolist.return_value = [[0.1] * 384, [0.2] * 384]
    mock_model.return_value.encode.return_value = emb
    mock_ingest.return_value = {"ingested_points": 2, "status": "completed"}
    pipeline.open_spider(spider)
    # Text long enough to create at least one chunk (create_chunks uses 1000 chunk_size)
    long_text = " ".join(["Sentence number {} here." for _ in range(80)])
    item = ScrapedPageItem(url="https://example.com", text=long_text)
    out = pipeline.process_item(item, spider)
    assert out == item
    assert mock_ingest.called
    call_kw = mock_ingest.call_args[1]
    assert call_kw["collection_name"] == "test_collection"
    assert call_kw["task_id"] == "test-task"
    assert len(call_kw["texts"]) >= 1
    assert len(call_kw["embeddings"]) == len(call_kw["texts"])
    assert spider.pipeline_pages_processed == 1
    assert spider.pipeline_chunks_created == 2


@patch("app.scrapy_crawler.pipelines.is_cancellation_requested")
def test_pipeline_raises_close_spider_on_cancellation(mock_cancel, pipeline, spider):
    from scrapy.exceptions import CloseSpider

    mock_cancel.return_value = True
    pipeline.open_spider(spider)
    item = ScrapedPageItem(url="https://example.com", text="Enough text here for processing.")
    with pytest.raises(CloseSpider) as exc_info:
        pipeline.process_item(item, spider)
    assert exc_info.value.reason == "cancelled"
