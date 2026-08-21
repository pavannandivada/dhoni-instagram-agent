from __future__ import annotations

from datetime import date, time
from typing import Any

import psycopg


ALLOWED_STATUSES = {
    "DRAFT",
    "PENDING_REVIEW",
    "APPROVED",
    "SCHEDULED",
    "PUBLISHED",
    "REJECTED",
}


def create_post(
    connection: psycopg.Connection[Any],
    *,
    post_id: str,
    scheduled_date: date | None,
    scheduled_time: time | None,
    content_type: str,
    topic: str | None,
    quote_stat: str | None,
    source_url: str | None,
    asset_id: str | None,
    caption: str | None,
    overlay_text: str | None,
    status: str,
) -> dict[str, Any]:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Unsupported status: {status}")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO content_calendar (
                post_id,
                scheduled_date,
                scheduled_time,
                content_type,
                topic,
                quote_stat,
                source_url,
                asset_id,
                caption,
                overlay_text,
                status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING
                post_id,
                scheduled_date,
                scheduled_time,
                content_type,
                topic,
                quote_stat,
                source_url,
                asset_id,
                caption,
                overlay_text,
                status,
                published,
                instagram_media_id,
                created_at,
                updated_at
            """,
            (
                post_id,
                scheduled_date,
                scheduled_time,
                content_type,
                topic,
                quote_stat,
                source_url,
                asset_id,
                caption,
                overlay_text,
                status,
            ),
        )

        row = cursor.fetchone()

    if row is None:
        raise RuntimeError("Content calendar insert failed.")

    connection.commit()

    columns = [
        "post_id",
        "scheduled_date",
        "scheduled_time",
        "content_type",
        "topic",
        "quote_stat",
        "source_url",
        "asset_id",
        "caption",
        "overlay_text",
        "status",
        "published",
        "instagram_media_id",
        "created_at",
        "updated_at",
    ]

    return dict(zip(columns, row))


def list_posts(
    connection: psycopg.Connection[Any],
    *,
    status: str | None = None,
) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        if status is None:
            cursor.execute(
                """
                SELECT
                    post_id,
                    scheduled_date,
                    scheduled_time,
                    content_type,
                    topic,
                    quote_stat,
                    source_url,
                    asset_id,
                    caption,
                    overlay_text,
                    status,
                    published,
                    instagram_media_id,
                    created_at,
                    updated_at
                FROM content_calendar
                ORDER BY
                    scheduled_date NULLS LAST,
                    scheduled_time NULLS LAST,
                    created_at DESC
                """
            )
        else:
            if status not in ALLOWED_STATUSES:
                raise ValueError(f"Unsupported status: {status}")

            cursor.execute(
                """
                SELECT
                    post_id,
                    scheduled_date,
                    scheduled_time,
                    content_type,
                    topic,
                    quote_stat,
                    source_url,
                    asset_id,
                    caption,
                    overlay_text,
                    status,
                    published,
                    instagram_media_id,
                    created_at,
                    updated_at
                FROM content_calendar
                WHERE status = %s
                ORDER BY
                    scheduled_date NULLS LAST,
                    scheduled_time NULLS LAST,
                    created_at DESC
                """,
                (status,),
            )

        rows = cursor.fetchall()

    columns = [
        "post_id",
        "scheduled_date",
        "scheduled_time",
        "content_type",
        "topic",
        "quote_stat",
        "source_url",
        "asset_id",
        "caption",
        "overlay_text",
        "status",
        "published",
        "instagram_media_id",
        "created_at",
        "updated_at",
    ]

    return [dict(zip(columns, row)) for row in rows]


def update_post(
    connection: psycopg.Connection[Any],
    post_id: str,
    updates: dict[str, Any],
) -> dict[str, Any] | None:
    if "status" in updates and updates["status"] not in ALLOWED_STATUSES:
        raise ValueError(f"Unsupported status: {updates['status']}")

    allowed_fields = {
        "scheduled_date",
        "scheduled_time",
        "content_type",
        "topic",
        "quote_stat",
        "source_url",
        "asset_id",
        "caption",
        "overlay_text",
        "status",
        "published",
        "instagram_media_id",
    }

    updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    if not updates:
        raise ValueError("No valid fields to update.")

    assignments = ", ".join(
        f"{field} = %s"
        for field in updates
    )

    values = list(updates.values())
    values.append(post_id)

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE content_calendar
            SET
                {assignments},
                updated_at = now()
            WHERE post_id = %s
            RETURNING
                post_id,
                scheduled_date,
                scheduled_time,
                content_type,
                topic,
                quote_stat,
                source_url,
                asset_id,
                caption,
                overlay_text,
                status,
                published,
                instagram_media_id,
                created_at,
                updated_at
            """,
            values,
        )

        row = cursor.fetchone()

    if row is None:
        return None

    connection.commit()

    columns = [
        "post_id",
        "scheduled_date",
        "scheduled_time",
        "content_type",
        "topic",
        "quote_stat",
        "source_url",
        "asset_id",
        "caption",
        "overlay_text",
        "status",
        "published",
        "instagram_media_id",
        "created_at",
        "updated_at",
    ]

    return dict(zip(columns, row))
