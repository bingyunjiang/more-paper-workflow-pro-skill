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

import sys, os, json, time, re, base64, urllib.request, urllib.error, urllib.parse, tomllib, argparse
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
CNKI_NON_OK_STATUSES = {
    "captcha_required",
    "pdf_probe_unknown",
    "manual_required",
    "chapter_download_mode",
}
WANFANG_NON_OK_STATUSES = {
    "manual_required",
    "pdf_probe_unknown",
    "fulltext_delivery_mode",
    "no_url",
}

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
                 article_url: str = "",
                 title: str = "") -> tuple[Optional[str], str, str]:
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
        title: Optional paper title. Used only for CNKI reusable-tab matching.

    Returns: (pdf_path_or_None, status, publisher_name)
      status: "ok" | "failed" | "skipped" | "manual_required" | "no_url"
              | "captcha_required" | "institution_login_required"
              | "pdf_probe_unknown" | "access_denied"
              | "chapter_download_mode"
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
        path = _strategy_direct_http(doi, publisher, output_dir)
        return path, ("ok" if path else "failed"), pub_name

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
            wf_result = _download_wanfang(port, article_url, publisher, timeout,
                                          output_dir=output_dir)
            if wf_result in WANFANG_NON_OK_STATUSES:
                return None, str(wf_result), pub_name
            if wf_result:
                return wf_result, "ok", pub_name
            return None, "failed", pub_name
        # CNKI: click-based download (requires Referrer from article page)
        elif pub_name == "cnki":
            cnki_result = _download_cnki(port, article_url, publisher, timeout,
                                         output_dir=output_dir, title=title)
            if cnki_result in CNKI_NON_OK_STATUSES:
                return None, str(cnki_result), pub_name
            if cnki_result:
                return cnki_result, "ok", pub_name
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
    if isinstance(pdf_data, str):
        return None, pdf_data.lower(), pub_name
    if pdf_data:
        return _save_pdf(pdf_data, dest), "ok", pub_name

    if pub_name == "ieee":
        ieee_path = _download_ieee_via_generic_fallback(
            port, doi, output_dir, publisher, timeout
        )
        if ieee_path:
            return ieee_path, "ok", pub_name

    # SI download (if requested and PDF failed)
    if include_si:
        si_paths = download_si(port, doi, publisher, output_dir)
        if si_paths:
            return None, "si_only", pub_name

    return None, "failed", pub_name


