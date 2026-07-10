#!/usr/bin/env python3
"""Build Step 1-4 research-question and evidence coverage matrix."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


VERIFIED = {"verified", "verified_local"}
T1_T2 = {"t1", "t2", "tier 1", "tier 2"}
CONTRADICTORY_ROLES = {"contradictory", "limiting", "contradictory_or_limiting"}


def _load(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _records(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("records", "results", "papers"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _tasks(payload: object) -> list[dict]:
    if isinstance(payload, dict) and isinstance(payload.get("search_tasks"), list):
        return [item for item in payload["search_tasks"] if isinstance(item, dict)]
    return []


def _tier(record: dict) -> str:
    return str(record.get("paper_tier") or record.get("_tier") or record.get("Tier") or "").strip().lower()


def _is_contradictory(record: dict) -> bool:
    card = record.get("paper_card") if isinstance(record.get("paper_card"), dict) else {}
    values = {
        str(record.get("support_grade") or "").lower(),
        str(card.get("evidence_role") or "").lower(),
    }
    return bool(values & CONTRADICTORY_ROLES)


def build_coverage_matrix(search_plan: object, search_results: object) -> dict:
    tasks = _tasks(search_plan)
    records = _records(search_results)
    by_task: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        task_ids = [record.get("search_task_id"), *(record.get("secondary_search_task_ids") or [])]
        for task_id in {str(item).strip() for item in task_ids if str(item or "").strip()}:
            by_task[task_id].append(record)

    rows = []
    for task in tasks:
        task_id = str(task.get("id") or "").strip()
        matched = by_task.get(task_id, [])
        verified = [r for r in matched if str(r.get("verification_status") or "").lower() in VERIFIED]
        strong = [r for r in verified if _tier(r) in T1_T2]
        contradictory = [r for r in matched if _is_contradictory(r)]
        minimum = int(task.get("minimum_t1_t2") or 2)
        if not matched:
            status = "uncovered"
        elif not verified or not strong:
            status = "weak"
        elif len(strong) < minimum:
            status = "draft-ready"
        else:
            status = "strong-ready"
        rows.append({
            "rq_id": str(task.get("rq_id") or task.get("research_question_id") or ""),
            "chapter_id": str(task.get("chapter_id") or ""),
            "chapter_title": str(task.get("chapter_title") or ""),
            "search_task_id": task_id,
            "question_to_answer": str(task.get("question_to_answer") or ""),
            "evidence_type": str(task.get("evidence_type") or ""),
            "minimum_t1_t2": minimum,
            "retrieved_count": len(matched),
            "verified_count": len(verified),
            "t1_t2_count": len(strong),
            "contradictory_count": len(contradictory),
            "coverage_status": status,
            "remaining_gap": "" if status == "strong-ready" else "补充已验证 T1/T2 证据或修复查询式",
        })

    status_counts = {status: sum(1 for row in rows if row["coverage_status"] == status) for status in [
        "uncovered", "weak", "draft-ready", "strong-ready",
    ]}
    return {
        "schema_version": "research-traceability-matrix.v1",
        "summary": {
            "search_task_count": len(rows),
            "result_count": len(records),
            "status_counts": status_counts,
            "all_required_tasks_covered": bool(rows) and status_counts["uncovered"] == 0 and status_counts["weak"] == 0,
        },
        "rows": rows,
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Research Traceability Matrix",
        "",
        "| RQ | Chapter | Search Task | Evidence Type | Retrieved | Verified | T1/T2 | Contradictory | Status |",
        "|---|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['rq_id']} | {row['chapter_id']} {row['chapter_title']} | {row['search_task_id']} | "
            f"{row['evidence_type']} | {row['retrieved_count']} | {row['verified_count']} | "
            f"{row['t1_t2_count']} | {row['contradictory_count']} | {row['coverage_status']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Step 1-4 research coverage matrix.")
    parser.add_argument("--search-plan", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--output-json", default="research_traceability_matrix.json")
    parser.add_argument("--output-md", default="research_traceability_matrix.md")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build_coverage_matrix(_load(args.search_plan), _load(args.results))
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(payload), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["summary"]["all_required_tasks_covered"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
