# Course

## 当前项目状态
- 核心功能：图片→可编辑 PPT 转换（背景建模/修复 + 前景拆分 + 文本重建）。
- 管线：读图 → OCR 文本检测 → 自适应背景建模 → 前景提取/组件拆分 → PPTX 分层组装。
- OCR：PaddleOCR 优先（已 patch OneDNN mkldnn bug），pytesseract 回退。
- 自动估计字号（非线性校正，±7% 偏差）、颜色（采样）、粗体（ink ratio）。

## 本轮变更
- **前景拆分修复**（`fg_extract.py`）：
  1. 移除 `_remove_noise_and_lines` 中误删设计元素的薄线过滤规则（`w>500 and h<=3` 等）
  2. 形态学 OPEN 改用 2×2 kernel，避免消除 1-2px 宽的细线（连接线、图标边缘）
  3. 新增 Canny 边缘检测辅助：边缘像素中 diff > threshold×0.35 的部分加入前景 mask
  4. 新增边缘伪影过滤：跨越 ≥90% 图像尺寸且 ≤5px 厚的薄条被排除
- **背景建模重写**（`bg_model.py`）：
  - 第一轮（无 fg_hint）：平滑背景（非背景像素替换为 bg_color + Gaussian blur）用于初始前景检测
  - 第二轮（有 fg_hint）：原图 + inpainting 修复前景/文字区域，非前景区域像素级保留原图
  - 删除旧的瓦片中值模型（`_tile_median_model`），消除瓦片拼接痕迹
- **清理旧代码**：删除 `skills/ppt-master/`、`archive/`、`projects/`、`exports/`，清理 `requirements.txt` 和 `.gitignore`

## 关键文件
- `image_to_ppt.py` — 主入口（CLI + 管线编排）
- `text_detect.py` — 文本检测模块（PaddleOCR / pytesseract + 样式估计 + mkldnn patch）
- `bg_model.py` — 背景建模模块（平滑背景初检 + 原图 inpainting 精修，非前景区域像素级保留）
- `fg_extract.py` — 前景提取模块（diff + 边缘检测 + 连通域拆分 + alpha feathering）
- `ppt_assemble.py` — PPTX 组装模块（背景层 + 前景组件层 + 全幅居中文本框层）

## 运行入口
```bash
# 基本用法（默认不加参考页）
python image_to_ppt.py input.png

# 指定输出路径
python image_to_ppt.py input.png -o output.pptx

# 调整参数
python image_to_ppt.py input.png --lang ch --period 32 --diff-threshold 20 --min-area 20

# 加参考页（第二页放原图对照）
python image_to_ppt.py input.png --reference
```

## 运行时依赖
- 见 `requirements.txt`（核心：python-pptx、opencv-python、Pillow、numpy）
- OCR 引擎至少需要一个：PaddleOCR（推荐，已内置 mkldnn patch）或 Tesseract

## 当前注意事项
- PaddleOCR v3.5.0 + PaddlePaddle 3.3.1 的 OneDNN mkldnn bug 已通过 `_patch_paddle_mkldnn()` 修复（强制 `run_mode='paddle'`）。
- Windows 环境需先 import torch 再 import paddle 以避免 DLL 路径污染（patch 中已处理）。
- 粗体检测基于墨水密度（Otsu + ink ratio），对大多数中英文文本有效。
- 背景建模分两轮：第一轮用平滑背景做初始前景检测，第二轮用原图+inpainting 精修，非前景区域像素级保留原图。
- 前景组件按连通域拆分（diff_threshold=20, min_area=20），Canny 边缘辅助捕获细线，每个组件为独立透明 PNG。
- 待优化：背景修复质量（复杂纹理/渐变区域）、文本颜色精度、更多图片类型验证。
