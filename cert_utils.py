"""
Certificate generation with intelligent layout-aware name placement.
"""

from __future__ import annotations

import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FONT_CACHE = Path(".cache/Poppins-Bold.ttf")
FONT_URL = (
    "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"
)

MIN_FONT_SIZE = 14
DEFAULT_FONT_SIZE = 68
MAX_TEXT_WIDTH_RATIO = 0.78
HORIZONTAL_MARGIN_RATIO = 0.14
NAME_TEXT_COLOR = (25, 25, 30)


def get_font_path() -> str:
    if FONT_CACHE.exists():
        return str(FONT_CACHE)

    FONT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(FONT_URL, FONT_CACHE)
    return str(FONT_CACHE)


def load_template(template_bytes: bytes) -> Image.Image:
    image = Image.open(BytesIO(template_bytes))
    return image.convert("RGB")


def _is_dark(r: int, g: int, b: int) -> bool:
    return r < 115 and g < 115 and b < 115


def _is_gold(r: int, g: int, b: int) -> bool:
    return r > 145 and g > 95 and b < 145 and (r - b) > 35


def _is_colored_ink(r: int, g: int, b: int) -> bool:
    if _is_dark(r, g, b):
        return True
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    return (max_c - min_c) > 38 and max_c > 80


def _analyze_rows(image: Image.Image) -> list[dict]:
    width, height = image.size
    pixels = image.load()
    x_start = int(width * HORIZONTAL_MARGIN_RATIO)
    x_end = width - x_start
    span = max(x_end - x_start, 1)

    rows = []
    for y in range(height):
        dark = gold = ink = 0
        for x in range(x_start, x_end):
            r, g, b = pixels[x, y]
            if _is_dark(r, g, b):
                dark += 1
            if _is_gold(r, g, b):
                gold += 1
            if _is_colored_ink(r, g, b):
                ink += 1

        rows.append(
            {
                "y": y,
                "dark": dark / span,
                "gold": gold / span,
                "ink": ink / span,
            }
        )
    return rows


def _smooth(values: list[float], radius: int = 2) -> list[float]:
    if not values:
        return values
    smoothed = []
    for index in range(len(values)):
        start = max(0, index - radius)
        end = min(len(values), index + radius + 1)
        smoothed.append(sum(values[start:end]) / (end - start))
    return smoothed


def _find_text_blocks(rows: list[dict], start_y: int, end_y: int) -> list[tuple[int, int]]:
    blocks = []
    in_block = False
    block_start = 0
    threshold = 0.045

    for y in range(start_y, end_y):
        if rows[y]["ink"] >= threshold:
            if not in_block:
                block_start = y
                in_block = True
        elif in_block:
            if y - block_start >= 4:
                blocks.append((block_start, y - 1))
            in_block = False

    if in_block and end_y - block_start >= 4:
        blocks.append((block_start, end_y - 1))

    return blocks


def _find_decorative_lines(
    rows: list[dict],
    start_y: int,
    end_y: int,
    min_y: int,
) -> list[tuple[int, float]]:
    gold_values = _smooth([row["gold"] for row in rows])
    candidates = []

    y = start_y
    while y < end_y:
        if y < min_y:
            y += 1
            continue

        if gold_values[y] < 0.018:
            y += 1
            continue

        segment_start = y
        peak = gold_values[y]
        while y < end_y and gold_values[y] >= 0.012:
            peak = max(peak, gold_values[y])
            y += 1

        segment_end = y - 1
        if segment_end - segment_start <= 10:
            center = (segment_start + segment_end) // 2
            width_score = peak * 100
            candidates.append((center, width_score))

    return candidates


def _find_blank_band(
    rows: list[dict],
    top_y: int,
    bottom_y: int,
) -> tuple[int, int] | None:
    if bottom_y - top_y < 18:
        return None

    best_start = top_y
    best_score = -1.0

    for start in range(top_y, bottom_y - 12):
        end = min(start + 40, bottom_y)
        window = rows[start:end]
        avg_ink = sum(row["ink"] for row in window) / len(window)
        height = end - start
        score = height - (avg_ink * 900)

        if avg_ink < 0.02 and score > best_score:
            best_score = score
            best_start = start

    band_height = bottom_y - best_start
    if band_height < 12:
        return None

    return best_start, bottom_y


