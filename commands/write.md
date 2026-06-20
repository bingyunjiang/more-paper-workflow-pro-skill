# Write

## 何时使用
- 已有 Zotero / PDF / BibTeX / 映射 JSON，需要直接进入 Step 7
- 想生成文献证据矩阵、风格蓝图、章节草稿、全文草稿或综述章节
- 已有草稿，需要续写、局部改写或基于审稿意见修稿

## 最小输入
- Zotero 条目、`文献-Zotero架构对照.json`、PDF 目录、已有草稿中的至少一种
- 对于 `chapter-only`：需指定章节范围
- 对于 `revision-only`：需提供审稿意见

## 本轮默认纪律
- 按大纲对应的 Zotero 子集合取证；不扫整个 Zotero 文库
- 每次只写一个当前小节，不提前展开后续小节
- `thesis` 默认按博士论文深度推进，不写成短综述或提纲式背景
- 关键论点优先使用“英文基础/国际研究 + 中文工程场景文献”联合支撑
- 重要判断尽量用 2-3 篇文献并列支撑，不让单篇文献独自承担关键结论
- 试写阶段默认使用作者-年份，并逐条标注 `（已读全文）/（已读摘要）/（仅元数据）`

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
- 若当前小节没有明确映射集合，或承载核心判断的论点缺少多源交叉支撑，应先补映射/补证据，不要硬写满
