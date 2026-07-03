#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 - Attribution-NonCommercial-ShareAlike 4.0 International
"""Diagnostic-only Step 5 download readiness checker."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from cdp_utils import cdp_browser_matches, check_cdp, check_required_deps, get_cdp_browser_product
from console_compat import FAIL, OK, WARN, configure_console_output
from generic_publisher_downloader import _PUBLISHER_CONFIGS, describe_publisher_session
from unified_download_router import step5_download_lock_path, _pid_is_running


def _output_writable(path: str | Path) -> tuple[bool, str]:
    output = Path(path)
    try:
        output.mkdir(parents=True, exist_ok=True)
        probe = output / ".step5_doctor_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True, "writable"
    except Exception as exc:
        return False, f"not_writable:{type(exc).__name__}"


def _lock_status() -> dict[str, Any]:
    path = step5_download_lock_path()
    if not path.exists():
        return {"path": str(path), "status": "absent", "running": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    pid = int(payload.get("pid") or 0)
    running = _pid_is_running(pid)
    return {"path": str(path), "status": "active" if running else "stale", "running": running, "payload": payload}


def build_doctor_report(port: int = 9223, browser: str = "chrome", output_dir: str = "paper-temp") -> dict[str, Any]:
    cdp_ok = check_cdp(port)
    browser_match = False
    browser_product = ""
    if cdp_ok:
        try:
            browser_product = get_cdp_browser_product(port)
            browser_match = cdp_browser_matches(port, browser)
        except Exception:
            browser_match = False

    deps_ok = check_required_deps()
    writable, writable_reason = _output_writable(output_dir)
    lock = _lock_status()
    sessions: dict[str, dict[str, Any]] = {}
    if cdp_ok:
        for key, cfg in _PUBLISHER_CONFIGS.items():
            if key not in {"sd_elsevier", "wiley", "springer", "acs", "rsc", "nature", "cnki", "wanfang"}:
                continue
            try:
                sessions[key] = describe_publisher_session(port, cfg)
            except Exception as exc:
                sessions[key] = {"probe_status": "error", "probe_reason": type(exc).__name__, "has_session": False}

    blocking = []
    warnings = []
    if not cdp_ok:
        blocking.append("cdp_not_running")
    elif not browser_match:
        warnings.append("cdp_browser_mismatch")
    if not deps_ok:
        blocking.append("missing_required_deps")
    if not writable:
        blocking.append("output_not_writable")
    if lock.get("running"):
        blocking.append("step5_download_lock_active")
    if cdp_ok and not any(s.get("probe_status") == "ok" for s in sessions.values()):
        warnings.append("no_trusted_publisher_session")

    status = "blocked" if blocking else "partial" if warnings else "ready"
    if "cdp_not_running" in blocking:
        next_action = f"start_cdp_browser --browser {browser} --port {port}"
    elif "step5_download_lock_active" in blocking:
        next_action = "wait_for_current_step5_download_or_clear_stale_lock"
    elif warnings:
        next_action = "login_or_verify_publisher_sessions_before_cdp_rounds"
    else:
        next_action = "run_step5_download"

    return {
        "schema_version": "step5-doctor.v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "next_action": next_action,
        "checks": {
            "cdp": {"ok": cdp_ok, "port": port, "browser": browser, "matches_requested_browser": browser_match, "product": browser_product},
            "dependencies": {"ok": deps_ok},
            "output_dir": {"path": str(output_dir), "ok": writable, "reason": writable_reason},
            "lock": lock,
            "sessions": sessions,
        },
        "blocking": blocking,
        "warnings": warnings,
    }


def main() -> int:
    configure_console_output()
    parser = argparse.ArgumentParser(description="Step 5 download readiness doctor; diagnostics only.")
    parser.add_argument("--port", type=int, default=9223)
    parser.add_argument("--browser", choices=("chrome", "edge"), default=os.environ.get("CDP_BROWSER", "chrome"))
    parser.add_argument("--output", default="paper-temp")
    parser.add_argument("--json", dest="json_path", nargs="?", const="AUTO", help="Write JSON report; default path is <output>/step5_doctor_report.json")
    args = parser.parse_args()

    report = build_doctor_report(args.port, args.browser, args.output)
    icon = OK if report["status"] == "ready" else WARN if report["status"] == "partial" else FAIL
    print("=== Step 5 Download Doctor ===")
    print(f"  {icon} status: {report['status']}")
    print(f"  next_action: {report['next_action']}")
    print(f"  cdp: {report['checks']['cdp']['ok']} ({report['checks']['cdp']['product'] or 'not running'})")
    print(f"  output_dir: {report['checks']['output_dir']['reason']}")
    print(f"  lock: {report['checks']['lock']['status']}")
    if report["blocking"]:
        print("  blocking: " + ", ".join(report["blocking"]))
    if report["warnings"]:
        print("  warnings: " + ", ".join(report["warnings"]))

    if args.json_path:
        path = Path(args.output) / "step5_doctor_report.json" if args.json_path == "AUTO" else Path(args.json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  report: {path}")
    return 2 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
