#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0
"""Shared workflow contracts for the More Paper 8-step pipeline.

This module is intentionally lightweight. It defines stable JSON shapes that
connect Step 3/4 search outputs, Step 5 downloads, Step 6 Zotero planning, and
Step 7/8 reporting without changing existing CLI defaults.
"""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "workflow-contracts.v1"
ARTIFACT_PASSPORT_SCHEMA = "artifact-passport.v1"
ROUTE_MODES = (
    "full-workflow",
    "direct-step",
    "plan-only",
    "repair",
    "audit-only",
    "resume",
)


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


PAPER_CARD_EVIDENCE_ROLES = {
    "method",
    "background",
    "theory",
    "review",
    "experiment",
    "data",
    "benchmark",
    "counterpoint",
    "standard_policy",
    "case_specific",
    "unknown",
}

PAPER_CARD_READING_DEPTHS = {
    "metadata_only",
    "abstract_only",
    "full_text",
    "zotero_note",
    "pdf_verified",
}

PAPER_CARD_CONTENT_FITS = {
    "direct",
    "adjacent",
    "background_only",
    "mismatch",
    "unknown",
}


def normalize_choice(value: Any, allowed: set[str], default: str = "unknown") -> str:
    choice = _clean(value).lower().replace("-", "_").replace(" ", "_")
    return choice if choice in allowed else default


def _clean_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean(v) for v in value if _clean(v)]
    if isinstance(value, tuple):
        return [_clean(v) for v in value if _clean(v)]
    text = _clean(value)
    if not text:
        return []
    return [v.strip() for v in re.split(r";|；|\n", text) if v.strip()]


@dataclass
class PaperCard:
    evidence_role: str = "unknown"
    primary_claim: str = ""
    main_methods_or_baselines: list[str] = field(default_factory=list)
    reading_depth: str = "metadata_only"
    content_fit: str = "unknown"
    content_fit_note: str = ""
    usable_for: list[str] = field(default_factory=list)
    not_usable_for: list[str] = field(default_factory=list)

    @classmethod
    def from_value(cls, value: Any) -> "PaperCard":
        if isinstance(value, PaperCard):
            return value
        if not isinstance(value, dict):
            return cls()
        return cls(
            evidence_role=normalize_choice(
                value.get("evidence_role"), PAPER_CARD_EVIDENCE_ROLES
            ),
            primary_claim=_clean(value.get("primary_claim")),
            main_methods_or_baselines=_clean_list(value.get("main_methods_or_baselines")),
            reading_depth=normalize_choice(
                value.get("reading_depth"), PAPER_CARD_READING_DEPTHS, "metadata_only"
            ),
            content_fit=normalize_choice(value.get("content_fit"), PAPER_CARD_CONTENT_FITS),
            content_fit_note=_clean(value.get("content_fit_note")),
            usable_for=_clean_list(value.get("usable_for")),
            not_usable_for=_clean_list(value.get("not_usable_for")),
        )

    def zotero_tags(self, paper_tier: str = "") -> list[str]:
        tags = [
            f"mp-role:{self.evidence_role}",
            f"mp-fit:{self.content_fit}",
            f"mp-depth:{self.reading_depth.replace('_', '-')}",
        ]
        tier = _clean(paper_tier)
        if tier:
            tags.append(f"mp-tier:{tier}")
        return tags

    def zotero_child_note(
        self,
        *,
        record_id: str = "",
        citekey: str = "",
        paper_tier: str = "",
        trust_status: str = "",
        search_task_id: str = "",
        chapter_id: str = "",
        updated_at: str = "",
        source_artifact: str = "workflow_search_results.json",
    ) -> str:
        updated_at = updated_at or datetime.now(timezone.utc).date().isoformat()
        methods = "\n".join(f"- {item}" for item in self.main_methods_or_baselines) or "- "
        usable = "\n".join(f"- {item}" for item in self.usable_for) or "- "
        not_usable = "\n".join(f"- {item}" for item in self.not_usable_for) or "- "
        return "\n".join([
            "# More-Paper Evidence Card",
            "",
            f"record_id: {record_id}",
            f"citekey: {citekey}",
            f"paper_tier: {paper_tier}",
            f"evidence_role: {self.evidence_role}",
            f"reading_depth: {self.reading_depth}",
            f"content_fit: {self.content_fit}",
            f"trust_status: {trust_status}",
            "",
            "## Primary Claim",
            self.primary_claim,
            "",
            "## Main Methods / Baselines",
            methods,
            "",
            "## Usable For",
            usable,
            "",
            "## Not Usable For",
            not_usable,
            "",
            "## Content Fit Note",
            self.content_fit_note,
            "",
            "## Workflow Trace",
            f"source_artifact: {source_artifact}",
            f"search_task_id: {search_task_id}",
            f"chapter_id: {chapter_id}",
            f"updated_at: {updated_at}",
        ])


