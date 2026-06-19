#!/usr/bin/env python3
"""Export Step 4 literature-to-outline mapping artifacts.

Outputs:
  - 文献-大纲对照.json
  - 文献-大纲对照.md
"""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import json
from pathlib import Path

from workflow_contracts import load_search_records


def _normalize_tier(value: str) -> str:
    text = (value or "").strip().upper().replace(" ", "")
    mapping = {"TIER1": "T1", "TIER2": "T2", "TIER3": "T3", "TIER4": "T4"}
    return mapping.get(text, text or "UNKNOWN")


def build_mapping_records(workflow_path: Path) -> list[dict]:
    records = load_search_records(workflow_path)
    rows: list[dict] = []
    for idx, record in enumerate(records, 1):
        tier = _normalize_tier(record.paper_tier)
        if tier == "T4":
            continue
        rows.append({
            "record_id": f"outline-{idx:04d}",
            "title": record.title,
            "source": record.source,
            "doi_or_source_id": record.doi or record.source_id,
            "search_task_id": record.search_task_id,
            "chapter_id": record.chapter_id,
            "chapter_title": record.chapter_title,
            "secondary_search_task_ids": record.secondary_search_task_ids,
            "secondary_chapter_ids": record.secondary_chapter_ids,
            "secondary_chapter_titles": record.secondary_chapter_titles,
            "evidence_type": record.evidence_type,
            "paper_tier": tier,
            "score": record.score,
        })
    return rows


def write_json(path: Path, rows: list[dict]) -> None:
    payload = {
        "schema_version": "outline-mapping.v1",
        "artifact_type": "literature_outline_mapping",
        "record_count": len(rows),
        "records": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, rows: list[dict]) -> None:
    lines = [
        "# 文献-大纲对照",
        "",
        "- 本文件表示 Step 4 已完成的文献与大纲章节初始挂接。",
        "- 机器主源仍为 `workflow_search_results.json`；本文件用于人工审阅与 Step 6/7 回查。",
        "",
        "| 序号 | record_id | 标题 | 来源 | DOI/source_id | primary_search_task | primary_chapter_id | primary_chapter_title | secondary_chapters | evidence_type | Tier | Score |",
        "|------|-----------|------|------|---------------|---------------------|--------------------|-----------------------|--------------------|---------------|------|-------|",
    ]
    for i, row in enumerate(rows, 1):
        secondary = "；".join(
            f"{cid}:{ctitle}" for cid, ctitle in zip(row.get("secondary_chapter_ids", []), row.get("secondary_chapter_titles", []))
        )
        lines.append(
            "| {i} | {record_id} | {title} | {source} | {doi} | {task} | {chapter_id} | {chapter_title} | {secondary} | {evidence_type} | {tier} | {score} |".format(
                i=i,
                record_id=row["record_id"],
                title=row["title"].replace("|", "\\|"),
                source=row["source"],
                doi=(row["doi_or_source_id"] or "").replace("|", "\\|"),
                task=row["search_task_id"],
                chapter_id=row["chapter_id"],
                chapter_title=(row["chapter_title"] or "").replace("|", "\\|"),
                secondary=secondary.replace("|", "\\|"),
                evidence_type=row["evidence_type"],
                tier=row["paper_tier"],
                score=row["score"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export 文献-大纲对照.md/.json from workflow_search_results.json")
    parser.add_argument("--workflow-inputs", required=True, type=Path, help="Input workflow_search_results.json")
    parser.add_argument("--output-json", required=True, type=Path, help="Output JSON path")
    parser.add_argument("--output-md", required=True, type=Path, help="Output Markdown path")
    args = parser.parse_args()

    rows = build_mapping_records(args.workflow_inputs)
    write_json(args.output_json, rows)
    write_md(args.output_md, rows)
    print(f"EXPORTED {len(rows)}")
    print(f"JSON {args.output_json}")
    print(f"MD {args.output_md}")
    print("")
    print("Step 4 完成：")
    print("- 文献检索已完成")
    print("- 文献与大纲初始对照已生成")
    print("- 可回查字段：search_task_id / chapter_id / chapter_title / evidence_type")
    print("")
    print("下一步可选：")
    print("A. 继续 Step 5 下载 PDF")
    print("B. 继续 Step 6 生成 Zotero 对照与入库计划")
    print("")
    print("推荐回复词：")
    print("- 继续 Step 5")
    print("- 继续 Step 6")


if __name__ == "__main__":
    main()
