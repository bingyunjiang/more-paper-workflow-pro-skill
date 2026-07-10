#!/usr/bin/env python3
"""Audit stratified Step 4 saturation and retrieval bias."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from build_research_coverage_matrix import build_coverage_matrix


def _records(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("records", "results", "papers"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def _dominance(counter: Counter[str]) -> tuple[str, float]:
    total = sum(counter.values())
    if not total:
        return "", 0.0
    label, count = counter.most_common(1)[0]
    return label, count / total


def _round_saturation(records: list[dict]) -> dict:
    rounds: dict[int, set[str]] = defaultdict(set)
    for index, record in enumerate(records):
        try:
            round_id = int(record.get("discovery_round") or record.get("search_round") or 0)
        except (TypeError, ValueError):
            round_id = 0
        key = str(record.get("doi") or record.get("source_id") or record.get("title") or index)
        rounds[round_id].add(key)
    nonzero = sorted(round_id for round_id in rounds if round_id > 0)
    if len(nonzero) < 2:
        return {"status": "unknown", "last_round_novelty_rate": None, "round_count": len(nonzero)}
    seen: set[str] = set()
    last_new = 0
    for round_id in nonzero:
        new = rounds[round_id] - seen
        last_new = len(new)
        seen.update(rounds[round_id])
    rate = last_new / max(len(seen), 1)
    return {"status": "saturated" if rate <= 0.05 else "not_saturated", "last_round_novelty_rate": round(rate, 3), "round_count": len(nonzero)}


def audit_search_coverage(search_plan: dict, search_results: object) -> dict:
    records = _records(search_results)
    traceability = build_coverage_matrix(search_plan, search_results)
    sources = Counter(str(r.get("source") or "unknown").lower() for r in records)
    languages = Counter(str(r.get("language") or r.get("lang") or "unknown").lower() for r in records)
    venues = Counter(str(r.get("venue") or r.get("journal") or "unknown") for r in records)
    years = Counter(str(r.get("year") or "unknown") for r in records)
    evidence_types = Counter(str(r.get("evidence_type") or "unknown") for r in records)

    bias_flags = []
    source_label, source_ratio = _dominance(sources)
    language_label, language_ratio = _dominance(languages)
    venue_label, venue_ratio = _dominance(venues)
    if len(records) >= 10 and source_ratio > 0.8:
        bias_flags.append({"flag": "single_source_dependency", "value": source_label, "ratio": round(source_ratio, 3)})
    if len(records) >= 10 and language_ratio > 0.9:
        bias_flags.append({"flag": "language_concentration", "value": language_label, "ratio": round(language_ratio, 3)})
    if len(records) >= 10 and venue_ratio > 0.5:
        bias_flags.append({"flag": "venue_concentration", "value": venue_label, "ratio": round(venue_ratio, 3)})
    contradictory = sum(
        1 for r in records
        if str(r.get("support_grade") or "").lower() in {"contradictory", "limiting", "contradictory_or_limiting"}
        or str((r.get("paper_card") or {}).get("evidence_role") if isinstance(r.get("paper_card"), dict) else "").lower() in {"contradictory", "limiting"}
    )
    if len(records) >= 10 and contradictory == 0:
        bias_flags.append({"flag": "no_contradictory_evidence_identified", "value": "", "ratio": 0.0})

    by_task: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_task[str(record.get("search_task_id") or "unmapped")].append(record)
    task_saturation = {task_id: _round_saturation(items) for task_id, items in sorted(by_task.items())}
    unsaturated = [task_id for task_id, item in task_saturation.items() if item["status"] == "not_saturated"]
    unknown = [task_id for task_id, item in task_saturation.items() if item["status"] == "unknown"]

    return {
        "schema_version": "stratified-search-audit.v1",
        "summary": {
            "record_count": len(records),
            "traceability_covered": traceability["summary"]["all_required_tasks_covered"],
            "bias_flag_count": len(bias_flags),
            "unsaturated_task_ids": unsaturated,
            "unknown_saturation_task_ids": unknown,
            "readiness": "blocked" if not traceability["summary"]["all_required_tasks_covered"] or unsaturated else "partial" if unknown or bias_flags else "complete",
        },
        "traceability": traceability,
        "strata": {
            "sources": dict(sources), "languages": dict(languages), "venues": dict(venues),
            "years": dict(years), "evidence_types": dict(evidence_types),
        },
        "task_saturation": task_saturation,
        "bias_flags": bias_flags,
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Stratified Search Audit", "",
        f"- readiness: `{payload['summary']['readiness']}`",
        f"- record_count: {payload['summary']['record_count']}",
        f"- bias_flag_count: {payload['summary']['bias_flag_count']}", "",
        "## Bias Flags", "",
    ]
    lines.extend(f"- {item['flag']}: {item['value']} ({item['ratio']})" for item in payload["bias_flags"])
    if not payload["bias_flags"]:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Step 4 stratified saturation and bias.")
    parser.add_argument("--search-plan", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--output-json", default="stratified_search_audit.json")
    parser.add_argument("--output-md", default="stratified_search_audit.md")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    plan = json.loads(Path(args.search_plan).read_text(encoding="utf-8"))
    results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    payload = audit_search_coverage(plan, results)
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(payload), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["summary"]["readiness"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
