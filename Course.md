# Course

## 当前项目状态
- `skills/pdf-image-to-editable-ppt` 处于 runtime-upgrade 实现阶段。
- 当前已接入依赖探测、页面模型扩展，并正在补真实 PDF 渲染、文字提取、图片提取、PPT 输出与端到端转换入口。

## 本轮新增或变更
- 新增 `skills/pdf-image-to-editable-ppt/scripts/dependencies.py`，用于探测 `fitz`、`PIL`、`paddleocr`、`pptx`。
- 扩展 `skills/pdf-image-to-editable-ppt/scripts/models.py` 的 `PagePlan`，新增 `source_type`、`page_width_points`、`page_height_points`。
- 开始把占位脚本接成真实管线：
  - `render_pdf_pages.py` 支持 PyMuPDF 渲染 PDF 页面。
  - `extract_text_layout.py` 支持 PDF 原生文本优先、OCR fallback。
  - `extract_images.py` 支持 PDF 原生图片提取和栅格图高置信裁切。
  - `page_planner.py` 负责把标准化文本/图片字典组装成 `PagePlan`。
  - `build_ppt.py` 支持背景优先的 PPT 输出。
  - `convert_to_ppt.py` 提供端到端转换入口。
- 新增与升级相关测试：
  - `tests/test_dependencies.py`
  - `tests/test_models_runtime.py`
  - `tests/test_render_pdf_pages.py`
  - `tests/test_extract_text_layout.py`
  - `tests/test_extract_images.py`
  - `tests/test_page_planner.py`
  - `tests/test_build_ppt_runtime.py`
  - `tests/test_convert_to_ppt.py`

## 关键修改文件
- `Course.md`
- `skills/pdf-image-to-editable-ppt/SKILL.md`
- `skills/pdf-image-to-editable-ppt/references/README.md`
- `skills/pdf-image-to-editable-ppt/scripts/dependencies.py`
- `skills/pdf-image-to-editable-ppt/scripts/models.py`
- `skills/pdf-image-to-editable-ppt/scripts/render_pdf_pages.py`
- `skills/pdf-image-to-editable-ppt/scripts/extract_text_layout.py`
- `skills/pdf-image-to-editable-ppt/scripts/extract_images.py`
- `skills/pdf-image-to-editable-ppt/scripts/page_planner.py`
- `skills/pdf-image-to-editable-ppt/scripts/build_ppt.py`
- `skills/pdf-image-to-editable-ppt/scripts/convert_to_ppt.py`
- `tests/*.py`

## 运行入口
- `skills/pdf-image-to-editable-ppt/SKILL.md`
- `skills/pdf-image-to-editable-ppt/scripts/convert_to_ppt.py`
- `skills/pdf-image-to-editable-ppt/scripts/build_ppt.py`
- `skills/pdf-image-to-editable-ppt/scripts/render_pdf_pages.py`
- `skills/pdf-image-to-editable-ppt/scripts/extract_text_layout.py`
- `skills/pdf-image-to-editable-ppt/scripts/extract_images.py`

## 当前注意事项
- OCR 不是硬依赖；不可用时必须回退到背景优先输出。
- 当前阶段仍以文字和图片层为主，复杂矢量、透明效果、字体拟合属于后续增强项。
- 当前 worktree 中的本轮改动尚未提交；若适合提交，需要先征求用户确认。
