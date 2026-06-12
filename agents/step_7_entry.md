# Step 7 Router: 写作与写作前证据组织入口

本文件是 Step 7 的路由层，不替代 [step_7_writing.md](./step_7_writing.md)。

## 1. 作用

- 将 Step 7 从单一超长协议拆成多个子模式
- 默认使用 `target_genre` 驱动，而不是期刊 prestige 驱动
- 让 style learning、citation audit、pre-review 等能力按需加载

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

## 5. 加载顺序

1. `manifest.step7.yaml`
2. `static/core/output-contract.md`
3. `references/genre-style-axis.md`
4. `references/writing-modes.md`
5. mode 对应 reference
6. `agents/step_7_writing.md`

## 6. 输出要求

Step 7 的正式输出应显式说明：

- `mode`
- `target_genre`
- `evidence_basis`
- `citation_risk_summary`
- `recommended_next_step`
