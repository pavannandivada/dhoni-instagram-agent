from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_system: str
    source_collection: str
    source_record_id: str
    source_row_number: int | None = None
    title: str | None = None
    content: str
    source_url: str | None = None
    verification_status: str = "UNVERIFIED"
    rights_status: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    normalized_payload: dict[str, Any] = Field(default_factory=dict)


class QuoteRecord(SourceRecord):
    quote_id: str
    quote: str
    context: str | None = None
    source: str | None = None
    quote_date: date | None = None
    verified: bool = False
    used: bool = False


class FactRecord(SourceRecord):
    fact_id: str
    category: str
    fact: str
    format: str | None = None
    source: str | None = None
    verified_date: date | None = None
    verified: bool = False
    used: bool = False


class AssetRecord(SourceRecord):
    asset_id: str
    asset_type: str
    category: str | None = None
    drive_file_id: str | None = None
    file_name: str
    creator: str | None = None
    license: str | None = None
    verified: bool = False
    used: bool = False
    last_used: datetime | None = None
    aspect_ratio: float | None = None
    width: int | None = None
    height: int | None = None
    checksum: str | None = None


class SpecialEventRecord(SourceRecord):
    event_id: str
    event_date: date
    event_type: str
    description: str
    priority: int = 0
    used: bool = False
    used_at: datetime | None = None
