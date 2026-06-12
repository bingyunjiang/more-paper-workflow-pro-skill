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

## 3. 加载顺序

1. `static/core/output-contract.md`
2. `references/zotero-output-contract.md`
3. `references/zotero-entry-modes.md`
4. `agents/step_6_zotero.md`

## 4. 输出要求

Step 6 默认至少产出：

- 一个可机读 JSON
- 一个可人工审阅 Markdown
- 一个 readiness 状态块

若用户直接从 Zotero 进入，也应尽量生成最小映射，而不是只给口头建议。
