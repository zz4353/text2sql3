from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Font helpers (same as ocr memory/t1.py)
# ---------------------------------------------------------------------------

def _load_font(size: int) -> ImageFont.ImageFont:
    font_names = (
        "consola.ttf",
        "cour.ttf",
        "DejaVuSansMono.ttf",
        "arial.ttf",
    )
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _font_metrics(font: ImageFont.ImageFont) -> tuple[int, int]:
    probe = Image.new("RGB", (1, 1), "white")
    draw = ImageDraw.Draw(probe)
    bbox = draw.textbbox((0, 0), "M", font=font)
    char_width = max(1, bbox[2] - bbox[0])
    line_height = max(1, bbox[3] - bbox[1] + 5)
    return char_width, line_height


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    if not text:
        return 0
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


# ---------------------------------------------------------------------------
# Pixel-accurate text wrapping (same as ocr memory/t1.py)
# ---------------------------------------------------------------------------

def _wrap_line_by_pixels(
    line: str,
    max_width: int,
    *,
    draw: ImageDraw.ImageDraw,
    font: ImageFont.ImageFont,
) -> list[str]:
    if not line:
        return [""]
    max_width = max(1, max_width)
    if _text_width(draw, line, font) <= max_width:
        return [line]

    wrapped: list[str] = []
    remaining = line
    while remaining:
        if _text_width(draw, remaining, font) <= max_width:
            wrapped.append(remaining)
            break
        low, high, fit = 1, len(remaining), 1
        while low <= high:
            mid = (low + high) // 2
            if _text_width(draw, remaining[:mid], font) <= max_width:
                fit = mid
                low = mid + 1
            else:
                high = mid - 1
        prefix = remaining[:fit]
        break_at = prefix.rfind(" ")
        if break_at > 0 and prefix[:break_at].strip():
            wrapped.append(prefix[:break_at].rstrip())
            remaining = remaining[break_at + 1:].lstrip()
        else:
            wrapped.append(prefix.rstrip() or prefix)
            remaining = remaining[fit:].lstrip()
    return wrapped or [""]


def _wrap_text_by_pixels(
    text: str,
    max_width: int,
    *,
    draw: ImageDraw.ImageDraw,
    font: ImageFont.ImageFont,
    tabsize: int = 4,
) -> list[str]:
    lines: list[str] = []
    for raw_line in text.expandtabs(tabsize).splitlines() or [""]:
        lines.extend(_wrap_line_by_pixels(raw_line, max_width, draw=draw, font=font))
    return lines


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_text_pages(
    text: str,
    *,
    header: str | None = None,
    width: int = 512,
    max_height: int = 512,
    min_height: int = 64,
    font_size: int = 11,
    margin: int = 2,
    background: str = "white",
) -> list[Image.Image]:
    """
    Render plain text into paginated images (font/wrapping style of ocr memory/t1.py).
    Width is fixed. Height shrinks to fit content, capped at max_height.
    Long content is split across multiple pages.

    If header is provided, it is drawn in red at the top of every page.
    """
    if not text.strip():
        return []

    font = _load_font(font_size)
    _, line_height = _font_metrics(font)

    probe = Image.new("RGB", (width, 1), background)
    probe_draw = ImageDraw.Draw(probe)

    content_width = width - 2 * margin
    wrapped = _wrap_text_by_pixels(text, content_width, draw=probe_draw, font=font)
    blank_gap = max(1, int(line_height * 0.4))

    header_height = (line_height + blank_gap) if header else 0

    # Build list of (line_text, pixel_height) per line
    line_items: list[tuple[str, int]] = []
    for line in wrapped:
        if line.strip() == "":
            line_items.append(("", blank_gap))
        else:
            line_items.append((line, line_height))

    # Paginate by accumulated pixel height
    usable_height = max_height - 2 * margin - header_height
    pages_data: list[list[tuple[str, int]]] = []
    current_page: list[tuple[str, int]] = []
    current_h = 0
    for item in line_items:
        if current_page and current_h + item[1] > usable_height:
            pages_data.append(current_page)
            current_page = []
            current_h = 0
        current_page.append(item)
        current_h += item[1]
    if current_page:
        pages_data.append(current_page)

    result: list[Image.Image] = []
    for page_lines in pages_data:
        content_h = sum(h for _, h in page_lines) + header_height
        page_h = min(max_height, max(min_height, content_h + 2 * margin))

        img = Image.new("RGB", (width, page_h), background)
        draw = ImageDraw.Draw(img)
        y = margin

        if header:
            draw.text((margin, y), header, fill="red", font=font)
            y += line_height + blank_gap

        for line_text, h in page_lines:
            if line_text:
                draw.text((margin, y), line_text, fill="black", font=font)
            y += h
        result.append(img)

    return result


def render_text_pages_b64(text: str, **kwargs) -> list[str]:
    """
    Same as render_text_pages but returns base64-encoded PNG strings.
    """
    images = render_text_pages(text, **kwargs)
    out: list[str] = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        out.append(base64.b64encode(buf.getvalue()).decode("ascii"))
    return out
