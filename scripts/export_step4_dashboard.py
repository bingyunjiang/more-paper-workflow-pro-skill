#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0
"""Export a static Step 4 search-results dashboard.

The dashboard is a review/display layer generated from the authoritative
workflow_search_results.json file. It never replaces the machine JSON,
BibTeX, Chinese metadata, or downstream evidence artifacts.
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
import shutil
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from workflow_contracts import SearchResultRecord, load_json, load_search_records


MOJIBAKE_MARKERS = ["????", "锟", "鐮", "浼", "寤", "璁", "鎽", "涓", "娑", "閻", "閸", "瀵"]
TIER_ORDER = {"T1": 1, "T2": 2, "T3": 3, "T4": 4}
CHINESE_SOURCES = {"cnki", "wanfang"}


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def normalize_tier(value: str) -> str:
    text = clean_text(value).upper().replace(" ", "")
    mapping = {
        "TIER1": "T1",
        "TIER2": "T2",
        "TIER3": "T3",
        "TIER4": "T4",
        "1": "T1",
        "2": "T2",
        "3": "T3",
        "4": "T4",
    }
    return mapping.get(text, text or "T4")


def stable_record_id(index: int, record: SearchResultRecord) -> str:
    seed = record.doi or record.source_id or record.article_url or record.title or f"record-{index}"
    compact = re.sub(r"[^a-zA-Z0-9]+", "-", seed).strip("-").lower()[:28]
    return f"rec-{index:04d}-{compact or 'record'}"


def source_language(source: str) -> str:
    return "中文源" if source in CHINESE_SOURCES else "英文/国际源"


def download_status(record: SearchResultRecord) -> str:
    if record.oa_pdf_url:
        return "oa_pdf_url"
    if record.download_hint:
        return record.download_hint
    if record.source in CHINESE_SOURCES:
        return "chinese_article_url" if record.article_url else "missing_article_url"
    if record.doi:
        return "doi"
    if record.article_url:
        return "publisher_url"
    return "unresolved"


def needs_access(record: SearchResultRecord) -> bool:
    if record.source in CHINESE_SOURCES:
        return True
    hint = download_status(record)
    return hint in {"publisher_url", "unresolved", "missing_article_url"}


def dashboard_record(index: int, record: SearchResultRecord) -> dict[str, Any]:
    tier = normalize_tier(record.paper_tier or record.tier)
    identifier = record.doi or record.source_id
    card = record.paper_card
    raw = record.raw or {}
    venue = raw.get("venue") or raw.get("journal") or raw.get("publication_title") or ""
    return {
        "record_id": stable_record_id(index, record),
        "title": record.title,
        "authors": record.authors,
        "year": record.year,
        "source": record.source or "unknown",
        "source_language": source_language(record.source),
        "doi": record.doi,
        "source_id": record.source_id,
        "identifier": identifier,
        "article_url": record.article_url,
        "search_task_id": record.search_task_id,
        "chapter_id": record.chapter_id,
        "chapter_title": record.chapter_title,
        "evidence_type": record.evidence_type,
        "score": record.score,
        "paper_tier": tier,
        "tier": record.tier,
        "verification_status": record.verification_status,
        "verification_confidence": record.verification_confidence,
        "warn_class": record.warn_class,
        "download_hint": download_status(record),
        "needs_access": needs_access(record),
        "abstract": record.abstract,
        "venue": clean_text(venue),
        "oa_status": record.oa_status,
        "oa_source": record.oa_source,
        "oa_pdf_url": record.oa_pdf_url,
        "oa_landing_url": record.oa_landing_url,
        "paper_card": {
            "evidence_role": card.evidence_role,
            "primary_claim": card.primary_claim,
            "main_methods_or_baselines": card.main_methods_or_baselines,
            "reading_depth": card.reading_depth,
            "content_fit": card.content_fit,
            "content_fit_note": card.content_fit_note,
            "usable_for": card.usable_for,
            "not_usable_for": card.not_usable_for,
        },
        "is_excluded": tier == "T4",
    }


def count_values(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        value = clean_text(record.get(key)) or "unknown"
        counter[value] += 1
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def build_meta(workflow_path: Path, workflow_payload: Any, records: list[dict[str, Any]]) -> dict[str, Any]:
    metadata = workflow_payload.get("metadata", {}) if isinstance(workflow_payload, dict) else {}
    included = [record for record in records if not record["is_excluded"]]
    download_ready = [
        record
        for record in records
        if record["paper_tier"] in {"T1", "T2"}
        and (record["doi"] or record["article_url"] or record["oa_pdf_url"])
    ]
    return {
        "schema_version": "step4-dashboard.v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_artifact": workflow_path.name,
        "authority": "display_layer_only",
        "notes": [
            "Dashboard data is derived from workflow_search_results.json.",
            "Do not use this display layer as the machine source for Step 5/6/7.",
            "Reading depth is shown explicitly to prevent abstract-only evidence from being treated as full text.",
        ],
        "workflow_metadata": metadata,
        "counts": {
            "total": len(records),
            "included_t1_t3": len(included),
            "excluded_t4": sum(1 for record in records if record["is_excluded"]),
            "download_ready_t1_t2": len(download_ready),
            "needs_access": sum(1 for record in records if record["needs_access"]),
        },
        "distributions": {
            "tier": count_values(records, "paper_tier"),
            "source": count_values(records, "source"),
            "year": count_values(records, "year"),
            "chapter": count_values(records, "chapter_id"),
            "search_task": count_values(records, "search_task_id"),
            "source_language": count_values(records, "source_language"),
            "evidence_type": count_values(records, "evidence_type"),
            "reading_depth": count_values([{"reading_depth": r["paper_card"]["reading_depth"]} for r in records], "reading_depth"),
        },
    }


def js_assignment(name: str, payload: Any) -> str:
    return f"window.{name} = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def validate_no_mojibake(output_dir: Path) -> None:
    checked = [
        output_dir / "index.html",
        output_dir / "styles.css",
        output_dir / "app.js",
        output_dir / "data" / "search-results.js",
        output_dir / "data" / "dashboard-meta.js",
    ]
    bad: list[str] = []
    for path in checked:
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(marker in text for marker in MOJIBAKE_MARKERS):
            bad.append(str(path))
    if bad:
        raise RuntimeError("Possible mojibake detected in dashboard outputs: " + ", ".join(bad))


def export_dashboard(workflow_inputs: Path, output_dir: Path, force: bool = False) -> dict[str, Any]:
    records = load_search_records(workflow_inputs)
    workflow_payload = load_json(workflow_inputs)
    dashboard_records = [dashboard_record(index, record) for index, record in enumerate(records, 1)]
    dashboard_records.sort(
        key=lambda item: (
            TIER_ORDER.get(item["paper_tier"], 9),
            item["source"],
            item["chapter_id"],
            item["title"],
        )
    )
    meta = build_meta(workflow_inputs, workflow_payload, dashboard_records)

    if output_dir.exists() and force:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data").mkdir(parents=True, exist_ok=True)

    write_text(output_dir / "index.html", INDEX_HTML)
    write_text(output_dir / "styles.css", STYLES_CSS)
    write_text(output_dir / "app.js", APP_JS)
    write_text(output_dir / "data" / "search-results.js", js_assignment("STEP4_SEARCH_RESULTS", dashboard_records))
    write_text(output_dir / "data" / "dashboard-meta.js", js_assignment("STEP4_DASHBOARD_META", meta))
    validate_no_mojibake(output_dir)
    return {
        "dashboard_dir": str(output_dir.resolve()),
        "records": len(dashboard_records),
        "included_t1_t3": meta["counts"]["included_t1_t3"],
        "excluded_t4": meta["counts"]["excluded_t4"],
    }


INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Step 4 Search Dashboard</title>
    <link rel="stylesheet" href="./styles.css" />
  </head>
  <body>
    <header class="topbar">
      <div>
        <p class="eyebrow">more-paper-workflow</p>
        <h1>Step 4 检索结果 Dashboard</h1>
        <p class="subtitle">展示层来自 workflow_search_results.json，不替代机器主工件。</p>
      </div>
      <div class="stats" id="stats"></div>
    </header>

    <main class="layout">
      <section class="toolbar" aria-label="Dashboard filters">
        <label class="search-box">
          <span>Search</span>
          <input id="searchInput" type="search" placeholder="标题、作者、DOI、source_id、摘要、primary claim" />
        </label>
        <div class="view-switch" role="tablist" aria-label="View mode">
          <button id="tableViewBtn" class="active" type="button">表格</button>
          <button id="cardViewBtn" type="button">卡片</button>
          <button id="downloadViewBtn" type="button">下载准备</button>
        </div>
      </section>

      <section class="filters" id="filters"></section>

      <section class="summary-grid">
        <section class="panel">
          <h2>Tier 分布</h2>
          <div id="tierDist" class="bars"></div>
        </section>
        <section class="panel">
          <h2>来源分布</h2>
          <div id="sourceDist" class="bars"></div>
        </section>
        <section class="panel">
          <h2>章节 / 子课题</h2>
          <div id="chapterDist" class="bars"></div>
        </section>
        <section class="panel">
          <h2>读取深度</h2>
          <div id="readingDist" class="bars"></div>
        </section>
      </section>

      <section class="notice">
        <strong>证据边界：</strong>
        页面显式显示 reading depth。metadata_only / abstract_only 不能支撑强结论；正文证据裁决仍在 Step 7 完成。
      </section>

      <section id="resultArea" class="results" aria-live="polite"></section>
    </main>

    <script src="./data/dashboard-meta.js"></script>
    <script src="./data/search-results.js"></script>
    <script src="./app.js"></script>
  </body>
</html>
"""


