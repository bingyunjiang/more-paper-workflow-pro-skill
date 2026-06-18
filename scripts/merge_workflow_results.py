#!/usr/bin/env python3
"""Merge incremental Step 4 workflow results into an existing main workflow.

Behavior:
  1. Load base workflow_search_results.json
  2. Append records from one or more incremental workflow JSON files
  3. Re-run Step 4 deduplication rules automatically
  4. Overwrite the main workflow JSON with the deduplicated result

This keeps incremental literature supplementation and deduplication tied
together so agents do not need to remember the manual sequence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from search_by_topic import deduplicate
from workflow_contracts import load_json


def _load_records(path: Path) -> list[dict]:
    data = load_json(path)
    if isinstance(data, dict):
        return [r for r in (data.get("records") or []) if isinstance(r, dict)]
    return []


def merge_workflow_results(base_path: Path, incoming_paths: list[Path]) -> dict:
    base_payload = load_json(base_path)
    if not isinstance(base_payload, dict):
        raise ValueError("Base workflow JSON must be an object payload")

    base_records = [r for r in (base_payload.get("records") or []) if isinstance(r, dict)]
    merged = list(base_records)
    incoming_total = 0
    for path in incoming_paths:
        rows = _load_records(path)
        incoming_total += len(rows)
        merged.extend(rows)

    deduped = deduplicate(merged)
    metadata = dict(base_payload.get("metadata") or {})
    metadata["incremental_merge_applied"] = True
    metadata["incoming_file_count"] = len(incoming_paths)
    metadata["incoming_record_count"] = incoming_total
    metadata["merged_record_count_before_dedup"] = len(merged)
    metadata["merged_record_count_after_dedup"] = len(deduped)

    base_payload["metadata"] = metadata
    base_payload["records"] = deduped
    return base_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge incremental workflow_search_results.json files and auto-deduplicate.")
    parser.add_argument("--base", required=True, type=Path, help="Base workflow_search_results.json")
    parser.add_argument("--incoming", required=True, nargs="+", type=Path, help="Incoming workflow JSON files to merge")
    parser.add_argument("--output", type=Path, help="Output path (default: overwrite --base)")
    args = parser.parse_args()

    merged = merge_workflow_results(args.base, args.incoming)
    out = args.output or args.base
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OUTPUT {out}")
    print(f"MERGED_AFTER_DEDUP {len(merged.get('records', []))}")
    print("")
    print("已完成增量合并，并同步执行 Step 4 去重。")
    print("下一步建议：")
    print("- 重新导出 检索文献表 / 文献库.bib / 中文论文元数据.json")
    print("- 如需更新章节挂接交付物，继续导出 文献-大纲对照.md/.json")


if __name__ == "__main__":
    main()
