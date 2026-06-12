#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0
"""Shared workflow contracts for the More Paper 8-step pipeline.

This module is intentionally lightweight. It defines stable JSON shapes that
connect Step 3/4 search outputs, Step 5 downloads, Step 6 Zotero planning, and
Step 7/8 reporting without changing existing CLI defaults.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "workflow-contracts.v1"


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_doi(value: Any) -> str:
    doi = _clean(value)
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip().rstrip(".")


def normalize_source(value: Any) -> str:
    source = _clean(value).lower()
    aliases = {
        "semantic": "semantic_scholar",
        "semanticscholar": "semantic_scholar",
        "wf": "wanfang",
        "cn": "cnki",
    }
    return aliases.get(source, source)


def stable_source_id(source: str, title: str, article_url: str = "") -> str:
    source = normalize_source(source) or "unknown"
    seed = article_url or title
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()[:12]
    return f"{source}.{digest}"


@dataclass
class SearchTask:
    id: str = ""
    chapter_id: str = ""
    chapter_title: str = ""
    evidence_type: str = ""
    question_to_answer: str = ""
    tier: str = ""
    route: dict[str, Any] = field(default_factory=dict)
    query_blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SearchResultRecord:
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: str = ""
    source: str = ""
    doi: str = ""
    source_id: str = ""
    article_url: str = ""
    search_task_id: str = ""
    chapter_id: str = ""
    chapter_title: str = ""
    evidence_type: str = ""
    query: str = ""
    verification_status: str = ""
    verification_confidence: str = ""
    warn_class: str = ""
    verified_sources: str = ""
    score: str = ""
    paper_tier: str = ""
    tier: str = ""
    evidence: str = ""
    download_hint: str = ""
    abstract: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_search_result(cls, row: dict[str, Any]) -> "SearchResultRecord":
        source = normalize_source(row.get("source"))
        doi = normalize_doi(row.get("doi") or row.get("DOI"))
        article_url = _clean(
            row.get("article_url")
            or row.get("url")
            or row.get("文章链接")
            or row.get("URL")
        )
        title = _clean(row.get("title") or row.get("标题"))
        source_id = _clean(row.get("source_id") or row.get("source id"))
        if not source_id and source in ("cnki", "wanfang") and title:
            source_id = stable_source_id(source, title, article_url)
        authors = row.get("authors") or row.get("作者") or []
        if isinstance(authors, str):
            authors = [a.strip() for a in re.split(r";|；|,|，|\band\b", authors) if a.strip()]
        paper_tier = _clean(row.get("paper_tier") or row.get("_tier") or row.get("Tier") or row.get("tier"))
        score = _clean(row.get("score") or row.get("_score") or row.get("评分"))
        return cls(
            title=title,
            authors=list(authors) if isinstance(authors, list) else [],
            year=_clean(row.get("year") or row.get("年份")),
            source=source,
            doi=doi,
            source_id=source_id,
            article_url=article_url,
            search_task_id=_clean(row.get("search_task_id") or row.get("_sub_query")),
            chapter_id=_clean(row.get("chapter_id")),
            chapter_title=_clean(row.get("chapter_title")),
            evidence_type=_clean(row.get("evidence_type")),
            query=_clean(row.get("query") or row.get("_query")),
            verification_status=_clean(row.get("verification_status")),
            verification_confidence=_clean(row.get("verification_confidence")),
            warn_class=_clean(row.get("warn_class")),
            verified_sources=_clean(row.get("verified_sources") or source),
            score=score,
            paper_tier=paper_tier,
            tier=_clean(row.get("search_tier") or row.get("tier")),
            evidence=_clean(row.get("evidence") or row.get("match_reason")),
            download_hint=infer_download_hint(doi, source, article_url),
            abstract=_clean(row.get("abstract") or row.get("摘要")),
            raw=dict(row),
        )

    @classmethod
    def from_markdown_row(cls, row: dict[str, Any]) -> "SearchResultRecord":
        return cls.from_search_result(row)


@dataclass
class DownloadManifestItem:
    item_id: str = ""
    title: str = ""
    doi: str = ""
    source: str = ""
    source_id: str = ""
    article_url: str = ""
    publisher: str = ""
    route_key: str = ""
    status: str = "ready"
    confidence: str = ""
    search_task_id: str = ""
    chapter_id: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_search_record(cls, record: SearchResultRecord, index: int = 1) -> "DownloadManifestItem":
        route_key = record.doi or record.source_id or stable_source_id(record.source, record.title, record.article_url)
        return cls(
            item_id=f"wf-{index:04d}",
            title=record.title,
            doi=record.doi,
            source=record.source,
            source_id=record.source_id,
            article_url=record.article_url,
            route_key=route_key,
            status="ready" if (record.doi or record.article_url) else "needs_user_confirm",
            confidence="high" if (record.doi or record.article_url) else "low",
            search_task_id=record.search_task_id,
            chapter_id=record.chapter_id,
            raw=record.raw,
        )


@dataclass
class DownloadResult:
    item_id: str = ""
    route_key: str = ""
    provider: str = ""
    status: str = ""
    file_path: str = ""
    failure_reason: str = ""
    attempts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ZoteroPlanRecord:
    record_id: str = ""
    citekey: str = ""
    title: str = ""
    source: str = ""
    source_id: str = ""
    doi: str = ""
    article_url: str = ""
    collection_path: list[str] = field(default_factory=list)
    import_method: str = ""
    import_status: str = ""
    attachment_status: str = ""


@dataclass
class ReportInputs:
    search_results: list[SearchResultRecord] = field(default_factory=list)
    download_results: list[DownloadResult] = field(default_factory=list)
    zotero_plan: list[ZoteroPlanRecord] = field(default_factory=list)
    curation_summary: dict[str, Any] = field(default_factory=dict)
    writing_blueprint: dict[str, Any] = field(default_factory=dict)


def infer_download_hint(doi: str, source: str, article_url: str) -> str:
    if source in ("cnki", "wanfang"):
        return "chinese_article_url" if article_url else "missing_article_url"
    if doi:
        return "doi"
    if article_url:
        return "publisher_url"
    return "unresolved"


def workflow_payload(records: list[SearchResultRecord], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "search_results",
        "metadata": metadata or {},
        "records": [asdict(r) for r in records],
    }


def write_workflow_json(path: str | Path, records: list[SearchResultRecord], metadata: dict[str, Any] | None = None) -> None:
    Path(path).write_text(
        json.dumps(workflow_payload(records, metadata), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_search_records(path: str | Path) -> list[SearchResultRecord]:
    data = load_json(path)
    if isinstance(data, dict):
        rows = data.get("records") or data.get("search_results") or data.get("papers") or []
    elif isinstance(data, list):
        rows = data
    else:
        rows = []
    return [SearchResultRecord.from_search_result(r) for r in rows if isinstance(r, dict)]


def load_download_manifest(path: str | Path) -> list[DownloadManifestItem]:
    data = load_json(path)
    if isinstance(data, dict):
        rows = data.get("items") or data.get("records") or data.get("papers") or []
    elif isinstance(data, list):
        rows = data
    else:
        rows = []
    items: list[DownloadManifestItem] = []
    for idx, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            continue
        if "route_key" in row or "item_id" in row:
            item = DownloadManifestItem(
                item_id=_clean(row.get("item_id") or f"dd-{idx:04d}"),
                title=_clean(row.get("title")),
                doi=normalize_doi(row.get("doi")),
                source=normalize_source(row.get("source")),
                source_id=_clean(row.get("source_id")),
                article_url=_clean(row.get("article_url") or row.get("url")),
                publisher=_clean(row.get("publisher")),
                route_key=_clean(row.get("route_key") or row.get("doi") or row.get("source_id")),
                status=_clean(row.get("status") or "ready"),
                confidence=_clean(row.get("confidence")),
                search_task_id=_clean(row.get("search_task_id")),
                chapter_id=_clean(row.get("chapter_id")),
                raw=dict(row),
            )
        else:
            item = DownloadManifestItem.from_search_record(SearchResultRecord.from_search_result(row), idx)
        if not item.route_key:
            item.route_key = item.doi or item.source_id or stable_source_id(item.source, item.title, item.article_url)
        items.append(item)
    return items


def download_items_from_search_records(records: list[SearchResultRecord]) -> list[DownloadManifestItem]:
    return [DownloadManifestItem.from_search_record(record, idx) for idx, record in enumerate(records, 1)]


def as_chinese_papers(items: list[DownloadManifestItem]) -> list[dict[str, str]]:
    papers: list[dict[str, str]] = []
    for item in items:
        if normalize_source(item.source) not in ("cnki", "wanfang"):
            continue
        if not item.article_url:
            continue
        papers.append({
            "title": item.title,
            "source": normalize_source(item.source),
            "article_url": item.article_url,
            "doi": item.doi or item.source_id or item.route_key,
        })
    return papers


def dois_from_download_items(items: list[DownloadManifestItem]) -> list[str]:
    dois: list[str] = []
    for item in items:
        if item.doi and normalize_source(item.source) not in ("cnki", "wanfang"):
            dois.append(item.doi)
    return dois
