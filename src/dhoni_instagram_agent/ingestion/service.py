from __future__ import annotations

from typing import Any, Callable

import psycopg

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.ingestion.normalizers import (
    normalize_asset,
    normalize_event,
    normalize_fact,
    normalize_quote,
)
from dhoni_instagram_agent.ingestion.repository import (
    upsert_asset,
    upsert_event,
    upsert_fact,
    upsert_knowledge_document,
    upsert_quote,
    write_audit_event,
)
from dhoni_instagram_agent.ingestion.validators import VALIDATORS


NORMALIZERS: dict[str, Callable[[dict[str, Any], int], dict[str, Any]]] = {
    "Quotes": normalize_quote,
    "Facts & Stats": normalize_fact,
    "Assets": normalize_asset,
    "Special Events": normalize_event,
}

UPSERTS = {
    "Quotes": upsert_quote,
    "Facts & Stats": upsert_fact,
    "Assets": upsert_asset,
    "Special Events": upsert_event,
}


def ingest_batch(
    settings: Settings,
    source_system: str,
    source_collection: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    if source_collection not in NORMALIZERS:
        raise ValueError(f"Unsupported source collection: {source_collection}")

    normalize = NORMALIZERS[source_collection]
    validate = VALIDATORS[source_collection]
    upsert_domain = UPSERTS[source_collection]

    received = len(records)
    inserted = 0
    updated = 0
    skipped = 0
    rejected = 0
    errors: list[dict[str, Any]] = []

    with psycopg.connect(settings.database_url) as connection:
        for index, raw_record in enumerate(records, start=1):
            row_number = int(raw_record.get("row_number") or index)

            normalized = normalize(raw_record, row_number)
            validation_errors = validate(normalized)

            if validation_errors:
                rejected += 1
                errors.extend(error.model_dump() for error in validation_errors)
                continue

            normalized["source_system"] = source_system

            knowledge_id, changed = upsert_knowledge_document(
                connection,
                normalized,
            )

            if not changed:
                skipped += 1
                continue

            upsert_domain(
                connection,
                normalized,
                knowledge_id,
            )

            write_audit_event(
                connection,
                "KNOWLEDGE_INGESTED",
                knowledge_id,
                {
                    "source_system": source_system,
                    "source_collection": source_collection,
                    "source_record_id": normalized["source_record_id"],
                    "row_number": row_number,
                },
            )

            if normalized["source_record_id"].startswith("row-"):
                updated += 1
            else:
                inserted += 1

        connection.commit()

    return {
        "status": "completed",
        "source_system": source_system,
        "collection": source_collection,
        "received": received,
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "rejected": rejected,
        "errors": errors,
    }
