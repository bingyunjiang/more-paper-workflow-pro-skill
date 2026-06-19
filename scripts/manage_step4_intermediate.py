#!/usr/bin/env python3
"""Manage Step 4 intermediate search artifacts.

Modes:
  - keep: no-op, only report matched files
  - clean: delete matched intermediate files
  - archive: move matched intermediate files into archive/ or intermediate/
"""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import shutil
from pathlib import Path


INTERMEDIATE_PATTERNS = [
    "workflow_search_results.cnki_*.json",
    "workflow_search_results.wanfang_*.json",
    "workflow_search_results.*_v2.json",
    "workflow_search_results.*_zhcheck.json",
    "cnki_*.bib",
    "wanfang_*.bib",
]

PROTECTED_NAMES = {
    "workflow_search_results.json",
    "检索文献表.md",
    "检索文献表.xlsx",
    "检索报告.md",
    "检索报告.pdf",
    "文献库.bib",
    "中文论文元数据.json",
    "文献-大纲对照.md",
    "文献-大纲对照.json",
    "retrieval_index_manifest.json",
}


def collect_intermediate_files(root: Path) -> list[Path]:
    matched: list[Path] = []
    for pattern in INTERMEDIATE_PATTERNS:
        matched.extend(root.glob(pattern))
    unique = []
    seen = set()
    for path in matched:
        if path.name in PROTECTED_NAMES:
            continue
        if path.is_file() and path not in seen:
            unique.append(path)
            seen.add(path)
    return sorted(unique)


def keep_files(files: list[Path]) -> None:
    print(f"KEEP {len(files)}")
    for path in files:
        print(path)


def clean_files(files: list[Path]) -> None:
    print(f"CLEAN {len(files)}")
    for path in files:
        path.unlink(missing_ok=True)
        print(path)


def archive_files(files: list[Path], root: Path, archive_dir: str) -> None:
    target_dir = root / archive_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"ARCHIVE {len(files)} -> {target_dir}")
    for path in files:
        target = target_dir / path.name
        if target.exists():
            target.unlink()
        shutil.move(path.as_posix(), target.as_posix())
        print(f"{path} -> {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Keep/clean/archive Step 4 intermediate search artifacts.")
    parser.add_argument("--root", required=True, type=Path, help="Directory containing Step 4 artifacts")
    parser.add_argument("--mode", required=True, choices=["keep", "clean", "archive"], help="Artifact handling mode")
    parser.add_argument("--archive-dir", default="archive", help="Archive directory name for --mode archive")
    args = parser.parse_args()

    files = collect_intermediate_files(args.root)
    if args.mode == "keep":
        keep_files(files)
    elif args.mode == "clean":
        clean_files(files)
    else:
        archive_files(files, args.root, args.archive_dir)


if __name__ == "__main__":
    main()
