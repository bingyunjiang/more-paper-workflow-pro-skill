#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Search academic papers by topic across multiple sources with T1->T2->T3 routing.
Outputs DOI list, .bib, .ris, or .nbib — ready for PII resolution + download + Zotero import.

v3.0 — adds boolean query building (concept blocks AND/OR/NOT), --bool mode,
       multi-strategy search (relevance/cited/recent), and L1/L2/L3 layering.

Usage:
  # Basic search (backward compatible)
  python3 search_by_topic.py "battery thermal management spray cooling" --limit 20

  # T1->T2->T3 routing with fallback
  python3 search_by_topic.py "cold plate topology optimization" \
      --t1 semantic_scholar --t2 crossref --t3 openalex --limit 50

  # v3.0: Boolean query from concept blocks JSON file
  python3 search_by_topic.py --bool query_plan.json \
      --source openalex --strategy relevance --limit 50

  # v3.0: Multi-strategy (relevance + cited + recent) in one call
  python3 search_by_topic.py --bool query_plan.json \
      --source openalex --strategy all --limit 50 --export-bib results.bib

  # Pre-flight API health check
  python3 search_by_topic.py --preflight

  # Export as .bib with tier/score notes (Zotero-ready)
  python3 search_by_topic.py "query" --t1 crossref --export-bib output.bib

  # Convert between formats
  python3 search_by_topic.py --convert input.bib --to ris --output output.ris
  python3 search_by_topic.py --convert input.bib --to nbib

  # Verify DOIs from a file
  python3 search_by_topic.py --verify-dois dois.txt

  # CNKI Chinese literature search (campus IP or CARSI CDP login)
  python3 search_by_topic.py "冷板拓扑优化" --source cnki --limit 20

  # CNKI multi-strategy: sort by citations
  python3 search_by_topic.py "拓扑优化" --source cnki --strategy cited --limit 20

  # T1/T2/T3 routing with CNKI primary + Wanfang supplement
  python3 search_by_topic.py "散热器优化" --t1 cnki --t2 wanfang --limit 50
