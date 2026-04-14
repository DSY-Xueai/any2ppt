# Course

## 当前项目状态
- `skills/pdf-image-to-editable-ppt` 采用**混合策略**：渲染背景图保证视觉保真 + 原生 PDF 文字叠加为可编辑文本框。
- 阶段一 runtime pipeline 已完成并单独提交。
- 阶段二已补到两层：
  - `2A`：文字严格拟合校验、常见效果映射、stage2 保守增强入口。
  - `2B`：页面分层、矢量候选映射、blend 分组回退基础设施。

## 本轮新增或变更
- **策略重构**：从"纯色背景+图表裁剪"改为"渲染背景图+原生文字叠加"混合策略。
  - `convert_to_ppt.py` 移除 `detect_background_color`、`extract_images`、`_remove_overlapping_text` 调用。
  - 每页始终嵌入渲染 PNG 作为全页背景图（`bg_color=None`），保证视觉保真。
  - 原生 PDF 文字以透明文本框叠加在背景上，保持可编辑性。
  - 图表裁剪不再执行（图表已在背景图中）。
- **修复坐标系错位**（保留）：原生 PDF 文字坐标 ×RENDER_SCALE=2 对齐渲染像素空间。
- **修复 EMU 精度**（保留）：`build_ppt.py` 中 `int()` → `round()`。
- **字号校正系数**（保留）：0.70 → 0.75，参数化。

## 关键修改文件
- `Course.md`
- `skills/pdf-image-to-editable-ppt/scripts/models.py`
- `skills/pdf-image-to-editable-ppt/scripts/page_segmentation.py` (新建)
- `skills/pdf-image-to-editable-ppt/scripts/extract_text_layout.py`
- `skills/pdf-image-to-editable-ppt/scripts/extract_images.py`
- `skills/pdf-image-to-editable-ppt/scripts/build_ppt.py`
- `skills/pdf-image-to-editable-ppt/scripts/convert_to_ppt.py`
- `skills/pdf-image-to-editable-ppt/scripts/page_planner.py`
- `skills/pdf-image-to-editable-ppt/scripts/filtering.py`
- `skills/pdf-image-to-editable-ppt/scripts/stage2_enhance.py`

## 运行入口
- `skills/pdf-image-to-editable-ppt/scripts/convert_to_ppt.py`
- `skills/pdf-image-to-editable-ppt/scripts/build_ppt.py`

## 运行时依赖
- `PyMuPDF` (fitz) — PDF 页面渲染
- `Pillow` (PIL) — 图像处理
- `python-pptx` (pptx) — PPT 生成
- `pytesseract` + Tesseract OCR — 文字识别（需 chi_sim 语言包）
- `PaddleOCR` (可选) — 备选 OCR

## 当前注意事项
- 混合策略下，每页 PPT 由全页背景图 + 可编辑文本框组成。背景图保证视觉保真，文字可点击编辑。
- Tesseract 中文包需手动安装到 tessdata 目录，或使用项目根目录下的 `tessdata/`（通过 `TESSDATA_PREFIX` 环境变量）。
- OCR 仅在图片型 PDF（无原生文字）时启用；原生文字 PDF 直接提取，无 OCR 误差。
- `RENDER_SCALE = 2` 必须与 `render_pdf_pages.py` 中 `fitz.Matrix(2, 2)` 保持一致。
- `page_segmentation.py`、`extract_images.py` 等模块保留但不在主流程中调用，供后续可选增强模式使用。
- 2B 复杂矢量真重建、多层透明/混合效果真重建还没落地。
- `tessdata/` 和生成的 `*_assets/` 目录不应进入 git 提交。
