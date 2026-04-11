from __future__ import annotations

from .models import ImageBlock, PagePlan, TextBlock


def build_page_plan(
    *,
    page_number,
    width_px,
    height_px,
    background_path,
    text_items,
    image_items,
    source_type="image",
    page_width_points=None,
    page_height_points=None,
):
    plan = PagePlan(
        page_number=page_number,
        width_px=width_px,
        height_px=height_px,
        background_path=background_path,
        source_type=source_type,
        page_width_points=page_width_points,
        page_height_points=page_height_points,
    )
    plan.text_blocks = [TextBlock(**item) for item in text_items]
    plan.image_blocks = [ImageBlock(**item) for item in image_items]
    return plan
