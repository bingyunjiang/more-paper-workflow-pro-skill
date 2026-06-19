#!/usr/bin/env python3
"""Lightweight config registry for source/provider/template metadata.

This module intentionally keeps config optional. Missing files, malformed
fields, or unknown keys must fall back to hard-coded defaults in callers.
"""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore


SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = SKILL_DIR / "config"


SOURCE_DEFAULTS: dict[str, dict[str, Any]] = {
    "openalex": {
        "key": "openalex",
        "display_name": "OpenAlex",
        "report_label": "OpenAlex",
        "default_language": "en",
        "is_chinese": False,
        "requires_cdp": False,
        "status_notes": {"ok": "已执行", "fail": "不可达"},
    },
    "crossref": {
        "key": "crossref",
        "display_name": "Crossref",
        "report_label": "Crossref",
        "default_language": "en",
        "is_chinese": False,
        "requires_cdp": False,
        "status_notes": {"ok": "已执行", "fail": "不可达"},
    },
    "semantic_scholar": {
        "key": "semantic_scholar",
        "display_name": "Semantic Scholar",
        "report_label": "Semantic Scholar",
        "default_language": "en",
        "is_chinese": False,
        "requires_cdp": False,
        "status_notes": {"ok": "已执行", "429": "HTTP 429 已跳过"},
    },
    "cnki": {
        "key": "cnki",
        "display_name": "CNKI",
        "report_label": "CNKI",
        "default_language": "zh",
        "is_chinese": True,
        "requires_cdp": True,
        "status_notes": {
            "ok": "IP 直连",
            "carsi_logged_in": "CARSI 登录",
            "skipped_no_account": "无机构账号已跳过",
            "skipped": "用户选择跳过",
        },
    },
    "wanfang": {
        "key": "wanfang",
        "display_name": "Wanfang Data",
        "report_label": "万方",
        "default_language": "zh",
        "is_chinese": True,
        "requires_cdp": True,
        "status_notes": {
            "ok": "IP 直连",
            "carsi_logged_in": "CARSI 登录",
            "attempted_failed": "已尝试但失败",
            "skipped_no_account": "无机构账号已跳过",
            "skipped": "用户选择跳过",
        },
    },
    "arxiv": {
        "key": "arxiv",
        "display_name": "arXiv",
        "report_label": "arXiv",
        "default_language": "en",
        "is_chinese": False,
        "requires_cdp": False,
        "status_notes": {"ok": "已执行"},
    },
}


OUTPUT_TEMPLATE_DEFAULTS: dict[str, Any] = {
    "search_report": {
        "default_filename": "检索报告.md",
        "title": "文献检索报告",
        "sections": [
            "检索概览",
            "检索范围与方法",
            "检索结果流水线",
            "评分维度与方法",
            "最终文献库分析",
            "引文扩展",
            "饱和度分析",
            "下一步行动",
        ],
    }
}


def _read_toml(path: str | Path) -> dict[str, Any]:
    if tomllib is None:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("rb") as f:
            data = tomllib.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _merge_dicts(default: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(default)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_source_registry(config_dir: str | Path | None = None) -> dict[str, dict[str, Any]]:
    cfg_dir = Path(config_dir) if config_dir else CONFIG_DIR
    data = _read_toml(cfg_dir / "sources.toml")
    sources = {key: dict(value) for key, value in SOURCE_DEFAULTS.items()}
    for key, value in data.get("sources", {}).items():
        if isinstance(value, dict):
            base = sources.get(key, {"key": key})
            sources[key] = _merge_dicts(base, value)
            sources[key].setdefault("key", key)
    return sources


def get_source_config(source_key: str, config_dir: str | Path | None = None) -> dict[str, Any]:
    key = (source_key or "").strip().lower().replace(" ", "_")
    registry = load_source_registry(config_dir)
    return registry.get(key, {
        "key": key,
        "display_name": source_key,
        "report_label": source_key,
        "default_language": "any",
        "is_chinese": False,
        "requires_cdp": False,
        "status_notes": {},
    })


def source_label(source_key: str, config_dir: str | Path | None = None) -> str:
    cfg = get_source_config(source_key, config_dir)
    return str(cfg.get("report_label") or cfg.get("display_name") or source_key)


def source_status_note(source_key: str, status: str, config_dir: str | Path | None = None) -> str:
    cfg = get_source_config(source_key, config_dir)
    notes = cfg.get("status_notes", {})
    if isinstance(notes, dict):
        return str(notes.get(status, status))
    return status


def is_chinese_source(source_key: str, config_dir: str | Path | None = None) -> bool:
    return bool(get_source_config(source_key, config_dir).get("is_chinese", False))


def source_requires_cdp(source_key: str, config_dir: str | Path | None = None) -> bool:
    return bool(get_source_config(source_key, config_dir).get("requires_cdp", False))


def load_output_templates(config_dir: str | Path | None = None) -> dict[str, Any]:
    cfg_dir = Path(config_dir) if config_dir else CONFIG_DIR
    data = _read_toml(cfg_dir / "output_templates.toml")
    templates = dict(OUTPUT_TEMPLATE_DEFAULTS)
    for key, value in data.get("templates", {}).items():
        if isinstance(value, dict):
            templates[key] = _merge_dicts(templates.get(key, {}), value)
    return templates


def get_output_template(template_key: str, config_dir: str | Path | None = None) -> dict[str, Any]:
    templates = load_output_templates(config_dir)
    return templates.get(template_key, OUTPUT_TEMPLATE_DEFAULTS.get(template_key, {}))
