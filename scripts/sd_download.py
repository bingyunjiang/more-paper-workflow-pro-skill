#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
SD PDF downloader — two-strategy hybrid with library API + CLI batch mode.

Two strategies, tried in order:
  A (fast): Navigate /pdfft → wait for PDF tab → capture via Fetch (~10s)
  B (fallback): Article page → extract ?md5= URL → navigate → wait for PDF tab → capture (~25s)

Design principle: all papers are accessible; failure means need a better strategy.

Library mode (imported by parallel_sd_downloader.py, auto_sd_downloader.py):
    from sd_download import download_sd_pii
    pdf_bytes = download_sd_pii(port, pii)

CLI mode:
    # Batch download from PII map JSON
    python3 scripts/sd_download.py --pii-map sd_pii_map.json
    python3 scripts/sd_download.py --port 9225 --pii-map sd_pii_map.json --start-offset 5

    # Single paper download
    python3 scripts/sd_download.py --port 9223 --pii S0022519326000012
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import websocket

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from cdp_utils import check_cdp, close_tab, get_cdp_ws_url, list_tabs, send_cmd_and_wait
from console_compat import configure_console_output

SD_PDF_HOST = "https://pdf.sciencedirectassets.com"
FETCH_PATTERN = "*pdf.sciencedirectassets.com*main.pdf*"
REFERENCEWORK_PATH_FRAGMENT = "/science/chapter/referencework/abs/pii/"


def _log(msg: str) -> None:
    """Flushed print for CLI progress output."""
    print(msg, flush=True)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_tab(port: int, url: str) -> str | None:
    """Create a new CDP tab navigating to *url*. Returns tab ID or None."""
    wu = get_cdp_ws_url(port)
    if not wu:
        return None
    ws = websocket.create_connection(wu, timeout=10)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                        "params": {"url": url}}))
    tid = json.loads(ws.recv())["result"]["targetId"]
    ws.close()
    return tid


def _wait_for_pdf_tab(port: int, timeout: int = 10) -> dict | None:
    """Wait for any tab whose URL contains the SD PDF host. Returns tab dict or None."""
    for _ in range(timeout):
        time.sleep(1)
        try:
            for t in list_tabs(port):
                if SD_PDF_HOST in t.get("url", ""):
                    return t
        except Exception:
            break
    return None


def _inspect_sd_tab_state(port: int, target_id: str) -> dict:
    """Inspect the current SD tab and classify common blockers."""
    try:
        for t in list_tabs(port):
            if t.get("id") != target_id:
                continue
            url = t.get("url", "") or ""
            title = t.get("title", "") or ""
            lower_url = url.lower()
            lower_title = title.lower()
            if REFERENCEWORK_PATH_FRAGMENT in lower_url:
                return {
                    "kind": "referencework_abs",
                    "url": url,
                    "title": title,
                    "reason": "referencework chapter redirected to abstract page",
                }
            if "are you a robot" in lower_title or "请稍候" in title or "challenge" in lower_url:
                return {
                    "kind": "manual_verification_required",
                    "url": url,
                    "title": title,
                    "reason": "article page still behind anti-bot verification",
                }
            if "/article/pii/" in lower_url and "pdfft" not in lower_url:
                return {
                    "kind": "article_page_only",
                    "url": url,
                    "title": title,
                    "reason": "article page opened but no PDF route became available",
                }
            return {"kind": "ok", "url": url, "title": title, "reason": ""}
    except Exception:
        pass
    return {"kind": "unknown", "url": "", "title": "", "reason": ""}


def _capture_from_tab(tab_ws_url: str, port: int, timeout: int = 20) -> bytes | None:
    """Connect to a PDF tab, reload with Fetch interception, capture PDF bytes."""
    pdf_data = None
    try:
        pws = websocket.create_connection(tab_ws_url, timeout=10)
        send_cmd_and_wait(pws, "Page.enable")
        send_cmd_and_wait(pws, "Fetch.enable", {
            "patterns": [{"urlPattern": FETCH_PATTERN, "requestStage": "Response"}]
        })
        # Reload to trigger the PDF request again
        pws.send(json.dumps({"id": 2, "method": "Page.reload"}))

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                pws.settimeout(0.5)
                msg = json.loads(pws.recv())
            except Exception:
                continue

            if msg.get("method") == "Fetch.requestPaused":
                rid = msg["params"]["requestId"]
                req_url = msg["params"].get("request", {}).get("url", "")

                if "main.pdf" in req_url or SD_PDF_HOST in req_url:
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
                                pdf_data = d
                    except Exception:
                        pass

                pws.send(json.dumps({"id": 3, "method": "Fetch.continueRequest",
                                     "params": {"requestId": rid}}))
                if pdf_data:
                    break
        pws.close()
    except Exception:
        pass

    return pdf_data


