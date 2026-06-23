# Entry Routing Index

This file keeps the cross-agent entry vocabulary out of `SKILL.md` frontmatter.

For the full long-form trigger list, see `references/trigger-catalog.md`.

## Core entry intents

- Step 1: research topic clarification, topic review, research-stage diagnosis
- Step 2: outline generation, outline review, outline optimization
- Step 3: search planning, structured literature search strategy
- Step 4: literature search, screening, scoring, PRISMA-style logs
- Step 5: batch PDF download, DOI/title download routing, session checks
- Step 6: Zotero organization, outline mapping, attachment consistency
- Step 7: writing, evidence matrix, style learning, citation audit
- Step 8: polishing, conservative revision, AI-trace diagnostics

## Common aliases

- Chinese entry phrases remain supported across agents, including `确定研究主题`, `生成论文大纲`, `文献检索`, `批量下载`, `Zotero 文库整理`, `写论文`, and `论文润色`.
- English entry phrases remain supported across agents, including `comprehensive search`, `outline review`, `download by paper title`, `review matrix`, `write selected chapter`, and `polish the draft`.
- Direct-entry requests keep their current step contracts; the router files under `agents/step_*.md` remain the source of truth.
- File type alone must not decide the step: `.bib` / BibTeX may mean Step 5 download input or Step 6 Zotero import input, so routing must follow the user's action words first.
- If the user says `下载 / 下 PDF / 批量下载 / download` with BibTeX, route to Step 5 first; only route to Step 6 when the user explicitly asks to `导入 Zotero / 建条目 / 入库 / 建集合 / 关联附件`.

## Platform notes

- Codex, Claude, Hermes, OpenClaw, and Reasonix should all route through the same step contracts.
- Platform-specific wrappers only control discovery metadata and launch hints; they must not fork workflow behavior.
