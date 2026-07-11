#!/usr/bin/env python3
"""Reconcile a Step 2 outline baseline against formal Step 4 search results."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]{2,}|[\u4e00-\u9fff]{2,}")
STOPWORDS = {
    "study", "research", "analysis", "method", "model", "based", "using", "effect",
    "研究", "分析", "方法", "模型", "基于", "应用", "影响", "系统", "一种",
}
VERIFIED_STATUSES = {"VERIFIED", "VERIFIED_LOCAL"}
STRONG_TIERS = {"T1", "T2", "TIER1", "TIER2"}


def _normalized_tier(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _records(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("records", "results", "papers"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _terms(text: str) -> list[str]:
    return [term.lower() for term in WORD_RE.findall(text or "") if term.lower() not in STOPWORDS]


def _section_records(section: dict, records: list[dict]) -> list[dict]:
    section_id = str(section.get("section_id") or "")
    rq_ids = {str(item) for item in section.get("rq_ids") or []}
    matched = []
    for record in records:
        chapter = str(record.get("chapter_id") or record.get("section_id") or "")
        rq_id = str(record.get("rq_id") or "")
        if chapter == section_id or (rq_id and rq_id in rq_ids):
            matched.append(record)
    return matched


def reconcile(outline: dict, results: object, *, outline_hash: str = "", results_hash: str = "") -> dict:
    sections = outline.get("sections") if isinstance(outline, dict) else []
    sections = sections if isinstance(sections, list) else []
    records = _records(results)
    section_reports = []
    covered = 0
    high_impact = []

    for section in sections:
        if not isinstance(section, dict):
            continue
        matched = _section_records(section, records)
        verified = [r for r in matched if str(r.get("verification_status") or "").upper() in VERIFIED_STATUSES]
        warnings = [r for r in matched if str(r.get("verification_status") or "").upper() == "WARN"]
        strong = [r for r in verified if _normalized_tier(r.get("paper_tier") or r.get("tier")) in STRONG_TIERS]
        corpus = " ".join(f"{r.get('title', '')} {r.get('abstract', '')}" for r in verified)
        frequencies = Counter(_terms(corpus))
        current_terms = []
        for value in section.get("keywords") or []:
            current_terms.extend(_terms(str(value)))
        observed = {term: frequencies.get(term, 0) for term in dict.fromkeys(current_terms)}
        suggested = [term for term, count in frequencies.most_common(12) if count >= 2 and term not in observed][:6]
        status = "covered" if strong else "weak" if verified else "uncovered"
        if status == "covered":
            covered += 1
        if status == "uncovered" and section.get("key_claims"):
            high_impact.append({
                "section_id": section.get("section_id"),
                "finding": "core section has no mapped retained evidence",
                "proposed_action": "review scope, query, or section responsibility",
            })
        section_reports.append({
            "section_id": section.get("section_id"),
            "section_title": section.get("section_title"),
            "coverage_status": status,
            "mapped_record_count": len(verified),
            "t1_t2_count": len(strong),
            "warn_count": len(warnings),
            "keyword_observations": observed,
            "suggested_corpus_terms": suggested,
            "evidence_gap": "" if status == "covered" else "formal search did not establish strong coverage",
        })

    total = len(section_reports)
    reconciliation_status = "evidence_validated" if total and covered == total else "requires_revision"
    calibrated_outline = json.loads(json.dumps(outline, ensure_ascii=False))
    calibrated_outline["outline_state"] = (
        "evidence_validated" if reconciliation_status == "evidence_validated" else "search_calibrated"
    )
    report_by_id = {str(item.get("section_id")): item for item in section_reports}
    for section in calibrated_outline.get("sections", []):
        if not isinstance(section, dict):
            continue
        report = report_by_id.get(str(section.get("section_id")))
        if not report:
            continue
        section["step4_evidence_status"] = report["coverage_status"]
        section["step4_mapped_record_count"] = report["mapped_record_count"]
        section["step4_t1_t2_count"] = report["t1_t2_count"]
        section["step4_suggested_corpus_terms"] = report["suggested_corpus_terms"]
        if report["evidence_gap"]:
            risks = section.get("risk_flags") if isinstance(section.get("risk_flags"), list) else []
            if "formal_search_evidence_gap" not in risks:
                risks.append("formal_search_evidence_gap")
            section["risk_flags"] = risks
    return {
        "schema_version": "step2-search-reconciliation.v1",
        "outline_lifecycle": {
            "input_state": str(outline.get("outline_state") or "outline_baseline"),
            "output_state": reconciliation_status,
        },
        "source_hashes": {"outline_sha256": outline_hash, "search_results_sha256": results_hash},
        "summary": {
            "section_count": total,
            "covered_section_count": covered,
            "reconciliation_status": reconciliation_status,
            "requires_user_confirmation": bool(high_impact),
        },
        "sections": section_reports,
        "calibrated_outline": calibrated_outline,
        "high_impact_proposals": high_impact,
        "automatic_change_boundary": {
            "allowed": ["keyword qualification", "synonym expansion", "evidence status", "evidence gap"],
            "requires_user_confirmation": ["primary RQ", "research object", "scope", "method route", "section merge/split"],
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# 大纲关键词-证据校准版", "",
        f"- 状态：`{summary['reconciliation_status']}`",
        f"- 章节覆盖：{summary['covered_section_count']}/{summary['section_count']}",
        f"- 高影响修改需用户确认：{'是' if summary['requires_user_confirmation'] else '否'}", "",
        "## 章节与关键词对账", "",
        "| 章节 | 覆盖状态 | 映射文献 | T1/T2 | 语料新增候选词 | 证据缺口 |",
        "|---|---:|---:|---:|---|---|",
    ]
    for item in payload["sections"]:
        lines.append(
            f"| {item.get('section_id')} {item.get('section_title') or ''} | {item['coverage_status']} | "
            f"{item['mapped_record_count']} | {item['t1_t2_count']} | "
            f"{', '.join(item['suggested_corpus_terms']) or '-'} | {item['evidence_gap'] or '-'} |"
        )
    lines.extend(["", "## 高影响修改建议", ""])
    if payload["high_impact_proposals"]:
        for item in payload["high_impact_proposals"]:
            lines.append(f"- {item['section_id']}: {item['finding']}；建议：{item['proposed_action']}（需用户确认）")
    else:
        lines.append("- 无。")
    lines.extend(["", "## 校准后章节基线", ""])
    for section in payload["calibrated_outline"].get("sections", []):
        if not isinstance(section, dict):
            continue
        lines.extend([
            f"### {section.get('section_id')} {section.get('section_title') or ''}", "",
            f"- 章节功能：{section.get('section_function') or '-'}",
            f"- 核心论点：{'; '.join(str(item) for item in section.get('key_claims') or []) or '-'}",
            f"- 原关键词：{'; '.join(str(item) for item in section.get('keywords') or []) or '-'}",
            f"- 语料候选词：{'; '.join(section.get('step4_suggested_corpus_terms') or []) or '-'}",
            f"- 正式检索覆盖：{section.get('step4_evidence_status') or 'unmapped'}",
            f"- T1/T2 数量：{section.get('step4_t1_t2_count', 0)}", "",
        ])
    lines.extend(["", "> 本文件不静默改变核心 RQ、研究对象、scope、方法路线或章节合并/拆分。", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile Step 2 outline and keywords after Step 4 search.")
    parser.add_argument("--outline", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--output-json", default="Step2-检索对账报告.json")
    parser.add_argument("--output-md", default="大纲关键词-证据校准版.md")
    args = parser.parse_args()
    outline_path = Path(args.outline)
    results_path = Path(args.results)
    outline = _load(outline_path)
    if not isinstance(outline, dict):
        raise SystemExit("outline must be a JSON object")
    payload = reconcile(outline, _load(results_path), outline_hash=_sha256(outline_path), results_hash=_sha256(results_path))
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
