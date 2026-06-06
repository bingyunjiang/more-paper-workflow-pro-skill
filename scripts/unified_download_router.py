#!/usr/bin/env python3
"""
Unified PDF download router — single entry point for all publishers.

Routes each DOI to the optimal download strategy using the publisher
routing matrix, then orchestrates download rounds:

  1. Sci-Hub CDP    → pre-2021 papers (free, ~6s/paper)
  2. SD CDP         → 10.1016/ Elsevier papers (96% success)
  3. Generic CDP    → IEEE (10.1109/) + all other publishers
                     (Wiley, ACS, RSC, Nature, Springer, etc.)
                     IEEE uses generic engine (strategy B: article page
                     → stamp URL extraction). Dedicated download_via_ieee.py
                     available as fallback for interactive SSO login flow.

Usage:
  python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/
  python3 scripts/unified_download_router.py dois.txt --port 9223
  python3 scripts/unified_download_router.py --papers DOI1,DOI2 --port 9223
  python3 scripts/unified_download_router.py --test 10.1021/acsnano.4c00001 --port 9223
  python3 scripts/unified_download_router.py --check-session --port 9223
"""

from __future__ import annotations

import sys, os, time, re, json, argparse, subprocess
from pathlib import Path
from datetime import datetime

# Ensure scripts/ is on path
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from cdp_utils import check_cdp, check_required_deps
from generic_publisher_downloader import (
    resolve_publisher, download_one as generic_download_one,
    check_publisher_session, _PUBLISHER_CONFIGS, extract_dois,
)

# ── Constants ───────────────────────────────────────────────────────────────

CDP_PORT = 9223
DEFAULT_OUTPUT = "paper-temp"
SCI_HUB_CUTOFF_YEAR = 2021  # Sci-Hub has very few papers after 2020

# Strategy routing table (for display and decisions)
STRATEGY_ORDER = ["scihub", "sd_cdp", "ieee_cdp", "generic", "direct_http", "skip"]


# ── Year Estimation ─────────────────────────────────────────────────────────

def estimate_year(doi: str) -> int | None:
    """Estimate publication year from DOI patterns. Returns int or None.

    DOIs often embed the year, e.g.:
      - 10.1016/j.jpowsour.2019.01.052 → 2019
      - 10.1109/tvt.2022.3183866 → 2022
      - 10.1002/ente.202301205 → 2023 (year embedded in larger number)
      - 10.1038/s41467-2024-45578 → 2024

    We scan the part AFTER the first '/' for 4-digit numbers in the
    publication-year range (1990–2026), skipping the DOI prefix.
    """
    # Split: "10.1016/j.jpowsour.2019.01.052" → prefix="10.1016", rest="j.jpowsour.2019.01.052"
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
        print(f"\n⏭ Round 1 (Sci-Hub): No pre-{SCI_HUB_CUTOFF_YEAR} papers to try ({len(new_dois)} papers are post-{SCI_HUB_CUTOFF_YEAR-1}).")
        return [], dois

    print(f"\n{'='*60}")
    print(f"Round 1: Sci-Hub CDP ({len(old_dois)} pre-{SCI_HUB_CUTOFF_YEAR} papers)")
    print(f"{'='*60}")

    # Write temp DOI list for scihub script
    scihub_input = os.path.join(output_dir, ".scihub_input.txt")
    os.makedirs(output_dir, exist_ok=True)
    with open(scihub_input, "w") as f:
        for d in old_dois:
            f.write(d + "\n")

    scihub_script = SCRIPTS_DIR / "download_via_scihub.py"
    if not scihub_script.exists():
        print(f"  WARNING: {scihub_script} not found — skipping Sci-Hub round.")
        return [], dois

    try:
        subprocess.run(
            [sys.executable, str(scihub_script), scihub_input,
             "--output", output_dir, "--port", str(port)],
            check=False, timeout=600  # 10 min max
        )
    except subprocess.TimeoutExpired:
        print("  ⚠ Sci-Hub round timed out after 10 minutes.")

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

    print(f"  Sci-Hub result: ✅ {len(downloaded)} downloaded, → {len(old_dois) - len(downloaded)} remaining for next round")

    # Cleanup
    try:
        os.remove(scihub_input)
    except Exception:
        pass

    return downloaded, remaining


