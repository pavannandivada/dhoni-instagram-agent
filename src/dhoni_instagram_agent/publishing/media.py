from __future__ import annotations

import os
import tempfile
from datetime import timedelta
from pathlib import Path

import google.auth
import requests
from google.auth import iam
from google.auth.transport import requests as google_requests
from google.cloud import storage  # type: ignore[import-untyped]

from dhoni_instagram_agent.publishing.renderer import render_overlay

GCS_BUCKET = "dhoni-instagram-media"
GCP_SERVICE_ACCOUNT = "dhoni-instagram-runtime@dhoniinstagramautomation.iam.gserviceaccount.com"


class MediaRenderError(RuntimeError):
    pass


def render_and_upload(
    source_url: str,
    post_id: str,
    overlay_text: str,
) -> str:
    if not source_url:
        raise MediaRenderError("Source image URL is empty.")

    if not overlay_text.strip():
        raise MediaRenderError("Overlay text is empty.")

    with tempfile.TemporaryDirectory(prefix="dhoni-render-") as temp_dir:
        temp_path = Path(temp_dir)
        source_path = temp_path / "source.jpg"
        output_path = temp_path / "rendered.jpg"

        storage_client = storage.Client()

        if source_url.startswith(f"https://storage.googleapis.com/{GCS_BUCKET}/"):
            object_name = source_url.removeprefix(f"https://storage.googleapis.com/{GCS_BUCKET}/")

            blob = storage_client.bucket(GCS_BUCKET).blob(object_name)

            try:
                blob.download_to_filename(str(source_path))
            except Exception as error:
                raise MediaRenderError(f"Unable to download GCS source image: {error}") from error
        else:
            response = requests.get(source_url, timeout=30)

            if not response.ok:
                raise MediaRenderError(
                    f"Unable to download source image: HTTP {response.status_code}"
                )

            content_type = response.headers.get("content-type", "").lower()

            if not content_type.startswith("image/"):
                raise MediaRenderError(
                    f"Source URL did not return an image. Content-Type: {content_type or 'unknown'}"
                )

            source_path.write_bytes(response.content)

        render_overlay(
            source_path=str(source_path),
            output_path=str(output_path),
            overlay_text=overlay_text,
        )

        object_name = f"instagram-rendered/{post_id}.jpg"

        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(object_name)

        blob.upload_from_filename(
            str(output_path),
            content_type="image/jpeg",
        )

        return _generate_signed_url(blob)


def _generate_signed_url(blob: storage.Blob) -> str:
    credentials, _ = google.auth.default()

    request = google_requests.Request()
    credentials.refresh(request)  # type: ignore[no-untyped-call]

    service_account_email = os.getenv(
        "GCP_SERVICE_ACCOUNT_EMAIL",
        GCP_SERVICE_ACCOUNT,
    )

    signer = iam.Signer(  # type: ignore[no-untyped-call]
        request,
        credentials,
        service_account_email,
    )

    return str(
        blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET",
            credentials=signer,
            service_account_email=service_account_email,
        )
    )
