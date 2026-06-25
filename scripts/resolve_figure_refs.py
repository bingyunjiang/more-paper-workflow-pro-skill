#!/usr/bin/env python3
"""Resolve [图: xxx] markers in a writing draft by matching against figure candidates.

Image quality hierarchy (best → worst):
  1. MinerU ZIP with captions     (source_type=caption_plus_text)
  2. MinerU ZIP without captions  (source_type=visual_pending)
  3. figure_index.json figures    (may have captions)
  4. PyMuPDF direct extraction    (pdf_direct, no captions)
  5. No match → keep placeholder + warning

Usage:
  python scripts/resolve_figure_refs.py \\
    --draft draft.md \\
    --cards deep_read_cards.json \\
    --output draft_resolved.md

  # With multiple card files:
  python scripts/resolve_figure_refs.py \\
    --draft draft.md \\
    --cards section1_cards.json --cards section2_cards.json \\
    --output draft_resolved.md
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
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from workflow_contracts import normalize_doi  # noqa: E402
except ImportError:
    normalize_doi = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _load_json(path: str | Path | None) -> Any:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8", errors="replace"))


def _load_cards(paths: list[str]) -> list[dict[str, Any]]:
    """Load figure_candidates from one or more deep_read_cards.json files."""
    all_candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        payload = _load_json(path)
        records = payload.get("records") if isinstance(payload, dict) else []
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            for fig in record.get("figure_candidates") or []:
                uid = _clean(fig.get("source_image_path") or fig.get("local_image_path"))
                if uid and uid not in seen:
                    seen.add(uid)
                    # Attach source metadata from the card
                    fig_copy = dict(fig)
                    fig_copy["_image_source"] = record.get("source_trace", {}).get("image_source", "unknown")
                    fig_copy["_text_source"] = record.get("source_trace", {}).get("text_source", "unknown")
                    fig_copy["_citekey"] = _clean(record.get("citekey"))
                    fig_copy["_title"] = _clean(record.get("title"))
                    all_candidates.append(fig_copy)
    return all_candidates


def _load_figure_index(path: str | Path | None) -> list[dict[str, Any]]:
    """Load figures from a figure_index.json file."""
    payload = _load_json(path)
    records = payload.get("records") if isinstance(payload, dict) else []
    if isinstance(records, list):
        return [r for r in records if isinstance(r, dict)]
    return []


# ---------------------------------------------------------------------------
# Marker scanning
# ---------------------------------------------------------------------------

_MARKER_PATTERN = re.compile(r"\[图[：:]\s*(.+?)\]")


def _find_markers(text: str) -> list[dict[str, Any]]:
    """Find all [图: xxx] markers in the text.

    Returns list of dicts: {description, start, end, context_before}
    """
    markers: list[dict[str, Any]] = []
    for match in _MARKER_PATTERN.finditer(text):
        desc = match.group(1).strip()
        if not desc:
            continue
        context_start = max(0, match.start() - 300)
        context_before = text[context_start:match.start()]
        markers.append({
            "description": desc,
            "start": match.start(),
            "end": match.end(),
            "context_before": _clean(context_before),
        })
    return markers


# ---------------------------------------------------------------------------
# Figure scoring
# ---------------------------------------------------------------------------

# Keywords that bridge Chinese descriptions to English captions
_DESCRIPTION_BRIDGE: dict[str, list[str]] = {
    "结构": ["structure", "schematic", "diagram", "layout", "internal", "external", "cross section"],
    "示意": ["schematic", "diagram", "overview", "illustration"],
    "流程": ["flow", "process", "pipeline", "workflow", "procedure"],
    "结果": ["result", "comparison", "performance", "experiment", "versus"],
    "对比": ["comparison", "versus", "compare", "baseline"],
    "方法": ["method", "model", "framework", "architecture", "approach"],
    "验证": ["validation", "verification", "experimental", "error"],
    "实验": ["experiment", "experimental", "test", "measurement"],
    "曲线": ["curve", "plot", "trend", "versus"],
    "温度": ["temperature", "thermal", "heat"],
    "气流": ["airflow", "air", "flow", "ventilation"],
    "散热": ["heat dissipation", "thermal", "cooling", "temperature"],
    "充电": ["charging", "charge", "pile"],
    "模块": ["module", "unit", "component"],
    "优化": ["optimization", "optimal", "improve"],
    "网络": ["network", "architecture", "layer"],
    "训练": ["training", "learn", "regression"],
    "分布": ["distribution", "layout", "arrangement"],
    "边界": ["boundary", "edge", "domain"],
    "网格": ["mesh", "grid", "discretization"],
    "模型": ["model", "framework", "schematic"],
    "设计": ["design", "configuration", "layout"],
    "变量": ["variable", "parameter", "factor"],
}


def _description_keywords(description: str, context: str) -> list[str]:
    """Extract matchable keywords from a Chinese description and surrounding context.

    Bridge expansion only uses the description itself (not context) to stay precise.
    Context is only used to find domain-specific English terms already in the text.
    """
    keywords: list[str] = []
    # Phase 1: bridge the Chinese description to English signal terms
    desc_lower = description.lower()
    for chinese_term, english_terms in _DESCRIPTION_BRIDGE.items():
        if chinese_term in desc_lower:
            keywords.extend(english_terms)
    # Phase 2: extract raw English/alphanumeric tokens from description
    for word in re.findall(r"[a-zA-Z0-9._%+\-]{2,}", description):
        keywords.append(word.lower())
    # Phase 3: supplement with domain English terms from surrounding context
    context_en = re.findall(r"[a-zA-Z]{4,}", context.lower())
    from collections import Counter
    context_freq = Counter(context_en)
    # Add top frequent English terms from context (likely domain terms)
    for term, _ in context_freq.most_common(8):
        if term not in {"that", "this", "with", "from", "into", "each", "also"}:
            keywords.append(term)
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for kw in keywords:
        if kw.lower() not in seen and len(kw) >= 2:
            seen.add(kw.lower())
            result.append(kw)
    return result


def _figure_search_blob(fig: dict[str, Any]) -> str:
    """Build a searchable text blob from a figure candidate."""
    parts = [
        _clean(fig.get("figure_id")),
        _clean(fig.get("caption")),
    ]
    return " ".join(p for p in parts if p).lower()


def _image_quality_score(fig: dict[str, Any]) -> int:
    """Score image source quality. Higher = better for writing.

    Quality tiers:
      4 = MinerU ZIP with caption (caption_plus_text)
      3 = MinerU ZIP or figure_index with any caption
      2 = MinerU ZIP without caption / PyMuPDF from MinerU-verified paper
      1 = PyMuPDF direct extraction (no caption)
      0 = unknown
    """
    img_src = _clean(fig.get("_image_source", "")).lower()
    caption = _clean(fig.get("caption", ""))

    if "mineru" in img_src and caption:
        return 4
    if caption:
        return 3
    if "mineru" in img_src:
        return 2
    if "pdf_direct" in img_src or "pymupdf" in img_src:
        return 1
    return 0


def _score_figure(fig: dict[str, Any], keywords: list[str]) -> tuple[int, int]:
    """Score a figure candidate against keywords.

    Returns (keyword_score, quality_score) tuple for sorting.
    Higher keyword_score = better content match.
    Higher quality_score = better source quality.
    """
    blob = _figure_search_blob(fig)
    lowered_kw = [k.lower() for k in keywords if k]
    if not lowered_kw:
        return (0, _image_quality_score(fig))
    keyword_score = sum(1 for kw in lowered_kw if kw in blob)
    return (keyword_score, _image_quality_score(fig))


# ---------------------------------------------------------------------------
# Figure block generation
# ---------------------------------------------------------------------------

def _build_figure_block(
    fig: dict[str, Any],
    fig_number: int,
    description: str,
    draft_path: Path,
) -> str:
    """Build the minimal text-figure unit: 引出句 + 图 + 图注."""
    local = _clean(fig.get("local_image_path"))
    source = _clean(fig.get("source_image_path"))
    img_path = local or source
    if not img_path:
        return f"[图 {fig_number}：{description} — 图片路径缺失]"

    # Compute relative path from draft location
    rel = img_path
    try:
        p = Path(img_path)
        if p.is_absolute():
            try:
                rel = p.relative_to(draft_path.parent).as_posix()
            except (ValueError, OSError):
                rel = p.name
        elif "::" in rel:
            # MinerU ZIP internal path — use only the image filename
            rel = rel.split("::")[-1] if "::" in rel else rel
        else:
            rel = p.as_posix()
    except Exception:
        rel = Path(img_path).name

    raw_caption = _clean(fig.get("caption")) or ""
    orig_figure_id = _clean(fig.get("figure_id")) or ""

    # Strip redundant figure_id prefix from caption (e.g. "Fig. 1. Internal..." → "Internal...")
    if orig_figure_id and raw_caption.lower().startswith(orig_figure_id.lower()):
        raw_caption = raw_caption[len(orig_figure_id):].lstrip(".,;: ")
    # Also strip generic "Fig. N." prefix
    raw_caption = re.sub(r"^Fig\.?\s*\d+[\.\s]*", "", raw_caption, flags=re.IGNORECASE).strip()

    display_caption = raw_caption or description

    # Lead-in sentence (引出句) — use the clean description from caption
    short_cap = display_caption[:80]
    if len(display_caption) > 80:
        short_cap = short_cap[:77].rstrip() + "..."

    lead_in = f"如图 {fig_number} 所示，{short_cap}"

    # Figure markdown
    figure_md = f"![图 {fig_number}]({rel})"

    # Caption line
    caption_line = f"*图 {fig_number}. {display_caption}*"

    return f"{lead_in}\n\n{figure_md}\n\n{caption_line}"


# ---------------------------------------------------------------------------
# Main resolution logic
# ---------------------------------------------------------------------------

def resolve_figure_refs(
    *,
    draft_path: str | Path,
    cards_paths: list[str],
    figure_index_path: str | None = None,
    output_path: str | Path,
) -> int:
    draft_p = Path(draft_path).expanduser().resolve()
    if not draft_p.exists():
        raise SystemExit(f"Draft not found: {draft_p}")
    text = draft_p.read_text(encoding="utf-8", errors="replace")
    markers = _find_markers(text)
    if not markers:
        print("No [图: xxx] markers found — draft unchanged.")
        Path(output_path).expanduser().write_text(text, encoding="utf-8")
        return 0

    # Load figure candidates from deep_read_cards
    all_candidates = _load_cards(cards_paths)

    # Supplement with figure_index if provided
    if figure_index_path:
        fi_figures = _load_figure_index(figure_index_path)
        seen_imgs: set[str] = {
            _clean(f.get("source_image_path") or f.get("local_image_path"))
            for f in all_candidates
        }
        for fig in fi_figures:
            uid = _clean(fig.get("source_image_path") or fig.get("local_image_path"))
            if uid and uid not in seen_imgs:
                seen_imgs.add(uid)
                fig_copy = dict(fig)
                fig_copy["_image_source"] = "figure_index"
                fig_copy["_text_source"] = "unknown"
                all_candidates.append(fig_copy)

    # Collect all available candidates for display purposes
    available_count = len(all_candidates)

    used_figure_ids: set[str] = set()
    resolved_count = 0
    warnings: list[str] = []

    # Process markers in reverse order to preserve positions
    markers.sort(key=lambda m: m["start"])
    replacements: list[tuple[int, int, str]] = []  # (start, end, replacement)

    for marker in markers:
        desc = marker["description"]
        context = marker["context_before"]
        keywords = _description_keywords(desc, context)

        # Score all candidates
        scored = [(fig, *_score_figure(fig, keywords)) for fig in all_candidates]
        # Filter already-used figures
        available = [
            (fig, kw_score, q_score)
            for fig, kw_score, q_score in scored
            if _clean(fig.get("source_image_path") or fig.get("local_image_path"))
            not in used_figure_ids
        ]
        if not available:
            # All figures used — reuse the best one
            available = scored

        # Sort: keyword_score desc, then quality_score desc
        available.sort(key=lambda x: (-x[1], -x[2]))

        best_fig, best_kw_score, best_q_score = available[0] if available else (None, 0, 0)

        if best_fig and best_kw_score > 0:
            fig_number = resolved_count + 1
            block = _build_figure_block(best_fig, fig_number, desc, draft_p)
            replacements.append((marker["start"], marker["end"], block))
            used_figure_ids.add(
                _clean(best_fig.get("source_image_path") or best_fig.get("local_image_path"))
            )
            resolved_count += 1
            qual_label = ["?", "PyMuPDF", "MinerU", "captioned", "captioned+MinerU"][
                min(best_q_score, 4)
            ]
            print(f"  [resolved] {desc!r} → {_clean(best_fig.get('figure_id'))} "
                  f"(kw={best_kw_score}, quality={qual_label})")
        elif best_fig:
            # Keyword score 0 but we have figures — use first unused but warn
            fig_number = resolved_count + 1
            block = _build_figure_block(best_fig, fig_number, desc, draft_p)
            replacements.append((marker["start"], marker["end"], block))
            used_figure_ids.add(
                _clean(best_fig.get("source_image_path") or best_fig.get("local_image_path"))
            )
            resolved_count += 1
            print(f"  [weak match] {desc!r} → {_clean(best_fig.get('figure_id'))} "
                  f"(no keyword overlap, quality={best_q_score})")
            warnings.append(f"弱匹配: {desc!r} → {_clean(best_fig.get('figure_id'))}")
        else:
            # No figures at all
            replacement = (
                f"[图 {resolved_count + 1}：{desc} — "
                f"未找到匹配图片（候选池 {available_count} 张，均未匹配关键词 "
                f"{', '.join(keywords[:5])}）]"
            )
            replacements.append((marker["start"], marker["end"], replacement))
            warnings.append(f"未匹配: {desc!r}（候选池 {available_count} 张）")
            print(f"  [unresolved] {desc!r} — no matching figure in {available_count} candidates")

    # Apply replacements in reverse order
    result = text
    for start, end, repl in reversed(replacements):
        result = result[:start] + repl + result[end:]

    # Add resolution summary at end of document
    summary_lines = [
        "",
        "---",
        "",
        f"<!-- 图表解析报告: {resolved_count}/{len(markers)} 个标记已解析 -->",
    ]
    if warnings:
        summary_lines.append("<!-- 警告:")
        for w in warnings:
            summary_lines.append(f"  - {w}")
        summary_lines.append("-->")
    result = result.rstrip() + "\n" + "\n".join(summary_lines) + "\n"

    Path(output_path).expanduser().write_text(result, encoding="utf-8")
    print(f"RESOLVED: {resolved_count}/{len(markers)} markers → {output_path}")
    if warnings:
        print(f"WARNINGS: {len(warnings)}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve [图: xxx] markers in a writing draft by matching figure candidates."
    )
    parser.add_argument("--draft", required=True, help="Path to draft .md with [图: xxx] markers")
    parser.add_argument(
        "--cards", action="append", default=[],
        help="Path to deep_read_cards.json (repeat for multiple sections)",
    )
    parser.add_argument(
        "--figure-index",
        default=None,
        help="Optional path to figure_index.json for supplementary candidates",
    )
    parser.add_argument("--output", default=None, help="Output path (default: draft_resolved.md)")
    args = parser.parse_args()

    if not args.cards and not args.figure_index:
        print("Warning: no --cards or --figure-index provided; all markers will be unresolved.",
              file=sys.stderr)

    output = args.output or str(Path(args.draft).with_suffix("")) + "_resolved.md"

    return resolve_figure_refs(
        draft_path=args.draft,
        cards_paths=args.cards,
        figure_index_path=args.figure_index,
        output_path=output,
    )


if __name__ == "__main__":
    raise SystemExit(main())
