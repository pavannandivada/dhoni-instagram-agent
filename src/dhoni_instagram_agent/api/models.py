from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dhoni_instagram_agent.rag.models import GroundedEvidence


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


class RagGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


class RagCriticRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caption: str = Field(min_length=1)
    evidence: list[GroundedEvidence]
