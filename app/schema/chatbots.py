from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

class ChatbotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    collection_name: str
    source_url: Optional[str] = None

class ChatbotInfo(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    collection_name: str
    source_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class UserChatbotsResponse(BaseModel):
    chatbots: List[ChatbotInfo]
    total_count: int
