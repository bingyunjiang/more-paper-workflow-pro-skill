#!/usr/bin/env python3
"""Audit Step 7 mechanism draft paragraphs against mechanism_argument_plan."""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))


def _load_plan(path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = _load_json(path)
    claims = payload.get("claims") if isinstance(payload, dict) else None
    if isinstance(claims, list):
        return [claim for claim in claims if isinstance(claim, dict)], payload.get("metadata") or {}
    raise SystemExit(f"Unsupported mechanism argument plan JSON shape: {path}")


def _split_paragraphs(text: str) -> list[str]:
    blocks = []
    for block in re.split(r"\n\s*\n", text):
        stripped = block.strip()
        if not stripped:
            continue
        if stripped.startswith("#") or stripped.startswith("![") or stripped.startswith("*图 ") or stripped.startswith("（来源："):
            continue
        blocks.append(stripped.replace("\n", " "))
    return blocks


def _score_claim(paragraph: str, claim: dict[str, Any]) -> int:
    blob = paragraph.lower()
    score = 0
    for field in ("mechanism_type", "state_variables", "discriminates_against"):
        for token in claim.get(field, []) or []:
            token_text = _clean(token).lower()
            if token_text and token_text in blob:
                score += 2
    for field in ("phenomenon",):
        value = _clean(claim.get(field)).lower()
        if value and any(part in blob for part in re.findall(r"[a-zA-Z\u4e00-\u9fff]{2,}", value)[:6]):
            score += 2
    citekey = _clean(claim.get("source_citekey")).lower()
    if citekey and citekey in blob:
        score += 3
    return score


def _best_claim(paragraph: str, claims: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked = sorted(((claim, _score_claim(paragraph, claim)) for claim in claims), key=lambda item: item[1], reverse=True)
    if ranked and ranked[0][1] > 0:
        return ranked[0][0]
    return None


def _has_boundary_cue(paragraph: str) -> bool:
    cues = ["不能直接外推", "不直接替代", "仅适用于", "在该工况下", "边界", "限定", "不宜", "requires boundary", "not directly"]
    blob = paragraph.lower()
    return any(cue.lower() in blob for cue in cues)


def _has_figure_ref(paragraph: str) -> bool:
    return bool(re.search(r"图\s*\d+", paragraph))


def _contains_strong_word(paragraph: str) -> bool:
    return any(word in paragraph for word in ("证明", "证实", "验证了", "demonstrates", "proves", "validated"))


def _audit_paragraphs(text: str, claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for idx, paragraph in enumerate(_split_paragraphs(text), start=1):
        claim = _best_claim(paragraph, claims)
        issues: list[str] = []
        paragraph_type = "mechanism" if any(token in paragraph for token in ("机理", "机制", "CDRX", "DDRX", "GF", "GR", "DRV", "DRX")) else "general"
        if _contains_strong_word(paragraph) and claim and claim.get("confirmation_status") != "confirmed_for_strong_claim":
            issues.append("strong_word_without_confirmed_claim")
        if "如图" in paragraph and not _has_figure_ref(paragraph):
            issues.append("visual_reference_without_figure_id")
        if claim and claim.get("transfer_risk") in {"cross_material_requires_boundary", "same_family_different_material"} and not _has_boundary_cue(paragraph):
            issues.append("cross_material_claim_missing_boundary")
        if paragraph_type == "mechanism" and claim and claim.get("discriminates_against") and not any(item in paragraph for item in claim.get("discriminates_against", [])):
            issues.append("mechanism_discrimination_not_explicit")
        findings.append({
            "paragraph_id": f"para-{idx:02d}",
            "paragraph_type": paragraph_type,
            "claim_id": _clean(claim.get("claim_id")) if claim else "",
            "source_citekey": _clean(claim.get("source_citekey")) if claim else "",
            "issues": issues,
            "severity": "pass" if not issues else "revise_recommended",
            "paragraph_preview": paragraph[:180],
        })
    return findings


def _render_markdown(findings: list[dict[str, Any]]) -> str:
    lines = ["# Mechanism Paragraph Audit", ""]
    for item in findings:
        lines.extend([
            f"## {item['paragraph_id']}",
            "",
            f"- paragraph_type: {item['paragraph_type']}",
            f"- claim_id: {item['claim_id'] or 'unmatched'}",
            f"- source_citekey: {item['source_citekey'] or 'unmatched'}",
            f"- severity: {item['severity']}",
            f"- issues: {'; '.join(item['issues']) or 'none'}",
            f"- preview: {item['paragraph_preview']}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def audit_paragraphs(draft_md: Path, plan_json: Path, output_json: Path, output_md: Path) -> int:
    claims, metadata = _load_plan(plan_json)
    draft_text = draft_md.read_text(encoding="utf-8", errors="replace")
    findings = _audit_paragraphs(draft_text, claims)
    payload = {
        "schema_version": "mechanism-paragraph-audit.v1",
        "metadata": {
            **metadata,
            "source_plan": str(plan_json),
            "source_draft": str(draft_md),
        },
        "findings": findings,
    }
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(findings), encoding="utf-8")
    print(f"MECHANISM_PARAGRAPH_AUDIT: {output_json}")
    print(f"PARAGRAPHS: {len(findings)}")
    print(f"REVISE_RECOMMENDED: {sum(1 for item in findings if item['severity'] != 'pass')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Step 7 mechanism draft paragraphs.")
    parser.add_argument("--draft-md", required=True, help="Path to mechanism draft markdown")
    parser.add_argument("--plan-json", required=True, help="Path to mechanism_argument_plan.json")
    parser.add_argument("--output-json", default="mechanism_paragraph_audit.json", help="Output audit JSON path")
    parser.add_argument("--output-md", default="mechanism_paragraph_audit.md", help="Output audit Markdown path")
    args = parser.parse_args()
    return audit_paragraphs(
        draft_md=Path(args.draft_md).expanduser().resolve(),
        plan_json=Path(args.plan_json).expanduser().resolve(),
        output_json=Path(args.output_json).expanduser(),
        output_md=Path(args.output_md).expanduser(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
