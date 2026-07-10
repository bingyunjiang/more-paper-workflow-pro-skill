#!/usr/bin/env python3
"""Compile Step 3 queries and evaluate optional pilot-search results."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


ENGLISH_SOURCES = {"openalex", "crossref", "semantic_scholar", "arxiv", "pubmed"}


def _quote(term: str) -> str:
    term = term.strip()
    return f'"{term}"' if " " in term else term


def _compile(blocks: list[dict], exclusions: list[str], source: str) -> str:
    compiled_blocks = []
    for block in blocks:
        terms = [str(term).strip() for term in block.get("terms", []) if str(term).strip()]
        if terms:
            compiled_blocks.append("(" + " OR ".join(_quote(term) for term in terms) + ")")
    query = " AND ".join(compiled_blocks)
    if exclusions:
        query += " NOT (" + " OR ".join(_quote(str(term)) for term in exclusions) + ")"
    if source in {"cnki", "wanfang"}:
        return query.replace(" AND ", " * ").replace(" OR ", " + ").replace(" NOT ", " - ")
    return query


def _sources(task: dict) -> list[str]:
    route = task.get("route") if isinstance(task.get("route"), dict) else {}
    values = []
    for level in ("l1", "l2", "l3"):
        for source in route.get(level, []) or []:
            normalized = str(source).strip().lower()
            if normalized and normalized not in values:
                values.append(normalized)
    return values


def lint_and_compile(plan: dict, pilot_results: object | None = None) -> dict:
    tasks = plan.get("search_tasks", []) if isinstance(plan, dict) else []
    pilot_records = []
    if isinstance(pilot_results, list):
        pilot_records = [item for item in pilot_results if isinstance(item, dict)]
    elif isinstance(pilot_results, dict):
        pilot_records = [item for item in pilot_results.get("records", []) if isinstance(item, dict)]
    pilot_by_task: dict[str, list[dict]] = defaultdict(list)
    for record in pilot_records:
        pilot_by_task[str(record.get("search_task_id") or "")].append(record)

    outputs = []
    all_errors = 0
    for task in tasks:
        task_id = str(task.get("id") or "")
        blocks = task.get("query_blocks", []) if isinstance(task.get("query_blocks"), list) else []
        exclusions = [str(item).strip() for item in task.get("exclusion_terms", []) if str(item).strip()]
        errors = []
        warnings = []
        if len(blocks) > 4:
            errors.append("and_block_count_exceeds_4")
        positive_terms = []
        for index, block in enumerate(blocks):
            terms = [str(item).strip() for item in block.get("terms", []) if str(item).strip()] if isinstance(block, dict) else []
            normalized = [term.lower() for term in terms]
            positive_terms.extend(terms)
            if len(set(normalized)) < 2:
                errors.append(f"block_{index}_needs_two_unique_terms")
            if len(normalized) != len(set(normalized)):
                warnings.append(f"block_{index}_duplicate_terms")
        collisions = sorted(set(term.lower() for term in positive_terms) & set(term.lower() for term in exclusions))
        if collisions:
            errors.append("exclusion_collision_with_positive:" + ",".join(collisions))

        compiled = {}
        for source in _sources(task):
            if source in ENGLISH_SOURCES and positive_terms and all(re.search(r"[\u4e00-\u9fff]", term) for term in positive_terms):
                errors.append(f"english_source_has_only_chinese_terms:{source}")
            compiled[source] = _compile(blocks, exclusions, source)

        pilot = pilot_by_task.get(task_id, [])
        pilot_summary = {"status": "not_run", "hit_count": 0, "title_relevance_ratio": None}
        if pilot_results is not None:
            core_terms = [term.lower() for term in positive_terms]
            relevant = sum(
                1 for record in pilot
                if any(term in str(record.get("title") or "").lower() for term in core_terms)
            )
            ratio = relevant / len(pilot) if pilot else 0.0
            status = "zero-result" if not pilot else "suspected_query_drift" if ratio < 0.3 else "too-broad" if len(pilot) >= 10 and ratio < 0.5 else "ok"
            pilot_summary = {"status": status, "hit_count": len(pilot), "title_relevance_ratio": round(ratio, 3)}
            if status != "ok":
                errors.append(f"pilot_{status}")

        all_errors += len(errors)
        outputs.append({
            "search_task_id": task_id,
            "compiled_queries": compiled,
            "lint_errors": errors,
            "lint_warnings": warnings,
            "pilot": pilot_summary,
        })
    return {
        "schema_version": "compiled-search-plan.v1",
        "summary": {"task_count": len(outputs), "error_count": all_errors, "status": "pass" if all_errors == 0 else "fail"},
        "tasks": outputs,
    }


def run_pilot(plan: dict, limit: int = 10, search_functions: dict | None = None) -> dict:
    if search_functions is None:
        from search_by_topic import SOURCE_FUNCTIONS

        search_functions = SOURCE_FUNCTIONS
    records = []
    errors = []
    for task in plan.get("search_tasks", []) if isinstance(plan, dict) else []:
        task_id = str(task.get("id") or "")
        sources = _sources(task)
        if not sources:
            errors.append({"search_task_id": task_id, "error": "no_routed_source"})
            continue
        source = sources[0]
        search = search_functions.get(source)
        if not search:
            errors.append({"search_task_id": task_id, "error": f"source_not_available:{source}"})
            continue
        query = _compile(task.get("query_blocks", []), task.get("exclusion_terms", []), source)
        try:
            results = search(query, limit, use_cache=False)
        except Exception as exc:
            errors.append({"search_task_id": task_id, "error": f"pilot_failed:{type(exc).__name__}"})
            continue
        for result in results[:limit]:
            if isinstance(result, dict):
                record = dict(result)
                record["search_task_id"] = task_id
                record["pilot_source"] = source
                records.append(record)
    return {"schema_version": "pilot-search-results.v1", "records": records, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint and compile Step 3 search plan.")
    parser.add_argument("search_plan")
    parser.add_argument("--pilot-results")
    parser.add_argument("--run-pilot", action="store_true", help="Execute a small search against each task's L1 source.")
    parser.add_argument("--pilot-limit", type=int, default=10)
    parser.add_argument("--pilot-output", default="pilot_search_results.json")
    parser.add_argument("--output", default="compiled_queries.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    plan = json.loads(Path(args.search_plan).read_text(encoding="utf-8"))
    pilot = json.loads(Path(args.pilot_results).read_text(encoding="utf-8")) if args.pilot_results else None
    if args.run_pilot:
        pilot = run_pilot(plan, limit=max(1, min(args.pilot_limit, 10)))
        Path(args.pilot_output).write_text(json.dumps(pilot, ensure_ascii=False, indent=2), encoding="utf-8")
    payload = lint_and_compile(plan, pilot)
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
