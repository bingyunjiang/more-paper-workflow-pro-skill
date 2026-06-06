#!/usr/bin/env python3
"""Generate a comprehensive 检索报告.md — full search methodology report.

Complements 检索文献表.md (the raw results table) with a standalone report covering:
  1. 检索概览          — executive summary with key metrics
  2. 检索范围与方法     — databases, query strategies, routing
  3. 检索结果流水线     — PRISMA-S flow diagram with per-stage counts
  4. 评分维度与方法     — five-dimension rubric with weights
  5. 最终文献库分析     — tier/subtopic/year/source distributions + top-N
  6. 引文扩展          — citation network expansion results (if triggered)
  7. 饱和度分析        — saturation curve interpretation
  8. 下一步行动         — recommended next steps

Usage:
  # Basic usage (extracts everything possible from .md alone)
  python3 scripts/generate_search_report.py \
    --results 检索文献表.md \
    --saturation saturation_snapshot.json \
    --output 检索报告.md

  # With search metadata for richer details
  python3 scripts/generate_search_report.py \
    --results 检索文献表.md \
    --metadata search_metadata.json \
    --saturation saturation_snapshot.json \
    --output 检索报告.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ── Markdown table parsing (reuses logic from generate_retrieval_report.py) ──

def _normalize_doi(doi: str) -> str:
    doi = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]
    return doi


def _parse_md_table(md_path: str) -> List[Dict]:
    """Parse a markdown table from 检索文献表.md into a list of dicts."""
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.split("\n")
    table_blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and "|" in line[1:]:
            if i + 1 < len(lines) and re.match(r'^\|[\s\-:|\s]+\|', lines[i + 1].strip()):
                header_line = line
                data_rows = []
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    data_rows.append(lines[j].strip())
                    j += 1
                table_blocks.append((header_line, data_rows))
                i = j
                continue
        i += 1

    if not table_blocks:
        return []

    best_header, best_data = "", []
    best_cols = 0
    for hl, dr in table_blocks:
        cols = [c.strip() for c in hl.strip("|").split("|")]
        if len(cols) > best_cols:
            best_cols = len(cols)
            best_header = hl
            best_data = dr

    if not best_header:
        return []

    columns = [c.strip().lower() for c in best_header.strip("|").split("|")]
    col_map = {}
    for idx, col in enumerate(columns):
        c = col.strip().lower()
        if "doi" in c:                      col_map["doi"] = idx
        elif "title" in c or "标题" in c:    col_map["title"] = idx
        elif "year" in c or "年份" in c:     col_map["year"] = idx
        elif "source" in c or "来源" in c:   col_map["source"] = idx
        elif "score" in c or "评分" in c or "分数" in c: col_map["score"] = idx
        elif "tier" in c:                   col_map["tier"] = idx
        elif "flag" in c or "旗标" in c:     col_map["flags"] = idx
        elif "citation" in c or "引用" in c:
            if "influential" in c or "影响力" in c or "高引" in c:
                col_map["influential_citations"] = idx
            else:
                col_map["citations"] = idx
        elif "sub" in c or "子课题" in c or "topic" in c: col_map["subtopic"] = idx
        elif "author" in c or "作者" in c:   col_map["authors"] = idx
        elif "journal" in c or "期刊" in c or "venue" in c: col_map["journal"] = idx

    rows = []
    for row_line in best_data:
        cells = [c.strip() for c in row_line.strip("|").split("|")]
        row = {}
        for key, idx in col_map.items():
            row[key] = cells[idx] if idx < len(cells) else ""
        if "doi" in row:
            row["doi"] = _normalize_doi(row["doi"])
        if row.get("doi"):
            rows.append(row)

    return rows


def _parse_retrieval_summary(md_path: str) -> Dict[str, str]:
    """Extract the 检索概况 block from the top of a .md file."""
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    info = {}
    patterns = {
        "search_date":    r"检索日期[：:]\s*(.+)",
        "tier":           r"Tier[：:]\s*(.+)",
        "databases":      r"数据库[：:]\s*(.+)",
        "original_count": r"原始检索[：:]\s*(.+)",
        "expansion":      r"引文扩展[：:]\s*(.+)",
        "final_count":    r"最终文献[：:]\s*(.+)",
        "coverage":       r"饱和度[：:]\s*(.+)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            info[key] = m.group(1).strip()
    return info


# ── Statistics & distributions ─────────────────────────────────────────────

def _safe_int(val) -> int:
    """Extract integer from a cell value (handles '22/25', 'T1', etc.)."""
    if isinstance(val, (int, float)):
        return int(val)
    m = re.search(r'(\d+)', str(val))
    return int(m.group(1)) if m else 0


def _compute_distributions(rows: List[Dict]) -> Dict:
    """Compute all distribution stats from the literature table."""
    stats = {}

    # Tier distribution
    tier_counts = Counter(r.get("tier", "").strip() for r in rows)
    stats["tier_counts"] = dict(tier_counts)

    # Score distribution
    scores = [_safe_int(r.get("score", 0)) for r in rows]
    if scores:
        stats["score_min"] = min(scores)
        stats["score_max"] = max(scores)
        stats["score_mean"] = round(sum(scores) / len(scores), 1)
        stats["score_median"] = sorted(scores)[len(scores) // 2]

    # Year distribution
    years = Counter(r.get("year", "?").strip() for r in rows)
    stats["year_counts"] = dict(sorted(years.items(), reverse=True)[:10])
    stats["year_median"] = sorted(years.keys())[len(years) // 2] if years else "?"

    # Source distribution
    sources = Counter(r.get("source", "?").strip() for r in rows)
    stats["source_counts"] = dict(sources.most_common(10))

    # Journal distribution
    journals = Counter(r.get("journal", "").strip() for r in rows if r.get("journal", "").strip())
    stats["journal_counts"] = dict(journals.most_common(10))

    # Subtopic distribution
    subtopics = Counter(r.get("subtopic", "").strip() for r in rows if r.get("subtopic", "").strip())
    stats["subtopic_counts"] = dict(subtopics.most_common(15))

    # Flag distribution
    flags = Counter(r.get("flags", "").strip() for r in rows if r.get("flags", "").strip())
    stats["flag_counts"] = dict(flags.most_common(10))

    # Citation stats
    citations = [_safe_int(r.get("citations", 0)) for r in rows]
    inf_citations = [_safe_int(r.get("influential_citations", 0)) for r in rows]
    if citations:
        stats["citation_total"] = sum(citations)
        stats["citation_mean"] = round(sum(citations) / len(citations), 1)
        stats["citation_max"] = max(citations)
    if inf_citations:
        stats["inf_citation_total"] = sum(inf_citations)
        stats["inf_citation_mean"] = round(sum(inf_citations) / len(inf_citations), 1)

    # Top papers by score
    top_by_score = sorted(rows, key=lambda r: _safe_int(r.get("score", 0)), reverse=True)[:10]
    stats["top_10"] = [
        {
            "doi": r.get("doi", ""),
            "title": r.get("title", "")[:80],
            "year": r.get("year", ""),
            "score": _safe_int(r.get("score", 0)),
            "tier": r.get("tier", "").strip(),
            "journal": r.get("journal", ""),
        }
        for r in top_by_score
    ]

    return stats


# ── PRISMA-S flow builder ───────────────────────────────────────────────────

def _build_prisma_flow(
    rows: List[Dict],
    summary: Dict[str, str],
    metadata: Optional[Dict] = None,
) -> str:
    """Build a textual PRISMA-S flow diagram from available data."""

    total = len(rows)  # final T1-T3 count — NOT the raw search count
    meta = metadata or {}

    # ── Per-source breakdown (supports nested dicts for per-stage counts) ──
    source_breakdown_raw = meta.get("source_breakdown", {})
    source_breakdown: Dict[str, Dict] = {}
    if source_breakdown_raw:
        for src, val in source_breakdown_raw.items():
            if isinstance(val, dict):
                # Nested: {"openalex": {"raw": 65, "dedup": 55, "named": "OpenAlex"}}
                source_breakdown[src] = {
                    "raw": val.get("raw", 0),
                    "dedup": val.get("dedup"),
                    "verified": val.get("verified"),
                    "named": val.get("named", src),
                }
            else:
                # Flat int: {"openalex": 65} — backward compat
                source_breakdown[src] = {"raw": int(val)}
    if not source_breakdown:
        # No metadata at all — count from final rows (source display only)
        src_counts = Counter(r.get("source", "").strip() for r in rows)
        for src, cnt in src_counts.items():
            source_breakdown[src] = {"raw": cnt}

    # ── Stage counts from metadata ONLY — never fall back to len(rows) ──
    # len(rows) is the final filtered T1-T3 table; raw/after_dedup/after_verify
    # are order-of-magnitude larger and MUST come from metadata.
    raw_total = meta.get("raw_total")
    after_dedup = meta.get("after_dedup")
    after_verify = meta.get("after_verify")
    t4_removed = meta.get("t4_removed", 0)
    expansion_added = meta.get("expansion_added", 0)

    has_flow = raw_total is not None and after_dedup is not None

    tier_counts = Counter(r.get("tier", "").strip() for r in rows)
    t1 = tier_counts.get("T1", 0)
    t2 = tier_counts.get("T2", 0)
    t3 = tier_counts.get("T3", 0)

    # ── Expansion staging ──
    initial_tier = meta.get("initial_tier_counts")  # e.g. {"T1": 28, "T2": 92, "T3": 0}
    expansion_tier = meta.get("expansion_tier_counts")  # e.g. {"T1": 23, "T2": 19, "T3": 18}
    expansion_candidates = meta.get("expansion_candidates")
    has_expansion_staging = initial_tier is not None and expansion_tier is not None

    lines = []
    lines.append("### 3.1 PRISMA-S 流程图")
    lines.append("")

    if not has_flow:
        lines.append("> ⚠️ 缺少检索元数据 (`--metadata search_metadata.json`)，无法绘制完整的 PRISMA-S 流程图。")
        lines.append("> 以下为最终文献库的 Tier 分布摘要：")
        lines.append("")
        lines.append("```")
        lines.append(f"  ⭐ T1 (≥20): {t1} 篇 — 核心文献")
        lines.append(f"  📘 T2 (15-19): {t2} 篇 — 重要文献")
        lines.append(f"  📄 T3 (10-14): {t3} 篇 — 参考文献")
        lines.append(f"  📊 最终文献库: {total} 篇 (T1-T3)")
        lines.append("```")
        lines.append("")
        return "\n".join(lines)

    lines.append("```")
    lines.append(f"  多渠道原始检索: {raw_total} 篇")
    lines.append("  │")

    db_names = {
        "openalex": "OpenAlex",
        "semantic_scholar": "Semantic Scholar",
        "crossref": "Crossref",
        "arxiv": "arXiv",
        "pubmed": "PubMed",
    }
    for src, sb in sorted(source_breakdown.items(), key=lambda x: -(x[1].get("raw", 0))):
        cnt = sb.get("raw", 0)
        db_label = sb.get("named") or db_names.get(src.lower().replace(" ", "_"), src)
        lines.append(f"  ├─ {db_label}: {cnt} 篇")

    lines.append("  │")
    dedup_removed = raw_total - after_dedup
    lines.append(f"  ▼ DOI去重: {after_dedup} 篇  (移除 {dedup_removed} 篇重复)")
    lines.append("  │")
    if after_verify is not None:
        verify_removed = after_dedup - after_verify
        lines.append(f"  ▼ 引文验证: {after_verify} 篇  (移除 {verify_removed} 篇无效/残缺)")
    else:
        lines.append(f"  ▼ 引文验证: (未记录)")
    lines.append("  │")

    if has_expansion_staging:
        # ── Staged: show initial screening → expansion → final ──
        init_t1 = initial_tier.get("T1", 0)
        init_t2 = initial_tier.get("T2", 0)
        init_t3 = initial_tier.get("T3", 0)
        init_total = init_t1 + init_t2 + init_t3
        lines.append(f"  ▼ 五维度评分 + Tier 分级 (初始筛选): {init_total} 篇")
        lines.append(f"  ├─ ⭐ T1 (≥20): {init_t1} 篇 — 核心文献，必须下载")
        lines.append(f"  ├─ 📘 T2 (15-19): {init_t2} 篇 — 重要文献，尽量下载")
        lines.append(f"  ├─ 📄 T3 (10-14): {init_t3} 篇 — 参考文献")
        lines.append(f"  └─ ⬜ T4 (<10): {t4_removed} 篇 — ⛔ 剔除")
        lines.append("  │")
        seeds = meta.get("expansion_seeds", "?")
        cand_text = f" (来自 {seeds} 篇 T1 种子)" if seeds != "?" else ""
        ec = expansion_candidates if expansion_candidates is not None else init_t1 + expansion_added
        lines.append(f"  ▼ 引文网络扩展候选: {ec} 篇{cand_text}")
        lines.append("  │")
        exp_t1 = expansion_tier.get("T1", 0)
        exp_t2 = expansion_tier.get("T2", 0)
        exp_t3 = expansion_tier.get("T3", 0)
        lines.append(f"  ▼ 引文扩展结果 (去重+评分后):")
        if expansion_added > 0:
            lines.append(f"  ├─ 实际新增: +{expansion_added} 篇")
            lines.append(f"  ├─ ⭐ T1: {exp_t1} 篇")
            lines.append(f"  ├─ 📘 T2: {exp_t2} 篇")
            lines.append(f"  └─ 📄 T3: {exp_t3} 篇")
        else:
            lines.append(f"  └─ 实际新增: 0 篇 (全部重复或 T4)")
        lines.append("  │")
        lines.append(f"  ▼ 最终文献库 (初始 + 扩展): {total} 篇 (T1-T3)")
        lines.append(f"  ├─ ⭐ T1 (≥20): {t1} 篇")
        lines.append(f"  ├─ 📘 T2 (15-19): {t2} 篇")
        lines.append(f"  └─ 📄 T3 (10-14): {t3} 篇")
    else:
        # ── Simple: all tiers from final rows ──
        lines.append(f"  ▼ 五维度评分 + Tier 分级:")
        lines.append(f"  ├─ ⭐ T1 (≥20): {t1} 篇 — 核心文献，必须下载")
        lines.append(f"  ├─ 📘 T2 (15-19): {t2} 篇 — 重要文献，尽量下载")
        lines.append(f"  ├─ 📄 T3 (10-14): {t3} 篇 — 参考文献，有选择下载")
        lines.append(f"  └─ ⬜ T4 (<10): {t4_removed} 篇 — ⛔ 剔除")
        lines.append("  │")
        if expansion_added > 0:
            lines.append(f"  ▼ 引文网络扩展 (1-hop): +{expansion_added} 篇")
            lines.append("  │")
        lines.append(f"  ▼ 最终文献库: {total} 篇 (T1-T3)")
    lines.append("```")
    lines.append("")

    # ── PRISMA-S compliance table (metadata-driven) ──
    lines.append("### 3.2 PRISMA-S 检索合规清单")
    lines.append("")

    # Database list from metadata
    db_list = meta.get("databases") or summary.get("databases") or "OpenAlex"
    # Source status notes for database description
    source_status = meta.get("source_status", {})
    db_notes = []
    if source_status.get("semantic_scholar") == "429":
        db_notes.append("Semantic Scholar 跳过")
    if source_status.get("wanfang") == "attempted_failed":
        db_notes.append(f"万方已尝试({meta.get('wanfang_fail_reason', '失败')})")
    db_desc = db_list
    if db_notes:
        db_desc += "；" + "；".join(db_notes)

    # Strategy description from metadata
    strategy_desc = meta.get("search_strategy") or _build_strategy_text(meta)

    # Record management from metadata (don't claim Zotero if not confirmed)
    record_mgmt = meta.get("record_management", ".md + .xlsx + .bib 导出，后续可导入 Zotero")

    lines.append("| # | 检查项 | 状态 | 说明 |")
    lines.append("|---|--------|:----:|------|")
    checks = [
        (1, "数据库选择", "✅", f"已使用: {db_desc}"),
        (2, "多源策略", "✅", strategy_desc),
        (3, "检索日期范围", "✅", f"执行日期: {summary.get('search_date', datetime.now().strftime('%Y-%m-%d'))}"),
        (4, "完整检索式记录", "✅", "已记录在检索方案 (Step 3)"),
        (5, "去重方法", "✅", "DOI 主键 + title+first_author+year 组合键"),
        (6, "记录管理", "✅", record_mgmt),
        (7, "筛选标准", "✅", "五维度评分 + Tier 1-4 分级"),
        (8, "灰色文献", "⬜", "非本自动化检索范围"),
        (9, "手动检索", "⬜", "非本自动化检索范围"),
        (10, "专家咨询", "⬜", "非本自动化检索范围"),
        (11, "引文追踪", "✅" if expansion_added > 0 else "⬜", "1-hop 引文网络扩展" if expansion_added > 0 else "未触发 (无 T1 种子)"),
        (12, "语言限制", "⬜", "未设置语言过滤"),
        (13, "更新检索", "⬜", "单轮检索，未设置定期更新"),
        (14, "数据提取", "✅", "自动化提取 DOI/标题/作者/年份/期刊/摘要"),
        (15, "质量评估", "✅", "rcs-rubric 启发式主题匹配度评估"),
        (16, "综合方法", "✅", "定量评分 + 定性旗标 + 饱和度估算"),
    ]
    for num, item, status, note in checks:
        lines.append(f"| {num} | {item} | {status} | {note} |")
    lines.append("")

    return "\n".join(lines)


# ── Report builder ──────────────────────────────────────────────────────────

def _build_strategy_text(meta: Dict) -> str:
    """Build strategy description from metadata, reflecting actual execution."""
    source_status = meta.get("source_status", {})
    parts = []

    # English sources used
    en_sources = []
    if source_status.get("openalex") == "ok":
        en_sources.append("OpenAlex")
    if source_status.get("crossref") == "ok":
        en_sources.append("Crossref")
    if source_status.get("semantic_scholar") == "ok":
        en_sources.append("Semantic Scholar")
    if en_sources:
        parts.append("英文 " + " + ".join(en_sources) + " 分层检索")

    # Chinese sources used
    cn_sources = []
    cn_auth = ""
    if source_status.get("cnki") in ("ok", "carsi_logged_in"):
        cn_sources.append("CNKI")
        if source_status.get("cnki") == "carsi_logged_in":
            cn_auth = "/CARSI"
    if source_status.get("wanfang") in ("ok", "carsi_logged_in"):
        cn_sources.append("万方")
        if not cn_auth and source_status.get("wanfang") == "carsi_logged_in":
            cn_auth = "/CARSI"
    if cn_sources:
        parts.append(f"中文 {' + '.join(cn_sources)}{cn_auth} 登录检索" if cn_auth else f"中文 {' + '.join(cn_sources)} IP 直连检索")

    # Expansion
    if meta.get("expansion_added", 0) > 0:
        parts.append(f"T1 种子 1-hop 引文扩展 (+{meta['expansion_added']} 篇)")

    # Failed/skipped sources
    notes = []
    if source_status.get("semantic_scholar") == "429":
        notes.append("Semantic Scholar 429 已跳过")
    if source_status.get("wanfang") == "attempted_failed":
        reason = meta.get("wanfang_fail_reason", "失败")
        notes.append(f"万方已尝试但{reason}")
    if source_status.get("cnki") == "skipped_no_account":
        notes.append("CNKI 用户无机构账号已跳过")
    if source_status.get("crossref") == "fail":
        notes.append("Crossref 不可达")

    result = "；".join(parts)
    if notes:
        result += "。" + "；".join(notes)
    return result or "relevance + cited + recent"


def _build_source_routing_table(meta: Dict, tier_param: str) -> List[str]:
    """Build a dynamic L1→L2→L3 routing table from source_status metadata."""
    source_status = meta.get("source_status", {})
    tier_limits = {"quick": 30, "standard": 50, "deep": 100}
    limit = tier_limits.get(tier_param, 50)

    lines = []
    lines.append("| 层级 | 数据库 | 策略 | 每策略上限 | 状态 / 说明 |")
    lines.append("|:----:|--------|------|:----------:|------------|")

    # L1: OpenAlex — always present
    oa_ok = source_status.get("openalex", "ok") == "ok"
    lines.append(
        f"| L1 | OpenAlex | relevance + cited + recent | {limit} "
        f"| {'✅ 已执行' if oa_ok else '❌ 不可达'} |")

    # L2: Crossref
    cr_status = source_status.get("crossref", "ok")
    cr_ok = cr_status == "ok"
    cr_note = {
        "deep": "Deep tier 必跑",
        "standard": "条件触发",
    }.get(tier_param, "条件触发")
    lines.append(
        f"| L2 | Crossref | relevance | {limit} "
        f"| {'✅ 已执行' if cr_ok else '⚠️ 跳过 (' + cr_status + ')'} | {cr_note} |")

    # L2: Semantic Scholar
    ss_status = source_status.get("semantic_scholar")
    if ss_status:
        if ss_status == "429":
            lines.append("| L2 | Semantic Scholar | — | — | ⬜ 跳过 (HTTP 429) |")
        elif ss_status == "ok":
            lines.append(
                f"| L2 | Semantic Scholar | relevance | {limit} "
                f"| ✅ 已执行 (影响力/引文富集) |")
        else:
            lines.append(
                f"| L2 | Semantic Scholar | — | — "
                f"| ⚠️ 跳过 ({ss_status}) |")

    # Chinese: CNKI
    cnki_status = source_status.get("cnki")
    if cnki_status:
        if cnki_status == "ok":
            lines.append(
                f"| L1 (中) | CNKI | relevance + cited | {limit} "
                f"| ✅ IP 直连 |")
        elif cnki_status == "carsi_logged_in":
            lines.append(
                f"| L1 (中) | CNKI | relevance + cited | {limit} "
                f"| ✅ CARSI 登录 |")
        elif cnki_status in ("skipped_no_account", "skipped"):
            lines.append(
                f"| L1 (中) | CNKI | — | — "
                f"| ⬜ 跳过 ({'无机构账号' if cnki_status == 'skipped_no_account' else '用户选择'}) |")

    # Chinese: Wanfang
    wf_status = source_status.get("wanfang")
    if wf_status:
        if wf_status == "ok":
            lines.append(
                f"| L2 (中) | Wanfang Data | relevance | {limit} "
                f"| ✅ IP 直连 |")
        elif wf_status == "carsi_logged_in":
            lines.append(
                f"| L2 (中) | Wanfang Data | relevance | {limit} "
                f"| ✅ CARSI 登录 |")
        elif wf_status == "attempted_failed":
            reason = meta.get("wanfang_fail_reason", "失败")
            lines.append(
                f"| L2 (中) | Wanfang Data | — | — "
                f"| ⚠️ 已尝试，{reason} |")
        elif wf_status in ("skipped_no_account", "skipped"):
            lines.append(
                f"| L2 (中) | Wanfang Data | — | — "
                f"| ⬜ 跳过 ({'无机构账号' if wf_status == 'skipped_no_account' else '用户选择'}) |")

    # arXiv
    if meta.get("arxiv_enabled"):
        lines.append(
            f"| L2* | arXiv | relevance (T-0~T-4) | 20 "
            f"| ✅ CS/AI 跨域信号 |")

    return lines

def build_report(
    rows: List[Dict],
    md_path: str,
    saturation: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> str:
    """Build the full 检索报告.md content."""

    summary = _parse_retrieval_summary(md_path)
    stats = _compute_distributions(rows)
    meta = metadata or {}
    sat = saturation or {}

    total = len(rows)  # final T1-T3 count — NOT the raw search count
    tier_counts = stats.get("tier_counts", {})
    t1 = tier_counts.get("T1", 0)
    t2 = tier_counts.get("T2", 0)
    t3 = tier_counts.get("T3", 0)
    t4_removed = meta.get("t4_removed", 0)
    expansion_added = meta.get("expansion_added", 0)
    # Stage counts from metadata ONLY — never derived from len(rows)
    raw_total = meta.get("raw_total")            # None when metadata absent
    after_dedup = meta.get("after_dedup")        # None when metadata absent
    after_verify_val = meta.get("after_verify")  # None when metadata absent
    has_flow = raw_total is not None and after_dedup is not None

    lines = []
    lines.append(f"# 文献检索报告")
    lines.append("")
    lines.append(f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} | 基于 `{Path(md_path).name}`")
    lines.append("")

    # ═══════════════════════════════════════════════════════════════════════
    # Section 1: 检索概览
    # ═══════════════════════════════════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 1. 检索概览")
    lines.append("")

    # Key metrics table
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    # ── Metadata priority: meta → summary → default ──
    tier_display = (meta.get("tier") or summary.get("tier") or "standard").upper()
    db_display = meta.get("databases") or summary.get("databases") or "OpenAlex"
    strategy_display = meta.get("search_strategy") or _build_strategy_text(meta)

    lines.append(f"| 检索日期 | {summary.get('search_date', '?')} |")
    lines.append(f"| 检索深度 | {tier_display} |")
    lines.append(f"| 数据库 | {db_display} |")
    lines.append(f"| 检索策略 | {strategy_display} |")

    # Pipeline counts — show "—" when metadata not provided
    lines.append(f"| 原始检索结果 | {raw_total if raw_total is not None else '—'} 篇 |")
    lines.append(f"| DOI 去重后 | {after_dedup if after_dedup is not None else '—'} 篇 |")
    lines.append(f"| 引文验证后 | {after_verify_val if after_verify_val is not None else '—'} 篇 |")
    if not has_flow:
        lines.append(f"| ⚠️ 精确流水线 | 需提供 `--metadata search_metadata.json` 以恢复完整计数 |")

    scored_total = total + t4_removed
    lines.append(f"| 评分筛选后 | {scored_total} 篇 (T1: {t1}, T2: {t2}, T3: {t3}, T4: {t4_removed}) |")
    if expansion_added > 0:
        lines.append(f"| 引文扩展 | +{expansion_added} 篇 (种子: {meta.get('expansion_seeds', '?')} 篇 T1) |")
    lines.append(f"| **最终文献库** | **{total} 篇** (T1: {t1} | T2: {t2} | T3: {t3}) |")

    # Saturation line
    if sat and not sat.get("fit_failed"):
        cov = sat.get("coverage_estimate", 0)
        ci_l = sat.get("ci_lower", 0)
        ci_u = sat.get("ci_upper", 0)
        interp = sat.get("interpretation", {})
        lines.append(f"| 饱和度 | {cov:.0%} (CI {ci_l:.0%}–{ci_u:.0%}) {interp.get('icon', '')} {interp.get('label_cn', '')} |")
    lines.append("")

    # ═══════════════════════════════════════════════════════════════════════
    # Section 2: 检索范围与方法
    # ═══════════════════════════════════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 2. 检索范围与方法")
    lines.append("")

    lines.append("### 2.1 分层检索路由 (L1 → L2 → L3)")
    lines.append("")
    tier_param = (meta.get("tier") or summary.get("tier") or "standard").lower()
    source_status = meta.get("source_status", {})
    if source_status:
        # Dynamic table from actual execution status
        routing_lines = _build_source_routing_table(meta, tier_param)
        lines.extend(routing_lines)
    else:
        # Fallback: static table when no metadata
        limit_val = {"quick": 30, "standard": 50, "deep": 100}.get(tier_param, 50)
        lines.append("| 层级 | 数据库 | 策略 | 每策略上限 | 触发条件 |")
        lines.append("|:----:|--------|------|:----------:|---------|")
        lines.append(f"| L1 | OpenAlex | relevance + cited + recent | {limit_val} | 所有子课题 |")
        lines.append(f"| L2 | Crossref | relevance | {limit_val} | Deep tier 必跑 / Standard 条件触发 |")
        lines.append(f"| L2 | Semantic Scholar | relevance | {limit_val} | CS/AI 交叉子领域 |")
        lines.append(f"| L3 | PubMed | relevance | {limit_val // 2} | 仅医工交叉 |")
        if meta.get("arxiv_enabled"):
            lines.append("| L2* | arXiv | relevance (T-0~T-4) | 20 | CS/AI 跨域信号 |")
    lines.append("")

    lines.append("### 2.2 检索式结构（概念块布尔）")
    lines.append("")
    if meta.get("query_summary"):
        for qs in meta["query_summary"]:
            lines.append(f"- **{qs.get('subtopic', '?')}**: `{qs.get('query', '?')}`")
    else:
        lines.append("> ⚠️ 检索式详情未随附。完整检索式请参见 Step 3 检索方案。")
        lines.append("> 如需在报告中收录检索式，运行 `generate_search_report.py` 时传入 `--metadata search_metadata.json`。")
    lines.append("")

    lines.append("### 2.3 检索参数 (Tier-driven)")
    lines.append("")
    lines.append("| 参数 | Quick | Standard (默认) | Deep |")
    lines.append("|------|:-----:|:---------------:|:----:|")
    lines.append("| limit/策略 | 30 | 50 | 100 |")
    lines.append("| strategies | relevance only | relevance + cited + recent | + seminal cutoff + review type |")
    lines.append("| 引文扩展 | 否 | T1 > 0 时触发 | T1 > 0 时触发 |")
    lines.append(f"| 本次使用 | {'✅' if tier_param == 'quick' else '—'} | {'✅' if tier_param == 'standard' else '—'} | {'✅' if tier_param == 'deep' else '—'} |")
    lines.append("")

    # ═══════════════════════════════════════════════════════════════════════
    # Section 3: 检索结果流水线
    # ═══════════════════════════════════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 3. 检索结果流水线")
    lines.append("")
    lines.append(_build_prisma_flow(rows, summary, metadata))
    lines.append("")

    # ═══════════════════════════════════════════════════════════════════════
    # Section 4: 评分维度与方法
    # ═══════════════════════════════════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 4. 评分维度与方法")
    lines.append("")
    lines.append("### 4.1 五维度评分体系")
    lines.append("")
    lines.append("| # | 维度 | 权重 | 分值 | 评分标准 |")
    lines.append("|---|------|:----:|:----:|---------|")
    lines.append("| 1 | 主题匹配度 | **35%** | 0-5 | 标题+摘要与研究主题的相关程度；rcs-rubric 四级锚定 |")
    lines.append("| 2 | 方法学严谨性 | **20%** | 0-5 | 实验验证 > 纯仿真；有对照实验 > 无对照 |")
    lines.append("| 3 | 来源质量 | **15%** | 0-5 | SCI 一区/CCF-A > 二区 > 三区/四区 > 无检索 |")
    lines.append("| 4 | 时效性 | **15%** | 0-5 | 近3年=5分，近5年=4分，近10年=3分，更早=2分 |")
    lines.append("| 5 | 影响力 | **15%** | 0-5 | 引用量 + Semantic Scholar influentialCitationCount |")
    lines.append("")
    lines.append(f"- **满分**: 25 分 | **实际范围**: {stats.get('score_min', '?')}–{stats.get('score_max', '?')} | **均值**: {stats.get('score_mean', '?')} | **中位**: {stats.get('score_median', '?')}")
    lines.append("")

    lines.append("### 4.2 Tier 分级筛选")
    lines.append("")
    lines.append("| 等级 | 分数 | 本报告数量 | 处理方式 |")
    lines.append("|:----:|:----:|:----------:|---------|")
    lines.append(f"| ⭐ T1 | ≥ 20 | {t1} | 核心文献，必须下载 |")
    lines.append(f"| 📘 T2 | 15–19 | {t2} | 重要文献，尽量下载 |")
    lines.append(f"| 📄 T3 | 10–14 | {t3} | 参考文献，有选择下载 |")
    lines.append(f"| ⬜ T4 | < 10 | {t4_removed} | ⛔ 剔除 — 不进入后续导出 |")
    lines.append("")

    lines.append("### 4.3 特殊旗标 (Flags)")
    lines.append("")
    flags = stats.get("flag_counts", {})
    if flags:
        lines.append("| 旗标 | 数量 | 含义 |")
        lines.append("|------|:----:|------|")
        flag_descriptions = {
            "foundation": "奠基性文献 — 在 ≥2 条策略线中重复出现，主题匹配度 +1",
            "recent_unindexed": "新预印本 — 不因缺引用而降分",
            "no_abstract_uncertain": "无摘要 — 最高评 4 分，不确定性标注",
            "seminal": "经典文献 — 高引用 + 方法学奠基",
            "review": "综述文章 — 提供全景视角",
        }
        for flag, count in sorted(flags.items(), key=lambda x: -x[1]):
            desc = flag_descriptions.get(flag, "")
            lines.append(f"| `{flag}` | {count} | {desc} |")
    else:
        lines.append("> 本轮未触发特殊旗标。")
    lines.append("")

    # ═══════════════════════════════════════════════════════════════════════
    # Section 5: 最终文献库分析
    # ═══════════════════════════════════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 5. 最终文献库分析")
    lines.append(f"> 共 {total} 篇 T1-T3 文献")
    lines.append("")

    # 5.1 Tier 分布
    lines.append("### 5.1 Tier 分布")
    lines.append("")
    lines.append("| Tier | 数量 | 占比 | 可视化 |")
    lines.append("|:----:|:----:|:----:|--------|")
    for tier_label, tier_name in [("T1", "核心"), ("T2", "重要"), ("T3", "参考")]:
        count = tier_counts.get(tier_label, 0)
        pct = count / total * 100 if total > 0 else 0
        bar = "█" * max(1, int(pct / 5)) + "░" * max(0, 20 - int(pct / 5))
        lines.append(f"| {tier_label} | {count} | {pct:.0f}% | {bar} |")
    lines.append("")

    # 5.2 子课题分布
    subtopics = stats.get("subtopic_counts", {})
    if subtopics:
        lines.append("### 5.2 子课题分布")
        lines.append("")
        lines.append("| 子课题 | T1 | T2 | T3 | 合计 |")
        lines.append("|--------|:--:|:--:|:--:|:----:|")
        for subtopic in subtopics:
            st_t1 = sum(1 for r in rows if r.get("subtopic", "").strip() == subtopic and r.get("tier", "").strip() == "T1")
            st_t2 = sum(1 for r in rows if r.get("subtopic", "").strip() == subtopic and r.get("tier", "").strip() == "T2")
            st_t3 = sum(1 for r in rows if r.get("subtopic", "").strip() == subtopic and r.get("tier", "").strip() == "T3")
            lines.append(f"| {subtopic} | {st_t1} | {st_t2} | {st_t3} | {st_t1 + st_t2 + st_t3} |")
        lines.append("")

    # 5.3 年份分布
    years = stats.get("year_counts", {})
    if years:
        lines.append("### 5.3 年份分布")
        lines.append("")
        lines.append("| 年份 | 数量 | T1 占比 |")
        lines.append("|:----:|:----:|:-------:|")
        for year, count in list(sorted(years.items(), reverse=True))[:10]:
            yr_t1 = sum(1 for r in rows if r.get("year", "").strip() == year and r.get("tier", "").strip() == "T1")
            lines.append(f"| {year} | {count} | {yr_t1}/{count} ({yr_t1/count*100:.0f}%)" if count > 0 else f"| {year} | {count} | — |")
        recent_3y = sum(1 for r in rows if _safe_int(r.get("year", 0)) >= datetime.now().year - 2)
        lines.append(f"| **近 3 年合计** | **{recent_3y}** | **{recent_3y/total*100:.0f}%** |" if total > 0 else "")
        lines.append("")

    # 5.4 来源分布
    sources = stats.get("source_counts", {})
    if sources:
        lines.append("### 5.4 数据来源分布")
        lines.append("")
        lines.append("| 来源 | 数量 | 占比 |")
        lines.append("|------|:----:|:----:|")
        for src, count in sources.items():
            lines.append(f"| {src} | {count} | {count/total*100:.0f}% |" if total > 0 else f"| {src} | {count} | — |")
        lines.append("")

    # 5.5 期刊分布
    journals = stats.get("journal_counts", {})
    if journals:
        lines.append("### 5.5 期刊/会议分布 (Top 10)")
        lines.append("")
        lines.append("| 期刊/会议 | 数量 |")
        lines.append("|-----------|:----:|")
        for j, count in journals.items():
            lines.append(f"| {j} | {count} |")
        lines.append("")

    # 5.6 Citation stats
    if stats.get("citation_total"):
        lines.append("### 5.6 引用统计")
        lines.append("")
        lines.append("| 指标 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| 总引用数 | {stats['citation_total']} |")
        lines.append(f"| 平均引用 | {stats['citation_mean']} |")
        lines.append(f"| 最高引用 | {stats['citation_max']} |")
        if stats.get("inf_citation_total"):
            lines.append(f"| 总影响力引用 | {stats['inf_citation_total']} |")
            lines.append(f"| 平均影响力引用 | {stats['inf_citation_mean']} |")
        lines.append("")

    # 5.7 Top 10 papers
    lines.append("### 5.7 Top 10 最高评分文献")
    lines.append("")
    lines.append("| # | DOI | 标题 | 年份 | 期刊 | 评分 | Tier |")
    lines.append("|---|-----|------|:----:|------|:----:|:----:|")
    for i, p in enumerate(stats.get("top_10", []), 1):
        lines.append(f"| {i} | `{p['doi'][:25]}...` | {p['title'][:60]} | {p['year']} | {p['journal'][:25]} | {p['score']} | {p['tier']} |")
    lines.append("")

    # ═══════════════════════════════════════════════════════════════════════
    # Section 6: 引文扩展
    # ═══════════════════════════════════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 6. 引文网络扩展")
    lines.append("")

    if expansion_added > 0:
        lines.append(f"- **种子论文**: {meta.get('expansion_seeds', '?')} 篇 T1")
        lines.append(f"- **扩展策略**: 单轮 1-hop (refs-limit 30 + cited-by-limit 50)")
        lines.append(f"- **新增文献**: {expansion_added} 篇")
        exp_t1 = meta.get("expansion_t1", 0)
        exp_t2 = meta.get("expansion_t2", 0)
        exp_t3 = meta.get("expansion_t3", 0)
        lines.append(f"  - T1: {exp_t1} 篇")
        lines.append(f"  - T2: {exp_t2} 篇")
        lines.append(f"  - T3: {exp_t3} 篇")
        lines.append(f"- **去重**: 已与原始文献库 DOI 去重")
        lines.append(f"- **评分**: 新增论文已完成五维度评分 + Tier 分级")
    else:
        lines.append("> 本轮**未触发**引文扩展。")
        if t1 == 0:
            lines.append("> 原因: 无 T1 种子论文 (score ≥ 20)。")
        else:
            lines.append(f"> 原因: 虽然有 {t1} 篇 T1 论文，但未执行扩展步骤。建议在检索深度为 deep 时触发。")
    lines.append("")

    # ═══════════════════════════════════════════════════════════════════════
    # Section 7: 饱和度分析
    # ═══════════════════════════════════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 7. 饱和度分析")
    lines.append("")

    if sat:
        interp = sat.get("interpretation", {})
        fq = sat.get("fit_quality", {})

        lines.append(f"### {interp.get('icon', '?')} 判定: {interp.get('label_cn', '未知')}")
        lines.append("")

        if sat.get("fit_failed"):
            reason = sat.get("fit_failed_reason", "模型拟合失败")
            lines.append(f"**拟合状态**: 失败 — {reason}")
        else:
            lines.append("| 指标 | 值 |")
            lines.append("|------|-----|")
            lines.append(f"| 覆盖率 | {sat.get('coverage_estimate', 0):.0%} |")
            lines.append(f"| 95% 置信区间 | {sat.get('ci_lower', 0):.0%} – {sat.get('ci_upper', 0):.0%} |")
            lines.append(f"| 估计文献池总量 | {sat.get('n_total_estimate', 0):.0f} 篇 |")
            lines.append(f"| 衰减系数 λ | {sat.get('lambda', 0):.4f} |")
            lines.append(f"| 模型 | {fq.get('model', 'exponential_decay')} |")
            lines.append(f"| 置信区间宽度 | {fq.get('ci_width', 0):.0%} — {'较窄，估计可靠' if fq.get('ci_width', 1) < 0.15 else '较宽，不确定性高'} |")
        lines.append("")

        lines.append("**解释**:")
        lines.append(sat.get("explanation", "无"))
        lines.append("")

        lines.append("**建议**:")
        lines.append(sat.get("recommendation", "无"))
        lines.append("")
    else:
        lines.append("> ⚠️ 未找到饱和度数据。请先运行 `discovery_curve.py` 生成 `saturation_snapshot.json`。")
    lines.append("")

    # ═══════════════════════════════════════════════════════════════════════
    # Section 8: 下一步
    # ═══════════════════════════════════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 8. 下一步行动")
    lines.append("")
    lines.append(f"- **Step 5**: 统一路由下载 {total} 篇 PDF（T1-T3）")
    lines.append(f"  - 自动路由: Sci-Hub → ScienceDirect CDP → IEEE CDP → Generic CDP")
    if sat and not sat.get("fit_failed"):
        cov = sat.get("coverage_estimate", 0)
        if cov < 0.6:
            lines.append(f"- ⚠️ 覆盖率仅 {cov:.0%}，建议先补充检索再下载")
    lines.append(f"- **Step 6**: 导入 Zotero → 生成文库架构 → 综述矩阵")
    lines.append(f"- **Step 7**: 论文写作（{total} 篇文献支撑）")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*本内容由 Dr. Jiang 的 More Paper Workflow Pro Skill 生成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    return "\n".join(lines)


# ── PDF generation ──────────────────────────────────────────────────────────

def _generate_pdf(md_path: str, output_path: str) -> bool:
    """Generate .pdf from .md using md_to_pdf.py."""
    script_dir = Path(__file__).resolve().parent
    md_to_pdf = script_dir / "md_to_pdf.py"

    if not md_to_pdf.exists():
        print(f"⚠️  md_to_pdf.py not found at {md_to_pdf}, skipping PDF generation",
              file=sys.stderr)
        return False

    cmd = [
        sys.executable, str(md_to_pdf),
        md_path,
        "-o", output_path,
        "--type", "auto",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"  ✅ PDF 已生成: {output_path}")
            return True
        else:
            print(f"  ⚠️  PDF 生成失败: {result.stderr.strip()}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  PDF 生成超时", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  ⚠️  PDF 生成错误: {e}", file=sys.stderr)
        return False


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a comprehensive literature search methodology report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --results 检索文献表.md --saturation saturation_snapshot.json -o 检索报告.md
  %(prog)s --results 检索文献表.md --metadata search_metadata.json --saturation snap.json -o report.md
  %(prog)s --results 检索文献表.md -o 检索报告.md --no-pdf
        """,
    )
    parser.add_argument("--results", required=True, type=Path, help="Path to 检索文献表.md")
    parser.add_argument("--metadata", type=Path, help="Optional search metadata JSON (enriches report with per-source counts etc.)")
    parser.add_argument("--saturation", type=Path, help="Optional saturation_snapshot.json from discovery_curve.py")
    parser.add_argument("--output", "-o", required=True, type=Path, help="Output path for 检索报告.md")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF generation (default: PDF is generated alongside .md)")
    args = parser.parse_args()

    # Load data
    if not args.results.exists():
        print(f"❌ Results file not found: {args.results}", file=sys.stderr)
        sys.exit(1)

    rows = _parse_md_table(str(args.results))
    if not rows:
        print(f"❌ No literature data found in {args.results}", file=sys.stderr)
        sys.exit(1)
    print(f"📋 Loaded {len(rows)} papers from {args.results.name}")

    metadata = None
    if args.metadata and args.metadata.exists():
        with open(args.metadata, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"📋 Loaded metadata from {args.metadata.name}")

    saturation = None
    if args.saturation and args.saturation.exists():
        with open(args.saturation, "r", encoding="utf-8") as f:
            saturation = json.load(f)
        print(f"📋 Loaded saturation data from {args.saturation.name}")

    # Build report
    report = build_report(
        rows=rows,
        md_path=str(args.results),
        saturation=saturation,
        metadata=metadata,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"\n✅ 检索报告已生成: {args.output}")
    print(f"   共 {len(report.splitlines())} 行 | {len(report)} 字符")

    # Generate PDF alongside .md
    if not args.no_pdf:
        pdf_path = args.output.with_suffix(".pdf")
        _generate_pdf(str(args.output), str(pdf_path))


if __name__ == "__main__":
    main()
