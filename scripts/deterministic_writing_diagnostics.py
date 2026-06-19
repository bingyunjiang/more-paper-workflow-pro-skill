#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Deterministic writing diagnostics for Step 8 polishing.

This script turns high-confidence "AI-ish / mechanical writing" patterns into
structured issues that can be merged into revision_ledger.json.

Usage:
  python3 deterministic_writing_diagnostics.py draft.md
  python3 deterministic_writing_diagnostics.py draft.md --lang zh --json
  python3 deterministic_writing_diagnostics.py draft.md --output ai_trace_issues.json
  python3 deterministic_writing_diagnostics.py draft.md --summary-output diagnostic_summary_ai_trace.md
  python3 deterministic_writing_diagnostics.py draft.md --merge-ledger revision_ledger.json --merged-output revision_ledger.merged.json
  echo "text" | python3 deterministic_writing_diagnostics.py - --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

SEV_INFO = "INFO"
SEV_WARN = "WARN"

RULE_FAMILIES = {
    "stock_phrases": "套话短语规则",
    "mechanical_connectives": "机械连接词堆积规则",
    "superficial_insight": "伪洞见与悬垂表达规则",
    "vague_attribution": "空泛归因规则",
    "structural_gap": "结构/资料缺口规则",
    "monotone_rhythm": "句长节奏过匀规则",
    "redundant_dashes": "冗余破折号与插入语规则",
}

STOCK_PATTERNS_EN = [
    r"plays?\s+an?\s+(?:vital|crucial|pivotal|key|important)\s+role",
    r"it\s+is\s+worth\s+noting\s+that",
    r"paving\s+the\s+way\s+for",
]
STOCK_PATTERNS_ZH = [
    r"值得注意的是",
    r"综上所述",
    r"不言而喻",
]

CONNECTIVES_EN = ["moreover", "furthermore", "additionally", "notably"]
CONNECTIVES_ZH = ["此外", "另外", "首先", "其次", "更重要的是"]

SUPERFICIAL_PATTERNS = [
    r",\s+(?:highlighting|underscoring|illustrating|signaling|reinforcing)\b[^.,;]*",
]

VAGUE_ATTR_PATTERNS_EN = [
    r"\b(?:studies|researchers|scientists|experts)\s+(?:have\s+)?(?:shown|found|suggested|believe)\b",
]
VAGUE_ATTR_PATTERNS_ZH = [
    r"(?:研究|学者|专家)(?:普遍)?(?:认为|表明|发现|指出)",
]

STRUCTURAL_GAP_PATTERNS = [
    r"\[\[TODO[^\]]*\]\]",
    r"\[\[补文献[^\]]*\]\]",
    r"\[\[待补[^\]]*\]\]",
    r"(?:此处|这里)(?:需要|待)(?:补|补充)(?:文献|资料|数据|图表|实验)",
    r"(?:文献|资料|数据|图表|实验)(?:待补|缺失|不足)",
]


@dataclass
class DiagnosticIssue:
    issue_id: str
    category: str
    issue_type: str
    severity: str
    location: str
    problem: str
    evidence_basis: str
    allowed_action: str
    proposed_revision: str
    meaning_audit_required: bool
    meaning_audit_reason: str
    verification: dict
    final_status: str
    next_action: str
    issue_state: str
    state_reason: str
    rule_family: str
    rule_id: str
    rule_examples: list[str] = field(default_factory=list)
    density_signal: str = ""
    deficiency_kind: str = ""


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _split_sentences(text: str, lang: str) -> list[str]:
    if lang == "zh":
        parts = re.split(r"(?<=[。！？；])", text)
    else:
        parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _count_words(sentence: str, lang: str) -> int:
    if lang == "zh":
        return len(re.findall(r"[\u4e00-\u9fff]", sentence)) + len(re.findall(r"[A-Za-z]+", sentence))
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", sentence))


