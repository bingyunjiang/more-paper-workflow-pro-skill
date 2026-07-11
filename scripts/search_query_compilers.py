#!/usr/bin/env python3
"""Compile concept-block queries using verified, endpoint-specific syntax."""

from __future__ import annotations

import re
from typing import Any


def _terms(block: dict[str, Any]) -> list[str]:
    return [str(item).strip() for item in block.get("terms", []) if str(item).strip()]


def _quote(term: str) -> str:
    return f'"{term}"' if re.search(r"\s", term) else term


def _boolean_query(blocks: list[dict[str, Any]], exclusions: list[str], *, not_operator: str = "NOT") -> str:
    positive = ["(" + " OR ".join(_quote(term) for term in _terms(block)) + ")" for block in blocks if _terms(block)]
    query = " AND ".join(positive)
    if exclusions:
        query += f" {not_operator} (" + " OR ".join(_quote(term) for term in exclusions) + ")"
    return query.strip()


def _plain_relevance_query(blocks: list[dict[str, Any]]) -> str:
    # Plain relevance endpoints cannot preserve within-block OR. Use one canonical
    # term per block and require concept-block post-filtering on returned records.
    canonical = [_terms(block)[0].replace("-", " ") for block in blocks if _terms(block)]
    return " ".join(_quote(term) for term in canonical)


def compile_source_query(blocks: list[dict[str, Any]], exclusions: list[str], source: str) -> dict[str, Any]:
    source = source.strip().lower()
    exclusions = [str(item).strip() for item in exclusions if str(item).strip()]

    if source == "openalex":
        query = _boolean_query(blocks, exclusions)
        return _result(source, query, "exact", request={"endpoint": "/works", "parameter": "search", "value": query})

    if source == "semantic_scholar_bulk":
        positive = ["(" + " | ".join(_quote(term.replace("-", " ")) for term in _terms(block)) + ")" for block in blocks if _terms(block)]
        query = " + ".join(positive)
        if exclusions:
            query += " " + " ".join("-" + _quote(term.replace("-", " ")) for term in exclusions)
        return _result(source, query.strip(), "exact", request={"endpoint": "/paper/search/bulk", "parameter": "query", "value": query.strip()})

    if source == "semantic_scholar":
        query = _plain_relevance_query(blocks)
        return _result(
            source, query, "degraded",
            dropped=["within_block_or", "server_side_not", "exact_phrase_contract"],
            post_filter=True,
            reason="/paper/search accepts plain text and officially supports no special query syntax",
            request={"endpoint": "/paper/search", "parameter": "query", "value": query},
        )

    if source == "crossref":
        query = " ".join(term for block in blocks for term in _terms(block))
        return _result(
            source, query, "degraded",
            dropped=["within_block_or", "between_block_and", "server_side_not", "exact_phrase_contract"],
            post_filter=True,
            reason="Crossref query.title is a relevance query; set-Boolean semantics were not verified",
            request={"endpoint": "/works", "parameter": "query.title", "value": query},
        )

    if source == "pubmed":
        positive = ["(" + " OR ".join(f"{_quote(term)}[tiab]" for term in _terms(block)) + ")" for block in blocks if _terms(block)]
        query = " AND ".join(positive)
        if exclusions:
            query += " NOT (" + " OR ".join(f"{_quote(term)}[tiab]" for term in exclusions) + ")"
        return _result(source, query.strip(), "exact", warnings=["PubMed phrase-index and Automatic Term Mapping behavior must be reviewed"], request={"parameter": "term", "value": query.strip()})

    if source == "arxiv":
        positive = ["(" + " OR ".join(f"all:{_quote(term)}" for term in _terms(block)) + ")" for block in blocks if _terms(block)]
        query = " AND ".join(positive)
        if exclusions:
            query += " ANDNOT (" + " OR ".join(f"all:{_quote(term)}" for term in exclusions) + ")"
        return _result(source, query.strip(), "exact", request={"endpoint": "/api/query", "parameter": "search_query", "value": query.strip()})

    if source in {"cnki", "wanfang"}:
        query = _boolean_query(blocks, exclusions)
        return _result(
            source, query, "manual_required",
            reason=f"{source} is executed through a CDP web adapter without a verified stable public API contract",
            warnings=["default workflow scope is Chinese-language records", "re-probe after UI signature changes"],
        )

    return _result(source, "", "invalid", reason="no verified source compiler is registered")


def _result(
    source: str,
    query: str,
    status: str,
    *,
    dropped: list[str] | None = None,
    post_filter: bool = False,
    reason: str = "",
    warnings: list[str] | None = None,
    request: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "query": query,
        "compile_status": status,
        "dropped_semantics": dropped or [],
        "post_filter_required": post_filter,
        "degradation_reason": reason,
        "warnings": warnings or [],
        "request": request or {},
    }

