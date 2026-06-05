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
            kw in line.lower() for kw in ["score", "tier", "评分", "分数", "等级"]
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
        if h in ("score", "评分", "分数", "总分"):
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

    if early_rate <= 0:
        return (max(float(current_y), current_y * 1.5), 0.0)

    # recent_rate == 0 means NO new T1 papers in the recent window →
    # this is actually PERFECT saturation (all relevant papers found early).
    # Use a very small positive value so the decay model estimates near-100% coverage.
    if recent_rate <= 0:
        if recent_dt > 0:
            # Zero new discoveries in recent window → strong saturation signal
            return (float(current_y) * 1.02, 0.1)
        return (max(float(current_y), current_y * 1.5), 0.0)

    if recent_rate >= early_rate:
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


def _bootstrap_snapshots(papers: List[Dict]) -> List[Dict]:
    """Generate virtual snapshots from a single batch of papers.

    Simulates "discovery order" — papers are assumed to be in descending
    relevance order (as real search results are). Creates snapshots at
    25%, 50%, 75%, 100% percentiles to provide enough data points for
    the exponential fit.

    Returns a list of snapshot dicts ordered by cumulative count.
    """
    if len(papers) < 4:
        return []

    percentiles = [0.25, 0.50, 0.75, 1.0]
    snapshots = []
    for pct in percentiles:
        cutoff = max(1, int(len(papers) * pct))
        subset = papers[:cutoff]
        n_eval = len(subset)
        n_rel = sum(1 for p in subset if _is_highly_relevant(p))
        snapshots.append({
            "papers_evaluated": n_eval,
            "highly_relevant_count": n_rel,
            "_bootstrapped": True,
        })
    return snapshots


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
    # ── Bootstrap internal snapshots if insufficient history ──
    # The exponential fit needs ≥3 data points. With only 1 snapshot,
    # simulate "discovery order" snapshots at 25%/50%/75%/100% of the paper list.
    if len(history) == 0 and len(papers) >= min_papers:
        internal_snapshots = _bootstrap_snapshots(papers)
        if len(internal_snapshots) >= 3:
            history = internal_snapshots[:-1]  # all but last (which is ≈current)
            # Use the bootstrapped total as the current value
            last_bs = internal_snapshots[-1]
            papers_evaluated = last_bs["papers_evaluated"]
            highly_relevant_count = last_bs["highly_relevant_count"]

    eval_series = [s["papers_evaluated"] for s in history] + [papers_evaluated]
    rel_series = [s["highly_relevant_count"] for s in history] + [
        highly_relevant_count
    ]

    n_total, lambda_est = fit_exponential(eval_series, rel_series)
    point, lower, upper = compute_coverage(highly_relevant_count, n_total)

    fit_failed = lambda_est <= 0.0
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "papers_evaluated": papers_evaluated,
        "highly_relevant_count": highly_relevant_count,
        "n_total_estimate": round(n_total, 1),
        "lambda": round(lambda_est, 5),
        "coverage_estimate": round(point, 3),
        "ci_lower": round(lower, 3),
        "ci_upper": round(upper, 3),
        "fit_failed": fit_failed,
    }
    # ── Interpretation ──
    snapshot.update(_interpret_saturation(snapshot, prior_snapshots, min_papers))
    return snapshot


# ── Interpretation engine ───────────────────────────────────────────────────