def _download_sciencedirect(port: int, doi: str, output_dir: str) -> tuple[Optional[str], str]:
    """ScienceDirect adapter used by the Generic CDP route.

    Keep the ScienceDirect-specific DOI -> PII knowledge, but use the generic
    capture primitive: fresh tab, Fetch.enable before navigation, and article
    referrer on the PDF request.
    """
    try:
        from batch_resolve_pii import _resolve_pii_from_crossref
        from sd_download import diagnose_sd_pii
    except Exception:
        return None, "failed"

    pii = _resolve_pii_from_crossref(doi)
    if not pii:
        return None, "pii_resolution_failed"

    article_url = f"https://www.sciencedirect.com/science/article/pii/{pii}"
    pdfft_url = f"{article_url}/pdfft"
    data = _navigate_and_capture_pdf(
        port,
        pdfft_url,
        referrer=article_url,
        timeout=DEFAULT_TIMEOUT,
    )
    if data and len(data) > 20000:
        return _save_pdf(data, _doi_to_filename(doi, output_dir)), "ok"

    diag = diagnose_sd_pii(port, pii)
    kind = diag.get("kind")
    if kind == "manual_verification_required":
        return None, "institution_login_required"
    if kind == "referencework_abs":
        return None, "not_subscribed_or_referencework"
    if kind == "article_page_only":
        return None, "pdf_probe_unknown"
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
    """Check if CDP browser has cookies for this publisher.
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


def describe_publisher_session(port: int, publisher: dict) -> dict:
    """Return a richer session/probe description for reporting."""
    key = publisher.get("_key", "unknown")
    domain = publisher.get("publisher_domain", "")
    strategy = publisher.get("strategy", "?")
    has_session, count = check_publisher_session(port, publisher)
    result = {
        "publisher": key,
        "domain": domain,
        "strategy": strategy,
        "has_session": has_session,
        "cookie_count": count,
        "signal_strength": "weak_cookie_probe",
        "probe_status": "unknown",
        "probe_reason": "cookie probe only",
    }

    if key == "sd_elsevier":
        try:
            from cdp_utils import check_sd_access
            status, reason = check_sd_access(port)
            result["signal_strength"] = "pdf_probe"
            result["probe_status"] = status
            result["probe_reason"] = reason
            if status == "ok":
                result["has_session"] = True
        except Exception as exc:
            result["probe_status"] = "error"
            result["probe_reason"] = f"probe error: {type(exc).__name__}"
    elif key == "wiley":
        status, reason = check_wiley_access(port, publisher)
        result["signal_strength"] = "article_probe"
        result["probe_status"] = status
        result["probe_reason"] = reason
        if status == "ok":
            result["has_session"] = True
    elif count == 0:
        result["probe_status"] = "unknown"
        result["probe_reason"] = "no matching cookies; manual verification may still succeed"
    else:
        result["probe_status"] = "cookie_present"
        result["probe_reason"] = f"{count} matching cookies"

    return result


_WILEY_TEST_DOI = "10.1002/ente.202301205"


def check_wiley_access(port: int, publisher: dict, timeout: int = DEFAULT_TIMEOUT) -> tuple[str, str]:
    """Probe whether Wiley looks downloadable in the current CDP session.

    This is lighter-weight than a full download: it loads a known Wiley article
    page, checks for access barriers, then asks the existing DOM extractor
    whether a plausible PDF link is present.
    """
    if not check_cdp(port):
        return "blocked", "CDP browser not running"

    article_url = _build_article_url(_WILEY_TEST_DOI)
    if not article_url:
        return "error", "failed to build Wiley test URL"

    try:
        _, tid = create_tab(port, article_url)
    except Exception:
        return "error", "failed to create Wiley probe tab"

    try:
        time.sleep(min(timeout, ARTICLE_RENDER_WAIT))
        barrier, barrier_detail = _detect_access_barrier(port, tid)
        pdf_url = _extract_pdf_url_from_dom(port, tid, publisher.get("selectors", []))

        if barrier == "captcha":
            return "blocked", f"captcha: {barrier_detail}"
        if pdf_url == "LOGIN_REQUIRED":
            return "blocked", "login_required: article page requests institutional login"
        if pdf_url == "ACCESS_DENIED":
            return "blocked", "access_denied: article page reports no access"
        if isinstance(pdf_url, str) and pdf_url not in ("NO_PDF_LINK", ""):
            return "ok", f"pdf_link_present: {pdf_url[:80]}"
        if barrier:
            return "blocked", f"{barrier}: {barrier_detail}"
        return "unknown", "no_pdf_link_observed"
    finally:
        close_tab(port, tid)


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
        if barrier == "captcha":
            return "CAPTCHA_REQUIRED"
        return "PDF_PROBE_UNKNOWN"

    # Keep the tab open when the site wants human login/verification so the
    # user has time to complete it in the visible CDP browser.
    if pdf_url in ("LOGIN_REQUIRED", "ACCESS_DENIED"):
        print(f"  ⚠ {pub_key or 'publisher'} requires manual access confirmation — leaving tab open")
        return pdf_url

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
    pdf_data = _navigate_and_capture_pdf(port, pdf_url, referrer=referrer, timeout=timeout)
    if pdf_data:
        return pdf_data

    if pub_key == "mdpi":
        print("  ⚠ MDPI PDF link found but CDP capture failed — leaving tab open for manual Download PDF click")
        try:
            _, manual_tid = create_tab(port, article_url)
            time.sleep(ARTICLE_RENDER_WAIT)
        except Exception:
            pass
        return "MANUAL_REQUIRED"

    return None


# ── Wanfang Download ─────────────────────────────────────────────────────────

def _parse_wanfang_article_url(article_url: str) -> tuple[str, str, str] | None:
    """Return (paper_type, paper_id, detail_url) for supported Wanfang URLs."""
    import urllib.parse as _urlparse

    parsed = _urlparse.urlparse(article_url)
    path = parsed.path.strip("/")
    query = _urlparse.parse_qs(parsed.query)

    if parsed.netloc == "d.wanfangdata.com.cn":
        parts = path.split("/", 1)
        if len(parts) == 2 and parts[0] in {"periodical", "thesis"} and parts[1]:
            return parts[0], parts[1], article_url

    if parsed.netloc == "www.wanfangdata.com.cn" and path == "details/detail.do":
        raw_type = (query.get("_type") or query.get("type") or [""])[0].lower()
        paper_id = (query.get("id") or [""])[0]
        if raw_type in {"perio", "periodical"} and paper_id:
            return "periodical", paper_id, f"https://d.wanfangdata.com.cn/periodical/{paper_id}"
        if raw_type == "thesis" and paper_id:
            return "thesis", paper_id, f"https://d.wanfangdata.com.cn/thesis/{paper_id}"

    return None


def _wanfang_detail_click_expression(paper_type: str) -> str:
    """Build Wanfang detail-page JS with per-type download white-listing."""
    allowed = "['整篇下载', '下载']" if paper_type == "thesis" else "['下载']"
    delivery = "['原文传递']"
    blocked = "['在线阅读', '评审材料', '分章下载']"
    return f'''
(function(){{
  var allowed = {allowed};
  var delivery = {delivery};
  var blocked = {blocked};
  function textOf(node) {{
    return ((node.innerText || node.textContent || node.getAttribute('title') || '') + '').trim();
  }}
  function hasAny(text, terms) {{
    for (var i = 0; i < terms.length; i++) {{
      if (text.indexOf(terms[i]) >= 0) return true;
    }}
    return false;
  }}
  var nodes = document.querySelectorAll('a, button, span, div');
  for (var i = 0; i < nodes.length; i++) {{
    var text = textOf(nodes[i]);
    if (hasAny(text, blocked)) continue;
    var compact = text.replace(/\\s+/g, '');
    if (allowed.indexOf(text) >= 0 || allowed.indexOf(compact) >= 0) {{
      if (nodes[i].removeAttribute) nodes[i].removeAttribute('target');
      nodes[i].click();
      return 'clicked:' + compact;
    }}
    if (delivery.indexOf(text) >= 0 || delivery.indexOf(compact) >= 0) {{
      return 'delivery:' + compact;
    }}
  }}
  return 'pdf_probe_unknown';
}})()
'''


def _wanfang_click_download_interstitial(port: int, tab_id: str) -> str:
    tab_ws_url = get_tab_ws_url(port, tab_id)
    if not tab_ws_url:
        return "pdf_probe_unknown"
    tab_ws = websocket.create_connection(tab_ws_url, timeout=10)
    js_click = '''
(function(){
  var as = document.querySelectorAll("a");
  for (var i = 0; i < as.length; i++) {
    if ((as[i].innerText || '').indexOf("点击此处") >= 0) {
      as[i].click();
      return "clicked";
    }
  }
  return "not_found";
})()
'''
    tab_ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": js_click}}))
    resp = json.loads(tab_ws.recv())
    tab_ws.close()
    return str(resp.get("result", {}).get("result", {}).get("value", ""))


def _wanfang_click_download_info_page(port: int, known_tab_ids: Optional[set[str]] = None) -> str:
    """Click Wanfang's real download link on the generated download-info page."""
    tabs = list_tabs(port)
    if known_tab_ids:
        new_tabs = [tab for tab in tabs if str(tab.get("id", "")) not in known_tab_ids]
        tabs = new_tabs or tabs
    for tab in tabs:
        tab_id = str(tab.get("id", ""))
        url = str(tab.get("url", ""))
        if "f.wanfangdata.com.cn/download/pc/" not in url:
            continue
        tab_ws_url = get_tab_ws_url(port, tab_id)
        if not tab_ws_url:
            continue
        tab_ws = websocket.create_connection(tab_ws_url, timeout=10)
        js_click = '''
(function(){
  var direct = document.querySelector("#doDownload");
  if (direct) {
    direct.click();
    return "clicked_doDownload";
  }
  var as = document.querySelectorAll("a");
  for (var i = 0; i < as.length; i++) {
    if ((as[i].innerText || '').indexOf("点击此处") >= 0) {
      as[i].click();
      return "clicked_text";
    }
  }
  return "not_found";
})()
'''
        tab_ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": js_click}}))
        resp = json.loads(tab_ws.recv())
        tab_ws.close()
        result = str(resp.get("result", {}).get("result", {}).get("value", ""))
        if result.startswith("clicked"):
            return result
    return "not_found"


