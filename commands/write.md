# Write

## 何时使用
- 已有 Zotero / PDF / BibTeX / 映射 JSON，需要直接进入 Step 7
- 想生成文献证据矩阵、风格蓝图、章节草稿、全文草稿或综述章节
- 已有草稿，需要续写、局部改写或基于审稿意见修稿

## 最小输入
- Zotero 条目、`文献-Zotero架构对照.json`、PDF 目录、已有草稿中的至少一种
- 对于 `chapter-only`：需指定章节范围
- 对于 `revision-only`：需提供审稿意见

## 主要产出
- `综述矩阵.csv/.md`
- `research_dossier/`
- `论文初稿.md/.docx` 或指定章节草稿
- `revision_roadmap.md`、`response_letter_skeleton.md`、`evidence_gap_list.md`

## 常见阻塞点
- 摘要级证据不能支撑强 claim
- 无 PDF / 无笔记 / 无全文时，只能降级为背景级证据
- `revision-only` 发现证据不足时，应回退 Step 4/6/7.2，而不是只改措辞
