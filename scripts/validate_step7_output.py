#!/usr/bin/env python3
"""Validate the Step 7 writing artifact chain.

This checks whether a Step 7 output directory has the minimum runtime
artifacts before a draft is treated as complete. It does not judge prose
quality or citation correctness.
"""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


MECHANISM_TERMS = [
    "机理",
    "机制",
    "受力",
    "变形特征",
    "影响规律",
    "演化规律",
    "作用路径",
    "耦合",
    "mechanism",
    "mechanistic",
    "causal pathway",
    "coupling",
]

DRAFT_PATTERNS = [
    "*draft*.md",
    "*初稿*.md",
    "*草稿*.md",
    "论文*.md",
    "journal_paper*.md",
    "section_*draft*.md",
]


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _exists_any(root: Path, names: list[str], patterns: list[str] | None = None) -> bool:
    for name in names:
        if (root / name).exists():
            return True
    for pattern in patterns or []:
        if any(root.glob(pattern)):
            return True
    return False


def _find_drafts(root: Path) -> list[Path]:
    drafts: list[Path] = []
    seen: set[Path] = set()
    excluded = {
        "citation_audit.md",
        "引用审计报告.md",
        "draft_risk_summary.md",
        "step7_execution_card.md",
        "evidence_matrix.md",
        "journal_evidence_matrix.md",
    }
    for pattern in DRAFT_PATTERNS:
        for path in root.glob(pattern):
            if path.name in excluded:
                continue
            if path not in seen and path.is_file():
                seen.add(path)
                drafts.append(path)
    return sorted(drafts)


def _load_json(path: Path) -> object | None:
    try:
        return json.loads(_read_text(path))
    except Exception:
        return None


def _execution_card_text(root: Path) -> str:
    card = root / "step7_execution_card.md"
    return _read_text(card) if card.exists() else ""


def _mechanism_decision(root: Path, card_text: str) -> str:
    for path in [
        root / "mechanism_trigger_decision.json",
        root / "mechanism_trigger_decision.md",
    ]:
        if not path.exists():
            continue
        if path.suffix == ".json":
            payload = _load_json(path)
            if isinstance(payload, dict):
                decision = payload.get("decision") or payload.get("mechanism_trigger_decision")
                if isinstance(decision, str):
                    return decision
        text = _read_text(path)
        match = re.search(r"(enter_mechanism_analysis|skip_mechanism_analysis)", text)
        if match:
            return match.group(1)
    match = re.search(r"(enter_mechanism_analysis|skip_mechanism_analysis)", card_text)
    return match.group(1) if match else ""


def _figure_mode_present(root: Path, card_text: str) -> bool:
    if (root / "figure_asset_check.md").exists() or (root / "figure_asset_check.json").exists():
        return True
    risk = root / "draft_risk_summary.md"
    texts = [card_text]
    if risk.exists():
        texts.append(_read_text(risk))
    return any(re.search(r"figure_mode\s*[:=]\s*(auto_insert|post_write|skip)", text) for text in texts)


def _contains_mechanism_terms(text: str) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in MECHANISM_TERMS)


def validate(root: Path) -> tuple[list[Finding], dict[str, object]]:
    findings: list[Finding] = []
    drafts = _find_drafts(root)
    card_text = _execution_card_text(root)
    combined_draft_text = "\n".join(_read_text(path)[:5000] for path in drafts)
    task_text = "\n".join([card_text, combined_draft_text])
    mechanism_task = _contains_mechanism_terms(task_text)
    decision = _mechanism_decision(root, card_text)

    if drafts and not (root / "step7_execution_card.md").exists():
        findings.append(Finding("fail", "missing_execution_card", "draft exists but step7_execution_card.md is missing"))

    if drafts and not _exists_any(
        root,
        ["evidence_matrix.md", "综述矩阵.md", "deep_read_cards.md", "evidence_pack.json"],
        ["*evidence_matrix*.md", "*deep_read_cards*.json", "*deep_read_cards*.md"],
    ):
        findings.append(Finding("fail", "missing_evidence_mapping", "draft exists but no evidence matrix, deep_read_cards, or evidence_pack was found"))

    if drafts and not _exists_any(
        root,
        ["citation_audit.md", "引用审计报告.md", "claim_evidence_audit.md"],
        ["*citation*audit*.md", "*引用审计*.md", "*claim*evidence*audit*.md"],
    ):
        findings.append(Finding("fail", "missing_citation_audit", "draft exists but citation/claim evidence audit is missing"))

    if drafts and not _figure_mode_present(root, card_text):
        findings.append(Finding("fail", "missing_figure_gate", "draft exists but figure_asset_check or explicit figure_mode is missing"))

    if mechanism_task and not decision:
        findings.append(Finding("fail", "missing_mechanism_decision", "mechanism-like task detected but mechanism_trigger_decision is missing"))

    if mechanism_task and decision == "enter_mechanism_analysis":
        required = [
            ("mechanism_cards", ["mechanism_cards.md", "mechanism_cards.json"]),
            ("mechanism_argument_plan", ["mechanism_argument_plan.md", "mechanism_argument_plan.json"]),
            ("mechanism_claim_audit", ["mechanism_claim_audit.md", "mechanism_claim_audit.json"]),
        ]
        for code, names in required:
            if not _exists_any(root, names):
                findings.append(Finding("fail", f"missing_{code}", f"mechanism task entered analysis but {code} is missing"))

    summary = {
        "root": str(root),
        "draft_count": len(drafts),
        "mechanism_task_detected": mechanism_task,
        "mechanism_decision": decision,
        "status": "pass" if not any(item.severity == "fail" for item in findings) else "fail",
    }
    return findings, summary


def render(findings: list[Finding], summary: dict[str, object]) -> str:
    lines = [
        f"STEP7_VALIDATION: {summary['status']}",
        f"root: {summary['root']}",
        f"draft_count: {summary['draft_count']}",
        f"mechanism_task_detected: {summary['mechanism_task_detected']}",
        f"mechanism_decision: {summary['mechanism_decision'] or '-'}",
    ]
    for item in findings:
        lines.append(f"{item.severity.upper()}: {item.code}: {item.message}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Step 7 output artifacts before treating a draft as complete.")
    parser.add_argument("output_dir", help="Step 7 output directory")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    root = Path(args.output_dir).expanduser().resolve()
    findings, summary = validate(root)
    if args.json:
        print(json.dumps({
            "summary": summary,
            "findings": [item.__dict__ for item in findings],
        }, ensure_ascii=False, indent=2))
    else:
        print(render(findings, summary))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