def _wait_for_wanfang_download_info_click(
    port: int,
    known_tab_ids: Optional[set[str]] = None,
    timeout: int = 20,
) -> str:
    """Wait for the Wanfang download-info page to appear, then click its real download control."""
    deadline = time.time() + max(timeout, 1)
    last_result = "not_found"
    while time.time() < deadline:
        result = _wanfang_click_download_info_page(port, known_tab_ids=known_tab_ids)
        if result.startswith("clicked"):
            return result
        last_result = result
        time.sleep(1)
    return last_result


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
    parsed = _parse_wanfang_article_url(article_url)
    if not parsed:
        return "no_url"
    paper_type, _paper_id, detail_url = parsed

    # Step 1: Open Wanfang detail page and click the type-specific white-list entry.
    browser_ws_url = get_cdp_ws_url(port)
    bws = websocket.create_connection(browser_ws_url, timeout=10)
    bws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                         "params": {"url": detail_url}}))
    tid = json.loads(bws.recv())["result"]["targetId"]
    bws.close()
    time.sleep(4)

    downloads_dir = _os.path.expanduser("~/Downloads")
    before_dl = set(_glob.glob(_os.path.join(downloads_dir, "*.pdf")))
    known_tab_ids = {str(tab.get("id", "")) for tab in list_tabs(port)}

    # Get tab WS for click operation
    tab_ws_url = get_tab_ws_url(port, tid)
    if not tab_ws_url:
        return "pdf_probe_unknown"
    tab_ws = websocket.create_connection(tab_ws_url, timeout=10)

    tab_ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate",
                            "params": {"expression": _wanfang_detail_click_expression(paper_type)}}))
    click_resp = json.loads(tab_ws.recv())
    click_result = str(click_resp.get("result", {}).get("result", {}).get("value", ""))
    tab_ws.close()
    delivery_clicked = click_result.startswith("delivery:")
    if not click_result.startswith("clicked:") and not delivery_clicked:
        close_tab(port, tid)
        return "pdf_probe_unknown"
    if delivery_clicked:
        close_tab(port, tid)
        return "fulltext_delivery_mode"

    # Step 2: If Wanfang opens an interstitial download page, click "点击此处".
    time.sleep(10)
    _wanfang_click_download_interstitial(port, tid)
    download_started_at = time.time()
    _wait_for_wanfang_download_info_click(
        port,
        known_tab_ids=known_tab_ids,
        timeout=min(max(timeout, 10), 30),
    )

    # Step 3: Wait for PDF in ~/Downloads (Browser.setDownloadBehavior path is unreliable)
    for i in range(timeout + 30):
        time.sleep(1)
        current = set(_glob.glob(_os.path.join(downloads_dir, "*.pdf")))
        new_pdfs = current - before_dl
        recent_pdfs = [
            path for path in current
            if _os.path.getmtime(path) >= download_started_at - 2
        ]
        crdownloads = _glob.glob(_os.path.join(downloads_dir, "*.crdownload"))
        candidates = list(new_pdfs) or recent_pdfs
        if candidates and not crdownloads:
            dl_path = max(candidates, key=_os.path.getmtime)
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

