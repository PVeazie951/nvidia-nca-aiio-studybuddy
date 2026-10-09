"""Schemas for API payloads."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    size_bytes: int
    kind: str
    extracted_text: str
    extraction_error: str
    topic_id: int | None
    created_at: datetime


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    weight: int
    sort_order: int
    confidence: int


class TopicUpdate(BaseModel):
    confidence: int | None = None
    title: str | None = None
    description: str | None = None
    weight: int | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int | None
    title: str
    body: str
    source: str
    created_at: datetime


class NoteCreate(BaseModel):
    topic_id: int | None = None
    title: str = ""
    body: str = ""
    source: str = "user"


class LlmProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_url: str
    model: str
    has_key: bool = False
    is_active: bool
    temperature: float
    max_tokens: int
    prompts: dict


class LlmProfileIn(BaseModel):
    name: str = "default"
    base_url: str
    model: str = ""
    api_key: str | None = None
    is_active: bool = True
    temperature: float = 0.3
    max_tokens: int = 1500
    prompts: dict | None = None


class AiRequest(BaseModel):
    feature: str  # whiteboard | hint | explain | quiz | gap
    topic_id: int | None = None
    asset_ids: list[int] = []
    question: str = ""
    count: int = 5
    extra: str = ""


class AiResponse(BaseModel):
    feature: str
    content: str
    model: str
    elapsed_ms: int
