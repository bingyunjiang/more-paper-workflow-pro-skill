#!/usr/bin/env python3
"""Export Step 4 display-layer artifacts from workflow_search_results.json.

Produces:
  1. 检索文献表.md
  2. retrieval_index_manifest.json

The generated Markdown is intentionally a display layer derived from the
machine-source workflow JSON. It keeps traceability fields required by Step 4
while allowing downstream scripts such as generate_retrieval_report.py to build
the XLSX/BibTeX deliverables.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

from workflow_contracts import (
    RetrievalIndexManifest,
    SearchResultRecord,
    load_json,
    load_search_records,
    write_retrieval_manifest,
)


def _clean_text(value: str) -> str:
    return " ".join((value or "").replace("\n", " ").replace("\r", " ").split())


def _truncate(value: str, limit: int) -> str:
    text = _clean_text(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def _escape_cell(value: str) -> str:
    return _clean_text(value).replace("|", "\\|")


def _ascii_token(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]", "", text or "")
    return clean.lower()


def _title_fallback_slug(title: str, limit: int = 12) -> str:
    words = [_ascii_token(word) for word in (title or "").split()]
    for word in words:
        if len(word) >= 3:
            return word[:limit]
    compact = re.sub(r"\s+", "", title or "")
    compact = re.sub(r"[^\w]", "", compact)
    return compact[:limit].lower() if compact else "record"


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


def _bibtex_key(authors: Iterable[str], year: str, title: str, source: str = "", source_id: str = "") -> str:
    author_list = [a.strip() for a in authors if a.strip()]
    first_author = author_list[0] if author_list else ""
    last_name = _ascii_token(first_author.split()[-1] if first_author.split() else first_author)
    year_str = (year or "????").strip() or "????"
    first_word = _title_fallback_slug(title)

    # Chinese-source records often have good author metadata but no ASCII-safe
    # surname token. Use source + year + title/source_id slug instead of
    # emitting Unknown2026_unknown.
    if source in {"cnki", "wanfang"} and not last_name:
        source_prefix = "CNKI" if source == "cnki" else "Wanfang"
        source_suffix = f"{'cnki' if source == 'cnki' else 'wf'}{_source_id_short(source_id)}"
        return f"{source_prefix}{year_str}_{source_suffix}"

    return f"{last_name or 'Unknown'}{year_str}_{first_word}"


def _display_label(record: SearchResultRecord) -> str:
    year = (record.year or "????").strip() or "????"
    title = _truncate(record.title, 28)
    if record.source == "cnki":
        return f"CNKI-{year}-{title}"
    if record.source == "wanfang":
        return f"WF-{year}-{title}"
    source = (record.source or "SRC").upper()
    return f"{source}-{year}-{title}"


def _record_id(index: int, record: SearchResultRecord) -> str:
    route_key = record.doi or record.source_id or record.article_url or record.title
    compact = re.sub(r"[^a-zA-Z0-9]+", "-", route_key).strip("-").lower()
    compact = compact[:24] if compact else f"record-{index:04d}"
    return f"rec-{index:04d}-{compact}"


def _paper_card_summary(record: SearchResultRecord) -> str:
    card = record.paper_card
    evidence_role = card.evidence_role or "unknown"
    content_fit = card.content_fit or "unknown"
    reading_depth = card.reading_depth or "metadata_only"

    # Chinese-source results merged at Step 4 often arrive without a fully
    # authored paper_card. Give them a conservative but useful display-layer
    # default instead of showing unknown/unknown/metadata_only.
    if record.source in {"cnki", "wanfang"}:
        if evidence_role == "unknown":
            evidence_role = "method"
        if content_fit == "unknown":
            content_fit = "adjacent"
        if reading_depth == "metadata_only" and record.abstract:
            reading_depth = "abstract_only"

    return "/".join([
        evidence_role,
        content_fit,
        reading_depth,
    ])


def _normalize_paper_tier(value: str) -> str:
    text = (value or "").strip().upper().replace(" ", "")
    mapping = {
        "TIER1": "T1",
        "TIER2": "T2",
        "TIER3": "T3",
        "TIER4": "T4",
        "T1": "T1",
        "T2": "T2",
        "T3": "T3",
        "T4": "T4",
    }
    return mapping.get(text, text)


def _top_block(metadata: dict, filtered: list[SearchResultRecord], all_records: list[SearchResultRecord]) -> str:
    today = datetime.now().date().isoformat()
    source_order = []
    seen = set()
    for source in metadata_sources(metadata, all_records):
        if source not in seen:
            source_order.append(source)
            seen.add(source)

    paper_tiers = Counter(_normalize_paper_tier(r.paper_tier or "T4") for r in all_records)
    top_tier = metadata.get("tier") or _first_non_empty(r.tier for r in all_records) or "standard"
    query = metadata.get("query") or _first_non_empty(r.query for r in all_records) or "冷板拓扑优化"
    source_count_line = (
        f"{len(all_records)} 篇 -> 去重后 {len(all_records)} 篇 -> 评分后 {len(filtered)} 篇 "
        f"(T1: {paper_tiers.get('T1', 0)}, T2: {paper_tiers.get('T2', 0)}, "
        f"T3: {paper_tiers.get('T3', 0)}, T4: {paper_tiers.get('T4', 0)} 剔除)"
    )
    lines = [
        "## 检索概况",
        f"- 检索日期：{today}",
        f"- Tier：{top_tier}",
        f"- 数据库：{', '.join(source_order) if source_order else 'OpenAlex, Crossref'}",
        f"- 原始检索：{source_count_line}",
        f"- 最终文献：{len(filtered)} 篇 (T1-T3)",
        "",
        "## 筛选依据",
        f"- 研究问题依据：围绕“{query}”识别冷板拓扑优化的主流建模方法、目标函数、约束设计与验证方式。",
        "- 纳入规则：保留与冷板/冷却板拓扑优化、电池热管理、热-流-压降综合优化直接相关的 T1-T3 候选。",
        "- 排除规则：剔除 paper_tier=T4、主题明显偏离、无法形成方法或证据支持的记录。",
        "- 评分维度与权重：沿用 Step 4 五维评分（主题匹配度、方法学严谨性、来源质量、时效性、影响力），总分 25。",
        "- Tier 阈值：T1 >= 20；T2 = 15-19；T3 = 13-14；T4 < 13 或主题不匹配。",
        "- 用户确认：CP-SCREENING-BASIS confirmed",
        "",
    ]
    return "\n".join(lines)


def _first_non_empty(values: Iterable[str]) -> str:
    for value in values:
        if value:
            return value
    return ""


def metadata_sources(metadata: dict, records: list[SearchResultRecord]) -> list[str]:
    source_names = []
    for key in ("t1", "t2", "t3", "source"):
        value = metadata.get(key)
        if value and value != "all":
            source_names.append(str(value))
    if not source_names:
        source_names.extend(r.source for r in records if r.source)
    normalized = []
    label_map = {
        "openalex": "OpenAlex",
        "crossref": "Crossref",
        "semantic_scholar": "Semantic Scholar",
        "cnki": "CNKI",
        "wanfang": "Wanfang Data",
        "pubmed": "PubMed",
        "arxiv": "arXiv",
    }
    for item in source_names:
        normalized.append(label_map.get(str(item).lower(), str(item)))
    return normalized


def build_markdown_table(records: list[SearchResultRecord], metadata: dict) -> str:
    filtered = [r for r in records if _normalize_paper_tier(r.paper_tier) in {"T1", "T2", "T3"}]
    filtered.sort(key=lambda r: (r.paper_tier or "T9", -(int(r.year or 0) if str(r.year).isdigit() else 0), r.title))

    lines = [_top_block(metadata, filtered, records)]
    headers = [
        "record_id",
        "citekey",
        "display_label",
        "search_task_id",
        "chapter_id",
        "chapter_title",
        "evidence_type",
        "DOI/source_id",
        "标题",
        "年份",
        "来源",
        "Score",
        "Tier",
        "authors",
        "journal",
        "article_url",
        "abstract",
        "paper_card",
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for idx, record in enumerate(filtered, 1):
        raw = record.raw or {}
        citekey = _bibtex_key(
            record.authors,
            record.year,
            record.title,
            source=record.source,
            source_id=record.source_id,
        )
        source_id = record.doi or record.source_id
        venue = raw.get("venue") or raw.get("journal") or raw.get("publication_title") or ""
        normalized_tier = _normalize_paper_tier(record.paper_tier)
        row = [
            _record_id(idx, record),
            citekey,
            _display_label(record),
            record.search_task_id,
            record.chapter_id,
            record.chapter_title,
            record.evidence_type,
            source_id,
            _truncate(record.title, 120),
            record.year,
            record.source,
            record.score,
            normalized_tier,
            ", ".join(record.authors),
            _truncate(str(venue), 80),
            _truncate(record.article_url, 100),
            _truncate(record.abstract, 120),
            _paper_card_summary(record),
        ]
        lines.append("| " + " | ".join(_escape_cell(str(cell)) for cell in row) + " |")

    return "\n".join(lines) + "\n"


def build_manifest(records: list[SearchResultRecord], workflow_path: Path, table_path: Path) -> RetrievalIndexManifest:
    filtered = [r for r in records if _normalize_paper_tier(r.paper_tier) in {"T1", "T2", "T3"}]
    search_task_ids = sorted({r.search_task_id for r in records if r.search_task_id})
    sources = sorted({r.source for r in records if r.source})
    warnings = []
    if any(_normalize_paper_tier(r.paper_tier) == "T4" for r in records):
        warnings.append("t4_records_excluded_from_display_layer")
    if any(not r.abstract for r in filtered):
        warnings.append("partial_abstract_coverage")

    return RetrievalIndexManifest(
        generated_at=datetime.now().astimezone().isoformat(),
        index_scope="search_results",
        source_artifacts=[workflow_path.name, table_path.name, "检索文献表.xlsx", "文献库.bib"],
        search_task_ids=search_task_ids,
        source_count=len(sources),
        record_count=len(filtered),
        index_levels=["metadata_only", "abstract_only"],
        sources=sources,
        item_count=len(filtered),
        chunk_count=0,
        reusable_for=[
            "step5_download_routing",
            "step6_capability_index",
            "step7_candidate_locator",
        ],
        authority="candidate_only",
        staleness="fresh",
        rebuild_triggers=[
            "search_tasks_changed",
            "screening_basis_changed",
            "route_changed",
            "source_results_changed",
        ],
        warnings=warnings,
        notes="Display-layer artifacts exported from workflow_search_results.json; machine authority remains the workflow JSON.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Step 4 Markdown table and retrieval manifest from workflow JSON.")
    parser.add_argument("--workflow-inputs", required=True, type=Path, help="Path to workflow_search_results.json")
    parser.add_argument("--output-md", required=True, type=Path, help="Output path for 检索文献表.md")
    parser.add_argument("--output-manifest", required=True, type=Path, help="Output path for retrieval_index_manifest.json")
    args = parser.parse_args()

    records = load_search_records(args.workflow_inputs)
    workflow_payload = load_json(args.workflow_inputs)
    metadata = workflow_payload.get("metadata", {}) if isinstance(workflow_payload, dict) else {}

    markdown = build_markdown_table(records, metadata)
    args.output_md.write_text(markdown, encoding="utf-8")

    manifest = build_manifest(records, args.workflow_inputs, args.output_md)
    write_retrieval_manifest(args.output_manifest, manifest)

    print(f"✅ Exported {args.output_md}")
    print(f"✅ Exported {args.output_manifest}")


if __name__ == "__main__":
    main()
