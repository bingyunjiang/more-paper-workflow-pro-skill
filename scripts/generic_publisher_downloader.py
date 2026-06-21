#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Generic publisher PDF downloader via CDP (Chrome DevTools Protocol).

Translates ref-downloader's per-publisher strategies into CDP websocket operations.
No Playwright dependency — uses the same websocket approach as the rest of the project.

Strategy order (tried sequentially for each paper):
  A: Direct PDF URL template   — fastest, no article page visit needed
  B: Article page extraction    — navigate, CSS selector extract, capture
  C: Direct HTTP download       — for OA journals (Frontiers, OA Nature)

Usage (as module):
  from generic_publisher_downloader import download_one, resolve_publisher

  publisher = resolve_publisher("10.1021/acsnano.4c00001")
  path, status, pub_name = download_one(9223, "10.1021/acsnano.4c00001", "paper-temp/")

Usage (as CLI):
  python3 scripts/generic_publisher_downloader.py dois.txt --port 9223 --output paper-temp/
  python3 scripts/generic_publisher_downloader.py --test 10.1021/acsnano.4c00001 --port 9223 --verbose
"""

from __future__ import annotations

import sys, os, json, time, re, base64, urllib.request, urllib.error, tomllib, argparse
from pathlib import Path
from typing import Optional

# Ensure scripts/ is on path for cdp_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdp_utils import (
    check_cdp, get_cdp_ws_url, list_tabs, close_tab, create_tab,
    get_tab_ws_url, send_cmd_and_wait, check_required_deps,
)
from console_compat import configure_console_output

configure_console_output()

# Lazy import for websocket (dependency checked at CLI entry)
try:
    import websocket
except ImportError:
    websocket = None  # type: ignore

# ── Config ──────────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "config" / "publishers.toml"
PDF_MAGIC = b"%PDF"
MIN_PDF_SIZE = 5000
DEFAULT_TIMEOUT = 25
LARGE_PDF_TIMEOUT = 30
ARTICLE_RENDER_WAIT = 8  # seconds for SPA page render
LOADING_PAGE_TIMEOUT = 30  # seconds for AIP/AVS "请稍候" loading page
HTTP_DOWNLOAD_TIMEOUT = 30  # seconds for direct HTTP download

# ── Config Loading ──────────────────────────────────────────────────────────

_ROUTING_TABLE: list[tuple[int, str, dict]] = []  # (prefix_len, prefix, config)
_PUBLISHER_CONFIGS: dict[str, dict] = {}
_BARRIERS: dict = {}

def _load_config():
    """Load publishers.toml and build in-memory routing table. Called at import."""
    global _ROUTING_TABLE, _PUBLISHER_CONFIGS, _BARRIERS
    if not CONFIG_PATH.exists():
        print(f"WARNING: {CONFIG_PATH} not found — generic downloader disabled.",
              file=sys.stderr)
        return

    with open(CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)

    for key, cfg in data.get("publishers", {}).items():
        _PUBLISHER_CONFIGS[key] = cfg
        for prefix in cfg.get("doi_prefixes", []):
            _ROUTING_TABLE.append((len(prefix), prefix, key, cfg))

    _ROUTING_TABLE.sort(key=lambda x: -x[0])  # longest prefix first

    _BARRIERS = data.get("barriers", {})

_load_config()

# ── Public API ──────────────────────────────────────────────────────────────

def resolve_publisher(doi: str) -> dict | None:
    """Map a DOI to its publisher config dict. Returns None if unknown."""
    doi_clean = doi.strip().lower()
    for _, prefix, key, config in _ROUTING_TABLE:
        if doi_clean.startswith(prefix.lower()):
            config["_key"] = key
            return config
    return None


def download_one(port: int, doi: str, output_dir: str = "paper-temp",
                 include_si: bool = False,
                 timeout: int = DEFAULT_TIMEOUT,
                 article_url: str = "") -> tuple[Optional[str], str, str]:
    """Download one paper via generic CDP strategies.

    Args:
        port: CDP Chrome debug port.
        doi: DOI string (or synthetic identifier for Chinese papers).
        output_dir: Directory to save downloaded PDF.
        include_si: If True, attempt supplementary info download.
        timeout: Max seconds per download attempt.
        article_url: Direct article page URL override.
                     Required for chinese_cdp strategy (CNKI/Wanfang
                     papers lack standard DOI→URL mapping).

    Returns: (pdf_path_or_None, status, publisher_name)
      status: "ok" | "failed" | "skipped" | "manual_required" | "no_url"
    """
    publisher = resolve_publisher(doi)
    pub_name = publisher.get("_key", "unknown") if publisher else "unknown"

    if publisher is None:
        # Check if article_url identifies a Chinese publisher without DOI match
        if article_url and "wanfangdata.com.cn" in article_url:
            publisher = {"strategy": "chinese_cdp", "_key": "wanfang"}
            pub_name = "wanfang"
        elif article_url and "cnki.net" in article_url:
            publisher = {"strategy": "chinese_cdp", "_key": "cnki"}
            pub_name = "cnki"
        else:
            publisher = {"strategy": "generic", "_key": "unknown"}

    strategy = publisher.get("strategy", "generic")

    # Route by strategy
    if strategy == "skip":
        return None, "skipped", pub_name

    if strategy == "direct_http":
        return _strategy_direct_http(doi, publisher, output_dir), \
               ("ok" if _strategy_direct_http(doi, publisher, output_dir) else "failed"), \
               pub_name

    if strategy in ("sd_cdp", "ieee_cdp", "scihub_only"):
        return None, "delegated", pub_name  # handled by router, not us

    # Chinese CDP: navigate directly to article detail page (no DOI→URL mapping)
    if strategy == "chinese_cdp":
        if not article_url:
            return None, "no_url", pub_name
        dest = _doi_to_filename(doi, output_dir)

        # Identify Chinese publisher from article_url if not matched by DOI
        if "wanfangdata.com.cn" in article_url:
            pub_name = "wanfang"
        elif "cnki.net" in article_url:
            pub_name = "cnki"

        # Wanfang: download directly to output_dir, returns path (no _save_pdf)
        if pub_name == "wanfang":
            pdf_path = _download_wanfang(port, article_url, publisher, timeout,
                                         output_dir=output_dir)
            if pdf_path:
                return pdf_path, "ok", pub_name
            return None, "failed", pub_name
        # CNKI: click-based download (requires Referrer from article page)
        elif pub_name == "cnki":
            pdf_path = _download_cnki(port, article_url, publisher, timeout,
                                      output_dir=output_dir)
            if pdf_path:
                return pdf_path, "ok", pub_name
            return None, "failed", pub_name
        else:
            pdf_data = _strategy_article_page(port, doi, publisher, timeout,
                                              article_url_override=article_url)
        if pdf_data:
            return _save_pdf(pdf_data, dest), "ok", pub_name
        return None, "failed", pub_name

    if pub_name == "sd_elsevier":
        pdf_path, status = _download_sciencedirect(port, doi, output_dir)
        return pdf_path, status, pub_name

    # Generic strategy: A → B fallback
    dest = _doi_to_filename(doi, output_dir)

    # Strategy A: Direct PDF URL
    pdf_data = _strategy_direct_pdf(port, doi, publisher, timeout)
    if pdf_data:
        return _save_pdf(pdf_data, dest), "ok", pub_name

    # Strategy B: Article page extraction
    pdf_data = _strategy_article_page(port, doi, publisher, timeout)
    if pdf_data == "MANUAL_REQUIRED":
        return None, "manual_required", pub_name
    if pdf_data:
        return _save_pdf(pdf_data, dest), "ok", pub_name

    # SI download (if requested and PDF failed)
    if include_si:
        si_paths = download_si(port, doi, publisher, output_dir)
        if si_paths:
            return None, "si_only", pub_name

    return None, "failed", pub_name


def _download_sciencedirect(port: int, doi: str, output_dir: str) -> tuple[Optional[str], str]:
    """ScienceDirect adapter used by the Generic CDP route."""
    try:
        from batch_resolve_pii import _resolve_pii_from_crossref
        from sd_download import diagnose_sd_pii, download_sd_pii
    except Exception:
        return None, "failed"

    pii = _resolve_pii_from_crossref(doi)
    if not pii:
        return None, "pii_resolution_failed"

    data = download_sd_pii(port, pii)
    if data and len(data) > 20000:
        return _save_pdf(data, _doi_to_filename(doi, output_dir)), "ok"

    diag = diagnose_sd_pii(port, pii)
    kind = diag.get("kind")
    if kind == "manual_verification_required":
        return None, "manual_required"
    if kind == "referencework_abs":
        return None, "not_subscribed_or_referencework"
    if kind == "article_page_only":
        return None, "article_page_no_pdf_route"
    return None, "failed"


def download_si(port: int, doi: str, publisher: dict,
                output_dir: str = "paper-temp") -> list[str]:
    """Download supplementary information for a paper. Returns list of file paths."""
    si_selectors = publisher.get("si_selectors", [])
    if not si_selectors:
        return []

    # Navigate to article page and extract SI links
    article_url = _build_article_url(doi)
    if not article_url:
        return []

    _, tid = create_tab(port, article_url)
    time.sleep(ARTICLE_RENDER_WAIT)

    tws_url = get_tab_ws_url(port, tid)
    if not tws_url:
        close_tab(port, tid)
        return []

    saved_paths = []
    try:
        ws = websocket.create_connection(tws_url, timeout=10)
        # Extract SI links
        selector_js = json.dumps(si_selectors)
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
            "params": {"expression": f"""
                (() => {{
                    const selectors = {selector_js};
                    const links = [];
                    for (const sel of selectors) {{
                        try {{
                            document.querySelectorAll(sel).forEach(el => {{
                                const href = el.href || el.getAttribute('href') || '';
                                if (href && !links.includes(href)) links.push(href);
                            }});
                        }} catch(e) {{}}
                    }}
                    return JSON.stringify(links);
                }})()
            """, "returnByValue": True}}))
        try:
            ws.settimeout(5)
            resp = json.loads(ws.recv())
            links_json = resp.get("result", {}).get("result", {}).get("value", "[]")
            links = json.loads(links_json) if isinstance(links_json, str) else []
        except Exception:
            links = []
        ws.close()
    except Exception:
        links = []

    close_tab(port, tid)

    # Download each SI file via direct HTTP
    for i, link in enumerate(links):
        try:
            ext = _guess_si_extension(link)
            si_dest = os.path.join(output_dir, f"{_doi_basename(doi)}_SI_{i+1}.{ext}")
            req = urllib.request.Request(link, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            })
            with urllib.request.urlopen(req, timeout=HTTP_DOWNLOAD_TIMEOUT) as resp:
                data = resp.read()
                if len(data) > 100:
                    with open(si_dest, "wb") as f:
                        f.write(data)
                    saved_paths.append(si_dest)
        except Exception:
            continue

    return saved_paths


def check_publisher_session(port: int, publisher: dict) -> tuple[bool, int]:
    """Check if CDP browser has valid cookies for this publisher.
    Returns (has_session, cookie_count)."""
    domain = publisher.get("publisher_domain", "")
    if not domain:
        return False, 0

    try:
        wu = get_cdp_ws_url(port)
        ws = websocket.create_connection(wu, timeout=10)
        ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
        cookies = []
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                cookies = msg.get("result", {}).get("cookies", [])
                break
        ws.close()

        matching = [c for c in cookies if domain in c.get("domain", "")]
        return len(matching) > 0, len(matching)
    except Exception:
        return False, -1


# ── Strategy A: Direct PDF URL ──────────────────────────────────────────────

def _strategy_direct_pdf(port: int, doi: str, publisher: dict,
                         timeout: int = DEFAULT_TIMEOUT) -> Optional[bytes]:
    """Try downloading via the publisher's direct PDF URL template."""
    url = _build_pdf_url(doi, publisher)
    if not url:
        return None
    return _navigate_and_capture_pdf(port, url, timeout=timeout)


