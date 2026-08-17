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


def _is_colored_ink(r: int, g: int, b: int) -> bool:
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    saturation = max_c - min_c
    return saturation > 25 and max_c > 50


def _analyze_image(image: Image.Image) -> dict:
    width, height = image.size
    pixels = image.load()
    margin = int(width * 0.06)
    center_x = width // 2
    center_strip_width = int(width * 0.25)
    
    col_ink = [0] * width
    row_ink = [0] * height
    center_ink = [0] * height
    
    for y in range(height):
        for x in range(margin, width - margin):
            r, g, b = pixels[x, y]
            if _is_colored_ink(r, g, b):
                row_ink[y] += 1
                if abs(x - center_x) < center_strip_width:
                    center_ink[y] += 1
    
    span = max(width - 2 * margin, 1)
    for y in range(height):
        row_ink[y] /= span
        center_ink[y] /= (2 * center_strip_width)
    
    return {
        "row_ink": row_ink,
        "center_ink": center_ink,
        "width": width,
        "height": height,
    }


def _smooth(values: list[float], radius: int = 3) -> list[float]:
    if not values:
        return values
    smoothed = []
    for index in range(len(values)):
        start = max(0, index - radius)
        end = min(len(values), index + radius + 1)
        smoothed.append(sum(values[start:end]) / (end - start))
    return smoothed


def _find_header_blocks(analysis: dict) -> int:
    row_ink = analysis["row_ink"]
    height = analysis["height"]
    
    header_end = int(height * 0.32)
    in_block = False
    block_start = 0
    
    for y in range(int(height * 0.10), int(height * 0.38)):
        if row_ink[y] > 0.025:
            if not in_block:
                in_block = True
                block_start = y
        elif in_block:
            if y - block_start >= 8:
                header_end = y
            in_block = False
    
    return header_end


def _find_name_underline(row_ink: list[float], header_end: int, height: int) -> tuple[int, float] | None:
    smoothed = _smooth(row_ink, radius=3)
    
    search_start = max(header_end + 20, int(height * 0.40))
    search_end = min(int(height * 0.60), len(smoothed) - 1)
    
    best_line_y = None
    best_line_score = 0
    in_candidate = False
    candidate_start = 0
    candidate_pixels = []
    
    for y in range(search_start, search_end):
        val = smoothed[y]
        
        if val > 0.015:
            if not in_candidate:
                in_candidate = True
                candidate_start = y
                candidate_pixels = []
            candidate_pixels.append(y)
        else:
            if in_candidate and len(candidate_pixels) >= 3:
                candidate_end = candidate_pixels[-1]
                width = candidate_end - candidate_start + 1
                
                if width <= 15:
                    avg_strength = sum(smoothed[p] for p in candidate_pixels) / len(candidate_pixels)
                    score = avg_strength * 100
                    
                    if score > best_line_score:
                        best_line_score = score
                        best_line_y = (candidate_start + candidate_end) // 2
            
            in_candidate = False
            candidate_pixels = []
    
    if in_candidate and len(candidate_pixels) >= 3:
        candidate_end = candidate_pixels[-1]
        width = candidate_end - candidate_start + 1
        if width <= 15:
            avg_strength = sum(smoothed[p] for p in candidate_pixels) / len(candidate_pixels)
            score = avg_strength * 100
            if score > best_line_score:
                best_line_y = (candidate_start + candidate_end) // 2
    
    if best_line_y is not None:
        return best_line_y, best_line_score
    return None


def _find_blank_rectangle(center_ink: list[float], header_end: int, height: int) -> tuple[int, int] | None:
    smoothed = _smooth(center_ink, radius=4)
    
    search_start = max(header_end + 25, int(height * 0.42))
    search_end = int(height * 0.58)
    
    best_start = search_start
    best_blank_score = -999.0
    window_size = 35
    
    for start in range(search_start, search_end - window_size):
        window = smoothed[start:start + window_size]
        avg = sum(window) / len(window)
        max_val = max(window)
        
        if max_val > 0.03:
            continue
        
        score = -avg * 2000
        if score > best_blank_score:
            best_blank_score = score
            best_start = start
    
    if best_blank_score > -500:
        return None
    
    return best_start, best_start + window_size


def detect_name_zone(image: Image.Image) -> tuple[int, int]:
    """
    Automatically detect the best name placement zone.
    
    Strategy:
    1. Find where header content ends
    2. Look for a horizontal line/underline in the name area (40-60%)
    3. Name should go ABOVE the line
    4. If no clear line, find the blankest rectangle in center band
    """
    analysis = _analyze_image(image)
    row_ink = analysis["row_ink"]
    center_ink = analysis["center_ink"]
    width = analysis["width"]
    height = analysis["height"]
    
    header_end = _find_header_blocks(analysis)
    
    underline = _find_name_underline(row_ink, header_end, height)
    
    if underline:
        line_y, score = underline
        
        zone_top = line_y - 38
        zone_bottom = line_y - 3
        
        if zone_top < header_end + 15:
            zone_top = header_end + 15
        
        return zone_top, zone_bottom
    
    blank_rect = _find_blank_rectangle(center_ink, header_end, height)
    
    if blank_rect:
        return blank_rect
    
    zone_top = int(height * 0.46)
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