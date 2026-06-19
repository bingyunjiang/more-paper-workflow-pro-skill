#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
"""
Attempt a non-destructive git-based skill upgrade and report whether the host
can continue with the current local version.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def run_git(root: Path, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def trim(text: str, limit: int = 600) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def build_result(root: Path) -> dict:
    local_before = run_git(root, ["rev-parse", "HEAD"], timeout=5)
    before_head = local_before.stdout.strip() if local_before.returncode == 0 else None

    try:
        pull = run_git(root, ["pull", "--ff-only"], timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "upgraded": False,
            "continue_with_current_version": True,
            "reason": "upgrade_command_failed",
            "message": "升级失败：当前网络或 git 环境不可用。将继续使用当前本地版本。",
            "details": str(exc),
            "command": f"cd {root} && git pull --ff-only",
            "local_head_before": before_head,
            "local_head_after": before_head,
        }

    local_after = run_git(root, ["rev-parse", "HEAD"], timeout=5)
    after_head = local_after.stdout.strip() if local_after.returncode == 0 else before_head
    upgraded = bool(before_head and after_head and before_head != after_head)

    if pull.returncode == 0:
        message = "升级成功：已更新到最新可见版本。" if upgraded else "已是最新版本，无需升级。"
        return {
            "ok": True,
            "upgraded": upgraded,
            "continue_with_current_version": True,
            "reason": "success",
            "message": message,
            "details": trim((pull.stdout or "") + ("\n" + pull.stderr if pull.stderr else "")),
            "command": f"cd {root} && git pull --ff-only",
            "local_head_before": before_head,
            "local_head_after": after_head,
        }

    stderr = trim(pull.stderr or pull.stdout or "")
    return {
        "ok": False,
        "upgraded": False,
        "continue_with_current_version": True,
        "reason": "git_pull_failed",
        "message": "升级失败：无法从远程拉取更新。将继续使用当前本地版本。",
        "details": stderr,
        "command": f"cd {root} && git pull --ff-only",
        "local_head_before": before_head,
        "local_head_after": after_head,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Perform a non-destructive skill upgrade attempt.")
    parser.add_argument("--json", action="store_true", help="Print JSON payload instead of plain text.")
    args = parser.parse_args(argv)

    payload = build_result(skill_dir())

    if args.json:
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(payload["message"] + "\n")
        if payload.get("details"):
            sys.stdout.write(payload["details"] + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
