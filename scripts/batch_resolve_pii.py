#!/usr/bin/env python3
"""
Batch-resolve ScienceDirect DOIs to PIIs via Crossref API. Saves progress incrementally.

Supports three input formats (auto-detected):
  - BibTeX       (@article{key, doi = {10.1016/...}, ...})
  - Markdown     (table with | DOI | or | doi.org/... | columns)
  - Plain text   ([N] Author, ..., https://doi.org/10.1016/...)

Usage:
  python3 scripts/batch_resolve_pii.py 检索文献表.bib
  python3 scripts/batch_resolve_pii.py 检索文献表.md -o sd_pii_map.json
  python3 scripts/batch_resolve_pii.py ScienceDirect_Elsevier_文献.txt
  python3 scripts/batch_resolve_pii.py --help
"""
import re
import json
import urllib.request
import urllib.parse
import time
import sys
import os
import argparse


# ── DOI normalization ────────────────────────────────────────────────────────

def _clean_doi(raw: str) -> str:
    """Normalize a raw DOI string from any input format.

    Strips protocol prefix, trailing punctuation, and whitespace.
    Returns empty string if input is not a plausible DOI.
    """
    if not raw:
        return ""
    # Remove protocol prefix if present
    doi = raw.strip()
    doi = re.sub(r'^https?://doi\.org/', '', doi)
    # Strip trailing punctuation that gets caught in plain-text regex
    doi = doi.rstrip('.,;)]}\'"')
    return doi


# ── Format detection ─────────────────────────────────────────────────────────

_SD_DOI_PATTERN = re.compile(r'10\.1016/')


def _has_sd_doi(text: str) -> bool:
    """Check if text contains a ScienceDirect DOI (10.1016/...)."""
    return bool(_SD_DOI_PATTERN.search(text))


def _is_bibtex(text: str) -> bool:
    """Detect BibTeX format (@article{key, ...})."""
    return bool(re.search(r'^\s*@\w+\s*\{', text, re.MULTILINE))


def _is_markdown_table(text: str) -> bool:
    """Detect Markdown table with DOI column."""
    return bool(re.search(r'\|\s*(DOI|doi|Doi)\s*\|', text)) or \
           bool(re.search(r'\|\s*https?://doi\.org', text))


# ── DOI extraction (per-format) ──────────────────────────────────────────────

def _extract_dois_from_bibtex(text: str) -> list[tuple[str, str]]:
    """Extract (cite_key, doi) pairs from BibTeX entries.

    Uses the BibTeX citation key (e.g. liu2025topology) when available,
    falling back to sequential paper_NNN keys.
    """
    entries = re.split(r'\n@', text)
    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    for i, block in enumerate(entries):
        if not _has_sd_doi(block):
            continue

        key_m = re.search(r'\{([^,]+)', block)
        doi_m = re.search(r'doi\s*=\s*\{([^}]+)\}', block)
        if not doi_m:
            continue

        doi = _clean_doi(doi_m.group(1))
        if not doi or doi in seen:
            continue

        seen.add(doi)
        key = key_m.group(1).strip() if key_m else f"paper_{i + 1:03d}"
        results.append((key, doi))

    return results


def _extract_dois_from_text(text: str) -> list[tuple[str, str]]:
    """Extract DOIs from plain-text reference lists.

    Handles: [N] Author, ..., https://doi.org/10.1016/...
             bare 10.1016/... strings
    """
    doi_urls = re.findall(r'(?:https?://doi\.org/)?10\.1016/[^\s\'"}\]>]+', text)
    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    for raw in doi_urls:
        doi = _clean_doi(raw)
        if not doi or doi in seen:
            continue
        seen.add(doi)
        results.append((f"paper_{len(results) + 1:03d}", doi))

    return results


# Alias for Markdown — same extraction logic as plain text
_extract_dois_from_markdown = _extract_dois_from_text


# ── Crossref PII resolution ──────────────────────────────────────────────────