STYLES_CSS = """* {
  box-sizing: border-box;
}

:root {
  color-scheme: light;
  --bg: #f6f7f8;
  --panel: #ffffff;
  --line: #d9dee5;
  --text: #1e252b;
  --muted: #65717d;
  --accent: #0f766e;
  --accent-soft: #d9f0ed;
  --blue: #2563eb;
  --amber: #b7791f;
  --red: #b42318;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--text);
}

button,
input,
select {
  font: inherit;
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  padding: 24px 32px;
  background: #ffffff;
  border-bottom: 1px solid var(--line);
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0;
}

h1 {
  margin: 0;
  font-size: 28px;
}

.subtitle {
  margin: 8px 0 0;
  color: var(--muted);
}

.stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  max-width: 560px;
}

.stat {
  min-width: 110px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  background: #fbfcfd;
  border-radius: 8px;
}

.stat strong {
  display: block;
  font-size: 22px;
}

.stat span {
  color: var(--muted);
  font-size: 12px;
}

.layout {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) auto;
  gap: 16px;
  align-items: end;
  margin-bottom: 16px;
}

.search-box span {
  display: block;
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 13px;
}

.search-box input {
  width: 100%;
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 12px;
  background: #fff;
}

.view-switch {
  display: flex;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.view-switch button {
  border: 0;
  border-left: 1px solid var(--line);
  background: transparent;
  padding: 10px 14px;
  cursor: pointer;
}

.view-switch button:first-child {
  border-left: 0;
}

.view-switch button.active {
  background: var(--accent);
  color: #fff;
}

.filters {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.filter label {
  display: block;
  margin-bottom: 5px;
  color: var(--muted);
  font-size: 12px;
}

.filter select {
  width: 100%;
  height: 38px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  padding: 0 10px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.panel,
.notice,
.results {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}

.panel {
  padding: 14px;
}

.panel h2 {
  margin: 0 0 10px;
  font-size: 15px;
}

.bars {
  display: grid;
  gap: 8px;
}

.bar-row {
  display: grid;
  grid-template-columns: minmax(72px, 1fr) minmax(80px, 2fr) 36px;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.bar-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-track {
  height: 8px;
  background: #e8edf2;
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  display: block;
  height: 100%;
  background: var(--accent);
}

.notice {
  padding: 12px 14px;
  margin-bottom: 16px;
  color: #42505c;
  background: #fffdf7;
  border-color: #ead9a8;
}

.results {
  overflow: hidden;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1180px;
}

th,
td {
  border-bottom: 1px solid var(--line);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
  font-size: 13px;
}

th {
  position: sticky;
  top: 0;
  background: #f8fafc;
  z-index: 1;
}

.title-cell {
  max-width: 360px;
}

.muted {
  color: var(--muted);
}

.badge {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eef2f7;
  color: #344150;
  font-size: 12px;
  white-space: nowrap;
}

.badge.t1 {
  background: #dff5e4;
  color: #116329;
}

.badge.t2 {
  background: #e0ecff;
  color: #174ea6;
}

.badge.t3 {
  background: #fff0d5;
  color: #8a4b10;
}

.badge.t4 {
  background: #ffe2df;
  color: var(--red);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 14px;
  padding: 14px;
}

.paper-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px;
  background: #fff;
}

.paper-card h3 {
  margin: 10px 0 8px;
  font-size: 16px;
}

.card-meta,
.card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.abstract {
  margin: 10px 0;
  color: #344150;
  font-size: 13px;
}

.paper-card dl {
  display: grid;
  gap: 6px;
  margin: 10px 0 0;
}

.paper-card dt {
  font-weight: 700;
}

.paper-card dd {
  margin: 0;
  color: #42505c;
}

.download-list {
  display: grid;
  gap: 10px;
  padding: 14px;
}

.download-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
}

.download-item strong {
  display: block;
  margin-bottom: 5px;
}

a {
  color: var(--blue);
}

.empty {
  padding: 28px;
  text-align: center;
  color: var(--muted);
}

@media (max-width: 980px) {
  .topbar,
  .toolbar {
    grid-template-columns: 1fr;
    display: grid;
  }

  .stats {
    justify-content: flex-start;
  }

  .filters,
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .layout,
  .topbar {
    padding: 16px;
  }

  .filters,
  .summary-grid,
  .card-grid {
    grid-template-columns: 1fr;
  }

  .view-switch {
    width: 100%;
  }

  .view-switch button {
    flex: 1;
  }
}
"""


