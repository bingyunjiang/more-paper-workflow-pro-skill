#!/usr/bin/env python3
"""
Auto-restart ScienceDirect PDF batch downloader — cross-platform (macOS / Windows / Linux).

Automatically detects Chrome and/or Edge. When both are available, runs dual-browser
parallel download (papers split 50/50). Gracefully degrades to single-browser mode.

Usage:
    python3 scripts/auto_sd_downloader.py
    python3 scripts/auto_sd_downloader.py --output-dir download/paper-temp
    python3 scripts/auto_sd_downloader.py --browser chrome   # force single browser

Requires:
    - Google Chrome and/or Microsoft Edge (auto-detected)
    - ScienceDirect institutional access (IP-based or SSO)
    - sd_pii_map.json in the current directory (from batch_resolve_pii.py)
"""
import json, time, os, base64, sys, argparse, threading

# Ensure scripts/ is on the path so `from cdp_utils import ...` works
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdp_utils import (
    check_cdp, close_all_tabs, create_tab, get_tab_ws_url,
    wait_for_tab_url, capture_pdf_via_fetch,
    find_chrome_path, find_edge_path, start_browser, kill_browser_by_port,
    kill_browser_by_profile, remove_profile_dir,
    CHROME_INSTALL_GUIDE, EDGE_INSTALL_GUIDE, check_required_deps,
    check_sd_access, SD_ACCESS_GUIDE_IP, SD_ACCESS_GUIDE_LOGIN, SD_ACCESS_GUIDE_BLOCKED,
)

SD_PDF_HOST = "https://pdf.sciencedirectassets.com"
SD_FETCH_PATTERN = "*pdf.sciencedirectassets.com*main.pdf*"
_BASE_TMP = os.environ.get("TMPDIR", os.environ.get("TEMP", "/tmp"))

# Each browser gets its own profile dir to avoid conflicts
DEFAULT_PROFILES = {
    "chrome": os.path.join(_BASE_TMP, "sd_chrome_profile"),
    "edge": os.path.join(_BASE_TMP, "sd_edge_profile"),
}


def restart_browser(port, browser_path, profile_dir):
    """Kill any existing browser on this port, remove profile, start fresh."""
    kill_browser_by_port(port)
    kill_browser_by_profile(profile_dir)
    remove_profile_dir(profile_dir)

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
    """Check SD access; if blocked, wait 30s for manual login. Returns True if OK."""
    status, reason = check_sd_access(port)
    if status == "ok":
        print(f"  {'IP 认证' if reason == 'ip' else '已登录'} — 端口 {port}", flush=True)
        return True
    print(f"  SD 访问异常 (端口 {port}): {reason}", flush=True)
    print(SD_ACCESS_GUIDE_BLOCKED, flush=True)
    print("  等待 30 秒供你手动登录...", flush=True)
    time.sleep(30)
    status, _ = check_sd_access(port)
    return status == "ok"


def download_one(key, pii, port, timeout):
    """Download a single SD paper PDF via CDP."""
    pdfft = f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft"
    if not check_cdp(port):
        return None
    try:
        create_tab(port, pdfft)
    except Exception:
        return None
    pdf_tab = wait_for_tab_url(port, SD_PDF_HOST, timeout=timeout)
    if not pdf_tab:
        close_all_tabs(port)
        return None
    tab_ws_url = get_tab_ws_url(port, pdf_tab["id"])
    if not tab_ws_url:
        close_all_tabs(port)
        return None
    pdf_data = capture_pdf_via_fetch(port, tab_ws_url, SD_FETCH_PATTERN,
                                     request_path_hint="main.pdf")
    close_all_tabs(port)
    return pdf_data


