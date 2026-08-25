from pathlib import Path

from PIL import Image

from dhoni_instagram_agent.publishing import renderer


def test_existing_text_image_is_normalized_to_instagram_ratio(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "source.jpg"
    output = tmp_path / "rendered.jpg"

    Image.new("RGB", (1600, 900), "white").save(source)

    monkeypatch.setattr(
        renderer,
        "detect_existing_text",
        lambda _: True,
    )

    renderer.render_overlay(
        source_path=str(source),
        output_path=str(output),
        overlay_text="Existing text",
    )

    with Image.open(output) as image:
        width, height = image.size

    assert width == 1080
    assert height == 1080
    assert width / height == 1.0
