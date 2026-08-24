from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from dhoni_instagram_agent.publishing.text_detection import detect_existing_text


class RenderError(RuntimeError):
    pass


def render_overlay(
    source_path: str,
    output_path: str,
    overlay_text: str,
    *,
    skip_if_text: bool = True,
) -> str:
    source = Path(source_path)
    output = Path(output_path)

    if not source.exists():
        raise RenderError(f"Source image not found: {source}")

    text = overlay_text.strip()

    if not text:
        raise RenderError("Overlay text is empty.")

    if skip_if_text and detect_existing_text(str(source)):
        output.parent.mkdir(parents=True, exist_ok=True)
        Image.open(source).convert("RGB").save(
            output,
            format="JPEG",
            quality=95,
            progressive=False,
            optimize=True,
        )
        return str(output)

    image = Image.open(source).convert("RGB")
    width, height = image.size
    draw = ImageDraw.Draw(image, "RGBA")

    font_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    font: ImageFont.FreeTypeFont | ImageFont.ImageFont | None = None

    for font_path in font_candidates:
        path = Path(font_path)
        if path.exists():
            try:
                font = ImageFont.truetype(str(path), max(28, int(width * 0.055)))
                break
            except OSError:
                continue

    if font is None:
        font = ImageFont.load_default()

    max_text_width = int(width * 0.84)
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)

        if bbox[2] <= max_text_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    if not lines:
        raise RenderError("Unable to render overlay text.")

    spacing = max(8, int(height * 0.01))
    line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
    total_height = sum(line_heights) + spacing * (len(lines) - 1)
    padding_y = int(height * 0.025)
    box_top = height - total_height - (padding_y * 2)

    draw.rectangle([0, box_top, width, height], fill=(0, 0, 0, 165))

    y = box_top + padding_y
    for line, line_height in zip(lines, line_heights, strict=True):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2

        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_height + spacing

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="JPEG", quality=95, progressive=False, optimize=True)
    return str(output)