def _cnki_download_click_expression() -> str:
    """Build CNKI detail-page JS for status split and text-first entry lookup."""
    return r'''
(function(){
  var title = (document.title || '').trim();
  var url = String(location.href || '');
  var body = (document.body && document.body.innerText || '').trim();
  if (url.indexOf('/verify/home') >= 0 ||
      title.indexOf('安全验证') >= 0 ||
      body.indexOf('请完成安全验证') >= 0) {
    return 'captcha_required';
  }

  function textOf(node) {
    return ((node.innerText || node.textContent || node.getAttribute('title') || '') + '').trim();
  }
  function hrefOf(node) {
    return ((node.href || node.getAttribute('href') || '') + '').trim();
  }
  function hasAny(text, terms) {
    for (var i = 0; i < terms.length; i++) {
      if (text.indexOf(terms[i]) >= 0) return true;
    }
    return false;
  }
  function isBlockedEntry(node) {
    var text = textOf(node);
    return hasAny(text, ['AI阅读', '原版阅读', 'CAJ下载', '章节下载', '分页下载', '我是作者', '免费下载']);
  }
  function findPdfDownload() {
    var nodes = document.querySelectorAll('a, button, span, div');
    for (var i = 0; i < nodes.length; i++) {
      if (isBlockedEntry(nodes[i])) continue;
      var text = textOf(nodes[i]);
      var href = hrefOf(nodes[i]).toLowerCase();
      if ((text.indexOf('PDF下载') >= 0 || text.indexOf('PDF 下载') >= 0) &&
          !hasAny(text, ['CAJ', '章节', '分页', 'AI阅读', '原版阅读', '我是作者', '免费'])) {
        return nodes[i];
      }
      if (href.indexOf('bar.cnki.net/bar/download/order') >= 0 &&
          (text.indexOf('PDF') >= 0 || href.indexOf('pdf') >= 0)) {
        return nodes[i];
      }
    }
    return null;
  }
  function hasChapterMode() {
    var nodes = document.querySelectorAll('a, button, span, div');
    for (var i = 0; i < nodes.length; i++) {
      var text = textOf(nodes[i]);
      if (hasAny(text, ['章节下载', '分页下载'])) return true;
    }
    return false;
  }
  function clickNode(node, label) {
    if (!node) return null;
    if (node.removeAttribute) node.removeAttribute('target');
    node.click();
    return 'clicked:' + label + ':' + hrefOf(node).substring(0, 120);
  }

  var pdfDown = document.querySelector('#pdfDown');
  var pdf = (pdfDown && !isBlockedEntry(pdfDown)) ? pdfDown : findPdfDownload();
  var clicked = clickNode(pdf, 'PDF下载');
  if (clicked) return clicked;

  // Journal and thesis detail pages use the same rule: click PDF only.
  // Chapter/page entries are diagnostic only when no PDF entry was found.
  if (hasChapterMode()) return 'chapter_download_mode';
  return 'pdf_probe_unknown';
})()
'''