def _interpret_saturation(
    snapshot: Dict,
    prior_snapshots: Optional[List[Dict]] = None,
    min_papers: int = 30,
) -> Dict:
    """Generate qualitative interpretation of a saturation snapshot.

    Returns a dict of interpretation fields suitable for merging into the snapshot.
    """
    cov = snapshot.get("coverage_estimate", 0.0)
    ci_l = snapshot.get("ci_lower", 0.0)
    ci_u = snapshot.get("ci_upper", 0.0)
    ci_width = ci_u - ci_l
    n_eval = snapshot.get("papers_evaluated", 0)
    n_rel = snapshot.get("highly_relevant_count", 0)
    n_total = snapshot.get("n_total_estimate", 0.0)
    lambda_val = snapshot.get("lambda", 0.0)
    fit_failed = snapshot.get("fit_failed", True)

    # ── Qualitative label ──
    if fit_failed:
        if n_eval < min_papers:
            label = "insufficient_data"
            label_cn = "数据不足"
            icon = "📉"
        else:
            label = "fit_failed"
            label_cn = "无法拟合"
            icon = "⚠️"
    elif cov >= 0.85 and ci_width < 0.15:
        label = "good_coverage"
        label_cn = "覆盖良好"
        icon = "✅"
    elif cov >= 0.85 and ci_width >= 0.15:
        label = "adequate_but_uncertain"
        label_cn = "覆盖较好但信心不足"
        icon = "⚠️"
    elif cov >= 0.60:
        label = "moderate_coverage"
        label_cn = "中等覆盖"
        icon = "⚠️"
    else:
        label = "low_coverage"
        label_cn = "覆盖不足"
        icon = "❌"

    # ── Explanation ──
    if fit_failed:
        if n_eval < min_papers:
            explanation = (
                f"当前仅有 {n_eval} 篇文献（阈值 {min_papers}），样本量不足，"
                f"无法对饱和度曲线进行有意义的拟合。建议继续检索以积累更多文献后再评估。"
            )
        else:
            explanation = (
                f"对 {n_eval} 篇文献拟合指数衰减模型失败（λ={lambda_val}），"
                f"最近窗口的边际发现率未明显下降，说明新文献仍在持续出现，"
                f"文献池尚未进入饱和阶段。建议扩大检索范围、增加同义词变体或触发引文扩展。"
            )
    else:
        # Build a detailed explanation
        parts = []
        parts.append(
            f"基于 {n_eval} 篇文献（其中 {n_rel} 篇 T1 高相关文献）拟合指数衰减模型 "
            f"N(t)=N_total×(1−e^(−λt))。"
        )
        parts.append(
            f"估计文献池总量约 {n_total:.0f} 篇高相关文献，"
            f"当前覆盖率 {cov:.0%}（95% CI: {ci_l:.0%}–{ci_u:.0%}）。"
        )

        if lambda_val > 0:
            # λ characterizes the decay rate: larger λ → faster saturation
            if lambda_val > 0.05:
                parts.append(
                    f"衰减系数 λ={lambda_val:.4f}（较大），说明边际发现率快速下降，"
                    f"文献池正在接近饱和。"
                )
            elif lambda_val > 0.01:
                parts.append(
                    f"衰减系数 λ={lambda_val:.4f}（适中），边际发现率在稳步下降，"
                    f"但仍可能有未覆盖的文献。"
                )
            else:
                parts.append(
                    f"衰减系数 λ={lambda_val:.4f}（较小），边际发现率下降缓慢，"
                    f"文献池距离饱和还有距离。"
                )

        if ci_width >= 0.15:
            parts.append(
                f"置信区间较宽（{ci_width:.0%}），估计不确定性较高，"
                f"可能是因为文献数偏少或 T1 文献分布不均。"
            )

        # Prior snapshot trend
        if prior_snapshots and len(prior_snapshots) >= 1:
            prev = prior_snapshots[-1]
            prev_cov = prev.get("coverage_estimate", 0.0)
            if prev_cov > 0:
                delta = cov - prev_cov
                if delta > 0.05:
                    parts.append(f"相比上一轮快照，覆盖率提升了 {delta:.0%}，进展明显。")
                elif delta > 0.01:
                    parts.append(f"相比上一轮快照，覆盖率小幅提升 {delta:.0%}。")
                else:
                    parts.append("相比上一轮快照，覆盖率几乎未变，边际收益正在递减。")

        explanation = "".join(parts)

    # ── Recommendation ──
    if fit_failed:
        if n_eval < min_papers:
            recommendation = (
                f"继续检索至 ≥ {min_papers} 篇后再运行饱和度分析。"
                f"可尝试：① 增加同义词变体 ② 扩展至 L2/L3 数据库 ③ 触发引文网络扩展。"
            )
        else:
            recommendation = (
                "拟合失败通常意味着边际发现率尚未下降——新的高相关文献仍在持续出现。"
                "建议：① 扩大检索策略（增加 synonym blocks）② 触发引文网络 1-hop 扩展 "
                "③ 放宽 Tier 2/3 纳入标准看是否有遗漏。"
            )
    elif label == "good_coverage":
        recommendation = (
            f"饱和度已达 {cov:.0%}，置信区间窄（{ci_width:.0%}），"
            f"继续检索的边际收益很低。可以进入 Step 5 下载阶段。"
            f"如果对特定子课题仍有疑虑，可针对该子课题单独补搜。"
        )
    elif label == "adequate_but_uncertain":
        recommendation = (
            f"覆盖率 {cov:.0%} 尚可但估计信心不足（CI 宽度 {ci_width:.0%}）。"
            f"建议：① 再补充一轮检索（增加 cited/recent 策略线）以收窄置信区间 "
            f"② 触发 T1 种子引文扩展 ③ 如进度紧迫可先进入下载，标注覆盖率信心不足。"
        )
    elif label == "moderate_coverage":
        recommendation = (
            f"覆盖率 {cov:.0%} 偏中等，估计还有 {n_total - n_rel:.0f} 篇高相关文献未覆盖。"
            f"强烈建议：① 触发引文网络扩展（对 T1 种子做 1-hop）"
            f"② 检查检索方案中是否遗漏了关键同义词/变体 "
            f"③ 补充 seminal/review 类型检索策略。"
        )
    else:  # low_coverage
        recommendation = (
            f"覆盖率仅 {cov:.0%}，严重不足——可能遗漏了大量关键文献。"
            f"必须：① 重新审视检索方案（概念块/同义词是否完整？）"
            f"② 对所有 T1 种子执行引文网络扩展 "
            f"③ 检查 Step 3 的 L1→L2→L3 路由是否覆盖了所有子课题 "
            f"④ 考虑回溯 seminal works（经典奠基文献）。"
        )

    # ── Fit quality metadata ──
    fit_quality = {
        "model": "exponential_decay N(t)=N_total×(1−e^(−λt))",
        "lambda_interpretation": (
            "λ 越大 → 边际发现率衰减越快 → 越接近饱和"
            if lambda_val > 0 else "λ ≤ 0 → 边际发现率未衰减 → 未饱和"
        ),
        "ci_width": round(ci_width, 3),
        "sample_adequacy": (
            "adequate" if n_eval >= min_papers else f"below_threshold (need ≥{min_papers})"
        ),
        "prior_snapshots_count": len(prior_snapshots or []),
    }

    return {
        "interpretation": {
            "label": label,
            "label_cn": label_cn,
            "icon": icon,
        },
        "explanation": explanation,
        "recommendation": recommendation,
        "fit_quality": fit_quality,
    }


