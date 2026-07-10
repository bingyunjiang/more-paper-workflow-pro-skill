#!/usr/bin/env python3
"""Validate structured Step 1, Step 2, or Step 3 artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


STEP1_SCORE_AXES = ["originality", "importance", "feasibility", "literature_support", "method_readiness"]
STEP2_REQUIRED = ["section_id", "section_title", "section_function", "key_claims", "evidence_needed", "do_not_write"]
STEP3_REQUIRED = ["id", "rq_id", "chapter_id", "evidence_type", "question_to_answer", "query_blocks", "route", "tier"]


def _frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    payload = yaml.safe_load(parts[1])
    return payload if isinstance(payload, dict) else {}


def _nonempty(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None


def validate_step1(path: Path) -> list[str]:
    data = _frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    errors = []
    topic = data.get("topic") if isinstance(data.get("topic"), dict) else {}
    for field in ["focused_topic", "primary_rq", "scope_boundaries", "evaluation_metrics"]:
        if not _nonempty(topic.get(field)):
            errors.append(f"topic.{field} is required")
    if len(topic.get("evaluation_metrics") or []) < 3:
        errors.append("topic.evaluation_metrics must contain at least 3 measurable metrics")
    for field in ["working_hypothesis", "falsification_condition", "minimum_viable_study", "topic_kill_criteria"]:
        if not _nonempty(topic.get(field)):
            errors.append(f"topic.{field} is required")

    pre = data.get("pre_review") if isinstance(data.get("pre_review"), dict) else {}
    scores = []
    for axis in STEP1_SCORE_AXES:
        record = pre.get(axis)
        if not isinstance(record, dict):
            errors.append(f"pre_review.{axis} is required")
            continue
        score = record.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 5:
            errors.append(f"pre_review.{axis}.score must be 0-5")
        else:
            scores.append(score)
        if not _nonempty(record.get("reason")):
            errors.append(f"pre_review.{axis}.reason is required")
    if len(scores) == len(STEP1_SCORE_AXES):
        total = sum(scores)
        if pre.get("total_score") != total:
            errors.append(f"pre_review.total_score must equal {total}")
        expected = "green" if total >= 21 else "yellow" if total >= 15 else "red"
        if pre.get("decision") != expected:
            errors.append(f"pre_review.decision must be {expected} for total_score={total}")
    return errors


def _json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_step2(path: Path) -> list[str]:
    payload = _json(path)
    sections = payload if isinstance(payload, list) else payload.get("sections", []) if isinstance(payload, dict) else []
    if not isinstance(sections, list) or not sections:
        return ["section_blueprints must contain a non-empty section list"]
    errors = []
    seen = set()
    rq_coverage = set()
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            errors.append(f"sections[{index}] must be an object")
            continue
        for field in STEP2_REQUIRED:
            if not _nonempty(section.get(field)):
                errors.append(f"sections[{index}].{field} is required")
        section_id = str(section.get("section_id") or "")
        if section_id in seen:
            errors.append(f"duplicate section_id: {section_id}")
        seen.add(section_id)
        rq_ids = section.get("rq_ids") or []
        if not rq_ids and section.get("section_function") not in {"conclusion-and-outlook", "front-matter"}:
            errors.append(f"sections[{index}].rq_ids is required for traceability")
        rq_coverage.update(str(item) for item in rq_ids)
    required_rqs = payload.get("core_research_question_ids", []) if isinstance(payload, dict) else []
    for rq_id in required_rqs:
        if str(rq_id) not in rq_coverage:
            errors.append(f"research question is not mapped to any section: {rq_id}")
    return errors


def validate_step3(path: Path) -> list[str]:
    payload = _json(path)
    tasks = payload.get("search_tasks", []) if isinstance(payload, dict) else []
    if not isinstance(tasks, list) or not tasks:
        return ["search_tasks must be a non-empty list"]
    errors = []
    seen = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"search_tasks[{index}] must be an object")
            continue
        for field in STEP3_REQUIRED:
            if not _nonempty(task.get(field)):
                errors.append(f"search_tasks[{index}].{field} is required")
        task_id = str(task.get("id") or "")
        if task_id in seen:
            errors.append(f"duplicate search task id: {task_id}")
        seen.add(task_id)
        blocks = task.get("query_blocks") or []
        if len(blocks) > 4:
            errors.append(f"search_tasks[{index}] has more than 4 AND blocks")
        for block_index, block in enumerate(blocks):
            terms = block.get("terms", []) if isinstance(block, dict) else []
            if len({str(term).strip().lower() for term in terms if str(term).strip()}) < 2:
                errors.append(f"search_tasks[{index}].query_blocks[{block_index}] needs at least 2 unique terms")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Step 1/2/3 structured output.")
    parser.add_argument("step", choices=["step1", "step2", "step3"])
    parser.add_argument("artifact")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    validators = {"step1": validate_step1, "step2": validate_step2, "step3": validate_step3}
    errors = validators[args.step](Path(args.artifact))
    payload = {"step": args.step, "status": "pass" if not errors else "fail", "errors": errors}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{args.step.upper()}_VALIDATION: {payload['status']}")
        for error in errors:
            print(f"FAIL: {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
