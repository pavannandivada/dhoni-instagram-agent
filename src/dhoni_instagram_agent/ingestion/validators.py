from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ValidationError(BaseModel):
    row_number: int
    code: str
    message: str


def validate_quote(record: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    row = int(record["source_row_number"])

    if not record["normalized_payload"].get("quote_id"):
        errors.append(
            ValidationError(
                row_number=row,
                code="QUOTE_ID_REQUIRED",
                message="Quote ID is required.",
            )
        )

    if not record["normalized_payload"].get("quote"):
        errors.append(
            ValidationError(
                row_number=row,
                code="QUOTE_TEXT_REQUIRED",
                message="Quote text is required.",
            )
        )

    if not record.get("source_url"):
        errors.append(
            ValidationError(
                row_number=row,
                code="QUOTE_SOURCE_URL_REQUIRED",
                message="A source URL is required for a publishable quote record.",
            )
        )

    return errors


def validate_fact(record: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    row = int(record["source_row_number"])

    if not record["normalized_payload"].get("fact_id"):
        errors.append(
            ValidationError(
                row_number=row,
                code="FACT_ID_REQUIRED",
                message="Fact ID is required.",
            )
        )

    if not record["normalized_payload"].get("fact"):
        errors.append(
            ValidationError(
                row_number=row,
                code="FACT_REQUIRED",
                message="Fact text is required.",
            )
        )

    if not record["normalized_payload"].get("category"):
        errors.append(
            ValidationError(
                row_number=row,
                code="FACT_CATEGORY_REQUIRED",
                message="Fact category is required.",
            )
        )

    if not record.get("source_url"):
        errors.append(
            ValidationError(
                row_number=row,
                code="FACT_SOURCE_URL_REQUIRED",
                message="A source URL is required for a grounded fact.",
            )
        )

    return errors


def validate_asset(record: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    row = int(record["source_row_number"])
    payload = record["normalized_payload"]

    if not payload.get("asset_id"):
        errors.append(
            ValidationError(
                row_number=row,
                code="ASSET_ID_REQUIRED",
                message="Asset ID is required.",
            )
        )

    if not payload.get("file_name"):
        errors.append(
            ValidationError(
                row_number=row,
                code="ASSET_FILE_NAME_REQUIRED",
                message="File name is required.",
            )
        )

    if not payload.get("drive_file_id") and not payload.get("source_url"):
        errors.append(
            ValidationError(
                row_number=row,
                code="ASSET_LOCATION_REQUIRED",
                message="A Drive file ID or source URL is required.",
            )
        )

    return errors


def validate_event(record: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    row = int(record["source_row_number"])
    payload = record["normalized_payload"]

    if not payload.get("event_id"):
        errors.append(
            ValidationError(
                row_number=row,
                code="EVENT_ID_REQUIRED",
                message="Event ID is required.",
            )
        )

    if not payload.get("event_date"):
        errors.append(
            ValidationError(
                row_number=row,
                code="EVENT_DATE_REQUIRED",
                message="Event date is required.",
            )
        )

    if not payload.get("event_type"):
        errors.append(
            ValidationError(
                row_number=row,
                code="EVENT_TYPE_REQUIRED",
                message="Event type is required.",
            )
        )

    if not payload.get("description"):
        errors.append(
            ValidationError(
                row_number=row,
                code="EVENT_DESCRIPTION_REQUIRED",
                message="Event description is required.",
            )
        )

    return errors


VALIDATORS = {
    "Quotes": validate_quote,
    "Facts & Stats": validate_fact,
    "Assets": validate_asset,
    "Special Events": validate_event,
}
