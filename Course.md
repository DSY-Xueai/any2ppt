# Course

## 当前项目状态
- 核心功能：图片转可编辑 PPTX，流程为读图、OCR 文本检测、背景建模/修复、前景组件提取、PPTX 分层组装。
- 默认输出不包含原图参考页；需要参考页时显式使用 `--reference`。
- 前景组件以透明 PNG 图层写入 PPT，文本以可编辑文本框写入 PPT。
- 项目已提供可分发 Skill：`skills/image-to-ppt/`。
- GitHub 仓库：`https://github.com/DSY-Xueai/any2ppt`。

## 本轮变更
- 将 README 中原 `Skill 包` 小节改为 `skills 安装`。
- 在 `skills 安装` 小节补充四种安装方式：`npx skills add`、让 Agent 自动安装、Claude Code plugin、手动复制 skill。
- 新增 `.claude-plugin/plugin.json`，声明 `any2ppt` plugin 元数据，并指向 `./skills/image-to-ppt`。
- README 项目结构补充 `.claude-plugin/plugin.json`。

## 关键修改文件
- `README.md`：补充 skills 四种安装方式，并更新项目结构。
- `.claude-plugin/plugin.json`：Claude Code plugin manifest，声明 skill 路径。
- `Course.md`：同步本轮项目状态和验证结果。

## 运行入口
```bash
python image_to_ppt.py input.png
python image_to_ppt.py img1.png img2.png -o output.pptx
python image_to_ppt.py ./slides_folder/ -o output.pptx
python image_to_ppt.py img1.png img2.png --reference
```

## skills 安装入口
```bash
npx skills add DSY-Xueai/any2ppt --skill image-to-ppt
claude plugin marketplace add https://github.com/DSY-Xueai/any2ppt
claude plugin install any2ppt@any2ppt --scope user
```

## 验证结果
- `python -m json.tool .claude-plugin\plugin.json > $null`：通过。
- `python -m pytest -q`：11 passed；存在 pytest-asyncio 配置弃用警告，非本轮引入。

## 当前注意事项
- 文字提取与字体风格仍是近似重建，不应宣称与原图完全一致。
- 当前前景保护阈值会拒绝覆盖率超过 45% 的单个 detector mask；这能防止整页误检，但极端大前景页面后续仍需更多样本验证。
- 背景 inpainting 在复杂纹理、渐变和文字密集区域仍可能有局部修补痕迹。
- README 中 Claude Code plugin 安装命令依赖 Claude Code 当前 plugin 机制；如上游 CLI 语法变化，应以后续官方文档为准。
