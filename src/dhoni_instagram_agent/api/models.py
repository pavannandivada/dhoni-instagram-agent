from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IngestionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_system: str
    source_collection: str
    records: list[dict[str, Any]]


class EmbeddingIndexRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=50, ge=1, le=500)


class RetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    collection: str | None = None
    top_k: int = Field(default=5, ge=1, le=50)
