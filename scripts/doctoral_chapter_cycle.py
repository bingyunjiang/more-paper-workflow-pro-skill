#!/usr/bin/env python3
"""Prepare and close a chapter while preserving whole-thesis logic."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def prepare(draft: Path, mapping: dict, chapter_id: str) -> dict:
    chapters = mapping.get("chapters") or []
    chapter = next((x for x in chapters if x.get("id") == chapter_id), None)
    provisional = chapter is None
    chapter = chapter or {"id": chapter_id, "rq_ids": [], "claim_ids": [], "result_ids": [], "contribution_ids": []}
    other_claims = {
        claim: item.get("id")
        for item in chapters if item.get("id") != chapter_id
        for claim in item.get("claim_ids", [])
    }
    return {
        "schema_version": "doctoral-chapter-snapshot.v1",
        "status": "provisional" if provisional else "prepared",
        "draft_sha256_at_prepare": sha256(draft),
        "map_sha256_at_prepare": hashlib.sha256(json.dumps(mapping, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        "chapter_id": chapter_id,
        "central_research_problem": mapping.get("central_research_problem"),
        "rq_ids": chapter.get("rq_ids", []),
        "allowed_claim_ids": chapter.get("claim_ids", []),
        "allowed_result_ids": chapter.get("result_ids", []),
        "allowed_contribution_ids": chapter.get("contribution_ids", []),
        "evidence_anchors": chapter.get("evidence_anchors", []),
        "transition_from": chapter.get("transition_from"),
        "transition_to": chapter.get("transition_to"),
        "reserved_claim_owners": other_claims,
        "prior_chapter_closures": [{"chapter_id": x.get("id"), "actual_claim_ids": x.get("actual_claim_ids", []), "actual_result_ids": x.get("actual_result_ids", [])} for x in chapters if x.get("writing_state") == "closed"],
        "global_context_gaps": ["chapter_not_in_global_map"] if provisional else [],
    }


def close(draft: Path, mapping: dict, snapshot: dict, record: dict) -> tuple[dict, dict]:
    findings = []
    chapter_id = snapshot.get("chapter_id")
    current_map_hash = hashlib.sha256(json.dumps(mapping, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if snapshot.get("map_sha256_at_prepare") != current_map_hash:
        findings.append({"code": "stale_snapshot", "message": "全文地图在 prepare 后已变化，请重新 prepare"})
    if snapshot.get("status") == "provisional":
        findings.append({"code": "provisional_snapshot", "message": "当前章未登记在全文地图中，不能自动回写"})
    actual_claims = set(record.get("actual_claim_ids") or [])
    actual_results = set(record.get("actual_result_ids") or [])
    allowed_claims = set(snapshot.get("allowed_claim_ids") or [])
    allowed_results = set(snapshot.get("allowed_result_ids") or [])
    actual_contributions = set(record.get("actual_contribution_ids") or [])
    allowed_contributions = set(snapshot.get("allowed_contribution_ids") or [])
    reserved = snapshot.get("reserved_claim_owners") or {}
    for claim in sorted(actual_claims):
        if claim in reserved:
            findings.append({"code": "later_chapter_claim_taken", "message": f"{claim} belongs to {reserved[claim]}"})
        elif claim not in allowed_claims:
            findings.append({"code": "unplanned_claim", "message": f"{claim} is not allowed for {chapter_id}"})
    for result in sorted(actual_results - allowed_results):
        findings.append({"code": "unregistered_result", "message": f"{result} is not registered for {chapter_id}"})
    for contribution in sorted(actual_contributions - allowed_contributions):
        findings.append({"code": "contribution_boundary_drift", "message": f"{contribution} is not assigned to {chapter_id}"})
    prior_claims = {claim for item in snapshot.get("prior_chapter_closures") or [] for claim in item.get("actual_claim_ids", [])}
    for claim in sorted(actual_claims & prior_claims):
        findings.append({"code": "cross_chapter_claim_duplicate", "message": f"{claim} was already closed in a prior chapter"})
    for field in ("evidence_anchors", "boundary_updates", "unresolved_questions", "next_chapter_obligations"):
        if field not in record:
            findings.append({"code": f"missing_{field}", "message": f"close record requires {field}"})
    status = "conflict" if findings else "closed"
    report = {"schema_version": "doctoral-chapter-cycle-report.v1", "status": status, "chapter_id": chapter_id, "findings": findings}
    if findings:
        return mapping, report
    updated = json.loads(json.dumps(mapping, ensure_ascii=False))
    chapter = next(x for x in updated["chapters"] if x.get("id") == chapter_id)
    chapter.update({
        "writing_state": "closed",
        "actual_claim_ids": sorted(actual_claims),
        "actual_result_ids": sorted(actual_results),
        "actual_contribution_ids": sorted(actual_contributions),
        "actual_evidence_anchors": record["evidence_anchors"],
        "boundary_updates": record["boundary_updates"],
        "unresolved_questions": record["unresolved_questions"],
        "next_chapter_obligations": record["next_chapter_obligations"],
        "last_draft_sha256": sha256(draft),
    })
    updated["draft_sha256"] = sha256(draft)
    updated.setdefault("chapter_cycle_log", []).append({"chapter_id": chapter_id, "status": "closed", "draft_sha256": sha256(draft)})
    return updated, report


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("prepare")
    pre.add_argument("draft", type=Path); pre.add_argument("map", type=Path); pre.add_argument("chapter_id"); pre.add_argument("snapshot", type=Path)
    post = sub.add_parser("close")
    post.add_argument("draft", type=Path); post.add_argument("map", type=Path); post.add_argument("snapshot", type=Path); post.add_argument("record", type=Path); post.add_argument("--report", type=Path)
    args = parser.parse_args()
    mapping = load(args.map)
    if args.command == "prepare":
        payload = prepare(args.draft, mapping, args.chapter_id)
        atomic_json(args.snapshot, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2)); return 0
    updated, report = close(args.draft, mapping, load(args.snapshot), load(args.record))
    if report["status"] == "closed":
        atomic_json(args.map, updated)
    if args.report:
        atomic_json(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "closed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