"""
try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import hashlib
import json
import urllib.request
import urllib.parse
import time
import sys
import re
import os

try:
    from workflow_contracts import SearchResultRecord, write_workflow_json
except ImportError:  # Allow standalone execution from unusual working dirs.
    SearchResultRecord = None
    write_workflow_json = None

# ── Semantic Cache ─────────────────────────────────────────────────────────

CACHE_DIR = os.path.expanduser("~/.cache/more-paper-workflow/search_cache")
CACHE_TTL_SECONDS = 7 * 24 * 3600  # 7 days
CACHE_MAX_ENTRIES = 500
SEMANTIC_SCHOLAR_ANON_MIN_INTERVAL = 1.2
_semantic_scholar_last_request_ts = 0.0
CNKI_CDP_MAX_ATTEMPTS = 3
CNKI_CDP_RETRY_WAIT_SECONDS = 2.0

# ── Wanfang Web Search ──────────────────────────────────────────────────

WANFANG_SEARCH_URL = "https://www.wanfangdata.com.cn/search/searchList.do"
# CDP Chrome port — override via env var CDP_PORT or --cdp-port CLI arg.
# Default 9223 matches start_cdp_chrome.sh. Use env CDP_PORT to override.
# macOS/Linux wrapper: bash scripts/start_cdp_chrome.sh --port 9223
_CDP_PORT = int(os.environ.get("CDP_PORT", "9223"))

WANFANG_CDP_PORT = _CDP_PORT
WANFANG_SPA_URL = "https://s.wanfangdata.com.cn/paper"

# ── CNKI Web Search ─────────────────────────────────────────────────────

CNKI_BASE_URL = "https://www.cnki.net"
CNKI_ADV_SEARCH_URL = "https://kns.cnki.net/kns/AdvSearch?classid=7NS01R8M"
CNKI_OLD_SEARCH_URL = "http://kns.cnki.net/kns/brief/brief.aspx"
CNKI_SEARCH_HANDLER = "http://kns.cnki.net/kns/request/SearchHandler.ashx"
CNKI_CDP_PORT = _CDP_PORT

# ── Language Detection ─────────────────────────────────────────────────────

# CJK Unified Ideographs range: U+4E00 – U+9FFF
_CJK_RE = re.compile(r'[一-鿿]')


def _has_chinese(text):
    """Return True if text contains at least one Chinese character."""
    if not text:
        return False
    return bool(_CJK_RE.search(text))


def _filter_by_language(results, language):
    """Post-search language filter on result titles.

    When language='zh': keep only results whose title contains Chinese characters.
    When language='en': keep only results whose title contains NO Chinese characters.
    When language='any': no filtering.

    This is a safety net for CNKI/Wanfang — even after query-level filtering,
    some English papers may leak through because Chinese journals publish
    bilingual content.  English papers in CNKI/Wanfang are hard to download
    via the CDP pipeline, so filtering them out early prevents Step 5 failures.

    Returns filtered list and a count of removed items.
    """
    if language == "any" or not language:
        return results, 0
    filtered = []
    removed = 0
    for r in results:
        title = r.get("title", "")
        is_cn = _has_chinese(title)
        if language == "zh" and not is_cn:
            removed += 1
            continue
        if language == "en" and is_cn:
            removed += 1
            continue
        filtered.append(r)
    return filtered, removed


def _pick_cdp_page_target(targets, preferred_markers=None):
    """Pick the most suitable CDP page target for a source-specific workflow.

    preferred_markers: ordered list of substrings matched against page URL/title.
    Falls back to the first non-extension page, then the first page target.
    """
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        return None

    preferred_markers = preferred_markers or []
    for marker in preferred_markers:
        marker = (marker or "").lower()
        for page in pages:
            haystack = f"{page.get('url', '')} {page.get('title', '')}".lower()
            if marker and marker in haystack:
                return page

    for page in pages:
        url = (page.get("url") or "").lower()
        if not url.startswith("chrome-extension://") and not url.startswith("devtools://"):
            return page

    return pages[0]


def _cache_key(query, source, limit, strategy=""):
    raw = f"{query}|{source}|{limit}|{strategy}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key):
    cache_file = os.path.join(CACHE_DIR, key + ".json")
    if not os.path.exists(cache_file):
        return None
    if time.time() - os.path.getmtime(cache_file) > CACHE_TTL_SECONDS:
        try:
            os.remove(cache_file)
        except OSError:
            pass
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _cache_set(key, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    # LRU eviction
    try:
        cache_files = sorted(
            [os.path.join(CACHE_DIR, f) for f in os.listdir(CACHE_DIR) if f.endswith(".json")],
            key=os.path.getmtime,
        )
        while len(cache_files) >= CACHE_MAX_ENTRIES:
            try:
                os.remove(cache_files.pop(0))
            except OSError:
                break
    except OSError:
        pass
    tmp = os.path.join(CACHE_DIR, key + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, os.path.join(CACHE_DIR, key + ".json"))


def _throttle_semantic_scholar_if_anonymous(api_key):
    """Throttle anonymous Semantic Scholar requests before hitting the API.

    Semantic Scholar's unauthenticated quota is easy to trip during repeated
    interactive searches. When no API key is configured, enforce a minimum
    spacing between requests. Authenticated callers keep the current behavior.
    """
    if api_key:
        return

    global _semantic_scholar_last_request_ts
    now = time.time()
    elapsed = now - _semantic_scholar_last_request_ts
    wait = SEMANTIC_SCHOLAR_ANON_MIN_INTERVAL - elapsed
    if wait > 0:
        print(f"  Semantic Scholar: anonymous throttle, waiting {wait:.1f}s...", flush=True)
        time.sleep(wait)
        now = time.time()
    _semantic_scholar_last_request_ts = now


# ── Abstract Utilities ─────────────────────────────────────────────────────

# Method detection keywords for abstract-based scoring
_experiment_kw = {"experiment", "experimental", "test rig", "prototype",
                  "measurement", "measured", "tested", "fabricated",
                  "实验", "测试", "样机", "实测"}
_simulation_kw = {"simulation", "cfd", "fem", "finite element", "numerical",
                  "simulated", "computational", "仿真", "数值模拟", "有限元"}


def _reconstruct_abstract(inverted_index):
    """Reconstruct abstract text from OpenAlex's abstract_inverted_index.

    OpenAlex stores abstracts as a word→positions map:
      {"the": [0, 5], "quick": [1], "brown": [2], ...}
    This reconstructs the original sentence order.

    Returns empty string if no abstract available.
    """
    if not inverted_index:
        return ""
    word_positions = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions[pos] = word
    if not word_positions:
        return ""
    return " ".join(word_positions[i] for i in sorted(word_positions))


# ── API Search Functions ───────────────────────────────────────────────────

def search_semantic_scholar(query, limit=20, use_cache=True):
    """Search Semantic Scholar API.

    Without API key: 1 req/s, 100/5min. With key: 10 req/s, 1000/5min.
    Set S2_API_KEY environment variable for higher limits.
    """
    if use_cache:
        key = _cache_key(query, "semantic_scholar", limit)
        cached = _cache_get(key)
        if cached is not None:
            print(f"  Semantic Scholar: cache hit ({len(cached)} results)", flush=True)
            return cached

    params = urllib.parse.urlencode({
        "q": query,
        "limit": min(limit, 100),
        "fields": "title,authors,externalIds,year,venue,citationCount,influentialCitationCount,abstract"
    })
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
    api_key = os.environ.get("S2_API_KEY", "")
    headers = {"User-Agent": "Hermes/1.0"}
    if api_key:
        headers["x-api-key"] = api_key

    results = []
    data = None
    rate_limited = False
    for attempt in range(4):
        try:
            _throttle_semantic_scholar_if_anonymous(api_key)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 429:
                    rate_limited = True
                    wait = 2 ** attempt
                    print(f"  Semantic Scholar: rate limited, retrying in {wait}s...", flush=True)
                    time.sleep(wait)
                    continue
                data = json.loads(resp.read())
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                rate_limited = True
                wait = 2 ** attempt
                print(f"  Semantic Scholar: rate limited (429), retrying in {wait}s...", flush=True)
                time.sleep(wait)
                continue
            print(f"  Semantic Scholar error: HTTP {e.code}", flush=True)
            return []
        except (urllib.error.URLError, OSError) as e:
            if attempt < 3:
                wait = 2 ** attempt
                print(f"  Semantic Scholar: connection error, retrying in {wait}s...", flush=True)
                time.sleep(wait)
                continue
            print(f"  Semantic Scholar error: {e}", flush=True)
            return []
        except Exception as e:
            print(f"  Semantic Scholar error: {e}", flush=True)
            return []

    if data is None:
        return []

    for p in data.get("data", []):
        ext_ids = p.get("externalIds", {})
        doi = ext_ids.get("DOI", "")
        title = p.get("title", "?")
        year = p.get("year", "?")
        venue = p.get("venue", "?")
        authors = [a.get("name", "?") for a in p.get("authors", [])]
        citations = p.get("citationCount", 0) or 0
        influential_citations = p.get("influentialCitationCount", 0) or 0
        abstract = p.get("abstract", "") or ""
        if doi:
            results.append({
                "doi": doi, "title": title, "year": year, "venue": venue,
                "authors": authors, "citations": citations,
                "influential_citations": influential_citations,
                "abstract": abstract,
                "source": "semantic_scholar"
            })
    if use_cache:
        _cache_set(key, results)

    if rate_limited and not results:
        print("  💡 Semantic Scholar 限流 — 免费申请 API Key 可提升 10 倍额度：",
              flush=True)
        print("     https://www.semanticscholar.org/product/api#api-key-form", flush=True)
        print("     拿到后设置: export S2_API_KEY=\"你的key\"", flush=True)

    return results


def search_semantic_scholar_bulk(query, limit=20, use_cache=True):
    """Search the Boolean-capable Semantic Scholar bulk endpoint."""
    if use_cache:
        key = _cache_key(query, "semantic_scholar_bulk", limit)
        cached = _cache_get(key)
        if cached is not None:
            print(f"  Semantic Scholar bulk: cache hit ({len(cached)} results)", flush=True)
            return cached

    params = urllib.parse.urlencode({
        "query": query,
        "fields": "title,authors,externalIds,year,venue,citationCount,abstract",
    })
    url = f"https://api.semanticscholar.org/graph/v1/paper/search/bulk?{params}"
    api_key = os.environ.get("S2_API_KEY", "")
    headers = {"User-Agent": "Hermes/1.0"}
    if api_key:
        headers["x-api-key"] = api_key
    try:
        _throttle_semantic_scholar_if_anonymous(api_key)
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        print(f"  Semantic Scholar bulk error: {exc}", flush=True)
        return []

    results = []
    for paper in data.get("data", [])[:limit]:
        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI", "")
        if not doi:
            continue
        results.append({
            "doi": doi,
            "title": paper.get("title") or "?",
            "year": paper.get("year") or "?",
            "venue": paper.get("venue") or "?",
            "authors": [author.get("name", "?") for author in paper.get("authors", [])],
            "citations": paper.get("citationCount", 0) or 0,
            "abstract": paper.get("abstract", "") or "",
            "source": "semantic_scholar_bulk",
        })
    if use_cache:
        _cache_set(key, results)
    return results


def search_crossref(query, limit=20, use_cache=True, query_params=None):
    """Search Crossref API. Free, generous rate limits."""
    if use_cache:
        key = _cache_key(query, "crossref", limit, json.dumps(query_params or {}, sort_keys=True))
        cached = _cache_get(key)
        if cached is not None:
            print(f"  Crossref: cache hit ({len(cached)} results)", flush=True)
            return cached
    params_payload = {
        "query.title": query,
        "rows": min(limit, 100),
        "sort": "relevance",
        "order": "desc"
    }
    params_payload.update(query_params or {})
    params_payload["rows"] = min(limit, 100)
    params = urllib.parse.urlencode(params_payload)
    url = f"https://api.crossref.org/works?{params}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Hermes/1.0 (mailto:research@example.com)"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  Crossref error: {e}", flush=True)
        return []

    results = []
    for item in data.get("message", {}).get("items", []):
        doi = item.get("DOI", "")
        title = (item.get("title") or ["?"])[0]
        date_parts = (item.get("published-print") or item.get("issued") or {}).get(
            "date-parts", [["?"]]
        )
        year = date_parts[0][0] if date_parts and date_parts[0] else "?"
        publisher = item.get("publisher", "?")
        authors = []
        for a in item.get("author", []):
            family = a.get("family", "")
            given = a.get("given", "")
            if family:
                authors.append(f"{family}, {given}" if given else family)
        if doi:
            results.append({
                "doi": doi, "title": title, "year": year, "venue": publisher,
                "authors": authors, "citations": 0,
                "abstract": item.get("abstract", "") or "",
                "source": "crossref"
            })
    if use_cache:
        _cache_set(key, results)
    return results


def search_openalex(query, limit=20, use_cache=True, query_params=None):
    """Search OpenAlex API. Free, no key needed."""
    if use_cache:
        key = _cache_key(query, "openalex", limit, json.dumps(query_params or {}, sort_keys=True))
        cached = _cache_get(key)
        if cached is not None:
            print(f"  OpenAlex: cache hit ({len(cached)} results)", flush=True)
            return cached
    params_payload = {
        "search": query,
        "per_page": min(limit, 50),
        "sort": "relevance_score:desc"
    }
    params_payload.update(query_params or {})
    params_payload["per_page"] = min(limit, 50)
    params = urllib.parse.urlencode(params_payload)
    url = f"https://api.openalex.org/works?{params}"

    results = []
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            break
        except (urllib.error.URLError, OSError, ConnectionError) as e:
            if attempt < 3:
                wait = 2 ** attempt
                print(f"  OpenAlex: connection error, retrying in {wait}s...", flush=True)
                time.sleep(wait)
                continue
            print(f"  OpenAlex error: {e}", flush=True)
            return []
        except Exception as e:
            print(f"  OpenAlex error: {e}", flush=True)
            return []

    results = []
    for p in data.get("results", []):
        doi = p.get("doi", "")
        if doi:
            doi = doi.replace("https://doi.org/", "")
        title = p.get("title", "?")
        year = p.get("publication_year", "?")
        venue = ""
        primary_loc = p.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        venue = source.get("display_name", "?")
        authors = []
        for a in p.get("authorships", []):
            name = (a.get("author") or {}).get("display_name", "")
            if name:
                authors.append(name)
        citations = p.get("cited_by_count", 0) or 0
        abstract_index = p.get("abstract_inverted_index")
        abstract = _reconstruct_abstract(abstract_index) if abstract_index else ""
        if doi:
            results.append({
                "doi": doi, "title": title, "year": year, "venue": venue,
                "authors": authors, "citations": citations,
                "abstract": abstract,
                "source": "openalex"
            })
    if use_cache:
        _cache_set(key, results)
    return results


# ── Wanfang Web Search ──────────────────────────────────────────────────

def _build_wanfang_url(query, page=1, page_size=20, language="any"):
    """Build Wanfang search URL with query parameters.

    Uses the SPA-based search endpoint at s.wanfangdata.com.cn/paper,
    which works with CARSI SSO sessions.

    Args:
        query: Search query string.
        page: Page number (1-indexed).
        page_size: Results per page (max 50).
        language: "zh" → add Chinese-only filter to URL;
                  "en"/"any" → no language filter.
    """
    params = {
        "q": query,
        "p": str(page),
        "pageSize": str(min(page_size, 50)),
    }
    # Wanfang SPA supports a language facet via the "lang" parameter.
    # When set to "chi", only Chinese-language papers are returned.
    # This prevents English papers (published in Chinese journals)
    # from appearing in Chinese-language searches — those English
    # papers are difficult to download via the CDP pipeline and
    # should be sourced from OpenAlex/Semantic Scholar/Crossref instead.
    if language == "zh":
        params["lang"] = "chi"
    return WANFANG_SPA_URL + "?" + urllib.parse.urlencode(params)


# ── Wanfang Author Utilities ──────────────────────────────────────────────

def _clean_wanfang_authors(raw):
    """Clean and parse Wanfang author strings.

    Handles dirty fields like:
      - "作者：张三;李四"
      - "[硕士论文]王龙泽机械工程兰州交通大学"
    """
    if not raw:
        return []
    text = re.sub(r'作者[：:]\s*', '', raw).strip()
    text = re.sub(r'^\[(硕士|博士|学位)论文\]', '', text)

    # Thesis format: name + major + school — extract name only
    thesis_m = re.match(r'^([一-龥]{2,4})(?:材料|机械|工程|航空|制造|车辆|控制|力学)', text)
    if thesis_m:
        return [thesis_m.group(1)]

    # Truncate at markers like abstract/keywords/download links
    text = re.split(r'摘要[：:]|关键词[：:]|在线阅读|下载|引用|收藏', text)[0]
    parts = [p.strip() for p in re.split(r'[;；,，、\s]+', text) if p.strip()]
    bad = {'万方数据', '硕士论文', '博士论文', '期刊', '会议', '摘要'}
    return [p for p in parts if p not in bad and 2 <= len(p) <= 30]


def _extract_wanfang_authors_from_text(text):
    """Extract authors from Wanfang result text using known patterns."""
    patterns = [
        r'作者[：:]\s*([^\n]+)',
        r'作者\s+([^\n]+)',
        r'\[(?:硕士|博士)论文\]([^\n]+)',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            authors = _clean_wanfang_authors(m.group(1))
            if authors:
                return authors
    return []


def _parse_wanfang_html(html, max_results):
    """Parse Wanfang search results HTML into paper dicts.

    Uses BeautifulSoup with fallback to regex-based extraction.
    """
    results = []

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        # Try common result container selectors
        items = (soup.select("div.result-item")
                 or soup.select("div.search-result-item")
                 or soup.select("div[class*='result'] li")
                 or soup.select("ul.search-list > li")
                 or [])

        for item in items:
            if len(results) >= max_results:
                break

            # Title: try link text within a heading
            title_el = (item.select_one("h3.title a")
                        or item.select_one("div.title a")
                        or item.select_one("a[href*='detail']"))
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or title == "?":
                continue

            # DOI: look for DOI pattern in text or link
            doi = ""
            doi_el = item.select_one("span.doi a, a[href*='doi']")
            if doi_el:
                doi_text = doi_el.get_text(strip=True)
                doi_match = re.search(r'(10\.\d{4,}/[^\s<"]+)', doi_text)
                if doi_match:
                    doi = doi_match.group(1)
            if not doi:
                # Check any text block for DOI pattern
                doi_match = re.search(r'DOI[:\s]*(10\.\d{4,}/[^\s<"]+)',
                                      item.get_text())
                if doi_match:
                    doi = doi_match.group(1)
            if not doi:
                # Synthetic identifier from title hash
                title_hash = hashlib.md5(title.encode()).hexdigest()[:12]
                doi = f"wanfang.{title_hash}"

            # Authors
            author_el = (
                item.select_one("p.author")
                or item.select_one("div.author")
                or item.select_one("[class*='author']")
                or item.select_one("[class*='creator']")
                or item.select_one("[class*='writer']")
            )
            authors = []
            if author_el:
                authors = _clean_wanfang_authors(author_el.get_text(" ", strip=True))
            if not authors:
                # Fallback: scan full item text for author pattern
                authors = _extract_wanfang_authors_from_text(item.get_text("\n", strip=True))

            # Capture detail page URL (for later author enrichment)
            detail_url = ""
            if title_el.get("href"):
                href = title_el["href"]
                detail_url = href if href.startswith("http") else "https://www.wanfangdata.com.cn" + href

            # Year + venue from source info
            year = 0
            venue = ""
            source_el = (item.select_one("p.source")
                         or item.select_one("div.source-info")
                         or item.select_one("[class*='source']")
                         or item.select_one("[class*='journal']"))
            if source_el:
                source_text = source_el.get_text(strip=True)
                year_match = re.search(r'(\d{4})', source_text)
                if year_match:
                    year = int(year_match.group(1))
                # Venue: first part before the first comma or year
                venue_part = re.split(r'[，,]', source_text)[0].strip()
                if venue_part and not re.match(r'^\d{4}', venue_part):
                    venue = venue_part

            # Citations (optional)
            citations_el = (item.select_one("span.cited-count")
                            or item.select_one("[class*='cited']"))
            citations = 0
            if citations_el:
                cit_match = re.search(r'(\d+)', citations_el.get_text())
                if cit_match:
                    citations = int(cit_match.group(1))

            results.append({
                "doi": doi,
                "title": title,
                "year": year,
                "venue": venue,
                "authors": authors,
                "citations": citations,
                "abstract": "",
                "source": "wanfang",
                "url": detail_url,
            })
    except Exception:
        # Fallback: regex-based extraction
        try:
            _parse_wanfang_html_regex(html, max_results, results)
        except Exception:
            pass

    return results


def _parse_wanfang_html_regex(html, max_results, results):
    """Fallback HTML parser using regex patterns."""
    # Find result blocks by looking for title-anchor patterns
    title_pattern = re.compile(
        r'<a[^>]*href="[^"]*detail[^"]*"[^>]*>([^<]+)</a>', re.IGNORECASE
    )
    year_pattern = re.compile(r'(\d{4})')
    doi_pattern = re.compile(r'DOI[:\s]*(10\.\d{4,}/[^\s<"]+)', re.IGNORECASE)

    for match in title_pattern.finditer(html):
        if len(results) >= max_results:
            break
        title = match.group(1).strip()
        if not title:
            continue

        title_hash = hashlib.md5(title.encode()).hexdigest()[:12]
        doi = f"wanfang.{title_hash}"

        # Search for DOI near this title match
        context = html[match.end():match.end() + 500]
        doi_m = doi_pattern.search(context)
        if doi_m:
            doi = doi_m.group(1)

        year_m = year_pattern.search(context)
        year = int(year_m.group(1)) if year_m else 0

        results.append({
            "doi": doi,
            "title": title,
            "year": year,
            "venue": "",
            "authors": [],
            "citations": 0,
            "abstract": "",
            "source": "wanfang",
        })


def _try_wanfang_ip(query, limit=20, language="any"):
    """Try direct HTTP search to Wanfang via institutional IP.

    Works when on campus / VPN. Returns parsed results on success.
    Returns None if blocked/CAS redirect detected (should try CARSI mode).

    Args:
        language: "zh" adds lang=chi URL param; "en"/"any" skips it.
    """
    url = _build_wanfang_url(query, page=1, page_size=min(limit, 20), language=language)
    headers = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.wanfangdata.com.cn/",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html_bytes = resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308, 401, 403):
            return None
        print(f"  Wanfang Data HTTP error: {e.code}", flush=True)
        return []
    except urllib.error.URLError as e:
        print(f"  Wanfang Data connection error: {e.reason}", flush=True)
        return None
    except Exception as e:
        print(f"  Wanfang Data error: {e}", flush=True)
        return None

    try:
        html = html_bytes.decode("utf-8", errors="replace")
    except Exception:
        html = html_bytes.decode("gbk", errors="replace")

    # Detect login/CAS redirect page.
    # The login keywords often appear deep in JS (6000+ chars),
    # so scan the full HTML but require the page lacks result content.
    has_login_keywords = any(ind in html.lower() for ind in
                            ["登录", "login", "统一身份认证",
                             "CARSI", "fsso", "my.wanfangdata.com.cn/auth"])
    if has_login_keywords:
        # Quick check: does the HTML contain any result-like structure?
        has_results = any(marker in html.lower() for marker in
                         ["result-item", "search-result", "searchList.do",
                          "class=\"title\"", "class=\"author\""])
        if not has_results:
            return None

    results = _parse_wanfang_html(html, limit)
    return results


def _parse_wanfang_results_from_text(text, max_results):
    """Parse Wanfang search results from visible page text.

    The SPA renders results as structured text blocks like:
    1. title
       [authors] [source] [year]
       [abstract...]
       [links and metrics]

    Returns list of paper dicts.
    """
    results = []
    # Split into lines and find result blocks
    lines = text.split("\n")
    i = 0
    while i < len(lines) and len(results) < max_results:
        line = lines[i].strip()
        # Check if line starts with a result number (e.g. "1.", "2.")
        m = re.match(r'^\d+[.．\s]\s*(.+)$', line)
        if m:
            title = m.group(1).strip()
            # Remove leading/trailing brackets or special chars
            title = re.sub(r'^["\'\[\(]+|["\'\]\)]+$', '', title).strip()
            # Skip non-result lines: pagination ("1 / 19", "/ 19 >"), UI noise, very short
            if (not title or len(title) < 4
                    or re.match(r'[\d]*\s*/\s*\d+|^\d+\s*页$', title)
                    or title in ["上一页", "下一页", "首页", "末页", "上一页下一页"]
                    or title.strip().startswith("/")):
                i += 1
                continue

            # Collect the next few lines for author/venue/year info
            info_lines = []
            for j in range(i + 1, min(i + 6, len(lines))):
                next_line = lines[j].strip()
                if not next_line or re.match(r'^\d+[.．\s]', next_line):
                    break  # Next result or end
                info_lines.append(next_line)

            info_text = " ".join(info_lines)

            # Parse year
            year = 0
            year_m = re.search(r'(?:^|\D)(\d{4})(?:\D|$)', info_text)
            if year_m:
                year = int(year_m.group(1))
                if not (1990 <= year <= 2026):
                    year = 0

            # Parse authors — use regex-based extraction instead of guessing
            authors = _extract_wanfang_authors_from_text(info_text)

            # Parse venue
            venue = ""
            venue_m = re.search(r'[-—]\s*(.+?)(?:\d{4}|\[\d)', info_text)
            if venue_m:
                venue = venue_m.group(1).strip().rstrip("，,")

            # Extract DOI if present in the text
            doi = ""
            doi_m = re.search(r'(10\.\d{4,}/[^\s<"]+)', text[max(0, i*50):(i+10)*50])
            if doi_m:
                doi = doi_m.group(1)
            if not doi:
                title_hash = hashlib.md5(title.encode()).hexdigest()[:12]
                doi = f"wanfang.{title_hash}"

            # Extract citation/download counts
            citations = 0
            cit_m = re.search(r'被引[：:](\d+)', info_text)
            if cit_m:
                citations = int(cit_m.group(1))

            # Extract Chinese abstract — Wanfang SPA renders "摘要：..." in results.
            # Exclude "英文摘要" (English abstract) — Chinese only.
            abstract = ""
            abs_m = re.search(r'(?<!英文)摘要[：:]\s*(.+?)(?=\n\d+[.．]|\n被引|\n英文摘要|\Z)', info_text, re.DOTALL)
            if not abs_m:
                # Fallback: look for abstract in individual info_lines
                for il in info_lines:
                    if il.startswith("摘要") and len(il) > 10:
                        abstract = il.replace("摘要：", "").replace("摘要:", "").strip()
                        break
            else:
                abstract = abs_m.group(1).strip()

            results.append({
                "doi": doi,
                "title": title,
                "year": year,
                "venue": venue,
                "authors": authors,
                "citations": citations,
                "abstract": abstract,
                "source": "wanfang",
            })

        i += 1

    return results


def _enrich_wanfang_authors_cdp(ws, results):
    """For Wanfang results with empty authors, navigate to detail page and extract.

    Uses the existing CDP WebSocket connection. Detail page URL is taken
    from the article_url field (injected by DOM extraction) or url field
    (from HTML parser).
    """
    enriched = 0
    for i, r in enumerate(results):
        if r.get("authors"):
            continue
        detail_url = r.get("article_url") or r.get("url", "")
        if not detail_url or "wanfangdata.com.cn" not in detail_url:
            continue

        try:
            ws.send(json.dumps({
                "id": 900 + i, "method": "Page.navigate",
                "params": {"url": detail_url},
            }))
            json.loads(ws.recv())

            # Wait for detail page to load
            for _ in range(8):
                time.sleep(0.8)
                ws.send(json.dumps({
                    "id": 910 + i, "method": "Runtime.evaluate",
                    "params": {"expression": (
                        "document.body ? document.body.innerText.substring(0, 3000) : ''"
                    )},
                }))
                resp = json.loads(ws.recv())
                body = resp.get("result", {}).get("result", {}).get("value", "")
                if len(body) > 200:
                    break

            authors = _extract_wanfang_authors_from_text(body)
            if authors:
                r["authors"] = authors
                enriched += 1
        except Exception:
            continue

    if enriched:
        print(f"  Wanfang CDP: enriched {enriched} authors from detail pages", flush=True)


def _try_wanfang_cdp(query, limit=20, language="any"):
    """Search Wanfang via CDP browser with CARSI SSO session.

    Uses the CDP browser to navigate to the SPA search at
    s.wanfangdata.com.cn/paper?q=... The CAS authentication
    flow happens automatically as the browser session is already
    authenticated. Results are extracted from the rendered page
    innerText for reliable parsing.

    Returns parsed results or None if CDP browser unavailable.

    Args:
        language: "zh" adds lang=chi URL param + post-search title filter;
                  "en"/"any" skips filtering.
    """
    try:
        from cdp_utils import check_cdp
        if not check_cdp(WANFANG_CDP_PORT):
            return None
    except Exception:
        return None

    try:
        import websocket
        targets = json.loads(
            urllib.request.urlopen(
                f"http://127.0.0.1:{WANFANG_CDP_PORT}/json"
            ).read()
        )
        page_target = _pick_cdp_page_target(
            targets,
            preferred_markers=[
                "wanfangdata.com.cn",
                "s.wanfangdata.com.cn",
                "万方",
            ],
        )
        if not page_target:
            return None

        wu = page_target["webSocketDebuggerUrl"]
        ws = websocket.create_connection(wu, timeout=10)

        # Navigate to SPA search URL
        search_url = _build_wanfang_url(query, page=1, page_size=min(limit, 20), language=language)
        ws.send(json.dumps({
            "id": 1,
            "method": "Page.navigate",
            "params": {"url": search_url},
        }))
        resp = json.loads(ws.recv())
        if "error" in resp:
            ws.close()
            return None

        # Wait for SPA to load and render search results
        # The SPA takes time to fetch data via AJAX after the shell loads
        timeout = time.time() + 15
        max_wait = 15
        last_body_len = 0
        stable_for = 0

        for _ in range(max_wait):
            time.sleep(1)

            # Check body text length — if stable and > 1000, data is ready
            ws.send(json.dumps({
                "id": 2,
                "method": "Runtime.evaluate",
                "params": {"expression": "document.body ? document.body.innerText.length : 0"},
            }))
            r = json.loads(ws.recv())
            body_len = r.get("result", {}).get("result", {}).get("value", 0)

            if body_len > 2000 and body_len == last_body_len:
                stable_for += 1
                if stable_for >= 2:  # Stable for 2 seconds → data loaded
                    break
            else:
                stable_for = 0

            last_body_len = body_len

            if time.time() > timeout:
                break

        # Extract structured results from Vue component DOM
        ws.send(json.dumps({
            "id": 10,
            "method": "Runtime.evaluate",
            "params": {"expression": f"""