# ── Strategy B: Article Page Extraction ─────────────────────────────────────

def _strategy_article_page(port: int, doi: str, publisher: dict,
                           timeout: int = DEFAULT_TIMEOUT,
                           article_url_override: str = "") -> Optional[bytes] | str:
    """Navigate to article page, find PDF link via CSS selectors, capture PDF.

    Args:
        article_url_override: If provided, use this URL directly instead of
                              building from DOI. Used for chinese_cdp strategy
                              where papers lack standard DOI→URL mapping.
    """
    if article_url_override:
        article_url = article_url_override
    else:
        article_url = _build_article_url(doi)
        if not article_url:
            return None

    selectors = publisher.get("selectors", [])
    if not selectors:
        return None

    pub_key = publisher.get("_key", "")

    # Navigate to article page
    _, tid = create_tab(port, article_url)

    # Wait for render (longer for SPA-heavy publishers)
    wait = ARTICLE_RENDER_WAIT
    if pub_key in ("aip", "avs"):
        wait = _handle_aip_loading_page(port, tid)

    time.sleep(wait)

    # Check for access barriers (non-fatal — still try to extract PDF URL)
    barrier, barrier_detail = _detect_access_barrier(port, tid)
    if barrier:
        print(f"  ⚠ Access barrier detected: {barrier} — {barrier_detail} (continuing anyway)")

    # Extract PDF URL from DOM
    pdf_url = _extract_pdf_url_from_dom(port, tid, selectors)

    if pub_key == "wiley" and (barrier or pdf_url in (None, "NO_PDF_LINK")):
        print("  ⚠ wiley requires manual access confirmation — leaving tab open")
        print("  ↳ Open institutional access on this Wiley page, or use: "
              "https://onlinelibrary.wiley.com/action/ssostart")
        return "MANUAL_REQUIRED"

    # Keep the tab open when the site wants human login/verification so the
    # user has time to complete it in the visible CDP browser.
    if pdf_url in ("LOGIN_REQUIRED", "ACCESS_DENIED"):
        print(f"  ⚠ {pub_key or 'publisher'} requires manual access confirmation — leaving tab open")
        return "MANUAL_REQUIRED"

    # Close article tab
    close_tab(port, tid)

    if not pdf_url:
        if barrier:
            print(f"  ⚠ No PDF link found + barrier present ({barrier})")
        return None

    # Resolve relative URLs
    domain = publisher.get("publisher_domain", "")
    if domain and not pdf_url.startswith("http"):
        pdf_url = f"https://{domain}{pdf_url}" if pdf_url.startswith("/") else f"https://{domain}/{pdf_url}"

    # Publisher-specific URL transformations
    pdf_url = _transform_pdf_url(pdf_url, publisher)

    # Some publishers (IEEE) require the article page as Referrer
    referrer = ""
    if publisher.get("pdf_url_requires_referrer"):
        referrer = article_url

    # Capture the PDF
    return _navigate_and_capture_pdf(port, pdf_url, referrer=referrer, timeout=timeout)


