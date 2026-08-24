from __future__ import annotations

from typing import Any

import psycopg
import pytest

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.ingestion.service import ingest_batch


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def clean_database(settings: Settings):
    with psycopg.connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE
                    quotes,
                    knowledge_documents,
                    audit_events
                CASCADE
                """
            )
        connection.commit()

    yield

    with psycopg.connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE
                    quotes,
                    knowledge_documents,
                    audit_events
                CASCADE
                """
            )
        connection.commit()


def quote_record(
    *,
    quote: str = "Test quote",
    source_url: str = "https://example.com/source",
) -> dict[str, Any]:
    return {
        "row_number": 2,
        "Quote ID": "TEST-001",
        "Quote": quote,
        "Context": "Testing",
        "Source": "Test Source",
        "Source URL": source_url,
        "Date": "2026-08-19",
        "Verified": "TRUE",
        "Used": "FALSE",
        "Used Date": "",
    }


def test_insert_quote(settings: Settings, clean_database) -> None:
    result = ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [quote_record()],
    )

    assert result["inserted"] == 1
    assert result["updated"] == 0
    assert result["skipped"] == 0
    assert result["rejected"] == 0


def test_repeat_quote_is_skipped(settings: Settings, clean_database) -> None:
    record = quote_record()

    first = ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [record],
    )
    second = ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [record],
    )

    assert first["inserted"] == 1
    assert second["inserted"] == 0
    assert second["updated"] == 0
    assert second["skipped"] == 1


def test_changed_quote_is_updated(settings: Settings, clean_database) -> None:
    first = ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [quote_record()],
    )

    second = ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [quote_record(quote="Changed quote")],
    )

    assert first["inserted"] == 1
    assert second["updated"] == 1
    assert second["inserted"] == 0
    assert second["skipped"] == 0


def test_blank_quote_is_rejected(settings: Settings, clean_database) -> None:
    result = ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [quote_record(quote="")],
    )

    assert result["rejected"] == 1
    assert result["inserted"] == 0
    assert result["updated"] == 0
    assert result["skipped"] == 0
    assert result["errors"][0]["code"] == "QUOTE_TEXT_REQUIRED"


def test_missing_source_is_rejected(settings: Settings, clean_database) -> None:
    result = ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [quote_record(source_url="")],
    )

    assert result["rejected"] == 1
    assert result["inserted"] == 0
    assert result["errors"][0]["code"] == "QUOTE_SOURCE_URL_REQUIRED"


def test_audit_event_created(settings: Settings, clean_database) -> None:
    ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [quote_record()],
    )

    with psycopg.connect(settings.database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT event_type
                FROM audit_events
                WHERE subject_type = 'KNOWLEDGE_DOCUMENT'
                ORDER BY created_at DESC
                LIMIT 1
                """
        )
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == "KNOWLEDGE_INSERTED"


def test_skip_creates_audit_event(settings: Settings, clean_database) -> None:
    record = quote_record()

    ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [record],
    )

    ingest_batch(
        settings,
        "google_sheets",
        "Quotes",
        [record],
    )

    with psycopg.connect(settings.database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT event_type
                FROM audit_events
                WHERE subject_type = 'KNOWLEDGE_DOCUMENT'
                ORDER BY created_at DESC
                LIMIT 1
                """
        )
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == "KNOWLEDGE_SKIPPED"
