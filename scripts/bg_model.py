#!/usr/bin/env python3
"""Background modeling and repair module.

Builds a clean background image by:
1. Adaptive background color detection (edge sampling)
2. Using the original image as base (preserving real background)
3. Inpainting foreground/text regions from surrounding pixels

Usage:
    from bg_model import build_background
    bg = build_background(img_rgb, text_mask=mask)
"""

from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_background(
    img: np.ndarray,
    text_mask: np.ndarray | None = None,
    fg_hint_mask: np.ndarray | None = None,
    period: int = 32,
) -> np.ndarray:
    """Build a clean background image from the input.

    Args:
        img: Input image (H, W, 3) RGB uint8.
        text_mask: Binary mask (H, W) where text regions = 255.
        fg_hint_mask: Optional binary mask of known foreground regions.
        period: Tile period (kept for API compatibility, unused in new approach).

    Returns:
        Clean background image (H, W, 3) RGB uint8.
    """
    h, w = img.shape[:2]

    if text_mask is None:
        text_mask = np.zeros((h, w), dtype=np.uint8)
    if fg_hint_mask is None:
        fg_hint_mask = np.zeros((h, w), dtype=np.uint8)

    # Combined exclusion mask
    exclude = ((text_mask > 0) | (fg_hint_mask > 0)).astype(np.uint8) * 255

    # Step 1: Detect background color adaptively
    bg_color, bg_std, candidate_mask = _detect_background(img, exclude)
    logger.info(
        "Background color: RGB(%d,%d,%d), std=%.1f",
        int(bg_color[0]), int(bg_color[1]), int(bg_color[2]), bg_std,
    )

    # Step 2: Build background — strategy depends on whether we have fg hints
    has_fg_hint = np.any(fg_hint_mask > 0)

    if has_fg_hint:
        # Refinement pass: use original image + inpainting for pixel-accurate bg
        bg = _original_based_background(img, exclude, bg_color)
    else:
        # Initial pass: smooth background for foreground detection
        bg = _smooth_background(img, bg_color, candidate_mask, text_mask)

    return bg


# ---------------------------------------------------------------------------
# Step 1: Adaptive background detection
# ---------------------------------------------------------------------------


def _detect_background(
    img: np.ndarray, exclude_mask: np.ndarray
) -> tuple[np.ndarray, float, np.ndarray]:
    """Detect the dominant background color by sampling image edges.

    Returns:
        bg_color: (3,) float array — dominant background RGB.
        bg_std: float — standard deviation of background pixels.
        candidate_mask: (H, W) bool — pixels likely belonging to background.
    """
    h, w = img.shape[:2]

    # Sample from edges (5% border on each side)
    margin_y = max(5, int(h * 0.05))
    margin_x = max(5, int(w * 0.05))

    edge_mask = np.zeros((h, w), dtype=bool)
    edge_mask[:margin_y, :] = True   # top
    edge_mask[-margin_y:, :] = True  # bottom
    edge_mask[:, :margin_x] = True   # left
    edge_mask[:, -margin_x:] = True  # right

    # Exclude known text/foreground from edge sampling
    edge_mask &= (exclude_mask == 0)

    edge_pixels = img[edge_mask].reshape(-1, 3).astype(np.float32)

    if len(edge_pixels) < 10:
        # Fallback: use all non-excluded pixels
        valid = exclude_mask == 0
        edge_pixels = img[valid].reshape(-1, 3).astype(np.float32)

    if len(edge_pixels) < 10:
        # Ultimate fallback
        bg_color = np.array([255.0, 255.0, 255.0])
        return bg_color, 30.0, np.ones((h, w), dtype=bool)

    # Find dominant color via histogram peak (faster than KMeans)
    bg_color = np.median(edge_pixels, axis=0)
    bg_std = float(np.mean(np.std(edge_pixels, axis=0)))

    # Adaptive threshold: pixels within N standard deviations of bg_color
    threshold = max(35.0, bg_std * 2.5)

    all_pixels = img.reshape(-1, 3).astype(np.float32)
    dists = np.linalg.norm(all_pixels - bg_color, axis=1)
    candidate_flat = dists < threshold

    candidate_mask = candidate_flat.reshape(h, w)
    # Exclude known foreground/text
    candidate_mask &= (exclude_mask == 0)

    return bg_color, bg_std, candidate_mask


