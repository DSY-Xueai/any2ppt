# Course

## 当前项目状态
- 当前目录已初始化为 Git 仓库。
- 项目当前处于“创建 PDF/图片转可编辑 PPT skill”的设计阶段。
- 已完成该 skill 的正式设计文档，尚未开始实现 `SKILL.md` 与脚本链路。

## 本轮新增或变更
- 新增 `docs/superpowers/specs/2026-04-11-pdf-image-to-editable-ppt-design.md`。
- 新增 `docs/superpowers/plans/2026-04-11-pdf-image-to-editable-ppt.md`。
- 设计已明确采用“双层方案”：
  - 底图层保证视觉 100% 保真、原底原色。
  - 编辑层仅在高置信情况下提取文字和图片。
- 明确支持多页 PDF，默认“每页一张幻灯片”，可按用户要求切分长页/长图。
- 明确失败回退策略：宁可少提取，也绝不破坏视觉完整性。
- 已完成实现计划拆解，下一步进入 skill 与脚本骨架开发。

## 关键修改文件
- `Course.md`
- `docs/superpowers/specs/2026-04-11-pdf-image-to-editable-ppt-design.md`
- `docs/superpowers/plans/2026-04-11-pdf-image-to-editable-ppt.md`

## 运行入口
- 当前暂无可运行入口。
- 后续预计新增：
  - `skills/pdf-image-to-editable-ppt/SKILL.md`
  - `skills/pdf-image-to-editable-ppt/scripts/*.py`

## 当前注意事项
- 设计已冻结，`spec` 与实现计划都已写入文档。
- 该 skill 的承诺是“视觉保真优先 + 尽量提取可编辑元素”，不是保证任意输入都能完整转换为全部可编辑对象。
- 当前工作树尚未提交；是否提交需等用户明确确认。