def _cnki_status_from_click_result(result_val: object) -> Optional[str]:
    value = str(result_val or "")
    if value in CNKI_NON_OK_STATUSES:
        return value
    if value.startswith("clicked:"):
        return None
    if value == "no_pdfDown":
        return "pdf_probe_unknown"
    return None


def _cnki_normalize_title(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def _cnki_same_article_url(left: str, right: str) -> bool:
    """Return True when two CNKI URLs identify the same detail page."""
    if not left or not right:
        return False
    left_parts = urllib.parse.urlparse(left)
    right_parts = urllib.parse.urlparse(right)
    left_key = (left_parts.netloc.lower(), left_parts.path.lower())
    right_key = (right_parts.netloc.lower(), right_parts.path.lower())
    if left_key == right_key and left_parts.query == right_parts.query:
        return True

    left_q = urllib.parse.parse_qs(left_parts.query)
    right_q = urllib.parse.parse_qs(right_parts.query)
    for key in ("filename", "dbcode"):
        left_val = (left_q.get(key) or left_q.get(key.upper()) or [""])[0].lower()
        right_val = (right_q.get(key) or right_q.get(key.upper()) or [""])[0].lower()
        if not left_val or not right_val or left_val != right_val:
            return False
    return True


def _cnki_url_references_article(candidate_url: str, article_url: str) -> bool:
    if not candidate_url or not article_url:
        return False
    candidate = urllib.parse.unquote(candidate_url).lower()
    target = urllib.parse.unquote(article_url).lower()
    if target and target in candidate:
        return True

    target_q = urllib.parse.parse_qs(urllib.parse.urlparse(article_url).query)
    filename = (target_q.get("filename") or target_q.get("FILENAME") or [""])[0].lower()
    dbcode = (target_q.get("dbcode") or target_q.get("DBCODE") or [""])[0].lower()
    if filename and filename in candidate:
        return not dbcode or dbcode in candidate
    return False


def _cnki_tab_probe_expression(target_title: str = "") -> str:
    return r'''
(function(targetTitle){
  function textOf(node) {
    return ((node.innerText || node.textContent || node.getAttribute('title') || '') + '').trim();
  }
  function hrefOf(node) {
    return ((node.href || node.getAttribute('href') || '') + '').trim();
  }
  function hasAny(text, terms) {
    for (var i = 0; i < terms.length; i++) {
      if (text.indexOf(terms[i]) >= 0) return true;
    }
    return false;
  }
  function isBlockedEntry(node) {
    var text = textOf(node);
    return hasAny(text, ['AI阅读', '原版阅读', 'CAJ下载', '章节下载', '分页下载', '我是作者', '免费下载']);
  }
  function hasPdfDownload() {
    var pdfDown = document.querySelector('#pdfDown');
    if (pdfDown && !isBlockedEntry(pdfDown)) return true;
    var nodes = document.querySelectorAll('a, button, span, div');
    for (var i = 0; i < nodes.length; i++) {
      if (isBlockedEntry(nodes[i])) continue;
      var text = textOf(nodes[i]);
      var href = hrefOf(nodes[i]).toLowerCase();
      if ((text.indexOf('PDF下载') >= 0 || text.indexOf('PDF 下载') >= 0) &&
          !hasAny(text, ['CAJ', '章节', '分页', 'AI阅读', '原版阅读', '我是作者', '免费'])) {
        return true;
      }
      if (href.indexOf('bar.cnki.net/bar/download/order') >= 0 &&
          (text.indexOf('PDF') >= 0 || href.indexOf('pdf') >= 0)) {
        return true;
      }
    }
    return false;
  }
  var title = (document.title || '').trim();
  var url = String(location.href || '');
  var body = (document.body && document.body.innerText || '').trim();
  return {
    url: url,
    title: title,
    body: body.substring(0, 5000),
    captcha: url.indexOf('/verify/home') >= 0 ||
      title.indexOf('安全验证') >= 0 ||
      body.indexOf('请完成安全验证') >= 0,
    pdfVisible: hasPdfDownload()
  };
})(''' + json.dumps(target_title or "", ensure_ascii=False) + r''')
'''


def _cnki_evaluate_tab(tab_ws_url: str, expression: str) -> object:
    tab_ws = websocket.create_connection(tab_ws_url, timeout=10)
    try:
        tab_ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                                "params": {"expression": expression, "returnByValue": True}}))
        result = json.loads(tab_ws.recv())
        return result.get("result", {}).get("result", {}).get("value")
    finally:
        tab_ws.close()


