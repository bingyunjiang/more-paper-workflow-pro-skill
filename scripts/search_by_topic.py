#!/usr/bin/env python3
"""
Search academic papers by topic across multiple sources.
Outputs a DOI list ready for Phase 1 (PII resolution) + Phase 2 (download).

Usage:
  python3 search_by_topic.py "battery thermal management spray cooling" --limit 20
  python3 search_by_topic.py "liquid cooling plate optimization" --source semantic --limit 50
  python3 search_by_topic.py "machine learning reduced order model heat transfer" --source crossref --limit 30 --output my_dois.txt
"""
import json, urllib.request, urllib.parse, time, sys, re

def search_semantic_scholar(query, limit=20):
    """Search Semantic Scholar API. Free, no key needed for basic search."""
    params = urllib.parse.urlencode({
        "q": query,
        "limit": min(limit, 100),
        "fields": "title,authors,externalIds,year,venue"
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
        if doi:
            results.append({"doi": doi, "title": title, "year": year, "venue": venue, "source": "semantic"})
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
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0 (mailto:research@example.com)"})
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
        year = (item.get("published-print") or item.get("issued") or {}).get("date-parts", [["?"]])[0][0]
        publisher = item.get("publisher", "?")
        if doi:
            results.append({"doi": doi, "title": title, "year": year, "venue": publisher, "source": "crossref"})
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
        venue = (p.get("primary_location") or {}).get("source", {}).get("display_name", "?")
        if doi:
            results.append({"doi": doi, "title": title, "year": year, "venue": venue, "source": "openalex"})
    return results


# === Main ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Search academic papers by topic")
    parser.add_argument("query", help="Search query (e.g. 'battery thermal management spray cooling')")
    parser.add_argument("--source", choices=["semantic", "crossref", "openalex", "all"], default="all",
                        help="Search source (default: all three)")
    parser.add_argument("--limit", type=int, default=20, help="Max results per source (default: 20)")
    parser.add_argument("--output", "-o", help="Output file (default: print to stdout)")
    parser.add_argument("--include-no-doi", action="store_true", help="Include results without DOIs")
    args = parser.parse_args()

    print(f"Searching: {args.query}", flush=True)

    all_results = []
    if args.source in ("semantic", "all"):
        print("  Querying Semantic Scholar...", flush=True)
        all_results += search_semantic_scholar(args.query, args.limit)
    if args.source in ("crossref", "all"):
        print("  Querying Crossref...", flush=True)
        all_results += search_crossref(args.query, args.limit)
    if args.source in ("openalex", "all"):
        print("  Querying OpenAlex...", flush=True)
        all_results += search_openalex(args.query, args.limit)

    # Deduplicate by DOI
    seen = set()
    unique = []
    for r in all_results:
        if r["doi"] not in seen:
            seen.add(r["doi"])
            unique.append(r)

    unique.sort(key=lambda x: -int(x.get("year", 0) or 0))

    if not args.include_no_doi:
        unique = [r for r in unique if r["doi"]]

    print(f"\nFound {len(unique)} unique papers (across {len(all_results)} raw hits):")
    print(f"{'DOI':<35} {'Year':<5} {'Source':<10} Title")
    print("-" * 100)
    for r in unique[:30]:
        doi_short = r["doi"][:33] + ".." if len(r["doi"]) > 35 else r["doi"]
        title_short = r["title"][:45] + ".." if len(r["title"]) > 45 else r["title"]
        print(f"{doi_short:<35} {str(r['year']):<5} {r['source']:<10} {title_short}")

    # Output
    if args.output:
        with open(args.output, "w") as f:
            for r in unique:
                f.write(f"{r['doi']}\n")
        print(f"\nSaved {len(unique)} DOIs to {args.output}", flush=True)
    else:
        print(f"\nDOIs only:")
        for r in unique:
            print(f"  {r['doi']}")