# ── Wanfang Download ─────────────────────────────────────────────────────────

def _download_wanfang(port: int, article_url: str, publisher: dict,
                      timeout: int = DEFAULT_TIMEOUT,
                      output_dir: str = "") -> Optional[str]:
    """Download Wanfang paper to output_dir. Returns PDF path or None.

    Downloads go to output_dir (no temp dirs, no deletions).
    A duplicate copy also appears in ~/Downloads (Chrome CDP behavior).
    """
    import os as _os, glob as _glob, hashlib, shutil as _shutil

    # Download directly to output dir — don't use temp dir that gets deleted
    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="wf_")
    _os.makedirs(output_dir, exist_ok=True)
    # Record existing PDFs so we only pick up the new one
    before = set(_glob.glob(_os.path.join(output_dir, "*.pdf")))

    # Step 1: Construct download page URL from article URL
    # Thesis:  d.wanfangdata.com.cn/thesis/{id} → f.wanfangdata.com.cn/download/pc/thesis/{id}
    # Periodical: d.wanfangdata.com.cn/periodical/{id} → f.wanfangdata.com.cn/download/pc/periodical/{id}
    import re as _re
    m = _re.match(r'https?://d\.wanfangdata\.com\.cn/(thesis|periodical)/(.+)', article_url)
    if not m:
        return None
    download_url = f"https://f.wanfangdata.com.cn/download/pc/{m.group(1)}/{m.group(2)}"

    # Step 2: Create tab and navigate to download page
    browser_ws_url = get_cdp_ws_url(port)
    bws = websocket.create_connection(browser_ws_url, timeout=10)
    bws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                         "params": {"url": download_url}}))
    tid = json.loads(bws.recv())["result"]["targetId"]
    bws.close()
    time.sleep(4)

    # Get tab WS for click operation
    tab_ws_url = get_tab_ws_url(port, tid)
    if not tab_ws_url:
        return None
    tab_ws = websocket.create_connection(tab_ws_url, timeout=10)

    # Step 3: Wait for countdown, then click "点击此处"
    time.sleep(10)

    js_click = '(function(){var as=document.querySelectorAll("a");for(var i=0;i<as.length;i++){if(as[i].innerText.indexOf("点击此处")>=0){as[i].click();return"clicked";}}return"not found";})()'
    tab_ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": js_click}}))
    json.loads(tab_ws.recv())
    tab_ws.close()

    # Step 4: Wait for PDF in ~/Downloads (Browser.setDownloadBehavior path is unreliable)
    downloads_dir = _os.path.expanduser("~/Downloads")
    before_dl = set(_glob.glob(_os.path.join(downloads_dir, "*.pdf")))
    for i in range(timeout + 30):
        time.sleep(1)
        current = set(_glob.glob(_os.path.join(downloads_dir, "*.pdf")))
        new_pdfs = current - before_dl
        crdownloads = _glob.glob(_os.path.join(downloads_dir, "*.crdownload"))
        if new_pdfs and not crdownloads:
            dl_path = list(new_pdfs)[0]
            if _os.path.getsize(dl_path) > MIN_PDF_SIZE:
                # Copy to output_dir with hash name for router compatibility
                dest = _os.path.join(output_dir,
                    f"wanfang.{hashlib.md5(article_url.encode()).hexdigest()[:16]}.pdf")
                _shutil.copy2(dl_path, dest)
                close_tab(port, tid)
                return dest

    close_tab(port, tid)
    return None


