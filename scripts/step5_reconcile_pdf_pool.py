#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 - Attribution-NonCommercial-ShareAlike 4.0 International
"""Reconcile manually downloaded PDFs back into Step 5 artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from console_compat import OK, WARN, configure_console_output
from unified_download_router import (
    _doi_pdf_basename,
    _recovery_buckets,
    _recommended_next_step,
    _safe_pdf_quality,
    build_pdf_pool_index,
    diagnose_pdf_file,
)
from workflow_contracts import step5_attempt, write_pdf_pool_index


def _norm(value: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", value.lower())


def _candidate_pdf_for_item(output_dir: Path, item: dict[str, Any]) -> Path | None:
    path, _, _ = _candidate_pdf_match(output_dir, item)
    return path


def _candidate_pdf_match(output_dir: Path, item: dict[str, Any]) -> tuple[Path | None, str, str]:
    candidates = sorted(output_dir.glob("*.pdf"))
    keys = [item.get("doi", ""), item.get("source_id", ""), item.get("id", "")]
    title_key = _norm(item.get("title", ""))[:48]
    for key in keys:
        if not key:
            continue
        fragment = _doi_pdf_basename(str(key)).lower()
        for path in candidates:
            if fragment and fragment in path.name.lower():
                return path, "confirmed", "stable_identifier_in_filename"
    if title_key and len(title_key) >= 12:
        for path in candidates:
            if title_key in _norm(path.stem):
                return path, "probable", "title_filename_match"
    return None, "none", "no_match"


def _append_attempt_once(item: dict[str, Any], attempt: dict[str, Any]) -> bool:
    attempts = item.setdefault("attempts", [])
    signature = (attempt.get("stage"), attempt.get("status"), attempt.get("reason"), attempt.get("pdf_path"))
    if any(
        (old.get("stage"), old.get("status"), old.get("reason"), old.get("pdf_path")) == signature
        for old in attempts
    ):
        return False
    attempts.append(attempt)
    return True


def _manifest_status(items: list[dict[str, Any]]) -> tuple[str, dict[str, list[str]], str]:
    total = len(items)
    downloaded = sum(1 for item in items if item.get("status") == "downloaded")
    failure_reasons = {
        item.get("doi") or item.get("source_id") or item.get("id") or item.get("title") or f"item-{idx}": item.get("failure_reason", "")
        for idx, item in enumerate(items, 1)
        if item.get("status") != "downloaded" and item.get("failure_reason")
    }
    readiness = "complete" if total and downloaded == total else "partial" if downloaded else "blocked"
    buckets = _recovery_buckets(failure_reasons)
    return readiness, buckets, _recommended_next_step(readiness, buckets)


def reconcile_pdf_pool(output_dir: str | Path, manifest_name: str = "download_manifest.json") -> dict[str, Any]:
    output = Path(output_dir)
    manifest_path = output / manifest_name
    if not manifest_path.exists():
        raise FileNotFoundError(f"download manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = manifest.get("items", [])
    changed: list[dict[str, Any]] = []
    pending_matches: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    attempt_rows: list[dict[str, Any]] = []
    run_id = str(manifest.get("run_id") or "step5-reconcile")
    manifest["run_id"] = run_id
    for item in items:
        existing_path = Path(item.get("pdf_path", "")) if item.get("pdf_path") else None
        existing_diagnostics = diagnose_pdf_file(existing_path) if existing_path else {}
        if item.get("status") == "downloaded" and existing_path and existing_diagnostics.get("verification_status") == "verified":
            item["quality"] = "pdf_verified"
            item["verification_status"] = "verified"
            item["verification_reason"] = "ok"
            item["verified_at"] = item.get("verified_at") or datetime.now().isoformat(timespec="seconds")
            item["sha256"] = existing_diagnostics.get("sha256", "")
            identifier = item.get("doi") or item.get("source_id") or item.get("id") or item.get("title", "")
            attempt = step5_attempt(
                "manual_reconcile", "verified", reason="legacy_manifest_backfill", pdf_path=str(existing_path),
                run_id=run_id, item_id=identifier, route="manual_reconcile", verification_status="verified",
            )
            if _append_attempt_once(item, attempt):
                attempt_rows.append({"id": identifier, **attempt})
            continue
        pdf_path, match_confidence, match_reason = _candidate_pdf_match(output, item)
        if not pdf_path:
            continue
        diagnostics = diagnose_pdf_file(pdf_path)
        identifier = item.get("doi") or item.get("source_id") or item.get("id") or item.get("title", "")
        if match_confidence != "confirmed":
            item["status"] = "manual_required"
            item["failure_reason"] = "probable_pdf_match_requires_confirmation"
            item["next_action"] = "confirm_pdf_match"
            pending_matches.append({"id": item.get("id", ""), "pdf_path": str(pdf_path), "match_reason": match_reason})
            continue
        if diagnostics.get("verification_status") != "verified":
            item["status"] = "invalid_pdf"
            item["quality"] = "pdf_unverified"
            item["pdf_path"] = str(pdf_path)
            item["failure_reason"] = diagnostics.get("issue") or "invalid_pdf"
            item["next_action"] = "replace_invalid_pdf"
            item["verification_status"] = "invalid"
            item["verification_reason"] = item["failure_reason"]
            item["sha256"] = diagnostics.get("sha256", "")
            attempt = step5_attempt(
                "manual_reconcile", "invalid", reason=item["failure_reason"], pdf_path=str(pdf_path),
                run_id=run_id, item_id=identifier, route="manual_reconcile", verification_status="invalid",
            )
            if _append_attempt_once(item, attempt):
                attempt_rows.append({"id": identifier, **attempt})
            invalid.append({"id": item.get("id", ""), "pdf_path": str(pdf_path), "reason": item["failure_reason"]})
            continue
        item["status"] = "downloaded"
        item["quality"] = _safe_pdf_quality(pdf_path)
        item["pdf_path"] = str(pdf_path)
        item["failure_reason"] = ""
        item["next_action"] = ""
        item["verification_status"] = "verified"
        item["verification_reason"] = "ok"
        item["verified_at"] = datetime.now().isoformat(timespec="seconds")
        item["sha256"] = diagnostics.get("sha256", "")
        attempt = step5_attempt(
            "manual_reconcile",
            "verified",
            reason=diagnostics.get("issue", ""),
            pdf_path=str(pdf_path),
            run_id=run_id,
            item_id=identifier,
            route="manual_reconcile",
            verification_status="verified",
        )
        if _append_attempt_once(item, attempt):
            attempt_rows.append({"id": identifier, **attempt})
        changed.append({"id": item.get("id", ""), "pdf_path": str(pdf_path), "quality": item["quality"]})

    readiness, buckets, next_step = _manifest_status(items)
    manifest["readiness"] = readiness
    manifest["recovery_buckets"] = buckets
    manifest["recommended_next_step"] = next_step
    summary = manifest.setdefault("summary", {})
    summary["total"] = len(items)
    summary["downloaded"] = sum(1 for item in items if item.get("status") == "downloaded")
    summary["remaining"] = len(items) - summary["downloaded"]
    summary["failed_or_pending"] = summary["remaining"]
    summary["manual_reconciled"] = len(changed)

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    pool_path = output / "pdf-附件池索引.json"
    write_pdf_pool_index(pool_path, build_pdf_pool_index(str(output), items))

    attempts_path = output / "download_attempts.jsonl"
    with attempts_path.open("a", encoding="utf-8") as f:
        for row in attempt_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {
        "schema_version": "step5-reconcile.v1",
        "output_dir": str(output),
        "manifest": str(manifest_path),
        "pdf_pool": str(pool_path),
        "reconciled": changed,
        "pending_matches": pending_matches,
        "invalid": invalid,
        "readiness": readiness,
        "recommended_next_step": next_step,
    }


def main() -> int:
    configure_console_output()
    parser = argparse.ArgumentParser(description="Reconcile manually downloaded PDFs into Step 5 manifest and PDF pool.")
    parser.add_argument("--output", "-o", default="paper-temp")
    parser.add_argument("--manifest", default="download_manifest.json")
    parser.add_argument("--json", dest="json_path", nargs="?", const="AUTO", help="Write reconcile report JSON")
    args = parser.parse_args()

    try:
        report = reconcile_pdf_pool(args.output, args.manifest)
    except FileNotFoundError as exc:
        print(f"{WARN} {exc}")
        return 2

    print("=== Step 5 PDF Pool Reconcile ===")
    print(f"  {OK} reconciled: {len(report['reconciled'])}")
    print(f"  readiness: {report['readiness']}")
    print(f"  next_action: {report['recommended_next_step']}")
    print(f"  manifest: {report['manifest']}")
    print(f"  pdf_pool: {report['pdf_pool']}")
    if args.json_path:
        path = Path(args.output) / "step5_reconcile_report.json" if args.json_path == "AUTO" else Path(args.json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  report: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
