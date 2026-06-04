from __future__ import annotations

import os
import time
import requests
from typing import Optional

_API_BASE = "https://api.semanticscholar.org/graph/v1"
_SIGNUP_URL = "https://www.semanticscholar.org/product/api"
_FIELDS = "title,authors,year,abstract,externalIds,venue,citationCount"


def _get_api_key() -> Optional[str]:
    return os.environ.get("SEMANTIC_SCHOLAR_API_KEY")


def _request_with_retry(
    url: str, params: dict, headers: dict, max_retries: int = 3
) -> requests.Response:
    for attempt in range(max_retries):
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 429:
            wait = 2 ** attempt
            print(f"Semantic Scholar rate limited. Waiting {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp
    resp.raise_for_status()
    return resp  # unreachable, satisfies type checkers


def _normalize(raw: dict) -> dict:
    """Convert Semantic Scholar API paper dict to shared paper dict format."""
    external = raw.get("externalIds") or {}
    return {
        "title": raw.get("title") or "",
        "authors": [a["name"] for a in (raw.get("authors") or [])],
        "year": raw.get("year") or 0,
        "doi": external.get("DOI"),
        "venue": raw.get("venue") or None,
        "abstract": raw.get("abstract") or "",
        "citation_count": raw.get("citationCount") or 0,
        "source": "semantic_scholar",
        "bibkey": "",
        "topics": [],
    }


def search(query: str, limit: int = 100) -> list[dict]:
    """Search Semantic Scholar. Returns list of normalized paper dicts."""
    api_key = _get_api_key()
    if api_key is None:
        print(
            f"No SEMANTIC_SCHOLAR_API_KEY found in environment. "
            f"Requests will be rate-limited.\n"
            f"Get a free key at: {_SIGNUP_URL}"
        )

    headers = {"x-api-key": api_key} if api_key else {}
    results: list[dict] = []
    offset = 0
    batch = min(limit, 100)

    while len(results) < limit:
        params = {
            "query": query,
            "limit": batch,
            "offset": offset,
            "fields": _FIELDS,
        }
        resp = _request_with_retry(
            f"{_API_BASE}/paper/search", params=params, headers=headers
        )
        data = resp.json()
        papers = data.get("data") or []
        if not papers:
            break
        results.extend(_normalize(p) for p in papers)
        offset += len(papers)
        if offset >= (data.get("total") or 0):
            break

    return results[:limit]