def _navigate_and_capture(port: int, url: str, redirect_timeout: int = 10,
                          capture_timeout: int = 20) -> bytes | None:
    """Create tab → navigate to URL → wait for PDF redirect tab → capture.

    Returns PDF bytes, or None on failure.
    """
    tid = _create_tab(port, url)
    if not tid:
        return None

    pdf = None
    pdf_tid = None
    try:
        pdf_tab = _wait_for_pdf_tab(port, timeout=redirect_timeout)
        if pdf_tab:
            pdf_tid = pdf_tab["id"]
            pdf = _capture_from_tab(pdf_tab["webSocketDebuggerUrl"], port, timeout=capture_timeout)
    except Exception:
        pass

    close_tab(port, tid)        # navigation tab
    if pdf_tid:
        close_tab(port, pdf_tid)  # PDF tab (prevents cross-paper interference)
    return pdf


# ── Strategy A: direct /pdfft ────────────────────────────────────────────────


def _strategy_a(port: int, pii: str, timeout: int = 10) -> bytes | None:
    """Navigate to /pdfft, wait for PDF redirect tab, capture.

    Works for ~30% of SD papers that redirect to pdf.sciencedirectassets.com.
    """
    pdfft = f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft"
    return _navigate_and_capture(port, pdfft, redirect_timeout=timeout, capture_timeout=15)


# ── Strategy B: article page → ?md5= URL ────────────────────────────────────


def _extract_pdfft_url(port: int, pii: str, render_timeout: int = 12) -> str | None:
    """Navigate to article page, wait for JS render, extract View PDF link with ?md5=.

    Returns the full pdfft URL with ?md5= and &pid= parameters, or None.
    """
    art_url = f"https://www.sciencedirect.com/science/article/pii/{pii}"
    tid = _create_tab(port, art_url)
    if not tid:
        return None

    full_url = None
    try:
        time.sleep(render_timeout)
        state = _inspect_sd_tab_state(port, tid)
        if state["kind"] in ("referencework_abs", "manual_verification_required"):
            return None

        tws = None
        for t in list_tabs(port):
            if t.get("id") == tid:
                tws = t.get("webSocketDebuggerUrl")
                break

        if tws:
            pws = websocket.create_connection(tws, timeout=10)
            pws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                                 "params": {"expression": """
(function(){
  var links=document.querySelectorAll('a');
  for(var i=0;i<links.length;i++){
    var h=links[i].href||'';
    if(h.indexOf('pdfft')>-1&&h.indexOf('md5=')>-1){
      return h;
    }
  }
  return '';
})()
"""}}))
            r = json.loads(pws.recv())
            pws.close()
            val = r.get("result", {}).get("result", {}).get("value", "")
            if val:
                full_url = val
    except Exception:
        pass

    close_tab(port, tid)
    return full_url


def _strategy_b(port: int, pii: str, timeout: int = 25) -> bytes | None:
    """Open article page, extract ?md5= URL, navigate, wait for PDF tab, capture.

    Works for ~70% of SD papers served via the online PDF viewer.
    """
    full_url = _extract_pdfft_url(port, pii, render_timeout=25)
    if not full_url:
        return None

    return _navigate_and_capture(port, full_url, redirect_timeout=timeout, capture_timeout=20)


def diagnose_sd_pii(port: int, pii: str, render_timeout: int = 12) -> dict:
    """Diagnose why a specific SD PII is not downloading."""
    art_url = f"https://www.sciencedirect.com/science/article/pii/{pii}"
    tid = _create_tab(port, art_url)
    if not tid:
        return {"kind": "unknown", "reason": "failed to create article tab", "url": "", "title": ""}
    try:
        time.sleep(render_timeout)
        return _inspect_sd_tab_state(port, tid)
    finally:
        close_tab(port, tid)


