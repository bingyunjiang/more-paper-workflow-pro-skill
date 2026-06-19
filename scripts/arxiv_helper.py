#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""arXiv L2 conditional search — find recent preprints (T-0 to T-4 window).

arXiv is a CONDITIONAL data source in the L1→L2→L3 routing architecture.
It is only enabled when the Step 3 search plan detects CS/AI cross-domain
signals (ML, transformer, neural network, computer vision, NLP, LLM, etc.)
or when the user explicitly requests the latest preprints.

For traditional engineering domains (mechanical, electrical, civil, chemical),
arXiv is skipped — OpenAlex already covers these well, and arXiv physics/CS
categories introduce noise.

Usage:
  # T-0~T-4 freshness window (primary use case)
  python3 scripts/arxiv_helper.py "transformer attention mechanism" \
    --days 4 --limit 20 --output arxiv_results.json

  # Broader search (wider window for Deep tier)
  python3 scripts/arxiv_helper.py "graph neural network thermal" \
    --days 30 --limit 50 --output arxiv_results.json

  # Without output file (prints JSON to stdout)
  python3 scripts/arxiv_helper.py "large language model reasoning" --limit 10

Dependencies:
  arxiv>=2.1  (pip install arxiv) — optional, only needed when arXiv is triggered.
  If not installed, the script prints a clear error and exits.