@dataclass
class SearchTask:
    id: str = ""
    chapter_id: str = ""
    chapter_title: str = ""
    secondary_chapter_ids: list[str] = field(default_factory=list)
    secondary_chapter_titles: list[str] = field(default_factory=list)
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
    secondary_search_task_ids: list[str] = field(default_factory=list)
    secondary_chapter_ids: list[str] = field(default_factory=list)
    secondary_chapter_titles: list[str] = field(default_factory=list)
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
    paper_card: PaperCard = field(default_factory=PaperCard)
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
            secondary_search_task_ids=_clean_list(row.get("secondary_search_task_ids")),
            secondary_chapter_ids=_clean_list(row.get("secondary_chapter_ids")),
            secondary_chapter_titles=_clean_list(row.get("secondary_chapter_titles")),
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
            paper_card=PaperCard.from_value(row.get("paper_card")),
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
    secondary_collection_paths: list[list[str]] = field(default_factory=list)
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


@dataclass
class ArtifactRecord:
    artifact_id: str = ""
    kind: str = ""
    path: str = ""
    source: str = "user_provided"  # user_provided | workflow_generated | agent_rebuilt
    format: str = ""
    step_origin: str = ""
    summary: str = ""
    exists: bool = True
    confidence: str = "medium"
    risk_level: str = "low"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepReadiness:
    step: str = ""
    ready: bool = False
    route_mode: str = "direct-step"
    allowed_modes: list[str] = field(default_factory=list)
    available_artifacts: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    blocked_reason: str = ""
    recommended_next_step: str = ""


@dataclass
class ArtifactPassport:
    schema_version: str = ARTIFACT_PASSPORT_SCHEMA
    project_root: str = ""
    generated_at: str = ""
    route_mode: str = "direct-step"
    current_step: str = ""
    recommended_step: str = ""
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    readiness: list[StepReadiness] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class RetrievalIndexManifest:
    schema_version: str = "retrieval-index.v1"
    generated_at: str = ""
    index_scope: str = ""
    source_artifacts: list[str] = field(default_factory=list)
    search_task_ids: list[str] = field(default_factory=list)
    source_count: int = 0
    record_count: int = 0
    index_levels: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    item_count: int = 0
    chunk_count: int = 0
    reusable_for: list[str] = field(default_factory=list)
    authority: str = "non_evidence"
    staleness: str = "unknown"
    rebuild_triggers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class CapabilityRecord:
    capability_id: str = ""
    source_artifact: str = ""
    status: str = ""  # available | partial | missing | blocked
    supports_steps: list[str] = field(default_factory=list)
    supports_actions: list[str] = field(default_factory=list)
    evidence_boundary: str = ""
    risk_note: str = ""


@dataclass
class CapabilityIndex:
    schema_version: str = "capability-index.v1"
    generated_at: str = ""
    project_root: str = ""
    asset_summary: dict[str, Any] = field(default_factory=dict)
    capabilities: list[CapabilityRecord] = field(default_factory=list)
    recommended_entry_points: list[str] = field(default_factory=list)
    blocking_gaps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_action: str = ""


@dataclass
class RetrievalCandidate:
    chapter_id: str = ""
    chapter_title: str = ""
    claim_id: str = ""
    claim_text: str = ""
    evidence_question_id: str = ""
    query_text: str = ""
    query_variant: str = ""
    step_context: str = ""
    candidate_item_key: str = ""
    candidate_chunk_id: str = ""
    page: str = ""
    source_page_hint: str = ""
    source_type: str = ""
    retrieval_score: str = ""
    match_reason: str = ""
    negative_or_conflicting_evidence: str = ""
    requires_direct_verification: bool = True
    post_verify_status: str = ""


