from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops


def _extract_native_pdf_images(source: Path, page_number: int, output_dir: Path) -> list[dict]:
    try:
        import fitz
    except ImportError:
        return []

    image_items: list[dict] = []
    with fitz.open(str(source)) as document:
        page = document.load_page(page_number - 1)
        for index, image_info in enumerate(page.get_images(full=True)):
            xref = image_info[0]
            image_data = document.extract_image(xref)
            extension = image_data.get("ext", "png")
            target = output_dir / f"page-{page_number}-img-{index}.{extension}"
            target.write_bytes(image_data["image"])
            with Image.open(target) as image:
                width, height = image.size
            image_items.append(
                {
                    "path": str(target),
                    "left": 0.0,
                    "top": 0.0,
                    "width": float(width),
                    "height": float(height),
                    "confidence": 0.99,
                    "extractable": True,
                }
            )
    return image_items


def _extract_cropped_images(source: Path, output_dir: Path) -> list[dict]:
    with Image.open(source) as image:
        rgb_image = image.convert("RGB")
        background = Image.new("RGB", rgb_image.size, "white")
        diff = ImageChops.difference(rgb_image, background)
        bbox = diff.getbbox()
        if bbox is None:
            return []
        crop = rgb_image.crop(bbox)
        target = output_dir / f"{source.stem}-crop-0.png"
        crop.save(target)
        left, top, right, bottom = bbox
        return [
            {
                "path": str(target),
                "left": float(left),
                "top": float(top),
                "width": float(right - left),
                "height": float(bottom - top),
                "confidence": 0.9,
                "extractable": True,
            }
        ]


def extract_diagram_regions(
    rendered_image_path: str,
    text_blocks: list[dict],
    background_color: str,
    output_dir: Path,
    page_number: int,
) -> list[dict]:
    """Crop non-text visual regions (diagrams, icons) from a rendered page image."""
    from .page_segmentation import find_non_text_regions

    rendered = Path(rendered_image_path)
    if not rendered.exists():
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(rendered) as image:
        text_boxes = [
            (
                int(b["left"]),
                int(b["top"]),
                int(b["left"] + b["width"]),
                int(b["top"] + b["height"]),
            )
            for b in text_blocks
        ]

        regions = find_non_text_regions(image, text_boxes, background_color)

        image_items: list[dict] = []
        for index, (left, top, right, bottom) in enumerate(regions):
            crop = image.crop((left, top, right, bottom))
            target = output_dir / f"page-{page_number}-diagram-{index}.png"
            crop.save(target)
            image_items.append(
                {
                    "path": str(target),
                    "left": float(left),
                    "top": float(top),
                    "width": float(right - left),
                    "height": float(bottom - top),
                    "confidence": 0.85,
                    "extractable": True,
                }
            )
    return image_items


def extract_images(
    input_path: str,
    *,
    page_number: int,
    output_dir: Path,
    rendered_image_path: str | None = None,
    text_blocks: list[dict] | None = None,
    background_color: str | None = None,
) -> list[dict]:
    """Extract native PDF images, diagram regions, or high-confidence raster crops."""
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(source)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Editable mode: extract diagram regions from the rendered page
    if rendered_image_path and background_color is not None:
        return extract_diagram_regions(
            rendered_image_path,
            text_blocks or [],
            background_color,
            output_dir,
            page_number,
        )

    if source.suffix.lower() == ".pdf":
        return _extract_native_pdf_images(source, page_number, output_dir)
    return _extract_cropped_images(source, output_dir)
