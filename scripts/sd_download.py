#!/usr/bin/env python3
"""
Hybrid SD download core — shared by parallel_sd_download.py and auto_sd_downloader.py.

Two strategies, tried in order:
  A (fast): Navigate /pdfft → wait for PDF tab → capture via Fetch (10s)
  B (fallback): Navigate article page → extract ?md5= URL → navigate → wait for PDF tab → capture (25s)

Design principle: all papers are accessible; failure means need a better strategy.
"""
import json, time, base64, os, urllib.request, websocket

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in __import__("sys").path:
    __import__("sys").path.insert(0, _SCRIPT_DIR)

from cdp_utils import get_cdp_ws_url, list_tabs, close_tab, send_cmd_and_wait, check_cdp

SD_PDF_HOST = "https://pdf.sciencedirectassets.com"
FETCH_PATTERN = "*pdf.sciencedirectassets.com*main.pdf*"

# ── Helpers ───────────────────────────────────────────


def _create_tab(port, url):
    """Create a tab, return tab ID."""
    wu = get_cdp_ws_url(port)
    ws = websocket.create_connection(wu, timeout=10)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                        "params": {"url": url}}))
    tid = json.loads(ws.recv())["result"]["targetId"]
    ws.close()
    return tid


def _wait_for_pdf_tab(port, timeout=10):
    """Wait for any tab with PDF host URL. Returns the tab dict or None."""
    for _ in range(timeout):
        time.sleep(1)
        try:
            for t in list_tabs(port):
                if SD_PDF_HOST in t.get("url", ""):
                    return t
        except Exception:
            break
    return None


def _capture_from_tab(tab_ws_url, port, timeout=20):
    """Connect to a PDF tab, reload with Fetch, capture PDF bytes."""
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


def _navigate_and_capture(port, url, redirect_timeout=10, capture_timeout=20):
    """Create a tab, navigate to URL, wait for PDF tab, capture.

    Returns PDF bytes or None.
    """
    tid = _create_tab(port, url)
    if not tid:
        return None

    pdf = None
    pdf_tid = None  # track the PDF tab to close it after capture
    try:
        pdf_tab = _wait_for_pdf_tab(port, timeout=redirect_timeout)
        if pdf_tab:
            pdf_tid = pdf_tab["id"]
            pdf = _capture_from_tab(pdf_tab["webSocketDebuggerUrl"], port, timeout=capture_timeout)
    except Exception:
        pass

    close_tab(port, tid)       # close the navigation tab
    if pdf_tid:
        close_tab(port, pdf_tid)  # close the PDF tab (prevents re-capture on next paper)
    return pdf


# ── Strategy A: direct /pdfft ─────────────────────────


def _strategy_a(port, pii, timeout=10):
    """Navigate to /pdfft, wait for PDF redirect tab, capture.

    Works for ~30% of SD papers that redirect to pdf.sciencedirectassets.com.
    """
    pdfft = f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft"
    return _navigate_and_capture(port, pdfft, redirect_timeout=timeout, capture_timeout=15)


# ── Strategy B: article page → ?md5= URL ─────────────


def _extract_pdfft_url(port, pii, render_timeout=12):
    """Navigate to article page, wait for JS render, extract View PDF link with ?md5=.

    Returns the full pdfft URL with ?md5= and &pid= parameters, or None.
    """
    art_url = f"https://www.sciencedirect.com/science/article/pii/{pii}"
    tid = _create_tab(port, art_url)
    if not tid:
        return None

    full_url = None
    try:
        # Wait for JS rendering
        time.sleep(render_timeout)

        # Find tab WS URL
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


def _strategy_b(port, pii, timeout=25):
    """Open article page, extract ?md5= URL, navigate, wait for PDF tab, capture.

    Works for ~70% of SD papers served via the online PDF viewer.
    """
    # Extract the full pdfft URL from the article page
    full_url = _extract_pdfft_url(port, pii, render_timeout=25)
    if not full_url:
        return None

    # Navigate to the full URL and capture
    return _navigate_and_capture(port, full_url, redirect_timeout=timeout, capture_timeout=20)


# ── Public API ────────────────────────────────────────


def download_one(port, pii, timeout_a=8, timeout_b=20):
    """Try both strategies to download a single SD paper.

    Args:
        port: CDP debugging port.
        pii: ScienceDirect PII identifier.
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
