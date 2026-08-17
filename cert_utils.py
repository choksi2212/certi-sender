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

# Zones as ratios of image height
NAME_ZONE_TOP_RATIO = 0.38
NAME_ZONE_BOTTOM_RATIO = 0.62


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


def _find_horizontal_lines(rows: list[dict], start_y: int, end_y: int) -> list[dict]:
    smoothed = _smooth([r["ink"] for r in rows], radius=2)
    
    lines = []
    in_line = False
    line_start = 0
    line_pixels = []
    
    for y in range(start_y, min(end_y, len(rows))):
        ink_val = smoothed[y]
        
        if ink_val > 0.02:
            if not in_line:
                in_line = True
                line_start = y
                line_pixels = []
            line_pixels.append(y)
        else:
            if in_line and len(line_pixels) >= 3:
                line_end = line_pixels[-1]
                width = line_end - line_start + 1
                avg_ink = sum(smoothed[p] for p in line_pixels) / len(line_pixels)
                
                if width <= 15 and width >= 2:
                    center_y = (line_start + line_end) // 2
                    lines.append({
                        "start": line_start,
                        "end": line_end,
                        "center": center_y,
                        "width": width,
                        "strength": avg_ink,
                    })
            in_line = False
            line_pixels = []
    
    if in_line and len(line_pixels) >= 3:
        line_end = line_pixels[-1]
        width = line_end - line_start + 1
        avg_ink = sum(smoothed[p] for p in line_pixels) / len(line_pixels)
        if width <= 15 and width >= 2:
            center_y = (line_start + line_end) // 2
            lines.append({
                "start": line_start,
                "end": line_end,
                "center": center_y,
                "width": width,
                "strength": avg_ink,
            })
    
    return lines


def _find_blank_zone_by_analysis(rows: list[dict], top_y: int, bottom_y: int) -> tuple[int, int]:
    if bottom_y - top_y < 20:
        return top_y, top_y + 30
    
    ink_values = [rows[y]["ink"] for y in range(top_y, bottom_y)]
    smoothed_ink = _smooth(ink_values, radius=4)
    
    best_start = top_y
    best_blank_score = -999.0
    
    window_size = 25
    
    for start in range(top_y, bottom_y - window_size):
        window = smoothed_ink[start - top_y:start - top_y + window_size]
        avg_ink = sum(window) / len(window)
        
        blank_score = -avg_ink * 1000
        
        for i, val in enumerate(window):
            if val > 0.015:
                blank_score -= 500
        
        if blank_score > best_blank_score:
            best_blank_score = blank_score
            best_start = start
    
    zone_top = best_start
    zone_bottom = min(best_start + 35, bottom_y)
    
    if zone_bottom - zone_top < 15:
        zone_bottom = zone_top + 30
    
    return zone_top, zone_bottom


def _find_blankest_band(rows: list[dict], top_y: int, bottom_y: int, min_height: int = 25) -> tuple[int, int]:
    if bottom_y - top_y < min_height:
        return top_y, top_y + min_height
    
    ink_values = [rows[y]["ink"] for y in range(top_y, bottom_y)]
    smoothed = _smooth(ink_values, radius=5)
    
    best_score = -999.0
    best_start = top_y
    
    for start in range(top_y, bottom_y - min_height):
        window = smoothed[start:top_y + min_height]
        avg = sum(window) / len(window)
        max_val = max(window)
        
        score = -(avg * 2000) - (max_val * 3000)
        
        if score > best_score:
            best_score = score
            best_start = start
    
    return best_start, best_start + min_height


def _find_text_blocks_in_zone(rows: list[dict], start_y: int, end_y: int) -> list[tuple[int, int]]:
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


def _find_decorative_lines(
    rows: list[dict],
    start_y: int,
    end_y: int,
    min_y: int,
) -> list[tuple[int, float]]:
    smoothed = _smooth([row["ink"] for row in rows])
    candidates = []

    y = start_y
    while y < end_y:
        if y < min_y:
            y += 1
            continue

        if smoothed[y] < 0.015:
            y += 1
            continue

        segment_start = y
        peak = smoothed[y]
        while y < end_y and smoothed[y] >= 0.010:
            peak = max(peak, smoothed[y])
            y += 1

        segment_end = y - 1
        if segment_end - segment_start <= 12:
            center = (segment_start + segment_end) // 2
            width_score = peak * 100
            candidates.append((center, width_score))

    return candidates