"""

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import arxiv

    HAS_ARXIV = True
except ImportError:
    HAS_ARXIV = False


# Default arXiv categories to include (CS + math + stat + q-bio + q-fin + econ).
# Excludes physics/astro/cond-mat to reduce noise for cross-domain CS/AI queries.
DEFAULT_CATEGORIES = [
    "cs.*",
    "math.*",
    "stat.*",
    "q-bio.*",
    "q-fin.*",
    "econ.*",
]

# Map of CS/AI signal keywords to query augmentation (adds specificity)
CS_AI_SIGNALS = [
    "machine learning",
    "deep learning",
    "neural network",
    "transformer",
    "attention mechanism",
    "large language model",
    "LLM",
    "GPT",
    "BERT",
    "computer vision",
    "natural language processing",
    "NLP",
    "reinforcement learning",
    "generative adversarial",
    "GAN",
    "diffusion model",
    "graph neural",
    "self-supervised",
    "contrastive learning",
    "foundation model",
]


# ── Helper functions ────────────────────────────────────────────────────────

def _build_query(query: str, all_categories: bool = False) -> str:
    """Build the arXiv query string.

    If all_categories is False, wraps the query with category filters
    to exclude physics/astro/cond-mat noise.
    """
    if all_categories:
        return query

    cat_filter = " OR ".join(f"cat:{c}" for c in DEFAULT_CATEGORIES)
    return f"({query}) AND ({cat_filter})"


def _arxiv_id_from_entry(entry_id: str) -> str:
    """Extract clean arXiv ID from entry ID URL.

    e.g. 'http://arxiv.org/abs/2301.12345v2' → '2301.12345'
    """
    arxiv_id = entry_id.split("/")[-1]
    # Strip version suffix
    if "v" in arxiv_id and arxiv_id.rsplit("v", 1)[-1].isdigit():
        arxiv_id = arxiv_id[: arxiv_id.rindex("v")]
    return arxiv_id


# ── Search functions ────────────────────────────────────────────────────────

def search_freshness(
    query: str,
    days: int = 4,
    limit: int = 20,
    all_categories: bool = False,
) -> list:
    """Search arXiv for papers submitted in the last N days.

    This is the primary use case — arXiv's unique value is T-0~T-4 freshness
    before papers appear in OpenAlex.

    Args:
        query: Search query string.
        days: Freshness window in days (default: 4).
        limit: Max results to return.
        all_categories: If True, include physics/astro/cond-mat categories.

    Returns:
        List of flat paper dicts (same format as search_by_topic.py).
    """
    if not HAS_ARXIV:
        print(
            "arxiv_helper: arXiv package not installed. "
            "Install with: pip install arxiv>=2.1",
            file=sys.stderr,
        )
        return []

    client = arxiv.Client(page_size=100, delay_seconds=4.0, num_retries=3)

    search_query = _build_query(query, all_categories)
    search = arxiv.Search(
        query=search_query,
        max_results=limit * 2,  # Over-fetch to allow date filtering
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results = []

    try:
        for paper in client.results(search):
            # Filter by submission date
            pub_date = paper.published
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            if pub_date < cutoff:
                continue

            arxiv_id = _arxiv_id_from_entry(paper.entry_id)
            results.append(
                {
                    "doi": f"10.48550/arxiv.{arxiv_id}",
                    "title": paper.title.strip(),
                    "year": pub_date.year,
                    "venue": "arXiv",
                    "authors": [a.name for a in paper.authors],
                    "citations": 0,  # arXiv papers have no citation count yet
                    "source": "arxiv",
                    "arxiv_id": arxiv_id,
                    "arxiv_categories": list(paper.categories),
                    "submitted_date": pub_date.isoformat(),
                }
            )

            if len(results) >= limit:
                break

    except Exception as e:
        print(f"arxiv_helper: search error — {e}", file=sys.stderr)
        return []

    return results


def search_general(
    query: str,
    limit: int = 20,
    sort: str = "relevance",
    all_categories: bool = False,
) -> list:
    """General arXiv search (not freshness-window constrained).

    Use this for Deep tier when the user wants comprehensive coverage
    including preprints.

    Args:
        query: Search query string.
        limit: Max results to return.
        sort: Sort order — 'relevance', 'submitted', or 'lastUpdated'.
        all_categories: If True, include physics/astro/cond-mat categories.

    Returns:
        List of flat paper dicts.
    """
    if not HAS_ARXIV:
        print(
            "arxiv_helper: arXiv package not installed. "
            "Install with: pip install arxiv>=2.1",
            file=sys.stderr,
        )
        return []

    client = arxiv.Client(page_size=100, delay_seconds=4.0, num_retries=3)

    sort_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "submitted": arxiv.SortCriterion.SubmittedDate,
        "lastUpdated": arxiv.SortCriterion.LastUpdatedDate,
    }
    sort_criterion = sort_map.get(sort, arxiv.SortCriterion.Relevance)

    search_query = _build_query(query, all_categories)
    search = arxiv.Search(
        query=search_query,
        max_results=limit,
        sort_by=sort_criterion,
    )

    results = []
    try:
        for paper in client.results(search):
            arxiv_id = _arxiv_id_from_entry(paper.entry_id)
            pub_date = paper.published
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            results.append(
                {
                    "doi": f"10.48550/arxiv.{arxiv_id}",
                    "title": paper.title.strip(),
                    "year": pub_date.year,
                    "venue": "arXiv",
                    "authors": [a.name for a in paper.authors],
                    "citations": 0,
                    "source": "arxiv",
                    "arxiv_id": arxiv_id,
                    "arxiv_categories": list(paper.categories),
                    "submitted_date": pub_date.isoformat(),
                }
            )

            if len(results) >= limit:
                break

    except Exception as e:
        print(f"arxiv_helper: search error — {e}", file=sys.stderr)
        return []

    return results


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "arXiv L2 conditional search — find recent preprints. "
            "Only triggered when CS/AI cross-domain signals are detected "
            "or user explicitly requests arXiv search."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Freshness window (T-0~T-4, primary use case)
  python3 scripts/arxiv_helper.py "transformer attention" --days 4 --limit 20

  # Wider window
  python3 scripts/arxiv_helper.py "graph neural network" --days 30 --limit 50

  # General search with all categories
  python3 scripts/arxiv_helper.py "quantum computing error correction" --sort relevance --all-cats

  # Check if arXiv is available
  python3 scripts/arxiv_helper.py --check
        """,
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Search query string (not needed with --check).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=4,
        help="Freshness window in days (default: 4). Only used in freshness mode.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max results to return (default: 20).",
    )
    parser.add_argument(
        "--sort",
        choices=["relevance", "submitted", "lastUpdated"],
        default="relevance",
        help="Sort order for general search (default: relevance).",
    )
    parser.add_argument(
        "--mode",
        choices=["freshness", "general"],
        default="freshness",
        help="Search mode: freshness (T-N window) or general (default: freshness).",
    )
    parser.add_argument(
        "--all-cats",
        action="store_true",
        help="Include all arXiv categories (physics/astro/cond-mat). "
        "Default: CS + math + stat + q-bio only.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output JSON file (default: stdout).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if arXiv package is installed and exit.",
    )
    args = parser.parse_args()

    # --check mode
    if args.check:
        if HAS_ARXIV:
            print("arxiv_helper: ✅ arXiv package is installed and available")
        else:
            print(
                "arxiv_helper: ❌ arXiv package is NOT installed. "
                "Install with: pip install arxiv>=2.1"
            )
        sys.exit(0 if HAS_ARXIV else 1)

    # Search mode
    if not args.query:
        parser.error("query is required for search mode (or use --check)")

    if not HAS_ARXIV:
        print(
            "arxiv_helper: arXiv package not installed. "
            "Install with: pip install arxiv>=2.1",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.mode == "freshness":
        results = search_freshness(
            query=args.query,
            days=args.days,
            limit=args.limit,
            all_categories=args.all_cats,
        )
    else:
        results = search_general(
            query=args.query,
            limit=args.limit,
            sort=args.sort,
            all_categories=args.all_cats,
        )

    output = json.dumps(results, indent=2, ensure_ascii=False)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(
            f"arxiv_helper: wrote {len(results)} results to {args.output}",
            file=sys.stderr,
        )
    else:
        print(output)

    # Summary
    print(
        f"arxiv_helper: found {len(results)} papers in {args.mode} mode "
        f"(query: '{args.query[:60]}{'...' if len(args.query) > 60 else ''}')",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