def run_sd_round(dois: list[str], output_dir: str, port: int) -> tuple[list[str], list[str]]:
    """Round 2: ScienceDirect CDP for 10.1016/ papers.
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
        print(f"\n⏭ Round 2 (SD CDP): No Elsevier papers remaining.")
        return [], dois

    print(f"\n{'='*60}")
    print(f"Round 2: ScienceDirect CDP ({len(sd_dois)} Elsevier papers)")
    print(f"{'='*60}")

    # First resolve PII via batch_resolve_pii.py
    sd_input = os.path.join(output_dir, ".sd_input.txt")
    pii_map_path = os.path.join(output_dir, "sd_pii_map.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(sd_input, "w") as f:
        for d in sd_dois:
            f.write(d + "\n")

    batch_pii_script = SCRIPTS_DIR / "batch_resolve_pii.py"
    if batch_pii_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(batch_pii_script), sd_input,
                 "--output", pii_map_path],
                check=False, timeout=300
            )
        except subprocess.TimeoutExpired:
            print("  ⚠ PII resolution timed out.")
    else:
        print(f"  WARNING: {batch_pii_script} not found — cannot resolve PII for SD.")

    # Download via auto_sd_downloader
    auto_sd_script = SCRIPTS_DIR / "auto_sd_downloader.py"
    if auto_sd_script.exists() and os.path.exists(pii_map_path):
        try:
            subprocess.run(
                [sys.executable, str(auto_sd_script),
                 "--output-dir", output_dir,
                 "--pii-map", pii_map_path,
                 "--port-chrome", str(port)],
                check=False, timeout=1800  # 30 min max
            )
        except subprocess.TimeoutExpired:
            print("  ⚠ SD download timed out after 30 minutes.")
    elif not os.path.exists(pii_map_path):
        print(f"  ⚠ PII map not found — skipping SD download.")

    # Check results
    downloaded = []
    remaining = list(other_dois)
    for d in sd_dois:
        basename = d.replace("/", "_").replace(":", "_")
        fpath = os.path.join(output_dir, f"{basename}.pdf")
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            downloaded.append(d)
        else:
            remaining.append(d)

    print(f"  SD result: ✅ {len(downloaded)} downloaded, → {len(sd_dois) - len(downloaded)} remaining for next round")

    try:
        os.remove(sd_input)
    except Exception:
        pass

    return downloaded, remaining


def run_ieee_round(dois: list[str], output_dir: str, port: int) -> tuple[list[str], list[str]]:
    """Round 3 (fallback): IEEE CDP for 10.1109/ papers.

    NOTE: IEEE is now handled by Round 4 (Generic CDP) via publishers.toml
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
        print(f"\n⏭ Round 3 (IEEE CDP): No IEEE papers remaining.")
        return [], dois

    print(f"\n{'='*60}")
    print(f"Round 3: IEEE CDP ({len(ieee_dois)} IEEE papers)")
    print(f"{'='*60}")

    ieee_script = SCRIPTS_DIR / "download_via_ieee.py"
    if not ieee_script.exists():
        print(f"  WARNING: {ieee_script} not found — skipping IEEE round.")
        return [], dois

    # Write temp input
    ieee_input = os.path.join(output_dir, ".ieee_input.txt")
    os.makedirs(output_dir, exist_ok=True)
    with open(ieee_input, "w") as f:
        for d in ieee_dois:
            f.write(d + "\n")

    try:
        subprocess.run(
            [sys.executable, str(ieee_script), ieee_input,
             "--output", output_dir, "--port", str(port),
             "--skip-session-check"],
            check=False, timeout=900  # 15 min max
        )
    except subprocess.TimeoutExpired:
        print("  ⚠ IEEE round timed out after 15 minutes.")

    # Check results — IEEE uses arnumber_DOI.pdf naming
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

    print(f"  IEEE result: ✅ {len(downloaded)} downloaded, → {len(ieee_dois) - len(downloaded)} remaining for next round")

    try:
        os.remove(ieee_input)
    except Exception:
        pass

    return downloaded, remaining


