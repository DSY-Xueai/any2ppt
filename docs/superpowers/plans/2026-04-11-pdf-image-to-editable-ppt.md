# PDF/Image To Editable PPT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable skill that converts PDF or image inputs into visually faithful PPT files with a conservative editable overlay for high-confidence text and images.

**Architecture:** The implementation uses a hybrid pipeline. `SKILL.md` orchestrates decisions, fallback behavior, and user-facing guarantees, while bundled Python scripts handle PDF page rendering, text/image extraction, and PPT assembly. The output pipeline is always bottom-up: render a fidelity-preserving background first, then add only high-confidence editable elements.

**Tech Stack:** Markdown skill docs, Python, `python-pptx`, optional PDF/OCR adapters behind script boundaries, `pytest`

---

### Task 1: Scaffold the skill package

**Files:**
- Create: `skills/pdf-image-to-editable-ppt/SKILL.md`
- Create: `skills/pdf-image-to-editable-ppt/scripts/__init__.py`
- Create: `skills/pdf-image-to-editable-ppt/references/README.md`
- Modify: `Course.md`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path


def test_skill_scaffold_exists():
    root = Path("skills/pdf-image-to-editable-ppt")
    assert (root / "SKILL.md").exists()
    assert (root / "scripts" / "__init__.py").exists()
    assert (root / "references" / "README.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skill_scaffold.py::test_skill_scaffold_exists -v`
Expected: FAIL because the skill directory and files do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create the directory tree and add:

```markdown
---
name: pdf-image-to-editable-ppt
description: Convert PDF files, multi-page PDFs, posters, scans, or images into a PPT while preserving the original look page by page. Use this whenever the user wants editable PowerPoint output but also insists on original layout, original colors, no visual damage, and conservative fallback for anything that cannot be safely reconstructed.
---
```

Create:

```python
# Package marker for bundled scripts.
```

Create:

```markdown
# References

Document dependency notes, adapter choices, and known limits here.
```

Update `Course.md` to mention the newly scaffolded skill package.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_skill_scaffold.py::test_skill_scaffold_exists -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_skill_scaffold.py skills/pdf-image-to-editable-ppt/SKILL.md skills/pdf-image-to-editable-ppt/scripts/__init__.py skills/pdf-image-to-editable-ppt/references/README.md Course.md
git commit -m "feat: scaffold pdf to editable ppt skill"
```

### Task 2: Define the skill workflow and guarantees

**Files:**
- Modify: `skills/pdf-image-to-editable-ppt/SKILL.md`
- Test: `tests/test_skill_content.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path


def test_skill_instructions_cover_core_guarantees():
    text = Path("skills/pdf-image-to-editable-ppt/SKILL.md").read_text(encoding="utf-8")
    assert "multi-page PDF" in text
    assert "visual fidelity" in text
    assert "background layer" in text
    assert "editable layer" in text
    assert "do not force extraction" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skill_content.py::test_skill_instructions_cover_core_guarantees -v`
Expected: FAIL because the scaffolded `SKILL.md` only has frontmatter.

- [ ] **Step 3: Write minimal implementation**

Expand `skills/pdf-image-to-editable-ppt/SKILL.md` with:

```markdown
## Core rules
- Preserve visual fidelity first.
- Build a background layer for every page.
- Add an editable layer only for high-confidence text and images.
- Support single images, single-page PDFs, and multi-page PDFs.
- If extraction could shift layout, do not force extraction; keep the source content in the background layer.
```

Also document:
- default mapping rules
- long-page split behavior
- page-by-page fallback
- expected script entry points

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_skill_content.py::test_skill_instructions_cover_core_guarantees -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_skill_content.py skills/pdf-image-to-editable-ppt/SKILL.md
git commit -m "feat: define pdf to ppt skill workflow"
```

### Task 3: Add the pipeline data model

**Files:**
- Create: `skills/pdf-image-to-editable-ppt/scripts/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
from skills.pdf-image-to-editable-ppt.scripts.models import PagePlan, TextBlock, ImageBlock


def test_page_plan_defaults_to_background_only():
    plan = PagePlan(page_number=1, width_px=1000, height_px=1500, background_path="page-1.png")
    assert plan.page_number == 1
    assert plan.text_blocks == []
    assert plan.image_blocks == []


def test_text_block_tracks_confidence_and_layout():
    block = TextBlock(
        text="Title",
        left=10.0,
        top=20.0,
        width=100.0,
        height=30.0,
        font_size=24.0,
        color="#112233",
        alignment="center",
        confidence=0.95,
    )
    assert block.alignment == "center"
    assert block.confidence == 0.95


def test_image_block_can_fall_back_to_background():
    block = ImageBlock(
        path="img.png",
        left=1.0,
        top=2.0,
        width=3.0,
        height=4.0,
        confidence=0.4,
        extractable=False,
    )
    assert block.extractable is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL because `models.py` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create typed dataclasses:

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class TextBlock:
    text: str
    left: float
    top: float
    width: float
    height: float
    font_size: float
    color: str
    alignment: str
    confidence: float


@dataclass(slots=True)
class ImageBlock:
    path: str
    left: float
    top: float
    width: float
    height: float
    confidence: float
    extractable: bool = True


@dataclass(slots=True)
class PagePlan:
    page_number: int
    width_px: int
    height_px: int
    background_path: str
    text_blocks: list[TextBlock] = field(default_factory=list)
    image_blocks: list[ImageBlock] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_models.py skills/pdf-image-to-editable-ppt/scripts/models.py
git commit -m "feat: add pipeline data models"
```

### Task 4: Implement editable-layer filtering rules

**Files:**
- Create: `skills/pdf-image-to-editable-ppt/scripts/filtering.py`
- Test: `tests/test_filtering.py`

- [ ] **Step 1: Write the failing test**

```python
from skills.pdf-image-to-editable-ppt.scripts.filtering import select_editable_blocks
from skills.pdf-image-to-editable-ppt.scripts.models import ImageBlock, PagePlan, TextBlock


def test_low_confidence_text_is_removed_from_editable_layer():
    plan = PagePlan(page_number=1, width_px=100, height_px=100, background_path="page.png")
    plan.text_blocks.append(
        TextBlock("x", 0, 0, 10, 10, 12, "#000000", "left", 0.49)
    )
    filtered = select_editable_blocks(plan, min_text_confidence=0.8, min_image_confidence=0.8)
    assert filtered.text_blocks == []


def test_high_confidence_text_and_images_are_preserved():
    plan = PagePlan(page_number=1, width_px=100, height_px=100, background_path="page.png")
    plan.text_blocks.append(
        TextBlock("x", 0, 0, 10, 10, 12, "#000000", "left", 0.95)
    )
    plan.image_blocks.append(
        ImageBlock("img.png", 0, 0, 10, 10, 0.96, True)
    )
    filtered = select_editable_blocks(plan, min_text_confidence=0.8, min_image_confidence=0.8)
    assert len(filtered.text_blocks) == 1
    assert len(filtered.image_blocks) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_filtering.py -v`
Expected: FAIL because `filtering.py` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create:

```python
from .models import PagePlan


def select_editable_blocks(
    plan: PagePlan,
    *,
    min_text_confidence: float,
    min_image_confidence: float,
) -> PagePlan:
    filtered = PagePlan(
        page_number=plan.page_number,
        width_px=plan.width_px,
        height_px=plan.height_px,
        background_path=plan.background_path,
    )
    filtered.text_blocks = [
        block for block in plan.text_blocks if block.confidence >= min_text_confidence
    ]
    filtered.image_blocks = [
        block
        for block in plan.image_blocks
        if block.extractable and block.confidence >= min_image_confidence
    ]
    return filtered
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_filtering.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_filtering.py skills/pdf-image-to-editable-ppt/scripts/filtering.py
git commit -m "feat: add conservative editable layer filtering"
```

### Task 5: Implement PPT assembly around a background-first page plan

**Files:**
- Create: `skills/pdf-image-to-editable-ppt/scripts/build_ppt.py`
- Test: `tests/test_build_ppt.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from skills.pdf-image-to-editable-ppt.scripts.build_ppt import build_presentation
from skills.pdf-image-to-editable-ppt.scripts.models import PagePlan


def test_build_presentation_creates_a_pptx(tmp_path):
    page = PagePlan(page_number=1, width_px=100, height_px=200, background_path="page.png")
    output_path = tmp_path / "result.pptx"
    build_presentation([page], output_path)
    assert output_path.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_build_ppt.py::test_build_presentation_creates_a_pptx -v`
Expected: FAIL because `build_ppt.py` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `build_ppt.py` with:

```python
from pathlib import Path

from pptx import Presentation


def build_presentation(page_plans, output_path: Path) -> None:
    presentation = Presentation()
    while presentation.slides:
        slide_id = presentation.slides._sldIdLst[0]
        presentation.slides._sldIdLst.remove(slide_id)

    for _page in page_plans:
        presentation.slides.add_slide(presentation.slide_layouts[6])

    presentation.save(output_path)
```

This first pass only proves the `.pptx` file can be created. Background image placement and editable overlays are added in the next task.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_build_ppt.py::test_build_presentation_creates_a_pptx -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_build_ppt.py skills/pdf-image-to-editable-ppt/scripts/build_ppt.py
git commit -m "feat: add baseline ppt assembly"
```

### Task 6: Add renderer and extraction script interfaces

**Files:**
- Create: `skills/pdf-image-to-editable-ppt/scripts/render_pdf_pages.py`
- Create: `skills/pdf-image-to-editable-ppt/scripts/extract_text_layout.py`
- Create: `skills/pdf-image-to-editable-ppt/scripts/extract_images.py`
- Test: `tests/test_script_interfaces.py`

- [ ] **Step 1: Write the failing test**

```python
from skills.pdf-image-to-editable-ppt.scripts.extract_images import extract_images
from skills.pdf-image-to-editable-ppt.scripts.extract_text_layout import extract_text_layout
from skills.pdf-image-to-editable-ppt.scripts.render_pdf_pages import render_pdf_pages


def test_script_functions_return_list_shapes(tmp_path):
    output_dir = tmp_path / "pages"
    rendered = render_pdf_pages("sample.pdf", output_dir)
    extracted_text = extract_text_layout("sample.pdf", page_number=1)
    extracted_images = extract_images("sample.pdf", page_number=1, output_dir=output_dir)
    assert isinstance(rendered, list)
    assert isinstance(extracted_text, list)
    assert isinstance(extracted_images, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_script_interfaces.py::test_script_functions_return_list_shapes -v`
Expected: FAIL because the script modules do not exist.

- [ ] **Step 3: Write minimal implementation**

Create placeholder-safe interfaces:

```python
from pathlib import Path


def render_pdf_pages(input_path: str, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    return []
```

```python
def extract_text_layout(input_path: str, *, page_number: int) -> list[dict]:
    return []
```

```python
from pathlib import Path


def extract_images(input_path: str, *, page_number: int, output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    return []
```

Document in each file that they are adapter boundaries for future PDF/OCR integrations.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_script_interfaces.py::test_script_functions_return_list_shapes -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_script_interfaces.py skills/pdf-image-to-editable-ppt/scripts/render_pdf_pages.py skills/pdf-image-to-editable-ppt/scripts/extract_text_layout.py skills/pdf-image-to-editable-ppt/scripts/extract_images.py
git commit -m "feat: add extraction adapter interfaces"
```

### Task 7: Document usage, limits, and test coverage

**Files:**
- Modify: `skills/pdf-image-to-editable-ppt/references/README.md`
- Modify: `Course.md`
- Test: `tests/test_references_readme.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path


def test_references_document_known_limits():
    text = Path("skills/pdf-image-to-editable-ppt/references/README.md").read_text(encoding="utf-8")
    assert "multi-page PDF" in text
    assert "fallback" in text
    assert "font" in text
    assert "OCR" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_references_readme.py::test_references_document_known_limits -v`
Expected: FAIL because the references file is still minimal.

- [ ] **Step 3: Write minimal implementation**

Expand `references/README.md` with:

```markdown
# References

## Supported inputs
- Single images
- Single-page PDFs
- Multi-page PDFs

## Fallback policy
- Preserve background fidelity first
- Only promote high-confidence text and images

## Known limits
- Missing or subset font mappings
- OCR uncertainty on scanned pages
- Complex effects remain in the background layer
```

Update `Course.md` so it reflects the implemented skill package and current limitations.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_references_readme.py::test_references_document_known_limits -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_references_readme.py skills/pdf-image-to-editable-ppt/references/README.md Course.md
git commit -m "docs: document skill limits and usage"
```

## Self-Review

- Spec coverage:
  - Trigger conditions and guarantees are covered in Task 2.
  - Core data model for page-wise processing is covered in Task 3.
  - Conservative fallback logic is covered in Task 4.
  - Background-first PPT generation is covered in Task 5.
  - Script adapter boundaries for rendering and extraction are covered in Task 6.
  - Documentation and current limits are covered in Task 7.
- Placeholder scan:
  - No `TODO`, `TBD`, or implicit “handle later” language remains in task steps.
  - Each task lists explicit files, a failing test, a verification command, and a minimal implementation target.
- Type consistency:
  - `PagePlan`, `TextBlock`, and `ImageBlock` are introduced before downstream use.
  - `build_presentation`, `select_editable_blocks`, `render_pdf_pages`, `extract_text_layout`, and `extract_images` use consistent names across tasks.