def _mk_issue(
    *,
    issue_id: str,
    category: str,
    severity: str,
    location: str,
    problem: str,
    allowed_action: str,
    proposed_revision: str,
    meaning_audit_required: bool,
    meaning_audit_reason: str,
    next_action: str = "",
    rule_family: str,
    rule_id: str,
    rule_examples: list[str],
    density_signal: str = "",
    evidence_basis: str = "deterministic-writing-diagnostics",
) -> DiagnosticIssue:
    if not next_action:
        if category == "可直接修订":
            next_action = "保留修改"
        elif category == "需作者决定":
            next_action = "转人工复核"
        else:
            next_action = "return_to_step_7_citation_audit"
    return DiagnosticIssue(
        issue_id=issue_id,
        category=category,
        issue_type="language_mechanical",
        severity=severity.lower(),
        location=location,
        problem=problem,
        evidence_basis=evidence_basis,
        allowed_action=allowed_action,
        proposed_revision=proposed_revision,
        meaning_audit_required=meaning_audit_required,
        meaning_audit_reason=meaning_audit_reason,
        verification={
            "term_consistency": "WARN",
            "meaning_drift": "WARN" if meaning_audit_required else "PASS",
            "claim_strength": "WARN" if meaning_audit_required else "PASS",
            "citation_reference_flow": "WARN" if meaning_audit_required else "PASS",
        },
        final_status="WARN",
        next_action=next_action,
        issue_state="identified",
        state_reason="由确定性写作诊断规则命中，待 Step 8 决定是否修订",
        rule_family=RULE_FAMILIES[rule_family],
        rule_id=rule_id,
        rule_examples=rule_examples[:3],
        density_signal=density_signal,
        deficiency_kind=(
            "citation_evidence"
            if next_action == "return_to_step_7_citation_audit"
            else ("structure_material" if next_action == "return_to_step_4_or_6" else "")
        ),
    )


def _pattern_hits(text: str, patterns: list[str], flags: int = re.IGNORECASE) -> list[re.Match]:
    hits: list[re.Match] = []
    for pattern in patterns:
        hits.extend(re.finditer(pattern, text, flags))
    return hits


def _check_stock_phrases(text: str, lang: str) -> list[DiagnosticIssue]:
    patterns = STOCK_PATTERNS_ZH if lang == "zh" else STOCK_PATTERNS_EN
    hits = _pattern_hits(text, patterns, 0 if lang == "zh" else re.IGNORECASE)
    if not hits:
        return []
    issue = _mk_issue(
        issue_id="ai-trace-stock-001",
        category="可直接修订",
        severity=SEV_WARN,
        location=f"L{_line_of(text, hits[0].start())}",
        problem=f"检测到套话短语/模板化句式 ×{len(hits)}，建议清理高频空泛表达。",
        allowed_action="直接修改",
        proposed_revision="删除套话短语，改为更具体的学术陈述或直接进入论点。",
        meaning_audit_required=False,
        meaning_audit_reason="",
        rule_family="stock_phrases",
        rule_id="stock_phrases.dense",
        rule_examples=[m.group(0) for m in hits[:3]],
        density_signal="dense" if len(hits) >= 3 else "sparse",
    )
    return [issue]


def _check_mechanical_connectives(text: str, lang: str) -> list[DiagnosticIssue]:
    words = CONNECTIVES_ZH if lang == "zh" else CONNECTIVES_EN
    total = 0
    first_line = 0
    for word in words:
        rx = re.compile(re.escape(word), 0 if lang == "zh" else re.IGNORECASE)
        matches = list(rx.finditer(text))
        if matches and not first_line:
            first_line = _line_of(text, matches[0].start())
        total += len(matches)
    if total < 3:
        return []
    return [
        _mk_issue(
            issue_id="ai-trace-connective-001",
            category="可直接修订",
            severity=SEV_WARN,
            location=f"L{first_line or 1}",
            problem=f"检测到机械连接词堆积 ×{total}，建议改为自然逻辑衔接或删去冗余连接。",
            allowed_action="直接修改",
            proposed_revision="压缩句首连接词，改用论证顺序或语义承接。",
            meaning_audit_required=False,
            meaning_audit_reason="",
            rule_family="mechanical_connectives",
            rule_id="mechanical_connectives.dense",
            rule_examples=words[:3],
            density_signal=f"hits={total}",
        )
    ]


