from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any


FORBIDDEN_TERMS = [
    "".join(map(chr, [79, 80, 74, 85])),
    "".join(map(chr, [111, 112, 106, 117])),
    "".join(map(chr, [111, 114, 105, 103, 105, 110, 112, 114, 111])),
    "".join(map(chr, [79, 114, 105, 103, 105, 110, 76, 97, 98])),
    "".join(map(chr, [71, 114, 97, 112, 104, 32, 71, 97, 108, 108, 101, 114, 121])),
    "".join(map(chr, [67, 79, 77, 32, 97, 117, 116, 111, 109, 97, 116, 105, 111, 110])),
]

IGNORED_DIRS = {"__pycache__", ".pytest_cache"}
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".r", ".toml", ".txt"}
PROJECT_NAME = "more-paper-workflow"
LEGACY_NAME = "more-paper-workflow" + "-pro-skill"
PUBLIC_STEP7_MODES = {
    "full-document",
    "chapter-only",
    "continue-existing",
    "abstract-only",
    "review-only",
    "revision-only",
}
STEP7_OPERATIONS = {"write", "citation-audit", "figure", "pre-review"}
LEGACY_NAME_ALLOWLIST = {
    "SKILL.md",
    "README.md",
    "CHANGELOG.md",
    "docs/rename-migration-v1.0.22.md",
    "references/trigger-catalog.md",
    "skills/more-paper-workflow/SKILL.md",
}
REQUIRED_ROOT_PATHS = {
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    "skills/more-paper-workflow/SKILL.md",
    "SKILL.md",
    "manifest.yaml",
    "manifest.step7.yaml",
}


def add_failure(failures: list[dict[str, str]], code: str, path: str, **details: str) -> None:
    failures.append({"code": code, "path": path, **details})


