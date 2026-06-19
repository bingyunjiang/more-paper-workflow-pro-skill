#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Step 8 AI-trace runner.

Wires draft -> deterministic diagnostics -> diagnostic_summary block ->
revision_ledger merge into one local command for Step 8.

Usage:
  python3 run_step8_ai_trace.py --project-root .
  python3 run_step8_ai_trace.py --project-root . --draft 指定章节草稿.md --lang en
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from deterministic_writing_diagnostics import (
    diagnose_text,
    merge_into_revision_ledger,
    render_diagnostic_summary_section,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Step 8 AI-trace diagnostics with default artifact names.")
    parser.add_argument("--project-root", default=".", help="Project directory to operate on.")
    parser.add_argument("--draft", default="论文初稿.md", help="Draft path relative to project root or absolute path.")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh", help="Draft language for deterministic diagnostics.")
    parser.add_argument(
        "--diagnostics-json",
        default=".skill-state/ai_trace_diagnostics.json",
        help="Where to write raw diagnostics JSON.",
    )
    parser.add_argument(
        "--diagnostic-summary",
        default="diagnostic_summary.md",
        help="Where to write or update the Step 8 diagnostic summary.",
    )
    parser.add_argument(
        "--revision-ledger",
        default="revision_ledger.json",
        help="Where to write or update the merged revision ledger JSON.",
    )
    parser.add_argument(
        "--revision-ledger-md",
        default="revision_ledger.md",
        help="Where to write the human-readable revision ledger Markdown.",
    )
    parser.add_argument(
        "--polish-quality-report",
        default="润色质量报告.md",
        help="Where to write or update the polish quality report.",
    )
    return parser.parse_args()


def _resolve(project_root: Path, candidate: str) -> Path:
    path = Path(candidate).expanduser()
    if path.is_absolute():
        return path
    return project_root / path


def _replace_or_append_section(existing: str, heading: str, section_body: str) -> str:
    if heading not in existing:
        existing = existing.rstrip()
        spacer = "\n\n" if existing else ""
        return f"{existing}{spacer}{section_body}".strip() + "\n"

    lines = existing.splitlines()
    new_lines: list[str] = []
    in_target = False
    replaced = False
    section_lines = section_body.rstrip().splitlines()
    for line in lines:
        if line.strip() == heading:
            if not replaced:
                new_lines.extend(section_lines)
                replaced = True
            in_target = True
            continue
        if in_target and line.startswith("## "):
            in_target = False
            new_lines.append(line)
            continue
        if not in_target:
            new_lines.append(line)
    return "\n".join(new_lines).rstrip() + "\n"


def _compute_step8_decision(payload: dict) -> dict:
    summary = payload["summary"]
    structure_rollbacks = summary.get("structure_material_rollback_count", 0)
    citation_rollbacks = summary.get("citation_evidence_rollback_count", 0)
    direct_fix_count = summary.get("direct_fix_count", 0)
    manual_review_count = summary.get("manual_review_count", 0)
    issue_count = summary.get("issue_count", 0)

    if structure_rollbacks > 0:
        return {
            "overall_status": "not_ready_requires_rollback",
            "next_action": "return_to_step_4_or_6",
            "decision_reason": "存在结构/资料缺口回退项，Step 8 不应在证据底座缺失时继续硬修。",
        }
    if citation_rollbacks > 0:
        return {
            "overall_status": "ready_with_warnings",
            "next_action": "return_to_step_7_citation_audit",
            "decision_reason": "存在引用/证据型回退项，正文可局部保留，但应先回到 Step 7 做引用审计或原文确认。",
        }
    if issue_count == 0:
        return {
            "overall_status": "ready_for_finalize",
            "next_action": "finalize_polished_draft",
            "decision_reason": "未检测到高置信 AI 味/机械化表达问题。",
        }
    if manual_review_count == 0 and direct_fix_count == issue_count:
        return {
            "overall_status": "ready_for_finalize",
            "next_action": "finalize_polished_draft",
            "decision_reason": "仅存在可直接修订的轻量问题，未触发人工复核或回退。",
        }
    return {
        "overall_status": "ready_with_warnings",
        "next_action": "转人工复核",
        "decision_reason": "存在需作者决定或人工复核项，但未达到必须回退证据底座的程度。",
    }


def _compute_status_contract(payload: dict, step8_decision: dict) -> dict:
    summary = payload["summary"]
    overall_status = step8_decision["overall_status"]
    next_action = step8_decision["next_action"]

    if overall_status == "ready_for_finalize":
        return {
            "readiness": "complete",
            "can_continue": True,
            "blocking": [],
            "warnings": [],
            "recommended_next_step": "Step 8",
        }

    if overall_status == "not_ready_requires_rollback":
        blocking = []
        if summary.get("structure_material_rollback_count", 0) > 0:
            blocking.append("存在待补文献/图表/实验材料，占位提示尚未闭环")
        return {
            "readiness": "blocked",
            "can_continue": False,
            "blocking": blocking,
            "warnings": [],
            "recommended_next_step": "Step 4/6" if next_action == "return_to_step_4_or_6" else "Step 7",
        }

    warnings: list[str] = []
    if summary.get("citation_evidence_rollback_count", 0) > 0:
        warnings.append("存在引用/证据型回退项，建议回到 Step 7 做引用审计或原文确认")
    if summary.get("manual_review_count", 0) > 0:
        warnings.append("存在需作者决定或人工复核项，当前仅建议带警告继续")
    if summary.get("issue_count", 0) > 0:
        warnings.append("仍有 AI 味/机械化表达问题待处理或待确认")

    recommended = "Step 8"
    if next_action == "return_to_step_7_citation_audit":
        recommended = "Step 7"
    elif next_action == "return_to_step_4_or_6":
        recommended = "Step 4/6"

    return {
        "readiness": "partial",
        "can_continue": True,
        "blocking": [],
        "warnings": warnings,
        "recommended_next_step": recommended,
    }


def _render_revision_ledger_md(ledger: dict) -> str:
    issues = ledger.get("issues", [])
    ai_summary = ledger.get("ai_trace_diagnostics", {}).get("summary", {})
    step8_decision = ledger.get("ai_trace_diagnostics", {}).get("step8_decision", {})
    status_contract = ledger.get("ai_trace_diagnostics", {}).get("status_contract", {})
    category_order = ["可直接修订", "需作者决定", "当前依据不足"]
    category_buckets = {name: [] for name in category_order}
    for issue in issues:
        category = issue.get("category", "需作者决定")
        category_buckets.setdefault(category, []).append(issue)
    lines = [
        "# revision_ledger",
        "",
        f"- issues: {len(issues)}",
        f"- direct_fix_count: {ai_summary.get('direct_fix_count', 0)}",
        f"- manual_review_count: {ai_summary.get('manual_review_count', 0)}",
        f"- overall_status: `{step8_decision.get('overall_status', '')}`",
        f"- next_action: `{step8_decision.get('next_action', '')}`",
        f"- readiness: `{status_contract.get('readiness', '')}`",
        f"- can_continue: `{status_contract.get('can_continue', '')}`",
        f"- recommended_next_step: `{status_contract.get('recommended_next_step', '')}`",
        "",
        "## Step 8 问题闭环摘要",
        "",
        "| issue_id | issue_type | severity | allowed_action | next_action | rule_family |",
        "|---|---|---|---|---|---|",
    ]
    for issue in issues:
        lines.append(
            "| {issue_id} | {issue_type} | {severity} | {allowed_action} | {next_action} | {rule_family} |".format(
                issue_id=issue.get("issue_id", ""),
                issue_type=issue.get("issue_type", ""),
                severity=issue.get("severity", ""),
                allowed_action=issue.get("allowed_action", ""),
                next_action=issue.get("next_action", ""),
                rule_family=issue.get("rule_family", ""),
            )
        )
    lines.extend(["", "## 问题分流", ""])
    for category in category_order:
        bucket = category_buckets.get(category, [])
        default_route = {
            "可直接修订": "保留修改",
            "需作者决定": "转人工复核",
            "当前依据不足": "return_to_step_7_citation_audit / return_to_step_4_or_6",
        }[category]
        lines.extend([f"### {category}", "", f"- count: {len(bucket)}", f"- default_next_action: `{default_route}`", ""])
        if not bucket:
            lines.append("- 无")
            lines.append("")
            continue
        if category == "当前依据不足":
            citation_evidence = [item for item in bucket if item.get("deficiency_kind") == "citation_evidence"]
            structure_material = [item for item in bucket if item.get("deficiency_kind") == "structure_material"]
            other = [item for item in bucket if item not in citation_evidence and item not in structure_material]
            subgroups = [
                ("#### 引用/证据型回退", citation_evidence),
                ("#### 结构/资料缺口回退", structure_material),
                ("#### 其他待判断缺口", other),
            ]
            for heading, subgroup in subgroups:
                lines.extend([heading, "", f"- count: {len(subgroup)}", ""])
                if not subgroup:
                    lines.extend(["- 无", ""])
                    continue
                for issue in subgroup:
                    lines.extend(
                        [
                            f"##### {issue.get('issue_id', '')}",
                            "",
                            f"- issue_type: `{issue.get('issue_type', '')}`",
                            f"- severity: `{issue.get('severity', '')}`",
                            f"- location: `{issue.get('location', '')}`",
                            f"- allowed_action: `{issue.get('allowed_action', '')}`",
                            f"- next_action: `{issue.get('next_action', '')}`",
                            f"- deficiency_kind: `{issue.get('deficiency_kind', '')}`",
                            f"- rule_family: `{issue.get('rule_family', '')}`",
                            f"- problem: {issue.get('problem', '')}",
                            f"- proposed_revision: {issue.get('proposed_revision', '')}",
                            f"- rule_examples: {', '.join(issue.get('rule_examples', [])) or '无'}",
                            "",
                        ]
                    )
            continue
        for issue in bucket:
            lines.extend(
                [
                    f"#### {issue.get('issue_id', '')}",
                    "",
                    f"- issue_type: `{issue.get('issue_type', '')}`",
                    f"- severity: `{issue.get('severity', '')}`",
                    f"- location: `{issue.get('location', '')}`",
                    f"- allowed_action: `{issue.get('allowed_action', '')}`",
                    f"- next_action: `{issue.get('next_action', '')}`",
                    f"- deficiency_kind: `{issue.get('deficiency_kind', '')}`",
                    f"- rule_family: `{issue.get('rule_family', '')}`",
                    f"- problem: {issue.get('problem', '')}",
                    f"- proposed_revision: {issue.get('proposed_revision', '')}",
                    f"- rule_examples: {', '.join(issue.get('rule_examples', [])) or '无'}",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def _render_polish_quality_report_section(payload: dict) -> str:
    summary = payload["summary"]
    decision = _compute_step8_decision(payload)
    status_contract = _compute_status_contract(payload, decision)
    lines = [
        "## AI 味检查结果",
        "",
        f"- 命中问题数：{summary['issue_count']}",
        f"- 已处理的高频机械表达候选：{summary['direct_fix_count']}",
        f"- 保留未改的风格性项：{max(summary['issue_count'] - summary['direct_fix_count'], 0)}",
        f"- 建议作者人工复核项：{summary['manual_review_count']}",
        f"- 引用/证据型回退数量：{summary['citation_evidence_rollback_count']}",
        f"- 结构/资料缺口回退数量：{summary['structure_material_rollback_count']}",
        f"- Overall Status：`{decision['overall_status']}`",
        f"- Next Action：`{decision['next_action']}`",
        "",
        "### 统一状态契约",
        f"- readiness：`{status_contract['readiness']}`",
        f"- can_continue：`{status_contract['can_continue']}`",
        f"- blocking：{status_contract['blocking'] or '[]'}",
        f"- warnings：{status_contract['warnings'] or '[]'}",
        f"- recommended_next_step：`{status_contract['recommended_next_step']}`",
        "",
        "### 说明",
        "- AI 味确定性检查只服务于润色诊断，不替代 Step 7 引用审计。",
        "- 风格类命中默认不触发 rollback；仅作为 Step 8 局部修订与人工复核分流依据。",
        f"- 判定理由：{decision['decision_reason']}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    draft_path = _resolve(project_root, args.draft)
    diagnostics_json = _resolve(project_root, args.diagnostics_json)
    diagnostic_summary = _resolve(project_root, args.diagnostic_summary)
    revision_ledger = _resolve(project_root, args.revision_ledger)
    revision_ledger_md = _resolve(project_root, args.revision_ledger_md)
    polish_quality_report = _resolve(project_root, args.polish_quality_report)

    text = draft_path.read_text(encoding="utf-8")
    payload = diagnose_text(text, lang=args.lang)
    step8_decision = _compute_step8_decision(payload)
    status_contract = _compute_status_contract(payload, step8_decision)

    diagnostics_json.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_payload = dict(payload)
    diagnostics_payload["step8_decision"] = step8_decision
    diagnostics_payload["status_contract"] = status_contract
    diagnostics_json.write_text(json.dumps(diagnostics_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_block = render_diagnostic_summary_section(payload)
    summary_block += (
        "\n"
        "### Step 8 总判断\n"
        f"- Overall Status：`{step8_decision['overall_status']}`\n"
        f"- Next Action：`{step8_decision['next_action']}`\n"
        f"- 判定理由：{step8_decision['decision_reason']}\n"
        "\n"
        "### 统一状态契约\n"
        f"- readiness：`{status_contract['readiness']}`\n"
        f"- can_continue：`{status_contract['can_continue']}`\n"
        f"- blocking：{status_contract['blocking'] or '[]'}\n"
        f"- warnings：{status_contract['warnings'] or '[]'}\n"
        f"- recommended_next_step：`{status_contract['recommended_next_step']}`\n"
    )
    if diagnostic_summary.exists():
        current = diagnostic_summary.read_text(encoding="utf-8")
    else:
        current = "# diagnostic_summary\n"
    updated_summary = _replace_or_append_section(current, "## AI 味确定性检查摘要", summary_block)
    diagnostic_summary.write_text(updated_summary, encoding="utf-8")

    if revision_ledger.exists():
        existing_ledger = json.loads(revision_ledger.read_text(encoding="utf-8"))
    else:
        existing_ledger = {}
    merged_ledger = merge_into_revision_ledger(existing_ledger, payload)
    merged_ledger.setdefault("ai_trace_diagnostics", {})
    merged_ledger["ai_trace_diagnostics"]["step8_decision"] = step8_decision
    merged_ledger["ai_trace_diagnostics"]["status_contract"] = status_contract
    revision_ledger.write_text(json.dumps(merged_ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    revision_ledger_md.write_text(_render_revision_ledger_md(merged_ledger), encoding="utf-8")

    polish_block = _render_polish_quality_report_section(payload)
    if polish_quality_report.exists():
        current_report = polish_quality_report.read_text(encoding="utf-8")
    else:
        current_report = "# 润色质量报告\n"
    updated_report = _replace_or_append_section(current_report, "## AI 味检查结果", polish_block)
    polish_quality_report.write_text(updated_report, encoding="utf-8")

    print(f"draft: {draft_path}")
    print(f"diagnostics_json: {diagnostics_json}")
    print(f"diagnostic_summary: {diagnostic_summary}")
    print(f"revision_ledger: {revision_ledger}")
    print(f"revision_ledger_md: {revision_ledger_md}")
    print(f"polish_quality_report: {polish_quality_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
