#!/usr/bin/env python3
"""Deterministic Step 7/8 scientific writing quality audit."""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class WritingQualityIssue:
    issue_id: str
    rule_id: str
    category: str
    severity: str
    location: str
    problem: str
    evidence_basis: str
    recommended_action: str
    rollback_target: str


SECTION_RULES = {
    "abstract": {
        "required": {
            "problem": [r"问题", r"challenge", r"problem"],
            "method": [r"方法", r"模型", r"实验", r"仿真", r"method", r"model", r"experiment", r"simulation"],
            "result": [r"\d+(?:\.\d+)?\s*%", r"提高", r"降低", r"结果", r"表明", r"result", r"improve", r"reduce"],
            "boundary": [r"工况", r"场景", r"条件", r"范围", r"under", r"condition", r"scenario"],
        },
        "gate": "abstract_quality_gate",
    },
    "introduction": {
        "required": {
            "gap": [r"不足", r"缺乏", r"尚未", r"however", r"gap", r"remain"],
            "scope": [r"本文", r"本研究", r"this work", r"we"],
            "contribution": [r"贡献", r"提出", r"建立", r"contribution", r"propose"],
        },
        "gate": "introduction_quality_gate",
    },
    "discussion": {
        "required": {
            "interpretation": [r"说明", r"表明", r"意味着", r"suggest", r"indicate"],
            "comparison": [r"相比", r"对比", r"基准", r"compared", r"baseline"],
            "limitation": [r"局限", r"限制", r"边界", r"limitation", r"limited"],
        },
        "gate": "discussion_quality_gate",
    },
    "conclusion": {
        "required": {
            "answer": [r"综上", r"因此", r"本文", r"conclude", r"in summary"],
            "finding": [r"发现", r"表明", r"结果", r"finding", r"result"],
            "scope": [r"范围", r"工况", r"场景", r"条件", r"scope", r"condition"],
        },
        "gate": "conclusion_quality_gate",
    },
}

GENERIC_ENDINGS = [r"具有重要意义", r"提供参考", r"奠定基础", r"important significance", r"future research"]
STRONG_NOVELTY = [r"首次", r"首创", r"first", r"novel", r"innovative"]


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _split_paragraphs(text: str) -> list[tuple[int, str]]:
    paragraphs = []
    for match in re.finditer(r"(?:^|\n\n)([^\n](?:.|\n(?!\n))*)", text):
        block = match.group(1).strip()
        if not block or block.startswith("#"):
            continue
        paragraphs.append((_line_of(text, match.start(1)), re.sub(r"\s+", " ", block)))
    return paragraphs


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _mk(
    issue_id: str,
    rule_id: str,
    category: str,
    severity: str,
    location: str,
    problem: str,
    recommended_action: str,
    rollback_target: str = "none",
    evidence_basis: str = "audit_scientific_writing_quality",
) -> WritingQualityIssue:
    return WritingQualityIssue(
        issue_id=issue_id,
        rule_id=rule_id,
        category=category,
        severity=severity,
        location=location,
        problem=problem,
        evidence_basis=evidence_basis,
        recommended_action=recommended_action,
        rollback_target=rollback_target,
    )


def audit_text(text: str, section_type: str = "auto") -> dict:
    section = _infer_section_type(text) if section_type == "auto" else section_type
    issues: list[WritingQualityIssue] = []
    if section in SECTION_RULES:
        issues.extend(_audit_section_gate(text, section))
    issues.extend(_audit_paragraph_function(text))
    issues.extend(_audit_figure_first(text))
    issues.extend(_audit_overclaim(text))

    summary = {
        "schema_version": "scientific-writing-quality-audit.v1",
        "section_type": section,
        "issue_count": len(issues),
        "critical_count": sum(1 for issue in issues if issue.severity == "critical"),
        "major_count": sum(1 for issue in issues if issue.severity == "major"),
        "minor_count": sum(1 for issue in issues if issue.severity == "minor"),
        "recommended_next_step": _recommended_next_step(issues),
    }
    return {"summary": summary, "issues": [asdict(issue) for issue in issues]}


def _infer_section_type(text: str) -> str:
    first_heading = next((line.strip("# ").lower() for line in text.splitlines() if line.startswith("#")), "")
    if any(token in first_heading for token in ("摘要", "abstract")):
        return "abstract"
    if any(token in first_heading for token in ("引言", "绪论", "introduction")):
        return "introduction"
    if any(token in first_heading for token in ("讨论", "discussion")):
        return "discussion"
    if any(token in first_heading for token in ("结论", "conclusion")):
        return "conclusion"
    return "general"


def _audit_section_gate(text: str, section: str) -> list[WritingQualityIssue]:
    config = SECTION_RULES[section]
    issues = []
    for move, patterns in config["required"].items():
        if not _contains_any(text, patterns):
            issues.append(_mk(
                issue_id=f"{section}-missing-{move}",
                rule_id=f"{config['gate']}.{move}",
                category="section_quality_gate",
                severity="major",
                location=section,
                problem=f"{config['gate']} 缺少 required move: {move}",
                recommended_action="补齐章节功能动作，若缺结果或证据则回退 Step 7",
                rollback_target="step_7_argument_plan",
            ))
    return issues


