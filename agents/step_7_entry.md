# Step 7 Router: 写作与写作前证据组织入口

本文件是 Step 7 的路由层，不替代 [step_7_writing.md](./step_7_writing.md)。

## 作用

- 将 Step 7 从单一超长协议拆成多个子模式
- 默认使用 `target_genre` 驱动，而不是期刊 prestige 驱动
- 让 style learning、citation audit、pre-review 等能力按需加载
- Step 7 内部可完成基础可读性整形，但用户不需要感知内部写作流水线；外部入口仍只有写作、续写、综述、审稿前自检等任务。
- Step 7 同时支持写文后补图和写作中同步插图；图文必须共享同一条证据链，不允许正文和图表分开漂移。

## mode 轴

- `full-document`
- `chapter-only`
- `continue-existing`
- `abstract-only`
- `review-only`
- `revision-only`

## figure_mode 轴

- `auto_insert`
- `post_write`
- `skip`

## target_genre 轴

- `thesis`
- `journal`
- `review`
- `report`
- `proposal`
- `conference`

## 路由规则

- 用户说“开始写/基于文献写全文” -> `full-document`
- 用户说“只写某章/只补某节/按章节写” -> `chapter-only`
- 用户说“续写已有草稿/基于现有正文继续写” -> `continue-existing`
- 用户说“只写摘要/中英摘要” -> `abstract-only`
- 用户说“写文献综述” -> `review-only`
- 用户说“按审稿意见修改/修稿/逐条回应后改正文” -> `revision-only`
- 用户说“自动插图/同步插图/写完顺手补图” -> 进入 Step 7 图文联合链路，默认 `figure_mode=auto_insert`

## Artifact Passport 读取规则

Step 7 启动时先检查 `$CWD/.skill-state/artifact_passport.json`：

- 有 `draft` 时，可直接进入 `continue-existing` 或 `chapter-only`，不要求回跑 Step 6。
- 有 `zotero_mapping / pdf_index / bibliography / workflow_search_results` 时，可进入 `full-document / review-only / chapter-only`。
- 有 `citation_audit` 时，可进入基于审计结果的 `revision-only`，或作为 `continue-existing / chapter-only` 的风险输入。
- 缺 `pdf-附件池索引.json` 或证据矩阵时，生成最小映射和风险标记；不得声明引用安全通过。
- Passport 的全局 `route_mode` 只决定 direct-entry/plan-only/repair，不覆盖本文件的 Step 7 `mode` 和 `target_genre`。

Artifact graph 只负责登记当前可用材料和可确认关系，不强制线性 Step 4→5→6→7：

- `zotero_item / evidence_item / claim / draft_section` 可以从 Zotero、evidence pack、MinerU ZIP、已有初稿或章节大纲独立登记。
- 每个正文 claim 或引用映射必须带 `reading_depth` 与 `trace_status`；`trace_status=inferred/unlinked` 只能支撑候选、背景或待确认表达。
- `metadata_only`、`abstract_only` 或 `unlinked` 证据必须显式进入 `citation_risk_summary` / `evidence_gap_list`，不得被写成全文已读或 confirmed evidence。
- 只有 `evidence_item -> claim` 或 `claim -> draft_section` 关系有明确 evidence id、citation key、页码/段落/注释来源时，才可标为 confirmed。
- direct-entry 下允许先产出“当前入口可继续版本”；如果用户要求“全链路可追溯”，则必须把缺失的 Step 4/5/6 关系列为待补任务。

## 图文联合规则

- `auto_insert_figures=true` 时，条目必须具备 `LLM-for-Zotero-MinerU-cache-*.zip` 或等价图文资产包。
- 没有 MinerU ZIP 但本地 PDF 可读时，允许先进入 `post_write`，用 PyMuPDF 生成 `pdf_direct` 低置信候选图；没有可读 PDF 或无候选图时，才只能放图位占位，不自动选图。
- `post_write` 用于正文先完成、后按章补图；`auto_insert` 用于写作中同步扫图位。
- `skip` 允许用户显式跳过插图，只保留正文和图位说明。

## 加载顺序

1. `manifest.step7.yaml`
2. `static/core/output-contract.md`
3. `references/genre-style-axis.md`
4. `references/writing-modes.md`
5. mode 对应 reference
6. `agents/step_7_writing.md`

## 输出要求

Step 7 的正式输出应显式说明：

- `mode`
- `target_genre`
- `evidence_basis`
- `citation_risk_summary`
- `recommended_next_step`

## existing-draft 三类入口边界

### `continue-existing`

- 适用：已有草稿，需要继续写主体内容
- 最小输入：已有草稿 + 续写范围或续写目标
- 最小输出：更新后的正文 + 当前章节/段落的证据状态说明
- 边界：允许继续展开主体内容，但仍不得跳过候选定位和原文确认

### `chapter-only`

- 适用：只处理指定章节或小节
- 最小输入：章节范围 + 最小证据基础（Zotero / PDF / BibTeX / workflow JSON / 已有草稿之一）
- 最小输出：章节草稿 + `argument_plan` + 候选/确认状态
- 边界：章节内部可走候选证据层，但不擅自扩写到未指定章节

### `revision-only`

- 适用：已有草稿 + 审稿意见或明确修订目标，只做定向修订
- 最小输入：已有草稿 + 审稿意见/修订目标 + 至少可追溯的证据状态
- 最小输出：修订正文 + `revision_roadmap.md` + `claim_delta_report.md` + `evidence_gap_list.md`
- 边界：只做定向修订，不接管主体重写；证据不足时优先回退或补证据，不得仅靠降级措辞掩盖问题
