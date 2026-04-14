from __future__ import annotations

from pathlib import Path


_ALIGNMENTS = {0: "left", 1: "center", 2: "right", 3: "justify"}


def _color_to_hex(value: int | None) -> str:
    if value is None:
        return "#000000"
    return f"#{value:06x}"


def _normalize_native_blocks(page_dict: dict) -> list[dict]:
    blocks: list[dict] = []
    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        bbox = block.get("bbox", [0.0, 0.0, 0.0, 0.0])
        spans = [
            span
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span.get("text", "").strip()
        ]
        if not spans:
            continue
        text = " ".join(span["text"].strip() for span in spans)
        blocks.append(
            {
                "text": text,
                "left": float(bbox[0]),
                "top": float(bbox[1]),
                "width": float(bbox[2] - bbox[0]),
                "height": float(bbox[3] - bbox[1]),
                "font_size": float(spans[0].get("size", bbox[3] - bbox[1])),
                "color": _color_to_hex(spans[0].get("color")),
                "alignment": _ALIGNMENTS.get(block.get("align", 0), "left"),
                "confidence": 0.99,
                "font_name": spans[0].get("font"),
            }
        )
    return blocks


def _detect_tesseract_cmd() -> str | None:
    """Return the tesseract executable path if discoverable."""
    import os
    import shutil

    # Allow local tessdata override via project-level directory
    local_tessdata = Path(__file__).resolve().parents[2] / "tessdata"
    if local_tessdata.is_dir():
        os.environ.setdefault("TESSDATA_PREFIX", str(local_tessdata))

    cmd = shutil.which("tesseract")
    if cmd:
        return cmd
    candidate = Path(r"C:/Program Files/Tesseract-OCR/tesseract.exe")
    if candidate.exists():
        return str(candidate)
    return None


def _extract_with_pytesseract(
    image,
    *,
    background_color: str = "#FFFFFF",
    image_height_px: int = 0,
) -> list[dict]:
    try:
        import pytesseract
    except ImportError:
        return []

    tess_cmd = _detect_tesseract_cmd()
    if tess_cmd:
        pytesseract.pytesseract.tesseract_cmd = tess_cmd

    # Determine available languages
    try:
        langs_output = pytesseract.get_languages()
        has_chi = any("chi_sim" in lang for lang in langs_output)
    except Exception:
        has_chi = False

    lang = "chi_sim+eng" if has_chi else "eng"
    config = f"--psm 3 -l {lang}"

    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=config)
    except Exception:
        return []

    from .page_segmentation import estimate_font_size_pt, sample_text_color

    word_items: list[dict] = []
    for text, left, top, width, height, conf in zip(
        data.get("text", []),
        data.get("left", []),
        data.get("top", []),
        data.get("width", []),
        data.get("height", []),
        data.get("conf", []),
    ):
        content = str(text).strip()
        confidence = float(conf) / 100.0 if str(conf).strip() not in {"", "-1"} else -1.0
        if not content or confidence < 0.3:
            continue
        word_items.append(
            {
                "text": content,
                "left": float(left),
                "top": float(top),
                "width": float(width),
                "height": float(height),
                "confidence": confidence,
            }
        )

    lines = _group_words_into_lines(word_items)

    img_h = image_height_px or getattr(image, "height", 0) or 1
    for line in lines:
        color = sample_text_color(
            image,
            int(line["left"]),
            int(line["top"]),
            int(line["width"]),
            int(line["height"]),
            background_color=background_color,
        )
        line["color"] = color
        line["font_size"] = estimate_font_size_pt(line["height"], img_h)
        line["alignment"] = "left"

    return lines


