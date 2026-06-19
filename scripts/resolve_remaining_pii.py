#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""Resolve remaining (unresolved) SD DOIs to PIIs — resume after interruptions.

Usage:
  python3 scripts/resolve_remaining_pii.py
  python3 scripts/resolve_remaining_pii.py 导出的条目.bib -o sd_pii_map.json
"""
try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import json, os, sys, argparse, re, urllib.request, time


def resolve_remaining(bib_path, map_path):
    """Continuation logic: resolve DOIs not yet in the PII map."""
    if not os.path.exists(map_path):
        print(f"错误: PII 映射文件不存在: {map_path}", flush=True)
        print("请先运行 batch_resolve_pii.py", flush=True)
        return

    # Load existing
    with open(map_path, encoding="utf-8") as f:
        data = json.load(f)
    results = data.get('resolved', {})
    errors = data.get('errors', [])

    # Get remaining DOIs from bib
    with open(bib_path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    entries = re.split(r'\n@', text)
    remaining = []
    for e in entries:
        if 'Elsevier' not in e and '10.1016/' not in e:
            continue
        key_m = re.search(r'\{([^,]+)', e)
        key = key_m.group(1) if key_m else '?'
        if key in results:
            continue
        err_keys = [e[0] for e in errors]
        if key in err_keys:
            continue
        doi_m = re.search(r'doi\s*=\s*\{([^}]+)\}', e)
        doi = doi_m.group(1) if doi_m else ''
        if doi and '10.1016/' in doi:
            remaining.append((key, doi))

    print(f"Remaining to resolve: {len(remaining)}")

    if not remaining:
        print("Nothing to do!")
        return

    for i, (key, doi) in enumerate(remaining):
        pii = None
        error = None
        try:
            url = f'https://api.crossref.org/works/{doi}'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Hermes/1.0 (mailto:user@example.com)'
            })
            resp = urllib.request.urlopen(req, timeout=8)
            msg = json.loads(resp.read()).get('message', {})

            for l in msg.get('link', []):
                lurl = l.get('URL', '')
                m = re.search(r'PII:?([A-Z0-9]+)', lurl)
                if m:
                    pii = m.group(1)
                    break
            if not pii:
                m = re.search(r'pii/([A-Z0-9]+)',
                              msg.get('resource', {}).get('primary', {}).get('URL', ''))
                if m:
                    pii = m.group(1)
        except Exception as ex:
            error = str(ex)[:80]

        if pii:
            results[key] = {'doi': doi, 'pii': pii}
            print(f'  OK [{i+1}/{len(remaining)}] {key}: {pii}')
        else:
            errors.append((key, doi, error or 'no_pii'))
            print(f'  ERR [{i+1}/{len(remaining)}] {key}: {error or "no_pii"}')

        time.sleep(0.3)

    with open(map_path, 'w', encoding="utf-8") as f:
        json.dump({'resolved': results, 'errors': errors}, f, indent=2)
    print(f"\nDone: {len(results)} resolved total, {len(errors)} errors")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resolve remaining (unresolved) SD DOIs to PIIs")
    parser.add_argument("input", nargs="?", default="导出的条目.bib",
                        help="BibTeX file with DOI entries (default: 导出的条目.bib)")
    parser.add_argument("--output", "-o", default="sd_pii_map.json",
                        help="PII mapping JSON to update (default: sd_pii_map.json)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}", flush=True)
        exit(1)

    resolve_remaining(args.input, args.output)
