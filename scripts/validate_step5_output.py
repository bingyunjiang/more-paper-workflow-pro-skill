#!/usr/bin/env python3
"""Validate Step 5 artifacts before download completion is claimed."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from unified_download_router import diagnose_pdf_file  # noqa: E402


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def _read_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def validate(root: Path) -> tuple[list[Finding], dict[str, object]]:
    findings: list[Finding] = []
    manifest_path = root / "download_manifest.json"
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "step5-download.v1":
        findings.append(Finding("fail", "invalid_manifest", "download_manifest.json is missing or invalid"))
        return findings, {"root": str(root), "status": "fail", "total": 0}

    items = manifest.get("items")
    if not isinstance(items, list):
        findings.append(Finding("fail", "invalid_items", "manifest items must be a list"))
        items = []

    downloaded = 0
    identifiers: set[str] = set()
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            findings.append(Finding("fail", "invalid_item", f"item {index} is not an object"))
            continue
        identifier = item.get("doi") or item.get("source_id") or item.get("id") or item.get("title") or f"item-{index}"
        identifiers.add(str(identifier))
        if item.get("status") != "downloaded":
            continue
        downloaded += 1
        pdf_path = Path(str(item.get("pdf_path", "")))
        diagnostics = diagnose_pdf_file(pdf_path)
        if item.get("verification_status") != "verified" or item.get("quality") != "pdf_verified":
            findings.append(Finding("fail", "downloaded_not_verified", f"{identifier} is downloaded without verified status"))
        if diagnostics.get("verification_status") != "verified":
            findings.append(Finding("fail", "downloaded_pdf_invalid", f"{identifier} points to an invalid PDF: {diagnostics.get('issue')}"))
        if item.get("sha256") and item.get("sha256") != diagnostics.get("sha256"):
            findings.append(Finding("fail", "pdf_hash_mismatch", f"{identifier} PDF hash does not match manifest"))

    summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}
    unresolved = len(items) - downloaded
    expected_readiness = "complete" if items and unresolved == 0 else "partial" if downloaded else "blocked"
    if summary.get("total") != len(items) or summary.get("downloaded") != downloaded or summary.get("failed_or_pending") != unresolved:
        findings.append(Finding("fail", "summary_mismatch", "manifest summary counts do not match item states"))
    if manifest.get("readiness") != expected_readiness:
        findings.append(Finding("fail", "readiness_mismatch", f"expected readiness={expected_readiness}"))

    for checkpoint_name in ("login_checkpoint.json", "chinese_login_checkpoint.json"):
        checkpoint = _read_json(root / checkpoint_name)
        if not isinstance(checkpoint, dict) or checkpoint.get("status") not in {"pending_user_login", "pending_captcha_verification"}:
            continue
        checkpoint_items = checkpoint.get("items")
        if not isinstance(checkpoint_items, list):
            findings.append(Finding("fail", "invalid_checkpoint_items", f"{checkpoint_name} items must be a list"))
            continue
        seen_checkpoint_ids: set[str] = set()
        for pending in checkpoint_items:
            if not isinstance(pending, dict):
                findings.append(Finding("fail", "invalid_checkpoint_item", f"{checkpoint_name} contains a non-object item"))
                continue
            identifier = pending.get("doi") or pending.get("source_id") or pending.get("id") or pending.get("title")
            if not identifier:
                findings.append(Finding("fail", "checkpoint_item_missing_identifier", f"{checkpoint_name} contains an item without identifier"))
                continue
            if str(identifier) in seen_checkpoint_ids:
                findings.append(Finding("fail", "duplicate_checkpoint_item", f"{checkpoint_name} repeats {identifier}"))
                continue
            seen_checkpoint_ids.add(str(identifier))
            matching = next((item for item in items if identifier in {item.get("doi"), item.get("source_id"), item.get("id"), item.get("title")}), None)
            if identifier in identifiers and matching and matching.get("status") == "downloaded":
                continue
            if identifier in identifiers and matching and matching.get("status") != "pending_user_login":
                findings.append(Finding("fail", "checkpoint_state_mismatch", f"{identifier} is pending in checkpoint but not in manifest"))

    attempts_path = root / "download_attempts.jsonl"
    if not attempts_path.exists():
        findings.append(Finding("fail", "missing_attempt_log", "download_attempts.jsonl is missing"))
    else:
        complete_run_ids: set[str] = set()
        for line_number, line in enumerate(attempts_path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                findings.append(Finding("fail", "invalid_attempt_row", f"attempt log line {line_number} is invalid JSON"))
                continue
            missing = [field for field in ("attempt_id", "run_id", "item_id", "stage", "status", "timestamp") if not row.get(field)]
            if missing:
                findings.append(Finding("warn", "legacy_attempt_row", f"attempt log line {line_number} lacks {', '.join(missing)}"))
            else:
                complete_run_ids.add(str(row["run_id"]))
        if items and str(manifest.get("run_id", "")) not in complete_run_ids:
            findings.append(Finding("fail", "missing_current_run_attempts", "attempt log has no complete event for the current manifest run"))

    status = "pass" if not any(item.severity == "fail" for item in findings) else "fail"
    return findings, {"root": str(root), "status": status, "total": len(items), "downloaded": downloaded, "failed_or_pending": unresolved}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Step 5 download artifacts.")
    parser.add_argument("output_dir")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    findings, summary = validate(Path(args.output_dir).expanduser().resolve())
    if args.json:
        print(json.dumps({"summary": summary, "findings": [asdict(item) for item in findings]}, ensure_ascii=False, indent=2))
    else:
        print(f"STEP5_VALIDATION: {summary['status']}")
        for item in findings:
            print(f"{item.severity.upper()}: {item.code}: {item.message}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
