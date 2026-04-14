# Course

## 当前项目状态
- `skills/pdf-image-to-editable-ppt` 已完成架构重建，从"全页背景图+文字叠加"升级为"纯色背景+OCR原生文本框+图表裁剪"模式。
- 阶段一 runtime pipeline 已完成并单独提交。
- 阶段二已补到两层：
  - `2A`：文字严格拟合校验、常见效果映射、stage2 保守增强入口。
  - `2B`：页面分层、矢量候选映射、blend 分组回退基础设施。
- 可编辑模式（editable mode）已落地：OCR 提取中英文文字 → 纯色背景 → 图表裁剪为独立图片。

## 本轮新增或变更
- **修复坐标系错位**：原生 PDF 文字坐标（PDF 点）未乘以渲染缩放因子（2×），导致所有文字元素定位在正确位置的一半。现在 `extract_text_layout.py` 在返回原生文字前对 left/top/width/height ×RENDER_SCALE=2，与 OCR 路径和图表裁剪的像素坐标对齐。
- **修复 EMU 精度**：`build_ppt.py` 中坐标转 EMU 从 `int()` 截断改为 `round()` 四舍五入，减少累积偏移。
- **背景色检测增加置信度**：`detect_background_color()` 返回 `(hex_color, confidence)` 元组，`convert_to_ppt.py` 在置信度 < 0.75 时回退为嵌入全页背景图，避免渐变/图片背景被替换为纯色。
- **字号校正系数调整**：`estimate_font_size_pt()` 校正系数从 0.70 上调至 0.75（更接近实际字体度量），并参数化为 `correction_factor` 参数。

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
- Tesseract 中文包需手动安装到 tessdata 目录，或使用项目根目录下的 `tessdata/`（通过 `TESSDATA_PREFIX` 环境变量）。
- OCR 识别有误差，特别是复杂排版页面（图表内文字标签、密集代码区域）。
- 字号估算基于 bbox 高度的 0.75 校正系数（可通过 `correction_factor` 参数调整），部分场景可能偏大或偏小。
- `RENDER_SCALE = 2` 必须与 `render_pdf_pages.py` 中 `fitz.Matrix(2, 2)` 保持一致；若更改渲染缩放需同步修改。
- 背景色置信度阈值 0.75：低于此值回退为嵌入背景图。纯色幻灯片通常 >0.95。
- 过大的图表区域（>50% 页面面积）会被跳过，避免吞掉整页内容。
- 2B 复杂矢量真重建、多层透明/混合效果真重建还没落地。
- `tessdata/` 和生成的 `*_assets/` 目录不应进入 git 提交。