# ---------------------------------------------------------------------------
# Step 2a: Smooth background for initial foreground detection
# ---------------------------------------------------------------------------


def _smooth_background(
    img: np.ndarray,
    bg_color: np.ndarray,
    candidate_mask: np.ndarray,
    text_mask: np.ndarray,
) -> np.ndarray:
    """Build a smooth background for the initial foreground detection pass.

    Replaces non-background pixels with bg_color and applies smoothing.
    This creates enough contrast for diff-based foreground detection while
    preserving the general background appearance.

    Args:
        img: Original image (H, W, 3) RGB uint8.
        bg_color: Detected background color (3,) float.
        candidate_mask: (H, W) bool — pixels likely belonging to background.
        text_mask: Binary mask (H, W) uint8 where text regions = 255.

    Returns:
        Smooth background (H, W, 3) RGB uint8.
    """
    bg = img.copy()
    fill = np.clip(bg_color, 0, 255).astype(np.uint8)

    # Replace non-candidate pixels (likely foreground) with bg_color
    bg[~candidate_mask] = fill

    # Also replace text regions
    if text_mask is not None:
        bg[text_mask > 0] = fill

    # Smooth to blend transitions and reduce artifacts
    bg = cv2.GaussianBlur(bg, (21, 21), 0)

    return bg


# ---------------------------------------------------------------------------
# Step 2b: Original-based background with inpainting (refinement pass)
# ---------------------------------------------------------------------------


def _original_based_background(
    img: np.ndarray,
    exclude_mask: np.ndarray,
    bg_color: np.ndarray,
) -> np.ndarray:
    """Build background by starting from original image and inpainting excluded regions.

    This preserves the original background pixel-for-pixel in areas without
    foreground/text, and uses inpainting to fill the excluded regions from
    surrounding real background pixels.

    Args:
        img: Original image (H, W, 3) RGB uint8.
        exclude_mask: Binary mask (H, W) uint8, regions to repair = 255.
        bg_color: Detected background color (3,) float.

    Returns:
        Clean background (H, W, 3) RGB uint8.
    """
    bg = img.copy()

    # If nothing to repair, return original
    if not np.any(exclude_mask > 0):
        return bg

    # Pre-fill excluded regions with bg_color for better inpainting seed
    fill_color = np.clip(bg_color, 0, 255).astype(np.uint8)
    bg[exclude_mask > 0] = fill_color

    # Build inpaint mask: excluded regions dilated slightly to cover edges
    inpaint_mask = _build_inpaint_mask(exclude_mask)

    # Inpaint to blend filled regions with surrounding real background
    bg = _inpaint(bg, inpaint_mask)

    return bg


def _build_inpaint_mask(exclude_mask: np.ndarray) -> np.ndarray:
    """Build inpaint mask from exclusion mask with slight dilation for edge coverage."""
    # Dilate to cover boundary artifacts
    kernel = np.ones((5, 5), np.uint8)
    inpaint_mask = cv2.dilate(exclude_mask, kernel, iterations=1)
    return inpaint_mask


# ---------------------------------------------------------------------------
# Inpainting
# ---------------------------------------------------------------------------


def _inpaint(bg: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Inpaint masked regions using dual-pass approach."""
    bgr = cv2.cvtColor(bg, cv2.COLOR_RGB2BGR)

    # First pass: Telea algorithm with larger radius for structural fill
    repaired = cv2.inpaint(bgr, mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)

    # Second pass: NS method for smoother blending on the same regions
    repaired = cv2.inpaint(repaired, mask, inpaintRadius=5, flags=cv2.INPAINT_NS)

    result = cv2.cvtColor(repaired, cv2.COLOR_BGR2RGB)

    # Gaussian blur at inpainting boundaries to smooth seams
    blurred = cv2.GaussianBlur(result, (5, 5), 0)
    boundary = cv2.dilate(mask, np.ones((5, 5), np.uint8)) - cv2.erode(mask, np.ones((3, 3), np.uint8))
    boundary_mask = (boundary > 0)

    output = result.copy()
    output[boundary_mask] = blurred[boundary_mask]

    return output