def _audit_paragraph_function(text: str) -> list[WritingQualityIssue]:
    issues = []
    for idx, (line, paragraph) in enumerate(_split_paragraphs(text), start=1):
        roles = 0
        role_hits = []
        role_patterns = {
            "context": [r"背景", r"近年来", r"with the development"],
            "method": [r"方法", r"模型", r"算法", r"method", r"model"],
            "result": [r"结果", r"提高", r"降低", r"\d+(?:\.\d+)?\s*%", r"result"],
            "discussion": [r"说明", r"意味着", r"机制", r"原因", r"suggest"],
        }
        for role, patterns in role_patterns.items():
            if _contains_any(paragraph, patterns):
                roles += 1
                role_hits.append(role)
        if roles >= 3:
            issues.append(_mk(
                issue_id=f"paragraph-multi-task-{idx:03d}",
                rule_id="paragraph_function_audit.single_task",
                category="paragraph_function",
                severity="minor",
                location=f"L{line}",
                problem=f"同一段可能同时承担多个任务：{', '.join(role_hits)}",
                recommended_action="拆分段落或明确主任务，避免背景、方法、结果、讨论混写",
            ))
    return issues


def _audit_figure_first(text: str) -> list[WritingQualityIssue]:
    issues = []
    visual_claims = list(re.finditer(r"(如图所示|图中可见|由图.*(?:证明|表明)|as shown in Fig)", text, re.IGNORECASE))
    for idx, hit in enumerate(visual_claims, start=1):
        window = text[max(0, hit.start() - 80): hit.end() + 80]
        if not re.search(r"(图\s*\d+|Fig\.?\s*\d+|Figure\s*\d+)", window, re.IGNORECASE):
            issues.append(_mk(
                issue_id=f"figure-first-missing-id-{idx:03d}",
                rule_id="figure_first_argument_plan.figure_or_table_id",
                category="figure_first_argument_plan",
                severity="major",
                location=f"L{_line_of(text, hit.start())}",
                problem="图表判断缺少明确 figure/table/panel 编号",
                recommended_action="补 figure_table_panel_binding，或删除视觉判断",
                rollback_target="step_7_argument_plan",
            ))
    return issues


def _audit_overclaim(text: str) -> list[WritingQualityIssue]:
    issues = []
    for idx, match in enumerate(re.finditer("|".join(GENERIC_ENDINGS + STRONG_NOVELTY), text, re.IGNORECASE), start=1):
        token = match.group(0)
        severity = "major" if _contains_any(token, STRONG_NOVELTY) else "minor"
        rollback = "step_7_citation_audit" if severity == "major" else "none"
        issues.append(_mk(
            issue_id=f"section-overclaim-{idx:03d}",
            rule_id="phrasebank_guardrail.claim_strength",
            category="claim_strength_boundary",
            severity=severity,
            location=f"L{_line_of(text, match.start())}",
            problem=f"可能存在空泛意义句或创新性过强措辞：{token}",
            recommended_action="降强度、补边界或回查证据覆盖",
            rollback_target=rollback,
        ))
    return issues


def _recommended_next_step(issues: list[WritingQualityIssue]) -> str:
    if any(issue.rollback_target != "none" and issue.severity in {"critical", "major"} for issue in issues):
        return "Step 7"
    if issues:
        return "Step 8"
    return "ready"


def render_markdown(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# Scientific Writing Quality Audit",
        "",
        f"- section_type: {summary['section_type']}",
        f"- issue_count: {summary['issue_count']}",
        f"- recommended_next_step: {summary['recommended_next_step']}",
        "",
    ]
    for issue in payload["issues"]:
        lines.extend([
            f"## {issue['issue_id']}",
            "",
            f"- rule_id: {issue['rule_id']}",
            f"- category: {issue['category']}",
            f"- severity: {issue['severity']}",
            f"- location: {issue['location']}",
            f"- problem: {issue['problem']}",
            f"- recommended_action: {issue['recommended_action']}",
            f"- rollback_target: {issue['rollback_target']}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit scientific writing section quality gates.")
    parser.add_argument("draft_md", help="Markdown/text path, or '-' for stdin")
    parser.add_argument("--section-type", choices=["auto", "general", "abstract", "introduction", "discussion", "conclusion"], default="auto")
    parser.add_argument("--output-json", help="Output JSON path")
    parser.add_argument("--output-md", help="Output Markdown path")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    args = parser.parse_args(argv)

    text = sys.stdin.read() if args.draft_md == "-" else Path(args.draft_md).read_text(encoding="utf-8", errors="replace")
    payload = audit_text(text, section_type=args.section_type)
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(render_markdown(payload), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif not args.output_json and not args.output_md:
        print(render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
