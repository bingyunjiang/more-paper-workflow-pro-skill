# Step 7 Router: 写作与写作前证据组织入口

本文件是 Step 7 的路由层，不替代 [step_7_writing.md](./step_7_writing.md)。

## 1. 作用

- 将 Step 7 从单一超长协议拆成多个子模式
- 默认使用 `target_genre` 驱动，而不是期刊 prestige 驱动
- 让 style learning、citation audit、pre-review 等能力按需加载
- Step 7 内部可完成基础可读性整形，但用户不需要感知内部写作流水线；外部入口仍只有写作、续写、综述、审稿前自检等任务。

## 2. mode 轴

- `full-document`
- `chapter-only`
- `continue-existing`
- `abstract-only`
- `review-only`
- `revision-only`

## 3. target_genre 轴

- `thesis`
- `journal`
- `review`
- `report`
- `proposal`
- `conference`

## 4. 路由规则

- 用户说“开始写/基于文献写全文” -> `full-document`
- 用户说“只写某章/只补某节/按章节写” -> `chapter-only`
- 用户说“续写已有草稿/基于现有正文继续写” -> `continue-existing`
- 用户说“只写摘要/中英摘要” -> `abstract-only`
- 用户说“写文献综述” -> `review-only`
- 用户说“按审稿意见修改/修稿/逐条回应后改正文” -> `revision-only`

## 5. Artifact Passport 读取规则

Step 7 启动时先检查 `$CWD/.skill-state/artifact_passport.json`：

- 有 `draft` 时，可直接进入 `continue-existing` 或 `chapter-only`，不要求回跑 Step 6。
- 有 `zotero_mapping / pdf_index / bibliography / workflow_search_results` 时，可进入 `full-document / review-only / chapter-only`。
- 有 `citation_audit` 时，可进入基于审计结果的 `revision-only`，或作为 `continue-existing / chapter-only` 的风险输入。
- 缺 `pdf-附件池索引.json` 或证据矩阵时，生成最小映射和风险标记；不得声明引用安全通过。
- Passport 的全局 `route_mode` 只决定 direct-entry/plan-only/repair，不覆盖本文件的 Step 7 `mode` 和 `target_genre`。

## 6. 加载顺序

1. `manifest.step7.yaml`
2. `static/core/output-contract.md`
3. `references/genre-style-axis.md`
4. `references/writing-modes.md`
5. mode 对应 reference
6. `agents/step_7_writing.md`

## 7. 输出要求

Step 7 的正式输出应显式说明：

- `mode`
- `target_genre`
- `evidence_basis`
- `citation_risk_summary`
- `recommended_next_step`

## 8. existing-draft 三类入口边界

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
