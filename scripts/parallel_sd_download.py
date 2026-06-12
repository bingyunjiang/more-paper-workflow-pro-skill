#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
ScienceDirect PDF download via CDP — auto-detects Chrome and/or Edge.

If both browsers are running with CDP, splits the paper list in half
for parallel download. Gracefully degrades to single-browser mode.

Hybrid download strategy:
  A (fast): /pdfft direct redirect → capture (8s)
  B (fallback): article page → extract ?md5= URL → capture (20s)

Usage:
  1. Start Chrome (and optionally Edge) with CDP and login to ScienceDirect
  2. python3 scripts/parallel_sd_download.py
  3. Script auto-detects which browsers are available

Design principle: all papers are accessible; failure means need a better strategy.
"""
import json, time, os, sys, threading, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdp_utils import check_cdp, check_sd_access, check_required_deps
from sd_download import download_sd_pii

log_lock = threading.Lock()


def worker(name, port, papers, output_dir):
    """Process a list of papers on one browser."""
    ok, fail = 0, 0
    for i, (key, doi, pii) in enumerate(papers, 1):
        t0 = time.time()
        data = download_sd_pii(port, pii)
        et = time.time() - t0

        if data and len(data) > 20000:
            fpath = os.path.join(output_dir, f"{key}.pdf")
            with open(fpath, "wb") as f:
                f.write(data)
            ok += 1
            with log_lock:
                print(f"[{name}] ✅ {key}: {len(data)//1024}KB ({et:.0f}s) [{i}/{len(papers)}]", flush=True)
        else:
            fail += 1
            with log_lock:
                print(f"[{name}] ❌ {key} ({et:.0f}s) [{i}/{len(papers)}]", flush=True)

    return ok, fail


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ScienceDirect PDF download — hybrid strategy (direct + article page extraction)")
    parser.add_argument("--output-dir", "-o", default="download/paper-temp",
                        help="PDF output directory (default: download/paper-temp)")
    parser.add_argument("--pii-map", "-p", default="./sd_pii_map.json",
                        help="DOI→PII mapping JSON (default: ./sd_pii_map.json)")
    parser.add_argument("--port-chrome", type=int, default=9223,
                        help="Chrome CDP port (default: 9223)")
    parser.add_argument("--port-edge", type=int, default=9225,
                        help="Edge CDP port (default: 9225)")
    parser.add_argument("--timeout-a", type=int, default=8,
                        help="Seconds for Strategy A — direct /pdfft (default: 8)")
    parser.add_argument("--timeout-b", type=int, default=20,
                        help="Seconds for Strategy B — article page extraction (default: 20)")
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

    # ---- Detect available browsers ----
    workers = []
    for name, port in [("Chrome", args.port_chrome), ("Edge", args.port_edge)]:
        if not check_cdp(port):
            continue
        status, reason = check_sd_access(port, timeout=8)
        if status == "ok":
            workers.append((name, port))
            print(f"✅ {name} (:{port}) — SD 已登录", flush=True)
        else:
            print(f"⚠ {name} (:{port}) — {reason}", flush=True)

    if not workers:
        print("❌ 未检测到可用的 CDP 浏览器。请先启动 Chrome/Edge 并登录 ScienceDirect。", flush=True)
        exit(1)

    # ---- Load paper list ----
    with open(PII_MAP) as f:
        data = json.load(f)

    pii_list = [(k, v["doi"], v["pii"]) for k, v in data["resolved"].items()]
    done = set(f[:-4] for f in os.listdir(OUTPUT_DIR) if f.startswith("paper_") and f.endswith(".pdf"))
    remaining = [p for p in pii_list if p[0] not in done]

    if not remaining:
        print(f"🎉 全部完成！已有 {len(done)} 篇 PDF", flush=True)
        exit(0)

    total = len(remaining)
    print(f"\n待下载: {total} 篇 | 已有: {len(done)}/94", flush=True)

    # ---- Split across browsers ----
    if len(workers) == 2:
        half = total // 2
        assignments = [
            (workers[0], remaining[:half]),
            (workers[1], remaining[half:]),
        ]
        print(f"双浏览器并行: {workers[0][0]}={len(remaining[:half])} 篇, {workers[1][0]}={len(remaining[half:])} 篇", flush=True)
    else:
        assignments = [(workers[0], remaining)]
        print(f"单浏览器模式: {remaining} 篇 → {workers[0][0]}", flush=True)

    print(f"混合策略: A(直连/{args.timeout_a}s) → B(文章页提取/{args.timeout_b}s)", flush=True)
    print()

    # ---- Download ----
    threads = []
    for (name, port), papers in assignments:
        t = threading.Thread(target=worker, args=(name, port, papers, OUTPUT_DIR))
        threads.append(t)

    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    elapsed = (time.time() - t0) / 60
    print(f"\n完成: {elapsed:.1f} min", flush=True)

    total_pdfs = len([f for f in os.listdir(OUTPUT_DIR) if f.startswith("paper_") and f.endswith(".pdf")])
    print(f"paper_* PDFs: {total_pdfs}/94", flush=True)