# ── CNKI Download ────────────────────────────────────────────────────────────

def _download_cnki(port: int, article_url: str, publisher: dict,
                   timeout: int = DEFAULT_TIMEOUT,
                   output_dir: str = "") -> Optional[str]:
    """Download CNKI paper by clicking PDF download on article detail page.

    CNKI requires Referrer from the article page, so we must click from
    the detail page rather than navigating directly to bar.cnki.net.
    """
    import os as _os, glob as _glob, hashlib, shutil as _shutil

    # Step 1: Create tab and navigate to CNKI article detail page
    browser_ws_url = get_cdp_ws_url(port)
    bws = websocket.create_connection(browser_ws_url, timeout=10)
    bws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                         "params": {"url": article_url}}))
    tid = json.loads(bws.recv())["result"]["targetId"]
    bws.close()
    time.sleep(5)  # CNKI detail pages are heavy

    # Get tab WS for click operation
    tab_ws_url = get_tab_ws_url(port, tid)
    if not tab_ws_url:
        return None
    tab_ws = websocket.create_connection(tab_ws_url, timeout=10)

    # Step 2: Click PDF download (#pdfDown), removing target attr first
    js = '''
(function(){
  var a = document.querySelector('#pdfDown');
  if (!a) {
    // Fallback: look for any PDF download link
    var all = document.querySelectorAll('a');
    for (var i=0; i<all.length; i++) {
      if (all[i].innerText.indexOf('PDF下载')>=0) { a = all[i]; break; }
    }
  }
  if (!a) return 'no_pdfDown';
  a.removeAttribute('target');
  a.click();
  return 'clicked: ' + a.href.substring(0, 80);
})()
'''
    tab_ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                            "params": {"expression": js}}))
    click_result = json.loads(tab_ws.recv())
    result_val = click_result.get("result", {}).get("result", {}).get("value", "")
    tab_ws.close()

    if "no_pdfDown" in str(result_val):
        close_tab(port, tid)
        return None

    # Step 3: Wait for PDF in ~/Downloads
    downloads_dir = _os.path.expanduser("~/Downloads")
    before_dl = set(_glob.glob(_os.path.join(downloads_dir, "*.pdf")))
    for i in range(timeout + 15):
        time.sleep(1)
        current = set(_glob.glob(_os.path.join(downloads_dir, "*.pdf")))
        new_pdfs = current - before_dl
        crdownloads = _glob.glob(_os.path.join(downloads_dir, "*.crdownload"))
        if new_pdfs and not crdownloads:
            dl_path = list(new_pdfs)[0]
            if _os.path.getsize(dl_path) > MIN_PDF_SIZE:
                dest = _os.path.join(output_dir,
                    f"cnki.{hashlib.md5(article_url.encode()).hexdigest()[:16]}.pdf")
                _shutil.copy2(dl_path, dest)
                close_tab(port, tid)
                return dest

    close_tab(port, tid)
    return None


