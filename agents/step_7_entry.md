# Step 7 Router: 写作与写作前证据组织入口

本文件是 Step 7 的路由层，不替代 [step_7_writing.md](./step_7_writing.md)。

## 1. 作用

- 将 Step 7 从单一超长协议拆成多个子模式
- 默认使用 `target_genre` 驱动，而不是期刊 prestige 驱动
- 让 style learning、citation audit、pre-review 等能力按需加载
- Step 7 内部可完成基础可读性整形，但用户不需要感知内部写作流水线；外部入口仍只有写作、续写、综述、审稿前自检等任务。

## 2. mode 轴

- `draft`
- `chapter-only`
- `continue-existing`
- `review-only`
- `citation-audit`
- `figure`
- `pre-review`

## 3. target_genre 轴

- `thesis`
- `journal`
- `review`
- `report`
- `proposal`
- `conference`

## 4. 路由规则

- 用户说“开始写/基于文献写/生成章节” -> `draft` 或 `chapter-only`
- 用户说“续写/只写某章/改已有草稿” -> `continue-existing` 或 `chapter-only`
- 用户说“写文献综述” -> `review-only`
- 用户说“引用审计/检查引用准确性” -> `citation-audit`
- 用户说“生成图表/论文配图” -> `figure`
- 用户说“审稿人视角/预审/投稿前自审” -> `pre-review`

## 5. Artifact Passport 读取规则

Step 7 启动时先检查 `$CWD/.skill-state/artifact_passport.json`：

- 有 `draft` 时，可直接进入 `continue-existing` 或 `chapter-only`，不要求回跑 Step 6。
- 有 `zotero_mapping / pdf_index / bibliography / workflow_search_results` 时，可进入 `draft / review-only / pre-review`。
- 有 `citation_audit` 时，可进入 `citation-audit` 或基于审计结果的 `pre-review`。
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
