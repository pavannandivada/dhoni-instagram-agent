from __future__ import annotations

import time
from typing import Any

import psycopg
import requests

from dhoni_instagram_agent.config import Settings


GRAPH_BASE_URL = "https://graph.facebook.com/v23.0"


class PublishError(RuntimeError):
    pass


def _meta_error(response: requests.Response) -> str:
    try:
        data = response.json()
        error = data.get("error", {})
        return (
            f"Meta API error {error.get('code')}: "
            f"{error.get('message', response.text)}"
        )
    except Exception:
        return f"Meta API HTTP {response.status_code}: {response.text}"


def publish_post(
    connection: psycopg.Connection[Any],
    post_id: str,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    settings = Settings()
    access_token = settings.instagram_access_token.get_secret_value()
    ig_user_id = settings.instagram_business_account_id

    if not access_token:
        raise PublishError("Instagram access token is not configured.")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                post_id,
                status,
                published,
                instagram_media_id,
                instagram_creation_id,
                caption,
                asset_id
            FROM content_calendar
            WHERE post_id = %s
            FOR UPDATE
            """,
            (post_id,),
        )

        row = cursor.fetchone()

        if row is None:
            raise PublishError(f"Post not found: {post_id}")

        (
            stored_post_id,
            status,
            published,
            instagram_media_id,
            instagram_creation_id,
            caption,
            asset_id,
        ) = row

        if published or instagram_media_id:
            return {
                "post_id": stored_post_id,
                "status": "ALREADY_PUBLISHED",
                "published": published,
                "instagram_media_id": instagram_media_id,
                "instagram_creation_id": instagram_creation_id,
            }

        if status != "APPROVED":
            raise PublishError(
                f"Post {post_id} is not APPROVED. Current status: {status}"
            )

        if not caption:
            raise PublishError(f"Post {post_id} has no caption.")

        if not asset_id:
            raise PublishError(f"Post {post_id} has no asset_id.")

        cursor.execute(
            """
            SELECT
                source_url,
                verified,
                used,
                rights_status
            FROM assets
            WHERE asset_id = %s
            """,
            (asset_id,),
        )

        asset = cursor.fetchone()

        if asset is None:
            raise PublishError(f"Asset not found: {asset_id}")

        image_url, verified, used, rights_status = asset

        if not verified:
            raise PublishError(
                f"Asset {asset_id} is not verified."
            )

        if used:
            raise PublishError(
                f"Asset {asset_id} has already been used."
            )

        if str(rights_status).strip().lower() not in {
            "owned",
            "licensed",
            "rights-cleared",
        }:
            raise PublishError(
                f"Asset {asset_id} does not have an acceptable rights status."
            )

        if not image_url:
            raise PublishError(
                f"Asset {asset_id} has no source URL."
            )

        # Remove accidental outer quotes produced by an LLM.
        clean_caption = caption.strip()

        if (
            len(clean_caption) >= 2
            and clean_caption[0] in {'"', "'"}
            and clean_caption[-1] == clean_caption[0]
        ):
            clean_caption = clean_caption[1:-1].strip()

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        # Reuse a previously created container when available.
        creation_id = instagram_creation_id

        if not creation_id:
            response = requests.post(
                f"{GRAPH_BASE_URL}/{ig_user_id}/media",
                headers=headers,
                data={
                    "image_url": image_url,
                    "caption": clean_caption,
                },
                timeout=30,
            )

            if not response.ok:
                raise PublishError(_meta_error(response))

            body = response.json()
            creation_id = body.get("id")

            if not creation_id:
                raise PublishError(
                    f"Meta did not return a creation ID: {body}"
                )

            cursor.execute(
                """
                UPDATE content_calendar
                SET instagram_creation_id = %s,
                    updated_at = now()
                WHERE post_id = %s
                """,
                (creation_id, post_id),
            )

            connection.commit()

        if dry_run:
            return {
                "post_id": post_id,
                "status": "CONTAINER_CREATED",
                "dry_run": True,
                "instagram_creation_id": creation_id,
                "image_url": image_url,
            }

        # Give Meta a short window to finish processing.
        status_url = (
            f"{GRAPH_BASE_URL}/{creation_id}"
        )

        for _ in range(10):
            status_response = requests.get(
                status_url,
                headers=headers,
                params={
                    "fields": "status_code,status",
                },
                timeout=30,
            )

            if not status_response.ok:
                raise PublishError(
                    _meta_error(status_response)
                )

            status_body = status_response.json()
            status_code = status_body.get("status_code")

            if status_code == "FINISHED":
                break

            if status_code in {
                "ERROR",
                "EXPIRED",
            }:
                raise PublishError(
                    f"Instagram container failed: {status_body}"
                )

            time.sleep(3)

        else:
            raise PublishError(
                "Instagram container did not become ready within the retry window."
            )

        publish_response = requests.post(
            f"{GRAPH_BASE_URL}/{ig_user_id}/media_publish",
            headers=headers,
            data={
                "creation_id": creation_id,
            },
            timeout=30,
        )

        if not publish_response.ok:
            raise PublishError(
                _meta_error(publish_response)
            )

        publish_body = publish_response.json()
        media_id = publish_body.get("id")

        if not media_id:
            raise PublishError(
                f"Meta did not return an Instagram Media ID: {publish_body}"
            )

        cursor.execute(
            """
            UPDATE content_calendar
            SET published = TRUE,
                instagram_media_id = %s,
                status = 'PUBLISHED',
                updated_at = now()
            WHERE post_id = %s
            """,
            (media_id, post_id),
        )

        cursor.execute(
            """
            UPDATE assets
            SET used = TRUE,
                last_used = now(),
                updated_at = now()
            WHERE asset_id = %s
            """,
            (asset_id,),
        )

        connection.commit()

        return {
            "post_id": post_id,
            "status": "PUBLISHED",
            "dry_run": False,
            "instagram_creation_id": creation_id,
            "instagram_media_id": media_id,
            "asset_id": asset_id,
        }
