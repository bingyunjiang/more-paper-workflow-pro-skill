# Agent Execution Discipline

> This file adapts engineering-agent discipline to the more-paper academic workflow. It is a runtime discipline, not a new linear Step.

---

## 1. Scope

Apply this discipline whenever the workflow reads evidence, designs a search, routes downloads, organizes Zotero records, writes a section, audits citations, or polishes an existing manuscript.

It does not override Step-specific contracts. When a Step file and this file both apply, follow the stricter evidence and completion rule.

---

## 2. Read Evidence Before Output

Before producing judgments, search plans, writing, revision, or completion claims:

- Read the user-provided materials that define the task.
- Read the relevant search results, metadata, PDFs, Zotero records, evidence packs, or existing manuscript text.
- Prefer project-local evidence and Step artifacts over generic background knowledge.
- If the required evidence is missing, state the gap instead of filling it with plausible content.

Do not turn titles, abstracts, candidate DOI matches, or unlinked PDFs into confirmed evidence unless the relevant Step contract allows that status.

---

## 3. Think Before Workflow

Before starting a multi-action Step, make the working frame explicit:

- Task: what the user is actually asking for.
- Assumptions: what is being inferred from incomplete information.
- Boundary: what will not be done in this pass.
- Success criterion: what must be true before the Step can be called complete.
- Tradeoff: any choice that changes coverage, precision, cost, login burden, evidence strength, or revision scope.

If a request has multiple reasonable interpretations, list them briefly and ask or choose only when the risk is low and the assumption is stated.

---

## 4. Simplicity First

Produce the smallest artifact that satisfies the current Step contract.

- Do not expand a direct-entry task into a full 8-Step workflow unless the user asks.
- Do not add databases, search branches, scoring dimensions, Zotero collections, or writing frameworks only for future flexibility.
- Do not generate decorative tables or long templates when a compact handoff is enough.
- Prefer a narrow, verifiable repair over a broad rerun.

A larger workflow is justified only when it closes a real evidence gap or a downstream contract cannot be satisfied otherwise.

---

## 5. Surgical Academic Changes

When revising an existing outline, manuscript, matrix, Zotero structure, or citation set:

- Change only the range needed for the user request.
- Preserve the user's intended argument unless evidence forces a downgrade.
- Do not rewrite adjacent sections for style preference alone.
- Remove orphan artifacts introduced by the current pass, but only flag pre-existing unrelated problems.
- In Step 8, do not add new claims, citations, or evidence unless the user explicitly asks for evidence expansion.

---

## 6. Verification Before Completion

A Step can be reported as complete only after the relevant completion gate is satisfied.

At minimum, distinguish:

- completed artifacts
- risks
- failed or skipped items
- items requiring user action
- evidence and traceability gaps

If the evidence is partial, use a partial-completion phrase such as `当前已形成可继续版本` rather than `已完成`.

---

## 7. Failure Triage Before Remedy

When search, download, Zotero mapping, evidence extraction, or writing fails, diagnose the layer before proposing a fix.

Use the failure-triage structure:

- Observed Symptom
- Likely Layer
- Required Evidence
- Next Action

Do not jump straight to broad reruns, source switching, mass rewriting, or manual cleanup before identifying the likely failure layer.

---

## 8. Evidence Discipline

Evidence status must stay conservative across the workflow.

- `candidate` is not `confirmed`.
- `metadata_only` is not full-text evidence.
- `abstract_only` cannot support strong mechanism claims.
- `unlinked_pdf` is not a verified download trace.
- `inferred` artifact relations must not be described as `confirmed`.
- Weak evidence should downgrade the claim, not be hidden by stronger language.

When evidence is insufficient, the correct output is a risk label, a narrower claim, or a request for additional material.

---

## 9. Communication Discipline

User-facing updates should say what changed, why it changed, and what remains uncertain.

Flag decisions that affect:

- database/source choice
- keyword scope
- scoring or filtering threshold
- download route
- Zotero collection mapping
- evidence grade
- citation confidence
- manuscript revision scope

Avoid explaining generic academic concepts the user already understands. Focus on the concrete decision and its consequence for the current artifact.
