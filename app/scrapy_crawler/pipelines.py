# Scrapy pipeline: chunk -> embed -> ingest to Qdrant with progress
import logging
from sentence_transformers import SentenceTransformer
from scrapy.exceptions import CloseSpider

from app.utils.common import create_chunks
from app.db.qdrant import ingest_to_qdrant_incremental, is_cancellation_requested
from app.utils.task_management import update_progress_safely

logger = logging.getLogger(__name__)

# One model instance shared across pipeline (lazy load)
_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


class QdrantIngestionPipeline:
    """
    For each scraped page item: clean text -> chunk -> embed -> ingest to Qdrant.
    Updates progress via update_progress_safely and supports cancellation.
    """

    def open_spider(self, spider):
        spider.pipeline_pages_processed = 0
        spider.pipeline_chunks_created = 0
        _get_embedding_model()

    def process_item(self, item, spider):
        task_id = getattr(spider, "task_id", None)
        collection_name = getattr(spider, "collection_name", None)
        if not task_id or not collection_name:
            logger.warning("Pipeline: missing task_id or collection_name on spider, skipping item")
            return item

        if is_cancellation_requested(task_id):
            raise CloseSpider(reason="cancelled")

        url = item.get("url", "")
        text = (item.get("text") or "").strip()
        if not text or len(text) < 20:
            spider.pipeline_pages_processed += 1
            update_progress_safely(
                task_id,
                "crawling",
                message=f"Processed page (no content): {url}",
                pages_scraped=spider.pipeline_pages_processed,
                chunks_created=spider.pipeline_chunks_created,
            )
            return item

        chunks = create_chunks(text, chunk_size=1000, overlap=200)
        if not chunks:
            spider.pipeline_pages_processed += 1
            update_progress_safely(
                task_id,
                "crawling",
                message=f"Crawled {spider.pipeline_pages_processed} pages, {spider.pipeline_chunks_created} chunks",
                pages_scraped=spider.pipeline_pages_processed,
                chunks_created=spider.pipeline_chunks_created,
            )
            return item

        if is_cancellation_requested(task_id):
            raise CloseSpider(reason="cancelled")

        model = _get_embedding_model()
        embeddings = model.encode(chunks).tolist()

        if is_cancellation_requested(task_id):
            raise CloseSpider(reason="cancelled")

        def progress_callback(stored, total, msg):
            update_progress_safely(
                task_id,
                "processing",
                message=msg,
                pages_scraped=spider.pipeline_pages_processed,
                chunks_created=spider.pipeline_chunks_created + stored,
            )

        result = ingest_to_qdrant_incremental(
            collection_name=collection_name,
            texts=chunks,
            embeddings=embeddings,
            task_id=task_id,
            progress_callback=progress_callback,
        )
        ingested = result.get("ingested_points", 0)
        spider.pipeline_chunks_created += ingested
        spider.pipeline_pages_processed += 1

        update_progress_safely(
            task_id,
            "crawling",
            message=f"Crawled {spider.pipeline_pages_processed} pages, {spider.pipeline_chunks_created} chunks",
            pages_scraped=spider.pipeline_pages_processed,
            chunks_created=spider.pipeline_chunks_created,
        )
        logger.info(
            f"Task {task_id}: page {spider.pipeline_pages_processed}, +{ingested} chunks, total {spider.pipeline_chunks_created}"
        )
        return item