APP_JS = """const records = window.STEP4_SEARCH_RESULTS || [];
const meta = window.STEP4_DASHBOARD_META || {};

const state = {
  view: "table",
  search: "",
  filters: {
    paper_tier: "All",
    source: "All",
    chapter_id: "All",
    search_task_id: "All",
    evidence_type: "All",
    evidence_role: "All",
    reading_depth: "All",
    content_fit: "All",
    download_hint: "All",
  },
};

const filterDefs = [
  ["paper_tier", "Tier"],
  ["source", "Source"],
  ["chapter_id", "Chapter"],
  ["search_task_id", "Search task"],
  ["evidence_type", "Evidence type"],
  ["evidence_role", "Evidence role"],
  ["reading_depth", "Reading depth"],
  ["content_fit", "Content fit"],
  ["download_hint", "Download hint"],
];

function valueFor(record, key) {
  if (key === "evidence_role") return record.paper_card?.evidence_role || "unknown";
  if (key === "reading_depth") return record.paper_card?.reading_depth || "metadata_only";
  if (key === "content_fit") return record.paper_card?.content_fit || "unknown";
  return record[key] || "unknown";
}

function tierClass(tier) {
  return String(tier || "").toLowerCase();
}

function badge(text, extra = "") {
  return `<span class="badge ${extra}">${escapeHtml(text || "unknown")}</span>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function truncate(value, limit) {
  const text = String(value || "");
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
}

function linkFor(record) {
  const href = record.article_url || record.oa_landing_url || (record.doi ? `https://doi.org/${record.doi}` : "");
  if (!href) return '<span class="muted">no url</span>';
  return `<a href="${escapeHtml(href)}" target="_blank" rel="noreferrer">open</a>`;
}

function searchableText(record) {
  return [
    record.title,
    (record.authors || []).join(" "),
    record.doi,
    record.source_id,
    record.article_url,
    record.abstract,
    record.paper_card?.primary_claim,
  ].join(" ").toLowerCase();
}

function filteredRecords() {
  const query = state.search.trim().toLowerCase();
  return records.filter((record) => {
    if (record.is_excluded && state.filters.paper_tier !== "T4") return false;
    if (query && !searchableText(record).includes(query)) return false;
    for (const [key] of filterDefs) {
      const selected = state.filters[key];
      if (selected !== "All" && valueFor(record, key) !== selected) return false;
    }
    return true;
  });
}

function countMap(items, getter) {
  const map = new Map();
  for (const item of items) {
    const value = getter(item) || "unknown";
    map.set(value, (map.get(value) || 0) + 1);
  }
  return [...map.entries()].sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])));
}

function renderStats(items) {
  const counts = meta.counts || {};
  const high = records.filter((r) => r.paper_tier === "T1").length;
  const medium = records.filter((r) => r.paper_tier === "T2").length;
  document.getElementById("stats").innerHTML = [
    ["当前显示", items.length],
    ["总记录", counts.total ?? records.length],
    ["T1", high],
    ["T2", medium],
    ["T4 excluded", counts.excluded_t4 ?? 0],
    ["需访问/补链", counts.needs_access ?? 0],
  ].map(([label, value]) => `<div class="stat"><strong>${value}</strong><span>${label}</span></div>`).join("");
}

function renderBars(id, entries) {
  const root = document.getElementById(id);
  const max = entries.length ? Math.max(...entries.map((entry) => entry[1])) : 0;
  root.innerHTML = entries.slice(0, 8).map(([label, count]) => {
    const width = max ? Math.max(8, Math.round((count / max) * 100)) : 0;
    return `
      <div class="bar-row">
        <span class="bar-label" title="${escapeHtml(label)}">${escapeHtml(label)}</span>
        <span class="bar-track"><span class="bar-fill" style="width: ${width}%"></span></span>
        <strong>${count}</strong>
      </div>
    `;
  }).join("") || '<p class="muted">No data</p>';
}

function renderDistributions(items) {
  renderBars("tierDist", countMap(records, (r) => r.paper_tier));
  renderBars("sourceDist", countMap(records, (r) => r.source));
  renderBars("chapterDist", countMap(records, (r) => r.chapter_id || "unmapped"));
  renderBars("readingDist", countMap(records, (r) => r.paper_card?.reading_depth || "metadata_only"));
}

function uniqueValues(key) {
  return countMap(records, (record) => valueFor(record, key)).map(([value]) => value);
}

function renderFilters() {
  const root = document.getElementById("filters");
  root.innerHTML = filterDefs.map(([key, label]) => {
    const options = ["All", ...uniqueValues(key)];
    return `
      <div class="filter">
        <label for="filter-${key}">${label}</label>
        <select id="filter-${key}" data-filter="${key}">
          ${options.map((value) => `<option value="${escapeHtml(value)}"${state.filters[key] === value ? " selected" : ""}>${escapeHtml(value)}</option>`).join("")}
        </select>
      </div>
    `;
  }).join("");
  for (const select of root.querySelectorAll("select")) {
    select.addEventListener("change", (event) => {
      state.filters[event.target.dataset.filter] = event.target.value;
      render();
    });
  }
}

function renderTable(items) {
  const rows = items.map((record) => `
    <tr>
      <td>${badge(record.paper_tier, tierClass(record.paper_tier))}</td>
      <td><code>${escapeHtml(record.record_id)}</code></td>
      <td class="title-cell">
        <strong>${escapeHtml(record.title)}</strong>
        <div class="muted">${escapeHtml((record.authors || []).join("; "))}</div>
      </td>
      <td>${escapeHtml(record.year)}</td>
      <td>${escapeHtml(record.source)}</td>
      <td>${escapeHtml(record.identifier || "missing")}</td>
      <td>${linkFor(record)}</td>
      <td>${escapeHtml(record.search_task_id || "unmapped")}</td>
      <td>${escapeHtml(record.chapter_id || "unmapped")}</td>
      <td>${escapeHtml(record.score)}</td>
      <td>${badge(record.paper_card?.reading_depth || "metadata_only")}</td>
      <td>${badge(record.paper_card?.evidence_role || "unknown")} ${badge(record.paper_card?.content_fit || "unknown")}</td>
      <td>${escapeHtml(record.download_hint)}</td>
    </tr>
  `).join("");
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Tier</th><th>record_id</th><th>Title</th><th>Year</th><th>Source</th>
            <th>DOI/source_id</th><th>URL</th><th>Task</th><th>Chapter</th><th>Score</th>
            <th>Reading</th><th>Paper card</th><th>Download</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderCards(items) {
  return `
    <div class="card-grid">
      ${items.map((record) => `
        <article class="paper-card">
          <div class="card-meta">
            ${badge(record.paper_tier, tierClass(record.paper_tier))}
            ${badge(record.source)}
            ${badge(record.paper_card?.reading_depth || "metadata_only")}
          </div>
          <h3>${escapeHtml(record.title)}</h3>
          <p class="muted">${escapeHtml(record.year)} · ${escapeHtml((record.authors || []).join("; "))}</p>
          <p class="abstract">${escapeHtml(truncate(record.abstract || "No abstract in workflow record.", 360))}</p>
          <dl>
            <div><dt>Stable ID</dt><dd><code>${escapeHtml(record.record_id)}</code></dd></div>
            <div><dt>DOI / Source ID</dt><dd>${escapeHtml(record.identifier || "missing")}</dd></div>
            <div><dt>Primary claim</dt><dd>${escapeHtml(record.paper_card?.primary_claim || "Not specified")}</dd></div>
            <div><dt>Content fit</dt><dd>${escapeHtml(record.paper_card?.content_fit || "unknown")} · ${escapeHtml(record.paper_card?.content_fit_note || "")}</dd></div>
          </dl>
          <div class="card-actions">${linkFor(record)} ${record.oa_pdf_url ? `<a href="${escapeHtml(record.oa_pdf_url)}" target="_blank" rel="noreferrer">OA PDF</a>` : ""}</div>
        </article>
      `).join("")}
    </div>
  `;
}

function renderDownload(items) {
  const targets = items.filter((record) => ["T1", "T2"].includes(record.paper_tier));
  return `
    <div class="download-list">
      ${targets.map((record) => `
        <article class="download-item">
          <div>
            <strong>${escapeHtml(record.title)}</strong>
            <div class="muted">
              ${escapeHtml(record.paper_tier)} · ${escapeHtml(record.source)} · ${escapeHtml(record.download_hint)}
              ${record.needs_access ? " · 需要访问/补链" : ""}
            </div>
            <div class="muted">record_id: <code>${escapeHtml(record.record_id)}</code> · DOI/source_id: ${escapeHtml(record.identifier || "missing")}</div>
            <div class="muted">article_url: ${record.article_url ? `<a href="${escapeHtml(record.article_url)}" target="_blank" rel="noreferrer">${escapeHtml(truncate(record.article_url, 90))}</a>` : "missing"}</div>
            <div class="muted">OA PDF: ${record.oa_pdf_url ? `<a href="${escapeHtml(record.oa_pdf_url)}" target="_blank" rel="noreferrer">${escapeHtml(truncate(record.oa_pdf_url, 90))}</a>` : "none"}</div>
          </div>
          <div>${badge(record.paper_card?.reading_depth || "metadata_only")}</div>
        </article>
      `).join("") || '<div class="empty">No T1/T2 records match current filters.</div>'}
    </div>
  `;
}

function renderResults(items) {
  const root = document.getElementById("resultArea");
  if (!items.length) {
    root.innerHTML = '<div class="empty">No matching records.</div>';
    return;
  }
  if (state.view === "cards") root.innerHTML = renderCards(items);
  else if (state.view === "download") root.innerHTML = renderDownload(items);
  else root.innerHTML = renderTable(items);
}

function setView(view) {
  state.view = view;
  document.getElementById("tableViewBtn").classList.toggle("active", view === "table");
  document.getElementById("cardViewBtn").classList.toggle("active", view === "cards");
  document.getElementById("downloadViewBtn").classList.toggle("active", view === "download");
  render();
}

function render() {
  const items = filteredRecords();
  renderStats(items);
  renderDistributions(items);
  renderResults(items);
}

document.getElementById("searchInput").addEventListener("input", (event) => {
  state.search = event.target.value;
  render();
});
document.getElementById("tableViewBtn").addEventListener("click", () => setView("table"));
document.getElementById("cardViewBtn").addEventListener("click", () => setView("cards"));
document.getElementById("downloadViewBtn").addEventListener("click", () => setView("download"));

renderFilters();
render();
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a static Step 4 dashboard from workflow_search_results.json.")
    parser.add_argument("--workflow-inputs", required=True, type=Path, help="Path to workflow_search_results.json")
    parser.add_argument("--output-dir", required=True, type=Path, help="Output directory, usually step4-dashboard")
    parser.add_argument("--force", action="store_true", help="Replace an existing dashboard directory.")
    args = parser.parse_args()

    result = export_dashboard(args.workflow_inputs, args.output_dir, force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