def read_json(path: Path, failures: list[dict[str, str]]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        add_failure(failures, "invalid_json", str(path), message=str(exc))
        return {}
    if not isinstance(payload, dict):
        add_failure(failures, "invalid_json_root", str(path))
        return {}
    return payload


def yaml_axis_allowed(text: str, axis: str) -> list[str]:
    lines = text.splitlines()
    in_axis = False
    in_allowed = False
    values: list[str] = []
    for line in lines:
        if re.fullmatch(rf"  {re.escape(axis)}:\s*", line):
            in_axis = True
            in_allowed = False
            continue
        if in_axis and re.match(r"  \S", line):
            break
        if in_axis and re.fullmatch(r"    allowed:\s*", line):
            in_allowed = True
            continue
        if in_allowed:
            match = re.fullmatch(r"      -\s+(.+?)\s*", line)
            if match:
                values.append(match.group(1).strip("'\""))
                continue
            if line.strip() and len(line) - len(line.lstrip()) <= 4:
                break
    return values


def yaml_mapping(text: str, section: str) -> dict[str, str]:
    lines = text.splitlines()
    in_section = False
    result: dict[str, str] = {}
    for line in lines:
        if re.fullmatch(rf"{re.escape(section)}:\s*", line):
            in_section = True
            continue
        if in_section and line and not line.startswith((" ", "\t")):
            break
        if in_section:
            match = re.fullmatch(r"  ([^:#]+):\s*(\S.*?)\s*", line)
            if match:
                result[match.group(1).strip()] = match.group(2).strip("'\"")
    return result


def validate_route_targets(
    root: Path,
    mapping: dict[str, str],
    failures: list[dict[str, str]],
    manifest_path: Path,
) -> None:
    resolved_root = root.resolve()
    for route, target in mapping.items():
        candidate = (root / target).resolve()
        if not candidate.is_relative_to(resolved_root):
            add_failure(
                failures,
                "route_target_outside_root",
                str(manifest_path),
                route=route,
                target=target,
            )
        elif not candidate.is_file():
            add_failure(
                failures,
                "missing_route_target",
                str(manifest_path),
                route=route,
                target=target,
            )


def validate_repository_structure(root: Path, failures: list[dict[str, str]]) -> None:
    if not (root / "SKILL.md").is_file() or not (root / "manifest.yaml").is_file():
        return

    for relative in sorted(REQUIRED_ROOT_PATHS):
        if not (root / relative).is_file():
            add_failure(failures, "missing_required_path", relative)

    main_manifest_path = root / "manifest.yaml"
    main_text = main_manifest_path.read_text(encoding="utf-8")
    allowed_steps = set(yaml_axis_allowed(main_text, "step"))
    step_routes = yaml_mapping(main_text, "step_routes")
    if allowed_steps != set(step_routes):
        add_failure(
            failures,
            "manifest_route_mismatch",
            "manifest.yaml",
            allowed=",".join(sorted(allowed_steps)),
            routes=",".join(sorted(step_routes)),
        )
    validate_route_targets(root, step_routes, failures, main_manifest_path)

    step7_path = root / "manifest.step7.yaml"
    step7_text = step7_path.read_text(encoding="utf-8")
    modes = set(yaml_axis_allowed(step7_text, "mode"))
    operations = set(yaml_axis_allowed(step7_text, "operation"))
    mode_routes = yaml_mapping(step7_text, "mode_routes")
    operation_routes = yaml_mapping(step7_text, "operation_routes")
    if modes != PUBLIC_STEP7_MODES or modes != set(mode_routes):
        add_failure(
            failures,
            "step7_mode_mismatch",
            "manifest.step7.yaml",
            allowed=",".join(sorted(modes)),
            routes=",".join(sorted(mode_routes)),
        )
    if operations != STEP7_OPERATIONS or operations != set(operation_routes):
        add_failure(
            failures,
            "step7_operation_mismatch",
            "manifest.step7.yaml",
            allowed=",".join(sorted(operations)),
            routes=",".join(sorted(operation_routes)),
        )
    validate_route_targets(root, mode_routes, failures, step7_path)
    validate_route_targets(root, operation_routes, failures, step7_path)

    skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
    skill_name_match = re.search(r"^name:\s*(\S+)", skill_text, re.MULTILINE)
    skill_version_match = re.search(r"^version:\s*v?(\d+\.\d+\.\d+)", skill_text, re.MULTILINE)
    skill_name = skill_name_match.group(1) if skill_name_match else ""
    skill_version = skill_version_match.group(1) if skill_version_match else ""

    plugin_path = root / ".codex-plugin" / "plugin.json"
    plugin = read_json(plugin_path, failures) if plugin_path.is_file() else {}
    if plugin.get("name") != skill_name or skill_name != PROJECT_NAME:
        add_failure(
            failures,
            "metadata_name_mismatch",
            ".codex-plugin/plugin.json",
            skill_name=skill_name,
            plugin_name=str(plugin.get("name", "")),
        )
    if plugin.get("version") != skill_version:
        add_failure(
            failures,
            "metadata_version_mismatch",
            ".codex-plugin/plugin.json",
            skill_version=skill_version,
            plugin_version=str(plugin.get("version", "")),
        )
    if plugin.get("skills") != "./skills/":
        add_failure(failures, "invalid_skills_root", ".codex-plugin/plugin.json")

    claude_plugin_path = root / ".claude-plugin" / "plugin.json"
    claude_plugin = read_json(claude_plugin_path, failures) if claude_plugin_path.is_file() else {}
    if claude_plugin.get("name") != PROJECT_NAME:
        add_failure(
            failures,
            "claude_plugin_name_mismatch",
            ".claude-plugin/plugin.json",
            plugin_name=str(claude_plugin.get("name", "")),
        )
    if claude_plugin.get("version") != skill_version:
        add_failure(
            failures,
            "claude_plugin_version_mismatch",
            ".claude-plugin/plugin.json",
            skill_version=skill_version,
            plugin_version=str(claude_plugin.get("version", "")),
        )

    claude_marketplace_path = root / ".claude-plugin" / "marketplace.json"
    claude_marketplace = (
        read_json(claude_marketplace_path, failures)
        if claude_marketplace_path.is_file()
        else {}
    )
    claude_plugins = (
        claude_marketplace.get("plugins")
        if isinstance(claude_marketplace.get("plugins"), list)
        else []
    )
    claude_entry = claude_plugins[0] if claude_plugins and isinstance(claude_plugins[0], dict) else {}
    if (
        claude_marketplace.get("name") != PROJECT_NAME
        or claude_entry.get("name") != PROJECT_NAME
    ):
        add_failure(
            failures,
            "claude_marketplace_name_mismatch",
            ".claude-plugin/marketplace.json",
        )
    if claude_entry.get("version") != skill_version:
        add_failure(
            failures,
            "claude_marketplace_version_mismatch",
            ".claude-plugin/marketplace.json",
            skill_version=skill_version,
            marketplace_version=str(claude_entry.get("version", "")),
        )

    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    marketplace = read_json(marketplace_path, failures) if marketplace_path.is_file() else {}
    plugins = marketplace.get("plugins") if isinstance(marketplace.get("plugins"), list) else []
    source_path = ""
    if plugins and isinstance(plugins[0], dict):
        if plugins[0].get("name") != PROJECT_NAME:
            add_failure(
                failures,
                "agents_marketplace_name_mismatch",
                ".agents/plugins/marketplace.json",
                plugin_name=str(plugins[0].get("name", "")),
            )
        source = plugins[0].get("source")
        if isinstance(source, dict):
            source_path = str(source.get("path", ""))
    if source_path != "./":
        add_failure(
            failures,
            "plugin_source_not_root",
            ".agents/plugins/marketplace.json",
            source_path=source_path,
        )

    entry_path = root / "skills" / PROJECT_NAME / "SKILL.md"
    if entry_path.is_file():
        entry_text = entry_path.read_text(encoding="utf-8")
        entry_name_match = re.search(r"^name:\s*(\S+)", entry_text, re.MULTILINE)
        entry_name = entry_name_match.group(1) if entry_name_match else ""
        if entry_name != PROJECT_NAME:
            add_failure(
                failures,
                "codex_skill_name_mismatch",
                str(entry_path.relative_to(root)),
                skill_name=entry_name,
            )
        targets = re.findall(r"\]\(([^)]+SKILL\.md)\)", entry_text)
        if not targets:
            add_failure(failures, "missing_canonical_skill_reference", str(entry_path.relative_to(root)))
        for target in targets:
            resolved = (entry_path.parent / target).resolve()
            if not resolved.is_relative_to(root.resolve()):
                add_failure(
                    failures,
                    "reference_outside_plugin",
                    str(entry_path.relative_to(root)),
                    target=target,
                )
            elif resolved != (root / "SKILL.md").resolve():
                add_failure(
                    failures,
                    "invalid_canonical_skill_reference",
                    str(entry_path.relative_to(root)),
                    target=target,
                )

    nested_plugin = root / "plugins" / PROJECT_NAME / ".codex-plugin" / "plugin.json"
    if nested_plugin.exists():
        add_failure(
            failures,
            "legacy_plugin_layout_present",
            str(nested_plugin.relative_to(root)),
        )

    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_DIRS | {".git", ".codegraph"} for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES | {".html", ".svg"}:
            continue
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if LEGACY_NAME in text and relative not in LEGACY_NAME_ALLOWLIST:
            add_failure(failures, "legacy_name_outside_allowlist", relative)
        if f"github.com/bingyunjiang/{LEGACY_NAME}" in text:
            add_failure(failures, "legacy_repository_url", relative)


def scan_skill(root: Path) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in {".pyc", ".pyo"}:
            failures.append({"code": "bytecode_present", "path": str(path)})
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for term in FORBIDDEN_TERMS:
                if term in text:
                    failures.append({"code": "forbidden_term", "term": term, "path": str(path)})
    validate_repository_structure(root, failures)
    return {
        "schema": "morepaper.package_validation.v1",
        "root": str(root),
        "status": "ok" if not failures else "failed",
        "failures": failures,
    }


def scan_zip(path: Path) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        required_suffixes = {
            "/.codex-plugin/plugin.json",
            "/.claude-plugin/plugin.json",
            "/.claude-plugin/marketplace.json",
            "/skills/more-paper-workflow/SKILL.md",
            "/SKILL.md",
            "/manifest.yaml",
        }
        for suffix in sorted(required_suffixes):
            if not any(name.endswith(suffix) for name in names):
                add_failure(failures, "missing_required_zip_entry", str(path), target=suffix)
        if any(
            name.endswith("/plugins/more-paper-workflow/.codex-plugin/plugin.json")
            for name in names
        ):
            add_failure(failures, "legacy_plugin_layout_in_zip", str(path))
        for name in names:
            if "\\" in name:
                failures.append({"code": "windows_separator_in_zip", "path": name})
            if "__pycache__" in name or name.endswith((".pyc", ".pyo")):
                failures.append({"code": "cache_in_zip", "path": name})
            try:
                with archive.open(name) as handle:
                    while handle.read(1024 * 64):
                        pass
            except Exception as exc:
                failures.append({"code": "zip_entry_unreadable", "path": name, "message": str(exc)})
    return {
        "schema": "morepaper.zip_package_validation.v1",
        "zip": str(path),
        "status": "ok" if not failures else "failed",
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a more-paper-workflow package.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--zip", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = scan_skill(args.root)
    if args.zip:
        result["zip_validation"] = scan_zip(args.zip)
        if result["zip_validation"]["status"] != "ok":
            result["status"] = "failed"
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
