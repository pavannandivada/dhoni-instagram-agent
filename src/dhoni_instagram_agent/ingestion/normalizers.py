from __future__ import annotations

from datetime import date, datetime
from typing import Any


def clean(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def parse_bool(value: Any, default: bool = False) -> bool:
    text = clean(value)
    if text is None:
        return default

    return text.lower() in {"true", "1", "yes", "y"}


def parse_date(value: Any) -> date | None:
    text = clean(value)
    if not text:
        return None

    return date.fromisoformat(text)


def parse_datetime(value: Any) -> datetime | None:
    text = clean(value)
    if not text:
        return None

    return datetime.fromisoformat(text)


def normalize_quote(row: dict[str, Any], row_number: int) -> dict[str, Any]:
    quote_id = clean(row.get("Quote ID"))
    quote = clean(row.get("Quote"))
    context = clean(row.get("Context"))
    source = clean(row.get("Source"))
    source_url = clean(row.get("Source URL"))

    return {
        "source_system": "google_sheets",
        "source_collection": "Quotes",
        "source_record_id": quote_id or f"row-{row_number}",
        "source_row_number": row_number,
        "title": quote_id,
        "content": quote or "",
        "source_url": source_url,
        "verification_status": "VERIFIED" if parse_bool(row.get("Verified")) else "UNVERIFIED",
        "rights_status": None,
        "raw_payload": row,
        "normalized_payload": {
            "quote_id": quote_id,
            "quote": quote,
            "context": context,
            "source": source,
            "source_url": source_url,
            "date": clean(row.get("Date")),
            "verified": parse_bool(row.get("Verified")),
            "used": parse_bool(row.get("Used")),
            "used_date": clean(row.get("Used Date")),
        },
    }


def normalize_fact(row: dict[str, Any], row_number: int) -> dict[str, Any]:
    fact_id = clean(row.get("Fact ID"))
    fact = clean(row.get("Fact"))
    category = clean(row.get("Category"))
    source = clean(row.get("Source"))
    source_url = clean(row.get("Source URL"))

    return {
        "source_system": "google_sheets",
        "source_collection": "Facts & Stats",
        "source_record_id": fact_id or f"row-{row_number}",
        "source_row_number": row_number,
        "title": fact_id,
        "content": fact or "",
        "source_url": source_url,
        "verification_status": "VERIFIED" if parse_bool(row.get("Verified")) else "UNVERIFIED",
        "rights_status": None,
        "raw_payload": row,
        "normalized_payload": {
            "fact_id": fact_id,
            "category": category,
            "fact": fact,
            "format": clean(row.get("Format")),
            "source": source,
            "source_url": source_url,
            "verified_date": clean(row.get("Verified Date")),
            "verified": parse_bool(row.get("Verified")),
            "used": parse_bool(row.get("Used")),
            "used_date": clean(row.get("Used Date")),
        },
    }


def normalize_asset(row: dict[str, Any], row_number: int) -> dict[str, Any]:
    asset_id = clean(row.get("Asset ID"))
    file_name = clean(row.get("File Name"))
    source_url = clean(row.get("Source URL"))
    rights_status = clean(row.get("License"))

    return {
        "source_system": "google_sheets",
        "source_collection": "Assets",
        "source_record_id": asset_id or f"row-{row_number}",
        "source_row_number": row_number,
        "title": file_name or asset_id,
        "content": file_name or "",
        "source_url": source_url,
        "verification_status": "VERIFIED" if parse_bool(row.get("Verified")) else "UNVERIFIED",
        "rights_status": rights_status,
        "raw_payload": row,
        "normalized_payload": {
            "asset_id": asset_id,
            "asset_type": clean(row.get("Asset Type")),
            "category": clean(row.get("Category")),
            "drive_file_id": clean(row.get("Drive File ID")),
            "file_name": file_name,
            "source_url": source_url,
            "creator": clean(row.get("Creator")),
            "license": clean(row.get("License")),
            "verified": parse_bool(row.get("Verified")),
            "used": parse_bool(row.get("Used")),
            "last_used": clean(row.get("Last Used")),
        },
    }


def normalize_event(row: dict[str, Any], row_number: int) -> dict[str, Any]:
    event_id = clean(row.get("Event ID"))
    description = clean(row.get("Description"))
    event_date = clean(row.get("Date"))

    return {
        "source_system": "google_sheets",
        "source_collection": "Special Events",
        "source_record_id": event_id or f"row-{row_number}",
        "source_row_number": row_number,
        "title": event_id,
        "content": description or "",
        "source_url": clean(row.get("Source URL")),
        "verification_status": "VERIFIED" if clean(row.get("Source URL")) else "UNVERIFIED",
        "rights_status": None,
        "raw_payload": row,
        "normalized_payload": {
            "event_id": event_id,
            "event_date": event_date,
            "event_type": clean(row.get("Event Type")),
            "description": description,
            "source_url": clean(row.get("Source URL")),
            "priority": clean(row.get("Priority")),
            "used": parse_bool(row.get("Used")),
            "used_date": clean(row.get("Used Date")),
        },
    }