def run_generic_round(dois: list[str], output_dir: str, port: int,
                      include_si: bool = False) -> tuple[list[str], list[str]]:
    """Round 4: Generic CDP for all remaining publishers.
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
            # SD or IEEE that weren't caught earlier — still try generic
            generic_dois.append(d)

    if not generic_dois:
        if skip_dois:
            print(f"\n⏭ Round 4 (Generic CDP): {len(skip_dois)} papers skipped (MDPI/unavailable), 0 eligible.")
        else:
            print(f"\n⏭ Round 4 (Generic CDP): No remaining papers.")
        return [], dois

    print(f"\n{'='*60}")
    print(f"Round 4: Generic Publisher CDP ({len(generic_dois)} papers)")
    print(f"{'='*60}")

    ok, fail = 0, 0
    downloaded = []
    remaining = []

    for i, doi in enumerate(generic_dois):
        pub = resolve_publisher(doi)
        pub_name = pub.get("_key", "unknown") if pub else "unknown"
        publisher_domain = pub.get("publisher_domain", "?") if pub else "?"

        print(f"  [{i+1}/{len(generic_dois)}] {doi[:50]} → {pub_name} ({publisher_domain})", end=" ", flush=True)

        t0 = time.time()
        result_path, status, _ = generic_download_one(
            port, doi, output_dir, include_si=include_si
        )
        elapsed = time.time() - t0

        if result_path and status == "ok":
            size_kb = os.path.getsize(result_path) // 1024
            print(f"✅ ({size_kb}KB, {elapsed:.1f}s)")
            downloaded.append(doi)
            ok += 1
        elif status == "si_only":
            print(f"⚠ SI only ({elapsed:.1f}s)")
            remaining.append(doi)
            fail += 1
        else:
            print(f"❌ ({elapsed:.1f}s)")
            remaining.append(doi)
            fail += 1

    # Remaining = failures + skips
    remaining = remaining + skip_dois
    print(f"  Generic result: ✅ {ok} downloaded, ❌ {fail} failed, ⏭ {len(skip_dois)} skipped")

    return downloaded, remaining


# ── Download Log ────────────────────────────────────────────────────────────

def generate_download_log(output_dir: str, all_dois: list[str],
                          round_results: list[dict]) -> str:
    """Generate a Markdown download tracking log."""
    log_path = os.path.join(output_dir, "download_log.md")

    # Build status map
    status_map: dict[str, dict] = {}
    for d in all_dois:
        status_map[d] = {"status": "pending", "source": "", "path": "", "size_kb": 0}

    for result in round_results:
        for d in result.get("downloaded", []):
            basename = d.replace("/", "_").replace(":", "_")
            fpath = os.path.join(output_dir, f"{basename}.pdf")
            size_kb = os.path.getsize(fpath) // 1024 if os.path.exists(fpath) else 0
            status_map[d] = {
                "status": "✅",
                "source": result.get("round", "unknown"),
                "path": fpath,
                "size_kb": size_kb,
            }

    # Generate Markdown
    lines = [
        f"# Download Log",
        f"",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Output dir: {output_dir}",
        f"Total DOIs: {len(all_dois)}",
        f"",
        f"| # | DOI | Status | Source | Size | Path |",
        f"|---|-----|--------|--------|------|------|",
    ]

    for i, doi in enumerate(all_dois, 1):
        info = status_map.get(doi, {})
        status = info.get("status", "⏳")
        source = info.get("source", "")
        size = f"{info.get('size_kb', 0)}KB" if info.get("size_kb") else "-"
        path = os.path.basename(info.get("path", "")) if info.get("path") else "-"
        lines.append(f"| {i} | `{doi[:45]}` | {status} | {source} | {size} | {path} |")

    # Summary
    ok_count = sum(1 for v in status_map.values() if v["status"] == "✅")
    fail_count = sum(1 for v in status_map.values() if v["status"] == "pending")
    lines.extend([
        f"",
        f"## Summary",
        f"",
        f"- ✅ Downloaded: {ok_count}/{len(all_dois)}",
        f"- ❌ Failed/Pending: {fail_count}/{len(all_dois)}",
    ])

    content = "\n".join(lines)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(content)

    return log_path


# ── Session Check ───────────────────────────────────────────────────────────

def check_all_sessions(port: int):
    """Print session status for all known publishers."""
    print("=== Publisher Session Check ===")
    print(f"{'Publisher':20s} {'Domain':35s} {'Session':10s} {'Cookies'}")
    print("-" * 75)

    for key, cfg in _PUBLISHER_CONFIGS.items():
        domain = cfg.get("publisher_domain", "N/A")
        strategy = cfg.get("strategy", "?")
        has_session, count = check_publisher_session(port, cfg)

        icon = "✅" if has_session else "❌"
        count_str = str(count) if count >= 0 else "err"
        print(f"  {icon} {key:18s} | {domain:35s} | {strategy:10s} | {count_str}")

    # Also check generic CDP browser availability
    if check_cdp(port):
        print(f"\n  ✅ CDP Chrome running on port {port}")
    else:
        print(f"\n  ❌ CDP Chrome NOT running on port {port}")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Unified PDF download router — auto-routes DOI to optimal strategy."
    )
    parser.add_argument("input", nargs="?", help="Input file: DOI list, Markdown literature table, or BibTeX")
    parser.add_argument("--papers", help="Comma-separated list of DOIs (inline)")
    parser.add_argument("--port", type=int, default=CDP_PORT, help=f"CDP Chrome debug port (default: {CDP_PORT})")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help=f"Output directory (default: {DEFAULT_OUTPUT}/)")
    parser.add_argument("--test", help="Test a single DOI (show routing decision + download)")
    parser.add_argument("--check-session", action="store_true", help="Check publisher sessions and exit")
    parser.add_argument("--skip-scihub", action="store_true", help="Skip Sci-Hub round (post-2021 papers)")
    parser.add_argument("--skip-sd", action="store_true", help="Skip ScienceDirect round")
    parser.add_argument("--skip-ieee", action="store_true", help="Skip IEEE round")
    parser.add_argument("--include-si", action="store_true", help="Download supplementary info where available")
    parser.add_argument("--dry-run", action="store_true", help="Show routing decisions without downloading")

    args = parser.parse_args()

    # --check-session
    if args.check_session:
        check_all_sessions(args.port)
        return

    # --test
    if args.test:
        doi = args.test.strip()
        info = classify_doi(doi)
        print(f"=== DOI Router — Test Mode ===")
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
            print(f"\n⏭ SKIPPED — automation not possible for this publisher")
            return

        if info['strategy'] in ("sd_cdp", "ieee_cdp"):
            print(f"\n→ Delegated to {info['strategy']} script (use dedicated downloader).")
            return

        if args.dry_run:
            print(f"\n[DRY RUN] Would use {info['strategy']} strategy.")
            return

        # Actual download attempt
        if not check_cdp(args.port):
            print(f"\nERROR: CDP Chrome not running on port {args.port}.")
            sys.exit(1)

        print(f"\nDownloading via {info['strategy']} strategy...")
        result_path, status, pub = generic_download_one(
            args.port, doi, args.output, include_si=args.include_si
        )
        if result_path and status == "ok":
            size_kb = os.path.getsize(result_path) // 1024
            print(f"✅ Downloaded: {result_path} ({size_kb} KB)")
        elif status == "si_only":
            print(f"⚠ SI downloaded only (no PDF)")
        else:
            print(f"❌ Failed: status={status}")
        return

    # Batch mode
    if args.input:
        dois = parse_input(args.input)
    elif args.papers:
        dois = [d.strip() for d in args.papers.split(",") if d.strip()]
    else:
        parser.print_help()
        sys.exit(1)

    if not dois:
        print("No DOIs found.")
        sys.exit(1)

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
    print()

    # Classify all DOIs
    classified = [classify_doi(d) for d in dois]
    by_strategy: dict[str, list] = {}
    for c in classified:
        s = c["strategy"]
        by_strategy.setdefault(s, []).append(c)

    print("Routing summary:")
    strategy_labels = {
        "scihub_only": "Sci-Hub (pre-2021)",
        "sd_cdp": "ScienceDirect CDP",
        "ieee_cdp": "IEEE CDP",
        "generic": "Generic CDP",
        "direct_http": "Direct HTTP",
        "skip": "SKIP (unavailable)",
    }
    for s in STRATEGY_ORDER:
        items = by_strategy.get(s, [])
        if items:
            label = strategy_labels.get(s, s)
            print(f"  {label:25s}: {len(items):3d} papers")

    if args.dry_run:
        print(f"\n[DRY RUN] Would download {sum(1 for c in classified if c['strategy'] != 'skip')} papers.")
        return

    # Check CDP
    if not check_cdp(args.port):
        print(f"\nERROR: CDP Chrome not running on port {args.port}.")
        print("Start Chrome with:")
        print(f"  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
        print(f"    --remote-debugging-port={args.port} \\")
        print(f"    --remote-allow-origins=http://127.0.0.1:{args.port} \\")
        print(f"    --no-first-run --no-default-browser-check")
        sys.exit(1)

    if not check_required_deps():
        sys.exit(1)

    # ── Run rounds ────────────────────────────────────────────────────
    remaining = list(dois)
    all_downloaded = []
    round_results = []

    # Round 1: Sci-Hub
    if not args.skip_scihub:
        downloaded, remaining = run_scihub_round(remaining, args.output, args.port)
        all_downloaded.extend(downloaded)
        round_results.append({"round": "Sci-Hub", "downloaded": downloaded})
    else:
        print(f"\n⏭ Round 1 (Sci-Hub): Skipped (--skip-scihub)")

    if not remaining:
        print(f"\n🎉 All papers downloaded! ({len(all_downloaded)}/{len(dois)})")
        generate_download_log(args.output, dois, round_results)
        return

    # Round 2: ScienceDirect
    if not args.skip_sd:
        downloaded, remaining = run_sd_round(remaining, args.output, args.port)
        all_downloaded.extend(downloaded)
        round_results.append({"round": "SD CDP", "downloaded": downloaded})
    else:
        print(f"\n⏭ Round 2 (SD CDP): Skipped (--skip-sd)")

    if not remaining:
        print(f"\n🎉 All papers downloaded! ({len(all_downloaded)}/{len(dois)})")
        generate_download_log(args.output, dois, round_results)
        return

    # Round 3: IEEE
    if not args.skip_ieee:
        downloaded, remaining = run_ieee_round(remaining, args.output, args.port)
        all_downloaded.extend(downloaded)
        round_results.append({"round": "IEEE CDP", "downloaded": downloaded})
    else:
        print(f"\n⏭ Round 3 (IEEE CDP): Skipped (--skip-ieee)")

    if not remaining:
        print(f"\n🎉 All papers downloaded! ({len(all_downloaded)}/{len(dois)})")
        generate_download_log(args.output, dois, round_results)
        return

    # Round 4: Generic CDP
    downloaded, remaining = run_generic_round(
        remaining, args.output, args.port, include_si=args.include_si
    )
    all_downloaded.extend(downloaded)
    round_results.append({"round": "Generic CDP", "downloaded": downloaded})

    # ── Final summary ─────────────────────────────────────────────────
    log_path = generate_download_log(args.output, dois, round_results)

    print(f"\n{'='*60}")
    print(f"Final Summary")
    print(f"{'='*60}")
    print(f"  Total DOIs:      {len(dois)}")
    print(f"  ✅ Downloaded:   {len(all_downloaded)}")
    print(f"  ❌ Failed/Pending: {len(remaining)}")

    if remaining:
        failed_path = os.path.join(args.output, "failed_dois.txt")
        with open(failed_path, "w") as f:
            for d in remaining:
                pub = resolve_publisher(d)
                pub_name = pub.get("_key", "unknown") if pub else "unknown"
                f.write(f"{d}  # {pub_name}\n")
        print(f"  Failed list:     {failed_path}")

    print(f"  Download log:    {log_path}")
    print(f"\n  Next step → Step 6: Zotero library management")


if __name__ == "__main__":
    main()
