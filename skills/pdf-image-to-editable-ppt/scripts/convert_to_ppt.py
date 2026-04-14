from __future__ import annotations

from pathlib import Path

from PIL import Image

from .build_ppt import build_presentation
from .effect_mapping import filter_mappable_effects
from .extract_images import extract_images
from .extract_text_layout import extract_text_layout
from .filtering import select_editable_blocks
from .page_planner import build_page_plan
from .page_segmentation import detect_background_color
from .render_pdf_pages import render_pdf_pages
from .stage2_enhance import apply_stage2_enhancements
from .text_fitting import mark_fit_verified, validate_text_block_fit


def _count_pdf_pages(source: Path) -> int:
    try:
        import fitz
    except ImportError:
        return 0

    with fitz.open(str(source)) as document:
        return len(document)


def _maybe_apply_stage2(plan):
    for block in plan.text_blocks:
        candidate = {
            "text": block.text,
            "font_name": block.font_name or "Arial",
            "font_size": block.font_size,
            "line_height": block.line_height or block.height,
            "left": block.left,
            "top": block.top,
            "width": block.width,
            "height": block.height,
            "alignment": block.alignment,
            "expected_lines": 1,
            "predicted_lines": 1,
            "position_delta": 0.0,
        }
        if validate_text_block_fit(candidate):
            mark_fit_verified(block)
    plan.effect_blocks = filter_mappable_effects(
        [{"effect_type": effect.effect_type, "confidence": effect.confidence, "complexity": "simple"} for effect in getattr(plan, "effect_blocks", [])]
    )
    return apply_stage2_enhancements(plan)


def _remove_overlapping_text(
    text_items: list[dict],
    image_items: list[dict],
    overlap_threshold: float = 0.5,
) -> list[dict]:
    """Remove text blocks that overlap significantly with diagram image regions."""
    if not image_items:
        return text_items

    result: list[dict] = []
    for text in text_items:
        t_left = text["left"]
        t_top = text["top"]
        t_right = t_left + text["width"]
        t_bottom = t_top + text["height"]
        t_area = text["width"] * text["height"]

        overlaps = False
        for img in image_items:
            i_left = img["left"]
            i_top = img["top"]
            i_right = i_left + img["width"]
            i_bottom = i_top + img["height"]

            inter_left = max(t_left, i_left)
            inter_top = max(t_top, i_top)
            inter_right = min(t_right, i_right)
            inter_bottom = min(t_bottom, i_bottom)

            if inter_right > inter_left and inter_bottom > inter_top:
                inter_area = (inter_right - inter_left) * (inter_bottom - inter_top)
                if t_area > 0 and inter_area / t_area >= overlap_threshold:
                    overlaps = True
                    break

        if not overlaps:
            result.append(text)
    return result


def convert_to_ppt(input_path: str, output_path: Path, enable_stage2: bool = False) -> None:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(source)

    output_dir = output_path.parent / f"{output_path.stem}_assets"
    output_dir.mkdir(parents=True, exist_ok=True)

    page_plans = []
    if source.suffix.lower() == ".pdf":
        rendered_pages = render_pdf_pages(str(source), output_dir / "pages")
        page_count = len(rendered_pages) or _count_pdf_pages(source)
        for index in range(page_count):
            background_path = rendered_pages[index] if index < len(rendered_pages) else ""
            if not background_path:
                continue
            with Image.open(background_path) as image:
                width_px, height_px = image.size

            # Detect background color for editable mode
            with Image.open(background_path) as image:
                bg_color_raw, bg_confidence = detect_background_color(image)
                bg_color = bg_color_raw if bg_confidence >= 0.75 else None

            # Extract text — passes rendered image for OCR fallback on image-based PDFs
            text_items = extract_text_layout(
                str(source),
                page_number=index + 1,
                rendered_image_path=background_path,
                background_color=bg_color or "#FFFFFF",
            )

            # Extract diagram regions (non-text visual content)
            image_items = extract_images(
                str(source),
                page_number=index + 1,
                output_dir=output_dir / f"images-{index + 1}",
                rendered_image_path=background_path,
                text_blocks=text_items,
                background_color=bg_color,
            )

            # Remove text blocks that overlap significantly with diagram regions
            text_items = _remove_overlapping_text(text_items, image_items)

            plan = build_page_plan(
                page_number=index + 1,
                width_px=width_px,
                height_px=height_px,
                background_path=background_path,
                source_type="pdf",
                text_items=text_items,
                image_items=image_items,
                background_color=bg_color,
            )
            filtered = select_editable_blocks(
                plan,
                min_text_confidence=0.5,
                min_image_confidence=0.5,
            )
            page_plans.append(_maybe_apply_stage2(filtered) if enable_stage2 else filtered)
    else:
        with Image.open(source) as image:
            width_px, height_px = image.size
            bg_color_raw, bg_confidence = detect_background_color(image)
            bg_color = bg_color_raw if bg_confidence >= 0.75 else None

        text_items = extract_text_layout(
            str(source),
            page_number=1,
            background_color=bg_color or "#FFFFFF",
        )

        image_items = extract_images(
            str(source),
            page_number=1,
            output_dir=output_dir / "images-1",
            rendered_image_path=str(source),
            text_blocks=text_items,
            background_color=bg_color,
        )

        text_items = _remove_overlapping_text(text_items, image_items)

        plan = build_page_plan(
            page_number=1,
            width_px=width_px,
            height_px=height_px,
            background_path=str(source),
            source_type="image",
            text_items=text_items,
            image_items=image_items,
            background_color=bg_color,
        )
        filtered = select_editable_blocks(
            plan,
            min_text_confidence=0.5,
            min_image_confidence=0.5,
        )
        page_plans.append(_maybe_apply_stage2(filtered) if enable_stage2 else filtered)

    build_presentation(page_plans, output_path)
