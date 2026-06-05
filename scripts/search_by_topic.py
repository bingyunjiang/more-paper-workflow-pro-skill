#!/usr/bin/env python3
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
"""
import json
import urllib.request
import urllib.parse
import time
import sys
import re
import os


# ── API Search Functions ───────────────────────────────────────────────────

def search_semantic_scholar(query, limit=20):
    """Search Semantic Scholar API. Free, no key needed for basic search."""
    params = urllib.parse.urlencode({
        "q": query,
        "limit": min(limit, 100),
        "fields": "title,authors,externalIds,year,venue,citationCount,abstract"
    })
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  Semantic Scholar error: {e}", flush=True)
        return []

    results = []
    for p in data.get("data", []):
        ext_ids = p.get("externalIds", {})
        doi = ext_ids.get("DOI", "")
        title = p.get("title", "?")
        year = p.get("year", "?")
        venue = p.get("venue", "?")
        authors = [a.get("name", "?") for a in p.get("authors", [])]
        citations = p.get("citationCount", 0) or 0
        if doi:
            results.append({
                "doi": doi, "title": title, "year": year, "venue": venue,
                "authors": authors, "citations": citations,
                "source": "semantic_scholar"
            })
    return results


def search_crossref(query, limit=20):
    """Search Crossref API. Free, generous rate limits."""
    params = urllib.parse.urlencode({
        "query.title": query,
        "rows": min(limit, 100),
        "sort": "relevance",
        "order": "desc"
    })
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
                "source": "crossref"
            })
    return results


def search_openalex(query, limit=20):
    """Search OpenAlex API. Free, no key needed."""
    params = urllib.parse.urlencode({
        "search": query,
        "per_page": min(limit, 50),
        "sort": "relevance_score:desc"
    })
    url = f"https://api.openalex.org/works?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
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
        venue = (p.get("primary_location") or {}).get(
            "source", {}
        ).get("display_name", "?")
        authors = []
        for a in p.get("authorships", []):
            name = (a.get("author") or {}).get("display_name", "")
            if name:
                authors.append(name)
        citations = p.get("cited_by_count", 0) or 0
        if doi:
            results.append({
                "doi": doi, "title": title, "year": year, "venue": venue,
                "authors": authors, "citations": citations,
                "source": "openalex"
            })
    return results


# Map source names to functions
SOURCE_FUNCTIONS = {
    "semantic_scholar": search_semantic_scholar,
    "crossref": search_crossref,
    "openalex": search_openalex,
}

SOURCE_ALIASES = {
    "semantic": "semantic_scholar",
    "ss": "semantic_scholar",
    "cr": "crossref",
    "oa": "openalex",
}


# ── Boolean Query Builder (v3.0) ─────────────────────────────────────────────

def build_query(concept_blocks, source, strategy="relevance"):
    """Build a source-specific query string from concept blocks.

    concept_blocks: list of dicts, each with:
        - "concept": str (required) — the core term
        - "synonyms": list[str] (optional) — OR-connected synonyms
        - "exclude": list[str] (optional) — terms to exclude
        - "logic": "AND"|"OR"|"NOT" (default "AND") — how to connect to previous block
    source: "openalex" | "semantic_scholar" | "crossref"
    strategy: "relevance" | "cited" | "recent" — for sort params

    Returns a dict with keys appropriate for each API:
        - openalex: {"search": ..., "filter": ..., "sort": ...}
        - semantic_scholar: {"q": ...}
        - crossref: {"query.title": ..., "sort": ..., "order": ...}
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
        return {"q": " ".join(parts)}

    elif source == "crossref":
        query = " AND ".join(and_clauses)
        # Crossref uses query.title for title-focused search
        return {"query.title": query, "sort": "relevance", "order": "desc"}

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
    with open(json_path, "r") as f:
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

    print("Pre-flight API Health Check")
    print("=" * 55)
    all_ok = True
    for name, url in endpoints.items():
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0"})
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            elapsed_ms = int((time.time() - start) * 1000)
            print(f"  ✅ {name:<20} OK ({elapsed_ms}ms)")
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
    with open(filepath, "r") as f:
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


# ── Deduplication ───────────────────────────────────────────────────────────

