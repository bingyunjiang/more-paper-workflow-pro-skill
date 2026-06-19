#!/usr/bin/env python3
"""Cross-platform interactive CNKI/Wanfang batch search helper.

Protocol markers are intentionally compatible with the historical
batch_chinese_search.sh wrapper.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from cdp_utils import check_cdp, list_tabs, start_persistent_cdp_browser


CNKI_URL = "https://kns.cnki.net/kns8s/"
WANFANG_URL = "https://www.wanfangdata.com.cn/"


def _load_queries(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("queries file must contain a JSON list")
    return data


def _navigate_initial_tabs(port: int) -> None:
    """Best-effort tab positioning for the visible login browser."""
    try:
        import websocket

        pages = [t for t in list_tabs(port) if t.get("type") == "page"]
        if not pages:
            return

        targets = [(pages[0], CNKI_URL)]
        if len(pages) > 1:
            targets.append((pages[1], WANFANG_URL))

        for page, url in targets:
            ws_url = page.get("webSocketDebuggerUrl")
            if not ws_url:
                continue
            ws = websocket.create_connection(ws_url, timeout=10)
            try:
                ws.send(json.dumps({
                    "id": 1,
                    "method": "Page.navigate",
                    "params": {"url": url},
                }))
                ws.recv()
            finally:
                ws.close()
    except Exception:
        pass


def _ensure_chinese_cdp(port: int, browser: str) -> bool:
    if check_cdp(port):
        print(f"CDP_ALIVE:{port}", flush=True)
        return True

    print(f"CDP_CHROME_STARTING:{port}", flush=True)
    proc = start_persistent_cdp_browser(
        port=port,
        browser=browser,
        urls=[CNKI_URL, WANFANG_URL],
    )
    if not proc or not check_cdp(port):
        print(f"ERROR: CDP Chrome failed to start on port {port}", flush=True)
        return False

    print(f"CDP_READY:{port}", flush=True)
    return True


def _run_searches(queries: list[dict], output_dir: Path, port: int) -> tuple[int, int]:
    script_dir = Path(__file__).resolve().parent
    search_script = script_dir / "search_by_topic.py"
    success = 0
    failed = 0

    for idx, query_spec in enumerate(queries):
        qid = query_spec.get("id", f"Q{idx + 1}")
        query = query_spec.get("query", "")
        source = query_spec.get("source", "cnki")
        limit = str(query_spec.get("limit", 50))
        strategy = query_spec.get("strategy", "")

        if not query:
            failed += 1
            continue

        print(f"SEARCH_START:{qid} ({idx + 1}/{len(queries)})", flush=True)
        bib_file = output_dir / f"{qid}_{source}.bib"

        cmd = [
            sys.executable,
            str(search_script),
            query,
            "--source",
            source,
            "--limit",
            limit,
            "--no-cache",
            "--language",
            "zh",
            "--export-bib",
            str(bib_file),
        ]
        if strategy:
            cmd.extend(["--strategy", strategy])

        env = os.environ.copy()
        env["CDP_PORT"] = str(port)

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
            if bib_file.exists():
                bib_count = sum(
                    1 for line in bib_file.read_text(encoding="utf-8", errors="replace").splitlines()
                    if line.startswith("@")
                )
                print(f"SEARCH_DONE:{qid}:{bib_count}", flush=True)
                success += 1
            else:
                print(f"SEARCH_DONE:{qid}:0 (no output)", flush=True)
                failed += 1
        except Exception as exc:
            print(f"SEARCH_DONE:{qid}:0 (error: {exc})", flush=True)
            failed += 1

    return success, failed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Interactive batch: CDP Chrome -> login -> CNKI+Wanfang search"
    )
    parser.add_argument("queries_file", nargs="?", help="JSON query file")
    parser.add_argument("--port", type=int, default=9223, help="CDP debug port")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--login-only", action="store_true", help="Only start browser and wait for login")
    parser.add_argument("--browser", choices=("chrome", "edge"), default="chrome")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    queries: list[dict] = []
    if not args.login_only:
        if not args.queries_file:
            print("ERROR: queries.json required", flush=True)
            return 1
        queries_path = Path(args.queries_file)
        if not queries_path.exists():
            print(f"ERROR: file not found: {queries_path}", flush=True)
            return 1
        try:
            queries = _load_queries(queries_path)
        except Exception as exc:
            print(f"ERROR: invalid queries file: {exc}", flush=True)
            return 1
        if not queries:
            print(f"ERROR: No valid queries found in {queries_path}", flush=True)
            return 1

    if not _ensure_chinese_cdp(args.port, args.browser):
        return 1

    _navigate_initial_tabs(args.port)

    print("", flush=True)
    print("=== LOGIN_REQUIRED ===", flush=True)
    print("Chrome opened. Please complete CARSI institution login in the browser.", flush=True)
    print("  • CNKI:   kns.cnki.net/kns8s/  → 右上角「机构登录」", flush=True)
    print("  • Wanfang: www.wanfangdata.com.cn → 右上角「登录」→ CARSI", flush=True)
    print("Type 'go' and press Enter when logged in:", flush=True)

    try:
        confirm = input()
    except EOFError:
        confirm = ""

    if confirm != "go":
        print("SKIPPED", flush=True)
        return 0

    if args.login_only:
        print("CHINESE_CDP_READY", flush=True)
        return 0

    success, failed = _run_searches(queries, output_dir, args.port)
    print("", flush=True)
    print("=== ALL_DONE ===", flush=True)
    print(f"Results: {success} success, {failed} failed (out of {len(queries)} queries)", flush=True)
    print(f"Output: {output_dir}/", flush=True)

    for bib in sorted(output_dir.glob("*.bib"))[:20]:
        print(str(bib), flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
