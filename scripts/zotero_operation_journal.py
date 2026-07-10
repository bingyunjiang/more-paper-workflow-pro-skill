#!/usr/bin/env python3
"""Append idempotent Zotero write-operation events and maintain current state."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def record_operation(root: str | Path, operation: dict[str, Any]) -> dict[str, Any]:
    output = Path(root)
    output.mkdir(parents=True, exist_ok=True)
    operation_type = str(operation.get("operation_type", "")).strip()
    target_id = str(operation.get("target_id", "")).strip()
    if not operation_type or not target_id:
        raise ValueError("operation_type and target_id are required")
    operation_id = str(operation.get("operation_id", "")).strip()
    if not operation_id:
        seed = f"{operation_type}|{target_id}|{operation.get('scope', '')}"
        operation_id = "zop-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]

    state_path = output / "zotero_execution_state.json"
    log_path = output / "zotero_write_operations.jsonl"
    state = _read_json(state_path) or {"schema_version": "zotero-execution.v1", "operations": {}}
    operations = state.setdefault("operations", {})
    previous = operations.get(operation_id)
    requested_status = str(operation.get("status") or "planned")
    if previous and (previous.get("status") == "success" or previous.get("status") == requested_status):
        return {"operation_id": operation_id, "skipped": True, "reason": "idempotent_replay", "current": previous}

    timestamp = _now()
    event = {
        "schema_version": "zotero-operation.v1",
        "event_id": "zev-" + hashlib.sha256(f"{operation_id}|{requested_status}|{timestamp}".encode("utf-8")).hexdigest()[:16],
        "operation_id": operation_id,
        "operation_type": operation_type,
        "target_id": target_id,
        "scope": operation.get("scope", ""),
        "status": requested_status,
        "zotero_key": operation.get("zotero_key", ""),
        "reason": operation.get("reason", ""),
        "checkpoint_confirmed": bool(operation.get("checkpoint_confirmed", False)),
        "timestamp": timestamp,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    operations[operation_id] = event
    state["updated_at"] = timestamp
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"operation_id": operation_id, "skipped": False, "current": event}


def main() -> int:
    parser = argparse.ArgumentParser(description="Record an idempotent Zotero write operation.")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--operation-type", required=True)
    parser.add_argument("--target-id", required=True)
    parser.add_argument("--scope", default="")
    parser.add_argument("--status", choices=("planned", "success", "failed", "manual_required"), default="planned")
    parser.add_argument("--zotero-key", default="")
    parser.add_argument("--reason", default="")
    parser.add_argument("--checkpoint-confirmed", action="store_true")
    args = parser.parse_args()
    result = record_operation(args.output_dir, vars(args))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