# ── Strategy C: Direct HTTP Download ────────────────────────────────────────

def _strategy_direct_http(doi: str, publisher: dict, output_dir: str) -> Optional[str]:
    """Download PDF via plain HTTP (for OA journals)."""
    url = _build_pdf_url(doi, publisher)
    if not url:
        return None

    dest = _doi_to_filename(doi, output_dir)
    if os.path.exists(dest) and os.path.getsize(dest) > MIN_PDF_SIZE:
        return dest

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=HTTP_DOWNLOAD_TIMEOUT) as resp:
            data = resp.read()
            if data[:4] == PDF_MAGIC and len(data) > MIN_PDF_SIZE:
                with open(dest, "wb") as f:
                    f.write(data)
                return dest
    except Exception:
        pass
    return None


# ── Core: Navigate + Fetch Capture ──────────────────────────────────────────

def _navigate_and_capture_pdf(port: int, url: str, referrer: str = "",
                              timeout: int = DEFAULT_TIMEOUT) -> Optional[bytes]:
    """Navigate to a PDF URL and capture the response via Fetch domain.

    CRITICAL (IEEE v1.0.1 insight): Fetch.enable MUST be called BEFORE
    Page.navigate from a fresh about:blank tab. If Fetch.enable comes after
    navigation, Chrome's PDF viewer consumes the response body and
    getResponseBody returns empty.
    """
    try:
        _, tid = create_tab(port, "about:blank")
    except Exception:
        return None

    time.sleep(0.5)
    tws_url = get_tab_ws_url(port, tid)
    if not tws_url:
        close_tab(port, tid)
        return None

    pdf_data = None
    ws = None
    try:
        ws = websocket.create_connection(tws_url, timeout=10)

        # CRITICAL: Fetch.enable BEFORE Page.navigate
        send_cmd_and_wait(ws, "Fetch.enable", {
            "patterns": [{"urlPattern": "*", "requestStage": "Response"}]
        })

        # Navigate to PDF URL
        nav_params: dict = {"url": url}
        if referrer:
            nav_params["referrer"] = referrer
        ws.send(json.dumps({"id": 1, "method": "Page.navigate",
                            "params": nav_params}))

        # Listen for Fetch.requestPaused events
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                ws.settimeout(2)
                msg = json.loads(ws.recv())
            except Exception:
                continue

            if msg.get("method") == "Fetch.requestPaused":
                rid = msg["params"]["requestId"]
                resp_headers = msg["params"].get("responseHeaders", [])
                ct = ""
                for h in resp_headers:
                    if h.get("name", "").lower() == "content-type":
                        ct = h.get("value", "").lower()

                rurl = msg["params"].get("request", {}).get("url", "").lower()

                # Detect PDF response
                # IEEE uses stamp/getPDF URLs that serve PDF content
                is_pdf = ("application/pdf" in ct or rurl.endswith(".pdf")
                         or "pdfdirect" in rurl or "stamp" in rurl
                         or "getpdf" in rurl)

                if is_pdf or not _is_likely_non_pdf(ct):
                    ws.send(json.dumps({"id": 100, "method": "Fetch.getResponseBody",
                                        "params": {"requestId": rid}}))
                    try:
                        ws.settimeout(LARGE_PDF_TIMEOUT)
                        resp = json.loads(ws.recv())
                        if "result" in resp:
                            body = resp["result"].get("body", "")
                            b64 = resp["result"].get("base64Encoded", False)
                            if body:
                                raw = base64.b64decode(body) if b64 else \
                                    body.encode("latin-1", errors="ignore")
                                if raw[:4] == PDF_MAGIC and len(raw) > MIN_PDF_SIZE:
                                    pdf_data = raw
                    except Exception:
                        pass

                ws.send(json.dumps({"id": 101, "method": "Fetch.continueRequest",
                                    "params": {"requestId": rid}}))

                if pdf_data:
                    break

            elif msg.get("method") == "Fetch.authRequired":
                rid = msg["params"]["requestId"]
                ws.send(json.dumps({"id": 102, "method": "Fetch.continueWithAuth",
                                    "params": {"requestId": rid}}))

    except Exception as e:
        pass
    finally:
        try:
            if ws:
                ws.close()
        except Exception:
            pass
        close_tab(port, tid)

    return pdf_data


