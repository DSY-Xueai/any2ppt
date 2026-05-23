from __future__ import annotations

import sys
import types
from pathlib import Path

from PIL import Image

from image_to_ppt import _parse_reference_option
from scripts.bg_model import _should_use_fg_hint
from scripts.fg_extract import _keep_detector_mask
from scripts.text_detect import (
    _adjust_font_size,
    _filter_noise,
    _select_font,
    _should_force_regular_weight,
    _try_tesseract,
)


def test_filter_noise_keeps_meaningful_all_caps_text() -> None:
    boxes = [
        {"text": "PROJECT ROADMAP", "box": (0, 0, 100, 20), "confidence": 0.95},
        {"text": "MCOULE ST:SETMP", "box": (0, 30, 100, 20), "confidence": 0.95},
    ]

    filtered = _filter_noise(boxes)

    assert [item["text"] for item in filtered] == ["PROJECT ROADMAP"]


def test_tesseract_fallback_uses_requested_language(
    tmp_path: Path, monkeypatch
) -> None:
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (60, 20), "white").save(image_path)

    captured = {}

    fake_tesseract = types.SimpleNamespace(tesseract_cmd="")

    def image_to_data(img, lang, output_type):
        captured["lang"] = lang
        return {
            "text": ["Hello"],
            "conf": ["95"],
            "left": [1],
            "top": [2],
            "width": [30],
            "height": [10],
            "block_num": [1],
            "par_num": [1],
            "line_num": [1],
        }

    fake_module = types.SimpleNamespace(
        Output=types.SimpleNamespace(DICT="DICT"),
        pytesseract=fake_tesseract,
        image_to_data=image_to_data,
    )
    monkeypatch.setitem(sys.modules, "pytesseract", fake_module)

    boxes = _try_tesseract(image_path, 0.7, lang="eng")

    assert captured["lang"] == "eng"
    assert boxes and boxes[0]["text"] == "Hello"


def test_reference_option_is_explicit() -> None:
    assert _parse_reference_option(reference=False, no_reference=False) is False
    assert _parse_reference_option(reference=True, no_reference=False) is True
    assert _parse_reference_option(reference=True, no_reference=True) is False


def test_huge_foreground_hint_is_rejected_for_background_refinement() -> None:
    assert not _should_use_fg_hint(nonzero_pixels=600, total_pixels=1000)
    assert _should_use_fg_hint(nonzero_pixels=200, total_pixels=1000)


def test_huge_detector_mask_is_rejected() -> None:
    assert not _keep_detector_mask(nonzero_pixels=600, total_pixels=1000)
    assert _keep_detector_mask(nonzero_pixels=200, total_pixels=1000)


def test_large_chinese_title_uses_calligraphy_font_without_bold() -> None:
    text = "辛亥革命的烽火岁月"

    assert _select_font(text, 80.0) == "华文行楷"
    assert _should_force_regular_weight(text, 80.0)
    assert _adjust_font_size(text, 100.0) == 88.0
    assert _adjust_font_size("红色全景资源创意展示", 20.0) == 20.0