def _check_superficial_insight(text: str) -> list[DiagnosticIssue]:
    hits = _pattern_hits(text, SUPERFICIAL_PATTERNS)
    if not hits:
        return []
    return [
        _mk_issue(
            issue_id="ai-trace-superficial-001",
            category="可直接修订",
            severity=SEV_WARN,
            location=f"L{_line_of(text, hits[0].start())}",
            problem=f"检测到伪洞见/悬垂表达 ×{len(hits)}，结尾抽象从句未增加实质信息。",
            allowed_action="局部补写",
            proposed_revision="改写为独立陈述句、限定句，或直接删除空转从句。",
            meaning_audit_required=False,
            meaning_audit_reason="",
            rule_family="superficial_insight",
            rule_id="superficial_insight.dangling",
            rule_examples=[m.group(0).strip() for m in hits[:3]],
            density_signal=f"hits={len(hits)}",
        )
    ]


def _check_vague_attribution(text: str, lang: str) -> list[DiagnosticIssue]:
    patterns = VAGUE_ATTR_PATTERNS_ZH if lang == "zh" else VAGUE_ATTR_PATTERNS_EN
    hits = _pattern_hits(text, patterns, 0 if lang == "zh" else re.IGNORECASE)
    if not hits:
        return []
    return [
        _mk_issue(
            issue_id="ai-trace-vague-001",
            category="当前依据不足",
            severity=SEV_WARN,
            location=f"L{_line_of(text, hits[0].start())}",
            problem=f"检测到空泛归因 ×{len(hits)}，若贴近关键 claim 应回查 Step 7 引用审计或原文支持。",
            allowed_action="人工决定",
            proposed_revision="改为更具体的来源表述，或保留并补充引用支撑检查。",
            meaning_audit_required=True,
            meaning_audit_reason="空泛归因可能影响句子强度，且可能与引用落点相邻。",
            next_action="return_to_step_7_citation_audit",
            rule_family="vague_attribution",
            rule_id="vague_attribution.generic",
            rule_examples=[m.group(0) for m in hits[:3]],
            density_signal=f"hits={len(hits)}",
            evidence_basis="deterministic-writing-diagnostics citation_risk_note",
        )
    ]


def _check_structural_gap(text: str) -> list[DiagnosticIssue]:
    hits = _pattern_hits(text, STRUCTURAL_GAP_PATTERNS)
    if not hits:
        return []
    return [
        _mk_issue(
            issue_id="ai-trace-structgap-001",
            category="当前依据不足",
            severity=SEV_WARN,
            location=f"L{_line_of(text, hits[0].start())}",
            problem=f"检测到结构/资料缺口提示 ×{len(hits)}，当前正文显式暴露待补文献、数据、图表或实验材料。",
            allowed_action="回退",
            proposed_revision="不要在 Step 8 内硬补；先回到 Step 4/6 补资料或证据底座，再继续润色。",
            meaning_audit_required=False,
            meaning_audit_reason="",
            next_action="return_to_step_4_or_6",
            rule_family="structural_gap",
            rule_id="structural_gap.placeholder",
            rule_examples=[m.group(0) for m in hits[:3]],
            density_signal=f"hits={len(hits)}",
            evidence_basis="deterministic-writing-diagnostics material_gap_note",
        )
    ]