def deduplicate(results):
    """Deduplicate by DOI (primary) or title+first_author+year (fallback)."""
    seen_doi = set()
    seen_title_key = set()
    unique = []

    for r in results:
        doi = r.get("doi", "")
        if doi:
            doi_norm = doi.lower().replace("https://doi.org/", "").strip()
            if doi_norm in seen_doi:
                # Keep the entry with more metadata
                for existing in unique:
                    if existing.get("doi", "").lower().replace("https://doi.org/", "").strip() == doi_norm:
                        if len(r.get("authors", [])) > len(existing.get("authors", [])):
                            existing.update(r)
                        break
                continue
            seen_doi.add(doi_norm)
            unique.append(r)
        else:
            # Fallback: title + first_author + year
            title = (r.get("title") or "?").lower().strip()[:80]
            first_author = (r.get("authors") or ["?"])[0].lower().split(",")[0].strip() if r.get("authors") else "?"
            year = str(r.get("year", "?"))
            key = f"{title}|{first_author}|{year}"
            if key in seen_title_key:
                continue
            seen_title_key.add(key)
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
        if note:
            lines.append(f"  note      = {{{_escape_bibtex(note)}}},")
        lines.append("}")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Exported {len(results)} references to {output_path} (.bib)", flush=True)


def _read_bibtex(filepath):
    """Parse a .bib file into a list of dicts. Simple parser, handles standard BibTeX."""
    with open(filepath, "r") as f:
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

    with open(output_path, "w") as f:
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

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


# ── Scoring Helpers ─────────────────────────────────────────────────────────

