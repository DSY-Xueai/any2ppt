#!/usr/bin/env python3
"""Convert image files to a single PDF for downstream processing by pdf_to_md.py.

Usage:
    python3 image_to_pdf.py image1.png image2.jpg -o output.pdf
    python3 image_to_pdf.py images_dir/ -o output.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def collect_images(paths: list[str]) -> list[Path]:
    """Collect image file paths from arguments (files or directories)."""
    result: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for ext in sorted(SUPPORTED_EXTENSIONS):
                result.extend(sorted(path.glob(f"*{ext}")))
        elif path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            result.append(path)
        else:
            print(f"[WARN] Skipping unsupported file: {path}", file=sys.stderr)
    return result


def images_to_pdf(image_paths: list[Path], output_pdf: Path) -> Path:
    """Convert a list of image files into a single PDF (one image per page)."""
    if not image_paths:
        raise ValueError("No valid images provided")

    rgb_images: list[Image.Image] = []
    for p in image_paths:
        img = Image.open(p)
        if img.mode != "RGB":
            img = img.convert("RGB")
        rgb_images.append(img)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    first, *rest = rgb_images
    first.save(output_pdf, "PDF", save_all=True, append_images=rest, resolution=150.0)

    for img in rgb_images:
        img.close()

    print(f"[OK] Created PDF: {output_pdf} ({len(rgb_images)} page(s))")
    return output_pdf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert images to PDF for ppt-master pipeline"
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Image files or directories containing images",
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output PDF path",
    )
    args = parser.parse_args()

    image_paths = collect_images(args.inputs)
    if not image_paths:
        print("[ERROR] No valid image files found", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Found {len(image_paths)} image(s): {[p.name for p in image_paths]}")
    images_to_pdf(image_paths, Path(args.output))


if __name__ == "__main__":
    main()
