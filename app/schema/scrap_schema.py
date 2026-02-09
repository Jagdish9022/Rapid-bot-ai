from typing import Optional
from pydantic import BaseModel


class ScrapeRequest(BaseModel):
    url: str
    collection_name: str
    chatbot_name: Optional[str] = None
    """If True, respect robots.txt; if False, crawl regardless (override)."""
    obey_robots: Optional[bool] = True  

class FileUploadRequest(BaseModel):
    collection_name: str  # Now required from frontend