def score_results(results, topic_keywords):
    """
    Score each result 0-5 on 5 dimensions for a max of 25.
    This is a heuristic — final scoring should be reviewed by the user.
    Returns dict of doi -> score string (e.g. "Tier 1 | Score: 22/25 | S1").
    """
    current_year = 2026
    tier_map = {}

    for r in results:
        score = 0
        reasons = []

        # 1. Topic match (title keyword overlap)
        title_lower = r.get("title", "").lower()
        kw_matches = sum(1 for kw in topic_keywords if kw.lower() in title_lower)
        topic_score = min(5, kw_matches * 2)
        score += topic_score
        if topic_score >= 4:
            reasons.append("title_match")

        # 2. Method match (heuristic — venue + title signals)
        method_score = 3  # default
        score += method_score

        # 3. Source quality (heuristic by venue presence)
        venue = r.get("venue", "?")
        source_score = 3 if venue and venue != "?" else 1
        score += source_score

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
        score += recency_score

        # 5. Citations
        citations = r.get("citations", 0)
        if citations >= 100:
            cite_score = 5
        elif citations >= 50:
            cite_score = 4
        elif citations >= 10:
            cite_score = 3
        elif citations > 0:
            cite_score = 2
        else:
            cite_score = 1
        score += cite_score

        # Determine tier
        if score >= 20:
            tier = "Tier 1"
        elif score >= 15:
            tier = "Tier 2"
        elif score >= 10:
            tier = "Tier 3"
        else:
            tier = "Tier 4"

        r["_score"] = score
        r["_tier"] = tier
        tier_map[r.get("doi", "")] = f"{tier} | Score: {score}/25"

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
        """
    )

    # Search mode
    parser.add_argument("query", nargs="?", help="Search query string")
    parser.add_argument("--source", choices=["semantic", "crossref", "openalex", "all",
                                              "semantic_scholar"],
                        default="all",
                        help="Search source (default: all). Use --t1/--t2/--t3 for routing.")
    parser.add_argument("--t1", help="Primary source (T1). Options: semantic_scholar, crossref, openalex")
    parser.add_argument("--t2", help="Secondary source (T2), used if T1 returns < --min-results")
    parser.add_argument("--t3", help="Last resort source (T3)")
    parser.add_argument("--min-results", type=int, default=30,
                        help="Min results from T1 before falling back to T2 (default: 30)")
    parser.add_argument("--limit", type=int, default=20, help="Max results per source (default: 20)")
    parser.add_argument("--output", "-o", help="Output file (DOI list, default: stdout)")
    parser.add_argument("--include-no-doi", action="store_true", help="Include results without DOIs")

    # v3.0 Boolean query mode
    parser.add_argument("--bool", dest="bool_file", metavar="JSON",
                        help="Query plan JSON file with concept blocks (v3.0)")
    parser.add_argument("--strategy", choices=["relevance", "cited", "recent", "all"],
                        default="relevance",
                        help="Search strategy for --bool mode (default: relevance). "
                             "Use 'all' to run all 3 strategies.")

    # Export mode
    parser.add_argument("--export-bib", help="Export results as .bib file (with tier/score notes)")
    parser.add_argument("--keywords", help="Comma-separated topic keywords for auto-scoring")

    # Convert mode
    parser.add_argument("--convert", help="Convert .bib to another format")
    parser.add_argument("--to", choices=["ris", "nbib"], help="Target format for --convert")

    # Verify mode
    parser.add_argument("--verify-dois", help="Verify DOIs from a file (checks validity + metadata)")

    # Pre-flight mode
    parser.add_argument("--preflight", action="store_true", help="Run API health check and exit")

    # Scoring
    parser.add_argument("--score", action="store_true", help="Auto-score results with heuristics")

    args = parser.parse_args()

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
                query_str = query_params.pop("q", query_params.pop("search", args.query))

                print(f"  [{sq_id}:{strat}] {source_canon}: {query_str[:80]}...", flush=True)
                results = SOURCE_FUNCTIONS[source_canon](query_str, args.limit)
                print(f"  [{sq_id}:{strat}] {source_canon}: {len(results)} results", flush=True)
                # Tag results with sub-query ID and strategy
                for r in results:
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
            for src, label in sources:
                if not src:
                    continue
                src_canon = _resolve_source(src)
                if src_canon not in SOURCE_FUNCTIONS:
                    print(f"  Unknown source '{src}' for {label}", file=sys.stderr)
                    continue

                print(f"  [{label}] Querying {src_canon}...", flush=True)
                results = SOURCE_FUNCTIONS[src_canon](args.query, args.limit)
                print(f"  [{label}] {src_canon}: {len(results)} results", flush=True)
                all_results.extend(results)

                # If T1 returned enough, skip T2/T3
                if label == "T1" and len(results) >= args.min_results:
                    print(f"  T1 returned >= {args.min_results}, skipping T2/T3 fallback")
                    break
        else:
            # Legacy mode: --source
            if args.source in ("semantic", "semantic_scholar", "all"):
                print("  Querying Semantic Scholar...", flush=True)
                all_results.extend(search_semantic_scholar(args.query, args.limit))
            if args.source in ("crossref", "all"):
                print("  Querying Crossref...", flush=True)
                all_results.extend(search_crossref(args.query, args.limit))
            if args.source in ("openalex", "all"):
                print("  Querying OpenAlex...", flush=True)
                all_results.extend(search_openalex(args.query, args.limit))

    # Deduplicate
    unique = deduplicate(all_results)
    unique.sort(key=lambda x: -(int(x.get("year", 0) or 0)))

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
    print(f"\nFound {len(unique)} unique papers (across {len(all_results)} raw hits):")
    print(f"{'DOI':<35} {'Yr':<5} {'Src':<12} {'Score':<6} {'Tier':<7} Title")
    print("-" * 110)

    for r in unique[:50]:
        doi_short = r["doi"][:33] + ".." if len(r.get("doi", "")) > 35 else r.get("doi", "")
        title_short = r["title"][:45] + ".." if len(r.get("title", "")) > 45 else r.get("title", "")
        score = r.get("_score", "?")
        tier = r.get("_tier", "?")
        print(f"{doi_short:<35} {str(r.get('year', '?')):<5} {r.get('source', '?')[:12]:<12} {str(score):<6} {tier:<7} {title_short}")

    # Output
    if args.export_bib:
        export_bibtex(unique, args.export_bib, tier_map)

    if args.output:
        with open(args.output, "w") as f:
            for r in unique:
                f.write(f"{r['doi']}\n")
        print(f"\nSaved {len(unique)} DOIs to {args.output}", flush=True)
    elif not args.export_bib:
        print(f"\nDOIs only:")
        for r in unique:
            print(f"  {r['doi']}")


if __name__ == "__main__":
    main()
