#!/usr/bin/env python3
"""Export Step 4 Chinese metadata handoff from workflow_search_results.json.

This artifact is the preferred machine-source for Step 5 Chinese downloads and
Step 6 Chinese Zotero entry creation. It must preserve title/authors/abstract/
source_id/article_url in full.
"""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import json
import re
from pathlib import Path

from workflow_contracts import load_search_records


def _source_id_short(source_id: str, fallback: str = "record") -> str:
    text = (source_id or "").strip().lower()
    if not text:
        return fallback
    for prefix in ("cnki.", "wanfang."):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    text = re.sub(r"[^a-z0-9]", "", text)
    return text[:8] if text else fallback


def _stable_chinese_citekey(source: str, year: str, source_id: str) -> str:
    year_str = (year or "????").strip() or "????"
    if source == "cnki":
        return f"CNKI{year_str}_cnki{_source_id_short(source_id)}"
    return f"Wanfang{year_str}_wf{_source_id_short(source_id)}"


def export_chinese_records(workflow_path: Path) -> list[dict]:
    records = load_search_records(workflow_path)
    exported: list[dict] = []
    for record in records:
        if record.source not in {"cnki", "wanfang"}:
            continue
        if not record.article_url:
            continue
        raw = record.raw or {}
        raw_inner = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}
        publication_title = (
            raw.get("publication_title")
            or raw_inner.get("publication_title")
            or raw.get("venue")
            or raw_inner.get("venue")
            or raw.get("journal")
            or raw_inner.get("journal")
            or ""
        )
        entry = {
            "title": record.title,
            "source": record.source,
            "source_id": record.source_id or record.doi,
            "article_url": record.article_url,
            "doi": record.doi if (record.doi or "").startswith("10.") else "",
            "authors": record.authors,
            "year": record.year,
            "publication_title": publication_title,
            "abstract": record.abstract,
            "language": "zh-CN",
            "tier": record.paper_tier,
            "score": record.score,
            "record_id": raw.get("record_id", "") or raw_inner.get("record_id", ""),
            "citekey": raw.get("citekey", "") or raw_inner.get("citekey", "") or _stable_chinese_citekey(record.source, record.year, record.source_id or record.doi),
        }
        exported.append(entry)
    return exported


def main() -> None:
    parser = argparse.ArgumentParser(description="Export 中文论文元数据.json from workflow_search_results.json")
    parser.add_argument("--workflow-inputs", required=True, type=Path, help="Input workflow_search_results.json")
    parser.add_argument("--output", required=True, type=Path, help="Output path for 中文论文元数据.json")
    args = parser.parse_args()

    exported = export_chinese_records(args.workflow_inputs)
    args.output.write_text(json.dumps(exported, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"EXPORTED {len(exported)}")
    print(f"OUTPUT {args.output}")


if __name__ == "__main__":
    main()
