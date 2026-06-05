#!/usr/bin/env python3
"""Discovery saturation curve — estimates literature coverage from scored results.

Theory: As a search exhausts relevant papers, the marginal discovery rate decays.
Fit N(t) = N_total * (1 - exp(-lambda * t)) to estimate coverage.

Adapted from paper-search-pro's discovery_curve.py (Apache 2.0).
Key adaptation: works with flat dict lists (the existing results format from
search_by_topic.py) instead of UnifiedPaperEntity. "High relevance" is defined
by the existing Tier system: Tier 1 (score >= 20) maps to "highly relevant".

CRITICAL: This module is ADVISORY ONLY. The agent decides when to stop.
should_warn_low_progress() returns advisory signals only — no hard stop.

Usage:
  # From markdown results table
  python3 scripts/discovery_curve.py --results 检索文献表.md --output snap.json

  # From JSON results file
  python3 scripts/discovery_curve.py --results results.json --output snap.json

  # With prior snapshots (for iterative runs)
  python3 scripts/discovery_curve.py --results results.json \
    --prior-snapshots prior.json --output snap.json

  # Override papers_evaluated count
  python3 scripts/discovery_curve.py --results results.json \
    --papers-evaluated 150 --output snap.json
"""

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ── Markdown table parsing ──────────────────────────────────────────────────

def _parse_markdown_table(md_text: str) -> List[Dict]:
    """Parse a pipe-table markdown file into a list of paper dicts.

    Expects columns that include: Score, Tier, DOI, Title, etc.
    Extracts at minimum: _score (int), _tier (str).
    """
    lines = md_text.strip().split("\n")
    papers: List[Dict] = []

    # Find the header row and separator row
    header_idx = -1
    for i, line in enumerate(lines):
        if "|" in line and any(
            kw in line.lower() for kw in ["score", "tier", "分数", "等级"]
        ):
            header_idx = i
            break

    if header_idx < 0:
        return papers

    # Parse header to find column indices
    headers = [h.strip().lower() for h in lines[header_idx].split("|")]
    # Skip the next line (separator like |---|----|)
    data_start = header_idx + 2

    # Map header aliases
    col_map: Dict[str, int] = {}
    for idx, h in enumerate(headers):
        if h in ("score", "分数", "总分"):
            col_map["score"] = idx
        elif h in ("tier", "等级", "tier_level"):
            col_map["tier"] = idx
        elif h in ("doi",):
            col_map["doi"] = idx
        elif h in ("title", "标题", "篇名"):
            col_map["title"] = idx

    for line in lines[data_start:]:
        if not line.strip() or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        try:
            score_val = None
            tier_val = ""
            doi_val = ""

            if "score" in col_map and col_map["score"] < len(cells):
                raw = cells[col_map["score"]]
                # Extract first integer from cell (e.g. "22/25" → 22)
                m = re.search(r"(\d+)", raw)
                if m:
                    score_val = int(m.group(1))

            if "tier" in col_map and col_map["tier"] < len(cells):
                tier_val = cells[col_map["tier"]]

            if "doi" in col_map and col_map["doi"] < len(cells):
                doi_val = cells[col_map["doi"]]

            if score_val is not None:
                papers.append(
                    {
                        "_score": score_val,
                        "_tier": tier_val,
                        "_doi": doi_val,
                    }
                )
        except (IndexError, ValueError):
            continue

    return papers