def _check_monotone_rhythm(text: str, lang: str) -> list[DiagnosticIssue]:
    sentences = _split_sentences(text, lang)
    lengths = [_count_words(s, lang) for s in sentences]
    lengths = [x for x in lengths if x > 0]
    if len(lengths) < 5:
        return []
    mean = sum(lengths) / len(lengths)
    variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    cv = (variance ** 0.5) / mean if mean else 0
    if cv >= 0.35:
        return []
    return [
        _mk_issue(
            issue_id="ai-trace-rhythm-001",
            category="需作者决定",
            severity=SEV_INFO,
            location="document",
            problem=f"句长节奏偏均匀（cv={cv:.2f}），可能呈现机械化节奏。",
            allowed_action="人工决定",
            proposed_revision="仅在段落级做节奏调整；避免为追求人味而破坏论证清晰度。",
            meaning_audit_required=False,
            meaning_audit_reason="",
            rule_family="monotone_rhythm",
            rule_id="monotone_rhythm.cv",
            rule_examples=[f"cv={cv:.2f}", f"sentences={len(lengths)}"],
            density_signal=f"cv={cv:.2f}",
        )
    ]


def _check_redundant_dashes(text: str) -> list[DiagnosticIssue]:
    count = text.count("—") + text.count("–") + len(re.findall(r"\s-\s", text))
    if count < 3:
        return []
    return [
        _mk_issue(
            issue_id="ai-trace-dash-001",
            category="可直接修订",
            severity=SEV_INFO,
            location="document",
            problem=f"检测到冗余破折号/插入语偏多 ×{count}，建议收口解释性补充。",
            allowed_action="直接修改",
            proposed_revision="改为更紧凑的逗号、冒号或拆句，减少插入式拉伸结构。",
            meaning_audit_required=False,
            meaning_audit_reason="",
            rule_family="redundant_dashes",
            rule_id="redundant_dashes.count",
            rule_examples=["—", "–", " - "],
            density_signal=f"hits={count}",
        )
    ]


def diagnose_text(text: str, lang: str = "zh") -> dict:
    issues: list[DiagnosticIssue] = []
    issues.extend(_check_stock_phrases(text, lang))
    issues.extend(_check_mechanical_connectives(text, lang))
    issues.extend(_check_superficial_insight(text))
    issues.extend(_check_vague_attribution(text, lang))
    issues.extend(_check_structural_gap(text))
    issues.extend(_check_monotone_rhythm(text, lang))
    issues.extend(_check_redundant_dashes(text))

    summary = {
        "readiness": "partial" if issues else "complete",
        "can_continue": True,
        "blocking": [],
        "warnings": [
            "AI 味确定性检查只服务于 Step 8 润色诊断，不替代 Step 7 引用审计。"
        ] if issues else [],
        "recommended_next_step": "Step 8",
        "issue_count": len(issues),
        "direct_fix_count": sum(1 for i in issues if i.allowed_action in {"直接修改", "局部补写"}),
        "manual_review_count": sum(1 for i in issues if i.meaning_audit_required or i.allowed_action == "人工决定"),
        "citation_evidence_rollback_count": sum(1 for i in issues if i.next_action == "return_to_step_7_citation_audit"),
        "structure_material_rollback_count": sum(1 for i in issues if i.next_action == "return_to_step_4_or_6"),
        "rule_family_counts": {},
    }
    for issue in issues:
        summary["rule_family_counts"][issue.rule_family] = summary["rule_family_counts"].get(issue.rule_family, 0) + 1

    return {
        "summary": summary,
        "issues": [asdict(issue) for issue in issues],
    }


