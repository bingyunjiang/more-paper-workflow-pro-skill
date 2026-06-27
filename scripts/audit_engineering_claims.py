#!/usr/bin/env python3
"""Audit engineering/power-energy claims for Step 7/8 writing workflows."""

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
class EngineeringClaimFinding:
    finding_id: str
    defect_id: str
    category: str
    severity: str
    location: str
    claim_text: str
    evidence_basis: str
    recommended_action: str
    rollback_target: str


POWER_TERMS = [
    "充电桩", "储能", "电力电子", "EMS", "V2G", "快充", "无线充电", "超级电容",
    "并网", "DAB", "LLC", "逆变器", "变换器", "power electronics", "EV charging",
    "energy storage", "wireless charging", "supercapacitor",
]


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _sentences(text: str) -> list[tuple[int, str]]:
    chunks = re.split(r"(?<=[。！？.!?])\s*", text)
    result = []
    cursor = 0
    for chunk in chunks:
        stripped = chunk.strip()
        if not stripped:
            continue
        pos = text.find(stripped, cursor)
        cursor = max(pos + len(stripped), cursor)
        result.append((_line_of(text, pos), stripped))
    return result


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _mk(
    idx: int,
    defect_id: str,
    category: str,
    severity: str,
    line: int,
    sentence: str,
    recommended_action: str,
    rollback_target: str,
) -> EngineeringClaimFinding:
    return EngineeringClaimFinding(
        finding_id=f"engineering-claim-{idx:03d}",
        defect_id=defect_id,
        category=category,
        severity=severity,
        location=f"L{line}",
        claim_text=sentence[:240],
        evidence_basis="audit_engineering_claims heuristic",
        recommended_action=recommended_action,
        rollback_target=rollback_target,
    )


def audit_text(text: str) -> dict:
    findings: list[EngineeringClaimFinding] = []
    idx = 1
    for line, sentence in _sentences(text):
        if _has_any(sentence, [r"稳定", r"stable", r"stability", r"鲁棒"]):
            if not _has_any(sentence, [r"Bode", r"Nyquist", r"Lyapunov", r"小信号", r"阻抗", r"HIL", r"阶跃", r"扰动"]):
                findings.append(_mk(idx, "stability_claim_without_stability_evidence", "power_energy", "major", line, sentence, "补稳定性证据或降强度", "step_7_argument_plan"))
                idx += 1
        if _has_any(sentence, [r"效率", r"efficiency"]):
            if not _has_any(sentence, [r"负载", r"功率等级", r"温度", r"输入", r"输出", r"load", r"temperature", r"kW", r"W"]):
                findings.append(_mk(idx, "efficiency_without_test_conditions", "power_energy", "major", line, sentence, "补效率测试条件、负载点和温度边界", "step_7_argument_plan"))
                idx += 1
        if _has_any(sentence, [r"仿真", r"simulation"]) and _has_any(sentence, [r"验证", r"工程可行", r"硬件", r"prototype", r"validated"]):
            if not _has_any(sentence, [r"实验", r"样机", r"HIL", r"hardware", r"prototype"]):
                findings.append(_mk(idx, "only_simulation_no_hardware_for_hardware_claim", "method", "critical", line, sentence, "区分仿真与硬件验证，或补样机/HIL证据", "step_7_argument_plan"))
                idx += 1
        if _has_any(sentence, [r"V2G", r"车网互动"]):
            if _has_any(sentence, [r"收益", r"稳定", r"削峰", r"调频", r"benefit", r"stability"]) and not _has_any(sentence, [r"退化", r"SOC", r"用户", r"可用性", r"degradation", r"user"]):
                findings.append(_mk(idx, "v2g_benefit_without_degradation_or_user_constraint", "power_energy", "major", line, sentence, "补电池退化、SOC窗口和用户可用性约束", "step_7_argument_plan"))
                idx += 1
        if _has_any(sentence, [r"EMS", r"能量管理", r"优化", r"optimization"]):
            if _has_any(sentence, [r"降低", r"提升", r"最优", r"reduce", r"improve", r"optimal"]) and not _has_any(sentence, [r"约束", r"基准", r"场景", r"电价", r"SOC", r"constraint", r"baseline", r"scenario"]):
                findings.append(_mk(idx, "ems_optimization_without_constraints", "power_energy", "major", line, sentence, "补目标函数、约束、基准和场景设置", "step_7_argument_plan"))
                idx += 1
        if _has_any(sentence, [r"无线充电", r"wireless charging"]):
            if _has_any(sentence, [r"效率", r"高效", r"efficiency"]) and not _has_any(sentence, [r"偏移", r"EMI", r"EMC", r"异物", r"misalignment", r"load range"]):
                findings.append(_mk(idx, "wireless_charging_without_misalignment_or_emc", "power_energy", "major", line, sentence, "补偏移、负载范围和 EMI/EMC 边界", "step_7_argument_plan"))
                idx += 1
        if _has_any(sentence, [r"首次", r"首创", r"first", r"novel"]):
            findings.append(_mk(idx, "first_claim_without_search_coverage", "novelty", "major", line, sentence, "回查检索覆盖和对比边界，必要时降强度", "step_7_citation_audit"))
            idx += 1

    summary = {
        "schema_version": "engineering-claim-audit.v1",
        "domain_detected": _has_any(text, [re.escape(term) for term in POWER_TERMS]),
        "finding_count": len(findings),
        "critical_count": sum(1 for item in findings if item.severity == "critical"),
        "major_count": sum(1 for item in findings if item.severity == "major"),
        "recommended_next_step": "Step 7" if findings else "ready",
    }
    return {"summary": summary, "findings": [asdict(item) for item in findings]}


def render_markdown(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# Engineering Claim Audit",
        "",
        f"- domain_detected: {summary['domain_detected']}",
        f"- finding_count: {summary['finding_count']}",
        f"- recommended_next_step: {summary['recommended_next_step']}",
        "",
    ]
    for item in payload["findings"]:
        lines.extend([
            f"## {item['finding_id']}",
            "",
            f"- defect_id: {item['defect_id']}",
            f"- category: {item['category']}",
            f"- severity: {item['severity']}",
            f"- location: {item['location']}",
            f"- claim_text: {item['claim_text']}",
            f"- recommended_action: {item['recommended_action']}",
            f"- rollback_target: {item['rollback_target']}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit engineering claims in a draft.")
    parser.add_argument("draft_md", help="Markdown/text path, or '-' for stdin")
    parser.add_argument("--output-json", help="Output JSON path")
    parser.add_argument("--output-md", help="Output Markdown path")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    args = parser.parse_args(argv)

    text = sys.stdin.read() if args.draft_md == "-" else Path(args.draft_md).read_text(encoding="utf-8", errors="replace")
    payload = audit_text(text)
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
