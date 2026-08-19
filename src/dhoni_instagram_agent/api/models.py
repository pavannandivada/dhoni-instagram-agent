from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class IngestionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_system: str
    source_collection: str
    records: list[dict[str, Any]]
