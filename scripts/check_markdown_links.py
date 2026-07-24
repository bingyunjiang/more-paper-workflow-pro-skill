#!/usr/bin/env python3
"""Check repository-local Markdown links.

The check resolves relative links from the Markdown file that contains them,
matching normal Markdown semantics. External URLs, mailto links, and pure
anchors are ignored.
"""
from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = (
    "agents",
    "commands",
    "docs",
    "examples",
    "references",
    "scripts",
    "skills",
    "tests",
)
SCAN_FILES = ("README.md", "SKILL.md", "CHANGELOG.md")
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
REF_RE = re.compile(r"^\s*\[[^\]]+\]:\s+(\S+)")
SCHEMES_TO_SKIP = {"http", "https", "mailto", "tel", "ftp", "data"}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    target: str
    resolved: Path


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for rel in SCAN_FILES:
        path = ROOT / rel
        if path.exists():
            files.append(path)
    for dirname in SCAN_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        files.extend(path for path in base.rglob("*.md") if path.is_file())
    return sorted(set(files))


def is_ignored_target(target: str) -> bool:
    target = target.strip()
    if not target or target.startswith("#"):
        return True
    parsed = urlparse(target)
    if parsed.scheme in SCHEMES_TO_SKIP:
        return True
    return bool(parsed.scheme and parsed.scheme not in {"", "file"})


def strip_fragment(target: str) -> str:
    return target.split("#", 1)[0]


def resolve_target(markdown_path: Path, target: str) -> Path:
    clean = unquote(strip_fragment(target))
    if clean.startswith("/"):
        return ROOT / clean.lstrip("/")
    return markdown_path.parent / clean


def iter_targets(line: str) -> list[str]:
    targets: list[str] = []
    for match in LINK_RE.finditer(line):
        targets.append(match.group(1) or match.group(2))
    ref_match = REF_RE.match(line)
    if ref_match:
        targets.append(ref_match.group(1))
    return targets


def scan() -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_markdown_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel == "scripts/packages/README.md":
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(lines, start=1):
            for target in iter_targets(line):
                if is_ignored_target(target):
                    continue
                resolved = resolve_target(path, target)
                if not resolved.exists():
                    findings.append(Finding(path, line_no, target, resolved))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository-local Markdown relative links.")
    parser.parse_args()

    findings = scan()
    for finding in findings:
        rel = finding.path.relative_to(ROOT)
        resolved = finding.resolved.relative_to(ROOT) if finding.resolved.is_relative_to(ROOT) else finding.resolved
        print(f"ERROR: {rel}:{finding.line}: missing link target {finding.target!r} -> {resolved}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