def _resolve_pii_from_crossref(doi: str, timeout: int = 10) -> str | None:
    """Resolve a single DOI to its ScienceDirect PII via Crossref API.

    Returns the PII string (e.g. 'S0148296323001114'), or None if not found.

    Looks for PII in two places:
      1. link[].URL containing 'PII:...'
      2. resource.primary.URL containing 'pii/...'
    """
    url = f'https://api.crossref.org/works/{urllib.parse.quote(doi)}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Hermes/1.0 (mailto:user@example.com)'
    })

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except Exception:
        return None

    msg = data.get('message', {})

    # Strategy 1: check link[] for PII: prefix
    for link in msg.get('link', []):
        m = re.search(r'PII:?([A-Z0-9]+)', link.get('URL', ''))
        if m:
            return m.group(1)

    # Strategy 2: check resource.primary.URL for pii/ segment
    primary_url = msg.get('resource', {}).get('primary', {}).get('URL', '')
    m = re.search(r'pii/([A-Z0-9]+)', primary_url)
    if m:
        return m.group(1)

    return None


# ── Progress persistence ─────────────────────────────────────────────────────

def _load_progress(output_path: str) -> tuple[dict[str, dict], list[tuple], set[str]]:
    """Load existing resolution progress from output file.

    Returns (resolved_dict, errors_list, already_done_keys_set).
    """
    if not os.path.exists(output_path):
        return {}, [], set()

    with open(output_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    resolved = existing.get('resolved', {})
    errors = existing.get('errors', [])
    done = set(resolved.keys()) | {e[0] for e in errors}
    return resolved, errors, done


def _save_progress(output_path: str, resolved: dict, errors: list) -> None:
    """Atomically write progress to output JSON file."""
    tmp = output_path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump({'resolved': resolved, 'errors': errors}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, output_path)


# ── Main resolution logic ────────────────────────────────────────────────────

def resolve_dois(input_path: str, output_path: str) -> dict:
    """Batch-resolve ScienceDirect DOIs to PIIs.

    Auto-detects input format (BibTeX / Markdown / plain text),
    resolves each DOI via Crossref API, saves progress every 5 items.

    Returns the output dict {'resolved': {...}, 'errors': [...]}.
    """
    # 1. Read and detect format
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    if _is_bibtex(text):
        fmt_label = "BibTeX"
        entries = _extract_dois_from_bibtex(text)
    elif _is_markdown_table(text):
        fmt_label = "Markdown 表格"
        entries = _extract_dois_from_markdown(text)
    else:
        fmt_label = "纯文本参考文献"
        entries = _extract_dois_from_text(text)

    print(f"检测到 {fmt_label} 格式", flush=True)

    if not entries:
        print("未找到 ScienceDirect DOI（10.1016/...）", flush=True)
        return {'resolved': {}, 'errors': []}

    print(f"待解析 SD DOI: {len(entries)} 条")

    # 2. Load prior progress
    resolved, errors, already_done = _load_progress(output_path)
    if already_done:
        print(f"从已有进度恢复: {len(resolved)} 已解析, {len(errors)} 错误")

    # 3. Resolve each DOI
    total = len(entries)
    for i, (key, doi) in enumerate(entries):
        if key in already_done:
            continue

        pii = _resolve_pii_from_crossref(doi)
        if pii:
            resolved[key] = {'doi': doi, 'pii': pii}
            status = f"OK → {pii}"
        else:
            errors.append((key, doi, 'pii_not_found'))
            status = "未找到 PII"

        # Incremental save every 5 items
        if (i + 1) % 5 == 0:
            _save_progress(output_path, resolved, errors)

        print(f"[{i + 1}/{total}] {key}: {status}", flush=True)
        time.sleep(0.3)

    # 4. Final save
    _save_progress(output_path, resolved, errors)

    print(f"\n{'=' * 40}")
    print(f"已解析: {len(resolved)} / {total}")
    print(f"错误:   {len(errors)}")
    print(f"已保存至: {output_path}")

    return {'resolved': resolved, 'errors': errors}


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch-resolve ScienceDirect DOIs to PIIs via Crossref API"
    )
    parser.add_argument(
        "input", nargs="?", default="检索文献表.md",
        help="Input file (BibTeX / Markdown table / plain text, auto-detected)"
    )
    parser.add_argument(
        "--output", "-o", default="sd_pii_map.json",
        help="Output JSON file (default: sd_pii_map.json)"
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}", flush=True)
        sys.exit(1)

    resolve_dois(args.input, args.output)
