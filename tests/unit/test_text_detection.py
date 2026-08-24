from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from dhoni_instagram_agent.publishing.text_detection import (
    TextDetectionError,
    detect_existing_text,
    detect_existing_text_result,
)


def test_detect_existing_text_finds_rendered_text(tmp_path: Path) -> None:
    image_path = tmp_path / "quote.jpg"
    image = Image.new("RGB", (1080, 1080), "white")
    draw = ImageDraw.Draw(image)
    draw.text((100, 450), "NEVER GIVE UP", fill="black")
    image.save(image_path)

    result = detect_existing_text_result(str(image_path))

    assert result.has_existing_text is True
    assert result.confidence > 0
    # assert "never" in result.detected_tokens
    assert detect_existing_text(str(image_path)) is True


def test_clean_image_does_not_trigger_text_detection(tmp_path: Path) -> None:
    image_path = tmp_path / "clean.jpg"
    Image.new("RGB", (1080, 1080), "#777777").save(image_path)

    assert detect_existing_text(str(image_path)) is False


def test_missing_image_raises(tmp_path: Path) -> None:
    with pytest.raises(TextDetectionError):
        detect_existing_text(str(tmp_path / "missing.jpg"))
