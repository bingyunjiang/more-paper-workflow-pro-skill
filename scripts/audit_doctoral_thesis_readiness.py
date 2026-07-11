#!/usr/bin/env python3
"""Audit whole-thesis doctoral argument closure against the current draft."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _present(value) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def audit(draft: Path, mapping: dict, require_closed: bool = False) -> dict:
    findings = []

    def need(ok: bool, code: str, message: str, location: str) -> None:
        if not ok:
            findings.append({"code": code, "location": location, "message": message})

    actual_hash = hashlib.sha256(draft.read_bytes()).hexdigest()
    need(mapping.get("schema_version") == "doctoral-thesis-map.v1", "schema", "schema_version 必须为 doctoral-thesis-map.v1", "schema_version")
    need(mapping.get("draft_sha256") == actual_hash, "stale_map", "映射与当前稿件哈希不一致", "draft_sha256")
    need(_present(mapping.get("central_research_problem")), "central_problem", "缺少可研究的中心问题", "central_research_problem")

    rqs = mapping.get("research_questions") or []
    results = {x.get("id") for x in mapping.get("results") or [] if x.get("id")}
    need(bool(rqs), "research_questions", "至少需要一个研究问题", "research_questions")
    for i, rq in enumerate(rqs):
        base = f"research_questions[{i}]"
        for key in ("id", "question", "chapter_ids", "result_ids", "conclusion"):
            need(_present(rq.get(key)), f"rq_{key}", f"研究问题缺少 {key}", f"{base}.{key}")
        need(all(x in results for x in rq.get("result_ids", [])), "rq_result_binding", "研究问题绑定了不存在的结果", f"{base}.result_ids")

    contributions = mapping.get("contributions") or []
    need(bool(contributions), "contributions", "至少需要一项可核验贡献", "contributions")
    for i, item in enumerate(contributions):
        base = f"contributions[{i}]"
        for key in ("id", "type", "claim", "result_ids", "evidence_anchors", "chapter_ids", "nearest_work", "novelty_boundary", "not_claimed"):
            need(_present(item.get(key)), f"contribution_{key}", f"贡献缺少 {key}", f"{base}.{key}")
        need(all(x in results for x in item.get("result_ids", [])), "contribution_result_binding", "贡献绑定了不存在的结果", f"{base}.result_ids")

    chapters = mapping.get("chapters") or []
    need(bool(chapters), "chapters", "缺少章节功能映射", "chapters")
    for i, chapter in enumerate(chapters):
        for key in ("id", "function", "rq_ids", "claim_ids", "evidence_anchors", "transition_from", "transition_to"):
            need(_present(chapter.get(key)), f"chapter_{key}", f"章节缺少 {key}", f"chapters[{i}].{key}")

    reproducibility = mapping.get("reproducibility") or {}
    for key in ("research_object", "data_or_materials", "variables_and_parameters", "baselines", "procedure", "analysis_method", "environment"):
        ok = _present(reproducibility.get(key)) or key in set(reproducibility.get("na_reasons") or [])
        need(ok, f"reproducibility_{key}", f"可复现信息缺少 {key}，且无 N/A 理由", f"reproducibility.{key}")

    for key, label in (("cross_chapter_synthesis", "跨章综合命题"), ("limitations_and_transfer_boundaries", "局限与外推边界"), ("authorial_decisions", "作者智识决定")):
        need(_present(mapping.get(key)), key, f"缺少{label}", key)
    unresolved = mapping.get("unresolved_author_inputs") or []
    if require_closed:
        need(not unresolved, "unresolved_author_inputs", "高完成状态仍有待作者确认项", "unresolved_author_inputs")

    if findings:
        status = "blocked" if require_closed else "provisional"
    else:
        status = "doctoral_ready"
    return {"schema_version": "doctoral-thesis-readiness-audit.v1", "status": status, "draft_sha256": actual_hash, "finding_count": len(findings), "findings": findings}


def render_md(payload: dict) -> str:
    lines = ["# Doctoral Thesis Readiness Audit", "", f"- status: `{payload['status']}`", f"- findings: {payload['finding_count']}", ""]
    lines.extend(f"- [{x['code']}] `{x['location']}`: {x['message']}" for x in payload["findings"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft", type=Path)
    parser.add_argument("map", type=Path)
    parser.add_argument("--require-closed", action="store_true")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    payload = audit(args.draft, json.loads(args.map.read_text(encoding="utf-8")), args.require_closed)
    if args.output_json:
        args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
