#!/usr/bin/env python3
"""Build Step 7 mechanism cards and argument plans from deep-read cards."""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import json
import re
from pathlib import Path
from typing import Any


FULLTEXT_DEPTHS = {"full_text", "pdf_verified", "zotero_note", "annotation_verified"}
FIGURE_UNAVAILABLE = "unavailable_without_mineru_or_manual_pdf_check"
FIGURE_AVAILABLE = "available_with_mineru_or_figure_index"
FIGURE_MANUAL = "manual_pdf_check_required"


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean(v) for v in value if _clean(v)]
    if isinstance(value, tuple):
        return [_clean(v) for v in value if _clean(v)]
    text = _clean(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r";|；|\n", text) if part.strip()]


def _load_json(path: str | Path | None) -> Any:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8", errors="replace"))


def _load_records(path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = _load_json(path)
    if isinstance(payload, dict):
        records = payload.get("records")
        if isinstance(records, list):
            return [r for r in records if isinstance(r, dict)], payload.get("metadata") or {}
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)], {}
    raise SystemExit(f"Unsupported deep_read_cards JSON shape: {path}")


def _load_figure_records(path: str | Path | None) -> list[dict[str, Any]]:
    payload = _load_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return [r for r in payload["records"] if isinstance(r, dict)]
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    return []


def _record_key_set(record: dict[str, Any]) -> set[str]:
    source = record.get("source_trace") if isinstance(record.get("source_trace"), dict) else {}
    values = [
        record.get("record_id"),
        record.get("citekey"),
        record.get("title"),
        source.get("zotero_item_key"),
        source.get("source_pdf"),
    ]
    return {_clean(v) for v in values if _clean(v)}