# ── Public API ───────────────────────────────────────────────────────────────


def download_sd_pii(port: int, pii: str, timeout_a: int = 8,
                    timeout_b: int = 20) -> bytes | None:
    """Try both strategies to download a single SD paper by PII.

    Args:
        port: CDP debugging port.
        pii: ScienceDirect PII identifier (e.g. "S0022519326000012").
        timeout_a: Seconds for Strategy A — direct /pdfft (default 8).
        timeout_b: Seconds for Strategy B — article page extraction (default 20,
                   not counting the 12s JS render wait).

    Returns:
        Raw PDF bytes, or None if both strategies fail.
    """
    if not check_cdp(port):
        return None

    # Clean up stale PDF tabs from previous downloads that might interfere
    try:
        for t in list_tabs(port):
            if "pdf.sciencedirectassets.com" in t.get("url", ""):
                close_tab(port, t["id"])
    except Exception:
        pass

    # Strategy A — fast path (direct /pdfft redirect)
    pdf = _strategy_a(port, pii, timeout=timeout_a)
    if pdf:
        return pdf

    # Strategy B — article page → ?md5= URL
    pdf = _strategy_b(port, pii, timeout=timeout_b)
    return pdf


# ── CLI batch mode ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    configure_console_output()

    parser = argparse.ArgumentParser(
        description="SD PDF downloader — two-strategy hybrid (library + CLI)")
    parser.add_argument("--output-dir", "-o", default="download/paper-temp")
    parser.add_argument("--pii-map", "-p",
                        help="JSON file mapping paper keys → {{doi, pii}} (batch mode)")
    parser.add_argument("--pii",
                        help="Single PII to download (quick mode)")
    parser.add_argument("--port", type=int, default=9223)
    parser.add_argument("--start-offset", type=int, default=0,
                        help="Skip first N remaining papers (for dual-browser split)")
    args = parser.parse_args()

    if not check_cdp(args.port):
        _log(f"❌ CDP not running on port {args.port}")
        sys.exit(1)

    # ── Single PII mode ──
    if args.pii:
        _log(f"Downloading PII: {args.pii}")
        t0 = time.time()
        pdf = download_sd_pii(args.port, args.pii)
        et = time.time() - t0
        if pdf:
            out_path = os.path.join(args.output_dir, f"{args.pii}.pdf")
            os.makedirs(args.output_dir, exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(pdf)
            _log(f"✅ {args.pii}: {len(pdf)//1024}KB ({et:.0f}s) → {out_path}")
        else:
            _log(f"❌ {args.pii} ({et:.0f}s)")
        sys.exit(0)

    # ── Batch mode (PII map) ──
    if not args.pii_map:
        parser.error("Either --pii or --pii-map is required")

    if not os.path.exists(args.pii_map):
        _log(f"❌ PII map not found: {args.pii_map}")
        sys.exit(1)

    with open(args.pii_map, encoding="utf-8") as f:
        data = json.load(f)

    # Determine already-downloaded papers
    os.makedirs(args.output_dir, exist_ok=True)
    done = set(
        f[:-4] for f in os.listdir(args.output_dir)
        if f.endswith(".pdf")
    )

    # Build remaining list: (key, doi, pii)
    remaining = [
        (k, v["doi"], v["pii"])
        for k, v in data.get("resolved", {}).items()
        if k not in done
    ]
    remaining = remaining[args.start_offset:]

    _log(f"Remaining: {len(remaining)} (offset {args.start_offset})")

    ok = 0
    for i, (key, doi, pii) in enumerate(remaining, 1):
        t0 = time.time()
        pdf = download_sd_pii(args.port, pii)
        et = time.time() - t0
        if pdf:
            out_path = os.path.join(args.output_dir, f"{key}.pdf")
            with open(out_path, "wb") as f:
                f.write(pdf)
            ok += 1
            _log(f"[{i}/{len(remaining)}] ✅ {key}: {len(pdf)//1024}KB ({et:.0f}s)")
        else:
            _log(f"[{i}/{len(remaining)}] ❌ {key} ({et:.0f}s)")

    _log(f"\nDone: {ok} / {len(remaining)}")
