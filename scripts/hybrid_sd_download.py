#!/usr/bin/env python3
"""
Hybrid SD PDF downloader — two-phase for maximum coverage.

Phase 1 (direct /pdfft):
  - Quick check for PDF redirect (15s timeout)
  - Works for ~30% of papers that redirect to pdf.sciencedirectassets.com

Phase 2 (article page extraction):
  - Opens the article page, extracts the full ?md5=&pid= URL from "View PDF" link
  - Navigates to the full URL with Fetch interception
  - Works for papers that require session-bound md5 token

Usage:
  # Download remaining papers (auto-skips already-downloaded)
  python3 scripts/hybrid_sd_download.py --output-dir paper-temp/ --pii-map sd_pii_map.json

  # Single browser
  python3 scripts/hybrid_sd_download.py --port 9223

  # Run on both Chrome and Edge in parallel (split remaining papers in half)
  # Terminal 1:
  python3 scripts/hybrid_sd_download.py --port 9223 --output-dir paper-temp/ --pii-map sd_pii_map.json
  # Terminal 2 (modifies different output dir or same with --start-offset):
  python3 scripts/hybrid_sd_download.py --port 9225 --output-dir paper-temp/ --pii-map sd_pii_map.json
"""
import sys, json, urllib.request, websocket, time, base64, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from cdp_utils import get_cdp_ws_url, list_tabs, close_tab, send_cmd_and_wait, check_cdp

PDF_HOST = "https://pdf.sciencedirectassets.com"
FETCH_PATTERN = "*pdf.sciencedirectassets.com*main.pdf*"

def log(msg):
    print(msg, flush=True)

def capture_fetch_pdf(pws, timeout=20):
    """Listen for Fetch.requestPaused and capture PDF bytes."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            pws.settimeout(0.5)
            msg = json.loads(pws.recv())
        except:
            continue
        if msg.get("method") == "Fetch.requestPaused":
            rid = msg["params"]["requestId"]
            req_url = msg["params"].get("request", {}).get("url", "")
            if "main.pdf" in req_url or PDF_HOST in req_url:
                pws.send(json.dumps({"id": 100, "method": "Fetch.getResponseBody",
                                     "params": {"requestId": rid}}))
                try:
                    pws.settimeout(5)
                    resp = json.loads(pws.recv())
                    body = resp.get("result", {}).get("body", "")
                    b64 = resp.get("result", {}).get("base64Encoded", False)
                    if body:
                        d = base64.b64decode(body) if b64 else body.encode("latin-1", errors="ignore")
                        if d[:4] == b"%PDF" and len(d) > 20000:
                            pws.send(json.dumps({"id": 3, "method": "Fetch.continueRequest",
                                                 "params": {"requestId": rid}}))
                            return d
                except:
                    pass
            pws.send(json.dumps({"id": 3, "method": "Fetch.continueRequest",
                                 "params": {"requestId": rid}}))
    return None

def phase1_direct(port, pii):
    """Phase 1: navigate to /pdfft, capture via Fetch (15s timeout)."""
    pdfft = f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft"
    wu = get_cdp_ws_url(port)
    ws = websocket.create_connection(wu, timeout=10)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": "about:blank"}}))
    tid = json.loads(ws.recv())["result"]["targetId"]
    ws.close()
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read())
    tws = next((t.get("webSocketDebuggerUrl") for t in tabs if t.get("id") == tid), None)
    if not tws:
        return None
    pws = websocket.create_connection(tws, timeout=10)
    send_cmd_and_wait(pws, "Page.enable")
    send_cmd_and_wait(pws, "Fetch.enable", {"patterns": [{"urlPattern": FETCH_PATTERN, "requestStage": "Response"}]})
    pws.send(json.dumps({"id": 2, "method": "Page.navigate", "params": {"url": pdfft}}))
    pdf = capture_fetch_pdf(pws, timeout=15)
    pws.close()
    close_tab(port, tid)
    return pdf

def phase2_article(port, pii):
    """Phase 2: open article page, extract full ?md5= URL, download."""
    art_url = f"https://www.sciencedirect.com/science/article/pii/{pii}"
    wu = get_cdp_ws_url(port)
    ws = websocket.create_connection(wu, timeout=10)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": art_url}}))
    tid = json.loads(ws.recv())["result"]["targetId"]
    ws.close()
    time.sleep(10)  # wait for JS rendering
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read())
    tws = next((t.get("webSocketDebuggerUrl") for t in tabs if t.get("id") == tid), None)
    if not tws:
        close_tab(port, tid)
        return None
    pws = websocket.create_connection(tws, timeout=10)
    # Extract the full PDF URL from View PDF link
    pws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
(function(){var l=document.querySelectorAll('a');for(var i=0;i<l.length;i++){var h=l[i].href||'';if(h.indexOf('pdfft')>-1&&h.indexOf('md5=')>-1)return h}return ''})()
"""}}))
    r = json.loads(pws.recv())
    full_url = r.get("result", {}).get("result", {}).get("value", "")
    if not full_url:
        pws.close()
        close_tab(port, tid)
        return None
    # Enable Fetch and navigate to the full URL
    send_cmd_and_wait(pws, "Fetch.enable", {"patterns": [{"urlPattern": FETCH_PATTERN, "requestStage": "Response"}]})
    pws.send(json.dumps({"id": 2, "method": "Page.navigate", "params": {"url": full_url}}))
    pdf = capture_fetch_pdf(pws, timeout=20)
    pws.close()
    close_tab(port, tid)
    return pdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hybrid SD PDF downloader (two-phase)")
    parser.add_argument("--output-dir", "-o", default="download/paper-temp")
    parser.add_argument("--pii-map", "-p", default="./sd_pii_map.json")
    parser.add_argument("--port", type=int, default=9223)
    parser.add_argument("--start-offset", type=int, default=0,
                        help="Skip first N remaining papers (for dual-browser split)")
    args = parser.parse_args()
    if not check_cdp(args.port):
        log(f"❌ CDP not running on port {args.port}")
        exit(1)
    with open(args.pii_map) as f:
        data = json.load(f)
    done = set(f[:-4] for f in os.listdir(args.output_dir) if f.startswith("paper_") and f.endswith(".pdf"))
    remaining = [(k, v["doi"], v["pii"]) for k, v in data["resolved"].items() if k not in done]
    remaining = remaining[args.start_offset:]
    log(f"Remaining: {len(remaining)} (offset {args.start_offset})")
    ok = 0
    for i, (key, doi, pii) in enumerate(remaining, 1):
        t0 = time.time()
        pdf = phase1_direct(args.port, pii)
        if not pdf:
            pdf = phase2_article(args.port, pii)
        et = time.time() - t0
        if pdf:
            with open(os.path.join(args.output_dir, f"{key}.pdf"), "wb") as f:
                f.write(pdf)
            ok += 1
            log(f"[{i}/{len(remaining)}] ✅ {key}: {len(pdf)//1024}KB ({et:.0f}s)")
        else:
            log(f"[{i}/{len(remaining)}] ❌ {key} ({et:.0f}s)")
    log(f"\nDone: {ok} / {len(remaining)}")
