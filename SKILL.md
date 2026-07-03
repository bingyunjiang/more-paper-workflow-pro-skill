---
name: more-paper-workflow-pro-skill
description: Use when the user asks for the more-paper academic workflow (more paper, more-paper, more_paper, morepaper): research topic clarification, outline and keyword generation, structured literature search plans, multi-source literature search and scoring, paper PDF download routing (Sci-Hub/IEEE/ScienceDirect), Zotero library organization, review matrices, paper writing, citation audit, or polishing. Especially useful for Chinese or English thesis, dissertation, literature review, PRISMA-style search logs, and GB/T 7714 references. 学术论文全流程：确定研究主题，生成大纲，文献检索，下载，Zotero，综述矩阵，论文写作，润色。
---

## Skill metadata

version: v1.0.19-20260704 (2026-07-04)
author: Dr. Jiang Bingyun（江博士）
wechat: Bingyunjiang
category: research
license: CC BY-NC-SA 4.0
related_skills:
  - science-direct-cdp-pipeline: "Overlaps on CDP ScienceDirect download; this skill adds the full 8-step workflow from topic definition to paper polishing."
  - zotero-review-matrix-skill: "Source of literature-review-matrix-schema, literature-review-docx-guide, and gbt7714-2015-citation-format references. Integrated into Step 7 writing preparation and writing."

## Entry routing

- 对外只保留一个主入口 `README.md` / `SKILL.md`，用户只需要记一个入口。
- 任一 Step 仍可直接进入，不把前序流程当成硬门槛。
- 快速导流先看 `references/entry-guide.md`，按任务意图选 Step，再回到对应 `agents/step_*.md`。
- 参考文件的功能分组见 `references/reference-index.md`，新增或重排 reference 前先更新索引。
- Cross-agent entry vocabulary lives in `references/entry-routing-index.md`.
- Full trigger vocabulary lives in `references/trigger-catalog.md`.
- Platform-specific launch hints live in thin adapter files such as `agents/openai.yaml` and `.claude-plugin/marketplace.json`.
- Step-specific runtime contracts remain in `agents/step_*.md` and `references/*.md`.

## Runtime rules

- Completion gates: `references/completion-gates.md`
- Failure triage: `references/failure-triage.md`
- Agent execution discipline: `references/agent-execution-discipline.md`
- Step handoff: `references/step-handoff-contract.md`
- Update reminders: `references/update-reminder-protocol.md`
- Direct-entry artifact graph: `.skill-state/artifact_passport.json`
- Artifact passport keeps `route_mode` as non-locking route metadata for direct-entry handoff.

## Global discipline

- `张力先行`：每一步先说清楚当前任务的核心拉扯。
- `双向校准`：同时防止“不够”和“过头”。
- `最小对比`：关键边界用最小对比例子校准。
- `反模式命名`：把常见错误写入对应 Step 的检查项。
- `任务定义优先于实现定义`：先判定问题、交付物和边界，再选动作。
- `读证据先于生成`：先读取用户材料、检索结果、PDF/Zotero/已有稿件，再输出判断或正文。
- `假设显式化`：任务边界、证据基础、数据源选择和写作范围必须先说明。
- `最小充分产物`：只生成当前 Step 需要的最小可用产物，不强行扩展全流程。
- `保守修改既有稿件`：润色和修订只处理明确范围，不新增未经确认的证据。
- `失败先分层`：检索、下载、Zotero、写作失败先定位层级，再给最小补救动作。
- `完成声明过门槛`：未满足 completion gate 时，不使用“已完成/没问题”等表达。
- `契约变更 vs 实现变更`：改输入输出、证据等级、路由或完成标准时，视为契约变更。
- `快速通道不跳质量门`：direct-entry 可以跳过前序流程，但不能跳过证据边界、登录门控、Zotero 写入确认、引用审计或 Step 8 保守修订边界。
- `Checkpoint 是“当前 Step 的输入与风险确认协议”，不是线性流程锁`。
- `不限制 Step 6/7 直接入口`。
- `防截断原则`：机器工件禁止截断；Markdown/XLSX/PDF 仅作为展示层可截断，必须保留稳定回查 ID，且不得反向污染 JSON、BibTeX、Zotero 映射或下载 manifest。

## Workflow map

- Step 1: research topic clarification and topic review
- Step 2: outline generation and outline optimization
- Step 3: search planning
- Step 4: literature search, scoring, and reporting
- Step 5: batch download routing
  - Stable artifacts: `download_manifest.json`, `download_attempts.jsonl`, `pdf-附件池索引.json`.
  - Manual recovery: after user-provided PDFs, run `scripts/step5_reconcile_pdf_pool.py --output <dir>` to reconcile without changing filenames.
- Step 6: Zotero organization and attachment consistency
- Step 7: writing, evidence matrix, style learning, citation audit
- Step 8: conservative polishing and verification

Step 4 public sequence: 4.4 筛选依据 → 4.5 五维 → 4.6 T1-T4 → 4.7 引文扩展 → 4.8 饱和 → 4.9 报告生成与完成检查。

## Step boundaries

- Step 1-6 负责定题、检索、下载和证据整理。
- Step 7 负责正文写作、证据矩阵、风格学习、图表与引用审计。
- Step 8 负责成稿级精修、终验和保守修订。
- `README.md` 只保留对外简洁入口，不承载运行态真相。
- 入口收敛不等于流程拦截，任一 Step 都可以按 direct-entry 合同进入。
- 推荐 Zotero 用户安装 `llm-for-zotero` 插件。
- `evidence_pack` 是无 Zotero/MinerU 时的本地证据包入口。
- `full-document / review-only / abstract-only / chapter-only / continue-existing / revision-only` 仍是 Step 7 的公开模式名。

## Public-first entry examples

README 首屏只保留 public-first entry examples；运行时细则仍以本文件和 `agents/step_*.md` 为准。

- Step 1: use the topic-clarification entry prompt in `README.md`
- Step 5: use the direct download entry prompt in `README.md`
- Step 7: use the writing entry prompt in `README.md`

## Update policy

- `SKILL.md` is the canonical version source.
- `README.md` and `CHANGELOG.md` are display copies and must stay in sync.
- `scripts/check_skill_update.py` compares the three version surfaces and reports any mismatch.
- `scripts/perform_skill_upgrade.py` only pulls the latest commit and does not rewrite versions.
