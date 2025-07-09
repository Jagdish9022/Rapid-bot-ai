from pydantic import BaseModel

class QARequest(BaseModel):
    question: str
    collection_name: str
