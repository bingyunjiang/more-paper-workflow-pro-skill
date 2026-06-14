# Step 6 Router: Zotero 与文库一致性入口

本文件是 Step 6 的新入口层，不替代 [step_6_zotero.md](./step_6_zotero.md)。

## 1. 作用

- 区分 Step 6 的 direct-entry 方式
- 显式约束本步的 JSON / Markdown 双工件输出
- 把文库整理从“操作说明”提升为“输出契约”

## 2. 入口模式

- `plan-from-bib`
  - 用户提供 `文献库.bib`、结构模板、PDF 池
- `plan-from-zotero`
  - 用户已有 Zotero 文库，需要整理或对齐大纲
- `consistency-adjustment`
  - 已有集合，但需要补附件、改层级、做覆盖映射

## 3. Artifact Passport 读取规则

Step 6 启动时先检查 `$CWD/.skill-state/artifact_passport.json`：

- 若 Passport 中有 `bibliography / workflow_search_results / pdf_pool / pdf`，优先判定为 `plan-from-bib`。
- 若 Passport 中有 `zotero_mapping / zotero_structure / pdf_index`，优先判定为 `plan-from-zotero`。
- 若同时有 Zotero 映射与 PDF/BibTeX 缺口，判定为 `consistency-adjustment`。
- Passport 只提供材料索引和风险说明，不强制回跑 Step 4/5；缺少正式上游产物时，在 Step 6 内生成最小 plan-only 映射。
- 进入 Step 6 后仍必须先确认 Zotero 模式：`local` / `cloud` / `skip`。`CP-ZOTERO-WRITE` 只阻塞真实写入，不阻塞只读、规划、查重或 dry-run。

## 4. 加载顺序

1. `static/core/output-contract.md`
2. `references/zotero-output-contract.md`
3. `references/zotero-entry-modes.md`
4. `agents/step_6_zotero.md`

## 5. 输出要求

Step 6 默认至少产出：

- 一个可机读 JSON
- 一个可人工审阅 Markdown
- 一个 readiness 状态块

若用户直接从 Zotero 进入，也应尽量生成最小映射，而不是只给口头建议。