def _analyze_zone_quality(rows: list[dict], zone_top: int, zone_bottom: int) -> float:
    if zone_bottom - zone_top < 10:
        return -999.0
    
    ink_vals = [rows[y]["ink"] for y in range(zone_top, zone_bottom)]
    avg_ink = sum(ink_vals) / len(ink_vals)
    
    blank_pixels = sum(1 for v in ink_vals if v < 0.01)
    blank_ratio = blank_pixels / len(ink_vals)
    
    quality = -avg_ink * 1000 + blank_ratio * 500
    
    return quality


def detect_name_zone(image: Image.Image) -> tuple[int, int]:
    """
    Locate the optimal name placement zone using multi-strategy analysis.
    
    Strategy 1: Look for horizontal decorative lines (underlines) in the name zone
    Strategy 2: Find the largest blank area in the expected name region
    Strategy 3: Analyze structural layout to infer name area
    
    Returns (zone_top, zone_bottom) pixel coordinates.
    """
    width, height = image.size
    rows = _analyze_rows(image)
    
    name_zone_top = int(height * NAME_ZONE_TOP_RATIO)
    name_zone_bottom = int(height * NAME_ZONE_BOTTOM_RATIO)
    
    header_end = int(height * 0.35)
    text_blocks = _find_text_blocks_in_zone(rows, int(height * 0.18), header_end + 20)
    if text_blocks:
        header_end = max(block[1] for block in text_blocks[:3])
    
    search_start = max(header_end + 5, name_zone_top - 10)
    search_end = name_zone_bottom + 10
    
    candidates = []
    
    lines = _find_horizontal_lines(rows, search_start, search_end)
    for line in lines:
        line_y = line["center"]
        
        zone_top = header_end + 8
        zone_bottom = line_y - 6
        
        if zone_bottom - zone_top < 12:
            zone_bottom = zone_top + 28
        
        blank_top, blank_bottom = _find_blank_zone_by_analysis(rows, zone_top, zone_bottom)
        
        quality = _analyze_zone_quality(rows, blank_top, blank_bottom)
        
        if blank_bottom - blank_top >= 15:
            candidates.append({
                "zone_top": blank_top,
                "zone_bottom": blank_bottom,
                "line_y": line_y,
                "quality": quality,
            })
    
    if not candidates:
        decor_lines = _find_decorative_lines(rows, search_start, search_end, header_end + 10)
        if decor_lines:
            decor_lines.sort(key=lambda x: x[1], reverse=True)
            line_y = decor_lines[0][0]
            
            zone_top = header_end + 8
            zone_bottom = line_y - 6
            
            if zone_bottom - zone_top < 12:
                zone_bottom = zone_top + 28
            
            blank_top, blank_bottom = _find_blank_zone_by_analysis(rows, zone_top, zone_bottom)
            quality = _analyze_zone_quality(rows, blank_top, blank_bottom)
            
            if blank_bottom - blank_top >= 15:
                candidates.append({
                    "zone_top": blank_top,
                    "zone_bottom": blank_bottom,
                    "line_y": line_y,
                    "quality": quality,
                })
    
    if candidates:
        candidates.sort(key=lambda x: x["quality"], reverse=True)
        best = candidates[0]
        return best["zone_top"], best["zone_bottom"]
    
    blank_top, blank_bottom = _find_blankest_band(
        rows, 
        max(search_start, header_end + 10), 
        min(search_end, name_zone_bottom),
        min_height=30
    )
    
    if blank_bottom - blank_top >= 20:
        return blank_top, blank_bottom
    
    fallback_top = max(header_end + 12, int(height * 0.42))
    fallback_bottom = int(height * 0.52)
    
    return fallback_top, fallback_bottom


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