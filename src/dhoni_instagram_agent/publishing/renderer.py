from __future__ import annotations

from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

from dhoni_instagram_agent.publishing.text_detection import detect_existing_text

RenderMode = Literal["QUOTE", "STANDARD", "MILESTONE"]

OUTPUT_SIZE = (1080, 1350)

GOLD = (244, 190, 0, 255)
WHITE = (255, 255, 255, 255)
BLACK = (8, 8, 8, 255)
TRANSPARENT_BLACK = (0, 0, 0, 0)


class RenderError(RuntimeError):
    pass


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    if bold:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue

    return ImageFont.load_default()


def _prepare_image(source: Path) -> Image.Image:
    image = Image.open(source).convert("RGB")

    width, height = image.size
    ratio = width / height

    # Keep common Instagram-friendly portrait/square compositions intact.
    # Only crop when the source is outside the supported portrait range.
    min_ratio = 4 / 5
    max_ratio = 1.0

    if ratio < min_ratio:
        new_height = int(width / min_ratio)
        top = max(0, (height - new_height) // 2)
        image = image.crop((0, top, width, top + new_height))

    elif ratio > max_ratio:
        new_width = height
        left = max(0, (width - new_width) // 2)
        image = image.crop((left, 0, left + new_width, height))

    # Normalize size while preserving the resulting aspect ratio.
    width, height = image.size

    if width >= height:
        target_width = 1080
        target_height = round(height * target_width / width)
    else:
        target_height = 1350
        target_width = round(width * target_height / height)

    return image.resize(
        (target_width, target_height),
        Image.Resampling.LANCZOS,
    )


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.split()

    if not words:
        return []

    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)

        if bbox[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def _draw_brand(draw: ImageDraw.ImageDraw) -> None:
    font = _load_font(32, bold=True)

    x = OUTPUT_SIZE[0] - 70
    y = 55

    text = "DHONI"
    text2 = "DAILY"

    bbox1 = draw.textbbox((0, 0), text, font=font)
    bbox2 = draw.textbbox((0, 0), text2, font=font)

    draw.text(
        (x - (bbox1[2] - bbox1[0]), y),
        text,
        font=font,
        fill=WHITE,
    )

    draw.text(
        (x - (bbox2[2] - bbox2[0]), y + 36),
        text2,
        font=font,
        fill=WHITE,
    )

    draw.line(
        (
            x - 58,
            y + 75,
            x,
            y + 75,
        ),
        fill=GOLD,
        width=4,
    )


def _draw_quote(image: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(image, "RGBA")

    # Bottom gradient.
    gradient = Image.new("RGBA", image.size, TRANSPARENT_BLACK)
    gradient_draw = ImageDraw.Draw(gradient, "RGBA")

    height = image.height
    start_y = int(height * 0.57)

    for y in range(start_y, height):
        progress = (y - start_y) / max(1, height - start_y)
        alpha = int(20 + (progress * 225))
        gradient_draw.line(
            (0, y, image.width, y),
            fill=(0, 0, 0, alpha),
        )

    image.alpha_composite(gradient)

    draw = ImageDraw.Draw(image, "RGBA")

    _draw_brand(draw)

    quote_font = _load_font(58, bold=True)
    name_font = _load_font(34, bold=True)

    lines = _wrap_text(
        draw,
        text,
        quote_font,
        max_width=850,
    )

    x = 80
    y = int(image.height * 0.70)

    draw.text(
        (75, y - 65),
        "“",
        font=_load_font(110, bold=True),
        fill=GOLD,
    )

    for line in lines[:4]:
        draw.text(
            (x, y),
            line,
            font=quote_font,
            fill=WHITE,
        )
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        y += bbox[3] + 12

    draw.line(
        (80, y + 20, 190, y + 20),
        fill=GOLD,
        width=5,
    )

    draw.text(
        (80, y + 50),
        "MS DHONI",
        font=name_font,
        fill=GOLD,
    )


def _draw_standard(image: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(image, "RGBA")

    # Editorial lower panel.
    # panel_top = 760
    panel_top = int(image.height * 0.56)
    draw.rectangle(
        (0, panel_top, image.width, image.height),
        fill=(0, 0, 0, 210),
    )

    # Gold accent stripe.
    draw.rectangle(
        (0, panel_top, image.width, panel_top + 8),
        fill=GOLD,
    )

    _draw_brand(draw)

    tag_font = _load_font(28, bold=True)
    title_font = _load_font(92, bold=True)
    subtitle_font = _load_font(38, bold=True)

    tag_text = "THE CAPTAIN"

    tag_bbox = draw.textbbox((0, 0), tag_text, font=tag_font)
    tag_width = tag_bbox[2] - tag_bbox[0]

    draw.rounded_rectangle(
        (
            70,
            panel_top + 45,
            70 + tag_width + 36,
            panel_top + 92,
        ),
        radius=8,
        fill=GOLD,
    )

    draw.text(
        (88, panel_top + 52),
        tag_text,
        font=tag_font,
        fill=BLACK,
    )

    lines = _wrap_text(
        draw,
        text,
        title_font,
        max_width=900,
    )

    y = panel_top + int(image.height * 0.09)

    for line in lines[:3]:
        draw.text(
            (70, y),
            line,
            font=title_font,
            fill=WHITE,
        )

        bbox = draw.textbbox((0, 0), line, font=title_font)
        y += bbox[3] + 4

    draw.line(
        (70, y + 15, 300, y + 15),
        fill=GOLD,
        width=4,
    )

    draw.text(
        (70, y + 40),
        "THE FINISHER. THE LEADER. THE LEGEND.",
        font=subtitle_font,
        fill=GOLD,
    )


def _draw_milestone(image: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(image, "RGBA")

    # Strong cinematic dark overlay.
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay, "RGBA")

    overlay_draw.rectangle(
        (0, 0, image.width, image.height),
        fill=(0, 0, 0, 75),
    )

    overlay_draw.rectangle(
        (0, 760, image.width, image.height),
        fill=(0, 0, 0, 215),
    )

    image.alpha_composite(overlay)

    draw = ImageDraw.Draw(image, "RGBA")

    _draw_brand(draw)

    title_font = _load_font(104, bold=True)
    subtitle_font = _load_font(42, bold=True)

    lines = _wrap_text(
        draw,
        text,
        title_font,
        max_width=920,
    )

    y = int(image.height * 0.59)

    for line in lines[:2]:
        draw.text(
            (70, y),
            line,
            font=title_font,
            fill=GOLD,
        )
        bbox = draw.textbbox((0, 0), line, font=title_font)
        y += bbox[3] + 5

    draw.text(
        (75, y + 35),
        "A CAPTAIN. A FINISHER. AN ICON.",
        font=subtitle_font,
        fill=WHITE,
    )

    draw.line(
        (75, y + 105, 430, y + 105),
        fill=GOLD,
        width=6,
    )

    draw.text(
        (75, y + 135),
        "NEVER STOPS. NEVER SETTLES.",
        font=subtitle_font,
        fill=GOLD,
    )


def render_overlay(
    source_path: str,
    output_path: str,
    overlay_text: str,
    mode: RenderMode = "STANDARD",
) -> str:
    source = Path(source_path)
    output = Path(output_path)

    if not source.exists():
        raise RenderError(f"Source image not found: {source}")

    text = overlay_text.strip()

    if not text:
        raise RenderError("Overlay text is empty.")

    if mode not in {"QUOTE", "STANDARD", "MILESTONE"}:
        raise RenderError(f"Unsupported render mode: {mode}")

    # Never overwrite an image that already contains meaningful text.
    # Preserve the source image unchanged.
    if detect_existing_text(str(source)):
        output.parent.mkdir(parents=True, exist_ok=True)

        image = Image.open(source).convert("RGB")
        image.save(
            output,
            format="JPEG",
            quality=95,
            progressive=True,
            optimize=True,
        )

        return str(output)

    # No existing text detected — apply our selected template.
    image = _prepare_image(source).convert("RGBA")

    if mode == "QUOTE":
        _draw_quote(image, text)
    elif mode == "STANDARD":
        _draw_standard(image, text)
    else:
        _draw_milestone(image, text)

    output.parent.mkdir(parents=True, exist_ok=True)

    image.convert("RGB").save(
        output,
        format="JPEG",
        quality=95,
        progressive=True,
        optimize=True,
    )

    return str(output)
