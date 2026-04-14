from __future__ import annotations

from collections import Counter
from typing import Sequence

from PIL import Image


def detect_background_color(
    image: Image.Image, margin_ratio: float = 0.05
) -> tuple[str, float]:
    """Sample pixels from page margins to detect the dominant background color.

    Returns ``(hex_color, confidence)`` where *confidence* is the fraction of
    sampled margin pixels that match the dominant quantized color.  A low
    confidence indicates a gradient or photographic background that should
    not be replaced by a solid fill.
    """
    img = image.convert("RGB")
    w, h = img.size
    margin_x = max(int(w * margin_ratio), 1)
    margin_y = max(int(h * margin_ratio), 1)

    pixels: list[tuple[int, int, int]] = []
    for x in range(w):
        for y in range(margin_y):
            pixels.append(img.getpixel((x, y)))
        for y in range(h - margin_y, h):
            pixels.append(img.getpixel((x, y)))
    for y in range(margin_y, h - margin_y):
        for x in range(margin_x):
            pixels.append(img.getpixel((x, y)))
        for x in range(w - margin_x, w):
            pixels.append(img.getpixel((x, y)))

    if not pixels:
        return "#FFFFFF", 0.0

    # Quantize to reduce noise (group similar colors)
    quantized = [(_q(r), _q(g), _q(b)) for r, g, b in pixels]
    counter = Counter(quantized)
    mode_color, mode_count = counter.most_common(1)[0]
    confidence = mode_count / len(quantized)
    return "#{:02X}{:02X}{:02X}".format(*mode_color), confidence


def _q(value: int, step: int = 8) -> int:
    """Quantize a color channel value to reduce noise."""
    return min(round(value / step) * step, 255)


def sample_text_color(
    image: Image.Image,
    left: int,
    top: int,
    width: int,
    height: int,
    background_color: str = "#FFFFFF",
) -> str:
    """Sample the dominant non-background color within a text bounding box."""
    img = image.convert("RGB")
    bg_r, bg_g, bg_b = _hex_to_rgb(background_color)
    tolerance = 60

    crop_left = max(left, 0)
    crop_top = max(top, 0)
    crop_right = min(left + width, img.width)
    crop_bottom = min(top + height, img.height)
    if crop_right <= crop_left or crop_bottom <= crop_top:
        return "#000000"

    region = img.crop((crop_left, crop_top, crop_right, crop_bottom))
    pixels: list[tuple[int, int, int]] = []
    for x in range(region.width):
        for y in range(region.height):
            r, g, b = region.getpixel((x, y))
            dist = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
            if dist > tolerance:
                pixels.append((_q(r), _q(g), _q(b)))

    if not pixels:
        return "#000000"

    mode_color = Counter(pixels).most_common(1)[0][0]
    return "#{:02X}{:02X}{:02X}".format(*mode_color)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def estimate_font_size_pt(
    bbox_height_px: float,
    image_height_px: int,
    slide_height_pt: float = 540.0,
    correction_factor: float = 0.75,
) -> float:
    """Convert OCR bounding box pixel height to approximate PowerPoint point size.

    The rendered page is at 2x resolution.  ``correction_factor`` accounts for
    the bbox including ascender/descender space beyond the nominal font size.
    """
    if image_height_px <= 0:
        return 12.0
    raw_pt = bbox_height_px * slide_height_pt / image_height_px
    corrected = raw_pt * correction_factor
    return max(round(corrected * 2) / 2, 6.0)


