#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 - Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Unified PDF download router - single entry point for all publishers.

Routes each DOI to the optimal download strategy using the publisher
routing matrix, then orchestrates download rounds:

  1. Sci-Hub CDP    -> pre-2021 papers (free, ~6s/paper)
  2. Generic CDP    -> Elsevier/ScienceDirect, IEEE, and other publishers
                     (Wiley, ACS, RSC, Nature, Springer, etc.)
                     IEEE uses generic engine (strategy B: article page
                     -> stamp URL extraction). Dedicated download_via_ieee.py
                     available as fallback for interactive SSO login flow.

Usage:
  python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/
  python3 scripts/unified_download_router.py dois.txt --port 9223
  python3 scripts/unified_download_router.py --papers DOI1,DOI2 --port 9223
  python3 scripts/unified_download_router.py --test 10.1021/acsnano.4c00001 --port 9223
  python3 scripts/unified_download_router.py --check-session --port 9223
"""

from __future__ import annotations

import sys, os, time, re, json, argparse, subprocess, hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

# Ensure scripts/ is on path
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from cdp_utils import (
    cdp_browser_matches,
    check_cdp,
    check_required_deps,
    get_cdp_browser_product,
    start_persistent_cdp_browser,
)
from console_compat import (
    ARROW,
    DONE,
    FAIL,
    OK,
    SKIP,
    WARN,
    configure_child_python_utf8_env,
    configure_console_output,
)
from generic_publisher_downloader import (
    resolve_publisher, download_one as generic_download_one,
    check_publisher_session, describe_publisher_session, _PUBLISHER_CONFIGS, extract_dois,
)
from sd_download import diagnose_sd_pii
from workflow_contracts import (
    as_chinese_papers,
    dois_from_download_items,
    download_items_from_search_records,
    load_download_manifest,
    load_search_records,
)

# ── Constants ───────────────────────────────────────────────────────────────

CDP_PORT = 9223
DEFAULT_OUTPUT = "paper-temp"
SCI_HUB_CUTOFF_YEAR = 2021  # Sci-Hub has very few papers after 2020

# Strategy routing table (for display and decisions)
STRATEGY_ORDER = ["scihub", "ieee_cdp", "generic", "chinese_cdp", "direct_http", "skip"]

# Chinese CDP publishers (identified by strategy, not DOI prefix)
CHINESE_PUBLISHERS = {"cnki", "wanfang"}

# Chinese paper entry schema (from literature table or JSON)
# Each entry: {"title": str, "source": "cnki"|"wanfang", "article_url": str, "doi": str}
CHINESE_PAPER_FIELDS = frozenset({"title", "source", "article_url"})


def ensure_cdp_running(port: int, browser: str = "chrome") -> bool:
    """Reuse an existing CDP browser only when it matches the requested browser."""
    browser = (browser or "chrome").lower()
    if check_cdp(port):
        if cdp_browser_matches(port, browser):
            return True
        product = get_cdp_browser_product(port) or "unknown browser"
        print(f"\nCDP port :{port} is {product}, but {browser.title()} was requested. Restarting {browser.title()}...")
    else:
        print(f"\nCDP {browser.title()} not detected on :{port}. Starting browser automatically...")
    start_persistent_cdp_browser(
        port=port,
        browser=browser,
        urls=["https://www.sciencedirect.com/"],
    )
    ok = check_cdp(port) and cdp_browser_matches(port, browser)
    if not ok:
        print(f"  {FAIL} CDP browser failed to start.")
        print("     Windows: set CHROME_PATH or EDGE_PATH if browser auto-detection fails.")
    return ok


# ── Year Estimation ─────────────────────────────────────────────────────────

def estimate_year(doi: str) -> Optional[int]:
    """Estimate publication year from DOI patterns. Returns int or None.

    DOIs often embed the year, e.g.:
      - 10.1016/j.jpowsour.2019.01.052 -> 2019
      - 10.1109/tvt.2022.3183866 -> 2022
      - 10.1002/ente.202301205 -> 2023 (year embedded in larger number)
      - 10.1038/s41467-2024-45578 -> 2024

    We scan the part AFTER the first '/' for 4-digit numbers in the
    publication-year range (1990–2026), skipping the DOI prefix.
    """
    # Split: "10.1016/j.jpowsour.2019.01.052" -> prefix="10.1016", rest="j.jpowsour.2019.01.052"
    parts = doi.split("/", 1)
    search_region = parts[1] if len(parts) > 1 else doi

    # Find all 4-digit numbers in the search region, return the first valid year
    for m in re.finditer(r'\d{4}', search_region):
        year = int(m.group(0))
        if 1990 <= year <= 2026:
            return year
    return None


# ── DOI Classification ──────────────────────────────────────────────────────

def classify_doi(doi: str) -> dict:
    """Classify a DOI into a download strategy category.
    Returns dict with: doi, strategy, publisher_name, year, reason"""
    publisher = resolve_publisher(doi)
    pub_name = publisher.get("_key", "unknown") if publisher else "unknown"
    strategy = publisher.get("strategy", "generic") if publisher else "generic"
    year = estimate_year(doi)

    return {
        "doi": doi,
        "strategy": strategy,
        "publisher": pub_name,
        "year": year,
        "publisher_config": publisher or {},
    }


# ── Input Parsing ───────────────────────────────────────────────────────────

def parse_input(input_path: str) -> list[str]:
    """Extract DOIs from a file. Supports:
    - Plain text (one DOI per line or inline)
    - Markdown literature tables (检索文献表.md)
    - BibTeX (.bib files)
    """
    path = Path(input_path)
    if not path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    dois = extract_dois(input_path)
    if not dois:
        print(f"ERROR: No DOIs found in {input_path}")
        sys.exit(1)
    return dois


def _parse_bibtex_fields(entry: str) -> dict[str, str]:
    """Extract simple BibTeX key/value fields used for routing decisions."""
    fields: dict[str, str] = {}
    for match in re.finditer(r'(?m)^\s*([A-Za-z_][\w-]*)\s*=\s*([{\"])(.*?)[}\"],?\s*$', entry):
        fields[match.group(1).lower()] = match.group(3).strip()
    return fields


def _split_bibtex_entries(text: str) -> list[str]:
    """Split BibTeX text into top-level entries without a full parser."""
    entries: list[str] = []
    start: Optional[int] = None
    depth = 0
    for i, ch in enumerate(text):
        if ch == "@" and depth == 0:
            start = i
        if start is None:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                entries.append(text[start:i + 1])
                start = None
    return entries


def _is_chinese_bibtex_entry(fields: dict[str, str]) -> bool:
    doi = fields.get("doi", "").lower()
    haystack = " ".join(fields.get(k, "") for k in ("title", "journal", "school", "langid")).lower()
    if fields.get("langid", "").lower() in ("chinese", "zh", "zh-cn"):
        return True
    if doi.startswith(("10.16638/j.cnki", "10.14044/j.1674-1757")):
        return True
    return bool(re.search(r"[\u4e00-\u9fff]", haystack))


def parse_bibtex_chinese_papers(input_path: str) -> list[dict]:
    """Extract Chinese BibTeX entries so they do not fall through to Generic CDP."""
    path = Path(input_path)
    if path.suffix.lower() != ".bib" or not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    papers: list[dict] = []
    for entry in _split_bibtex_entries(text):
        fields = _parse_bibtex_fields(entry)
        doi = fields.get("doi", "").strip()
        if not doi or not _is_chinese_bibtex_entry(fields):
            continue
        url = fields.get("article_url") or fields.get("url", "")
        if not url and doi:
            url = f"https://doi.org/{doi}"
        source = "cnki" if "cnki" in doi.lower() or "cnki" in url.lower() else "cnki"
        papers.append({
            "title": fields.get("title", ""),
            "source": source,
            "article_url": url if url.startswith("http") else "",
            "doi": doi,
        })
    return papers


def parse_doi_file(input_path: str) -> list[str]:
    """Read one DOI per line from a plain text file."""
    path = Path(input_path)
    if not path.exists():
        print(f"ERROR: DOI file not found: {input_path}")
        sys.exit(1)
    dois = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line:
            dois.append(line)
    if not dois:
        print(f"ERROR: No DOIs found in DOI file: {input_path}")
        sys.exit(1)
    return dois


# ── Chinese Paper Parsing ────────────────────────────────────────────────────

def parse_chinese_papers(input_path: str) -> list[dict]:
    """Extract Chinese papers (CNKI/Wanfang) from literature table or JSON.

    For Markdown literature tables, reads rows where the source column
    is 'cnki' or 'wanfang'. Extracts title, DOI/synthetic-ID, and
    any article URL present.

    For JSON files, expects:
      [{"title": "...", "source": "cnki"|"wanfang",
        "article_url": "https://...", "doi": "10.xxxx/..."}, ...]

    Returns list of {title, source, article_url, doi} dicts.
    """
    path = Path(input_path)
    if not path.exists():
        print(f"ERROR: Chinese input file not found: {input_path}")
        sys.exit(1)

    text = path.read_text(encoding="utf-8", errors="replace")

    # Try JSON first
    stripped = text.strip()
    if stripped.startswith("[") or stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict) and "papers" in data:
                data = data["papers"]
            if not isinstance(data, list):
                print("ERROR: Chinese JSON must be a list of paper objects.")
                sys.exit(1)
            papers = []
            for item in data:
                if isinstance(item, dict) and item.get("source", "").lower() in ("cnki", "wanfang"):
                    papers.append({
                        "title": item.get("title", ""),
                        "source": item["source"].lower(),
                        "article_url": item.get("article_url", item.get("url", "")),
                        "doi": item.get("doi") or item.get("source_id", ""),
                    })
            return papers
        except json.JSONDecodeError:
            pass  # Not JSON, fall through to Markdown parsing

    # Markdown table parsing
    papers = []
    in_table = False
    headers: list[str] = []
    source_col = -1
    title_col = -1
    doi_col = -1
    url_col = -1

    for line in text.split("\n"):
        # Detect table header row
        if "|" in line and not in_table:
            parts = [p.strip() for p in line.split("|")]
            # Skip separator lines (|---|---|)
            if all(re.match(r'^[-:]+$', p) for p in parts if p):
                continue
            headers = parts
            # Find column indices (case-insensitive)
            for i, h in enumerate(headers):
                hl = h.lower()
                if hl in ("来源", "source"):
                    source_col = i
                elif hl in ("标题", "title", "论文标题"):
                    title_col = i
                elif hl in ("doi", "doi/url", "doi/source_id", "source_id"):
                    doi_col = i
                elif hl in ("文章链接", "url", "article_url", "详情链接"):
                    url_col = i
            if source_col >= 0:
                in_table = True
            continue

        if not in_table:
            continue

        # End of table: blank line or new heading
        if not line.strip() or line.startswith("##"):
            in_table = False
            continue

        # Skip separator lines inside table
        parts = [p.strip() for p in line.split("|")]
        if all(re.match(r'^[-:]+$', p) for p in parts if p):
            continue

        if source_col >= len(parts):
            continue

        source_val = parts[source_col].strip().lower()
        if source_val not in ("cnki", "wanfang"):
            continue

        title = parts[title_col].strip() if 0 <= title_col < len(parts) else ""
        # Clean markdown link formatting from title
        title = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', title)

        doi = parts[doi_col].strip() if 0 <= doi_col < len(parts) else ""
        # Extract DOI from markdown link if present
        doi_m = re.search(r'(10\.\d{4,}/[^\s<")]+|cnki\.\w+|wanfang\.\w+)', doi)
        doi = doi_m.group(1) if doi_m else doi

        article_url = parts[url_col].strip() if 0 <= url_col < len(parts) else ""
        # Extract URL from markdown link
        url_m = re.search(r'\]\(([^)]+)\)', article_url) or re.search(r'(https?://[^\s)]+)', article_url)
        if url_m and not article_url.startswith("http"):
            article_url = url_m.group(1)

        if title:
            papers.append({
                "title": title,
                "source": source_val,
                "article_url": article_url,
                "doi": doi,
            })

    return papers


# ── Round Executors ─────────────────────────────────────────────────────────

def run_scihub_round(dois: list[str], output_dir: str, port: int) -> tuple[list[str], list[str]]:
    """Round 1: Try Sci-Hub for pre-2021 papers.
    Returns (downloaded_dois, remaining_dois)."""
    old_dois = []
    new_dois = []
    for d in dois:
        year = estimate_year(d)
        if year and year <= SCI_HUB_CUTOFF_YEAR:
            old_dois.append(d)
        else:
            new_dois.append(d)

    if not old_dois:
        print(f"\n{SKIP} Round 1 (Sci-Hub): No pre-{SCI_HUB_CUTOFF_YEAR} papers to try ({len(new_dois)} papers are post-{SCI_HUB_CUTOFF_YEAR-1}).")
        return [], dois

    print(f"\n{'='*60}")
    print(f"Round 1: Sci-Hub CDP ({len(old_dois)} pre-{SCI_HUB_CUTOFF_YEAR} papers)")
    print(f"{'='*60}")

    # Write temp DOI list for scihub script
    scihub_input = os.path.join(output_dir, ".scihub_input.txt")
    os.makedirs(output_dir, exist_ok=True)
    with open(scihub_input, "w", encoding="utf-8") as f:
        for d in old_dois:
            f.write(d + "\n")

    scihub_script = SCRIPTS_DIR / "download_via_scihub.py"
    if not scihub_script.exists():
        print(f"  WARNING: {scihub_script} not found - skipping Sci-Hub round.")
        return [], dois

    try:
        subprocess.run(
            [sys.executable, str(scihub_script), scihub_input,
             "--output", output_dir, "--port", str(port)],
            check=False, timeout=600, env=configure_child_python_utf8_env()
        )
    except subprocess.TimeoutExpired:
        print(f"  {WARN} Sci-Hub round timed out after 10 minutes.")

    # Check which papers now exist on disk
    downloaded = []
    remaining = list(new_dois)  # post-2021 papers always go to next round
    for d in old_dois:
        basename = d.replace("/", "_").replace(":", "_")
        fpath = os.path.join(output_dir, f"{basename}.pdf")
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            downloaded.append(d)
        else:
            remaining.append(d)

    print(f"  Sci-Hub result: {OK} {len(downloaded)} downloaded, {ARROW} {len(old_dois) - len(downloaded)} remaining for next round")

    # Cleanup
    try:
        os.remove(scihub_input)
    except Exception:
        pass

    return downloaded, remaining


def run_sd_round(dois: list[str], output_dir: str, port: int,
                 sd_browser: str = "chrome") -> tuple[list[str], list[str], dict[str, str]]:
    """Legacy standalone ScienceDirect CDP round.

    Main routing now sends 10.1016/ papers through Generic CDP, which calls
    the ScienceDirect adapter internally.

    Returns (downloaded_dois, remaining_dois)."""
    sd_dois = []
    other_dois = []
    for d in dois:
        pub = resolve_publisher(d)
        strategy = pub.get("strategy", "generic") if pub else "generic"
        # Check if it's an SD DOI (with PII resolvable) or if publisher says sd_cdp
        if strategy == "sd_cdp":
            sd_dois.append(d)
        else:
            other_dois.append(d)

    if not sd_dois:
        print(f"\n{SKIP} Round 2 (SD CDP): No Elsevier papers remaining.")
        return [], dois, {}

    print(f"\n{'='*60}")
    print(f"Round 2: ScienceDirect CDP ({len(sd_dois)} Elsevier papers)")
    print(f"{'='*60}")

    # First resolve PII via batch_resolve_pii.py
    sd_input = os.path.join(output_dir, ".sd_input.txt")
    pii_map_path = os.path.join(output_dir, "sd_pii_map.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(sd_input, "w", encoding="utf-8") as f:
        for d in sd_dois:
            f.write(d + "\n")

    batch_pii_script = SCRIPTS_DIR / "batch_resolve_pii.py"
    if batch_pii_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(batch_pii_script), sd_input,
                 "--output", pii_map_path],
                check=False, timeout=300, env=configure_child_python_utf8_env()
            )
        except subprocess.TimeoutExpired:
            print(f"  {WARN} PII resolution timed out.")
    else:
        print(f"  WARNING: {batch_pii_script} not found - cannot resolve PII for SD.")

    # Download via auto_sd_downloader
    auto_sd_script = SCRIPTS_DIR / "auto_sd_downloader.py"
    if auto_sd_script.exists() and os.path.exists(pii_map_path):
        auto_sd_cmd = [
            sys.executable, str(auto_sd_script),
            "--output-dir", output_dir,
            "--pii-map", pii_map_path,
            "--browser", sd_browser,
        ]
        if sd_browser == "edge":
            auto_sd_cmd.extend(["--port-edge", str(port)])
        else:
            auto_sd_cmd.extend(["--port-chrome", str(port)])
        try:
            subprocess.run(
                auto_sd_cmd,
                check=False, timeout=1800, env=configure_child_python_utf8_env()
            )
        except subprocess.TimeoutExpired:
            print(f"  {WARN} SD download timed out after 30 minutes.")
    elif not os.path.exists(pii_map_path):
        print(f"  {WARN} PII map not found - skipping SD download.")

    # Check results
    downloaded = []
    remaining = list(other_dois)
    failure_reasons: dict[str, str] = {}
    pii_map: dict[str, dict] = {}
    if os.path.exists(pii_map_path):
        try:
            pii_map = json.loads(Path(pii_map_path).read_text(encoding="utf-8")).get("resolved", {})
        except Exception:
            pii_map = {}
    for d in sd_dois:
        basename = d.replace("/", "_").replace(":", "_")
        fpath = os.path.join(output_dir, f"{basename}.pdf")
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            downloaded.append(d)
        else:
            remaining.append(d)
            pii = pii_map.get(basename, {}).get("pii")
            if pii:
                diag = diagnose_sd_pii(port, pii)
                if diag["kind"] == "manual_verification_required":
                    failure_reasons[d] = "manual_verification_required"
                elif diag["kind"] == "referencework_abs":
                    failure_reasons[d] = "not_subscribed_or_referencework"
                elif diag["kind"] == "article_page_only":
                    failure_reasons[d] = "article_page_no_pdf_route"
                else:
                    failure_reasons[d] = "sd_failed_unknown"
            else:
                failure_reasons[d] = "pii_resolution_failed"

    print(f"  SD result: {OK} {len(downloaded)} downloaded, {ARROW} {len(sd_dois) - len(downloaded)} remaining for next round")

    try:
        os.remove(sd_input)
    except Exception:
        pass

    return downloaded, remaining, failure_reasons


def run_ieee_round(dois: list[str], output_dir: str, port: int) -> tuple[list[str], list[str]]:
    """Round 3 (fallback): IEEE CDP for 10.1109/ papers.

    NOTE: IEEE is now handled by Round 2 (Generic CDP) via publishers.toml
    strategy="generic". This round is a fallback that only triggers if
    the publisher config is overridden to strategy="ieee_cdp" or when
    download_via_ieee.py is invoked directly for interactive SSO login.
    Returns (downloaded_dois, remaining_dois)."""
    ieee_dois = []
    other_dois = []
    for d in dois:
        pub = resolve_publisher(d)
        strategy = pub.get("strategy", "generic") if pub else "generic"
        if strategy == "ieee_cdp":
            ieee_dois.append(d)
        else:
            other_dois.append(d)

    if not ieee_dois:
        print(f"\n{SKIP} Round 3 (IEEE CDP): No IEEE papers remaining.")
        return [], dois

    print(f"\n{'='*60}")
    print(f"Round 3: IEEE CDP ({len(ieee_dois)} IEEE papers)")
    print(f"{'='*60}")

    ieee_script = SCRIPTS_DIR / "download_via_ieee.py"
    if not ieee_script.exists():
        print(f"  WARNING: {ieee_script} not found - skipping IEEE round.")
        return [], dois

    # Write temp input
    ieee_input = os.path.join(output_dir, ".ieee_input.txt")
    os.makedirs(output_dir, exist_ok=True)
    with open(ieee_input, "w", encoding="utf-8") as f:
        for d in ieee_dois:
            f.write(d + "\n")

    try:
        subprocess.run(
            [sys.executable, str(ieee_script), ieee_input,
             "--output", output_dir, "--port", str(port),
             "--skip-session-check"],
            check=False, timeout=900, env=configure_child_python_utf8_env()
        )
    except subprocess.TimeoutExpired:
        print(f"  {WARN} IEEE round timed out after 15 minutes.")

    # Check results - IEEE uses arnumber_DOI.pdf naming
    downloaded = []
    remaining = list(other_dois)
    for d in ieee_dois:
        basename = d.replace("/", "_").replace(":", "_").replace("/", "_")
        # Look for any file containing the DOI basename
        found = False
        for f in os.listdir(output_dir) if os.path.exists(output_dir) else []:
            if basename in f and f.endswith(".pdf"):
                fpath = os.path.join(output_dir, f)
                if os.path.getsize(fpath) > 5000:
                    downloaded.append(d)
                    found = True
                    break
        if not found:
            remaining.append(d)

    print(f"  IEEE result: {OK} {len(downloaded)} downloaded, {ARROW} {len(ieee_dois) - len(downloaded)} remaining for next round")

    try:
        os.remove(ieee_input)
    except Exception:
        pass

    return downloaded, remaining


def run_generic_round(dois: list[str], output_dir: str, port: int,
                      include_si: bool = False) -> tuple[list[str], list[str], dict[str, str]]:
    """Round 2: Generic CDP for all remaining publishers.
    Returns (downloaded_dois, remaining_dois)."""
    # Filter: generic + direct_http publishers only
    generic_dois = []
    skip_dois = []
    for d in dois:
        pub = resolve_publisher(d)
        strategy = pub.get("strategy", "generic") if pub else "generic"
        if strategy in ("generic", "direct_http"):
            generic_dois.append(d)
        elif strategy == "skip":
            skip_dois.append(d)
        else:
            # SD or IEEE that weren't caught earlier - still try generic
            generic_dois.append(d)

    if not generic_dois:
        if skip_dois:
            print(f"\n{SKIP} Round 2 (Generic CDP): {len(skip_dois)} papers skipped (MDPI/unavailable), 0 eligible.")
        else:
            print(f"\n{SKIP} Round 2 (Generic CDP): No remaining papers.")
        return [], dois, {}

    print(f"\n{'='*60}")
    print(f"Round 2: Generic Publisher CDP ({len(generic_dois)} papers)")
    print(f"{'='*60}")

    ok, fail = 0, 0
    downloaded = []
    remaining = []
    failure_reasons: dict[str, str] = {}

    for i, doi in enumerate(generic_dois):
        pub = resolve_publisher(doi)
        pub_name = pub.get("_key", "unknown") if pub else "unknown"
        publisher_domain = pub.get("publisher_domain", "?") if pub else "?"

        print(f"  [{i+1}/{len(generic_dois)}] {doi[:50]} {ARROW} {pub_name} ({publisher_domain})", end=" ", flush=True)

        t0 = time.time()
        try:
            result_path, status, _ = generic_download_one(
                port, doi, output_dir, include_si=include_si
            )
        except Exception as e:
            if ensure_cdp_running(port):
                try:
                    result_path, status, _ = generic_download_one(
                        port, doi, output_dir, include_si=include_si
                    )
                except Exception:
                    result_path, status = None, "failed"
            else:
                result_path, status = None, "failed"
            print(f"\n  {WARN} Retry after error: {type(e).__name__}")
        elapsed = time.time() - t0

        if result_path and status == "ok":
            size_kb = os.path.getsize(result_path) // 1024
            print(f"{OK} ({size_kb}KB, {elapsed:.1f}s)")
            downloaded.append(doi)
            ok += 1
        elif status in (
            "manual_required",
            "captcha_required",
            "institution_login_required",
            "pdf_probe_unknown",
            "access_denied",
            "login_required",
        ):
            print(f"{WARN} manual confirmation needed ({elapsed:.1f}s)")
            print(f"  {ARROW} {pub_name} 需要你现在去可见 Chrome 完成机构登录/验证；完成后可继续重跑剩余列表。")
            remaining.append(doi)
            fail += 1
            failure_reasons[doi] = status
        elif status == "si_only":
            print(f"{WARN} SI only ({elapsed:.1f}s)")
            remaining.append(doi)
            fail += 1
            failure_reasons[doi] = "supplementary_only"
        elif status in ("pii_resolution_failed", "not_subscribed_or_referencework", "article_page_no_pdf_route"):
            print(f"{FAIL} ({status}, {elapsed:.1f}s)")
            remaining.append(doi)
            fail += 1
            failure_reasons[doi] = status
        else:
            print(f"{FAIL} ({elapsed:.1f}s)")
            remaining.append(doi)
            fail += 1
            failure_reasons[doi] = "generic_failed"

    # Remaining = failures + skips
    remaining = remaining + skip_dois
    print(f"  Generic result: {OK} {ok} downloaded, {FAIL} {fail} failed, {SKIP} {len(skip_dois)} skipped")

    return downloaded, remaining, failure_reasons


# ── Chinese Round ────────────────────────────────────────────────────────────

def run_chinese_round(papers: list[dict], output_dir: str, port: int) -> tuple[list[str], list[str]]:
    """Chinese CDP download round for CNKI and Wanfang papers.

    Each paper dict must have: title, source (cnki|wanfang), article_url.
    Uses the generic_publisher_downloader engine with publisher override
    set to the matching Chinese publisher config.

    Args:
        papers: List of {title, source, article_url, doi} dicts.
        output_dir: Directory to save downloaded PDFs.
        port: CDP Chrome debug port.

    Returns: (downloaded_dois, remaining_dois).
    """
    if not papers:
        print(f"\n{SKIP} Chinese Round: No Chinese papers to download.")
        return [], []

    print(f"\n{'='*60}")
    print(f"Chinese Round: CNKI / Wanfang CDP ({len(papers)} papers)")
    print(f"{'='*60}")

    # Map source name to publisher config key
    source_to_pub = {"cnki": "cnki", "wanfang": "wanfang"}

    ok, fail, skipped = 0, 0, 0
    downloaded = []
    remaining = []

    for i, paper in enumerate(papers):
        title = paper.get("title", f"paper_{i+1}")
        source = paper.get("source", "").lower()
        article_url = paper.get("article_url", "")
        doi = paper.get("doi", "")

        # Shorten title for display
        display_title = title[:45] + ("..." if len(title) > 45 else "")

        print(f"  [{i+1}/{len(papers)}] [{source.upper():6s}] {display_title}", end=" ", flush=True)

        if not article_url:
            print(f"{FAIL} (no article URL - cannot download)")
            remaining.append(doi or title)
            skipped += 1
            continue

        t0 = time.time()

        # Override publisher resolution: map source to Chinese publisher config
        pub_key = source_to_pub.get(source, source)
        publisher = resolve_publisher(doi) if doi else None
        if publisher is None or publisher.get("strategy") != "chinese_cdp":
            # Force publisher to Chinese config
            from generic_publisher_downloader import _PUBLISHER_CONFIGS
            publisher = _PUBLISHER_CONFIGS.get(pub_key, {"strategy": "chinese_cdp", "_key": pub_key})

        result_path, status, _ = generic_download_one(
            port, doi or f"{source}.{hashlib.md5(title.encode()).hexdigest()[:12]}",
            output_dir, article_url=article_url
        )
        elapsed = time.time() - t0

        if result_path and status == "ok":
            size_kb = os.path.getsize(result_path) // 1024
            print(f"{OK} ({size_kb}KB, {elapsed:.1f}s)")
            downloaded.append(doi or title)
            ok += 1
        elif status == "no_url":
            print(f"{FAIL} (no article URL)")
            remaining.append(doi or title)
            skipped += 1
        else:
            print(f"{FAIL} ({elapsed:.1f}s)")
            remaining.append(doi or title)
            fail += 1

    print(f"  Chinese result: {OK} {ok} downloaded, {FAIL} {fail} failed, {SKIP} {skipped} skipped (no URL)")

    return downloaded, remaining


# ── English Pipeline (R1->R2->R3 sequential) ────────────────────────────────

def run_english_pipeline(dois: list[str], output_dir: str, port: int,
                         skip_scihub: bool = False, skip_sd: bool = False,
                         include_si: bool = False,
                         sd_browser: str = "chrome") -> tuple[list[str], list[str], list[dict], dict[str, str]]:
    """Run English download pipeline: R1 Sci-Hub -> R2 Generic CDP.

    Designed to be called in parallel with run_chinese_round() via
    ThreadPoolExecutor, sharing the same CDP port.

    Args:
        dois: List of DOIs to download.
        output_dir: Directory to save PDFs.
        port: CDP Chrome debug port.
        skip_scihub: Skip Sci-Hub round.
        skip_sd: Backward-compatible no-op; ScienceDirect now flows through Generic CDP.
        include_si: Download supplementary info where available.

    Returns:
        (downloaded, remaining, round_results) tuple.
    """
    all_downloaded: list[str] = []
    round_results: list[dict] = []
    remaining = list(dois)
    failure_reasons: dict[str, str] = {}

    # Round 1: Sci-Hub
    if not skip_scihub:
        downloaded, remaining = run_scihub_round(remaining, output_dir, port)
        all_downloaded.extend(downloaded)
        round_results.append({"round": "Sci-Hub", "downloaded": downloaded})
    else:
        print(f"\n{SKIP} Round 1 (Sci-Hub): Skipped (--skip-scihub)")

    if not remaining:
        print(f"\n{DONE} English pipeline complete - all {len(all_downloaded)}/{len(dois)} downloaded!")
        return all_downloaded, remaining, round_results, failure_reasons

    if skip_sd:
        print(f"\n{SKIP} --skip-sd ignored: ScienceDirect is handled inside Generic CDP.")

    # Round 2: Generic CDP (ScienceDirect and IEEE included here)
    downloaded, remaining, generic_failures = run_generic_round(
        remaining, output_dir, port, include_si=include_si
    )
    all_downloaded.extend(downloaded)
    round_results.append({"round": "Generic CDP", "downloaded": downloaded})
    failure_reasons.update(generic_failures)

    print(f"\n{DONE} English pipeline complete - {OK} {len(all_downloaded)}/{len(dois)}, {FAIL} {len(remaining)} remaining")
    return all_downloaded, remaining, round_results, failure_reasons


def run_english_cdp(dois: list[str], output_dir: str, port: int,
                    skip_sd: bool = False, include_si: bool = False,
                    sd_browser: str = "chrome"
                    ) -> tuple[list[str], list[str], list[dict], dict[str, str]]:
    """Run English CDP-only pipeline through Generic CDP. No Sci-Hub.

    Designed to run AFTER English login gate in Phase 2.
    """
    all_downloaded: list[str] = []
    round_results: list[dict] = []
    remaining = list(dois)
    failure_reasons: dict[str, str] = {}

    if skip_sd:
        print(f"\n{SKIP} --skip-sd ignored: ScienceDirect is handled inside Generic CDP.")

    # R2: Generic CDP
    downloaded, remaining, generic_failures = run_generic_round(
        remaining, output_dir, port, include_si=include_si
    )
    all_downloaded.extend(downloaded)
    round_results.append({"round": "Generic CDP", "downloaded": downloaded})
    failure_reasons.update(generic_failures)

    login_retry_dois = _filter_login_required_dois(remaining, generic_failures)
    if login_retry_dois:
        print(f"\n{WARN} Institutional login required for {len(login_retry_dois)} publisher item(s).")
        gate_result = show_english_login_gate(
            login_retry_dois,
            skip_sd=skip_sd,
            interactive=sys.stdin.isatty(),
        )
        if gate_result is None:
            failure_reasons.update({
                doi: "pending_user_login"
                for doi in login_retry_dois
            })
            checkpoint_path = write_login_checkpoint(
                output_dir,
                stage="english_cdp_retry",
                dois=login_retry_dois,
                failure_reasons=failure_reasons,
            )
            print(f"  {ARROW} Login checkpoint written; resume after manual login: {checkpoint_path}")
        elif gate_result:
            retry_downloaded, retry_remaining, retry_failures = run_generic_round(
                login_retry_dois, output_dir, port, include_si=include_si
            )
            all_downloaded.extend(retry_downloaded)
            round_results.append({"round": "Generic CDP (after login)", "downloaded": retry_downloaded})
            remaining = [doi for doi in remaining if doi not in login_retry_dois]
            remaining.extend(retry_remaining)
            for doi in retry_downloaded:
                failure_reasons.pop(doi, None)
            failure_reasons.update(retry_failures)
        else:
            print("English CDP login retry skipped by user.")

    print(f"\n{DONE} English CDP complete - {OK} {len(all_downloaded)}/{len(dois)}, {FAIL} {len(remaining)} remaining")
    return all_downloaded, remaining, round_results, failure_reasons


# ── Download Log ────────────────────────────────────────────────────────────

def generate_download_log(output_dir: str, all_dois: list[str],
                          round_results: list[dict],
                          failure_reasons: Optional[dict[str, str]] = None) -> str:
    """Generate a Markdown download tracking log."""
    log_path = os.path.join(output_dir, "download_log.md")

    failure_reasons = failure_reasons or {}
    # Build status map
    status_map: dict[str, dict] = {}
    for d in all_dois:
        status_map[d] = {"status": "pending", "source": "", "path": "", "size_kb": 0, "reason": failure_reasons.get(d, "")}

    for result in round_results:
        for d in result.get("downloaded", []):
            basename = d.replace("/", "_").replace(":", "_")
            fpath = os.path.join(output_dir, f"{basename}.pdf")
            size_kb = os.path.getsize(fpath) // 1024 if os.path.exists(fpath) else 0
            status_map[d] = {
                "status": "[OK]",
                "source": result.get("round", "unknown"),
                "path": fpath,
                "size_kb": size_kb,
                "reason": "",
            }

    # Generate Markdown
    lines = [
        f"# Download Log",
        f"",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Output dir: {output_dir}",
        f"Total DOIs: {len(all_dois)}",
        f"",
        f"| # | DOI | Status | Source | Reason | Size | Path |",
        f"|---|-----|--------|--------|--------|------|------|",
    ]

    for i, doi in enumerate(all_dois, 1):
        info = status_map.get(doi, {})
        status = info.get("status", "[PENDING]")
        source = info.get("source", "")
        reason = info.get("reason", "") or "-"
        size = f"{info.get('size_kb', 0)}KB" if info.get("size_kb") else "-"
        path = os.path.basename(info.get("path", "")) if info.get("path") else "-"
        lines.append(f"| {i} | `{doi[:45]}` | {status} | {source} | {reason} | {size} | {path} |")

    # Summary
    ok_count = sum(1 for v in status_map.values() if v["status"] == "[OK]")
    fail_count = sum(1 for v in status_map.values() if v["status"] == "pending")
    lines.extend([
        f"",
        f"## Summary",
        f"",
        f"- [OK] Downloaded: {ok_count}/{len(all_dois)}",
        f"- [FAIL] Failed/Pending: {fail_count}/{len(all_dois)}",
    ])

    content = "\n".join(lines)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(content)

    return log_path


def write_failed_doi_sidecar(output_dir: str, remaining: list[str],
                             failure_reasons: dict[str, str]) -> str:
    """Write structured failed DOI metadata for later replay and triage."""
    sidecar_path = os.path.join(output_dir, "failed_dois.json")
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "items": [],
    }
    for doi in remaining:
        pub = resolve_publisher(doi)
        payload["items"].append({
            "doi": doi,
            "publisher": pub.get("_key", "unknown") if pub else "unknown",
            "domain": pub.get("publisher_domain", "") if pub else "",
            "strategy": pub.get("strategy", "") if pub else "",
            "failure_reason": failure_reasons.get(doi, ""),
            "retry_hint": f"python3 scripts/unified_download_router.py --papers \"{doi}\" --output {output_dir}",
        })
    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return sidecar_path


# ── Login Gates ──────────────────────────────────────────────────────────────

# Publishers that typically require institutional login for CDP download.
# OA publishers (direct_http strategy) are excluded.
# Sci-Hub and Chinese publishers are handled separately.
ENGLISH_LOGIN_STRATEGIES = {"generic"}
ENGLISH_LOGIN_REQUIRED_REASONS = {
    "manual_confirmation_required",
    "manual_required",
    "captcha_required",
    "institution_login_required",
    "login_required",
    "login_wall",
    "access_denied",
    "pdf_probe_blocked",
    "pdf_probe_unknown",
}


def _safe_gate_input(prompt: str) -> Optional[str]:
    """Read gate input without collapsing host IO failures into explicit skip."""
    try:
        return input(prompt)
    except EOFError:
        print(f"\n{WARN} Interactive input unavailable in current host.")
        return None
    except KeyboardInterrupt:
        print(f"\n{WARN} Login confirmation interrupted.")
        return None


def _filter_login_required_dois(dois: list[str], failure_reasons: dict[str, str]) -> list[str]:
    """Return failed DOIs that should prompt an institutional-login retry."""
    return [
        doi for doi in dois
        if failure_reasons.get(doi) in ENGLISH_LOGIN_REQUIRED_REASONS
    ]


def write_login_checkpoint(output_dir: str, stage: str, dois: list[str],
                           failure_reasons: dict[str, str]) -> str:
    """Write a re-runnable login checkpoint for remaining English CDP items."""
    path = os.path.join(output_dir, "login_checkpoint.json")
    items = []
    for doi in dois:
        info = classify_doi(doi)
        pub_cfg = info.get("publisher_config", {}) or {}
        items.append({
            "doi": doi,
            "publisher": info.get("publisher", "unknown"),
            "strategy": info.get("strategy", "unknown"),
            "domain": pub_cfg.get("publisher_domain", ""),
            "failure_reason": failure_reasons.get(doi, ""),
        })
    payload = {
        "checkpoint_type": "publisher_login",
        "status": "pending_user_login",
        "stage": stage,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "items": items,
        "rerun_hint": "python3 scripts/unified_download_router.py --resume-login-checkpoint paper-temp/login_checkpoint.json --output paper-temp/",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def resume_from_login_checkpoint(checkpoint_path: str, output_dir: str, port: int,
                                 include_si: bool = False) -> tuple[list[str], list[str], list[dict], dict[str, str]]:
    """Resume only the English DOI subset stored in a login checkpoint."""
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    dois = [
        item.get("doi", "").strip()
        for item in payload.get("items", [])
        if item.get("doi", "").strip()
    ]
    if not dois:
        return [], [], [], {}

    downloaded, remaining, failure_reasons = run_generic_round(
        dois, output_dir, port, include_si=include_si
    )
    round_results = [{"round": "Generic CDP (resume login checkpoint)", "downloaded": downloaded}]

    login_retry_dois = _filter_login_required_dois(remaining, failure_reasons)
    if login_retry_dois:
        failure_reasons.update({
            doi: "pending_user_login"
            for doi in login_retry_dois
        })
        refreshed = write_login_checkpoint(
            output_dir,
            stage="english_cdp_retry_resume",
            dois=login_retry_dois,
            failure_reasons=failure_reasons,
        )
        print(f"{WARN} Some resumed DOI(s) still require login; checkpoint refreshed: {refreshed}")

    return downloaded, remaining, round_results, failure_reasons


def show_chinese_login_gate(chinese_papers: list[dict]) -> bool:
    """Display Chinese (CNKI/Wanfang) login gate. Returns True if confirmed."""
    if not chinese_papers:
        return True
    from generic_publisher_downloader import _PUBLISHER_CONFIGS

    pubs: list[str] = []
    for paper in chinese_papers:
        source = paper.get("source", "").lower()
        if source in ("cnki", "wanfang"):
            cfg = _PUBLISHER_CONFIGS.get(source, {})
            domain = cfg.get("publisher_domain", "?")
            pubs.append(f"  - {source} ({domain})")
    if not pubs:
        return True

    print(f"\n{'='*60}")
    print("Chinese Login Gate - CNKI / Wanfang")
    print(f"{'='*60}")
    print()
    print("Please verify CNKI/Wanfang login in the CDP browser.")
    print("Choose one option:")
    print("  1) 已登录，继续")
    print("  2) 没有账号，跳过并继续")
    print("  3) 稍后重试")
    print()
    for p in sorted(set(pubs)):
        print(p)
    print()
    print("  CNKI:  https://kns.cnki.net/")
    print("  Wanfang: https://www.wanfangdata.com.cn/")
    print()
    try:
        resp = input("Enter 1/2/3: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nSkipping Chinese download.")
        return False
    if resp in ("1", "已登录", "y", "yes", "done", "继续", "go"):
        print(f"{OK} Chinese login confirmed - starting CNKI/Wanfang CDP.\n")
        return True
    if resp in ("2", "skip", "q", "quit", "exit", "n", "no", "无账号", "没有账号"):
        print(f"{SKIP} Chinese login skipped - continuing with other download paths.\n")
        return False
    print(f"{SKIP} Chinese login deferred - continuing with other download paths.\n")
    return False


def show_english_login_gate(dois: list[str], skip_sd: bool = False,
                            interactive: bool = True) -> Optional[bool]:
    """Display English publisher login gate for remaining CDP papers.

    Only triggers for papers needing Generic CDP strategy.
    Sci-Hub and Chinese are excluded (handled separately).
    Returns:
      True  -> user explicitly confirmed login
      False -> user explicitly skipped or deferred
      None  -> host cannot continue interactive input
    """
    # Classify remaining DOIs to find CDP-dependent publishers
    login_publishers: dict[str, set[str]] = {}  # strategy -> set of publisher keys
    seen = set()

    for doi in dois:
        c = classify_doi(doi)
        strategy = c["strategy"]
        if strategy not in ENGLISH_LOGIN_STRATEGIES:
            continue
        pub_key = c["publisher"]
        pub_config = c.get("publisher_config", {})
        domain = pub_config.get("publisher_domain", "?") if pub_config else "?"
        if pub_key not in seen:
            seen.add(pub_key)
            login_publishers.setdefault(strategy, set()).add(f"{pub_key} ({domain})")

    if not login_publishers:
        print(f"\n{OK} No English publishers requiring institutional login.")
        return True

    print(f"\n{'='*60}")
    print("English Login Gate - Institutional Access Required")
    print(f"{'='*60}")
    print()
    print("The following publishers require institutional login before download:")
    print()
    for strategy, pubs in sorted(login_publishers.items()):
        label = {"generic": "Generic CDP"}.get(strategy, strategy)
        print(f"  [{label}]")
        for p in sorted(pubs):
            print(f"    - {p}")
        print()
    print("Please complete these steps BEFORE continuing.")
    print("If you do not have an institutional account for some or all of these")
    print("publishers, type 'skip' and the workflow will continue with OA/direct paths")
    print("plus any already-completed downloads, without treating this as a fatal stop.")
    print("Choose one option:")
    print("  1) 已登录，继续")
    print("  2) 没有账号，跳过并继续")
    print("  3) 稍后重试")
    print()
    print("  1. Open CDP Chrome at http://127.0.0.1:9223")
    print("  2. Navigate to each publisher's homepage (domains listed above)")
    print("  3. Complete institutional SSO login for each publisher")
    print("  4. Verify the login persists (check for 'Access provided by...' badges)")
    print()
    print(f"{'='*60}")
    if not interactive:
        print(f"{WARN} Non-interactive mode: login checkpoint required before rerun.\n")
        return None
    raw_resp = _safe_gate_input("\nEnter 1/2/3: ")
    if raw_resp is None:
        print("\nEnglish login requires checkpoint/resume rather than treating this as skip.")
        return None
    resp = raw_resp.strip().lower()
    if resp in ("1", "已登录", "y", "yes", "done", "logged in", "继续", "go"):
        print(f"{OK} Login confirmed - proceeding with English CDP.\n")
        return True
    elif resp in ("2", "q", "quit", "exit", "n", "no", "skip", "无账号", "没有账号"):
        print(f"{SKIP} English institutional login skipped - continuing without login-only publishers.")
        return False
    elif resp in ("3", "later", "retry", "稍后", "重试"):
        print("English login deferred - you can rerun the remaining list later.\n")
        return False
    else:
        print(f"{WARN} Unrecognized response - proceeding (Ctrl+C to abort).\n")
        return True


# ── Session Check ───────────────────────────────────────────────────────────

def check_all_sessions(port: int):
    """Print session status for all known publishers."""
    def _readiness_label(signal: dict) -> str:
        if signal.get("probe_status") == "ok":
            return "可直接尝试下载"
        if signal.get("probe_status") == "blocked":
            return "需要先人工登录/验证"
        return "信号不足，需实际下载验证"

    print("=== Publisher Session Check ===")
    print(f"{'Publisher':20s} {'Domain':35s} {'结论':16s} {'Signal':16s} {'Probe'}")
    print("-" * 128)

    for key, cfg in _PUBLISHER_CONFIGS.items():
        signal = describe_publisher_session(port, cfg)
        icon = OK if signal["has_session"] else FAIL
        probe = f"{signal['probe_status']}: {signal['probe_reason']}"
        signal_label = f"{signal['signal_strength']} ({signal['cookie_count']})"
        readiness = _readiness_label(signal)
        print(f"  {icon} {key:18s} | {signal['domain']:35s} | {readiness:16s} | {signal_label:16s} | {probe}")

    # Also check generic CDP browser availability
    if check_cdp(port):
        print(f"\n  {OK} CDP Chrome running on port {port}")
    else:
        print(f"\n  {FAIL} CDP Chrome NOT running on port {port}")
    print("  Note: cookie count is a weak signal; only PDF/article probe can confirm access.")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    configure_console_output()

    parser = argparse.ArgumentParser(
        description="Unified PDF download router - auto-routes DOI to optimal strategy."
    )
    parser.add_argument("input", nargs="?", help="Input file: DOI list, Markdown literature table, or BibTeX")
    parser.add_argument("--papers", help="Comma-separated list of DOIs (inline)")
    parser.add_argument("--doi-file", help="Plain text file with one DOI per line")
    parser.add_argument("--port", type=int, default=CDP_PORT, help=f"CDP Chrome debug port (default: {CDP_PORT})")
    parser.add_argument("--browser", choices=("chrome", "edge"),
                        default=os.environ.get("CDP_BROWSER", "chrome"),
                        help="CDP browser for single-browser rounds (default: chrome; use edge to reuse Edge login)")
    parser.add_argument("--sd-browser", choices=("chrome", "edge", "auto"),
                        help=argparse.SUPPRESS)
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help=f"Output directory (default: {DEFAULT_OUTPUT}/)")
    parser.add_argument("--test", help="Test a single DOI (show routing decision + download)")
    parser.add_argument("--check-session", action="store_true", help="Check publisher sessions and exit")
    parser.add_argument("--skip-scihub", action="store_true", help="Skip Sci-Hub round (post-2021 papers)")
    parser.add_argument("--skip-sd", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-ieee", action="store_true", help="Skip IEEE round")
    parser.add_argument("--include-si", action="store_true", help="Download supplementary info where available")
    parser.add_argument("--dry-run", action="store_true", help="Show routing decisions without downloading")
    parser.add_argument("--require-login-confirm", action="store_true",
                        help="Pause before CDP rounds to prompt user to complete institutional login")
    parser.add_argument("--chinese-input", help="Chinese papers input: JSON file or Markdown literature table")
    parser.add_argument("--workflow-results", help="Step 4 workflow search results JSON (workflow-contracts.v1)")
    parser.add_argument("--download-manifest", help="Direct download manifest JSON (workflow-contracts.v1)")
    parser.add_argument("--skip-chinese", action="store_true", help="Skip Chinese CDP round")
    parser.add_argument("--parallel-phase1", action="store_true",
                        help="Opt in to running Sci-Hub and Chinese CDP concurrently. Default is serial for CDP reliability.")
    parser.add_argument("--test-cnki", help="Test single CNKI paper download (provide article URL)")
    parser.add_argument("--test-wanfang", help="Test single Wanfang paper download (provide article URL)")
    parser.add_argument("--resume-login-checkpoint", nargs="?", const="AUTO",
                        help="Resume English DOI download from login_checkpoint.json (default: <output>/login_checkpoint.json)")

    args = parser.parse_args()
    sd_browser = args.sd_browser or args.browser

    # --check-session
    if args.check_session:
        check_all_sessions(args.port)
        return

    if args.resume_login_checkpoint:
        checkpoint_path = args.resume_login_checkpoint
        if checkpoint_path == "AUTO":
            checkpoint_path = os.path.join(args.output, "login_checkpoint.json")
        if not os.path.exists(checkpoint_path):
            print(f"ERROR: login checkpoint not found: {checkpoint_path}")
            sys.exit(1)
        if not ensure_cdp_running(args.port, browser=args.browser):
            print(f"\nERROR: CDP {args.browser.title()} not running on port {args.port}.")
            sys.exit(1)
        if not check_required_deps():
            sys.exit(1)

        downloaded, remaining, round_results, failure_reasons = resume_from_login_checkpoint(
            checkpoint_path,
            args.output,
            args.port,
            include_si=args.include_si,
        )
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        all_dois = [
            item.get("doi", "").strip()
            for item in payload.get("items", [])
            if item.get("doi", "").strip()
        ]
        generate_download_log(args.output, all_dois, round_results, failure_reasons)
        print(f"\n{DONE} Resume complete - {OK} {len(downloaded)}/{len(all_dois)}, {FAIL} {len(remaining)} remaining")
        return

    # --test
    if args.test:
        doi = args.test.strip()
        info = classify_doi(doi)
        print("=== DOI Router - Test Mode ===")
        print(f"DOI:       {doi}")
        print(f"Publisher: {info['publisher']}")
        print(f"Strategy:  {info['strategy']}")
        print(f"Est. year: {info['year'] or 'unknown'}")

        domain = info['publisher_config'].get('publisher_domain', 'N/A')
        notes = info['publisher_config'].get('notes', '')
        known = info['publisher_config'].get('known_issues', '')
        print(f"Domain:    {domain}")
        if notes:
            print(f"Notes:     {notes}")
        if known:
            print(f"Issues:    {known}")

        if info['strategy'] == "skip":
            print(f"\n{SKIP} SKIPPED - automation not possible for this publisher")
            return

        if info['strategy'] == "ieee_cdp":
            print(f"\n{ARROW} Delegated to {info['strategy']} script (use dedicated downloader).")
            return

        if args.dry_run:
            print(f"\n[DRY RUN] Would use {info['strategy']} strategy.")
            return

        # Actual download attempt
        if not ensure_cdp_running(args.port, browser=args.browser):
            print(f"\nERROR: CDP {args.browser.title()} not running on port {args.port}.")
            sys.exit(1)

        print(f"\nDownloading via {info['strategy']} strategy...")
        result_path, status, pub = generic_download_one(
            args.port, doi, args.output, include_si=args.include_si
        )
        if result_path and status == "ok":
            size_kb = os.path.getsize(result_path) // 1024
            print(f"{OK} Downloaded: {result_path} ({size_kb} KB)")
        elif status == "si_only":
            print(f"{WARN} SI downloaded only (no PDF)")
        else:
            print(f"{FAIL} Failed: status={status}")
        return

    # --test-cnki (single CNKI paper via article URL)
    if args.test_cnki:
        article_url = args.test_cnki.strip()
        if not article_url.startswith("http"):
            print(f"ERROR: --test-cnki requires a full article URL (https://...)")
            sys.exit(1)
        print("=== Chinese Download - Test Mode (CNKI) ===")
        print(f"URL: {article_url}")
        if not ensure_cdp_running(args.port, browser=args.browser):
            print(f"\nERROR: CDP {args.browser.title()} not running on port {args.port}.")
            sys.exit(1)
        print(f"\nDownloading via CNKI CDP...")
        result_path, status, pub = generic_download_one(
            args.port, f"cnki.test.{hashlib.md5(article_url.encode()).hexdigest()[:8]}",
            args.output, article_url=article_url
        )
        if result_path and status == "ok":
            size_kb = os.path.getsize(result_path) // 1024
            print(f"{OK} Downloaded: {result_path} ({size_kb} KB)")
        else:
            print(f"{FAIL} Failed: status={status}")
        return

    # --test-wanfang (single Wanfang paper via article URL)
    if args.test_wanfang:
        article_url = args.test_wanfang.strip()
        if not article_url.startswith("http"):
            print(f"ERROR: --test-wanfang requires a full article URL (https://...)")
            sys.exit(1)
        print("=== Chinese Download - Test Mode (Wanfang) ===")
        print(f"URL: {article_url}")
        if not ensure_cdp_running(args.port, browser=args.browser):
            print(f"\nERROR: CDP {args.browser.title()} not running on port {args.port}.")
            sys.exit(1)
        print(f"\nDownloading via Wanfang CDP...")
        result_path, status, pub = generic_download_one(
            args.port, f"wanfang.test.{hashlib.md5(article_url.encode()).hexdigest()[:8]}",
            args.output, article_url=article_url
        )
        if result_path and status == "ok":
            size_kb = os.path.getsize(result_path) // 1024
            print(f"{OK} Downloaded: {result_path} ({size_kb} KB)")
        else:
            print(f"{FAIL} Failed: status={status}")
        return

    workflow_items = []
    if args.workflow_results:
        workflow_items.extend(download_items_from_search_records(load_search_records(args.workflow_results)))
    if args.download_manifest:
        workflow_items.extend(load_download_manifest(args.download_manifest))

    workflow_dois = dois_from_download_items(workflow_items)
    workflow_chinese_papers = as_chinese_papers(workflow_items)

    # Batch mode
    bibtex_chinese_papers: list[dict] = []
    if args.doi_file:
        dois = parse_doi_file(args.doi_file)
    elif args.input:
        dois = parse_input(args.input)
        bibtex_chinese_papers = parse_bibtex_chinese_papers(args.input)
        if bibtex_chinese_papers:
            chinese_dois = {
                p.get("doi", "").strip().lower()
                for p in bibtex_chinese_papers
                if p.get("doi")
            }
            dois = [d for d in dois if d.strip().lower() not in chinese_dois]
    elif args.papers:
        dois = [d.strip() for d in args.papers.split(",") if d.strip()]
    elif workflow_items:
        dois = workflow_dois
    elif args.chinese_input:
        dois = []  # Chinese-only mode, no English DOIs to parse
    else:
        parser.print_help()
        sys.exit(1)

    if not dois and not args.chinese_input and not workflow_chinese_papers:
        print("No DOIs or Chinese papers found.")
        sys.exit(1)

    # ── Parse Chinese papers ───────────────────────────────────────────
    chinese_papers: list[dict] = list(workflow_chinese_papers) + bibtex_chinese_papers
    if args.chinese_input:
        chinese_papers.extend(parse_chinese_papers(args.chinese_input))
    if chinese_papers:
        seen_chinese: dict[tuple[str, str], int] = {}
        deduped_chinese: list[dict] = []
        for paper in chinese_papers:
            key = (paper.get("source", ""), paper.get("doi", "") or paper.get("title", ""))
            if key in seen_chinese:
                existing = deduped_chinese[seen_chinese[key]]
                if not existing.get("article_url") or "doi.org/" in existing.get("article_url", ""):
                    if paper.get("article_url"):
                        existing.update(paper)
                continue
            seen_chinese[key] = len(deduped_chinese)
            deduped_chinese.append(paper)
        chinese_papers = deduped_chinese
        cnki_count = sum(1 for p in chinese_papers if p["source"] == "cnki")
        wf_count = sum(1 for p in chinese_papers if p["source"] == "wanfang")
        print(f"Chinese papers: {len(chinese_papers)} total ({cnki_count} CNKI + {wf_count} Wanfang)")
    elif args.chinese_input or args.workflow_results or args.download_manifest:
        print("No Chinese papers found in input.")

    # Deduplicate
    seen = set()
    unique_dois = []
    for d in dois:
        d_clean = d.strip().lower()
        if d_clean not in seen:
            seen.add(d_clean)
            unique_dois.append(d.strip())
    dois = unique_dois

    os.makedirs(args.output, exist_ok=True)

    # Print classification summary
    print(f"=== Unified Download Router ===")
    print(f"Total unique DOIs: {len(dois)}")
    print(f"Output directory:  {args.output}/")
    print(f"CDP port:          {args.port}")
    if chinese_papers:
        print(f"Chinese papers:    {len(chinese_papers)} "
              f"({sum(1 for p in chinese_papers if p['source']=='cnki')} CNKI + "
              f"{sum(1 for p in chinese_papers if p['source']=='wanfang')} Wanfang)")
    print()

    # Initialize classified list (may be empty for Chinese-only mode)
    classified = [classify_doi(d) for d in dois]

    # Build classified entries for Chinese papers (for routing display + login gate)
    if chinese_papers:
        for p in chinese_papers:
            if p.get("article_url"):
                c = classify_doi(p.get("doi", ""))
                c["strategy"] = "chinese_cdp"
                c["publisher"] = p["source"]
                classified.append(c)

    # Group classified entries by strategy for display
    by_strategy: dict[str, list] = {}
    for c in classified:
        s = c["strategy"]
        by_strategy.setdefault(s, []).append(c)

    print("Routing summary:")
    strategy_labels = {
        "scihub_only": "Sci-Hub (pre-2021)",
        "ieee_cdp": "IEEE CDP",
        "generic": "Generic CDP",
        "chinese_cdp": "Chinese CDP (CNKI/Wanfang)",
        "direct_http": "Direct HTTP",
        "skip": "SKIP (unavailable)",
    }
    for s in STRATEGY_ORDER:
        items = by_strategy.get(s, [])
        if items:
            label = strategy_labels.get(s, s)
            print(f"  {label:25s}: {len(items):3d} papers")

    if args.dry_run:
        total = sum(1 for c in classified if c["strategy"] != "skip")
        print(f"\n[DRY RUN] Would download {total} papers "
              f"({sum(1 for c in classified if c['strategy']=='chinese_cdp')} Chinese)")
        return

    # Check CDP (required for all rounds except Sci-Hub only)
    has_cdp_rounds = any(c["strategy"] in ("generic", "chinese_cdp")
                         for c in classified) or bool(chinese_papers)
    if has_cdp_rounds and not ensure_cdp_running(args.port, browser=args.browser):
        print(f"\nERROR: CDP {args.browser.title()} not running on port {args.port}.")
        print(f"Start {args.browser.title()} with:")
        print(f"  {sys.executable} scripts/start_cdp_browser.py --browser {args.browser} --port {args.port}")
        print("  macOS/Linux wrapper also supported: bash scripts/start_cdp_chrome.sh")
        sys.exit(1)

    if not check_required_deps():
        sys.exit(1)

    # ═══════════════════════════════════════════════════════════════════
    # Phase 1: Sci-Hub + Chinese gate + Chinese CDP
    # Default is serial because CNKI/Wanfang and shared CDP browser state are
    # more reliable when not competing with other browser automation.
    # ═══════════════════════════════════════════════════════════════════

    scihub_dl: list[str] = []
    scihub_rem = list(dois)
    ch_dl: list[str] = []
    ch_rem: list[str] = []

    if args.parallel_phase1:
        from concurrent.futures import ThreadPoolExecutor

        scihub_future = None
        ch_future = None
        with ThreadPoolExecutor(max_workers=2) as phase1:
            if dois and not args.skip_scihub:
                scihub_future = phase1.submit(
                    run_scihub_round, list(dois), args.output, args.port
                )

            if chinese_papers and not args.skip_chinese:
                if args.require_login_confirm:
                    if show_chinese_login_gate(chinese_papers):
                        ch_future = phase1.submit(
                            run_chinese_round, chinese_papers, args.output, args.port
                        )
                    else:
                        print("Chinese download skipped by user.")
                else:
                    ch_future = phase1.submit(
                        run_chinese_round, chinese_papers, args.output, args.port
                    )

        if scihub_future:
            scihub_dl, scihub_rem = scihub_future.result()
        if ch_future:
            ch_dl, ch_rem = ch_future.result()
    else:
        if dois and not args.skip_scihub:
            scihub_dl, scihub_rem = run_scihub_round(list(dois), args.output, args.port)

        if chinese_papers and not args.skip_chinese:
            if args.require_login_confirm:
                if show_chinese_login_gate(chinese_papers):
                    ch_dl, ch_rem = run_chinese_round(chinese_papers, args.output, args.port)
                else:
                    print("Chinese download skipped by user.")
            else:
                ch_dl, ch_rem = run_chinese_round(chinese_papers, args.output, args.port)

    # ═══════════════════════════════════════════════════════════════════
    # Phase 2: English login gate (after Sci-Hub) + English CDP
    # Only fires if papers remain after Sci-Hub and need CDP access.
    # ═══════════════════════════════════════════════════════════════════

    en_dl: list[str] = []
    en_rem = list(scihub_rem)
    en_results: list[dict] = []
    en_failure_reasons: dict[str, str] = {}

    if en_rem:
        # Check if remaining papers actually need CDP
        has_cdp = any(
            classify_doi(d)["strategy"] == "generic"
            for d in en_rem
        )
        if args.require_login_confirm and has_cdp:
            gate_result = show_english_login_gate(en_rem, skip_sd=args.skip_sd)
            if gate_result is None:
                checkpoint_path = write_login_checkpoint(
                    args.output,
                    stage="english_preflight_login",
                    dois=en_rem,
                    failure_reasons={doi: "pending_user_login" for doi in en_rem},
                )
                print(f"English CDP login checkpoint written: {checkpoint_path}")
            elif gate_result:
                en_dl, en_rem, en_results, en_failure_reasons = run_english_cdp(
                    en_rem, args.output, args.port,
                    skip_sd=args.skip_sd, include_si=args.include_si,
                    sd_browser=sd_browser
                )
            else:
                print("English CDP skipped by user - Sci-Hub papers saved.")
        else:
            en_dl, en_rem, en_results, en_failure_reasons = run_english_cdp(
                en_rem, args.output, args.port,
                skip_sd=args.skip_sd, include_si=args.include_si,
                sd_browser=sd_browser
            )
    elif not scihub_rem:
        print(f"\n{DONE} Sci-Hub downloaded all papers! ({len(scihub_dl)}/{len(dois)})")

    # ═══════════════════════════════════════════════════════════════════
    # Phase 3: Merge results from all phases
    # ═══════════════════════════════════════════════════════════════════

    all_downloaded = scihub_dl + ch_dl + en_dl
    round_results = (
        [{"round": "Sci-Hub", "downloaded": scihub_dl}] * (1 if scihub_dl else 0) +
        ([{"round": "Chinese CDP", "downloaded": ch_dl}] if ch_dl or (chinese_papers and not args.skip_chinese) else []) +
        en_results
    )
    remaining = en_rem + ch_rem

    # Extend doi list with Chinese paper identifiers for download log
    ch_dois = [p.get("doi") or p.get("title", "") for p in chinese_papers] if chinese_papers else []
    if ch_dois:
        dois = dois + ch_dois

    # ── Final summary ─────────────────────────────────────────────────
    log_path = generate_download_log(args.output, dois, round_results, en_failure_reasons)

    total_all = len(dois)
    print(f"\n{'='*60}")
    print(f"Final Summary")
    print(f"{'='*60}")
    print(f"  Total papers:     {total_all}")
    print(f"  {OK} Downloaded:    {len(all_downloaded)}")
    print(f"  {FAIL} Failed/Pending: {len(remaining)}")

    if remaining:
        failed_path = os.path.join(args.output, "failed_dois.txt")
        with open(failed_path, "w", encoding="utf-8") as f:
            for d in remaining:
                pub = resolve_publisher(d)
                pub_name = pub.get("_key", "unknown") if pub else "unknown"
                reason = en_failure_reasons.get(d, "")
                suffix = f" | {reason}" if reason else ""
                f.write(f"{d}  # {pub_name}{suffix}\n")
        sidecar_path = write_failed_doi_sidecar(args.output, remaining, en_failure_reasons)
        print(f"  Failed list:     {failed_path}")
        print(f"  Failed sidecar:  {sidecar_path}")

    print(f"  Download log:    {log_path}")
    print(f"\n  Next step {ARROW} Step 6: Zotero library management")


if __name__ == "__main__":
    main()