def detect_name_zone(image: Image.Image) -> tuple[int, int]:
    """
    Locate the blank name band on a certificate template.

    Uses full layout analysis:
    1. Find static text blocks in the upper/middle area
    2. Find decorative name underline below the header text
    3. Pick the cleanest blank band between them
    """
    height = image.size[1]
    rows = _analyze_rows(image)

    upper_start = int(height * 0.24)
    upper_end = int(height * 0.62)
    text_blocks = _find_text_blocks(rows, upper_start, upper_end)

    if text_blocks:
        title_blocks = text_blocks[:3]
        header_end = max(block[1] for block in title_blocks)
    else:
        header_end = int(height * 0.38)

    line_search_start = header_end + 8
    line_search_end = int(height * 0.56)
    decorative_lines = _find_decorative_lines(
        rows,
        line_search_start,
        line_search_end,
        min_y=header_end + 10,
    )

    if decorative_lines:
        decorative_lines.sort(key=lambda item: item[1], reverse=True)
        line_y = decorative_lines[0][0]
    else:
        dark_values = _smooth([row["dark"] for row in rows])
        line_y = None
        for y in range(line_search_start, line_search_end):
            if y < header_end + 14:
                continue
            if dark_values[y] > 0.12 and dark_values[y] > dark_values[y - 1]:
                local = dark_values[max(0, y - 1): min(height, y + 2)]
                if sum(local) / len(local) > 0.10:
                    line_y = y
                    break
        if line_y is None:
            line_y = int(height * 0.47)

    zone_top = header_end + 10
    zone_bottom = line_y - 8
    blank_band = _find_blank_band(rows, zone_top, zone_bottom)

    if blank_band:
        return blank_band

    fallback_top = header_end + 14
    fallback_bottom = max(fallback_top + 28, line_y - 6)
    return fallback_top, fallback_bottom


def _fit_font(
    draw: ImageDraw.ImageDraw,
    name: str,
    font_path: str,
    max_width: int,
    max_height: int,
    start_size: int,
) -> tuple[ImageFont.FreeTypeFont, tuple[int, int, int, int]]:
    font_size = start_size

    while font_size >= MIN_FONT_SIZE:
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if text_width <= max_width and text_height <= max_height:
            return font, bbox

        font_size -= 1

    font = ImageFont.truetype(font_path, MIN_FONT_SIZE)
    bbox = draw.textbbox((0, 0), name, font=font)
    return font, bbox


def compute_name_position(
    image: Image.Image,
    name: str,
    font_path: str,
    font_size: int = DEFAULT_FONT_SIZE,
) -> tuple[int, int, ImageFont.FreeTypeFont]:
    width, height = image.size
    zone_top, zone_bottom = detect_name_zone(image)
    zone_height = max(zone_bottom - zone_top, 20)

    max_text_width = int(width * MAX_TEXT_WIDTH_RATIO)
    max_text_height = int(zone_height * 0.92)

    draw = ImageDraw.Draw(image)
    font, bbox = _fit_font(
        draw,
        name,
        font_path,
        max_text_width,
        max_text_height,
        font_size,
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) // 2
    y = zone_top + max((zone_height - text_height) // 2, 0)
    y = max(zone_top, min(y, zone_bottom - text_height))

    return x, y, font


def generate_certificate(
    template_bytes: bytes,
    name: str,
    font_path: str | None = None,
    font_size: int = DEFAULT_FONT_SIZE,
) -> bytes:
    if not name.strip():
        raise ValueError("Name cannot be empty.")

    font_path = font_path or get_font_path()
    image = load_template(template_bytes)
    draw = ImageDraw.Draw(image)

    x, y, font = compute_name_position(image, name, font_path, font_size)
    draw.text((x, y), name, font=font, fill=NAME_TEXT_COLOR)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def preview_certificate(
    template_bytes: bytes,
    sample_name: str,
    font_path: str | None = None,
) -> bytes:
    font_path = font_path or get_font_path()
    image = load_template(template_bytes)
    draw = ImageDraw.Draw(image)

    x, y, font = compute_name_position(image, sample_name, font_path)
    draw.text((x, y), sample_name, font=font, fill=NAME_TEXT_COLOR)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
