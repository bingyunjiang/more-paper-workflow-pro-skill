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

## Workflow map

- Step 1: research topic clarification and topic review
- Step 2: outline generation and outline optimization
- Step 3: search planning
- Step 4: literature search, scoring, and reporting
- Step 5: batch download routing
- Step 6: Zotero organization and attachment consistency
- Step 7: writing, evidence matrix, style learning, citation audit
- Step 8: conservative polishing and verification

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
