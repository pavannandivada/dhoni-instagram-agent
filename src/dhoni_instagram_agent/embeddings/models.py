from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EmbeddingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    dimension: int
    values: list[float]


class RetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str
    collection: str
    content: str
    title: str | None
    source_url: str | None
    verification_status: str
    score: float
