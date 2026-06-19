#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Auto-restart ScienceDirect PDF batch downloader — cross-platform (macOS / Windows / Linux).

Automatically detects Chrome and/or Edge. When both are available, runs dual-browser
parallel download (papers split 50/50). Gracefully degrades to single-browser mode.

Hybrid download strategy:
  A (fast): /pdfft direct redirect → capture (8s)
  B (fallback): article page → extract ?md5= URL → capture (20s)

Usage:
    python3 scripts/auto_sd_downloader.py
    python3 scripts/auto_sd_downloader.py --output-dir download/paper-temp
    python3 scripts/auto_sd_downloader.py --browser chrome   # force single browser

Design principle: all papers are accessible; failure means need a better strategy.
"""
import json, time, os, sys, argparse, threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdp_utils import (
    check_cdp, start_browser, kill_browser_by_port, kill_browser_by_profile,
    find_chrome_path, find_edge_path, check_required_deps,
    check_sd_access, CHROME_INSTALL_GUIDE,
)
from console_compat import configure_console_output
from sd_download import download_sd_pii

# Each browser gets its own persistent profile dir — retains SD login across runs
DEFAULT_PROFILES = {
    "chrome": os.path.join(os.path.expanduser("~/.hermes"), "chrome_sd_profile"),
    "edge": os.path.join(os.path.expanduser("~/.hermes"), "edge_sd_profile"),
}


def _load_remaining_papers(pii_map_path: str, output_dir: str):
    """Load remaining papers from a UTF-8 JSON mapping file."""
    with open(pii_map_path, encoding="utf-8") as f:
        data = json.load(f)
    pii_list = [(k, v["doi"], v["pii"]) for k, v in data["resolved"].items()]
    done = set(
        f[:-4]
        for f in os.listdir(output_dir)
        if f.startswith("paper_") and f.endswith(".pdf")
    )
    remaining = [p for p in pii_list if p[0] not in done]
    return remaining, len(done)


def restart_browser(port, browser_path, profile_dir):
    """Kill any existing browser on this port, start fresh with the persistent profile."""
    kill_browser_by_port(port)
    kill_browser_by_profile(profile_dir)
    # Do NOT remove profile_dir — retain SD cookies across restarts

    proc = start_browser(port, profile_dir,
                         url="https://www.sciencedirect.com",
                         browser_path=browser_path)
    if proc is None:
        return False
    for _ in range(15):
        time.sleep(1)
        if check_cdp(port):
            return True
    return False


def ensure_sd_access(port):
    """Check SD access; if blocked, wait 30s for manual login."""
    status, reason = check_sd_access(port)
    if status == "ok":
        print(f"  {'IP 认证' if reason == 'ip' else '已登录'} — 端口 {port}", flush=True)
        return True
    print(f"  SD 访问异常 (端口 {port}): {reason}", flush=True)
    print("  等待 30 秒供你手动登录...", flush=True)
    time.sleep(30)
    status, _ = check_sd_access(port)
    return status == "ok"


def _worker(name, port, papers, output_dir, results, log_lock):
    """Download a list of papers on one browser."""
    ok, fail = 0, 0
    for i, (key, doi, pii) in enumerate(papers):
        if results.get("_stop"):
            break

        t0 = time.time()
        data = download_sd_pii(port, pii)
        et = time.time() - t0

        if data and len(data) > 20000:
            fpath = os.path.join(output_dir, f"{key}.pdf")
            with open(fpath, "wb") as f:
                f.write(data)
            ok += 1
            with log_lock:
                results["total"] = results.get("total", 0) + 1
                print(f"[{name}] ✅ {key}: {len(data)//1024}KB ({et:.0f}s) [{i+1}/{len(papers)}]", flush=True)
        else:
            fail += 1
            with log_lock:
                print(f"[{name}] ❌ {key} ({et:.0f}s) [{i+1}/{len(papers)}]", flush=True)

    return ok, fail


if __name__ == "__main__":
    configure_console_output()

    parser = argparse.ArgumentParser(
        description="Auto-restart SD PDF downloader — hybrid strategy (direct + article page extraction)")
    parser.add_argument("--output-dir", "-o", default="download/paper-temp",
                        help="PDF output directory")
    parser.add_argument("--pii-map", "-p", default="./sd_pii_map.json",
                        help="DOI→PII mapping JSON")
    parser.add_argument("--browser", choices=["auto", "chrome", "edge"], default="auto",
                        help="auto=detect Chrome+Edge, chrome/edge=single browser")
    parser.add_argument("--browser-path",
                        help="Browser executable path (overrides auto-detection)")
    parser.add_argument("--browser-path-edge",
                        help="Edge executable path (for dual-browser parallel mode)")
    parser.add_argument("--port-chrome", type=int, default=9223)
    parser.add_argument("--port-edge", type=int, default=9225)
    parser.add_argument("--timeout-a", type=int, default=8,
                        help="Seconds for Strategy A — direct /pdfft (default: 8)")
    parser.add_argument("--timeout-b", type=int, default=20,
                        help="Seconds for Strategy B — article page extraction (default: 20)")
    parser.add_argument("--restart", action="store_true",
                        help="Force restart the browser (KILLS existing session — requires re-login!)")
    args = parser.parse_args()

    if not check_required_deps():
        exit(1)

    OUTPUT_DIR = args.output_dir
    PII_MAP = args.pii_map
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(PII_MAP):
        print(f"错误: PII 映射文件不存在: {PII_MAP}", flush=True)
        print("请先运行 batch_resolve_pii.py 生成该文件", flush=True)
        exit(1)

    # ---- Resolve browser(s) ----
    browsers = []
    chrome_path = find_chrome_path() if args.browser in ("auto", "chrome") else None
    if chrome_path:
        browsers.append(("Chrome", chrome_path, args.port_chrome, DEFAULT_PROFILES["chrome"]))

    edge_path = None
    if args.browser == "auto" and not args.browser_path:
        edge_path = args.browser_path_edge or find_edge_path()
    if edge_path and edge_path != chrome_path:
        if not browsers or edge_path != browsers[0][1]:
            browsers.append(("Edge", edge_path, args.port_edge, DEFAULT_PROFILES["edge"]))

    if args.browser_path and not browsers:
        browsers.append(("Custom", args.browser_path, args.port_chrome, DEFAULT_PROFILES["chrome"]))

    if not browsers:
        print(CHROME_INSTALL_GUIDE, flush=True)
        exit(1)

    # ---- Load paper list ----
    wave = 0
    zero_progress_waves = 0

    while True:
        remaining, already_done = _load_remaining_papers(PII_MAP, OUTPUT_DIR)
        if not remaining:
            print(f"\n🎉 ALL DONE! Total: {already_done}/94 papers", flush=True)
            break

        wave += 1
        print(f"\n{'='*55}", flush=True)
        print(f"Wave {wave}: {len(remaining)} remaining, {already_done} done", flush=True)
        print(f"策略: 直连({args.timeout_a}s) → 文章页提取({args.timeout_b}s)", flush=True)
        print(f"{'='*55}", flush=True)

        # ---- Start or confirm browsers ----
        all_ready = True
        if args.restart:
            # Explicit restart requested — kills existing session (will require re-login!)
            for name, path, port, prof in browsers:
                print(f"⚠️ 强制重启 {name} (port {port}) — 将丢失登录会话！", flush=True)
                if not restart_browser(port, path, prof):
                    print(f"  ❌ Failed to start {name}", flush=True)
                    all_ready = False
                else:
                    ensure_sd_access(port)
        else:
            # Default: reuse existing CDP session (preserves login cookies)
            for name, path, port, prof in browsers:
                if check_cdp(port):
                    print(f"  ✅ {name} (port {port}) — 复用现有会话", flush=True)
                    if not ensure_sd_access(port):
                        all_ready = False
                else:
                    print(f"  ⚠️ {name} (port {port}) CDP 未运行，启动中...", flush=True)
                    if not restart_browser(port, path, prof):
                        print(f"  ❌ Failed to start {name}", flush=True)
                        all_ready = False
                    else:
                        ensure_sd_access(port)

        if not all_ready:
            print("浏览器不可用，退出", flush=True)
            break

        # ---- Split papers across browsers ----
        n = len(browsers)
        chunk_size = len(remaining) // n
        assignments = []
        for idx, (name, path, port, prof) in enumerate(browsers):
            chunk = remaining[idx * chunk_size:] if idx == n - 1 else remaining[idx * chunk_size:(idx + 1) * chunk_size]
            assignments.append((name, port, chunk))

        for name, port, chunk in assignments:
            print(f"  {name}: {len(chunk)} papers", flush=True)
        print()

        # ---- Parallel download ----
        log_lock = threading.Lock()
        results = {"total": 0, "_stop": False}
        threads = []

        for name, port, chunk in assignments:
            t = threading.Thread(
                target=_worker,
                args=(name, port, chunk, OUTPUT_DIR, results, log_lock)
            )
            threads.append(t)

        t0 = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        wave_ok = results.get("total", 0)
        print(f"\nWave {wave} done: {wave_ok} papers ({((time.time()-t0)/60):.1f}min)", flush=True)

        # Zero-progress guard (restart loop detection)
        if wave_ok == 0:
            zero_progress_waves += 1
            if zero_progress_waves >= 2:
                print(f"\n⛔ 连续 {zero_progress_waves} 波零下载，退出。", flush=True)
                break
        else:
            zero_progress_waves = 0

    # Keep browser alive — do not kill
    total = len([f for f in os.listdir(OUTPUT_DIR) if f.startswith("paper_") and f.endswith(".pdf")])
    print(f"\nFINAL: {total} paper_* PDFs in {OUTPUT_DIR}", flush=True)
