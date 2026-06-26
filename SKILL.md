---
name: more-paper-workflow-pro-skill
description: Use when the user asks for the more-paper academic workflow: research topic clarification, outline and keyword generation, structured literature search plans, multi-source literature search and scoring, paper PDF download routing (Sci-Hub/IEEE/ScienceDirect), Zotero library organization, review matrices, paper writing, citation audit, or polishing. Especially useful for Chinese or English thesis, dissertation, literature review, PRISMA-style search logs, and GB/T 7714 references. 学术论文全流程：确定研究主题，生成大纲，文献检索，下载，Zotero，综述矩阵，论文写作，润色。
---

## Skill metadata

version: v1.0.17-20260624 (2026-06-24)
author: Dr. Jiang Bingyun（江博士）
wechat: Bingyunjiang
category: research
license: CC BY-NC-SA 4.0
related_skills:
  - science-direct-cdp-pipeline: "Overlaps on CDP ScienceDirect download; this skill adds the full 8-step workflow from topic definition to paper polishing."
  - zotero-review-matrix-skill: "Source of literature-review-matrix-schema, literature-review-docx-guide, and gbt7714-2015-citation-format references. Integrated into Step 7 writing preparation and writing."

## Entry routing

- Cross-agent entry vocabulary lives in `references/entry-routing-index.md`.
- Full trigger vocabulary lives in `references/trigger-catalog.md`.
- Platform-specific launch hints live in thin adapter files such as `agents/openai.yaml` and `.claude-plugin/marketplace.json`.
- Step-specific runtime contracts remain in `agents/step_*.md` and `references/*.md`.

## Runtime rules

- Completion gates: `references/completion-gates.md`
- Failure triage: `references/failure-triage.md`
- Step handoff: `references/step-handoff-contract.md`
- Update reminders: `references/update-reminder-protocol.md`
- Entry vocabulary: `references/entry-routing-index.md`
- Trigger catalog: `references/trigger-catalog.md`
- Direct-entry artifact graph: `.skill-state/artifact_passport.json`

## Direct-entry artifact passport

- `artifact_passport.json` 是 direct-entry / resume / repair 的轻量产物护照，不是线性流程锁。
- 它记录 `route_mode`、`recommended_step`、nodes、edges、gaps、risks 和每个 Step 的 readiness；缺失前序 Step 默认不阻塞当前入口。
- Step 5/6/7/8 可从 DOI/BibTeX/PDF/Zotero/evidence pack/初稿等现有材料直接进入；无法确认的关系必须标为 `inferred`、`unlinked` 或 `conflict`，不得伪装为 confirmed。
- 全局借鉴口径是先发散、后收敛、候选池先保留；每一步都要有输入边界、候选池、输出工件和失败回退。

## Global execution discipline

These rules are embedded inside the existing Step 1-8 contracts; they do not create a new public step or user entry.

- `张力先行`：每一步先说明当前任务的核心拉扯，例如完整性 vs 可执行性、召回率 vs 精准度、写作张力 vs 证据边界。
- `双向校准`：同时防止“不够”和“过头”，例如检索不够会漏文献，检索过头会污染候选池；润色不足会保留硬伤，润色过头会改坏论证。
- `最小对比`：关键边界用最小对比例子校准，例如同一材料何时是下载输入、何时才是 Zotero 入库输入。
- `反模式命名`：把常见错误命名并写入对应 Step 的检查项，避免下游反复解释同一种失败。
- `任务定义优先于实现定义`：先判定用户要解决的问题、交付物和边界，再选择命令、脚本或写作动作。
- `契约变更 vs 实现变更`：改动输入输出、证据等级、路由或完成标准时视为契约变更；只改局部执行方式时才是实现变更。
- `快速通道不跳质量门`：direct-entry 可以跳过前序流程，但不能跳过证据边界、登录门控、Zotero 写入确认、引用审计或 Step 8 保守修订边界。

## Workflow map

- Step 1: research topic clarification and topic review
- Step 2: outline generation and outline optimization
- Step 3: search planning
- Step 4: literature search, scoring, and reporting
- Step 5: batch download routing
- Step 6: Zotero organization and attachment consistency
- Step 7: writing, evidence matrix, style learning, citation audit
- Step 8: conservative polishing and verification
- Step 4: screening basis confirmation, five-dimension scoring, T1-T4 grading, citation expansion, saturation, and completion check
- Public Step 4 summary: 4.4 筛选依据确认 → 4.5 五维评分 → 4.6 T1-T4 分级 → 4.7 引文扩展 → 4.8 饱和度估算 → 4.9 报告生成与完成检查
- Step 4 public summary also retains the phrasing `4.4 筛选依据` / `4.5 五维` / `4.6 T1-T4` / `4.7 引文扩展` / `4.8 饱和` / `4.9`

## Step 7 compatibility anchors

- Public writing modes: `full-document`, `review-only`, `abstract-only`, `chapter-only`, `continue-existing`, `revision-only`.
- Evidence intake modes include `zotero_full`, `zotero_mineru`, `evidence_pack`, `draft_only`, `mixed`, and the internal Step 7 evidence-refinement submode `deep_read_refine`.
- 推荐 Zotero 用户安装 `llm-for-zotero` 插件以复用 MinerU ZIP 图文资产；没有 Zotero/MinerU 时仍可使用本地 `evidence_pack`，但证据等级必须显式降级。

## Compatibility notes

- Keep `README.md` public-facing and compressed.
- Keep this file and `agents/*.md` authoritative for runtime behavior.
- Do not duplicate workflow logic per agent; only thin adapters should vary.
- Windows/macOS/Linux compatibility remains a default constraint.
- On Windows, if Chinese text displays incorrectly, first read `SKILL.md`, `README.md`, and `agents/*.md` explicitly as UTF-8 before concluding the files are corrupted.
- 防截断原则：JSON/BibTeX/证据映射等机器主工件禁止截断；Markdown/XLSX/PDF 展示层可截断但必须保留稳定回查 ID，且不得反向污染机器工件。
- 机器工件禁止截断；Markdown/XLSX/PDF 仅作为展示层可截断。

## Public-first entry examples

- `README 首屏` only provides onboarding shortcuts and does not redefine runtime contracts.
- Step 1: use the topic-clarification entry prompt in `README.md`
- Step 5: use the direct download entry prompt in `README.md`
- Step 7: use the writing entry prompt in `README.md`

## Update policy

- `SKILL.md` is the canonical version source.
- `README.md` and `CHANGELOG.md` are display copies and must stay in sync.
- `scripts/check_skill_update.py` compares the three version surfaces and reports any mismatch.
- `scripts/perform_skill_upgrade.py` only pulls the latest commit and does not rewrite versions.