def _group_words_into_lines(
    word_items: list[dict],
    vertical_tolerance_ratio: float = 0.5,
) -> list[dict]:
    """Group word-level OCR results into line-level text blocks."""
    if not word_items:
        return []

    sorted_words = sorted(word_items, key=lambda w: (w["top"], w["left"]))

    lines: list[list[dict]] = []
    current_line: list[dict] = [sorted_words[0]]

    for word in sorted_words[1:]:
        prev = current_line[-1]
        avg_height = (prev["height"] + word["height"]) / 2.0
        tolerance = avg_height * vertical_tolerance_ratio
        if abs(word["top"] - prev["top"]) <= tolerance:
            current_line.append(word)
        else:
            lines.append(current_line)
            current_line = [word]
    lines.append(current_line)

    result: list[dict] = []
    for line_words in lines:
        line_words.sort(key=lambda w: w["left"])
        left = min(w["left"] for w in line_words)
        top = min(w["top"] for w in line_words)
        right = max(w["left"] + w["width"] for w in line_words)
        bottom = max(w["top"] + w["height"] for w in line_words)

        text_parts: list[str] = []
        for i, w in enumerate(line_words):
            if i > 0:
                gap = w["left"] - (line_words[i - 1]["left"] + line_words[i - 1]["width"])
                avg_h = (w["height"] + line_words[i - 1]["height"]) / 2.0
                prev_text = line_words[i - 1]["text"]
                curr_text = w["text"]
                prev_is_cjk = prev_text and ord(prev_text[-1]) > 0x2E80
                curr_is_cjk = curr_text and ord(curr_text[0]) > 0x2E80
                if prev_is_cjk and curr_is_cjk:
                    pass  # No space between CJK characters
                elif gap > avg_h * 0.3:
                    text_parts.append(" ")
            text_parts.append(w["text"])
        text = "".join(text_parts)

        avg_conf = sum(w["confidence"] for w in line_words) / len(line_words)

        result.append(
            {
                "text": text,
                "left": left,
                "top": top,
                "width": right - left,
                "height": bottom - top,
                "confidence": avg_conf,
                "color": "#000000",
                "font_size": bottom - top,
                "alignment": "left",
            }
        )
    return result


def _extract_with_ocr(
    image,
    *,
    background_color: str = "#FFFFFF",
    image_height_px: int = 0,
) -> list[dict]:
    pytesseract_items = _extract_with_pytesseract(
        image,
        background_color=background_color,
        image_height_px=image_height_px,
    )
    if pytesseract_items:
        return pytesseract_items

    try:
        from paddleocr import PaddleOCR
    except ImportError:
        return []

    ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    results = ocr.ocr(image)
    text_items: list[dict] = []
    for line in results or []:
        for bbox, payload in line:
            text, confidence = payload
            xs = [point[0] for point in bbox]
            ys = [point[1] for point in bbox]
            text_items.append(
                {
                    "text": text,
                    "left": float(min(xs)),
                    "top": float(min(ys)),
                    "width": float(max(xs) - min(xs)),
                    "height": float(max(ys) - min(ys)),
                    "font_size": float(max(ys) - min(ys)),
                    "color": "#000000",
                    "alignment": "left",
                    "confidence": float(confidence),
                }
            )
    return text_items


def extract_text_layout(
    input_path: str,
    *,
    page_number: int,
    rendered_image_path: str | None = None,
    background_color: str = "#FFFFFF",
) -> list[dict]:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(source)

    suffix = source.suffix.lower()
    if suffix == ".pdf":
        try:
            import fitz
        except ImportError:
            pass
        else:
            # Native PDF text coordinates are in PDF points.  The rendered
            # page image is produced at 2× zoom (fitz.Matrix(2, 2) in
            # render_pdf_pages.py), so all downstream code — overlap
            # removal, diagram masking, PPT scaling — expects coordinates
            # in rendered-pixel space.  Multiply by RENDER_SCALE to align.
            RENDER_SCALE = 2  # must match Matrix(2, 2) in render_pdf_pages
            with fitz.open(str(source)) as document:
                page = document.load_page(page_number - 1)
                blocks = _normalize_native_blocks(page.get_text("dict"))
                if blocks:
                    for block in blocks:
                        block["left"] *= RENDER_SCALE
                        block["top"] *= RENDER_SCALE
                        block["width"] *= RENDER_SCALE
                        block["height"] *= RENDER_SCALE
                        # font_size stays in points — correct for Pt() in build_ppt
                    return blocks

        # Native text empty (image-based PDF) — fall back to OCR on rendered image
        if rendered_image_path and Path(rendered_image_path).exists():
            from PIL import Image

            image = Image.open(rendered_image_path)
            try:
                return _extract_with_ocr(
                    image,
                    background_color=background_color,
                    image_height_px=image.height,
                )
            finally:
                image.close()
        return []

    from PIL import Image

    image = Image.open(source)
    try:
        return _extract_with_ocr(
            image,
            background_color=background_color,
            image_height_px=image.height,
        )
    finally:
        close = getattr(image, "close", None)
        if callable(close):
            close()
