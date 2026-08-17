"""
Certificate generation with automatic name placement.

Detects the name underline on the template (common on participation
certificates) and centers the name above it. Falls back to a typical
name band when no underline is found.
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
DEFAULT_FONT_SIZE = 70
MAX_TEXT_WIDTH_RATIO = 0.82
UNDERLINE_SCAN_START = 0.30
UNDERLINE_SCAN_END = 0.72
UNDERLINE_DARK_THRESHOLD = 110
UNDERLINE_MIN_COVERAGE = 0.22
GAP_ABOVE_LINE = 10
FALLBACK_Y_RATIO = 0.46


def get_font_path() -> str:
    """Download and cache a bold font for consistent rendering."""
    if FONT_CACHE.exists():
        return str(FONT_CACHE)

    FONT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(FONT_URL, FONT_CACHE)
    return str(FONT_CACHE)


def load_template(template_bytes: bytes) -> Image.Image:
    image = Image.open(BytesIO(template_bytes))
    return image.convert("RGB")


def _row_dark_coverage(pixels, width: int, y: int, threshold: int) -> float:
    dark = 0
    for x in range(width):
        r, g, b = pixels[x, y]
        if r < threshold and g < threshold and b < threshold:
            dark += 1
    return dark / width


def detect_name_line_y(image: Image.Image) -> int | None:
    """
    Find the horizontal underline where the participant name usually goes.

    Certificates often have a decorative line under the blank name area.
    We scan the middle band of the image and pick the strongest line.
    """
    width, height = image.size
    pixels = image.load()

    start_y = int(height * UNDERLINE_SCAN_START)
    end_y = int(height * UNDERLINE_SCAN_END)

    best_y = None
    best_score = 0.0

    for y in range(start_y, end_y):
        coverage = _row_dark_coverage(
            pixels, width, y, UNDERLINE_DARK_THRESHOLD
        )
        if coverage >= UNDERLINE_MIN_COVERAGE and coverage > best_score:
            best_score = coverage
            best_y = y

    return best_y


def _fit_font(
    draw: ImageDraw.ImageDraw,
    name: str,
    font_path: str,
    max_width: int,
    start_size: int,
) -> tuple[ImageFont.FreeTypeFont, tuple[int, int, int, int]]:
    font_size = start_size

    while font_size >= MIN_FONT_SIZE:
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
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
    """
    Compute x, y, and font so the name sits centered in the right spot.

    Strategy:
    1. Detect underline -> place text centered above it.
    2. No underline -> place text in the usual certificate name band (~46%).
    3. Shrink font until the name fits within 82% of image width.
    """
    width, height = image.size
    max_text_width = int(width * MAX_TEXT_WIDTH_RATIO)

    draw = ImageDraw.Draw(image)
    font, bbox = _fit_font(draw, name, font_path, max_text_width, font_size)

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) // 2

    underline_y = detect_name_line_y(image)
    if underline_y is not None:
        y = underline_y - text_height - GAP_ABOVE_LINE
    else:
        y = int(height * FALLBACK_Y_RATIO) - text_height // 2

    y = max(0, min(y, height - text_height))
    return x, y, font


def generate_certificate(
    template_bytes: bytes,
    name: str,
    font_path: str | None = None,
    font_size: int = DEFAULT_FONT_SIZE,
) -> bytes:
    """Return PNG bytes for one personalized certificate."""
    if not name.strip():
        raise ValueError("Name cannot be empty.")

    font_path = font_path or get_font_path()
    image = load_template(template_bytes)
    draw = ImageDraw.Draw(image)

    x, y, font = compute_name_position(image, name, font_path, font_size)
    draw.text((x, y), name, font=font, fill=(0, 0, 0))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def preview_placement(
    template_bytes: bytes,
    sample_name: str,
    font_path: str | None = None,
) -> tuple[bytes, dict]:
    """
    Generate a preview and return placement metadata for the UI.
    """
    font_path = font_path or get_font_path()
    image = load_template(template_bytes)
    underline_y = detect_name_line_y(image)
    x, y, font = compute_name_position(image, sample_name, font_path)

    draw = ImageDraw.Draw(image)
    draw.text((x, y), sample_name, font=font, fill=(0, 0, 0))

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    bbox = draw.textbbox((x, y), sample_name, font=font)
    info = {
        "x": x,
        "y": y,
        "font_size": font.size,
        "underline_detected": underline_y is not None,
        "underline_y": underline_y,
        "text_box": bbox,
    }
    return buffer.getvalue(), info