def _is_likely_non_pdf(content_type: str) -> bool:
    """Check if content-type indicates a definitely non-PDF response."""
    ct = content_type.lower()
    non_pdf_types = ("text/html", "text/css", "text/javascript", "application/javascript",
                     "image/", "video/", "font/", "application/json")
    for t in non_pdf_types:
        if t in ct:
            return True
    return False


# ── DOM Extraction Helpers ──────────────────────────────────────────────────

def _extract_pdf_url_from_dom(port: int, tab_id: str,
                              selectors: list[str]) -> Optional[str]:
    """Extract PDF URL from the page DOM using CSS selectors and JS evaluation."""
    tws_url = get_tab_ws_url(port, tab_id)
    if not tws_url:
        return None

    result = None
    try:
        ws = websocket.create_connection(tws_url, timeout=10)
        selector_js = json.dumps(selectors)

        # Use JavaScript to find the PDF link
        js_expr = f"""
        (() => {{
            const selectors = {selector_js};

            // 1. Try CSS selectors
            for (const sel of selectors) {{
                try {{
                    const el = document.querySelector(sel);
                    if (el) {{
                        const href = el.href || el.getAttribute('href') || '';
                        if (href && href !== '#' && !href.startsWith('javascript:')) {{
                            return 'PDF_URL:' + href;
                        }}
                    }}
                }} catch(e) {{}}
            }}

            // 2. Text-based fallback: scan all links
            for (const a of document.querySelectorAll('a')) {{
                const text = (a.textContent || '').trim().toLowerCase();
                const href = a.href || a.getAttribute('href') || '';
                if (!href || href === '#' || href.startsWith('javascript:')) continue;
                if (text === 'pdf' || text === 'download pdf' || text === 'view pdf' ||
                    text === 'full text pdf' || text === 'pdf (opens in new window)') {{
                    return 'PDF_URL:' + href;
                }}
            }}

            // 3. Check for login wall
            const loginEls = document.querySelectorAll(
                'a[href*="login"], a[href*="signin"], a[href*="sso"], a[href*="wayf"]');
            if (loginEls.length > 0) return 'LOGIN_REQUIRED';

            // 4. Check for access-denied indicators
            if (document.title.includes('Access Denied') ||
                document.body.innerText.includes('access denied')) {{
                return 'ACCESS_DENIED';
            }}

            return 'NO_PDF_LINK';
        }})()
        """

        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
            "params": {"expression": js_expr, "returnByValue": True}}))
        try:
            ws.settimeout(5)
            resp = json.loads(ws.recv())
            value = resp.get("result", {}).get("result", {}).get("value", "")
            if isinstance(value, str):
                if value.startswith("PDF_URL:"):
                    result = value[len("PDF_URL:"):]
                elif value in ("LOGIN_REQUIRED", "ACCESS_DENIED", "NO_PDF_LINK"):
                    result = value
        except Exception:
            pass
        ws.close()
    except Exception:
        pass

    return result


# ── Access Barrier Detection ────────────────────────────────────────────────

def _detect_access_barrier(port: int, tab_id: str) -> tuple[Optional[str], str]:
    """Check if current tab shows an access barrier.
    Returns (barrier_type, details) or (None, "")."""
    # Fast path: check tab title and URL
    for t in list_tabs(port):
        if t.get("id") != tab_id:
            continue
        title = (t.get("title") or "").lower()
        url = (t.get("url") or "").lower()

        # Check against configured patterns
        for barrier_name in ("cloudflare", "radware", "login_wall"):
            bc = _BARRIERS.get(barrier_name, {})
            for pattern in bc.get("title_patterns", []):
                if pattern.lower() in title:
                    return barrier_name, f"title matched '{pattern}'"
            for pattern in bc.get("url_patterns", []):
                if pattern.lower() in url:
                    return barrier_name, f"url matched '{pattern}'"

        break

    # Deep check: Runtime.evaluate for barrier selectors
    tws_url = get_tab_ws_url(port, tab_id)
    if not tws_url:
        return None, ""

    try:
        ws = websocket.create_connection(tws_url, timeout=5)

        # Check Cloudflare body selectors
        cf_selectors = _BARRIERS.get("cloudflare", {}).get("body_selectors", [])
        if cf_selectors:
            cf_js = " || ".join(f"!!document.querySelector('{s}')" for s in cf_selectors)
            ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                "params": {"expression": cf_js, "returnByValue": True}}))
            try:
                ws.settimeout(3)
                resp = json.loads(ws.recv())
                if resp.get("result", {}).get("result", {}).get("value"):
                    ws.close()
                    return "cloudflare", "body selector matched"
            except Exception:
                pass

        # Check captcha selectors
        captcha_selectors = _BARRIERS.get("captcha", {}).get("detection_selectors", [])
        if captcha_selectors:
            cp_js = " || ".join(f"!!document.querySelector('{s}')" for s in captcha_selectors)
            ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate",
                "params": {"expression": cp_js, "returnByValue": True}}))
            try:
                ws.settimeout(3)
                resp = json.loads(ws.recv())
                if resp.get("result", {}).get("result", {}).get("value"):
                    ws.close()
                    return "captcha", "captcha iframe detected"
            except Exception:
                pass

        ws.close()
    except Exception:
        pass

    return None, ""


