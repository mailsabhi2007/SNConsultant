"""Chat request/response models."""

from typing import Optional, Any, Dict, List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[int] = None
    is_cached: bool = False
    judge_result: Optional[Dict[str, Any]] = None


class ConversationSummary(BaseModel):
    conversation_id: int
    title: Optional[str] = None
    started_at: str
    last_activity: str
    message_count: int


class ConversationDetail(BaseModel):
    conversation_id: int
    title: Optional[str] = None
    started_at: str
    last_activity: str
    message_count: int
    messages: List[Dict[str, Any]]
