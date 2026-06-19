#!/usr/bin/env python3
"""Static platform compatibility scan for runtime docs and scripts."""
from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("scripts", "agents", "references", "docs", "commands")
SCAN_FILES = ("README.md", "SKILL.md")
TMP_RUNTIME_PREFIXES = ("scripts/", "agents/")


@dataclass(frozen=True)
class Finding:
    level: str
    path: Path
    line: int
    message: str


def _iter_text_files() -> list[Path]:
    files: list[Path] = []
    for rel in SCAN_FILES:
        p = ROOT / rel
        if p.exists():
            files.append(p)
    for dirname in SCAN_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".py", ".sh", ".md", ".txt"}:
                files.append(p)
    ignored = {
        ROOT / "scripts" / "check_platform_compat.py",
    }
    return sorted(p for p in set(files) if p not in ignored and "tests" not in p.parts)


def _allowed_macos_path(rel: str, text: str) -> bool:
    if rel == "scripts/cdp_utils.py":
        return True
    if rel in {"docs/ZOTERO_MCP_SETUP.md", "agents/known_pitfalls.md"}:
        return True
    return "macOS" in text or "macOS/Linux" in text


def scan() -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_text_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if "/Applications/Google Chrome" in line and not _allowed_macos_path(rel, line):
                findings.append(Finding(
                    "ERROR", path, idx,
                    "macOS Chrome path appears without platform scoping",
                ))
            if "open -na" in line and rel != "agents/known_pitfalls.md":
                findings.append(Finding(
                    "ERROR", path, idx,
                    "macOS open command appears in runtime docs/scripts",
                ))
            if "bash scripts/" in line and "macOS/Linux" not in line and "wrapper" not in line:
                findings.append(Finding(
                    "WARN", path, idx,
                    "bash entry should be labeled macOS/Linux or replaced by Python entry",
                ))
            if re.search(r"curl\s+-s\s+http://127\.0\.0\.1", line):
                findings.append(Finding(
                    "WARN", path, idx,
                    "curl-based localhost probe should have a Python alternative",
                ))
            if (
                rel.startswith(TMP_RUNTIME_PREFIXES)
                and rel != "scripts/gen_batch6.py"
                and "/tmp/" in line
                and "macOS" not in line
                and "Linux" not in line
                and "tempfile" not in line
            ):
                findings.append(Finding(
                    "WARN", path, idx,
                    "hard-coded /tmp path should be platform scoped or use tempfile",
                ))
            if "zotero-mcp" in line and "get_zotero_bin" in line:
                continue
            if rel == "scripts/setup_zotero.py" and "zotero-mcp.exe" not in "\n".join(lines):
                findings.append(Finding(
                    "ERROR", path, idx,
                    "setup_zotero.py must detect zotero-mcp.exe on Windows",
                ))
                break

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan platform compatibility risks.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    findings = scan()
    for finding in findings:
        rel = finding.path.relative_to(ROOT)
        print(f"{finding.level}: {rel}:{finding.line}: {finding.message}")

    has_error = any(f.level == "ERROR" for f in findings)
    has_warn = any(f.level == "WARN" for f in findings)
    if has_error or (args.strict and has_warn):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
