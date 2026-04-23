# Course

## 当前项目状态
- 已集成 `hugohe3/ppt-master` 作为基础设施（SVG→PPTX DrawingML 转换管线）。
- 新增 `faithful_convert.py`：忠实还原转换器，支持两种模式：
  - `--mode ai`：AI 视觉全元素重建（多模态 AI 分析图片→识别元素→原生 SVG 重建 + 复杂区域裁剪嵌入）
  - `--mode ocr`：背景图 + OCR 文字叠加（Tesseract）
- 新增 `vision_analyzer.py`：多模态 AI 视觉分析模块，支持 Anthropic / OpenAI / 任意 OpenAI 兼容 API。
- 新增 `auto_convert.py`：自动化编排脚本（prepare + export 两阶段）。
- 旧 skill `pdf-image-to-editable-ppt` 已归档至 `archive/`。

## 本轮变更
- **架构替换**：从 OCR+背景图叠加方案切换到 AI 驱动的混合裁剪策略。
- 集成 `hugohe3/ppt-master` 的 `skills/ppt-master/` 完整目录（SVG→PPTX、项目管理、源文档转换等）。
- 新增 `faithful_convert.py`：核心转换入口，AI 模式下实现"复杂图形裁剪嵌入 + 文字/形状原生可编辑"。
- 新增 `vision_analyzer.py`：多 provider AI 视觉分析（自动检测 Anthropic/OpenAI 环境变量）。
- 新增 `auto_convert.py`：自动化编排（图片→PDF→Markdown→项目初始化→导入→导出）。
- 新增 `image_to_pdf.py`：图片→PDF 桥接脚本。
- 添加 `CLAUDE.md`、`AGENTS.md`、`.env.example`、`requirements.txt`。
- 旧 skill、旧测试、旧 worktree（3 个 feature 分支）全部归档/清理。

## 关键文件
- `faithful_convert.py` — 核心转换入口（AI 模式 / OCR 模式）
- `vision_analyzer.py` — 多模态 AI 视觉分析模块
- `auto_convert.py` — 自动化编排脚本
- `skills/ppt-master/SKILL.md` — ppt-master 工作流定义
- `skills/ppt-master/scripts/svg_to_pptx/` — SVG→原生 PPTX (DrawingML)
- `skills/ppt-master/scripts/source_to_md/` — 源文档转 Markdown
- `skills/ppt-master/scripts/source_to_md/image_to_pdf.py` — 图片→PDF 桥接

## 运行入口
```bash
# AI 全元素重建（推荐）
python faithful_convert.py input.png --mode ai --provider openai

# OCR + 背景图模式（fallback）
python faithful_convert.py input.pdf --mode ocr

# 自动化编排
python auto_convert.py prepare input.png --name my_project
python auto_convert.py export projects/my_project_ppt169_xxx
```

## 运行时依赖
- 见 `requirements.txt`（核心：python-pptx、PyMuPDF、Pillow、svglib、reportlab、anthropic、openai）
- Tesseract OCR（OCR 模式需要，`C:\Program Files\Tesseract-OCR\`，需 chi_sim 语言包）

## 关键目录
- `skills/ppt-master/` — ppt-master skill（SVG→PPTX 基础设施）
- `projects/` — 用户项目工作区（gitignored）
- `exports/` — 导出的 PPTX（gitignored）
- `archive/` — 旧 skill 归档

## 当前注意事项
- AI 模式需要配置多模态 API（通过环境变量 `OPENAI_API_KEY` + `OPENAI_BASE_URL`，或 `ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL`）。
- AI 模式下，复杂图形区域（插图、照片等）从原图裁剪嵌入，文字和简单形状为原生可编辑元素。
- AI 还原度取决于模型能力，当前已验证 Claude Sonnet 4 可用。
- `projects/` 和 `exports/` 已 gitignore。
- 待优化：AI 元素识别精度、文字位置精确度、更多形状类型支持。
