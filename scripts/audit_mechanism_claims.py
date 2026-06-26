#!/usr/bin/env python3
"""Audit Step 7 mechanism claims before drafting."""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_mechanism_argument_plan import audit_plan_items  # noqa: E402


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))


def _load_claims(path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = _load_json(path)
    if isinstance(payload, dict):
        claims = payload.get("claims")
        if isinstance(claims, list):
            return [item for item in claims if isinstance(item, dict)], payload.get("metadata") or {}
        records = payload.get("records")
        if isinstance(records, list):
            return [item for item in records if isinstance(item, dict)], payload.get("metadata") or {}
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)], {}
    raise SystemExit(f"Unsupported mechanism plan JSON shape: {path}")


def _render_markdown(findings: list[dict[str, Any]]) -> str:
    lines = ["# Mechanism Claim Audit", ""]
    for item in findings:
        lines.extend([
            f"## {item.get('claim_id', '')}",
            "",
            f"- source_citekey: {item.get('source_citekey', '')}",
            f"- severity: {item.get('severity', '')}",
            f"- missing: {'; '.join(item.get('missing', []))}",
            f"- recommended_action: {item.get('recommended_action', '')}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def audit_claims(plan_json: Path, output_json: Path, output_md: Path) -> int:
    claims, metadata = _load_claims(plan_json)
    findings = audit_plan_items(claims)
    payload = {
        "schema_version": "mechanism-claim-audit.v1",
        "metadata": {
            **metadata,
            "source_plan": str(plan_json),
        },
        "findings": findings,
    }
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(findings), encoding="utf-8")
    print(f"MECHANISM_CLAIM_AUDIT: {output_json}")
    print(f"MECHANISM_CLAIM_AUDIT_MD: {output_md}")
    print(f"CLAIMS: {len(findings)}")
    print(f"DOWNGRADED: {sum(1 for item in findings if item['severity'] != 'pass')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Step 7 mechanism_argument_plan.json.")
    parser.add_argument("--plan-json", required=True, help="Path to mechanism_argument_plan.json")
    parser.add_argument("--output-json", default="mechanism_claim_audit.json", help="Output audit JSON path")
    parser.add_argument("--output-md", default="mechanism_claim_audit.md", help="Output audit Markdown path")
    args = parser.parse_args()
    return audit_claims(
        plan_json=Path(args.plan_json).expanduser().resolve(),
        output_json=Path(args.output_json).expanduser(),
        output_md=Path(args.output_md).expanduser(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