@dataclass
class EvidenceSourceRecord:
    schema_version: str = "evidence-source.v1"
    source_path: str = ""
    source_type: str = ""  # pdf | mineru_zip | bibliography | report | data | draft | standard | image | unknown
    evidence_level: str = "candidate_only"
    claim_scope: str = "background_or_candidate"
    risk_flags: list[str] = field(default_factory=list)
    verification_action: str = "inspect_before_use"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MinerUZipSummary:
    schema_version: str = "mineru-zip.v1"
    zip_path: str = ""
    parent_item_key: str = ""
    attachment_key: str = ""
    source_filename: str = ""
    has_full_md: bool = False
    has_manifest_json: bool = False
    has_content_list_json: bool = False
    image_count: int = 0
    entries: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FigureIndexRecord:
    schema_version: str = "figure-index.v1"
    item_key: str = ""
    figure_id: str = ""
    figure_type: str = ""  # figure | table
    page: str = ""
    caption: str = ""
    mentions_in_text: list[str] = field(default_factory=list)
    source_type: str = ""  # caption_only | caption_plus_text | visual_pending
    collection_path: list[str] = field(default_factory=list)
    paper_tier: str = ""
    source_item_key: str = ""
    source_attachment_key: str = ""
    source_image_path: str = ""
    local_image_path: str = ""
    section_id: str = ""
    claim_binding: str = ""


@dataclass
class FigureEvidenceRecord:
    schema_version: str = "figure-evidence.v1"
    figure_id: str = ""
    item_key: str = ""
    claim_binding: str = ""
    figure_intent: str = ""
    evidence_basis: str = ""
    candidate_specs: list[dict[str, Any]] = field(default_factory=list)
    human_selected_candidate: str = ""
    figure_risk_note: str = ""
    caption_support: str = ""
    text_support: str = ""
    visual_support: str = ""
    evidence_status: str = ""
    recommended_action: str = ""


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


def retrieval_manifest_payload(manifest: RetrievalIndexManifest) -> dict[str, Any]:
    return asdict(manifest)


def capability_index_payload(index: CapabilityIndex) -> dict[str, Any]:
    return asdict(index)


def retrieval_candidates_payload(candidates: list[RetrievalCandidate], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "retrieval-candidates.v1",
        "metadata": metadata or {},
        "candidates": [asdict(c) for c in candidates],
    }


def evidence_pack_payload(records: list[EvidenceSourceRecord], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "evidence-pack.v1",
        "metadata": metadata or {},
        "records": [asdict(r) for r in records],
    }


