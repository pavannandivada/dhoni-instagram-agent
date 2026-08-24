from __future__ import annotations

from pathlib import Path

from PIL import Image


class TextDetectionError(RuntimeError):
    pass


def detect_existing_text(source_path: str) -> bool:
    """Return True when an image contains meaningful visible text.

    OCR is intentionally optional. If pytesseract/Tesseract is not installed,
    fail closed so we never add an overlay to an asset we cannot confidently
    classify as text-free.
    """
    source = Path(source_path)

    if not source.exists():
        raise TextDetectionError(f"Source image not found: {source}")

    try:
        import pytesseract
    except ImportError as error:
        raise TextDetectionError(
            "pytesseract is required for existing-text detection."
        ) from error

    try:
        image = Image.open(source).convert("RGB")
        text = pytesseract.image_to_string(image, config="--psm 11")
    except Exception as error:
        raise TextDetectionError(f"OCR failed for {source}: {error}") from error

    # Ignore OCR noise consisting only of punctuation or isolated characters.
    meaningful_tokens = [
        token
        for token in text.split()
        if any(character.isalnum() for character in token)
    ]

    return len(meaningful_tokens) >= 2 or any(
        len(token.strip(".,:;!?-_'\"()[]{}")) >= 4
        for token in meaningful_tokens
    )