def _handle_aip_loading_page(port: int, tab_id: str) -> int:
    """Handle AIP/AVS '请稍候' (Please wait) loading page.
    Waits up to LOADING_PAGE_TIMEOUT seconds for it to resolve.
    Returns the actual wait time used (for downstream caller to know)."""
    tws_url = get_tab_ws_url(port, tab_id)
    if not tws_url:
        return ARTICLE_RENDER_WAIT

    try:
        ws = websocket.create_connection(tws_url, timeout=5)
        # Wait for title to not contain "稍候" and have meaningful content
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
            "params": {"expression": """
                (() => {
                    const title = document.title;
                    if (title.includes('稍候') || title.includes('Loading') || title.length < 3) {
                        return 'LOADING';
                    }
                    return 'READY';
                })()
            """, "returnByValue": True}}))
        try:
            ws.settimeout(3)
            resp = json.loads(ws.recv())
            status = resp.get("result", {}).get("result", {}).get("value", "")
            ws.close()
            if status == "LOADING":
                # Wait for the loading page to resolve
                deadline = time.time() + LOADING_PAGE_TIMEOUT
                while time.time() < deadline:
                    time.sleep(2)
                    # Re-check via tab title (fast path)
                    for t in list_tabs(port):
                        if t.get("id") == tab_id:
                            title = t.get("title", "")
                            if "稍候" not in title and "Loading" not in title and len(title) > 3:
                                return LOADING_PAGE_TIMEOUT - max(0, deadline - time.time()) + 2
                            break
                return LOADING_PAGE_TIMEOUT
        except Exception:
            ws.close()
    except Exception:
        pass

    return ARTICLE_RENDER_WAIT


# ── URL Construction Helpers ────────────────────────────────────────────────

def _build_pdf_url(doi: str, publisher: dict) -> Optional[str]:
    """Build direct PDF URL from template, handling {slug} where needed."""
    template = publisher.get("pdf_url_template")
    if not template:
        return None

    if "{slug}" in template:
        slug = _resolve_slug(doi)
        if not slug:
            return None
        return template.replace("{slug}", slug).replace("{doi}", doi)

    return template.replace("{doi}", doi)


def _build_article_url(doi: str) -> str:
    """Build article landing page URL.

    Always uses doi.org redirect — it reliably resolves to the correct
    publisher page regardless of publisher-specific URL structures.
    """
    return f"https://doi.org/{doi}"


def _transform_pdf_url(url: str, publisher: dict) -> str:
    """Apply publisher-specific URL transformations before capture.

    IEEE: stamp.jsp returns HTML; getPDF.jsp returns PDF directly.
    """
    if publisher.get("_key") == "ieee" and "stamp.jsp" in url:
        return url.replace("stamp/stamp.jsp", "stampPDF/getPDF.jsp")
    return url


def _resolve_slug(doi: str) -> Optional[str]:
    """Resolve a DOI to extract the publisher-specific article slug.
    Follows the doi.org redirect and extracts the path component."""
    try:
        req = urllib.request.Request(
            f"https://doi.org/{doi}",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        final_url = resp.geturl()
        # Extract slug: the article identifier in the URL path
        # e.g. https://www.nature.com/articles/s41467-024-45578-4 → s41467-024-45578-4
        # or https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.130.100801 → prl
        parsed = urllib.parse.urlparse(final_url)
        path_parts = [p for p in parsed.path.split("/") if p]
        if path_parts:
            # For APS: the slug is a short journal code (e.g. "prl", "prb")
            # For Nature: slug is the article ID
            # Strategy: return the last substantial path segment
            for part in reversed(path_parts):
                if part not in ("articles", "article", "abstract", "content", "doi", "pdf"):
                    return part
        return None
    except Exception:
        return None


# ── File Helpers ────────────────────────────────────────────────────────────

def _doi_basename(doi: str) -> str:
    """Convert DOI to a safe filename base."""
    return doi.replace("/", "_").replace(":", "_").replace("?", "_")


def _doi_to_filename(doi: str, output_dir: str) -> str:
    """Get full file path for a DOI's PDF."""
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, f"{_doi_basename(doi)}.pdf")