def _cnki_probe_tab(port: int, tab_id: str, title: str = "") -> Optional[dict]:
    tab_ws_url = get_tab_ws_url(port, tab_id)
    if not tab_ws_url:
        return None
    value = _cnki_evaluate_tab(tab_ws_url, _cnki_tab_probe_expression(title))
    return value if isinstance(value, dict) else None


def _find_reusable_cnki_tab(port: int, article_url: str,
                            title: str = "") -> tuple[Optional[str], Optional[str]]:
    """Find an already-open CNKI detail tab for the target paper.

    Returns (tab_id, status). status is "captcha_required" when the matching
    tab is a CNKI verification page that should be left open for the user.
    """
    target_title = _cnki_normalize_title(title)
    for tab in list_tabs(port):
        tab_id = tab.get("id", "")
        tab_url = tab.get("url", "")
        if not tab_id or "cnki.net" not in tab_url.lower():
            continue
        probe = _cnki_probe_tab(port, tab_id, title)
        if not probe:
            continue
        probe_url = str(probe.get("url") or tab_url)
        haystack = _cnki_normalize_title(
            f"{probe.get('title', '')} {probe.get('body', '')}"
        )
        same_url = _cnki_same_article_url(probe_url, article_url)
        title_match = bool(target_title and target_title in haystack)
        if probe.get("captcha") and (
            same_url or title_match or _cnki_url_references_article(probe_url, article_url)
        ):
            return tab_id, "captcha_required"
        if same_url:
            return tab_id, None
        if title_match and probe.get("pdfVisible"):
            return tab_id, None
    return None, None


