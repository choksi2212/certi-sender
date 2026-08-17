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
MAX_TEXT_WIDTH_RATIO = 0.80
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


def _analyze_rows(image: Image.Image) -> list[dict]:
    width, height = image.size
    pixels = image.load()
    margin = int(width * 0.08)
    span = max(width - 2 * margin, 1)

    rows = []
    for y in range(height):
        ink = 0
        for x in range(margin, width - margin):
            r, g, b = pixels[x, y]
            if _is_colored_ink(r, g, b):
                ink += 1
        rows.append({
            "y": y,
            "ink": ink / span,
        })
    return rows


def _is_colored_ink(r: int, g: int, b: int) -> bool:
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    saturation = max_c - min_c
    return saturation > 30 and max_c > 60


def _smooth(values: list[float], radius: int = 3) -> list[float]:
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
    threshold = 0.03

    for y in range(start_y, end_y):
        if rows[y]["ink"] >= threshold:
            if not in_block:
                block_start = y
                in_block = True
        elif in_block:
            if y - block_start >= 5:
                blocks.append((block_start, y - 1))
            in_block = False

    if in_block and end_y - block_start >= 5:
        blocks.append((block_start, end_y - 1))

    return blocks


def _find_horizontal_line_candidates(rows: list[dict], start_y: int, end_y: int) -> list[dict]:
    smoothed = _smooth([r["ink"] for r in rows], radius=2)
    
    candidates = []
    for y in range(start_y, min(end_y, len(rows) - 1)):
        current = smoothed[y]
        next_row = smoothed[y + 1] if y + 1 < len(rows) else 0
        
        if current > 0.015 and next_row > 0.015:
            width = 1
            while y + width < len(rows) and smoothed[y + width] > 0.010:
                width += 1
                if width > 12:
                    break
            
            if 2 <= width <= 12:
                center_y = y + width // 2
                candidates.append({
                    "start": y,
                    "end": y + width - 1,
                    "center": center_y,
                    "width": width,
                    "strength": current,
                })
    
    candidates.sort(key=lambda x: x["strength"], reverse=True)
    return candidates


def _find_blank_band_by_scan(rows: list[dict], top_y: int, bottom_y: int) -> tuple[int, int]:
    if bottom_y - top_y < 15:
        return top_y, top_y + 30
    
    ink_values = [rows[y]["ink"] for y in range(top_y, bottom_y)]
    smoothed = _smooth(ink_values, radius=4)
    
    best_score = -999.0
    best_start = 0
    window_size = 30
    
    for start in range(0, len(smoothed) - window_size):
        window = smoothed[start:start + window_size]
        avg_ink = sum(window) / len(window)
        max_val = max(window)
        score = -(avg_ink * 3000) - (max_val * 5000)
        
        if score > best_score:
            best_score = score
            best_start = start
    
    return top_y + best_start, top_y + best_start + window_size


def detect_name_zone(image: Image.Image) -> tuple[int, int]:
    """
    Detect the best zone for placing participant name.
    
    Algorithm:
    1. Find the header area (title text)
    2. Search for underlines/decoration BELOW the header
    3. The name zone is the blank area ABOVE the underline
    4. Fall back to proportional positioning if no underline found
    """
    width, height = image.size
    rows = _analyze_rows(image)
    
    header_end = int(height * 0.30)
    text_blocks = _find_text_blocks(rows, int(height * 0.12), int(height * 0.38))
    if text_blocks:
        header_end = max(block[1] for block in text_blocks[:3])
    
    min_name_y = int(height * 0.40)
    name_area_top = max(header_end + 15, min_name_y)
    name_area_bottom = int(height * 0.58)
    
    underline_candidates = _find_horizontal_line_candidates(rows, name_area_top, name_area_bottom)
    
    if underline_candidates:
        best_line = underline_candidates[0]
        line_y = best_line["center"]
        
        zone_top = name_area_top
        zone_bottom = line_y - 4
        
        if zone_bottom - zone_top >= 20:
            found_top, found_bottom = _find_blank_band_by_scan(rows, zone_top, zone_bottom)
            if found_bottom - found_top >= 15:
                return found_top, found_bottom
        
        zone_height = zone_bottom - zone_top
        if zone_height < 20:
            zone_top = line_y - 35
            zone_bottom = line_y - 4
        
        return zone_top, zone_bottom
    
    zone_top, zone_bottom = _find_blank_band_by_scan(rows, name_area_top, name_area_bottom)
    if zone_bottom - zone_top >= 20:
        return zone_top, zone_bottom
    
    zone_top = int(height * 0.44)
    zone_bottom = int(height * 0.54)
    return zone_top, zone_bottom


def _fit_font(
    draw: ImageDraw.ImageDraw,
    name: str,
    font_path: str,
    max_width: int,
    max_height: int,
    start_size: int,
) -> tuple[ImageFont.FreeTypeFont, tuple]:
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
    max_text_height = int(zone_height * 0.88)

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