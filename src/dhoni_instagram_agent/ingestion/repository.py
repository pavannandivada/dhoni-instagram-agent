from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

import psycopg


class PersistenceAction(StrEnum):
    INSERTED = "INSERTED"
    UPDATED = "UPDATED"
    SKIPPED = "SKIPPED"


def upsert_knowledge_document(
    connection: psycopg.Connection[Any],
    record: dict[str, Any],
) -> tuple[str, PersistenceAction]:
    from dhoni_instagram_agent.ingestion.hashing import content_hash

    hash_payload = {
        **record["normalized_payload"],
        "verification_status": record["verification_status"],
        "rights_status": record["rights_status"],
    }

    payload_hash = content_hash(hash_payload)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, content_hash
            FROM knowledge_documents
            WHERE source_system = %s
              AND source_collection = %s
              AND source_record_id = %s
            """,
            (
                record["source_system"],
                record["source_collection"],
                record["source_record_id"],
            ),
        )
        existing = cursor.fetchone()

        if existing and existing[1] == payload_hash:
            return str(existing[0]), PersistenceAction.SKIPPED

        if existing:
            cursor.execute(
                """
                UPDATE knowledge_documents
                SET source_row_number = %s,
                    title = %s,
                    content = %s,
                    source_url = %s,
                    verification_status = %s,
                    rights_status = %s,
                    raw_payload = %s::jsonb,
                    normalized_payload = %s::jsonb,
                    content_hash = %s,
                    updated_at = now()
                WHERE id = %s
                RETURNING id
                """,
                (
                    record["source_row_number"],
                    record["title"],
                    record["content"],
                    record["source_url"],
                    record["verification_status"],
                    record["rights_status"],
                    json.dumps(record["raw_payload"]),
                    json.dumps(record["normalized_payload"]),
                    payload_hash,
                    existing[0],
                ),
            )

            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Knowledge document update did not return an ID.")

            return str(row[0]), PersistenceAction.UPDATED

        cursor.execute(
            """
            INSERT INTO knowledge_documents (
                source_system,
                source_collection,
                source_record_id,
                source_row_number,
                title,
                content,
                source_url,
                verification_status,
                rights_status,
                raw_payload,
                normalized_payload,
                content_hash
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s::jsonb, %s::jsonb, %s
            )
            RETURNING id
            """,
            (
                record["source_system"],
                record["source_collection"],
                record["source_record_id"],
                record["source_row_number"],
                record["title"],
                record["content"],
                record["source_url"],
                record["verification_status"],
                record["rights_status"],
                json.dumps(record["raw_payload"]),
                json.dumps(record["normalized_payload"]),
                payload_hash,
            ),
        )

        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Knowledge document insert did not return an ID.")

        return str(row[0]), PersistenceAction.INSERTED


def upsert_quote(
    connection: psycopg.Connection[Any],
    record: dict[str, Any],
    knowledge_id: str,
) -> None:
    payload = record["normalized_payload"]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO quotes (
                quote_id,
                quote,
                context,
                source,
                source_url,
                quote_date,
                verified,
                used,
                used_at,
                knowledge_document_id
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (quote_id)
            DO UPDATE SET
                quote = EXCLUDED.quote,
                context = EXCLUDED.context,
                source = EXCLUDED.source,
                source_url = EXCLUDED.source_url,
                quote_date = EXCLUDED.quote_date,
                verified = EXCLUDED.verified,
                used = EXCLUDED.used,
                used_at = EXCLUDED.used_at,
                knowledge_document_id = EXCLUDED.knowledge_document_id,
                updated_at = now()
            """,
            (
                payload["quote_id"],
                payload["quote"],
                payload["context"],
                payload["source"],
                payload["source_url"],
                payload["date"] or None,
                payload["verified"],
                payload["used"],
                payload["used_date"] or None,
                knowledge_id,
            ),
        )


