from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GroundedEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str
    collection: str
    content: str
    source_url: str | None
    verification_status: str
    score: float


class CriticResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    issues: list[str]


class RagGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


class RagGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: str
    caption: str
    grounded: bool
    evidence: list[GroundedEvidence]
    evidence_ids: list[str]
    notes: list[str]


class RagCriticRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caption: str = Field(min_length=1)
    evidence: list[GroundedEvidence]


class RagCriticResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    issues: list[str]
