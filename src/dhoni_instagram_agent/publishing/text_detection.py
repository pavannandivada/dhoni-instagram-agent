from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


class TextDetectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class TextDetectionResult:
    has_existing_text: bool
    confidence: float
    detected_tokens: tuple[str, ...]


def _ocr_variants(image: Image.Image) -> tuple[Image.Image, ...]:
    """Build a small set of OCR-friendly views without adding new CV dependencies."""
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(1.35)
    gray = gray.resize((gray.width * 2, gray.height * 2), Image.Resampling.LANCZOS)

    threshold = gray.point(lambda value: 255 if value >= 175 else 0)

    return image, gray, threshold


def detect_existing_text_result(source_path: str) -> TextDetectionResult:
    """Detect meaningful visible text using multiple OCR passes.

    The detector is intentionally conservative: if OCR returns plausible text but
    confidence is weak, the result still protects the source image from an overlay.
    A false positive only means we leave the user's image unchanged; a false
    negative could permanently obscure an existing quote.
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
        candidates: list[tuple[str, float]] = []

        for variant in _ocr_variants(image):
            data = pytesseract.image_to_data(
                variant,
                config="--psm 11",
                output_type=pytesseract.Output.DICT,
            )
            for raw_text, raw_conf in zip(data["text"], data["conf"], strict=True):
                token = raw_text.strip()
                if not token or not any(character.isalnum() for character in token):
                    continue
                try:
                    confidence = float(raw_conf)
                except (TypeError, ValueError):
                    continue
                if confidence >= 0:
                    candidates.append((token, confidence))
    except Exception as error:
        raise TextDetectionError(f"OCR failed for {source}: {error}") from error

    # De-duplicate OCR variants while keeping the strongest confidence.
    strongest: dict[str, float] = {}
    for token, confidence in candidates:
        normalized = " ".join(token.split()).lower()
        if len(normalized) < 2:
            continue
        strongest[normalized] = max(strongest.get(normalized, -1.0), confidence)

    ranked = sorted(strongest.items(), key=lambda item: item[1], reverse=True)
    reliable = [token for token, confidence in ranked if len(token) >= 3 and confidence >= 45]
    very_reliable = [
        token for token, confidence in ranked if len(token) >= 4 and confidence >= 70
    ]

    # Two reasonably confident words, or one strong word, is enough to protect the image.
    has_text = len(reliable) >= 2 or bool(very_reliable)
    confidence = max((confidence for _, confidence in ranked), default=0.0)

    return TextDetectionResult(
        has_existing_text=has_text,
        confidence=round(min(confidence / 100.0, 1.0), 2),
        detected_tokens=tuple(token for token, _ in ranked[:20]),
    )


def detect_existing_text(source_path: str) -> bool:
    """Return whether an image should be protected from a new text overlay."""
    return detect_existing_text_result(source_path).has_existing_text
