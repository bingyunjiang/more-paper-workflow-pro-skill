#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
"""
Best-effort update reminder for More Paper Workflow Pro Skill.

The script never mutates the skill repository. It only compares local metadata
and, when available, the git remote HEAD, then prints a short reminder.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path


DEFAULT_INTERVAL_HOURS = 24
REMOTE_TIMEOUT_SECONDS = 5


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def parse_skill_version(root: Path) -> str | None:
    match = re.search(r"^version:\s*(\S+)\s*$", read_text(root / "SKILL.md"), re.M)
    return match.group(1) if match else None


def parse_readme_version(root: Path) -> str | None:
    match = re.search(r"more paper workflow pro skill\s+`([^`]+)`", read_text(root / "README.md"), re.I)
    return match.group(1) if match else None


def parse_changelog_version(root: Path) -> str | None:
    match = re.search(r"^##\s+(v[0-9][^\s]+)", read_text(root / "CHANGELOG.md"), re.M)
    return match.group(1) if match else None


def run_git(root: Path, args: list[str], timeout: int = REMOTE_TIMEOUT_SECONDS) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def state_path() -> Path:
    cache_root = os.environ.get("XDG_CACHE_HOME")
    if cache_root:
        base = Path(cache_root)
    else:
        base = Path.home() / ".cache"
    return base / "more-paper-workflow-pro-skill" / "update-check.json"


def load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(path: Path, state: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def should_check(path: Path, interval_hours: float, force: bool) -> bool:
    if force:
        return True
    state = load_state(path)
    last_checked = float(state.get("last_checked", 0) or 0)
    return (time.time() - last_checked) >= interval_hours * 3600


def print_reminder(lines: list[str]) -> None:
    print("🔔 More Paper Workflow Pro Skill 更新提醒")
    for line in lines:
        print(line)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check whether this skill may need an update.")
    parser.add_argument("--force", action="store_true", help="Ignore daily throttling and check now.")
    parser.add_argument("--no-network", action="store_true", help="Only compare local metadata; skip git remote check.")
    parser.add_argument("--quiet", action="store_true", help="Only print when an update or metadata mismatch is found.")
    parser.add_argument(
        "--interval-hours",
        type=float,
        default=float(os.environ.get("MORE_PAPER_SKILL_UPDATE_INTERVAL_HOURS", DEFAULT_INTERVAL_HOURS)),
        help="Minimum hours between automatic checks. Default: 24.",
    )
    args = parser.parse_args(argv)

    if os.environ.get("MORE_PAPER_SKILL_UPDATE_CHECK", "").lower() in {"0", "false", "no", "off"}:
        return 0

    root = skill_dir()
    state_file = state_path()
    if not should_check(state_file, args.interval_hours, args.force):
        return 0

    skill_version = parse_skill_version(root)
    readme_version = parse_readme_version(root)
    changelog_version = parse_changelog_version(root)

    lines: list[str] = []
    expected_version = changelog_version or readme_version
    if expected_version and skill_version and skill_version != expected_version:
        lines.append(f"- 本地 SKILL.md 版本为 {skill_version}，但 README/CHANGELOG 最新为 {expected_version}。")
        lines.append("- 建议先同步 skill 元数据，避免 Agent 读取到旧版本号。")

    local_head = run_git(root, ["rev-parse", "HEAD"], timeout=2)
    remote_head = None
    remote_url = run_git(root, ["config", "--get", "remote.origin.url"], timeout=2)
    if not args.no_network and remote_url and local_head:
        remote_raw = run_git(root, ["ls-remote", "origin", "HEAD"], timeout=REMOTE_TIMEOUT_SECONDS)
        if remote_raw:
            remote_head = remote_raw.split()[0]
            if remote_head and remote_head != local_head:
                lines.append(f"- 远程仓库已有新提交：本地 {local_head[:7]}，远程 {remote_head[:7]}。")
                lines.append(f"- 更新命令：cd {root} && git pull --ff-only")

    save_state(
        state_file,
        {
            "last_checked": time.time(),
            "skill_version": skill_version,
            "readme_version": readme_version,
            "changelog_version": changelog_version,
            "local_head": local_head,
            "remote_head": remote_head,
        },
    )

    if lines:
        print_reminder(lines)
    elif not args.quiet:
        print(f"✅ More Paper Workflow Pro Skill 已是当前可见版本：{skill_version or 'unknown'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
