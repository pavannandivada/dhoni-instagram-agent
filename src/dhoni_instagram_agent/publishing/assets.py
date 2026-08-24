from __future__ import annotations

from typing import Any

import psycopg


class AssetSelectionError(RuntimeError):
    pass


def attach_available_asset(
    connection: psycopg.Connection[Any],
    post_id: str,
) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                status,
                published,
                asset_id
            FROM content_calendar
            WHERE post_id = %s
            FOR UPDATE
            """,
            (post_id,),
        )

        post = cursor.fetchone()

        if post is None:
            raise AssetSelectionError(f"Post not found: {post_id}")

        status, published, current_asset_id = post

        if published:
            raise AssetSelectionError(f"Post {post_id} is already published.")

        if status != "APPROVED":
            raise AssetSelectionError(f"Post {post_id} is not APPROVED. Current status: {status}")

        if current_asset_id:
            return {
                "post_id": post_id,
                "asset_id": current_asset_id,
                "status": "ALREADY_ATTACHED",
            }

        cursor.execute(
            """
            SELECT asset_id
            FROM assets
            WHERE verified = TRUE
              AND used = FALSE
              AND LOWER(COALESCE(rights_status, '')) IN (
                  'owned',
                  'licensed',
                  'rights-cleared'
              )
            ORDER BY created_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """
        )

        asset = cursor.fetchone()

        if asset is None:
            raise AssetSelectionError("No verified, unused, rights-cleared asset is available.")

        selected_asset_id = asset[0]

        cursor.execute(
            """
            UPDATE content_calendar
            SET asset_id = %s,
                updated_at = now()
            WHERE post_id = %s
            RETURNING post_id, asset_id, status
            """,
            (selected_asset_id, post_id),
        )

        result = cursor.fetchone()

        if result is None:
            raise AssetSelectionError("Failed to attach asset to content calendar post.")

        connection.commit()

        return {
            "post_id": result[0],
            "asset_id": result[1],
            "status": result[2],
        }