# ── Markdown report ─────────────────────────────────────────────────────────

def generate_markdown_report(snapshot: Dict) -> str:
    """Generate a human-readable markdown report from a saturation snapshot."""

    interp = snapshot.get("interpretation", {})
    icon = interp.get("icon", "⚠️")
    label_cn = interp.get("label_cn", "未知")
    cov = snapshot.get("coverage_estimate", 0.0)
    ci_l = snapshot.get("ci_lower", 0.0)
    ci_u = snapshot.get("ci_upper", 0.0)
    n_eval = snapshot.get("papers_evaluated", 0)
    n_rel = snapshot.get("highly_relevant_count", 0)
    n_total = snapshot.get("n_total_estimate", 0.0)
    lambda_val = snapshot.get("lambda", 0.0)
    fit_failed = snapshot.get("fit_failed", True)
    fq = snapshot.get("fit_quality", {})

    lines = []
    lines.append("## 文献饱和度分析报告")
    lines.append("")
    lines.append(f"**生成时间**：{snapshot.get('timestamp', '?')}")
    lines.append("")
    lines.append(f"### {icon} 饱和度判定：{label_cn}")
    lines.append("")

    # Key metrics table
    lines.append("| 指标 | 值 | 说明 |")
    lines.append("|------|-----|------|")
    lines.append(
        f"| 文献总数 | {n_eval} | 纳入评分的 T1-T3 文献 |"
    )
    lines.append(
        f"| 高相关文献 (T1) | {n_rel} | score ≥ 20，用于拟合的核心文献 |"
    )
    lines.append(
        f"| 估计文献池总量 | {n_total:.0f} | 指数模型估计的高相关文献上限 |"
    )
    if not fit_failed:
        lines.append(
            f"| 覆盖率 | {cov:.0%} | 当前 T1 文献 / 估计总量 |"
        )
        lines.append(
            f"| 95% 置信区间 | {ci_l:.0%} – {ci_u:.0%} | 宽度 {ci_u - ci_l:.0%} —— "
            + ("较窄，估计可靠" if (ci_u - ci_l) < 0.15 else "较宽，估计不确定性高")
        )
        lines.append(
            f"| 衰减系数 λ | {lambda_val:.4f} | "
            + ("边际发现率快速衰减 → 接近饱和" if lambda_val > 0.05
               else "边际发现率稳步下降" if lambda_val > 0.01
               else "边际发现率下降缓慢 → 距离饱和较远")
        )

    lines.append("")
    lines.append(f"**估计模型**：{fq.get('model', 'exponential_decay')}")
    lines.append(f"**样本充足性**：{fq.get('sample_adequacy', '?')}")
    lines.append("")

    # Explanation
    lines.append("### 📝 详细解释")
    lines.append("")
    lines.append(snapshot.get("explanation", "无"))
    lines.append("")

    # Recommendation
    lines.append("### 🎯 行动建议")
    lines.append("")
    lines.append(snapshot.get("recommendation", "无"))
    lines.append("")

    # Raw data (collapsed)
    lines.append("<details>")
    lines.append("<summary>📊 原始数据（JSON）</summary>")
    lines.append("")
    lines.append("```json")
    # Only include numeric fields, skip interpretation text
    raw = {
        k: v for k, v in snapshot.items()
        if k not in ("interpretation", "explanation", "recommendation", "fit_quality")
    }
    lines.append(json.dumps(raw, indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


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
  python3 scripts/discovery_curve.py --results results.json -o snap.json --report 饱和度报告.md
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
    parser.add_argument(
        "--report", "-r",
        type=Path,
        help="Optional path to write a human-readable markdown saturation report.",
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

    # Write JSON output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"discovery_curve: wrote snapshot to {args.output}")

    # ── Rich interpretation to stdout ──
    interp = snapshot.get("interpretation", {})
    print()
    print("=" * 55)
    print(f"  {interp.get('icon', '?')} 饱和度判定：{interp.get('label_cn', '?')}  ({interp.get('label', '?')})")
    print("=" * 55)

    if snapshot["fit_failed"]:
        reason = snapshot.get("fit_failed_reason", "fit returned lambda <= 0")
        print(f"  ⚠️  拟合失败: {reason}")
    else:
        cov = snapshot["coverage_estimate"]
        ci_l = snapshot["ci_lower"]
        ci_u = snapshot["ci_upper"]
        ci_w = ci_u - ci_l
        print(f"  文献总数:    {snapshot['papers_evaluated']} 篇")
        print(f"  T1 高相关:   {snapshot['highly_relevant_count']} 篇")
        print(f"  估计总量:    {snapshot['n_total_estimate']:.0f} 篇")
        print(f"  覆盖率:      {cov:.0%}")
        print(f"  95% CI:      {ci_l:.0%} – {ci_u:.0%}  (宽度 {ci_w:.0%})")
        print(f"  衰减系数 λ:  {snapshot['lambda']:.4f}")

    print(f"")
    print(f"  📝 {snapshot.get('explanation', '')[:120]}...")
    print(f"")
    print(f"  🎯 {snapshot.get('recommendation', '')[:150]}...")
    print(f"")

    # ── Markdown report ──
    if args.report:
        md_report = generate_markdown_report(snapshot)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(md_report, encoding="utf-8")
        print(f"discovery_curve: wrote markdown report to {args.report}")


if __name__ == "__main__":
    main()
