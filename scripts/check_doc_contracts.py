#!/usr/bin/env python3
"""Structured documentation contract checks.

This script keeps README-facing claims tied to repository facts instead of
free-floating marketing numbers. It also checks that main Step files keep a
small common skeleton so large files can be split safely over time.
"""
from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PUBLISHERS = ROOT / "config" / "publishers.toml"
STEP5 = ROOT / "agents" / "step_5_download.md"

MAIN_STEP_FILES = (
    "agents/step_1_topic.md",
    "agents/step_2_outline.md",
    "agents/step_3_search_plan.md",
    "agents/step_4_search_score.md",
    "agents/step_5_download.md",
    "agents/step_6_zotero.md",
    "agents/step_7_writing.md",
    "agents/step_8_polishing.md",
)

REQUIRED_STEP_HEADINGS = (
    "适用任务",
    "输入要求",
    "标准输出",
    "执行流程",
    "质量门槛",
    "收尾检查",
    "故障排除",
)

DOC_LINE_BUDGETS = {
    "README.md": 1680,
    "agents/step_7_writing.md": 1686,
}

DRIFTY_CURRENT_README_PATTERNS = (
    r"\b\d+\+\s*个\s*Python CLI 脚本",
    r"\b\d+\+\s*Python CLI scripts",
    r"\b\d+\s*个\s*Agent 模块",
    r"\b\d+\s*Agent modules",
    r"\b\d+\s*独立 Agent 文件",
    r"\b\d+\s*independent Agent files",
    r"\b\d+\s*家出版社",
    r"\b\d+\s+publishers",
    r"\b\d+\+\s*家出版社",
    r"\b\d+\+\s*publishers",
    r"成功率\s*\d+(?:\.\d+)?%",
    r"\b\d+(?:\.\d+)?%\+",
    r"\b\d+\s*条触发词",
    r"\b\d+\s*trigger phrases",
)


@dataclass(frozen=True)
class Finding:
    level: str
    path: str
    line: int
    message: str


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _publisher_count() -> int:
    text = PUBLISHERS.read_text(encoding="utf-8")
    return len(re.findall(r"^\[publishers\.[^\]]+\]", text, flags=re.MULTILINE))


def _step5_route_phases() -> list[str]:
    text = STEP5.read_text(encoding="utf-8")
    phases: list[str] = []
    for phase in ("Phase 1", "Phase 2", "Phase 3", "Phase 4"):
        if f"{phase}:" in text or f"{phase}：" in text:
            phases.append(phase)
    return phases


def inventory() -> dict:
    main_step_paths = [ROOT / rel for rel in MAIN_STEP_FILES]
    return {
        "schema_version": "doc-contracts.v1",
        "python_script_count": len(list((ROOT / "scripts").glob("*.py"))),
        "step_document_count": len(list((ROOT / "agents").glob("step_*.md"))),
        "main_step_document_count": len(main_step_paths),
        "publisher_config_count": _publisher_count(),
        "step5_route_phases": _step5_route_phases(),
        "line_counts": {
            rel: _line_count(ROOT / rel)
            for rel in ("README.md", "agents/step_7_writing.md")
        },
    }


def _current_readme_text() -> str:
    text = README.read_text(encoding="utf-8")
    chinese = text.split("## 📋 版本历史", 1)[0]
    if "## 📖 Introduction" in text and "## 📋 Version History" in text:
        english = text.split("## 📖 Introduction", 1)[1].split("## 📋 Version History", 1)[0]
    else:
        english = ""
    return chinese + "\n" + english


def check_readme_current_claims() -> list[Finding]:
    findings: list[Finding] = []
    lines = _current_readme_text().splitlines()
    for line_no, line in enumerate(lines, start=1):
        for pattern in DRIFTY_CURRENT_README_PATTERNS:
            if re.search(pattern, line):
                findings.append(Finding(
                    "ERROR",
                    "README.md",
                    line_no,
                    f"current overview uses drift-prone numeric claim: {line.strip()}",
                ))
                break
    return findings


def check_step_structure() -> list[Finding]:
    findings: list[Finding] = []
    for rel in MAIN_STEP_FILES:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        headings = [
            line.strip("# ").strip()
            for line in text.splitlines()
            if line.startswith("## ")
        ]
        for required in REQUIRED_STEP_HEADINGS:
            if not any(required in heading for heading in headings):
                findings.append(Finding(
                    "ERROR",
                    rel,
                    1,
                    f"main Step file missing required section containing {required!r}",
                ))
        if "CHECKPOINT" not in text:
            findings.append(Finding(
                "ERROR",
                rel,
                1,
                "main Step file must define at least one checkpoint boundary",
            ))
    return findings


def check_doc_budgets() -> list[Finding]:
    findings: list[Finding] = []
    for rel, max_lines in DOC_LINE_BUDGETS.items():
        path = ROOT / rel
        line_count = _line_count(path)
        if line_count > max_lines:
            findings.append(Finding(
                "ERROR",
                rel,
                max_lines + 1,
                f"document exceeds line budget: {line_count} > {max_lines}",
            ))
    return findings


def check() -> list[Finding]:
    return check_readme_current_claims() + check_step_structure() + check_doc_budgets()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check structured documentation contracts.")
    parser.add_argument("--json", action="store_true", help="Print generated inventory as JSON.")
    args = parser.parse_args()

    findings = check()
    if args.json:
        payload = inventory()
        payload["findings"] = [asdict(finding) for finding in findings]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for finding in findings:
            print(f"{finding.level}: {finding.path}:{finding.line}: {finding.message}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