def render_diagnostic_summary_section(payload: dict) -> str:
    summary = payload["summary"]
    family_counts = summary["rule_family_counts"]
    hot_families = [f"{family} ×{count}" for family, count in family_counts.items()]
    high_density = [
        f"{item['location']} [{item['rule_family']}]"
        for item in payload["issues"]
        if item.get("density_signal") and item.get("location") != "document"
    ]
    lines = [
        "## AI 味确定性检查摘要",
        "",
        f"- 规则族命中数量：{summary['issue_count']}",
        f"- 高密度章节/段落：{'；'.join(high_density[:5]) if high_density else '无明显高密度段落'}",
        f"- 可直接修复项数量：{summary['direct_fix_count']}",
        f"- 需人工复核项数量：{summary['manual_review_count']}",
        f"- 引用/证据型回退数量：{summary['citation_evidence_rollback_count']}",
        f"- 结构/资料缺口回退数量：{summary['structure_material_rollback_count']}",
        "",
        "### 规则族分布",
    ]
    if hot_families:
        lines.extend([f"- {item}" for item in hot_families])
    else:
        lines.append("- 无命中")
    lines.extend(["", "### 处理提醒"])
    if payload["issues"]:
        lines.append("- 风格类命中默认不触发 rollback；仅作为 Step 8 润色诊断与修订分流依据。")
        lines.append("- 若空泛归因贴近关键 claim，建议回查 Step 7 引用审计或原文支持。")
    else:
        lines.append("- 本轮未检测到高置信 AI 味/机械化表达问题。")
    return "\n".join(lines) + "\n"


def merge_into_revision_ledger(existing: dict | None, payload: dict) -> dict:
    existing = existing or {}
    existing_issues = existing.get("issues", [])
    new_issues = payload["issues"]
    merged_by_id = {item["issue_id"]: item for item in existing_issues}
    for issue in new_issues:
        merged_by_id[issue["issue_id"]] = issue

    merged = dict(existing)
    merged["issues"] = list(merged_by_id.values())
    merged["ai_trace_diagnostics"] = {
        "summary": payload["summary"],
        "issue_ids": [item["issue_id"] for item in new_issues],
    }
    merged.setdefault("warnings", [])
    note = "已并入 deterministic writing diagnostics 结果"
    if note not in merged["warnings"]:
        merged["warnings"].append(note)
    return merged


def _render_md(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# AI 味确定性检查摘要",
        "",
        f"- 问题数：{summary['issue_count']}",
        f"- 可直接修复项：{summary['direct_fix_count']}",
        f"- 需人工复核项：{summary['manual_review_count']}",
        "",
        "## 规则族命中",
        "",
    ]
    for family, count in summary["rule_family_counts"].items():
        lines.append(f"- {family}: {count}")
    lines.extend(["", "## 结构化 issue", ""])
    for item in payload["issues"]:
        lines.append(f"- `{item['issue_id']}` {item['problem']} @ {item['location']}")
    return "\n".join(lines) + "\n"


def _read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Step 8 deterministic writing diagnostics")
    parser.add_argument("path", help="Markdown/text path, or '-' to read stdin")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    parser.add_argument("--output", help="Optional output path for JSON or Markdown")
    parser.add_argument("--summary-output", help="Write a diagnostic_summary.md-ready Markdown block")
    parser.add_argument("--merge-ledger", help="Existing revision_ledger.json path to merge issues into")
    parser.add_argument("--merged-output", help="Where to write merged revision_ledger JSON; defaults to --merge-ledger path")
    args = parser.parse_args(argv)

    payload = diagnose_text(_read_input(args.path), lang=args.lang)

    if args.output:
        out = Path(args.output)
        if args.json or out.suffix.lower() == ".json":
            out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            out.write_text(_render_md(payload), encoding="utf-8")

    if args.summary_output:
        Path(args.summary_output).write_text(render_diagnostic_summary_section(payload), encoding="utf-8")

    if args.merge_ledger:
        ledger_path = Path(args.merge_ledger)
        if ledger_path.exists():
            existing = json.loads(ledger_path.read_text(encoding="utf-8"))
        else:
            existing = {}
        merged = merge_into_revision_ledger(existing, payload)
        merged_path = Path(args.merged_output) if args.merged_output else ledger_path
        merged_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_md(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