def _worker(name, port, papers, output_dir, timeout, per_paper_max_s,
            max_consecutive_fail, results, log_lock):
    """Download a list of papers on one browser; updates shared results dict."""
    ok, fail = 0, 0
    consec = 0
    for i, (key, doi, pii) in enumerate(papers):
        # Check stop signal (other worker hit consecutive fail limit)
        if results.get("_stop"):
            break

        t0 = time.time()
        data = download_one(key, pii, port, timeout)
        et = time.time() - t0

        if et > per_paper_max_s and not data:
            fail += 1
            consec += 1
            with log_lock:
                print(f"[{name}] TIMEOUT {key} ({et:.0f}s) [{i+1}/{len(papers)}]")
            continue

        if data and len(data) > 20000:
            fpath = os.path.join(output_dir, f"{key}.pdf")
            with open(fpath, "wb") as f:
                f.write(data)
            ok += 1
            consec = 0
            with log_lock:
                results["total"] = results.get("total", 0) + 1
                print(f"[{name}] ✅ {key}: {len(data)//1024}KB ({et:.0f}s) [{i+1}/{len(papers)}]")
        else:
            fail += 1
            consec += 1
            with log_lock:
                print(f"[{name}] ❌ {key} ({et:.0f}s) [{i+1}/{len(papers)}]")

        if consec >= max_consecutive_fail:
            with log_lock:
                print(f"[{name}] {consec} 次连续失败，信号重启...")
                results["_stop"] = True
            break

    return ok, fail


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Auto-restart ScienceDirect PDF batch downloader (supports dual-browser parallel)")
    parser.add_argument("--output-dir", "-o", default="download/paper-temp",
                        help="PDF output directory")
    parser.add_argument("--pii-map", "-p", default="./sd_pii_map.json",
                        help="DOI→PII mapping JSON")
    parser.add_argument("--browser", choices=["auto", "chrome", "edge"], default="auto",
                        help="auto=detect Chrome+Edge, chrome/edge=single browser")
    parser.add_argument("--browser-path",
                        help="Browser executable path (overrides auto-detection for primary browser)")
    parser.add_argument("--browser-path-edge",
                        help="Edge executable path (for dual-browser parallel mode)")
    parser.add_argument("--port-chrome", type=int, default=9223)
    parser.add_argument("--port-edge", type=int, default=9225)
    parser.add_argument("--timeout", type=int, default=50,
                        help="Seconds to wait for PDF redirect")
    parser.add_argument("--max-consecutive-fail", type=int, default=5,
                        help="Consecutive failures before restart")
    parser.add_argument("--per-paper-max-s", type=int, default=120,
                        help="Per-paper timeout in seconds")
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
    # Each entry: (name, path, port, profile_dir)
    browsers = []

    # Chrome
    chrome_path = None
    if args.browser in ("auto", "chrome"):
        chrome_path = find_chrome_path()
    if chrome_path:
        browsers.append(("Chrome", chrome_path, args.port_chrome,
                         DEFAULT_PROFILES["chrome"]))

    # Edge — only add if auto mode and we want dual-browser
    edge_path = None
    if args.browser == "auto" and not args.browser_path:
        edge_path = args.browser_path_edge or find_edge_path()
    if edge_path and edge_path != chrome_path:
        # Avoid duplicate if both point to same binary (e.g. Chromium)
        if not browsers or edge_path != browsers[0][1]:
            browsers.append(("Edge", edge_path, args.port_edge,
                             DEFAULT_PROFILES["edge"]))

    # Single-browser forced path override
    if args.browser_path and not browsers:
        browsers.append(("custom", args.browser_path, args.port_chrome,
                         DEFAULT_PROFILES["chrome"]))

    if not browsers:
        print(CHROME_INSTALL_GUIDE, flush=True)
        exit(1)

    # ---- Display configuration ----
    if len(browsers) == 2:
        print(f"🚀 双浏览器并行模式:", flush=True)
    else:
        print(f"🖥️ 单浏览器模式:", flush=True)
    for name, path, port, prof in browsers:
        print(f"   {name}: {path} (port {port})", flush=True)
    print()

    # ---- Load paper list ----
    def load_remaining():
        with open(PII_MAP) as f:
            data = json.load(f)
        pii_list = [(k, v["doi"], v["pii"]) for k, v in data["resolved"].items()]
        done = set(f[:-4] for f in os.listdir(OUTPUT_DIR) if f.endswith(".pdf"))
        remaining = [p for p in pii_list if p[0] not in done]
        return remaining, len(done)

    total_downloaded = 0
    wave = 0

    while True:
        remaining, already_done = load_remaining()
        if not remaining:
            print(f"\n🎉 ALL DONE! Total: {already_done} papers", flush=True)
            break

        wave += 1
        print(f"\n{'='*55}", flush=True)
        print(f"Wave {wave}: {len(remaining)} remaining, {already_done} done", flush=True)
        print(f"{'='*55}", flush=True)

        # ---- Restart all browsers ----
        all_ready = True
        for name, path, port, prof in browsers:
            print(f"Starting {name} (port {port})...", flush=True)
            if not restart_browser(port, path, prof):
                print(f"  ❌ Failed to start {name}", flush=True)
                all_ready = False
            else:
                ensure_sd_access(port)

        if not all_ready:
            print("Failed to start one or more browsers, aborting", flush=True)
            break

        # ---- Split papers across browsers ----
        n = len(browsers)
        chunk_size = len(remaining) // n
        assignments = []
        for idx, (name, path, port, prof) in enumerate(browsers):
            if idx == n - 1:
                chunk = remaining[idx * chunk_size:]
            else:
                chunk = remaining[idx * chunk_size:(idx + 1) * chunk_size]
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
                args=(name, port, chunk, OUTPUT_DIR, args.timeout,
                      args.per_paper_max_s, args.max_consecutive_fail,
                      results, log_lock)
            )
            threads.append(t)

        t0 = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        wave_ok = results.get("total", 0)
        print(f"\nWave {wave} done: downloaded {wave_ok} papers "
              f"({(time.time()-t0)/60:.1f}min)", flush=True)

    # ---- Cleanup ----
    for name, path, port, prof in browsers:
        kill_browser_by_port(port)
        kill_browser_by_profile(prof)
    print(f"\nFINAL: papers in {OUTPUT_DIR}", flush=True)