def find_non_text_regions(
    image: Image.Image,
    text_boxes: Sequence[tuple[int, int, int, int]],
    background_color: str,
    min_area: int = 2000,
    max_page_ratio: float = 0.5,
    text_pad: int = 10,
) -> list[tuple[int, int, int, int]]:
    """Detect non-text visual regions (diagrams, icons) in the page image.

    Returns list of (left, top, right, bottom) bounding boxes.
    Regions covering more than ``max_page_ratio`` of the total page area are
    discarded — they usually indicate that the whole slide was merged into one
    blob, which defeats the purpose of extracting individual diagram crops.
    """
    img = image.convert("RGB")
    w, h = img.size
    bg_r, bg_g, bg_b = _hex_to_rgb(background_color)
    threshold = 40
    page_area = w * h

    # Use a downscaled version for performance (images can be 2752x1536 at 2x)
    scale = 4
    sw, sh = w // scale, h // scale
    if sw == 0 or sh == 0:
        return []

    small = img.resize((sw, sh), Image.NEAREST)
    mask = [[False] * sw for _ in range(sh)]

    for y in range(sh):
        for x in range(sw):
            r, g, b = small.getpixel((x, y))
            dist = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
            mask[y][x] = dist > threshold

    # Mask out text regions (with padding to avoid merging text into diagrams)
    pad_s = max(text_pad // scale, 1)
    for left, top, right, bottom in text_boxes:
        sl = max(left // scale - pad_s, 0)
        st = max(top // scale - pad_s, 0)
        sr = min(right // scale + pad_s, sw)
        sb = min(bottom // scale + pad_s, sh)
        for y in range(st, sb):
            for x in range(sl, sr):
                mask[y][x] = False

    # Find connected components using simple flood fill
    visited = [[False] * sw for _ in range(sh)]
    regions: list[tuple[int, int, int, int]] = []

    for start_y in range(sh):
        for start_x in range(sw):
            if not mask[start_y][start_x] or visited[start_y][start_x]:
                continue
            # BFS flood fill
            min_x, min_y = start_x, start_y
            max_x, max_y = start_x, start_y
            stack = [(start_x, start_y)]
            visited[start_y][start_x] = True
            count = 0
            while stack:
                cx, cy = stack.pop()
                count += 1
                min_x = min(min_x, cx)
                min_y = min(min_y, cy)
                max_x = max(max_x, cx)
                max_y = max(max_y, cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < sw and 0 <= ny < sh and not visited[ny][nx] and mask[ny][nx]:
                        visited[ny][nx] = True
                        stack.append((nx, ny))

            area = count * scale * scale
            if area >= min_area:
                regions.append((
                    min_x * scale,
                    min_y * scale,
                    min((max_x + 1) * scale, w),
                    min((max_y + 1) * scale, h),
                ))

    merged = merge_nearby_boxes(regions)

    # Discard regions that are too large (likely the whole page content)
    return [
        r for r in merged
        if (r[2] - r[0]) * (r[3] - r[1]) / page_area <= max_page_ratio
    ]


def merge_nearby_boxes(
    boxes: list[tuple[int, int, int, int]],
    gap: int = 20,
) -> list[tuple[int, int, int, int]]:
    """Merge bounding boxes that overlap or are within ``gap`` pixels."""
    if not boxes:
        return []

    merged = list(boxes)
    changed = True
    while changed:
        changed = False
        new_merged: list[tuple[int, int, int, int]] = []
        used = [False] * len(merged)
        for i in range(len(merged)):
            if used[i]:
                continue
            current = merged[i]
            for j in range(i + 1, len(merged)):
                if used[j]:
                    continue
                if _boxes_near(current, merged[j], gap):
                    current = (
                        min(current[0], merged[j][0]),
                        min(current[1], merged[j][1]),
                        max(current[2], merged[j][2]),
                        max(current[3], merged[j][3]),
                    )
                    used[j] = True
                    changed = True
            new_merged.append(current)
        merged = new_merged
    return merged


def _boxes_near(
    a: tuple[int, int, int, int],
    b: tuple[int, int, int, int],
    gap: int,
) -> bool:
    """Check if two boxes overlap or are within ``gap`` pixels of each other."""
    return not (
        a[2] + gap < b[0]
        or b[2] + gap < a[0]
        or a[3] + gap < b[1]
        or b[3] + gap < a[1]
    )
