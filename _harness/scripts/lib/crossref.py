from __future__ import annotations

import re
import time
import requests
from typing import Optional

_API_BASE = "https://api.crossref.org/works"
_MAILTO = "paperharness@example.com"
_COURTESY_DELAY = 1  # seconds between requests (polite pool)


def _get(url: str, params: dict) -> Optional[dict]:
    params["mailto"] = _MAILTO
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def _normalize_title(title: str) -> str:
    return re.sub(r"\W+", " ", title).strip().lower()


def lookup_doi(doi: str) -> Optional[dict]:
    """Fetch CrossRef metadata for a DOI. Returns normalized dict or None."""
    data = _get(f"{_API_BASE}/{doi}", {})
    if not data:
        return None
    return _parse_work(data.get("message") or {})


def search_title(title: str, rows: int = 3) -> list[dict]:
    """Search CrossRef by title. Returns up to `rows` normalized results."""
    data = _get(_API_BASE, {"query.bibliographic": title, "rows": rows})
    if not data:
        return []
    items = (data.get("message") or {}).get("items") or []
    return [_parse_work(w) for w in items]


def _parse_work(work: dict) -> dict:
    titles = work.get("title") or []
    title = titles[0] if titles else ""

    authors = []
    for a in work.get("author") or []:
        family = a.get("family") or ""
        given = a.get("given") or ""
        authors.append(f"{given} {family}".strip() if given else family)

    date_parts = ((work.get("published") or work.get("published-print") or
                   work.get("published-online") or {}).get("date-parts") or [[]])
    year = date_parts[0][0] if date_parts and date_parts[0] else 0

    container = work.get("container-title") or []
    venue = container[0] if container else None

    return {
        "doi": work.get("DOI"),
        "title": title,
        "authors": authors,
        "year": int(year) if year else 0,
        "venue": venue,
        "type": work.get("type"),
    }


def title_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity between two titles, 0.0–1.0."""
    wa = set(_normalize_title(a).split())
    wb = set(_normalize_title(b).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)