def _match_figures(card: dict[str, Any], figure_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    keys = _record_key_set(card)
    for fig in figure_records:
        fig_keys = {
            _clean(fig.get("item_key")),
            _clean(fig.get("source_item_key")),
            _clean(fig.get("source_attachment_key")),
        }
        if keys & fig_keys:
            matches.append(fig)
    if matches:
        return matches
    candidates = card.get("figure_candidates")
    if isinstance(candidates, list):
        return [c for c in candidates if isinstance(c, dict)]
    return []


def _anchor_level(card: dict[str, Any], anchors: list[dict[str, Any]], figures: list[dict[str, Any]]) -> str:
    if figures:
        for fig in figures:
            source_type = _clean(fig.get("source_type")).lower()
            caption = _clean(fig.get("caption"))
            source_path = _clean(fig.get("source_image_path") or fig.get("local_image_path"))
            if "caption" in source_type or caption or "LLM-for-Zotero-MinerU-cache" in source_path:
                return "mineru_figure_anchor"
        return "pdf_page_or_chunk"

    for anchor in anchors:
        if _clean(anchor.get("page")) or _clean(anchor.get("chunk_id")):
            return "pdf_page_or_chunk"

    source = card.get("source_trace") if isinstance(card.get("source_trace"), dict) else {}
    if _clean(source.get("chunks_json")):
        return "pdf_page_or_chunk"
    if _clean(card.get("reading_depth")).lower() in FULLTEXT_DEPTHS:
        return "pdf_fulltext_no_page"
    return "abstract_or_metadata"


def _figure_status(level: str, figures: list[dict[str, Any]]) -> str:
    if level == "mineru_figure_anchor":
        return FIGURE_AVAILABLE
    if figures:
        return FIGURE_MANUAL
    return FIGURE_UNAVAILABLE


def _claim_strength(card: dict[str, Any], hints: dict[str, Any], anchor_level: str) -> str:
    reading_depth = _clean(card.get("reading_depth")).lower()
    has_chain = bool(hints.get("causal_chain"))
    has_boundary = bool(hints.get("boundary_conditions"))
    has_validation = bool(hints.get("validation_path"))
    if reading_depth in FULLTEXT_DEPTHS and has_chain and has_boundary and has_validation:
        return "strong_mechanism_claim_allowed"
    if reading_depth in FULLTEXT_DEPTHS and has_chain and has_boundary:
        return "moderate_mechanism_claim_allowed"
    if anchor_level == "abstract_or_metadata":
        return "weak_background_or_candidate_only"
    return "candidate_mechanism_only"


def _not_allowed_claims(claim_strength: str, figure_status: str, anchor_level: str) -> list[str]:
    blocked = []
    if claim_strength != "strong_mechanism_claim_allowed":
        blocked.append("不得写成已证明的确定性机理结论")
    if anchor_level in {"abstract_or_metadata", "pdf_fulltext_no_page"}:
        blocked.append("不得写页码、公式号、图号或精确数值级结论")
    if figure_status != FIGURE_AVAILABLE:
        blocked.append("不得自动写“如图X所示”“图中可见”等视觉判断")
    return blocked


def _evidence_anchor(
    card: dict[str, Any],
    hints: dict[str, Any],
    figures: list[dict[str, Any]],
    anchor_level: str,
) -> list[dict[str, Any]]:
    anchors = hints.get("evidence_anchor")
    result = [a for a in anchors if isinstance(a, dict)] if isinstance(anchors, list) else []
    for fig in figures[:3]:
        result.append({
            "type": "figure_or_table",
            "value": _clean(fig.get("figure_id") or fig.get("caption") or fig.get("source_image_path")),
            "page": _clean(fig.get("page")),
            "evidence_level": anchor_level,
        })
    source = card.get("source_trace") if isinstance(card.get("source_trace"), dict) else {}
    if not result and _clean(source.get("source_pdf")):
        result.append({
            "type": "pdf",
            "value": _clean(source.get("source_pdf")),
            "page": "",
            "evidence_level": anchor_level,
        })
    return result


def _build_mechanism_card(card: dict[str, Any], figure_records: list[dict[str, Any]]) -> dict[str, Any]:
    hints = card.get("mechanism_hints") if isinstance(card.get("mechanism_hints"), dict) else {}
    figures = _match_figures(card, figure_records)
    raw_anchors = [a for a in hints.get("evidence_anchor", []) if isinstance(a, dict)] if isinstance(hints.get("evidence_anchor"), list) else []
    anchor_level = _anchor_level(card, raw_anchors, figures)
    figure_status = _figure_status(anchor_level, figures)
    strength = _claim_strength(card, hints, anchor_level)
    anchors = _evidence_anchor(card, hints, figures, anchor_level)
    return {
        "schema_version": "mechanism-card.v1",
        "record_id": _clean(card.get("record_id")),
        "citekey": _clean(card.get("citekey")),
        "title": _clean(card.get("title")),
        "section_id": _clean(card.get("section_id")),
        "section_title": _clean(card.get("section_title")),
        "reading_depth": _clean(card.get("reading_depth")) or "metadata_only",
        "phenomenon": _clean(hints.get("phenomenon") or card.get("claim_summary")),
        "state_variables": _clean_list(hints.get("state_variables")),
        "causal_chain": _clean_list(hints.get("causal_chain")),
        "governing_model": _clean_list(hints.get("governing_model")),
        "boundary_conditions": _clean_list(hints.get("boundary_conditions")),
        "evidence_anchor": anchors,
        "evidence_level": anchor_level,
        "figure_evidence_status": figure_status,
        "alternative_explanations": _clean_list(hints.get("alternative_explanations")),
        "validation_path": _clean_list(hints.get("validation_path")),
        "claim_limit": _clean(hints.get("claim_limit")),
        "claim_strength": strength,
        "not_allowed_claims": _not_allowed_claims(strength, figure_status, anchor_level),
        "source_trace": card.get("source_trace") if isinstance(card.get("source_trace"), dict) else {},
        "risk_flags": _clean_list(card.get("risk_flags")),
    }


def _confirmation_status(card: dict[str, Any]) -> str:
    if card["claim_strength"] == "strong_mechanism_claim_allowed":
        return "confirmed_for_strong_claim"
    if card["claim_strength"] == "moderate_mechanism_claim_allowed":
        return "usable_with_cautious_wording"
    if card["evidence_level"] == "abstract_or_metadata":
        return "downgraded_to_background_or_candidate"
    return "requires_manual_evidence_upgrade"


def _build_argument_item(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": f"mech-{card['record_id'] or card['citekey'] or 'unknown'}",
        "source_citekey": card["citekey"],
        "phenomenon": card["phenomenon"],
        "state_variables": card["state_variables"],
        "causal_chain": card["causal_chain"],
        "governing_model": card["governing_model"],
        "boundary_conditions": card["boundary_conditions"],
        "evidence_anchor": card["evidence_anchor"],
        "evidence_level": card["evidence_level"],
        "figure_evidence_status": card["figure_evidence_status"],
        "validation_path": card["validation_path"],
        "alternative_explanations": card["alternative_explanations"],
        "claim_limit": card["claim_limit"],
        "not_allowed_claims": card["not_allowed_claims"],
        "confirmation_status": _confirmation_status(card),
    }


def audit_plan_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for item in items:
        missing = []
        if not item.get("causal_chain"):
            missing.append("causal_chain")
        if not item.get("boundary_conditions"):
            missing.append("boundary_conditions")
        if not item.get("validation_path"):
            missing.append("validation_path")
        if not item.get("evidence_anchor"):
            missing.append("evidence_anchor")
        if item.get("evidence_level") == "abstract_or_metadata":
            missing.append("full_text_evidence")
        severity = "pass" if not missing else "downgrade_required"
        findings.append({
            "claim_id": item.get("claim_id", ""),
            "source_citekey": item.get("source_citekey", ""),
            "severity": severity,
            "missing": missing,
            "recommended_action": "可写强机理主张" if severity == "pass" else "降级为候选机制，并补全文/页码/图表/验证锚点",
        })
    return findings


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _render_cards_md(cards: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    lines = ["# Mechanism Cards", "", f"- source_cards: {metadata.get('source_cards', '')}", f"- records: {len(cards)}", ""]
    for card in cards:
        lines.extend([
            f"## {card['citekey'] or card['record_id'] or 'unknown'} - {card['title']}",
            "",
            f"- reading_depth: {card['reading_depth']}",
            f"- evidence_level: {card['evidence_level']}",
            f"- figure_evidence_status: {card['figure_evidence_status']}",
            f"- claim_strength: {card['claim_strength']}",
            f"- phenomenon: {card['phenomenon']}",
            f"- state_variables: {'; '.join(card['state_variables']) or '待补充'}",
            "",
            "### Causal Chain",
        ])
        lines.extend([f"- {item}" for item in card["causal_chain"]] or ["- 待补充"])
        lines.append("")
        lines.append("### Evidence Anchors")
        lines.extend([
            f"- {a.get('type', '')}: {a.get('value', '')} page={a.get('page', '')} level={a.get('evidence_level', card['evidence_level'])}"
            for a in card["evidence_anchor"]
        ] or ["- 待补充"])
        lines.append("")
        lines.append("### Not Allowed Claims")
        lines.extend([f"- {item}" for item in card["not_allowed_claims"]] or ["- 未触发"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_plan_md(items: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    lines = ["# Mechanism Argument Plan", "", f"- source_cards: {metadata.get('source_cards', '')}", f"- claims: {len(items)}", ""]
    for item in items:
        lines.extend([
            f"## {item['claim_id']}",
            "",
            f"- source_citekey: {item['source_citekey']}",
            f"- confirmation_status: {item['confirmation_status']}",
            f"- evidence_level: {item['evidence_level']}",
            f"- figure_evidence_status: {item['figure_evidence_status']}",
            f"- phenomenon: {item['phenomenon']}",
            f"- boundary_conditions: {'; '.join(item['boundary_conditions']) or '待补充'}",
            f"- validation_path: {'; '.join(item['validation_path']) or '待补充'}",
            "",
            "### Causal Chain",
        ])
        lines.extend([f"- {entry}" for entry in item["causal_chain"]] or ["- 待补充"])
        lines.append("")
        lines.append("### Not Allowed Claims")
        lines.extend([f"- {entry}" for entry in item["not_allowed_claims"]] or ["- 未触发"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_gap_md(audit: list[dict[str, Any]]) -> str:
    lines = ["# Evidence Gap List", ""]
    gaps = [item for item in audit if item["severity"] != "pass"]
    if not gaps:
        lines.append("- 未发现必须降级的机理主张。")
        return "\n".join(lines) + "\n"
    for item in gaps:
        lines.extend([
            f"## {item['claim_id']}",
            "",
            f"- source_citekey: {item['source_citekey']}",
            f"- missing: {'; '.join(item['missing'])}",
            f"- recommended_action: {item['recommended_action']}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def build_mechanism_argument_plan(
    *,
    cards_json: Path,
    figure_index: str | None,
    output_dir: Path,
    output_prefix: str = "",
) -> int:
    records, card_metadata = _load_records(cards_json)
    figure_records = _load_figure_records(figure_index)
    output_dir.mkdir(parents=True, exist_ok=True)

    mechanism_cards = [_build_mechanism_card(record, figure_records) for record in records]
    plan_items = [_build_argument_item(card) for card in mechanism_cards]
    audit = audit_plan_items(plan_items)
    metadata = {
        "schema_version": "mechanism-analysis-artifacts.v1",
        "source_cards": str(cards_json),
        "source_card_metadata": card_metadata,
        "figure_index": str(figure_index or ""),
        "figure_evidence_fallback": FIGURE_UNAVAILABLE,
        "evidence_priority": "MinerU 图表锚点 > PDF 页/段落锚点 > PDF 全文无页码锚点 > 摘要/元数据",
    }

    prefix = f"{output_prefix}_" if output_prefix else ""
    cards_json_out = output_dir / f"{prefix}mechanism_cards.json"
    cards_md_out = output_dir / f"{prefix}mechanism_cards.md"
    plan_json_out = output_dir / f"{prefix}mechanism_argument_plan.json"
    plan_md_out = output_dir / f"{prefix}mechanism_argument_plan.md"
    audit_json_out = output_dir / f"{prefix}mechanism_claim_audit.json"
    gap_md_out = output_dir / f"{prefix}evidence_gap_list.md"

    _write_json(cards_json_out, {
        "schema_version": "mechanism-cards.v1",
        "metadata": metadata,
        "records": mechanism_cards,
    })
    cards_md_out.write_text(_render_cards_md(mechanism_cards, metadata), encoding="utf-8")
    _write_json(plan_json_out, {
        "schema_version": "mechanism-argument-plan.v1",
        "metadata": metadata,
        "claims": plan_items,
    })
    plan_md_out.write_text(_render_plan_md(plan_items, metadata), encoding="utf-8")
    _write_json(audit_json_out, {
        "schema_version": "mechanism-claim-audit.v1",
        "metadata": metadata,
        "findings": audit,
    })
    gap_md_out.write_text(_render_gap_md(audit), encoding="utf-8")

    print(f"MECHANISM_CARDS: {cards_json_out}")
    print(f"MECHANISM_ARGUMENT_PLAN: {plan_json_out}")
    print(f"MECHANISM_CLAIM_AUDIT: {audit_json_out}")
    print(f"EVIDENCE_GAP_LIST: {gap_md_out}")
    print(f"CLAIMS: {len(plan_items)}")
    print(f"DOWNGRADED: {sum(1 for item in audit if item['severity'] != 'pass')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Step 7 mechanism argument plan from deep_read_cards.json.")
    parser.add_argument("--cards-json", required=True, help="Path to deep_read_cards.json")
    parser.add_argument("--figure-index", help="Optional figure_index.json generated from MinerU ZIP or equivalent")
    parser.add_argument("--output-dir", default=".", help="Directory for mechanism artifacts")
    parser.add_argument("--output-prefix", default="", help="Optional output filename prefix")
    args = parser.parse_args()
    return build_mechanism_argument_plan(
        cards_json=Path(args.cards_json).expanduser().resolve(),
        figure_index=args.figure_index,
        output_dir=Path(args.output_dir).expanduser(),
        output_prefix=args.output_prefix,
    )


if __name__ == "__main__":
    raise SystemExit(main())
