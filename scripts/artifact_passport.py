#!/usr/bin/env python3
"""Build or inspect the lightweight Artifact Passport for direct-step routing.

The passport is an offline routing/status index. It stores artifact pointers,
readiness, gaps, and risks; it never stores full paper text and never touches
network, downloads, or Zotero.
"""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
from pathlib import Path
import sys

from workflow_contracts import (
    ArtifactPassport,
    build_artifact_passport,
    load_artifact_passport,
    write_artifact_passport,
)


COMMON_PATTERNS = (
    "研究主题.md",
    "大纲关键词.md",
    "检索方案.md",
    "检索文献表.md",
    "检索文献表.xlsx",
    "文献库.bib",
    "中文论文元数据.json",
    "saturation_snapshot.json",
    "workflow*.json",
    "*search*results*.json",
    "*检索*results*.json",
    "*download*manifest*.json",
    "zotero-架构.md",
    "zotero-架构.json",
    "文献-Zotero架构对照.md",
    "文献-Zotero架构对照.json",
    "pdf-附件池索引.json",
    "引用审计报告.md",
    "论文初稿.md",
    "指定章节.md",
    "论文润色稿.md",
    "diagnostic_summary.md",
    ".skill-state/ai_trace_diagnostics.json",
)


COMMON_DIRS = (
    "paper-temp",
    "pdf",
    "PDF",
    "PDFs",
    "figures",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or show .skill-state/artifact_passport.json without side effects.",
    )
    parser.add_argument("--project-root", default=".", help="Project directory to scan.")
    parser.add_argument(
        "--entry-step",
        choices=["step4", "step5", "step6", "step7", "step8"],
        default="",
        help="Direct-entry step to evaluate without requiring earlier workflow steps.",
    )
    parser.add_argument("--scan", action="store_true", help="Scan common workflow artifact names.")
    parser.add_argument("--add", action="append", default=[], help="Add an explicit artifact path. Can repeat.")
    parser.add_argument("--output", help="Output JSON path. Defaults to PROJECT/.skill-state/artifact_passport.json.")
    parser.add_argument("--show", action="store_true", help="Show an existing passport instead of rebuilding unless --scan/--add is present.")
    return parser.parse_args()


def default_output(project_root: Path) -> Path:
    return project_root / ".skill-state" / "artifact_passport.json"


def scan_artifacts(project_root: Path) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()

    def add(path: Path) -> None:
        key = path.resolve().as_posix()
        if key not in seen and path.exists():
            seen.add(key)
            paths.append(path)

    for pattern in COMMON_PATTERNS:
        for path in project_root.glob(pattern):
            add(path)
    for dirname in COMMON_DIRS:
        add(project_root / dirname)
    for path in project_root.glob("*.docx"):
        add(path)
    for path in project_root.glob("*.pdf"):
        add(path)
    return paths


def print_summary(passport: ArtifactPassport) -> None:
    print(f"schema: {passport.schema_version}")
    print(f"project_root: {passport.project_root}")
    print(f"route_mode: {passport.route_mode}")
    if passport.current_step:
        print(f"current_step: {passport.current_step}")
    print(f"recommended_step: {passport.recommended_step}")
    print(f"artifacts: {len(passport.artifacts)}")
    print(f"nodes: {len(passport.nodes)}")
    print(f"edges: {len(passport.edges)}")
    if passport.gaps:
        print(f"gaps: {'; '.join(passport.gaps)}")
    if passport.risks:
        print(f"risks: {'; '.join(passport.risks)}")
    for readiness in passport.readiness:
        status = "ready" if readiness.ready else "blocked"
        modes = ", ".join(readiness.allowed_modes) if readiness.allowed_modes else "-"
        print(f"- {readiness.step}: {status}; route_mode={readiness.route_mode}; modes={modes}")
        if readiness.blocked_reason:
            print(f"  blocked_reason: {readiness.blocked_reason}")
        if readiness.risks:
            print(f"  risks: {'; '.join(readiness.risks)}")


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    output = Path(args.output).expanduser() if args.output else default_output(project_root)
    if not output.is_absolute():
        output = project_root / output

    if args.show and not args.scan and not args.add:
        if not output.exists():
            print(f"passport not found: {output}", file=sys.stderr)
            return 1
        print_summary(load_artifact_passport(output))
        return 0

    artifact_paths: list[Path] = []
    if args.scan:
        artifact_paths.extend(scan_artifacts(project_root))
    artifact_paths.extend(Path(p).expanduser() for p in args.add)

    passport = build_artifact_passport(project_root, artifact_paths, entry_step=args.entry_step)

    output.parent.mkdir(parents=True, exist_ok=True)
    write_artifact_passport(output, passport)
    print(f"wrote: {output}")
    print_summary(passport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