def upsert_fact(
    connection: psycopg.Connection[Any],
    record: dict[str, Any],
    knowledge_id: str,
) -> None:
    payload = record["normalized_payload"]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO facts (
                fact_id,
                category,
                fact,
                format,
                source,
                source_url,
                verified_date,
                verified,
                used,
                used_at,
                knowledge_document_id
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (fact_id)
            DO UPDATE SET
                category = EXCLUDED.category,
                fact = EXCLUDED.fact,
                format = EXCLUDED.format,
                source = EXCLUDED.source,
                source_url = EXCLUDED.source_url,
                verified_date = EXCLUDED.verified_date,
                verified = EXCLUDED.verified,
                used = EXCLUDED.used,
                used_at = EXCLUDED.used_at,
                knowledge_document_id = EXCLUDED.knowledge_document_id,
                updated_at = now()
            """,
            (
                payload["fact_id"],
                payload["category"],
                payload["fact"],
                payload["format"],
                payload["source"],
                payload["source_url"],
                payload["verified_date"] or None,
                payload["verified"],
                payload["used"],
                payload["used_date"] or None,
                knowledge_id,
            ),
        )


def upsert_asset(
    connection: psycopg.Connection[Any],
    record: dict[str, Any],
    knowledge_id: str,
) -> None:
    payload = record["normalized_payload"]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO assets (
                asset_id,
                asset_type,
                category,
                drive_file_id,
                file_name,
                source_url,
                creator,
                license,
                rights_status,
                verified,
                used,
                last_used,
                knowledge_document_id
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (asset_id)
            DO UPDATE SET
                asset_type = EXCLUDED.asset_type,
                category = EXCLUDED.category,
                drive_file_id = EXCLUDED.drive_file_id,
                file_name = EXCLUDED.file_name,
                source_url = EXCLUDED.source_url,
                creator = EXCLUDED.creator,
                license = EXCLUDED.license,
                rights_status = EXCLUDED.rights_status,
                verified = EXCLUDED.verified,
                used = EXCLUDED.used,
                last_used = EXCLUDED.last_used,
                knowledge_document_id = EXCLUDED.knowledge_document_id,
                updated_at = now()
            """,
            (
                payload["asset_id"],
                payload["asset_type"],
                payload["category"],
                payload["drive_file_id"],
                payload["file_name"],
                payload["source_url"],
                payload["creator"],
                payload["license"],
                payload["license"],
                payload["verified"],
                payload["used"],
                payload["last_used"] or None,
                knowledge_id,
            ),
        )


def upsert_event(
    connection: psycopg.Connection[Any],
    record: dict[str, Any],
    knowledge_id: str,
) -> None:
    payload = record["normalized_payload"]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO special_events (
                event_id,
                event_date,
                event_type,
                description,
                source_url,
                priority,
                used,
                used_at,
                knowledge_document_id
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (event_id)
            DO UPDATE SET
                event_date = EXCLUDED.event_date,
                event_type = EXCLUDED.event_type,
                description = EXCLUDED.description,
                source_url = EXCLUDED.source_url,
                priority = EXCLUDED.priority,
                used = EXCLUDED.used,
                used_at = EXCLUDED.used_at,
                knowledge_document_id = EXCLUDED.knowledge_document_id,
                updated_at = now()
            """,
            (
                payload["event_id"],
                payload["event_date"],
                payload["event_type"],
                payload["description"],
                payload["source_url"],
                int(payload["priority"] or 0),
                payload["used"],
                payload["used_date"] or None,
                knowledge_id,
            ),
        )


def write_audit_event(
    connection: psycopg.Connection[Any],
    event_type: str,
    subject_id: str,
    payload: dict[str, Any],
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO audit_events (
                event_type,
                actor_type,
                subject_type,
                subject_id,
                payload
            )
            VALUES (%s, %s, %s, %s, %s::jsonb)
            """,
            (
                event_type,
                "INGESTION_SERVICE",
                "KNOWLEDGE_DOCUMENT",
                subject_id,
                json.dumps(payload),
            ),
        )
