#!/usr/bin/env python3
"""
ScienceDirect PDF download via CDP — auto-detects Chrome and/or Edge.

If both browsers are running with CDP, splits the paper list in half
for parallel download. Gracefully degrades to single-browser mode
when only one is available.

Usage:
  1. Start Chrome (and optionally Edge) with CDP and login to ScienceDirect
  2. python3 scripts/parallel_sd_download.py
  3. Script auto-detects which browsers are available

Requires:
  - sd_pii_map.json (DOI→PII mapping, from batch_resolve_pii.py)
  - At least one CDP browser running with SD logged in
"""
import json, time, os, base64, sys, threading, argparse

# Ensure scripts/ is on the path so `from cdp_utils import ...` works
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdp_utils import (check_cdp, close_all_tabs, create_tab, get_tab_ws_url,
                        wait_for_tab_url, capture_pdf_via_fetch, check_required_deps,
                        check_sd_access, SD_ACCESS_GUIDE_IP, SD_ACCESS_GUIDE_LOGIN,
                        SD_ACCESS_GUIDE_BLOCKED)

log_lock = threading.Lock()

# ScienceDirect PDF redirect target
SD_PDF_HOST = "https://pdf.sciencedirectassets.com"
SD_FETCH_PATTERN = "*pdf.sciencedirectassets.com*main.pdf*"


def download_one(port, key, pii, timeout):
    """Download a single ScienceDirect paper PDF via CDP.

    Flow: navigate to pdfft → wait for PDF redirect → capture via Fetch domain.
    """
    pdfft = f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft"

    if not check_cdp(port):
        return None

    # Step 1: create tab and navigate to pdfft URL
    try:
        wu, tid = create_tab(port, pdfft)
    except Exception:
        return None

    # Step 2: wait for the PDF asset URL to appear (SD redirects to pdf.sciencedirectassets.com)
    pdf_tab = wait_for_tab_url(port, SD_PDF_HOST, timeout=timeout)
    if not pdf_tab:
        close_all_tabs(port)
        return None

    tab_ws_url = get_tab_ws_url(port, pdf_tab["id"])
    if not tab_ws_url:
        close_all_tabs(port)
        return None

    # Step 3: capture PDF bytes via Fetch domain
    pdf_data = capture_pdf_via_fetch(port, tab_ws_url, SD_FETCH_PATTERN,
                                     request_path_hint="main.pdf")
    close_all_tabs(port)
    return pdf_data

def worker(name, port, papers, output_dir, timeout):
    ok, fail = 0, 0
    for i, (key, doi, pii) in enumerate(papers):
        t0 = time.time()
        data = download_one(port, key, pii, timeout)
        et = time.time() - t0
        if data and len(data) > 20000:
            fpath = os.path.join(output_dir, f"{key}.pdf")
            with open(fpath, "wb") as f: f.write(data)
            ok += 1
            with log_lock:
                print(f"[{name}] OK {key}: {len(data)//1024}KB ({et:.0f}s) [{i+1}/{len(papers)}]")
        else:
            fail += 1
            with log_lock:
                print(f"[{name}] NO {key} ({et:.0f}s) [{i+1}/{len(papers)}]")
    return ok, fail


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ScienceDirect PDF download — auto-detects Chrome and/or Edge")
    parser.add_argument("--output-dir", "-o", default="download/paper-temp",
                        help="PDF output directory (default: download/paper-temp)")
    parser.add_argument("--pii-map", "-p", default="./sd_pii_map.json",
                        help="DOI→PII mapping JSON from batch_resolve_pii.py (default: ./sd_pii_map.json)")
    parser.add_argument("--port-chrome", type=int, default=9223,
                        help="Chrome CDP port (default: 9223)")
    parser.add_argument("--port-edge", type=int, default=9225,
                        help="Edge CDP port (default: 9225)")
    parser.add_argument("--timeout", "-t", type=int, default=10,
                        help="Seconds to wait for PDF redirect before skip (default: 10)")
    args = parser.parse_args()

    if not check_required_deps():
        exit(1)

    OUTPUT_DIR = args.output_dir
    PII_MAP = args.pii_map
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(PII_MAP):
        print(f"错误: PII 映射文件不存在: {PII_MAP}", flush=True)
        print(f"请先运行 batch_resolve_pii.py 生成该文件", flush=True)
        exit(1)

    # ---- Detect available browsers ----
    chrome_ok = check_cdp(args.port_chrome)
    edge_ok = check_cdp(args.port_edge)

    if not chrome_ok and not edge_ok:
        print("❌ 未检测到任何 CDP 浏览器。", flush=True)
        print(f"   Chrome (port {args.port_chrome}): 未运行", flush=True)
        print(f"   Edge   (port {args.port_edge}): 未运行", flush=True)
        print("\n  请先以 CDP 模式启动浏览器并登录 ScienceDirect：", flush=True)
        print(f"   Chrome:  google-chrome --remote-debugging-port={args.port_chrome} ...")
        print(f"   Edge:    msedge --remote-debugging-port={args.port_edge} ...")
        print("\n  或使用全自动版本: python3 scripts/auto_sd_downloader.py", flush=True)
        exit(1)

    # Build worker list
    workers = []
    if chrome_ok:
        # Check SD access
        sd_status, sd_reason = check_sd_access(args.port_chrome, timeout=8)
        if sd_status == "ok":
            workers.append(("Chrome", args.port_chrome))
            print(f"✅ Chrome (:{args.port_chrome}) — SD {'IP 认证' if sd_reason == 'ip' else '已登录'}", flush=True)
        else:
            print(f"⚠ Chrome (:{args.port_chrome}) — {sd_reason}", flush=True)

    if edge_ok:
        sd_status, sd_reason = check_sd_access(args.port_edge, timeout=8)
        if sd_status == "ok":
            workers.append(("Edge", args.port_edge))
            print(f"✅ Edge   (:{args.port_edge}) — SD {'IP 认证' if sd_reason == 'ip' else '已登录'}", flush=True)
        else:
            print(f"⚠ Edge   (:{args.port_edge}) — {sd_reason}", flush=True)

    if not workers:
        print("\n❌ 浏览器已运行但无法访问 ScienceDirect。", flush=True)
        print(SD_ACCESS_GUIDE_BLOCKED, flush=True)
        exit(1)

    # ---- Load paper list ----
    with open(PII_MAP) as f:
        data = json.load(f)
    pii_list = [(k, v['doi'], v['pii']) for k, v in data['resolved'].items()]
    done = set(f[:-4] for f in os.listdir(OUTPUT_DIR) if f.endswith('.pdf'))
    remaining = [p for p in pii_list if p[0] not in done]
    total = len(remaining)

    # ---- Distribute papers across available browsers ----
    if len(workers) == 2:
        half = total // 2
        assignments = [
            (workers[0], remaining[:half]),
            (workers[1], remaining[half:]),
        ]
        print(f"\n双浏览器并行: {total} 篇 | {workers[0][0]}: {len(remaining[:half])} | {workers[1][0]}: {len(remaining[half:])}", flush=True)
    else:
        assignments = [(workers[0], remaining)]
        print(f"\n单浏览器模式: {total} 篇 → {workers[0][0]}", flush=True)

    # ---- Download ----
    threads = []
    for (name, port), papers in assignments:
        t = threading.Thread(
            target=worker,
            args=(name, port, papers, OUTPUT_DIR, args.timeout)
        )
        threads.append(t)

    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    em = (time.time() - t0) / 60
    print(f"\nDone: {em:.1f}min", flush=True)
    total_files = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.pdf')])
    print(f"Total PDFs: {total_files}", flush=True)