def _cnki_create_detail_tab(port: int, article_url: str) -> Optional[str]:
    browser_ws_url = get_cdp_ws_url(port)
    bws = websocket.create_connection(browser_ws_url, timeout=10)
    try:
        bws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                             "params": {"url": article_url}}))
        return json.loads(bws.recv())["result"]["targetId"]
    finally:
        bws.close()


def _cnki_wait_for_download(downloads_dir: str, before_dl: set[str],
                            output_dir: str, article_url: str,
                            timeout: int) -> Optional[str]:
    import os as _os, glob as _glob, hashlib, shutil as _shutil

    for _ in range(timeout + 15):
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
                return dest
    return None


def _download_cnki(port: int, article_url: str, publisher: dict,
                   timeout: int = DEFAULT_TIMEOUT,
                   output_dir: str = "",
                   title: str = "") -> Optional[str]:
    """Download CNKI paper by clicking PDF download on article detail page.

    CNKI requires Referrer from the article page, so we must click from
    the detail page rather than navigating directly to bar.cnki.net.
    """
    import os as _os, glob as _glob

    # Step 1: Prefer a user-verified CNKI detail tab before opening the URL
    # again, because revisiting the URL can trigger CNKI verification loops.
    tid, reusable_status = _find_reusable_cnki_tab(port, article_url, title=title)
    should_close_tab = False
    if reusable_status:
        return reusable_status
    if not tid:
        tid = _cnki_create_detail_tab(port, article_url)
        should_close_tab = True
        time.sleep(5)  # CNKI detail pages are heavy
    if not tid:
        return None

    # Get tab WS for click operation
    tab_ws_url = get_tab_ws_url(port, tid)
    if not tab_ws_url:
        return None

    # Step 2: Click whole-paper download entries, or return a precise CNKI state.
    downloads_dir = _os.path.expanduser("~/Downloads")
    before_dl = set(_glob.glob(_os.path.join(downloads_dir, "*.pdf")))
    js = _cnki_download_click_expression()
    result_val = _cnki_evaluate_tab(tab_ws_url, js)

    status = _cnki_status_from_click_result(result_val)
    if status:
        # Leave captcha/manual tabs open so the user can verify or click manually.
        if should_close_tab and status not in ("captcha_required", "manual_required", "chapter_download_mode"):
            close_tab(port, tid)
        return status

    # Step 3: Wait for PDF in ~/Downloads
    pdf_path = _cnki_wait_for_download(
        downloads_dir, before_dl, output_dir, article_url, timeout
    )
    if pdf_path:
        if should_close_tab:
            close_tab(port, tid)
        return pdf_path

    return "manual_required"


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


def _resolve_ieee_arnumber(doi: str) -> tuple[Optional[str], str]:
    """Resolve IEEE arnumber from doi.org redirect target."""
    try:
        req = urllib.request.Request(
            f"https://doi.org/{doi}",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        final_url = resp.geturl()
        match = re.search(r"/document/(\d+)", final_url)
        if match:
            return match.group(1), final_url
        return None, final_url
    except Exception as exc:
        return None, str(exc)


def _download_ieee_via_generic_fallback(port: int, doi: str, output_dir: str,
                                        publisher: dict,
                                        timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    """Fallback IEEE download path using arnumber -> stamp/getPDF URLs."""
    arnumber, article_url = _resolve_ieee_arnumber(doi)
    if not arnumber:
        return None

    dest = _doi_to_filename(doi, output_dir)
    candidate_urls = [
        f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arnumber}",
        f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber}",
    ]
    referrer = article_url if article_url.startswith("http") else _build_article_url(doi)

    for url in candidate_urls:
        pdf_data = _navigate_and_capture_pdf(port, url, referrer=referrer, timeout=timeout)
        if pdf_data:
            return _save_pdf(pdf_data, dest)
    return None


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
            signal = describe_publisher_session(args.port, cfg)
            icon = "✅" if signal["has_session"] else "❌"
            print(
                f"  {icon} {key:20s} | {signal['domain']:35s} | "
                f"cookies={signal['cookie_count']} | "
                f"{signal['probe_status']}: {signal['probe_reason']}"
            )
        print("\n  Note: cookie count is only a weak signal; real PDF access may differ.")
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