def _parse_json_results(json_text: str) -> List[Dict]:
    """Parse a JSON results file (list of paper dicts) into scored paper list.

    Each dict should have at minimum: _score (int), _tier (str).
    Also accepts fields: score, tier, doi.
    """
    data = json.loads(json_text)
    if not isinstance(data, list):
        return []

    papers: List[Dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        score_val = item.get("_score") or item.get("score")
        tier_val = item.get("_tier") or item.get("tier") or ""
        if score_val is not None:
            papers.append(
                {
                    "_score": int(score_val),
                    "_tier": str(tier_val),
                    "_doi": item.get("_doi") or item.get("doi", ""),
                }
            )
    return papers


# ── Threshold: "highly relevant" = Tier 1 (>=20)  ──────────────────────────

def _is_highly_relevant(paper: Dict) -> bool:
    """Check if a paper is 'highly relevant' for saturation tracking.

    Uses the existing Tier system:
      - Tier 1: score >= 20  → highly relevant
      - Tier 2: score 15-19  → borderline (counted for saturation)
    """
    tier = paper.get("_tier", "").lower()
    if tier in ("tier 1", "t1", "⭐ tier 1"):
        return True
    score = paper.get("_score", 0)
    return score >= 20


# ── Marginal rates ──────────────────────────────────────────────────────────

def compute_marginal_rates(snapshots: List[Dict]) -> List[float]:
    """Compute per-window marginal discovery rate.

    Each snapshot has: papers_evaluated (int), highly_relevant_count (int).
    Returns one rate per adjacent pair: delta_highly_relevant / delta_evaluated.
    """
    if len(snapshots) < 2:
        return []
    rates: List[float] = []
    for prev, curr in zip(snapshots[:-1], snapshots[1:]):
        d_eval = curr.get("papers_evaluated", 0) - prev.get("papers_evaluated", 0)
        d_rel = curr.get("highly_relevant_count", 0) - prev.get(
            "highly_relevant_count", 0
        )
        if d_eval > 0:
            rates.append(d_rel / d_eval)
    return rates


# ── Exponential fit ─────────────────────────────────────────────────────────

def fit_exponential(
    papers_evaluated: List[int],
    highly_relevant: List[int],
) -> Tuple[float, float]:
    """Fit N(t) = N_total * (1 - exp(-lambda * t)).

    Strategy: compare early-window rate vs recent-window rate.
    If recent < early, the curve is decaying → solve for lambda.
    Otherwise lambda=0.0 signals fit failure.

    Returns (N_total_estimate, lambda). lambda <= 0 means fit_failed.
    """
    if len(papers_evaluated) < 3 or len(highly_relevant) < 3:
        if highly_relevant:
            return (max(1.0, highly_relevant[-1] * 1.5), 0.0)
        return (1.0, 0.0)

    current_t = papers_evaluated[-1]
    current_y = highly_relevant[-1]
    if current_t <= 0 or current_y <= 0:
        return (max(1.0, current_y * 1.5), 0.0)

    cutoff = max(1, len(papers_evaluated) // 5)

    early_dt = papers_evaluated[cutoff] - papers_evaluated[0]
    early_dy = highly_relevant[cutoff] - highly_relevant[0]
    recent_dt = papers_evaluated[-1] - papers_evaluated[-cutoff - 1]
    recent_dy = highly_relevant[-1] - highly_relevant[-cutoff - 1]

    early_rate = (early_dy / early_dt) if early_dt > 0 else 0.0
    recent_rate = (recent_dy / recent_dt) if recent_dt > 0 else 0.0

    if early_rate <= 0 or recent_rate <= 0 or recent_rate >= early_rate:
        return (max(float(current_y), current_y * 1.5), 0.0)

    try:
        lambda_est = -math.log(recent_rate / early_rate) / current_t
    except (ValueError, ZeroDivisionError):
        return (max(float(current_y), current_y * 1.5), 0.0)

    if not math.isfinite(lambda_est) or lambda_est <= 0:
        return (max(float(current_y), current_y * 1.5), 0.0)

    lambda_est = max(1e-4, min(0.2, lambda_est))

    exp_factor = 1.0 - math.exp(-lambda_est * current_t)
    if exp_factor <= 1e-3:
        n_total_est = current_y / 0.5
    else:
        n_total_est = current_y / exp_factor

    n_total_est = max(float(current_y), min(current_y * 5.0, n_total_est))
    return (n_total_est, lambda_est)


# ── Coverage ────────────────────────────────────────────────────────────────

def compute_coverage(
    current_relevant: int,
    n_total: float,
) -> Tuple[float, float, float]:
    """Coverage point estimate + 95% CI bounds.

    Returns (point, lower, upper). All clamped to [0, 1].
    """
    if n_total <= 0:
        return (1.0, 0.5, 1.0)

    point = min(1.0, max(0.0, current_relevant / n_total))
    upper_total = n_total * 0.85
    lower_total = n_total * 1.15
    lower = (
        min(1.0, max(0.0, current_relevant / lower_total))
        if lower_total > 0
        else 0.0
    )
    upper = (
        min(1.0, max(0.0, current_relevant / upper_total))
        if upper_total > 0
        else 1.0
    )
    if lower > upper:
        lower, upper = upper, lower
    return (point, lower, upper)


# ── Snapshot ────────────────────────────────────────────────────────────────

def make_snapshot(
    papers: List[Dict],
    prior_snapshots: Optional[List[Dict]] = None,
    papers_evaluated: Optional[int] = None,
    min_papers: int = 30,
) -> Dict:
    """Compute the current discovery snapshot from a list of scored papers.

    Args:
        papers: list of dicts, each with at least _score (int) and _tier (str).
        prior_snapshots: optional list of earlier snapshots for rate comparison.
        papers_evaluated: optional override (default: len(papers)).
        min_papers: minimum papers required for meaningful fit (default 30).

    Returns:
        snapshot dict with saturation fit + coverage estimate.
    """
    if papers_evaluated is None:
        papers_evaluated = len(papers)

    highly_relevant_count = sum(1 for p in papers if _is_highly_relevant(p))

    # Below threshold: return fit_failed snapshot
    if papers_evaluated < min_papers:
        return {
            "timestamp": datetime.now().isoformat(),
            "papers_evaluated": papers_evaluated,
            "highly_relevant_count": highly_relevant_count,
            "n_total_estimate": 0.0,
            "lambda": 0.0,
            "coverage_estimate": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "fit_failed": True,
            "fit_failed_reason": f"insufficient_data ({papers_evaluated} < {min_papers})",
        }

    history = list(prior_snapshots or [])
    eval_series = [s["papers_evaluated"] for s in history] + [papers_evaluated]
    rel_series = [s["highly_relevant_count"] for s in history] + [
        highly_relevant_count
    ]

    n_total, lambda_est = fit_exponential(eval_series, rel_series)
    point, lower, upper = compute_coverage(highly_relevant_count, n_total)

    return {
        "timestamp": datetime.now().isoformat(),
        "papers_evaluated": papers_evaluated,
        "highly_relevant_count": highly_relevant_count,
        "n_total_estimate": round(n_total, 1),
        "lambda": round(lambda_est, 5),
        "coverage_estimate": round(point, 3),
        "ci_lower": round(lower, 3),
        "ci_upper": round(upper, 3),
        "fit_failed": lambda_est <= 0.0,
    }


# ── Low-progress warning ────────────────────────────────────────────────────

def should_warn_low_progress(
    snapshots: List[Dict],
    min_papers_analyzed: int = 100,
    monotonic_tolerance: float = 0.005,
    monotonic_window: int = 5,
) -> Tuple[bool, str]:
    """Advisory: should we warn that progress has stalled?

    NEVER triggers a hard stop. Returns (should_warn, reason).
    """
    if not snapshots:
        return (False, "insufficient_samples")

    last = snapshots[-1]
    if last.get("papers_evaluated", 0) < min_papers_analyzed:
        return (False, "insufficient_samples")

    if last.get("fit_failed", False):
        return (False, "fit_failed")

    rates = compute_marginal_rates(snapshots)
    if len(rates) < monotonic_window:
        return (False, "insufficient_samples")

    recent = rates[-monotonic_window:]
    for prev, curr in zip(recent[:-1], recent[1:]):
        if curr > prev + monotonic_tolerance:
            return (False, "not_yet_saturated")

    if recent[-1] < 0.02:
        return (
            True,
            f"low_progress (recent_rate={recent[-1]:.3f}, "
            f"coverage={last.get('coverage_estimate', 0.0):.0%})",
        )
    return (False, "not_yet_saturated")


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Discovery saturation curve — fit exponential model to scored "
            "literature results and estimate coverage. ADVISORY ONLY."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 scripts/discovery_curve.py --results 检索文献表.md --output snap.json
  python3 scripts/discovery_curve.py --results results.json --output snap.json --min-papers 20
  python3 scripts/discovery_curve.py --results results.json --prior-snapshots prior.json -o snap.json
        """,
    )
    parser.add_argument(
        "--results",
        required=True,
        type=Path,
        help="Path to results file (.md markdown table or .json list).",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        type=Path,
        help="Where to write the snapshot JSON.",
    )
    parser.add_argument(
        "--prior-snapshots",
        type=Path,
        help="Optional JSON list of prior snapshots for rate comparison.",
    )
    parser.add_argument(
        "--papers-evaluated",
        type=int,
        help="Override for papers_evaluated counter (default: count of scored papers).",
    )
    parser.add_argument(
        "--min-papers",
        type=int,
        default=30,
        help="Minimum papers required for meaningful fit (default: 30).",
    )
    args = parser.parse_args()

    # Load results
    results_text = args.results.read_text(encoding="utf-8")
    if args.results.suffix.lower() in (".md", ".markdown"):
        papers = _parse_markdown_table(results_text)
        print(
            f"discovery_curve: parsed {len(papers)} scored papers from markdown table"
        )
    elif args.results.suffix.lower() == ".json":
        papers = _parse_json_results(results_text)
        print(f"discovery_curve: loaded {len(papers)} scored papers from JSON")
    else:
        # Try JSON first, fall back to markdown
        try:
            papers = _parse_json_results(results_text)
            print(f"discovery_curve: loaded {len(papers)} scored papers (JSON)")
        except (json.JSONDecodeError, ValueError):
            papers = _parse_markdown_table(results_text)
            print(
                f"discovery_curve: parsed {len(papers)} scored papers (markdown fallback)"
            )

    if not papers:
        sys.exit(
            "discovery_curve: no scored papers found in results file. "
            "Ensure the file contains a table with Score and Tier columns, "
            "or a JSON list with _score/_tier fields."
        )

    # Load prior snapshots if provided
    prior_snapshots: List[Dict] = []
    if args.prior_snapshots:
        prior_snapshots = json.loads(
            args.prior_snapshots.read_text(encoding="utf-8")
        )
        if not isinstance(prior_snapshots, list):
            sys.exit("--prior-snapshots must contain a JSON list")

    snapshot = make_snapshot(
        papers=papers,
        prior_snapshots=prior_snapshots,
        papers_evaluated=args.papers_evaluated,
        min_papers=args.min_papers,
    )

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"discovery_curve: wrote snapshot to {args.output}")

    # Summary for agent
    if snapshot["fit_failed"]:
        reason = snapshot.get("fit_failed_reason", "fit returned lambda <= 0")
        print(f"  ⚠️  Fit failed: {reason}")
        print(
            f"  📊 Found {snapshot['highly_relevant_count']} highly relevant "
            f"papers out of {snapshot['papers_evaluated']} total"
        )
    else:
        cov = snapshot["coverage_estimate"]
        ci_l = snapshot["ci_lower"]
        ci_u = snapshot["ci_upper"]
        print(
            f"  📊 Coverage: {cov:.0%} (CI {ci_l:.0%}–{ci_u:.0%}) | "
            f"Estimated total: {snapshot['n_total_estimate']:.0f} papers | "
            f"Highly relevant: {snapshot['highly_relevant_count']}"
        )
        if cov >= 0.85 and (ci_u - ci_l) < 0.15:
            print("  ✅ Good coverage — diminishing returns likely")
        elif cov < 0.6:
            print("  ⚠️  Low coverage — consider expanding search or citation chasing")


if __name__ == "__main__":
    main()