def write_evidence_pack(path: str | Path, records: list[EvidenceSourceRecord], metadata: dict[str, Any] | None = None) -> None:
    Path(path).write_text(
        json.dumps(evidence_pack_payload(records, metadata), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_retrieval_manifest(path: str | Path, manifest: RetrievalIndexManifest) -> None:
    Path(path).write_text(
        json.dumps(retrieval_manifest_payload(manifest), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_capability_index(path: str | Path, index: CapabilityIndex) -> None:
    Path(path).write_text(
        json.dumps(capability_index_payload(index), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_retrieval_candidates(path: str | Path, candidates: list[RetrievalCandidate], metadata: dict[str, Any] | None = None) -> None:
    Path(path).write_text(
        json.dumps(retrieval_candidates_payload(candidates, metadata), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def figure_index_payload(records: list[FigureIndexRecord], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "figure-index.v1",
        "metadata": metadata or {},
        "records": [asdict(r) for r in records],
    }


def figure_evidence_payload(records: list[FigureEvidenceRecord], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "figure-evidence.v1",
        "metadata": metadata or {},
        "records": [asdict(r) for r in records],
    }


def write_figure_index(path: str | Path, records: list[FigureIndexRecord], metadata: dict[str, Any] | None = None) -> None:
    Path(path).write_text(
        json.dumps(figure_index_payload(records, metadata), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_figure_evidence(path: str | Path, records: list[FigureEvidenceRecord], metadata: dict[str, Any] | None = None) -> None:
    Path(path).write_text(
        json.dumps(figure_evidence_payload(records, metadata), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def inspect_mineru_zip(path: str | Path) -> MinerUZipSummary:
    p = Path(path)
    warnings: list[str] = []
    entries: list[str] = []
    source_meta: dict[str, Any] = {}
    if not p.exists():
        return MinerUZipSummary(zip_path=p.as_posix(), warnings=["zip_missing"])
    try:
        with zipfile.ZipFile(p) as zf:
            entries = zf.namelist()
            if "_llm_source.json" in entries:
                try:
                    source_meta = json.loads(zf.read("_llm_source.json").decode("utf-8"))
                except Exception:
                    warnings.append("invalid_llm_source_json")
    except zipfile.BadZipFile:
        return MinerUZipSummary(zip_path=p.as_posix(), warnings=["bad_zip"])

    has_full_md = "full.md" in entries
    has_manifest = "manifest.json" in entries
    has_content_list = any(name.endswith("content_list.json") or "content_list_v2.json" in name for name in entries)
    image_count = sum(1 for name in entries if name.startswith("images/") and not name.endswith("/"))
    if not has_manifest:
        warnings.append("manifest_missing")
    if not has_full_md:
        warnings.append("full_md_missing")
    if image_count == 0:
        warnings.append("images_missing")
    return MinerUZipSummary(
        zip_path=p.as_posix(),
        parent_item_key=_clean(source_meta.get("parentItemKey")),
        attachment_key=_clean(source_meta.get("attachmentKey")),
        source_filename=_clean(source_meta.get("sourceFilename")),
        has_full_md=has_full_md,
        has_manifest_json=has_manifest,
        has_content_list_json=has_content_list,
        image_count=image_count,
        entries=entries,
        warnings=warnings,
    )


def evidence_source_from_path(path: str | Path, project_root: str | Path = ".") -> EvidenceSourceRecord:
    root = Path(project_root)
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    kind = infer_artifact_kind(p)
    rel_path = _relative_or_string(p, root)
    source_type = {
        "pdf": "pdf",
        "mineru_zip": "mineru_zip",
        "bibliography": "bibliography",
        "draft": "draft",
        "evidence_data": "data",
        "evidence_report": "report",
        "standard_file": "standard",
        "image": "image",
    }.get(kind, "unknown")
    level_by_type = {
        "pdf": "pdf_fulltext_supported",
        "mineru_zip": "pdf_fulltext_supported",
        "bibliography": "metadata_only",
        "draft": "author_provided",
        "data": "author_provided",
        "report": "author_provided",
        "standard": "source_document_supported",
        "image": "visual_candidate",
    }
    risk_flags: list[str] = []
    verification_action = "inspect_before_use"
    claim_scope = "background_or_candidate"
    metadata: dict[str, Any] = {}
    if source_type == "mineru_zip":
        summary = inspect_mineru_zip(p)
        metadata["mineru_zip"] = asdict(summary)
        risk_flags.extend(summary.warnings)
        risk_flags.append("must_verify_against_pdf")
        verification_action = "confirm_against_pdf_or_manifest"
        claim_scope = "figure_or_fulltext_candidate"
    elif source_type == "pdf":
        verification_action = "read_fulltext_or_pages"
        claim_scope = "claim_support_after_page_check"
    elif source_type in {"data", "report", "standard"}:
        verification_action = "confirm_author_or_source_context"
        claim_scope = "strong_claim_if_traceable"
    elif source_type in {"bibliography", "image"}:
        risk_flags.append("candidate_only")

    return EvidenceSourceRecord(
        source_path=rel_path,
        source_type=source_type,
        evidence_level=level_by_type.get(source_type, "candidate_only"),
        claim_scope=claim_scope,
        risk_flags=sorted(set(risk_flags)),
        verification_action=verification_action,
        metadata=metadata,
    )


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _artifact_id(path: str | Path, kind: str) -> str:
    seed = f"{kind}:{Path(path).as_posix()}"
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:12]


def _relative_or_string(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def infer_artifact_kind(path: str | Path) -> str:
    p = Path(path)
    name = p.name.lower()
    suffix = p.suffix.lower()
    text = p.as_posix().lower()

    if p.is_dir():
        if any(part in text for part in ("paper-temp", "pdf", "附件池")):
            return "pdf_pool"
        return "artifact_directory"
    if suffix == ".zip" and ("mineru" in name or "llm-for-zotero-mineru-cache" in name):
        return "mineru_zip"
    if suffix == ".pdf":
        return "pdf"
    if suffix in (".csv", ".xlsx", ".xls", ".tsv"):
        return "evidence_data"
    if suffix in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".svg"):
        return "image"
    if name in ("研究主题.md", "topic.md") or "研究主题" in name:
        return "topic"
    if "大纲关键词" in name or "章节证据需求" in name or name.startswith("目录"):
        return "outline"
    if "检索方案" in name or "search_tasks" in name:
        return "search_plan"
    if "检索文献表" in name or "retrieval_report" in name:
        return "search_table"
    if suffix == ".bib" or "文献库" in name:
        return "bibliography"
    if suffix == ".json" and (
        "workflow" in name
        or "search" in name
        or "检索" in name
        or "results" in name
    ):
        return "workflow_search_results"
    if "download" in name and ("manifest" in name or "下载" in name):
        return "download_manifest"
    if "中文论文元数据" in name or "chinese" in name:
        return "chinese_metadata"
    if "zotero-架构" in name or "zotero_structure" in name:
        return "zotero_structure"
    if "文献-zotero架构对照" in name or "zotero_mapping" in name:
        return "zotero_mapping"
    if "pdf-附件池索引" in name or "pdf_index" in name:
        return "pdf_index"
    if "capability_index" in name or "能力索引" in name:
        return "capability_index"
    if "引用审计" in name or "citation_audit" in name:
        return "citation_audit"
    if "ai_trace_diagnostics" in name:
        return "polishing"
    if any(token in name for token in ("实验报告", "试验报告", "evidence_report", "report")) and suffix in (".md", ".docx", ".txt", ".pdf"):
        return "evidence_report"
    if any(token in name for token in ("标准", "规范", "standard", "spec")) and suffix in (".md", ".docx", ".txt", ".pdf"):
        return "standard_file"
    if "论文初稿" in name or "指定章节" in name or "draft" in name or suffix == ".docx":
        return "draft"
    if "diagnostic_summary" in name or "论文润色稿" in name or "polish" in name:
        return "polishing"
    return "unknown"


def artifact_record_from_path(
    path: str | Path,
    project_root: str | Path = ".",
    source: str = "user_provided",
    kind: str = "",
) -> ArtifactRecord:
    root = Path(project_root)
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    inferred_kind = kind or infer_artifact_kind(p)
    exists = p.exists()
    rel_path = _relative_or_string(p, root)
    fmt = "directory" if p.is_dir() else p.suffix.lstrip(".").lower()
    risk_level = "low" if exists else "medium"
    confidence = "high" if inferred_kind != "unknown" and exists else "medium"
    metadata = {"size_bytes": p.stat().st_size if exists and p.is_file() else 0}
    if exists and inferred_kind == "polishing" and fmt == "json":
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            status_contract = payload.get("status_contract")
            if isinstance(status_contract, dict):
                metadata["status_contract"] = status_contract
            ai_trace = payload.get("ai_trace_diagnostics")
            if isinstance(ai_trace, dict):
                if isinstance(ai_trace.get("status_contract"), dict):
                    metadata["status_contract"] = ai_trace["status_contract"]
                if isinstance(ai_trace.get("step8_decision"), dict):
                    metadata["step8_decision"] = ai_trace["step8_decision"]
        except Exception:
            metadata["status_contract_parse_error"] = True
    return ArtifactRecord(
        artifact_id=_artifact_id(rel_path, inferred_kind),
        kind=inferred_kind,
        path=rel_path,
        source=source,
        format=fmt,
        step_origin=infer_step_origin(inferred_kind),
        summary=f"{inferred_kind}: {rel_path}",
        exists=exists,
        confidence=confidence,
        risk_level=risk_level,
        metadata=metadata,
    )


def infer_step_origin(kind: str) -> str:
    mapping = {
        "topic": "Step 1",
        "outline": "Step 2",
        "search_plan": "Step 3",
        "search_table": "Step 4",
        "bibliography": "Step 4",
        "workflow_search_results": "Step 4",
        "chinese_metadata": "Step 4",
        "download_manifest": "Step 5",
        "pdf": "Step 5",
        "pdf_pool": "Step 5",
        "mineru_zip": "Step 6",
        "zotero_structure": "Step 6",
        "zotero_mapping": "Step 6",
        "pdf_index": "Step 6",
        "capability_index": "Step 6",
        "draft": "Step 7",
        "citation_audit": "Step 7",
        "evidence_data": "Step 7",
        "evidence_report": "Step 7",
        "standard_file": "Step 7",
        "image": "Step 7",
        "polishing": "Step 8",
    }
    return mapping.get(kind, "")


def evaluate_passport_readiness(artifacts: list[ArtifactRecord]) -> list[StepReadiness]:
    existing = [a for a in artifacts if a.exists]
    kinds = {a.kind for a in existing}
    polishing_status_contracts = [
        a.metadata.get("status_contract")
        for a in existing
        if a.kind == "polishing" and isinstance(a.metadata.get("status_contract"), dict)
    ]
    step8_status_contract = polishing_status_contracts[0] if polishing_status_contracts else None

    def ids(*allowed: str) -> list[str]:
        return [a.artifact_id for a in existing if a.kind in allowed]

    readiness: list[StepReadiness] = []

    step4_ready = bool(kinds & {"search_plan", "search_table", "bibliography", "workflow_search_results", "outline"})
    readiness.append(StepReadiness(
        step="Step 4",
        ready=step4_ready,
        route_mode="direct-step" if step4_ready else "plan-only",
        allowed_modes=["execute-search", "repair-search-table", "plan-only"] if step4_ready else ["plan-only"],
        available_artifacts=ids("search_plan", "search_table", "bibliography", "workflow_search_results", "outline"),
        missing_required=[] if step4_ready else ["search_plan 或等价查询/文献表/文献库"],
        missing_optional=["章节证据需求表", "term_aliases.md"] if step4_ready else [],
        risks=[] if "search_plan" in kinds or "workflow_search_results" in kinds else ["缺少正式 search_tasks 时，Step 4 需先重建最小检索依据"],
        blocked_reason="" if step4_ready else "没有可执行检索或等价文献输入",
        recommended_next_step="生成或修复检索结果",
    ))

    step5_ready = bool(kinds & {"bibliography", "search_table", "workflow_search_results", "download_manifest", "chinese_metadata"})
    readiness.append(StepReadiness(
        step="Step 5",
        ready=step5_ready,
        route_mode="direct-step" if step5_ready else "plan-only",
        allowed_modes=["manifest-from-any-input", "dry-run", "download"] if step5_ready else ["plan-only"],
        available_artifacts=ids("bibliography", "search_table", "workflow_search_results", "download_manifest", "chinese_metadata"),
        missing_required=[] if step5_ready else ["DOI 列表、中文 article_url、publisher URL、BibTeX 或 workflow JSON"],
        missing_optional=["下载优先级", "登录态说明"] if step5_ready else [],
        risks=["真实下载可能触发登录或版权访问边界，先 dry-run"] if step5_ready else [],
        blocked_reason="" if step5_ready else "没有可归一为 DownloadManifestItem 的输入",
        recommended_next_step="先生成下载 manifest，再决定 dry-run 或真实下载",
    ))

    step6_ready = bool(kinds & {"bibliography", "workflow_search_results", "zotero_mapping", "zotero_structure", "pdf_pool", "pdf", "pdf_index", "capability_index"})
    step6_modes: list[str] = []
    if kinds & {"bibliography", "workflow_search_results", "pdf_pool", "pdf"}:
        step6_modes.append("plan-from-bib")
    if kinds & {"zotero_mapping", "zotero_structure", "pdf_index", "capability_index"}:
        step6_modes.append("plan-from-zotero")
        step6_modes.append("consistency-adjustment")
    if not step6_modes and step6_ready:
        step6_modes.append("plan-only")
    readiness.append(StepReadiness(
        step="Step 6",
        ready=step6_ready,
        route_mode="plan-only",
        allowed_modes=step6_modes or ["plan-only"],
        available_artifacts=ids("bibliography", "workflow_search_results", "zotero_mapping", "zotero_structure", "pdf_pool", "pdf", "pdf_index", "capability_index"),
        missing_required=[] if step6_ready else ["文献库.bib、workflow JSON、PDF 池或 Zotero 现有映射"],
        missing_optional=["Zotero mode: local/cloud/skip", "collection/tag 策略"] if step6_ready else [],
        risks=["CP-ZOTERO-WRITE 只阻塞真实写入，不阻塞 plan-only/只读/dry-run"] if step6_ready else [],
        blocked_reason="" if step6_ready else "没有可规划 Zotero 的文献或文库材料",
        recommended_next_step="先确认 local/cloud/skip，再生成 plan-only",
    ))

    local_evidence_kinds = {"pdf", "pdf_pool", "mineru_zip", "evidence_data", "evidence_report", "standard_file", "image"}
    step7_ready = bool(kinds & {"zotero_mapping", "bibliography", "pdf_index", "draft", "workflow_search_results", "citation_audit", "capability_index"} | local_evidence_kinds)
    step7_modes: list[str] = []
    if "draft" in kinds:
        step7_modes.extend(["continue-existing", "chapter-only"])
    if kinds & local_evidence_kinds:
        step7_modes.append("evidence_pack")
    if "draft" in kinds and not (kinds - {"draft"}):
        step7_modes.append("draft_only")
    if (kinds & local_evidence_kinds) and (kinds & {"zotero_mapping", "bibliography", "pdf_index", "workflow_search_results", "capability_index", "draft"}):
        step7_modes.append("mixed")
    if kinds & {"zotero_mapping", "bibliography", "pdf_index", "workflow_search_results", "capability_index"}:
        step7_modes.extend(["draft", "review-only", "pre-review", "zotero_full"])
    if "mineru_zip" in kinds and kinds & {"zotero_mapping", "pdf_index", "capability_index"}:
        step7_modes.append("zotero_mineru")
    if "citation_audit" in kinds:
        step7_modes.append("citation-audit")
    readiness.append(StepReadiness(
        step="Step 7",
        ready=step7_ready,
        route_mode="direct-step" if step7_ready else "plan-only",
        allowed_modes=sorted(set(step7_modes)) or ["plan-only"],
        available_artifacts=ids("zotero_mapping", "bibliography", "pdf_index", "draft", "workflow_search_results", "citation_audit", "capability_index", "pdf", "pdf_pool", "mineru_zip", "evidence_data", "evidence_report", "standard_file", "image"),
        missing_required=[] if step7_ready else ["Zotero 对照、文献库、PDF 索引、workflow JSON、证据包或初稿"],
        missing_optional=["引用审计", "style_profile", "section_blueprints", "evidence_pack.json"] if step7_ready else [],
        risks=["缺证据矩阵时只能生成风险标记或最小映射，不声明引用安全通过；本地证据包需先标注 evidence_level"] if step7_ready else [],
        blocked_reason="" if step7_ready else "没有可支撑写作、续写或审计的材料",
        recommended_next_step="按可用证据选择写作、续写、综述或引用审计模式",
    ))

    step8_ready = "draft" in kinds or "polishing" in kinds
    step8_blocked_by_status = bool(
        isinstance(step8_status_contract, dict) and step8_status_contract.get("readiness") == "blocked"
    )
    step8_can_continue = not (
        isinstance(step8_status_contract, dict) and step8_status_contract.get("can_continue") is False
    )
    step8_recommended = "按文本范围选择局部润色、章节修订或全稿精修"
    step8_risks = ["Step 8 不替代 Step 7 引用审计；缺审计时只能标记风险"] if step8_ready else []
    step8_blocked_reason = "" if step8_ready else "没有可润色的正文材料"
    if isinstance(step8_status_contract, dict):
        contract_warnings = step8_status_contract.get("warnings") or []
        if isinstance(contract_warnings, list):
            step8_risks.extend(str(item) for item in contract_warnings if str(item) not in step8_risks)
        recommended = step8_status_contract.get("recommended_next_step")
        if isinstance(recommended, str) and recommended:
            step8_recommended = recommended
        if step8_blocked_by_status:
            blocking = step8_status_contract.get("blocking") or []
            if isinstance(blocking, list) and blocking:
                step8_blocked_reason = "；".join(str(item) for item in blocking)
            else:
                step8_blocked_reason = "Step 8 运行态状态块标记为 blocked"
    readiness.append(StepReadiness(
        step="Step 8",
        ready=step8_ready and not step8_blocked_by_status and step8_can_continue,
        route_mode="audit-only" if "citation_audit" in kinds and "draft" not in kinds else "direct-step",
        allowed_modes=["local-polish", "section-revision", "full-manuscript-pass"] if step8_ready else ["risk-note-only"],
        available_artifacts=ids("draft", "polishing", "citation_audit"),
        missing_required=[] if step8_ready else ["论文初稿、指定章节或待润色文本"],
        missing_optional=["引用审计报告", "term_aliases.md"] if step8_ready else [],
        risks=step8_risks,
        blocked_reason=step8_blocked_reason,
        recommended_next_step=step8_recommended,
    ))
    return readiness


def infer_passport_route_mode(artifacts: list[ArtifactRecord], readiness: list[StepReadiness]) -> str:
    existing = [a for a in artifacts if a.exists]
    if not existing:
        return "full-workflow"
    kinds = {a.kind for a in existing}
    if "citation_audit" in kinds and not (kinds & {"draft", "bibliography", "zotero_mapping"}):
        return "audit-only"
    if kinds & {"polishing", "download_manifest", "zotero_mapping"}:
        return "resume"
    if kinds <= {"topic", "outline", "search_plan"}:
        return "plan-only"
    if any(a.risk_level in ("medium", "high") for a in existing if a.kind == "unknown"):
        return "repair"
    return "direct-step"


def recommend_passport_step(artifacts: list[ArtifactRecord], readiness: list[StepReadiness]) -> str:
    kinds = {a.kind for a in artifacts if a.exists}
    ready_by_step = {r.step: r for r in readiness if r.ready}
    if kinds & {"draft", "polishing"} and "Step 8" in ready_by_step:
        return "Step 8"
    if kinds & {"zotero_mapping", "pdf_index", "citation_audit", "capability_index", "mineru_zip", "evidence_data", "evidence_report", "standard_file"} and "Step 7" in ready_by_step:
        return "Step 7"
    if kinds & {"bibliography", "pdf_pool", "pdf", "zotero_structure"} and "Step 6" in ready_by_step:
        return "Step 6"
    if kinds & {"workflow_search_results", "search_table", "chinese_metadata", "download_manifest"} and "Step 5" in ready_by_step:
        return "Step 5"
    if kinds & {"search_plan", "outline"} and "Step 4" in ready_by_step:
        return "Step 4"
    return "Step 1"


def build_artifact_passport(
    project_root: str | Path,
    artifact_paths: list[str | Path] | None = None,
    source: str = "user_provided",
) -> ArtifactPassport:
    root = Path(project_root)
    artifacts = [
        artifact_record_from_path(path, root, source=source)
        for path in (artifact_paths or [])
    ]
    readiness = evaluate_passport_readiness(artifacts)
    route_mode = infer_passport_route_mode(artifacts, readiness)
    return ArtifactPassport(
        project_root=root.as_posix(),
        generated_at=_now_iso(),
        route_mode=route_mode,
        recommended_step=recommend_passport_step(artifacts, readiness),
        artifacts=artifacts,
        readiness=readiness,
        notes=["Passport 只保存材料指针、缺口和风险，不保存正文内容。"],
    )


def artifact_passport_payload(passport: ArtifactPassport) -> dict[str, Any]:
    payload = asdict(passport)
    payload["schema_version"] = ARTIFACT_PASSPORT_SCHEMA
    return payload


def write_artifact_passport(path: str | Path, passport: ArtifactPassport) -> None:
    Path(path).write_text(
        json.dumps(artifact_passport_payload(passport), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_artifact_passport(path: str | Path) -> ArtifactPassport:
    data = load_json(path)
    artifacts = [ArtifactRecord(**row) for row in data.get("artifacts", []) if isinstance(row, dict)]
    readiness = [StepReadiness(**row) for row in data.get("readiness", []) if isinstance(row, dict)]
    return ArtifactPassport(
        schema_version=data.get("schema_version", ARTIFACT_PASSPORT_SCHEMA),
        project_root=data.get("project_root", ""),
        generated_at=data.get("generated_at", ""),
        route_mode=data.get("route_mode", "direct-step"),
        current_step=data.get("current_step", ""),
        recommended_step=data.get("recommended_step", ""),
        artifacts=artifacts,
        readiness=readiness,
        notes=list(data.get("notes", [])),
    )


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
