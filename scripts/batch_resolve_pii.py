#!/usr/bin/env python3
"""Batch-resolve ScienceDirect DOIs to PIIs via Crossref API. Saves progress incrementally.

Usage:
  python3 scripts/batch_resolve_pii.py 检索文献表.md
  python3 scripts/batch_resolve_pii.py 检索文献表.md -o sd_pii_map.json
  python3 scripts/batch_resolve_pii.py --help
"""
import re, json, urllib.request, time, sys, os, argparse


def resolve_dois(bib_path, output_path):
    """Main resolution logic, separated from CLI for testability."""
    with open(bib_path, 'r', encoding='utf-8') as f:
        text = f.read()

    entries = re.split(r'\n@', text)
    sd_entries = []
    for e in entries:
        if 'Elsevier' in e or '10.1016/' in e:
            key_m = re.search(r'\{([^,]+)', e)
            key = key_m.group(1) if key_m else '?'
            doi_m = re.search(r'doi\s*=\s*\{([^}]+)\}', e)
            doi = doi_m.group(1) if doi_m else ''
            if doi and '10.1016/' in doi:
                sd_entries.append((key, doi))

    print(f"Total SD DOIs to resolve: {len(sd_entries)}")

    # Load existing progress
    results = {}
    errors = []
    if os.path.exists(output_path):
        with open(output_path) as f:
            existing = json.load(f)
        results = existing.get('resolved', {})
        errors = existing.get('errors', [])
        already_done = set(results.keys()) | set(e[0] for e in errors)
        print(f"Resuming with {len(results)} already resolved, {len(errors)} errors")
    else:
        already_done = set()

    for i, (key, doi) in enumerate(sd_entries):
        if key in already_done:
            continue

        pii = None
        error = None
        try:
            url = f'https://api.crossref.org/works/{doi}'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Hermes/1.0 (mailto:user@example.com)'
            })
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            msg = data.get('message', {})

            for l in msg.get('link', []):
                lurl = l.get('URL', '')
                m = re.search(r'PII:?([A-Z0-9]+)', lurl)
                if m:
                    pii = m.group(1)
                    break
            if not pii:
                res_url = msg.get('resource', {}).get('primary', {}).get('URL', '')
                m = re.search(r'pii/([A-Z0-9]+)', res_url)
                if m:
                    pii = m.group(1)
        except Exception as ex:
            error = str(ex)[:80]

        if pii:
            results[key] = {'doi': doi, 'pii': pii}
            status = f'OK -> {pii}'
        else:
            errors.append((key, doi, error or 'no_pii'))
            status = f'ERR: {error or "no_pii"}'

        # Save every 5 items
        if (i+1) % 5 == 0:
            with open(output_path, 'w') as f:
                json.dump({'resolved': results, 'errors': errors}, f, indent=2)

        print(f"[{i+1}/{len(sd_entries)}] {key}: {status}")
        time.sleep(0.3)

    # Final save
    with open(output_path, 'w') as f:
        json.dump({'resolved': results, 'errors': errors}, f, indent=2)
    print(f"\n{'='*40}")
    print(f"Resolved: {len(results)} / {len(sd_entries)}")
    print(f"Errors: {len(errors)}")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch-resolve ScienceDirect DOIs to PIIs via Crossref API")
    parser.add_argument("input", nargs="?", default="检索文献表.md",
                        help="Input file with DOIs (BibTeX or Markdown table)")
    parser.add_argument("--output", "-o", default="sd_pii_map.json",
                        help="Output JSON file (default: sd_pii_map.json)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}", flush=True)
        exit(1)

    resolve_dois(args.input, args.output)
