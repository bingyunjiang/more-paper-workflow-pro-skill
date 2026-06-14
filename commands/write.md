# Write

## 何时使用
- 已有 Zotero / PDF / BibTeX / 映射 JSON，需要直接进入 Step 7
- 想生成文献证据矩阵、风格蓝图、章节草稿、全文草稿或综述章节
- 已有草稿，需要续写、局部改写或基于审稿意见修稿

## 最小输入
- Zotero 条目、`文献-Zotero架构对照.json`、PDF 目录、已有草稿中的至少一种
- 对于 `chapter-only`：需指定章节范围
- 对于 `revision-only`：需提供审稿意见

如果输入是已有草稿，优先判定为：
- `continue-existing`
- `chapter-only`
- `revision-only`

三者都允许 direct-entry，但都不能跳过证据确认。

## 主要产出
- `综述矩阵.csv/.md`
- `research_dossier/`
- `retrieval_candidates.json`
- `argument_plan.md/json` 中的证据确认区块
- `论文初稿.md/.docx` 或指定章节草稿
- `revision_roadmap.md`、`response_letter_skeleton.md`、`evidence_gap_list.md`

## 常见阻塞点
- 摘要级证据不能支撑强 claim
- 无 PDF / 无笔记 / 无全文时，只能降级为背景级证据
- 候选召回命中后，仍必须回到 note / annotation / PDF 原文确认
- `retrieval_candidates.json` 可记录 `evidence_question_id`、`query_variant`、`source_page_hint` 和 `negative_or_conflicting_evidence`，但这些字段只帮助定位证据，不直接决定正文写法
- `revision-only` 发现证据不足时，应回退 Step 4/6/7.2，而不是只改措辞