def _save_pdf(pdf_data: bytes, dest: str) -> str:
    """Save PDF bytes to disk. Returns the file path."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(pdf_data)
    return dest


def _guess_si_extension(url: str) -> str:
    """Guess file extension from a supplementary info URL."""
    path = urllib.parse.urlparse(url).path.lower()
    for ext in ("pdf", "zip", "docx", "doc", "xlsx", "xls", "csv", "mp4", "cif", "txt"):
        if path.endswith(f".{ext}"):
            return ext
    return "pdf"  # default


# ── DOI List Extraction ─────────────────────────────────────────────────────

def extract_dois(input_path: str) -> list[str]:
    """Extract DOIs from a text file or Markdown literature table."""
    dois = set()
    with open(input_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    for m in re.finditer(r"10\.\d{4,}/[^\s,;)\]}\"'<>]+", text):
        doi = m.group(0).rstrip(".,;)}\"'")
        dois.add(doi)
    return sorted(dois)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generic publisher PDF downloader via CDP Chrome."
    )
    parser.add_argument("input", nargs="?", help="DOI list file (one DOI per line)")
    parser.add_argument("--port", type=int, default=9223, help="CDP Chrome debug port (default: 9223)")
    parser.add_argument("--output", "-o", default="paper-temp", help="Output directory (default: paper-temp/)")
    parser.add_argument("--test", help="Test download a single DOI")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Download timeout in seconds")
    parser.add_argument("--include-si", action="store_true", help="Also download supplementary info")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--check-session", action="store_true", help="Check publisher cookies and exit")

    args = parser.parse_args()

    if not check_required_deps():
        print("ERROR: websocket-client not installed. Run: pip install websocket-client")
        sys.exit(1)

    if not check_cdp(args.port):
        print(f"ERROR: CDP Chrome not running on port {args.port}.")
        print("Start Chrome with:")
        print(f"  {sys.executable} scripts/start_cdp_browser.py --port {args.port}")
        print("  macOS/Linux wrapper also supported: bash scripts/start_cdp_chrome.sh")
        sys.exit(1)

    # --check-session mode
    if args.check_session:
        print("=== Publisher Session Check ===")
        for key, cfg in _PUBLISHER_CONFIGS.items():
            has_session, count = check_publisher_session(args.port, cfg)
            domain = cfg.get("publisher_domain", "N/A")
            icon = "✅" if has_session else "❌"
            print(f"  {icon} {key:20s} | {domain:35s} | cookies={count}")
        return

    # --test mode
    if args.test:
        doi = args.test.strip()
        print(f"=== Testing: {doi} ===")
        publisher = resolve_publisher(doi)
        pub_name = publisher.get("_key", "unknown") if publisher else "unknown"
        strategy = publisher.get("strategy", "generic") if publisher else "unknown"
        domain = publisher.get("publisher_domain", "N/A") if publisher else "N/A"
        print(f"  Publisher: {pub_name}")
        print(f"  Strategy:  {strategy}")
        print(f"  Domain:    {domain}")

        if strategy in ("sd_cdp", "ieee_cdp"):
            print(f"  → Delegated to existing {strategy} script. Use dedicated downloader.")
            return

        if strategy == "skip":
            print(f"  → SKIPPED: {publisher.get('notes', 'automation blocked')}" if publisher else "Unknown publisher")
            return

        result_path, status, pub = download_one(
            args.port, doi, args.output,
            include_si=args.include_si,
            timeout=args.timeout
        )

        if result_path and status == "ok":
            size_kb = os.path.getsize(result_path) // 1024
            print(f"  ✅ Downloaded: {result_path} ({size_kb} KB)")
        else:
            print(f"  ❌ Failed: status={status}")
        return

    # Batch mode
    if not args.input:
        parser.print_help()
        sys.exit(1)

    dois = extract_dois(args.input)
    if not dois:
        print("No DOIs found in input file.")
        sys.exit(1)

    print(f"DOI count: {len(dois)}")
    print(f"Output:    {args.output}/")
    print(f"CDP port:  {args.port}\n")

    ok, fail, skip = 0, 0, 0
    failed_dois = []

    for i, doi in enumerate(dois):
        publisher = resolve_publisher(doi)
        pub_name = publisher.get("_key", "unknown") if publisher else "unknown"
        strategy = publisher.get("strategy", "generic") if publisher else "unknown"

        print(f"[{i+1}/{len(dois)}] {doi[:50]}", end=" ", flush=True)

        if strategy in ("sd_cdp", "ieee_cdp"):
            print(f"→ delegating to {strategy} (skipped by generic downloader)")
            skip += 1
            continue

        if strategy == "skip":
            print(f"→ SKIP ({publisher.get('notes', '')[:40]})" if publisher else "→ SKIP (unknown)")
            skip += 1
            continue

        t0 = time.time()
        result_path, status, _ = download_one(
            args.port, doi, args.output,
            include_si=args.include_si,
            timeout=args.timeout
        )
        elapsed = time.time() - t0

        if result_path and status == "ok":
            size_kb = os.path.getsize(result_path) // 1024
            print(f"✅ {pub_name} ({size_kb}KB, {elapsed:.1f}s)")
            ok += 1
        elif status == "si_only":
            print(f"⚠ SI only, no PDF ({elapsed:.1f}s)")
            fail += 1
            failed_dois.append(doi)
        else:
            print(f"❌ {pub_name} failed ({elapsed:.1f}s)")
            fail += 1
            failed_dois.append(doi)

        time.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"Complete: ✅ {ok}  ❌ {fail}  ⏭ {skip}")
    print(f"Output: {args.output}/")

    if failed_dois:
        failed_path = os.path.join(args.output, "generic_failed_dois.txt")
        with open(failed_path, "w", encoding="utf-8") as f:
            for d in failed_dois:
                f.write(d + "\n")
        print(f"Failed list: {failed_path}")


if __name__ == "__main__":
    main()
