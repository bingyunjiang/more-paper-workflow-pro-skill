#!/usr/bin/env python3
"""Best-effort enrichment for missing English abstracts.

Scope:
  - Only English/non-Chinese sources
  - Only T1/T2 records
  - Only records whose abstract is empty
  - No institutional login required

Strategy:
  1. OpenAlex by DOI
  2. Crossref by DOI
  3. Mark record raw.abstract_enrichment_status when still missing
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from workflow_contracts import load_json, load_search_records


ENGLISH_SOURCES = {"openalex", "crossref", "semantic_scholar", "arxiv", "pubmed"}


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    if not inverted_index:
        return ""
    positions = {}
    for word, pos_list in inverted_index.items():
        for pos in pos_list:
            positions[pos] = word
    if not positions:
        return ""
    return " ".join(positions[i] for i in sorted(positions))


def _strip_jats(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    return " ".join(cleaned.split())


def _fetch_openalex_abstract(doi: str) -> str:
    doi_clean = doi.strip().replace("https://doi.org/", "")
    url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi_clean)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return _reconstruct_abstract(data.get("abstract_inverted_index"))


def _fetch_crossref_abstract(doi: str) -> str:
    doi_clean = doi.strip().replace("https://doi.org/", "")
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi_clean)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0 (mailto:research@example.com)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    message = data.get("message", {})
    return _strip_jats(message.get("abstract", "") or "")


def should_enrich(record: dict) -> bool:
    source = (record.get("source") or "").lower()
    paper_tier = (record.get("paper_tier") or "").replace(" ", "").upper()
    abstract = (record.get("abstract") or "").strip()
    return source in ENGLISH_SOURCES and paper_tier in {"T1", "T2", "TIER1", "TIER2"} and not abstract


def enrich_record(record: dict) -> tuple[bool, str]:
    doi = (record.get("doi") or "").strip()
    raw = record.setdefault("raw", {})
    if not doi:
        raw["abstract_enrichment_status"] = "skipped_no_doi"
        return False, "no_doi"

    try:
        abstract = _fetch_openalex_abstract(doi)
        if abstract:
            record["abstract"] = abstract
            raw["abstract_enrichment_status"] = "openalex"
            return True, "openalex"
    except Exception:
        pass

    try:
        abstract = _fetch_crossref_abstract(doi)
        if abstract:
            record["abstract"] = abstract
            raw["abstract_enrichment_status"] = "crossref"
            return True, "crossref"
    except Exception:
        pass

    raw["abstract_enrichment_status"] = "missing_after_enrichment"
    return False, "missing"


def main() -> None:
    parser = argparse.ArgumentParser(description="Best-effort enrichment for missing English abstracts in workflow JSON.")
    parser.add_argument("--input", required=True, type=Path, help="Input workflow_search_results.json")
    parser.add_argument("--output", type=Path, help="Output path (default: overwrite input)")
    args = parser.parse_args()

    payload = load_json(args.input)
    if not isinstance(payload, dict):
        raise SystemExit("Input workflow JSON must be an object")

    records = payload.get("records") or []
    enriched = 0
    attempted = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        if not should_enrich(record):
            continue
        attempted += 1
        changed, _ = enrich_record(record)
        if changed:
            enriched += 1

    meta = payload.setdefault("metadata", {})
    meta["english_abstract_enrichment_attempted"] = attempted
    meta["english_abstract_enrichment_succeeded"] = enriched

    out = args.output or args.input
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ATTEMPTED {attempted}")
    print(f"ENRICHED {enriched}")
    print(f"OUTPUT {out}")


if __name__ == "__main__":
    main()
