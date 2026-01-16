from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    conversation_history: List[Message] = []  # Last 5 exchanges

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    is_clarification: bool = False  # True if bot is asking for clarification
    rephrased_query: Optional[str] = None  # Shows if query was rephrased
    warnings: Optional[List[str]] = None  # Any warnings

class IndexRequest(BaseModel):
    document_id: Optional[str] = None

class IndexResponse(BaseModel):
    message: str
    chunks_indexed: int
    documents_processed: int
    total_documents: Optional[int] = None
    warnings: Optional[Dict[str, Any]] = None

class DocumentInfo(BaseModel):
    id: str
    name: str
    modified: str
    indexed: bool
