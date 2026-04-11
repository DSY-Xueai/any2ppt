from __future__ import annotations

from pathlib import Path

from PIL import Image

from .build_ppt import build_presentation
from .extract_images import extract_images
from .extract_text_layout import extract_text_layout
from .filtering import select_editable_blocks
from .page_planner import build_page_plan
from .render_pdf_pages import render_pdf_pages


def _count_pdf_pages(source: Path) -> int:
    try:
        import fitz
    except ImportError:
        return 0

    with fitz.open(str(source)) as document:
        return len(document)


def convert_to_ppt(input_path: str, output_path: Path) -> None:
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
            plan = build_page_plan(
                page_number=index + 1,
                width_px=width_px,
                height_px=height_px,
                background_path=background_path,
                source_type="pdf",
                text_items=extract_text_layout(str(source), page_number=index + 1),
                image_items=extract_images(
                    str(source),
                    page_number=index + 1,
                    output_dir=output_dir / f"images-{index + 1}",
                ),
            )
            page_plans.append(
                select_editable_blocks(
                    plan,
                    min_text_confidence=0.8,
                    min_image_confidence=0.8,
                )
            )
    else:
        with Image.open(source) as image:
            width_px, height_px = image.size
        plan = build_page_plan(
            page_number=1,
            width_px=width_px,
            height_px=height_px,
            background_path=str(source),
            source_type="image",
            text_items=extract_text_layout(str(source), page_number=1),
            image_items=extract_images(
                str(source),
                page_number=1,
                output_dir=output_dir / "images-1",
            ),
        )
        page_plans.append(
            select_editable_blocks(
                plan,
                min_text_confidence=0.8,
                min_image_confidence=0.8,
            )
        )

    build_presentation(page_plans, output_path)