(() => {{
  // Check for login page
  var body = document.body ? document.body.innerText : '';
  var isLogin = body.indexOf('统一身份认证') >= 0 ||
                body.indexOf('CARSI') >= 0 ||
                body.indexOf('fsso') >= 0;

  var results = [];
  // Use global selector — .normal-list may have nested wrappers
  var items = document.querySelectorAll('.title-area');

  for (var i = 0; i < items.length && results.length < {limit}; i++) {{
    var ta = items[i];

    // Title
    var titleEl = ta.querySelector('.title');
    if (!titleEl) continue;
    var title = titleEl.innerText.trim();
    if (!title || title.length < 3) continue;

    // Paper ID → construct detail page URL
    var idEl = ta.querySelector('.title-id-hidden');
    var paperId = idEl ? idEl.innerText.trim() : '';
    // Title hash for synthetic DOI and indexing
    var titleHash = '';
    for (var j = 0; j < Math.min(title.length, 12); j++) {{
      titleHash += title.charCodeAt(j).toString(16);
    }}

    // Find the parent card/item container — walk up until we find one with .authors
    var card = ta.parentElement;
    for (var k = 0; k < 6 && card && !card.querySelector('.authors'); k++) {{
      card = card.parentElement;
    }}
    if (!card) card = ta.parentElement;

    // Authors — each in <span class="authors">Name</span>
    var authorEls = card.querySelectorAll('.authors');
    var authors = [];
    authorEls.forEach(function(a) {{
      var name = a.innerText.trim();
      // Filter out non-name strings (dates, issue numbers, separator symbols)
      if (name && name !== 'Unknown' &&
          !/^\\d/.test(name) &&          // skip '2025年7期'
          !/^[等和及与,，;；]$/.test(name) &&  // skip single separator chars
          name.length >= 2 && name.length <= 10) {{
        authors.push(name);
      }}
    }});

    // Paper type: <span class="essay-type">期刊论文/硕士论文</span>
    var typeEl = card.querySelector('.essay-type');
    var essayType = typeEl ? typeEl.innerText.trim() : '';

    // Journal or institution: <span class="periodical-title"> for journals, <span class="org"> for theses
    var journalEl = card.querySelector('.periodical-title');
    var journal = journalEl ? journalEl.innerText.trim().replace(/^[《〈](.+)[》〉]$/, '$1') : '';
    if (!journal) {{
      // Thesis paper — get institution from <span class="org">
      var orgEl = card.querySelector('.org');
      if (orgEl) {{
        journal = orgEl.innerText.trim().replace(/\\d{4}$/, '').trim();
        // If org contains year, use only the institution name
        var orgSpan = orgEl.querySelector('span');
        if (orgSpan) journal = orgSpan.innerText.trim();
      }}
    }}

    // Year — from card text, find 4-digit year
    var cardText = (card.innerText || '').replace(/\\n/g, ' ');
    var yearMatch = cardText.match(/(\\d{{4}})/);
    var year = 0;

    // Abstract — walk up to find the result row then check for abstract
    var row = card;
    for (var k2 = 0; k2 < 6 && row && !row.querySelector('[class*=\"abstract\"]'); k2++) {{
      row = row.parentElement;
    }}
    var absEl = row ? row.querySelector('[class*=\"abstract\"], [class*=\"desc\"]') : null;
    var abstract = absEl ? absEl.innerText.trim() : '';
    // Fallback: look for 摘要：in card text
    if (!abstract) {{
      var absMatch = cardText.match(/(?<!英文)摘要[：:]\\s*(.+?)(?=\\n\\d+[.．]|\\n\\[|\\Z)/);
      if (absMatch) abstract = absMatch[1].trim();
    }}
    // Validate year range (filter out alloy numbers like 5052)
    if (yearMatch) {{
      var y = parseInt(yearMatch[1]);
      if (y >= 1990 && y <= 2026) year = y;
    }}

    results.push({{
      doi: 'wanfang.' + titleHash,
      title: title,
      year: year,
      venue: journal || '万方数据',
      authors: authors,
      citations: 0,
      abstract: abstract,
      source: 'wanfang',
      // Build correct URL: d.wanfangdata.com.cn/thesis/{id} or periodical/{id}
      article_url: paperId ? (
        paperId.indexOf('thesis_') === 0
          ? 'https://d.wanfangdata.com.cn/thesis/' + paperId.replace('thesis_', '')
          : 'https://d.wanfangdata.com.cn/periodical/' + paperId.replace('periodical_', '')
      ) : '',
      _paper_id: paperId,
    }});
  }}

  return JSON.stringify({{
    count: results.length,
    isLogin: isLogin,
    results: results,
  }});
}})()
            """},
        }))
        r = json.loads(ws.recv())
        ws.close()

        raw_val = r.get("result", {}).get("result", {}).get("value", "{}")
        try:
            parsed = json.loads(raw_val) if isinstance(raw_val, str) else raw_val
        except Exception:
            return None

        if isinstance(parsed, dict) and parsed.get("error"):
            return None
        if isinstance(parsed, dict) and parsed.get("isLogin"):
            print("  Wanfang Data: CDP mode — still on login page. "
                  "Please complete CARSI login in the browser.", flush=True)
            return None

        if isinstance(parsed, dict) and "results" in parsed:
            results = parsed["results"]
            print(f"  Wanfang Data CDP: {len(results)} results found", flush=True)
        else:
            return []

        # Post-search language filter (safety net — even with lang=chi param,
        # some English papers from Chinese journals may still appear.)
        if language == "zh":
            results, removed = _filter_by_language(results, "zh")
            if removed:
                print(f"  Wanfang Data CDP: filtered {removed} English-language results", flush=True)

        return results

    except Exception as e:
        print(f"  Wanfang Data CDP error: {e}", flush=True)
        try:
            ws.close()
        except Exception:
            pass
        return None


def search_wanfang(query, limit=20, use_cache=True, language="any"):
    """Search Wanfang Data via institutional web access (no API key needed).

    Two modes:
      1. IP mode (auto): Direct HTTP GET to searchList.do
         Works when on-campus or on institutional VPN.
      2. CARSI mode (fallback): CDP-assisted session cookies
         Requires user to log in via CARSI SSO in CDP browser.

    Papers without DOIs receive a synthetic 'wanfang.{title_md5[:12]}'
    identifier so they pass through the standard --include-no-doi filter.

    Args:
        query: Search query string.
        limit: Max results (default: 20).
        use_cache: If True, check/write disk cache.
        language: "zh" → lang=chi URL param + post-search title filter;
                  "en"/"any" → no filtering.

    Returns:
        List of paper dicts with keys: doi, title, year, venue, authors,
        citations, source.
    """
    # Cache check — include language in cache key to avoid cross-contamination
    cache_key = _cache_key(query, "wanfang", limit, language)
    if use_cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            print(f"  Wanfang Data: cache hit ({len(cached)} results)", flush=True)
            return cached

    # Try IP mode first (on-campus or VPN)
    print("  Wanfang Data: trying IP-direct mode...", flush=True)
    results = _try_wanfang_ip(query, limit, language=language)

    if results is not None:
        # IP mode succeeded (may be 0 results — that's fine)
        if use_cache:
            _cache_set(cache_key, results)
        return results

    # IP mode failed → try CARSI mode with CDP browser
    print("  Wanfang Data: IP access not available, trying CARSI mode...", flush=True)
    results = _try_wanfang_cdp(query, limit, language=language)

    if results is not None:
        if use_cache:
            _cache_set(cache_key, results)
        return results

    # CDP browser or CARSI session not available
    print("", flush=True)
    print("  ╔══════════════════════════════════════════════════════════════╗", flush=True)
    print("  ║  万方校外访问 — CARSI 机构登录                             ║", flush=True)
    print("  ╠══════════════════════════════════════════════════════════════╣", flush=True)
    print("  ║ 1. 启动 CDP Chrome:                                        ║", flush=True)
    print("  ║    scripts/start_cdp_chrome.sh                             ║", flush=True)
    print("  ║ 2. 在浏览器中访问:                                         ║", flush=True)
    print("  ║    https://fsso.wanfangdata.com.cn                         ║", flush=True)
    print("  ║ 3. 选择您的学校 → 完成统一身份认证登录                      ║", flush=True)
    print("  ║ 4. 保留浏览器窗口，重新执行检索                              ║", flush=True)
    print("  ╚══════════════════════════════════════════════════════════════╝", flush=True)
    return []


# ── CNKI Web Search ─────────────────────────────────────────────────────

CNKI_STRATEGY_MAP = {
    "relevance": "(FFD,'RANK') desc",
    "recent":    "(发表时间,'TIME') desc",
    "cited":     "(被引频次,'INTEGER') desc",
}

def _build_cnki_post_data(query, page=1, sorttype="", language="any"):
    """Build POST form data for CNKI's SearchHandler.ashx.

    The old HTTP interface uses the same params as verified by
    mohuishou/PaperDownload (Go) and itstyren/CNKI-download (Python).

    Args:
        query: Search query string.
        page: Page number (unused; kept for API stability).
        sorttype: CNKI sort expression (e.g., "(发表时间,'TIME') desc").
        language: "zh" → disable Chinese-English expansion (isinEn=0);
                  "en"/"any" → enable expansion (isinEn=1, default).
    """
    # When searching for Chinese papers, disable the Chinese-English
    # cross-language expansion so CNKI doesn't return English papers
    # that happen to match the topic keywords.  English papers in CNKI
    # are hard to download via the CDP pipeline and should be sourced
    # from OpenAlex/Semantic Scholar instead.
    isin_en = "0" if language == "zh" else "1"
    data = {
        "action": "",
        "NaviCode": "*",
        "ua": "1.21",
        "isinEn": isin_en,
        "PageName": "ASP.brief_default_result_aspx",
        "DbPrefix": "SCDB",
        "DbCatalog": "中国学术期刊网络出版总库",
        "ConfigFile": "CJFQ.xml",
        "db_opt": "CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD",
        "txt_1_sel": "SU",
        "txt_1_value1": query,
        "txt_1_relation": "#CNKI_AND",
        "txt_1_special1": "%",
        "his": "0",
    }
    data["sorttype"] = sorttype if sorttype else "(发表时间,'TIME') desc"
    return data


def _parse_cnki_html(html, max_results):
    """Parse CNKI search results HTML into paper dicts.

    Old interface returns a table.GridTableContent with columns:
    0: checkbox, 1: title+link, 2: author, 3: source, 4: date,
    5: database, 6: (skip), 7: download count
    """
    results = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return results

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="GridTableContent")
    if not table:
        return results

    rows = table.find_all("tr")
    # Skip header row (first tr)
    for tr in rows[1:]:
        if len(results) >= max_results:
            break
        try:
            tds = tr.find_all("td")
            if len(tds) < 6:
                continue

            # Title + link
            title_el = tds[1].find("a") if len(tds) > 1 else None
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or title == "?":
                continue

            # Article URL from title link href (detail page, used by Step 5 download)
            article_url = ""
            if title_el.get("href"):
                href = title_el["href"]
                article_url = "http://kns.cnki.net/kns/brief/" + href if href.startswith("brief") else href

            # Download URL from briefDl_D link
            download_url = ""
            dl_link = tds[1].find("a", class_="briefDl_D") if len(tds) > 1 else None
            if dl_link and dl_link.get("href"):
                download_url = "http://kns.cnki.net/kns/brief/" + dl_link["href"]

            # DOI — CNKI rarely has DOIs on the results page
            doi = ""
            # Use export ID as secondary identifier
            export_id = ""
            cb = tr.find("input", type="checkbox")
            if cb and cb.get("value"):
                export_id = cb["value"]

            # Generate synthetic DOI from title
            title_hash = hashlib.md5(title.encode(errors="replace")).hexdigest()[:12]
            doi = f"cnki.{title_hash}"

            # Authors
            authors_raw = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            authors = [a.strip() for a in re.split(r'[;；]', authors_raw) if a.strip()[:1]]

            # Source/journal
            venue = tds[3].get_text(strip=True) if len(tds) > 3 else ""

            # Date
            year = 0
            date_raw = tds[4].get_text(strip=True) if len(tds) > 4 else ""
            year_m = re.search(r"(\d{4})", date_raw)
            if year_m:
                year = int(year_m.group(1))

            # Citations (from text)
            citations = 0

            results.append({
                "doi": doi,
                "title": title,
                "year": year,
                "venue": venue,
                "authors": authors,
                "citations": citations,
                "abstract": "",
                "source": "cnki",
                "article_url": article_url,
                "_download_url": download_url,
                "_export_id": export_id,
            })
        except Exception:
            continue

    return results


def _try_cnki_ip(query, limit=20, strategy="", language="any"):
    """Search CNKI via old HTTP POST/GET interface (campus IP / VPN).

    Uses urllib with CookieJar for session management.
    Returns parsed results on success, None if blocked/CAS redirect.

    Args:
        language: "zh" disables isinEn expansion; "en"/"any" keeps it on.
    """
    import http.cookiejar

    headers = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"),
        "Accept": ("text/html,application/xhtml+xml,application/xml;"
                   "q=0.9,*/*;q=0.8"),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj)
    )

    # Step 1: GET to establish initial session cookie
    try:
        req = urllib.request.Request(
            "http://kns.cnki.net/kns/brief/result.aspx",
            headers=headers
        )
        with opener.open(req, timeout=15) as resp:
            resp.read()  # consume to set cookies
    except Exception:
        return None

    # Step 2: POST to SearchHandler.ashx
    sort_expr = CNKI_STRATEGY_MAP.get(strategy, "(发表时间,'TIME') desc")
    post_data = _build_cnki_post_data(query, sorttype=sort_expr, language=language)
    try:
        req = urllib.request.Request(
            CNKI_SEARCH_HANDLER,
            data=urllib.parse.urlencode(post_data).encode("utf-8"),
            headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
        )
        with opener.open(req, timeout=15) as resp:
            pagename = resp.read().decode("utf-8", errors="replace").strip()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308, 401, 403):
            return None
        return None
    except Exception:
        return None

    if not pagename:
        return None

    # Step 3: GET the brief.aspx result page
    encoded_query = urllib.parse.quote(query)
    page_size = min(limit, 20)
    result_url = (
        f"{CNKI_OLD_SEARCH_URL}?pagename={urllib.parse.quote(pagename)}"
        f"&keyValue={encoded_query}&S=1&sorttype={urllib.parse.quote(sort_expr)}"
        f"&recordsperpage={page_size}"
    )
    try:
        req = urllib.request.Request(
            result_url,
            headers={**headers, "Referer": CNKI_SEARCH_HANDLER},
        )
        with opener.open(req, timeout=15) as resp:
            html_bytes = resp.read()
    except Exception:
        return None

    try:
        html = html_bytes.decode("utf-8", errors="replace")
    except Exception:
        html = html_bytes.decode("gbk", errors="replace")

    # Detect captcha or login redirect
    if "tcaptcha_transform_dy" in html.lower():
        return None  # captcha triggered, fall back to CDP mode
    if "统一身份认证" in html or "CARSI" in html:
        return None  # not on campus IP

    results = _parse_cnki_html(html, limit)

    # Step 4: Handle pagination if limit > 20
    if len(results) < limit:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            count_mark = soup.select_one(".countPageMark")
            if count_mark:
                parts = count_mark.get_text(strip=True).split("/")
                if len(parts) == 2:
                    total_pages = int(parts[1])
                    query_id = ""
                    # Extract QueryID from URL or page
                    qid_m = re.search(r"QueryID=(\d+)", result_url)
                    if qid_m:
                        query_id = qid_m.group(1)

                    for pg in range(2, total_pages + 1):
                        if len(results) >= limit:
                            break
                        page_url = (
                            f"{CNKI_OLD_SEARCH_URL}?QueryID={query_id}"
                            f"&curpage={pg}&tpagemode=L&dbPrefix=SCDB"
                            f"&recordsperpage={page_size}&sorttype={urllib.parse.quote(sort_expr)}"
                            f"&keyValue={encoded_query}&S=1"
                        )
                        try:
                            req = urllib.request.Request(
                                page_url,
                                headers={**headers, "Referer": result_url},
                            )
                            with opener.open(req, timeout=15) as resp:
                                pg_html = resp.read().decode("utf-8", errors="replace")
                            pg_results = _parse_cnki_html(pg_html, limit - len(results))
                            results.extend(pg_results)
                        except Exception:
                            break
        except Exception:
            pass

    return results


def _try_cnki_cdp(query, limit=20, language="any"):
    """Search CNKI via CDP browser using the old AdvSearch interface.

    Verified flow (2026-06-06):
      1. navigate_page → https://kns.cnki.net/kns/AdvSearch?classid=7NS01R8M
      2. Wait for #txt_1_value1 to be DOM-ready
      3. Fill #txt_1_value1 with query, dispatch input event
      4. Click div.search with mouse events (mousedown+mouseup+click)
      5. Poll for a.fz14 links in #gridTable (AJAX results load inline)
      6. Extract titles, authors, journals, dates from <tr> rows

    The old interface renders results inside #gridTable via AJAX.
    No captcha issues unlike the new kns8s SPA.
    Falls back gracefully if CDP browser is unavailable.

    Args:
        language: "zh" applies post-search title language filtering;
                  "en"/"any" skips filtering.
    """
    # Brief delay to avoid triggering CNKI anti-bot rate limiting
    time.sleep(3)

    try:
        from cdp_utils import check_cdp
        if not check_cdp(CNKI_CDP_PORT):
            return None
    except Exception:
        return None

    try:
        import websocket
        targets = json.loads(
            urllib.request.urlopen(
                f"http://127.0.0.1:{CNKI_CDP_PORT}/json"
            ).read()
        )
        page_target = _pick_cdp_page_target(
            targets,
            preferred_markers=[
                "kns.cnki.net",
                "cnki.net",
                "中国知网",
                "cnki",
            ],
        )
        if not page_target:
            return None

        wu = page_target["webSocketDebuggerUrl"]
        ws = websocket.create_connection(wu, timeout=10)

        # Step 1: Navigate to old AdvSearch interface
        ws.send(json.dumps({
            "id": 1, "method": "Page.navigate",
            "params": {"url": CNKI_ADV_SEARCH_URL},
        }))
        json.loads(ws.recv())

        # Step 2: Wait for form to be ready (#txt_1_value1 present)
        for _ in range(12):
            time.sleep(1)
            ws.send(json.dumps({
                "id": 2, "method": "Runtime.evaluate",
                "params": {"expression": "!!document.querySelector('#txt_1_value1')"},
            }))
            r = json.loads(ws.recv())
            ready = r.get("result", {}).get("result", {}).get("value", False)
            if ready:
                break

        # Step 3: Fill search form and click search button
        escaped_query = query.replace("\\", "\\\\").replace("'", "\\'")
        fill_js = (
            f"var inp=document.querySelector('#txt_1_value1');"
            f"if(!inp){{'error:no_input';}}"
            f"else{{inp.value='{escaped_query}';"
            f"inp.dispatchEvent(new Event('input',{{bubbles:true}}));"
            f"inp.dispatchEvent(new Event('change',{{bubbles:true}}));"
            f"var b=document.querySelector('div.search');"
            f"if(!b){{'error:no_btn';}}"
            f"else{{"
            f"b.dispatchEvent(new MouseEvent('mousedown',{{bubbles:true}}));"
            f"b.dispatchEvent(new MouseEvent('mouseup',{{bubbles:true}}));"
            f"b.dispatchEvent(new MouseEvent('click',{{bubbles:true}}));"
            f"'clicked';}}}}"
        )
        ws.send(json.dumps({
            "id": 3, "method": "Runtime.evaluate",
            "params": {"expression": fill_js},
        }))
        r = json.loads(ws.recv())
        click_result = r.get("result", {}).get("result", {}).get("value", "")

        # Step 4: Wait for AJAX results to render (a.fz14 links appear in #gridTable)
        result_count = 0
        for i in range(20):
            time.sleep(1)
            ws.send(json.dumps({
                "id": 4, "method": "Runtime.evaluate",
                "params": {"expression": (
                    "var g=document.querySelector('#gridTable');"
                    "g ? g.querySelectorAll('a.fz14').length : 0"
                )},
            }))
            r = json.loads(ws.recv())
            result_count = r.get("result", {}).get("result", {}).get("value", 0)
            if result_count > 0:
                break
            # Also check for "条结果" anywhere in body (fallback)
            if i > 3:
                ws.send(json.dumps({
                    "id": 5, "method": "Runtime.evaluate",
                    "params": {"expression": (
                        "document.body.innerText.includes('条结果')"
                    )},
                }))
                r2 = json.loads(ws.recv())
                has_results = r2.get("result", {}).get("result", {}).get("value", False)
                if has_results:
                    break

        if result_count == 0:
            ws.close()
            print(f"  CNKI CDP: search returned 0 results", flush=True)
            return []

        # Step 5: Extract results from #gridTable
        extract_js = f"""
(() => {{
  var grid = document.querySelector('#gridTable');
  if (!grid) return JSON.stringify({{error: 'no_grid'}});

  var trs = grid.querySelectorAll('tr');
  var results = [];
  for (var i = 0; i < Math.min(trs.length, 40) && results.length < {limit}; i++) {{
    var tr = trs[i];
    var titleA = tr.querySelector('a.fz14');
    if (!titleA) continue;
    var title = titleA.innerText.trim();
    if (!title || title.length < 3) continue;

    var tds = tr.querySelectorAll('td');
    var authorLinks = tr.querySelectorAll('a.KnowledgeNetLink');
    var authors = Array.from(authorLinks).map(function(a) {{
      return a.innerText.trim();
    }});

    // Journal: typically td[3] or the first <a> in the source column
    var journalA = (tds.length > 3) ? tds[3].querySelector('a') : null;
    var journal = journalA ? journalA.innerText.trim() : '';
    // If no link in td[3], try raw text
    if (!journal && tds.length > 3) {{
      journal = tds[3].innerText.trim().split('\\n')[0];
    }}
    var date = (tds.length > 4) ? tds[4].innerText.trim() : '';
    var year = 0;
    var ym = date.match(/(\\d{{4}})/);
    if (ym) year = parseInt(ym[1]);

    // Downloads: td[7]
    var dls = (tds.length > 7) ? tds[7].innerText.trim() : '';
    var citations = parseInt(dls) || 0;

    // Generate synthetic DOI
    var titleHash = '';
    for (var j = 0; j < 12 && j < title.length; j++) {{
      var c = title.charCodeAt(j);
      titleHash += c.toString(16);
    }}
    var doi = 'cnki.' + titleHash;

    results.push({{
      doi: doi,
      title: title,
      year: year,
      venue: journal,
      authors: authors,
      citations: citations,
      source: 'cnki',
      _href: titleA.href,
      _date: date,
    }});
  }}
  return JSON.stringify({{count: results.length, results: results}});
}})()
"""
        ws.send(json.dumps({
            "id": 6, "method": "Runtime.evaluate",
            "params": {"expression": extract_js},
        }))
        r = json.loads(ws.recv())

        raw_val = r.get("result", {}).get("result", {}).get("value", "{}")
        parsed = json.loads(raw_val) if isinstance(raw_val, str) else raw_val
        if isinstance(parsed, dict) and "results" in parsed:
            results = parsed["results"]
            # Expose _href as article_url for Step 5 download
            for r in results:
                if r.get("_href") and not r.get("article_url"):
                    r["article_url"] = r["_href"]
            print(f"  CNKI CDP: {len(results)} results found", flush=True)
        elif isinstance(parsed, dict) and "error" in parsed:
            ws.close()
            return None
        else:
            ws.close()
            return []

        # Step 6: Navigate to each paper's detail page to extract abstract.
        # Detail-page extraction is best-effort only: search hits are still
        # usable for Step 4 even if individual abstract pages fail or the
        # session gets redirected mid-run.
        try:
            _extract_cnki_abstracts(ws, results, limit)
        except Exception as e:
            print(f"  CNKI CDP: abstract enrichment skipped ({e})", flush=True)
        ws.close()

        # Post-search language filter (safety net — CDP mode doesn't use
        # _build_cnki_post_data's isinEn parameter, so we rely on title
        # language detection to catch English papers that leak through.)
        if language == "zh":
            results, removed = _filter_by_language(results, "zh")
            if removed:
                print(f"  CNKI CDP: filtered {removed} English-language results", flush=True)

        return results

    except Exception as e:
        print(f"  CNKI CDP error: {e}", flush=True)
        try:
            ws.close()
        except Exception:
            pass
        return None


def _extract_cnki_abstracts(ws, results, limit):
    """For each CNKI search result, navigate to detail page and extract abstract.

    Navigates to kcms2/article/abstract pages sequentially,
    extracts .abstract-text content, and populates the result dicts.
    """
    collected = 0
    for i, r in enumerate(results):
        if r.get("abstract"):
            collected += 1
            continue  # already has abstract (e.g., from cache)
        href = r.get("_href", "")
        if not href or "kcms2" not in href:
            continue
        if collected >= limit:
            break

        # Navigate to paper detail page
        ws.send(json.dumps({
            "id": 100 + i, "method": "Page.navigate",
            "params": {"url": href},
        }))
        json.loads(ws.recv())

        # Wait for detail page to load (.abstract-text or .brief h1)
        abstract_text = ""
        for _ in range(10):
            time.sleep(1)
            ws.send(json.dumps({
                "id": 200 + i, "method": "Runtime.evaluate",
                "params": {"expression": (
                    "var a=document.querySelector('.abstract-text');"
                    "a?a.innerText.trim():''"
                )},
            }))
            resp = json.loads(ws.recv())
            abstract_text = resp.get("result", {}).get("result", {}).get("value", "")
            if abstract_text:
                break
            # Fallback: check if title loaded
            ws.send(json.dumps({
                "id": 300 + i, "method": "Runtime.evaluate",
                "params": {"expression": (
                    "var h=document.querySelector('.brief h1');"
                    "h?h.innerText.trim():''"
                )},
            }))
            resp = json.loads(ws.recv())
            title_text = resp.get("result", {}).get("result", {}).get("value", "")
            if title_text and "网络首发" not in title_text:
                continue  # page loaded but no abstract yet, keep waiting

        if abstract_text:
            # Also grab keywords
            ws.send(json.dumps({
                "id": 400 + i, "method": "Runtime.evaluate",
                "params": {"expression": (
                    "Array.from(document.querySelectorAll('p.keywords a'))"
                    ".map(function(a){return a.innerText.replace(/;$/,'').trim()})"
                    ".join('; ')"
                )},
            }))
            kw_resp = json.loads(ws.recv())
            keywords = kw_resp.get("result", {}).get("result", {}).get("value", "")

            r["abstract"] = abstract_text
            if keywords:
                r["_keywords"] = keywords
            collected += 1

        time.sleep(0.5)


def search_cnki(query, limit=20, use_cache=True, strategy="", language="any"):
    """Search CNKI (中国知网) for Chinese academic papers.

    Two modes:
      1. CDP mode (primary): SPA browser automation via kns8s.
         Requires CDP Chrome running on port 9223 by default.
         Supports search via browser automation (no captcha issues).
      2. IP mode (legacy fallback, likely dead): Old HTTP POST/GET via
         SearchHandler.ashx. Works on-campus if old interface still available.

    Papers without DOIs receive a synthetic 'cnki.{title_md5[:12]}' identifier.

    Args:
        query: Search query string (Chinese).
        limit: Max results (default: 20).
        use_cache: If True, check/write disk cache.
        strategy: Sort order — unused in CDP mode (SPA default sort).
        language: "zh" → disable isinEn expansion + post-search title filter;
                  "en"/"any" → no filtering.

    Returns:
        List of paper dicts with keys: doi, title, year, venue, authors,
        citations, source.
    """
    cache_key = _cache_key(query, "cnki", limit, strategy + language)
    if use_cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            print(f"  CNKI: cache hit ({len(cached)} results)", flush=True)
            return cached

    # Try CDP mode first (kns8s SPA, requires running Chrome).
    # CNKI occasionally returns an empty grid even when the same browser
    # session can succeed a moment later, so treat 0-result searches as
    # transient and retry a small fixed number of times.
    print("  CNKI: trying CDP mode...", flush=True)
    results = None
    for attempt in range(1, CNKI_CDP_MAX_ATTEMPTS + 1):
        results = _try_cnki_cdp(query, limit, language=language)
        if results is None:
            break
        if results:
            print(f"  CNKI CDP mode: {len(results)} results", flush=True)
            if use_cache:
                _cache_set(cache_key, results)
            return results
        if attempt < CNKI_CDP_MAX_ATTEMPTS:
            print(
                f"  CNKI CDP mode: 0 results on attempt {attempt}/{CNKI_CDP_MAX_ATTEMPTS}, retrying...",
                flush=True,
            )
            time.sleep(CNKI_CDP_RETRY_WAIT_SECONDS)

    if results is not None:
        print(
            f"  CNKI CDP mode: 0 results after {CNKI_CDP_MAX_ATTEMPTS} attempts",
            flush=True,
        )
        if use_cache:
            _cache_set(cache_key, results)
        return results

    # CDP failed
    print("", flush=True)
    print("  ╔══════════════════════════════════════════════════════════════╗",
          flush=True)
    print("  ║  CNKI 检索失败 — 需要 CDP Chrome                            ║",
          flush=True)
    print("  ╠══════════════════════════════════════════════════════════════╣",
          flush=True)
    print(f"  ║ 请确保 CDP Chrome 正在运行（端口 {CNKI_CDP_PORT}）：                   ║",
          flush=True)
    print("  ║   scripts/start_cdp_chrome.sh                               ║",
          flush=True)
    print("  ║                                                              ║",
          flush=True)
    print("  ║ 然后在浏览器中访问:                                         ║",
          flush=True)
    print("  ║   https://www.cnki.net                                      ║",
          flush=True)
    print("  ║ 完成 CARSI 机构认证或账号登录后重试                          ║",
          flush=True)
    print("  ╚══════════════════════════════════════════════════════════════╝",
          flush=True)
    return []


# ── Source Registration ──────────────────────────────────────────────────

SOURCE_FUNCTIONS = {
    "semantic_scholar": search_semantic_scholar,
    "semantic_scholar_bulk": search_semantic_scholar_bulk,
    "crossref": search_crossref,
    "openalex": search_openalex,
    "wanfang": search_wanfang,
    "cnki": search_cnki,
}

SOURCE_ALIASES = {
    "semantic": "semantic_scholar",
    "ss": "semantic_scholar",
    "semantic_bulk": "semantic_scholar_bulk",
    "ss_bulk": "semantic_scholar_bulk",
    "cr": "crossref",
    "oa": "openalex",
    "wf": "wanfang",
    "cn": "cnki",
}


# ── Citation Network Expansion ─────────────────────────────────────────────

def fetch_citation_network(doi, refs_limit=30, cited_by_limit=50, existing_dois=None):
    """Fetch forward (cited_by) and backward (references) citations for a DOI.

    Uses OpenAlex API to resolve the DOI to a work ID, then fetches the
    citation network in both directions.

    Args:
        doi: DOI string (with or without 'https://doi.org/' prefix).
        refs_limit: Max backward references to fetch (default: 30).
        cited_by_limit: Max forward citations to fetch (default: 50).
        existing_dois: set of DOIs to exclude from results (already in KG).

    Returns:
        List of flat paper dicts (same format as search functions) with
        source="openalex_citation_network".
    """
    existing_dois = existing_dois or set()
    doi_clean = doi.strip().replace("https://doi.org/", "")

    # Step 1: Resolve DOI to OpenAlex work ID
    resolve_url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi_clean)}"
    req = urllib.request.Request(resolve_url, headers={"User-Agent": "Hermes/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            work = json.loads(resp.read())
    except Exception as e:
        print(f"  citation-network: DOI resolve error for {doi_clean} — {e}", flush=True)
        return []

    oa_id = work.get("id", "")
    if not oa_id:
        print(f"  citation-network: no OpenAlex ID for {doi_clean}", flush=True)
        return []

    # Remove https://openalex.org/ prefix to get clean ID for filter
    oa_id_clean = oa_id.replace("https://openalex.org/", "")

    results = []

    # Step 2: Fetch backward references (papers THIS paper cites)
    refs_url = (
        f"https://api.openalex.org/works"
        f"?filter=cites:{oa_id_clean}"
        f"&per_page={min(refs_limit, 50)}"
        f"&sort=cited_by_count:desc"
    )
    try:
        with urllib.request.urlopen(
            urllib.request.Request(refs_url, headers={"User-Agent": "Hermes/1.0"}),
            timeout=15,
        ) as resp:
            refs_data = json.loads(resp.read())
    except Exception as e:
        print(f"  citation-network: refs fetch error — {e}", flush=True)
        refs_data = {}

    for p in refs_data.get("results", []):
        p_doi = (p.get("doi") or "").replace("https://doi.org/", "")
        if p_doi and p_doi not in existing_dois:
            results.append(_openalex_work_to_dict(p, "openalex_citation_network"))

    # Step 3: Fetch forward citations (papers that cite THIS paper)
    cited_by_url = (
        f"https://api.openalex.org/works"
        f"?filter=cited_by:{oa_id_clean}"
        f"&per_page={min(cited_by_limit, 50)}"
        f"&sort=cited_by_count:desc"
    )
    try:
        with urllib.request.urlopen(
            urllib.request.Request(cited_by_url, headers={"User-Agent": "Hermes/1.0"}),
            timeout=15,
        ) as resp:
            cited_data = json.loads(resp.read())
    except Exception as e:
        print(f"  citation-network: cited_by fetch error — {e}", flush=True)
        cited_data = {}

    for p in cited_data.get("results", []):
        p_doi = (p.get("doi") or "").replace("https://doi.org/", "")
        if p_doi and p_doi not in existing_dois:
            results.append(_openalex_work_to_dict(p, "openalex_citation_network"))

    return results


def _openalex_work_to_dict(p, source_label):
    """Convert an OpenAlex work JSON object to a flat paper dict."""
    doi = (p.get("doi") or "").replace("https://doi.org/", "")
    title = p.get("title", "?")
    year = p.get("publication_year", "?")
    venue = (p.get("primary_location") or {}).get("source", {}).get("display_name", "?")
    authors = []
    for a in p.get("authorships", []):
        name = (a.get("author") or {}).get("display_name", "")
        if name:
            authors.append(name)
    citations = p.get("cited_by_count", 0) or 0
    return {
        "doi": doi,
        "title": title,
        "year": year,
        "venue": venue,
        "authors": authors,
        "citations": citations,
        "source": source_label,
    }


# ── Boolean Query Builder (v3.0) ─────────────────────────────────────────────

def build_query(concept_blocks, source, strategy="relevance"):
    """Build a source-specific query string from concept blocks.

    concept_blocks: list of dicts, each with:
        - "concept": str (required) — the core term
        - "synonyms": list[str] (optional) — OR-connected synonyms
        - "exclude": list[str] (optional) — terms to exclude
        - "logic": "AND"|"OR"|"NOT" (default "AND") — how to connect to previous block
    source: "openalex" | "semantic_scholar" | "crossref" | "wanfang"
    strategy: "relevance" | "cited" | "recent" — for sort params

    Returns a dict with keys appropriate for each API:
        - openalex: {"search": ..., "filter": ..., "sort": ...}
        - semantic_scholar: {"q": ...}
        - crossref: {"query.title": ..., "sort": ..., "order": ...}
        - wanfang: {"q": ...} (PQ-format query string)
    """
    if not concept_blocks:
        return {}

    and_clauses = []
    not_terms = []

    for block in concept_blocks:
        terms = [block["concept"]] + block.get("synonyms", [])
        # Quote multi-word terms
        quoted = [f'"{t}"' if " " in t else t for t in terms]
        or_clause = " OR ".join(quoted)
        if len(terms) > 1:
            or_clause = f"({or_clause})"
        and_clauses.append(or_clause)

        for ex in block.get("exclude", []):
            not_terms.append(f'"{ex}"' if " " in ex else ex)

    if source == "openalex":
        query = " AND ".join(and_clauses)
        # OpenAlex search= param supports AND/OR, filters for title precision
        title_terms = []
        for block in concept_blocks:
            terms = [block["concept"]] + block.get("synonyms", [])
            title_terms.extend(terms)
        title_filter = "|".join(t.replace(" ", "+") for t in title_terms)

        result = {"search": query}
        if title_filter:
            result["filter"] = f"title.search:{title_filter}"
        # Map strategy to sort
        sort_map = {
            "relevance": "relevance_score:desc",
            "cited": "cited_by_count:desc",
            "recent": "publication_date:desc",
        }
        result["sort"] = sort_map.get(strategy, "relevance_score:desc")
        return result

    elif source == "semantic_scholar":
        # S2: +term for required, -term for excluded, space = implicit AND
        parts = []
        for block in concept_blocks:
            terms = [block["concept"]] + block.get("synonyms", [])
            for t in terms:
                prefix = "+" if " " not in t else '+"'
                suffix = '"' if " " in t else ""
                parts.append(f"{prefix}{t}{suffix}")
        for ex in not_terms:
            parts.append(f"-{ex}")
        return {
            "q": " ".join(parts),
            "strategy_requested": strategy,
            "strategy_applied": "relevance",
            "strategy_degraded": strategy != "relevance",
        }

    elif source == "crossref":
        query = " AND ".join(and_clauses)
        # Crossref uses query.title for title-focused search
        sort_map = {"relevance": "relevance", "cited": "is-referenced-by-count", "recent": "published"}
        return {"query.title": query, "sort": sort_map.get(strategy, "relevance"), "order": "desc"}

    elif source == "wanfang":
        # Wanfang PQ query: 标题:(term1 OR term2) AND 标题:(term3) NOT 标题:excl
        and_clauses = []
        not_terms = []
        for block in concept_blocks:
            terms = [block["concept"]] + block.get("synonyms", [])
            quoted = [f'"{t}"' if " " in t else t for t in terms]
            or_clause = " OR ".join(quoted)
            if len(terms) > 1:
                or_clause = f"({or_clause})"
            and_clauses.append(f"标题:{or_clause}")
            for ex in block.get("exclude", []):
                ex_quoted = f'"{ex}"' if " " in ex else ex
                not_terms.append(f"NOT 标题:{ex_quoted}")
        pq = " AND ".join(and_clauses)
        if not_terms:
            pq += " " + " ".join(not_terms)
        return {"q": pq}

    elif source == "cnki":
        # CNKI uses POST form fields, so just return the AND-joined plain query
        return {"q": " AND ".join(and_clauses)}

    else:
        # Unknown source: return raw AND-joined query
        return {"q": " AND ".join(and_clauses)}


def load_query_plan(json_path):
    """Load a boolean query plan from a JSON file.

    Expected format:
    {
      "topic": "research topic",
      "field": "engineering",
      "subfield": "mechanical_thermal",
      "framework": "concept_block",
      "sub_queries": [
        {
          "id": "S1",
          "label": "sub-topic description",
          "concept_blocks": [
            {"concept": "cold plate", "synonyms": ["liquid cooling"], "exclude": ["PCM"]},
            {"concept": "topology optimization", "synonyms": ["shape optimization"]}
          ]
        }
      ]
    }
    """
    with open(json_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    # Validate required fields
    if "sub_queries" not in plan:
        raise ValueError("Query plan must contain 'sub_queries' list")
    for sq in plan["sub_queries"]:
        if "concept_blocks" not in sq:
            raise ValueError(f"Sub-query '{sq.get('id', '?')}' missing 'concept_blocks'")
        for cb in sq["concept_blocks"]:
            if "concept" not in cb:
                raise ValueError(
                    f"Sub-query '{sq.get('id', '?')}': concept block missing 'concept'"
                )
    return plan


def _resolve_source(name):
    """Resolve alias to canonical source name."""
    return SOURCE_ALIASES.get(name.lower(), name.lower())


# ── Pre-flight Check ───────────────────────────────────────────────────────

def preflight():
    """Test all API endpoints and report status/latency."""
    endpoints = {
        "Semantic Scholar": "https://api.semanticscholar.org/graph/v1/paper/search?q=test&limit=1",
        "Crossref": "https://api.crossref.org/works?query.title=test&rows=1",
        "OpenAlex": "https://api.openalex.org/works?search=test&per_page=1",
    }
    endpoints["Wanfang Data"] = _build_wanfang_url("test", page=1, page_size=1)
    endpoints["CNKI"] = CNKI_SEARCH_HANDLER

    print("Pre-flight API Health Check")
    print("=" * 55)
    all_ok = True
    for name, url in endpoints.items():
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0"})
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read()
                # Wanfang and CNKI return HTML, other sources return JSON
                if name in ("Wanfang Data", "CNKI"):
                    ok = len(body) > 100  # Got actual content, not a redirect page
                else:
                    json.loads(body)  # Verify JSON is parseable
                    ok = True
            elapsed_ms = int((time.time() - start) * 1000)
            if ok:
                print(f"  ✅ {name:<20} OK ({elapsed_ms}ms)")
            else:
                print(f"  ❌ {name:<20} FAIL ({elapsed_ms}ms) — truncated/redirect")
                all_ok = False
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            err_msg = str(e)[:50]
            print(f"  ❌ {name:<20} FAIL ({elapsed_ms}ms) — {err_msg}")
            all_ok = False

    print("=" * 55)
    if all_ok:
        print("All endpoints reachable.")
    else:
        print("Some endpoints unreachable — check network/proxy.")

    # Cache status
    cache_count = 0
    if os.path.isdir(CACHE_DIR):
        try:
            cache_count = len([f for f in os.listdir(CACHE_DIR) if f.endswith(".json")])
        except OSError:
            pass
    print(f"Cache: {cache_count} entries in {CACHE_DIR}")
    return all_ok


# ── DOI Verification ───────────────────────────────────────────────────────

def verify_doi(doi):
    """Check if a DOI resolves via Crossref. Returns (is_valid, metadata_dict)."""
    doi_clean = doi.strip().replace("https://doi.org/", "")
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi_clean)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Hermes/1.0 (mailto:research@example.com)"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read())
                msg = data.get("message", {})
                title = (msg.get("title") or ["?"])[0]
                date_parts = (msg.get("published-print") or msg.get("issued") or {}).get(
                    "date-parts", [["?"]]
                )
                year = date_parts[0][0] if date_parts and date_parts[0] else "?"
                authors = []
                for a in msg.get("author", []):
                    family = a.get("family", "")
                    given = a.get("given", "")
                    if family:
                        authors.append(f"{family}, {given}" if given else family)
                return True, {
                    "doi": doi_clean,
                    "title": title,
                    "year": year,
                    "authors": authors,
                    "venue": (msg.get("container-title") or ["?"])[0],
                }
            else:
                return False, {}
    except Exception:
        return False, {}


def verify_dois_from_file(filepath):
    """Verify all DOIs in a file, report validity and metadata completeness."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Extract DOIs from text (BibTeX, Markdown table, or plain list)
    dois = re.findall(r'10\.\d{4,}/[^\s"\'},\]]+', content)
    # Clean trailing punctuation
    dois = [re.sub(r'[.,;:)\]]+$', '', d) for d in dois]
    unique_dois = list(dict.fromkeys(dois))

    print(f"Verifying {len(unique_dois)} unique DOIs...")
    print(f"{'DOI':<40} {'Status':<8} {'Title/Year'}")
    print("-" * 90)

    valid = []
    invalid = []
    incomplete = []

    for doi in unique_dois:
        is_valid, meta = verify_doi(doi)
        doi_short = doi[:38] + ".." if len(doi) > 40 else doi
        if is_valid:
            has_title = meta.get("title") and meta["title"] != "?"
            has_year = meta.get("year") and meta["year"] != "?"
            has_authors = meta.get("authors") and len(meta["authors"]) > 0

            if has_title and has_year and has_authors:
                title_short = meta["title"][:40] + ".." if len(meta.get("title", "")) > 40 else meta.get("title", "")
                print(f"  {doi_short:<40} ✅ OK    {title_short} ({meta['year']})")
                valid.append(doi)
            else:
                missing = []
                if not has_title:
                    missing.append("title")
                if not has_year:
                    missing.append("year")
                if not has_authors:
                    missing.append("authors")
                print(f"  {doi_short:<40} ⚠️ INCOMPLETE (missing: {', '.join(missing)})")
                incomplete.append({"doi": doi, "missing": missing})
        else:
            print(f"  {doi_short:<40} ❌ INVALID")
            invalid.append(doi)
        time.sleep(0.3)  # Rate limit courtesy

    print(f"\nResults: ✅ {len(valid)} valid | ⚠️ {len(incomplete)} incomplete | ❌ {len(invalid)} invalid")
    return valid, invalid, incomplete


def _normalized_title_words(value):
    return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", str(value or "").lower()))


def _title_agreement(left, right):
    a = _normalized_title_words(left)
    b = _normalized_title_words(right)
    if not a or not b:
        return 0.0
    return len(a & b) / max(len(a), len(b))


def verify_search_results(results, verifier=verify_doi):
    """Attach trust states without treating temporary API failure as invalid DOI."""
    for record in results:
        doi = record.get("doi")
        source = str(record.get("source") or "").lower()
        if not doi:
            if source in {"cnki", "wanfang"} and (record.get("source_id") or record.get("article_url")):
                record["verification_status"] = "VERIFIED_LOCAL"
                record["verification_confidence"] = "medium"
                record["verified_sources"] = source
                record["warn_class"] = ""
            else:
                record["verification_status"] = "WARN"
                record["verification_confidence"] = "low"
                record["warn_class"] = "missing_identifier"
            continue
        valid, metadata = verifier(doi)
        if not valid:
            record["verification_status"] = "WARN"
            record["verification_confidence"] = "low"
            record["warn_class"] = "doi_verification_unavailable"
            continue
        agreement = _title_agreement(record.get("title"), metadata.get("title"))
        if agreement < 0.5:
            record["verification_status"] = "WARN"
            record["verification_confidence"] = "low"
            record["warn_class"] = "metadata_mismatch"
        else:
            record["verification_status"] = "VERIFIED"
            record["verification_confidence"] = "high" if agreement >= 0.8 else "medium"
            record["warn_class"] = ""
        sources = [str(record.get("source") or "").strip(), "crossref"]
        record["verified_sources"] = ",".join(dict.fromkeys(item for item in sources if item))
    return results


# ── Deduplication ───────────────────────────────────────────────────────────

def _normalize_doi_key(value):
    return (value or "").lower().replace("https://doi.org/", "").strip()


def _normalize_title_key(value):
    return re.sub(r"\s+", "", (value or "").lower())


def _normalize_author_key(authors):
    if not authors:
        return ""
    cleaned = []
    for author in authors:
        text = str(author).strip().lower()
        if not text:
            continue
        text = text.split(",")[0].strip()
        text = re.sub(r"\s+", "", text)
        cleaned.append(text)
    return "|".join(cleaned)


def _prefer_richer_record(existing, candidate):
    discovered_sources = []
    for record in (existing, candidate):
        for source in [record.get("source"), *(record.get("discovered_sources") or [])]:
            source = str(source or "").strip()
            if source and source not in discovered_sources:
                discovered_sources.append(source)
    existing["discovered_sources"] = discovered_sources
    discovery_rounds = sorted({
        int(value) for record in (existing, candidate)
        for value in ([record.get("discovery_round")] + list(record.get("discovery_rounds") or []))
        if str(value or "").isdigit() and int(value) > 0
    })
    existing["discovery_rounds"] = discovery_rounds
    if discovery_rounds:
        existing["discovery_round"] = discovery_rounds[0]
    metadata_sources = dict(existing.get("metadata_sources") or {})
    for field in ("title", "authors", "abstract", "article_url", "year", "venue", "citations", "doi"):
        if existing.get(field) and field not in metadata_sources:
            metadata_sources[field] = existing.get("source", "")
        if candidate.get(field) and (not existing.get(field) or field == "abstract" and len(str(candidate.get(field))) > len(str(existing.get(field)))):
            metadata_sources[field] = candidate.get("source", "")
    existing["metadata_sources"] = metadata_sources
    existing_score = 0
    candidate_score = 0
    for field in ("authors", "abstract", "article_url", "year", "venue", "source_id"):
        ex_val = existing.get(field)
        ca_val = candidate.get(field)
        if isinstance(ex_val, list):
            existing_score += len(ex_val)
        elif ex_val:
            existing_score += 1
        if isinstance(ca_val, list):
            candidate_score += len(ca_val)
        elif ca_val:
            candidate_score += 1
    if candidate_score > existing_score:
        preserved = {
            "discovered_sources": discovered_sources,
            "metadata_sources": metadata_sources,
            "discovery_rounds": discovery_rounds,
            "discovery_round": discovery_rounds[0] if discovery_rounds else 0,
        }
        existing.update(candidate)
        existing.update(preserved)


def _effective_hits(results, topic_keywords=None):
    """Count deduplicated records with a plausible identifier and topic signal."""
    unique = deduplicate(results)
    keywords = [str(item).strip().lower() for item in (topic_keywords or []) if str(item).strip()]
    effective = []
    for record in unique:
        if not (record.get("doi") or record.get("source_id") or record.get("article_url")):
            continue
        if keywords:
            haystack = f"{record.get('title', '')} {record.get('abstract', '')}".lower()
            if not any(keyword in haystack for keyword in keywords):
                continue
        effective.append(record)
    return effective


def _tag_discovery(records, *, source, round_id, strategy="relevance", query=""):
    for record in records:
        record.setdefault("discovered_sources", [source])
        if source not in record["discovered_sources"]:
            record["discovered_sources"].append(source)
        record["discovery_round"] = round_id
        rounds = {int(item) for item in record.get("discovery_rounds") or [] if str(item).isdigit()}
        rounds.add(round_id)
        record["discovery_rounds"] = sorted(rounds)
        record["discovery_strategy"] = strategy
        record["_query"] = query


def deduplicate(results):
    """Deduplicate English by DOI and Chinese by author+title."""
    seen_doi = set()
    seen_fallback_key = set()
    unique = []

    for r in results:
        source = (r.get("source") or "").lower().strip()
        title_key = _normalize_title_key(r.get("title", ""))
        author_key = _normalize_author_key(r.get("authors") or [])

        if source in ("cnki", "wanfang"):
            key = f"{author_key}|{title_key}"
            if key in seen_fallback_key:
                for existing in unique:
                    ex_source = (existing.get("source") or "").lower().strip()
                    if ex_source in ("cnki", "wanfang"):
                        ex_key = f"{_normalize_author_key(existing.get('authors') or [])}|{_normalize_title_key(existing.get('title', ''))}"
                        if ex_key == key:
                            _prefer_richer_record(existing, r)
                            break
                continue
            seen_fallback_key.add(key)
            unique.append(r)
            continue

        doi = r.get("doi", "")
        doi_norm = _normalize_doi_key(doi)
        if doi_norm:
            if doi_norm in seen_doi:
                for existing in unique:
                    if _normalize_doi_key(existing.get("doi", "")) == doi_norm:
                        _prefer_richer_record(existing, r)
                        break
                continue
            seen_doi.add(doi_norm)
            unique.append(r)
        else:
            title = _normalize_title_key(r.get("title", ""))[:120]
            first_author = (r.get("authors") or ["?"])[0].lower().split(",")[0].strip() if r.get("authors") else "?"
            year = str(r.get("year", "?"))
            key = f"{title}|{first_author}|{year}"
            if key in seen_fallback_key:
                for existing in unique:
                    ex_title = _normalize_title_key(existing.get("title", ""))[:120]
                    ex_first = (existing.get("authors") or ["?"])[0].lower().split(",")[0].strip() if existing.get("authors") else "?"
                    ex_year = str(existing.get("year", "?"))
                    if f"{ex_title}|{ex_first}|{ex_year}" == key:
                        _prefer_richer_record(existing, r)
                        break
                continue
            seen_fallback_key.add(key)
            unique.append(r)

    return unique


# ── BibTeX / RIS / NBIB Export ─────────────────────────────────────────────

def _escape_bibtex(text):
    """Escape special characters for BibTeX."""
    if not text:
        return "?"
    text = str(text)
    for char, repl in [("\\", "\\\\"), ("{", "\\{"), ("}", "\\}"),
                        ("_", "\\_"), ("&", "\\&"), ("$", "\\$"),
                        ("#", "\\#"), ("%", "\\%"), ("~", "\\~{}")]:
        text = text.replace(char, repl)
    return text


def _bibtex_key(authors, year, title):
    """Generate a BibTeX citation key: FirstAuthorYear_FirstWord."""
    first_author = "unknown"
    if authors and len(authors) > 0:
        first_author = authors[0].split(",")[0].strip().lower()
        first_author = re.sub(r'[^a-z]', '', first_author)
    year_str = str(year) if year and year != "?" else "????"
    first_word = "paper"
    if title and title != "?":
        words = title.lower().split()
        for w in words:
            clean = re.sub(r'[^a-z]', '', w)
            if len(clean) > 3 and clean not in ("with", "from", "using", "based", "novel", "approach", "method", "study", "research", "analysis", "effect", "model", "system", "design"):
                first_word = clean
                break
    return f"{first_author}{year_str}_{first_word}"


def export_bibtex(results, output_path, tier_map=None):
    """Export results as .bib file with tier/score in note field."""
    tier_map = tier_map or {}
    lines = []
    lines.append(f"% Generated by search_by_topic.py v2.0")
    lines.append(f"% {len(results)} references")
    lines.append("")

    for i, r in enumerate(results):
        authors = r.get("authors", [])
        author_str = " and ".join(authors) if authors else "Unknown"
        title = r.get("title", "?")
        year = r.get("year", "?")
        doi = r.get("doi", "")
        venue = r.get("venue", "?")
        source = r.get("source", "?")

        cite_key = _bibtex_key(authors, year, title)

        # Build note field with tier/score info
        note_parts = []
        if doi in tier_map:
            note_parts.append(tier_map[doi])
        note_parts.append(f"source: {source}")
        if r.get("influential_citations"):
            note_parts.append(f"influential_citations: {r['influential_citations']}")
        note = " | ".join(note_parts)

        entry_type = "article"
        lines.append(f"@{entry_type}{{{cite_key},")
        lines.append(f"  title     = {{{_escape_bibtex(title)}}},")
        lines.append(f"  author    = {{{_escape_bibtex(author_str)}}},")
        if venue and venue != "?":
            lines.append(f"  journal   = {{{_escape_bibtex(venue)}}},")
        lines.append(f"  year      = {{{year}}},")
        if doi:
            lines.append(f"  doi       = {{{doi}}},")
        abstract = r.get("abstract", "")
        if abstract:
            lines.append(f"  abstract  = {{{_escape_bibtex(abstract)}}},")
        if note:
            lines.append(f"  note      = {{{_escape_bibtex(note)}}},")
        article_url = r.get("article_url", "")
        if article_url:
            lines.append(f"  url       = {{{_escape_bibtex(article_url)}}},")
        lines.append("}")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Exported {len(results)} references to {output_path} (.bib)", flush=True)


def _read_bibtex(filepath):
    """Parse a .bib file into a list of dicts. Simple parser, handles standard BibTeX."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    entries = []
    # Match @type{key, ...}
    pattern = r'@(\w+)\s*\{([^,]+),\s*(.*?)\}'
    # Use a simpler approach: split by @ and parse each
    blocks = re.split(r'\n(?=@)', text.strip())

    for block in blocks:
        block = block.strip()
        if not block.startswith("@"):
            continue

        m = re.match(r'@(\w+)\s*\{([^,]+),\s*(.*)', block, re.DOTALL)
        if not m:
            continue

        entry_type = m.group(1)
        cite_key = m.group(2)
        body = m.group(3).rstrip("}").rstrip().rstrip(",")

        entry = {"type": entry_type, "key": cite_key}

        # Parse fields: field = {value} or field = "value"
        for field_m in re.finditer(r'(\w+)\s*=\s*[{"]([^}"]*)[}"]', body):
            entry[field_m.group(1).lower()] = field_m.group(2)

        entries.append(entry)

    return entries


def convert_format(input_path, to_format, output_path):
    """Convert .bib to .ris or .nbib."""
    entries = _read_bibtex(input_path)
    if not entries:
        print(f"No entries found in {input_path}")
        return

    if to_format == "ris":
        _write_ris(entries, output_path)
    elif to_format == "nbib":
        _write_nbib(entries, output_path)
    else:
        print(f"Unknown format: {to_format}. Supported: ris, nbib")
        return

    print(f"Converted {len(entries)} entries: {input_path} -> {output_path} ({to_format})")


def _write_ris(entries, output_path):
    """Write RIS format (Zotero/EndNote compatible)."""
    type_map = {"article": "JOUR", "inproceedings": "CONF", "book": "BOOK",
                "phdthesis": "THES", "mastersthesis": "THES", "misc": "GEN"}

    lines = []
    for e in entries:
        ris_type = type_map.get(e.get("type", "article"), "JOUR")
        lines.append(f"TY  - {ris_type}")
        for au in re.split(r'\s+and\s+', e.get("author", "Unknown")):
            au = au.strip()
            if au:
                lines.append(f"AU  - {au}")
        if e.get("title"):
            lines.append(f"TI  - {e['title']}")
        if e.get("journal"):
            lines.append(f"JO  - {e['journal']}")
        if e.get("year"):
            lines.append(f"PY  - {e['year']}")
        if e.get("doi"):
            lines.append(f"DO  - {e['doi']}")
        if e.get("note"):
            lines.append(f"N1  - {e['note']}")
        lines.append("ER  - ")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_nbib(entries, output_path):
    """Write PubMed NBIB format."""
    lines = []
    for e in entries:
        lines.append(f"PMID- ")
        lines.append(f"OWN - NLM")
        lines.append(f"STAT- Publisher")
        if e.get("doi"):
            lines.append(f"LID - {e['doi']} [doi]")
        for au in re.split(r'\s+and\s+', e.get("author", "Unknown")):
            au = au.strip()
            if "," in au:
                parts = au.split(",", 1)
                lines.append(f"FAU - {parts[0].strip()}")
                lines.append(f"AU  - {au}")
        if e.get("title"):
            lines.append(f"TI  - {e['title']}")
        if e.get("journal"):
            lines.append(f"JT  - {e['journal']}")
            lines.append(f"TA  - {e['journal']}")
        if e.get("year"):
            lines.append(f"DP  - {e['year']}")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ── Scoring Helpers ─────────────────────────────────────────────────────────

def score_results(results, topic_keywords):
    """
    Score each result 0-5 on 5 dimensions for a max of 25.
    This is a heuristic — final scoring should be reviewed by the user.
    Returns dict of doi -> score string (e.g. "Tier 1 | Score: 22/25 | S1").
    """
    current_year = time.gmtime().tm_year
    weights = {
        "topic_match": 0.35,
        "method_rigor": 0.20,
        "source_quality": 0.15,
        "recency": 0.15,
        "impact": 0.15,
    }
    tier_map = {}

    for r in results:
        reasons = []
        uncertainty_flags = []

        # 1. Topic match (title + abstract keyword overlap)
        title_lower = r.get("title", "").lower()
        abstract = r.get("abstract", "") or ""
        abstract_lower = abstract.lower()
        kw_matches_title = sum(1 for kw in topic_keywords if kw.lower() in title_lower)
        kw_matches_abstract = sum(1 for kw in topic_keywords if kw.lower() in abstract_lower)
        # Title match counts double, abstract match counts once
        topic_score = min(5, kw_matches_title * 2 + kw_matches_abstract)
        if not abstract.strip():
            topic_score = min(topic_score, 4)
            uncertainty_flags.append("no_abstract_uncertain")
        reasons.append(f"topic_match={topic_score}: title_hits={kw_matches_title}, abstract_hits={kw_matches_abstract}")

        # 2. Method match (from abstract text)
        method_score = 1
        if abstract:
            abs_lower = abstract_lower
            has_experiment = any(w in abs_lower for w in _experiment_kw)
            has_simulation = any(w in abs_lower for w in _simulation_kw)
            has_validation = any(w in abs_lower for w in {
                "validation", "validated", "baseline", "control group", "benchmark",
                "statistical", "sensitivity", "uncertainty", "reproducibility",
            })
            if has_experiment and has_validation:
                method_score = 5
            elif has_experiment:
                method_score = 4
            elif has_simulation and has_validation:
                method_score = 4
            elif has_simulation:
                method_score = 3
            else:
                method_score = 2
                uncertainty_flags.append("method_rigor_uncertain")
        else:
            uncertainty_flags.append("method_rigor_unavailable")
        reasons.append(f"method_rigor={method_score}: abstract method/validation signals")

        # 3. Source quality (heuristic by venue presence)
        venue = r.get("venue") or r.get("journal") or ""
        source = str(r.get("source") or "").lower()
        if venue and venue != "?":
            source_score = 3
        elif source in {"openalex", "crossref", "semantic_scholar", "pubmed", "cnki", "wanfang"}:
            source_score = 2
            uncertainty_flags.append("venue_quality_unresolved")
        else:
            source_score = 1
            uncertainty_flags.append("source_quality_unresolved")
        reasons.append(f"source_quality={source_score}: venue={venue or 'missing'}, source={source or 'unknown'}")

        # 4. Recency
        year = r.get("year", "?")
        try:
            y = int(year)
            age = current_year - y
            if age <= 3:
                recency_score = 5
            elif age <= 5:
                recency_score = 4
            elif age <= 10:
                recency_score = 3
            else:
                recency_score = 2
        except (ValueError, TypeError):
            recency_score = 2
        reasons.append(f"recency={recency_score}: publication_year={year}")

        # 5. Citations
        citations = r.get("citations", 0) or 0
        try:
            citations = int(citations)
        except (TypeError, ValueError):
            citations = 0
            uncertainty_flags.append("citation_count_invalid")
        try:
            paper_age = max(1, current_year - int(year) + 1)
        except (TypeError, ValueError):
            paper_age = 5
            uncertainty_flags.append("publication_year_unknown")
        citations_per_year = citations / paper_age
        if citations_per_year >= 20:
            cite_score = 5
        elif citations_per_year >= 10:
            cite_score = 4
        elif citations_per_year >= 3:
            cite_score = 3
        elif citations_per_year > 0:
            cite_score = 2
        else:
            cite_score = 2 if paper_age <= 2 else 1
            if paper_age <= 2:
                uncertainty_flags.append("recent_unindexed")
        reasons.append(f"impact={cite_score}: citations_per_year={citations_per_year:.2f}")

        dimensions = {
            "topic_match": topic_score,
            "method_rigor": method_score,
            "source_quality": source_score,
            "recency": recency_score,
            "impact": cite_score,
        }
        weighted_score = round(sum(dimensions[name] * weights[name] for name in weights) * 5, 2)
        score = int(round(weighted_score))
        confidence = "high" if not uncertainty_flags else "medium" if len(uncertainty_flags) <= 2 else "low"

        # Determine tier
        if weighted_score >= 20 and topic_score >= 4 and method_score >= 3 and confidence != "low":
            tier = "Tier 1"
        elif weighted_score >= 15:
            tier = "Tier 2"
        elif weighted_score >= 10:
            tier = "Tier 3"
        else:
            tier = "Tier 4"

        r["_score"] = score
        r["_weighted_score"] = weighted_score
        r["_tier"] = tier
        r["_score_dimensions"] = dimensions
        r["_score_weights"] = weights
        r["_score_reasons"] = reasons
        r["_score_confidence"] = confidence
        r["_uncertainty_flags"] = sorted(set(uncertainty_flags))
        tier_map[r.get("doi", "")] = f"{tier} | Score: {weighted_score:.2f}/25"

    return tier_map


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Search academic papers by topic (v2.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search (backward compatible)
  python3 search_by_topic.py "battery thermal management" --limit 20

  # T1->T2->T3 routing with fallback threshold
  python3 search_by_topic.py "cold plate topology optimization" \\
      --t1 semantic_scholar --t2 crossref --t3 openalex \\
      --min-results 30 --limit 50

  # Pre-flight API health check
  python3 search_by_topic.py --preflight

  # Export as .bib with tier/score notes
  python3 search_by_topic.py "query" --t1 crossref --export-bib output.bib

  # Convert .bib to .ris (Zotero/EndNote) or .nbib (PubMed)
  python3 search_by_topic.py --convert input.bib --to ris --output output.ris

  # Verify DOIs from a file
  python3 search_by_topic.py --verify-dois dois.txt

  # Wanfang Data Chinese literature search (requires institutional IP or CARSI SSO login)
  python3 search_by_topic.py "冷板拓扑优化" --source wanfang --limit 20

  # CNKI Chinese literature search (campus IP or CARSI CDP login)
  python3 search_by_topic.py "拓扑优化" --source cnki --limit 20

  # CNKI multi-strategy: sort by citations
  python3 search_by_topic.py "拓扑优化" --source cnki --strategy cited --limit 20

  # T1/T2/T3 routing with CNKI primary + Wanfang supplement
  python3 search_by_topic.py "散热器优化" --t1 cnki --t2 wanfang --limit 30

  # T1/T2/T3 routing with Wanfang fallback
  python3 search_by_topic.py "battery thermal management" --t1 openalex --t2 wanfang
        """
    )

    # Search mode
    parser.add_argument("query", nargs="?", help="Search query string")
    parser.add_argument("--source", choices=["semantic", "crossref", "openalex", "wanfang", "wf",
                                              "cnki", "cn", "all", "semantic_scholar",
                                              "semantic_scholar_bulk", "semantic_bulk", "ss_bulk"],
                        default="all",
                        help="Search source (default: all). Use --t1/--t2/--t3 for routing.")
    parser.add_argument("--t1", help="Primary source (T1). Options: semantic_scholar, crossref, openalex, wanfang, cnki")
    parser.add_argument("--t2", help="Secondary source (T2), used if T1 returns < --min-results "
                        "(unless --parallel is set)")
    parser.add_argument("--t3", help="Last resort source (T3)")
    parser.add_argument("--parallel", action="store_true",
                        help="Always run T1+T2 (never skip T2). Recommended for Chinese routing.")
    parser.add_argument("--min-results", type=int, default=30,
                        help="Min results from T1 before falling back to T2 (default: 30)")
    parser.add_argument("--limit", type=int, default=20, help="Max results per source (default: 20)")
    parser.add_argument("--output", "-o", help="Export DOI list only (plain text, one per line). Use --export-bib for full BibTeX.")
    parser.add_argument("--include-no-doi", action="store_true", help="Include results without DOIs")

    # v3.0 Boolean query mode
    parser.add_argument("--bool", dest="bool_file", metavar="JSON",
                        help="Query plan JSON file with concept blocks (v3.0)")
    parser.add_argument("--strategy", choices=["relevance", "cited", "recent", "all"],
                        default="relevance",
                        help="Search strategy for --bool mode (default: relevance). "
                             "Use 'all' to run all 3 strategies.")

    # Export mode
    parser.add_argument("--export-bib", help="Export full BibTeX (.bib) with title/author/year/doi/abstract/tier/score notes")
    parser.add_argument("--export-workflow-json",
                        help="Export standard workflow search results JSON for Step 5/6/7 handoff")
    parser.add_argument("--keywords", help="Comma-separated topic keywords for auto-scoring")

    # Convert mode
    parser.add_argument("--convert", help="Convert .bib to another format")
    parser.add_argument("--to", choices=["ris", "nbib"], help="Target format for --convert")

    # Verify mode
    parser.add_argument("--verify-dois", help="Verify DOIs from a file (checks validity + metadata)")

    # Pre-flight mode
    parser.add_argument("--preflight", action="store_true", help="Run API health check and exit")

    # Citation network mode
    parser.add_argument("--citation-network", metavar="DOI",
                        help="Fetch citation network (forward+backward) for a given DOI via OpenAlex")
    parser.add_argument("--refs-limit", type=int, default=30,
                        help="Max backward references for --citation-network (default: 30)")
    parser.add_argument("--cited-by-limit", type=int, default=50,
                        help="Max forward citations for --citation-network (default: 50)")
    parser.add_argument("--existing-dois", help="File of DOIs to exclude from citation network results")

    # Cache control
    parser.add_argument("--no-cache", action="store_true", help="Bypass semantic cache for fresh results")

    # Language filter (CNKI/Wanfang)
    parser.add_argument("--language", choices=["zh", "en", "any"],
                        default="any",
                        help="Language filter for CNKI/Wanfang sources. "
                             "'zh' keeps only Chinese-titled papers (isinEn=0 + title filter). "
                             "'en' keeps only English-titled papers. "
                             "'any' (default) disables filtering. "
                             "For this workflow, CNKI/Wanfang should normally use --language zh.")

    # CDP port
    parser.add_argument("--cdp-port", type=int, default=None,
                        help="CDP Chrome DevTools port (default: $CDP_PORT env or 9223)")

    # Scoring
    parser.add_argument("--score", action="store_true", help="Auto-score results with heuristics")
    parser.add_argument("--verify-metadata", action="store_true",
                        help="Verify DOI/title metadata and write VERIFIED/WARN trust fields")

    args = parser.parse_args()

    # Override CDP port if --cdp-port provided
    if args.cdp_port is not None:
        global _CDP_PORT, WANFANG_CDP_PORT, CNKI_CDP_PORT
        _CDP_PORT = args.cdp_port
        WANFANG_CDP_PORT = args.cdp_port
        CNKI_CDP_PORT = args.cdp_port

    # ── Pre-flight mode ──
    if args.preflight:
        ok = preflight()
        sys.exit(0 if ok else 1)

    # ── Convert mode ──
    if args.convert:
        if not args.to:
            print("ERROR: --convert requires --to (ris or nbib)", file=sys.stderr)
            sys.exit(1)
        out_path = args.output or args.convert.rsplit(".", 1)[0] + f".{args.to}"
        convert_format(args.convert, args.to, out_path)
        sys.exit(0)

    # ── Verify mode ──
    if args.verify_dois:
        verify_dois_from_file(args.verify_dois)
        sys.exit(0)

    # ── Citation network mode ──
    if args.citation_network:
        existing_dois = set()
        if args.existing_dois:
            try:
                with open(args.existing_dois, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        doi_match = re.search(r'10\.\d{4,}/[^\s"\'},\]]+', line)
                        if doi_match:
                            existing_dois.add(
                                doi_match.group(0)
                                .replace("https://doi.org/", "")
                                .lower()
                                .strip()
                            )
            except Exception as e:
                print(f"Warning: could not read existing DOIs file: {e}", file=sys.stderr)

        print(f"Citation network for: {args.citation_network}", flush=True)
        print(f"  refs_limit={args.refs_limit}, cited_by_limit={args.cited_by_limit}, "
              f"existing_dois={len(existing_dois)}", flush=True)

        results = fetch_citation_network(
            args.citation_network,
            refs_limit=args.refs_limit,
            cited_by_limit=args.cited_by_limit,
            existing_dois=existing_dois,
        )
        _tag_discovery(results, source="openalex_citation_network", round_id=3, strategy="citation_network", query=args.citation_network)

        # Auto-score if keywords provided
        if args.score or args.keywords:
            keywords = []
            if args.keywords:
                keywords = [k.strip() for k in args.keywords.split(",")]
            score_results(results, keywords)

        # Output
        if args.export_bib:
            export_bibtex(results, args.export_bib)
        if args.export_workflow_json:
            if not SearchResultRecord or not write_workflow_json:
                print("ERROR: workflow_contracts.py is unavailable", file=sys.stderr)
                sys.exit(1)
            records = [SearchResultRecord.from_search_result(r) for r in results]
            write_workflow_json(
                args.export_workflow_json,
                records,
                metadata={
                    "mode": "citation_network",
                    "seed_doi": args.citation_network,
                    "refs_limit": args.refs_limit,
                    "cited_by_limit": args.cited_by_limit,
                },
            )
            print(f"Saved workflow JSON to {args.export_workflow_json}", flush=True)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(results)} citation network papers to {args.output}", flush=True)
        elif not args.export_bib and not args.export_workflow_json:
            for r in results:
                print(json.dumps(r, ensure_ascii=False))
        print(f"\nCitation network complete: {len(results)} new papers found", flush=True)
        sys.exit(0)

    # ── v3.0 Boolean query mode ──
    if args.bool_file:
        if not args.query:
            print("ERROR: --bool requires a query string (used as fallback if JSON fails)",
                  file=sys.stderr)
            sys.exit(1)
        plan = load_query_plan(args.bool_file)
        source = args.t1 if args.t1 else args.source
        if source in ("all", "semantic"):
            source = "openalex"  # default to OpenAlex for bool mode
        source_canon = _resolve_source(source)
        if source_canon not in SOURCE_FUNCTIONS:
            print(f"ERROR: Unknown source '{source}' for --bool mode", file=sys.stderr)
            sys.exit(1)

        all_results = []
        strategies = ["relevance", "cited", "recent"] if args.strategy == "all" else [args.strategy]

        for sq in plan.get("sub_queries", []):
            sq_id = sq.get("id", "?")
            blocks = sq.get("concept_blocks", [])

            for strat in strategies:
                query_params = build_query(blocks, source_canon, strat)
                query_str = query_params.get("q", query_params.get("search", query_params.get("query.title", args.query)))

                print(f"  [{sq_id}:{strat}] {source_canon}: {query_str[:80]}...", flush=True)
                if source_canon in ("cnki", "wanfang"):
                    results = SOURCE_FUNCTIONS[source_canon](query_str, args.limit, use_cache=not args.no_cache, language=args.language)
                elif source_canon in ("openalex", "crossref"):
                    results = SOURCE_FUNCTIONS[source_canon](
                        query_str, args.limit, use_cache=not args.no_cache, query_params=query_params,
                    )
                else:
                    results = SOURCE_FUNCTIONS[source_canon](query_str, args.limit, use_cache=not args.no_cache)
                print(f"  [{sq_id}:{strat}] {source_canon}: {len(results)} results", flush=True)
                # Tag results with sub-query ID and strategy
                _tag_discovery(results, source=source_canon, round_id=strategies.index(strat) + 1, strategy=strat, query=query_str)
                for r in results:
                    if query_params.get("strategy_degraded"):
                        r["strategy_degraded"] = True
                        r["strategy_applied"] = query_params.get("strategy_applied")
                    r["_sub_query"] = sq_id
                    r["_strategy"] = strat
                all_results.extend(results)

    # ── Search mode (backward compatible) ──
    elif not args.query:
        print("ERROR: query is required for search mode. Use --preflight, --convert, or --verify-dois instead.",
              file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Searching: {args.query}", flush=True)

        # Resolve sources with T1->T2->T3 routing
        all_results = []

        if args.t1:
            # T1->T2->T3 routing mode
            sources = [(args.t1, "T1"), (args.t2, "T2"), (args.t3, "T3")]
            fallback_keywords = [w.strip().lower() for w in args.query.split() if len(w.strip()) > 3]
            for round_id, (src, label) in enumerate(sources, 1):
                if not src:
                    continue
                src_canon = _resolve_source(src)
                if src_canon not in SOURCE_FUNCTIONS:
                    print(f"  Unknown source '{src}' for {label}", file=sys.stderr)
                    continue

                print(f"  [{label}] Querying {src_canon}...", flush=True)
                # Pass language for CNKI/Wanfang sources
                if src_canon in ("cnki", "wanfang"):
                    results = SOURCE_FUNCTIONS[src_canon](args.query, args.limit, use_cache=not args.no_cache, language=args.language)
                else:
                    results = SOURCE_FUNCTIONS[src_canon](args.query, args.limit, use_cache=not args.no_cache)
                print(f"  [{label}] {src_canon}: {len(results)} results", flush=True)
                _tag_discovery(results, source=src_canon, round_id=round_id, query=args.query)
                all_results.extend(results)

                # Use deduplicated, topically plausible records for fallback decisions.
                effective_count = len(_effective_hits(all_results, fallback_keywords))
                if not args.parallel and label == "T1" and effective_count >= args.min_results:
                    print(f"  T1 returned >= {args.min_results} effective unique results, skipping T2/T3 "
                          f"(use --parallel to force both)")
                    break
        else:
            # Legacy mode: --source
            if args.source in ("semantic", "semantic_scholar", "all"):
                print("  Querying Semantic Scholar...", flush=True)
                results = search_semantic_scholar(args.query, args.limit, use_cache=not args.no_cache)
                _tag_discovery(results, source="semantic_scholar", round_id=1, query=args.query)
                all_results.extend(results)
            if args.source in ("crossref", "all"):
                print("  Querying Crossref...", flush=True)
                results = search_crossref(args.query, args.limit, use_cache=not args.no_cache)
                _tag_discovery(results, source="crossref", round_id=1, query=args.query)
                all_results.extend(results)
            if args.source in ("openalex", "all"):
                print("  Querying OpenAlex...", flush=True)
                results = search_openalex(args.query, args.limit, use_cache=not args.no_cache)
                _tag_discovery(results, source="openalex", round_id=1, query=args.query)
                all_results.extend(results)
            if args.source in ("wanfang", "wf", "all"):
                print("  Querying Wanfang Data...", flush=True)
                results = search_wanfang(args.query, args.limit, use_cache=not args.no_cache, language=args.language)
                _tag_discovery(results, source="wanfang", round_id=2, query=args.query)
                all_results.extend(results)
            if args.source in ("cnki", "cn", "all"):
                print("  Querying CNKI...", flush=True)
                results = search_cnki(args.query, args.limit, use_cache=not args.no_cache, strategy=args.strategy if args.strategy and args.strategy != "all" else "", language=args.language)
                _tag_discovery(results, source="cnki", round_id=2, strategy=args.strategy, query=args.query)
                all_results.extend(results)

    # Deduplicate
    unique = deduplicate(all_results)
    unique.sort(key=lambda x: -(int(x.get("year", 0) or 0)))
    workflow_unique = list(unique)

    if args.verify_metadata:
        verify_search_results(workflow_unique)

    # Filter no-DOI
    if not args.include_no_doi:
        unique = [r for r in unique if r.get("doi")]

    # Auto-score if requested
    tier_map = {}
    if args.score or args.keywords:
        keywords = []
        if args.keywords:
            keywords = [k.strip() for k in args.keywords.split(",")]
        else:
            # Extract from query
            keywords = [w.strip() for w in args.query.split() if len(w.strip()) > 3]
        tier_map = score_results(unique, keywords)

    # Print summary
    has_abstract = sum(1 for r in unique if r.get("abstract"))
    print(f"\nFound {len(unique)} unique papers ({has_abstract} with abstracts) "
          f"(across {len(all_results)} raw hits):")
    print(f"{'DOI':<35} {'Yr':<5} {'Src':<12} {'Score':<6} {'Tier':<7} {'Abs':<4} Title")
    print("-" * 115)

    for r in unique[:50]:
        doi_short = r["doi"][:33] + ".." if len(r.get("doi", "")) > 35 else r.get("doi", "")
        title_short = r["title"][:45] + ".." if len(r.get("title", "")) > 45 else r.get("title", "")
        score = r.get("_score", "?")
        tier = r.get("_tier", "?")
        abs_flag = "✅" if r.get("abstract") else "—"
        print(f"{doi_short:<35} {str(r.get('year', '?')):<5} {r.get('source', '?')[:12]:<12} {str(score):<6} {tier:<7} {abs_flag:<4} {title_short}")

    # Output
    if args.export_bib:
        export_bibtex(unique, args.export_bib, tier_map)

    if args.export_workflow_json:
        if not SearchResultRecord or not write_workflow_json:
            print("ERROR: workflow_contracts.py is unavailable", file=sys.stderr)
            sys.exit(1)
        records = [SearchResultRecord.from_search_result(r) for r in workflow_unique]
        write_workflow_json(
            args.export_workflow_json,
            records,
            metadata={
                "query": args.query,
                "source": args.source,
                "t1": args.t1,
                "t2": args.t2,
                "t3": args.t3,
                "language": args.language,
                "strategy": args.strategy,
                "limit": args.limit,
                "raw_hits": len(all_results),
                "unique_hits": len(unique),
                "workflow_records": len(workflow_unique),
            },
        )
        print(f"\nSaved workflow JSON to {args.export_workflow_json}", flush=True)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for r in unique:
                f.write(f"{r['doi']}\n")
        print(f"\nSaved {len(unique)} DOIs to {args.output}", flush=True)
    elif not args.export_bib:
        print(f"\nDOIs only:")
        for r in unique:
            print(f"  {r['doi']}")


if __name__ == "__main__":
    main()
