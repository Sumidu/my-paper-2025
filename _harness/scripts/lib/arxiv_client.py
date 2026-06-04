from __future__ import annotations

import time
import requests
import xml.etree.ElementTree as ET

_API_BASE = "https://export.arxiv.org/api/query"
_ATOM = "http://www.w3.org/2005/Atom"
_COURTESY_DELAY = 3  # seconds between paginated requests (arXiv policy)


def _parse_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall(f"{{{_ATOM}}}entry"):
        title_el = entry.find(f"{{{_ATOM}}}title")
        title = (title_el.text or "").strip() if title_el is not None else ""

        authors = [
            (name_el.text or "").strip()
            for author_el in entry.findall(f"{{{_ATOM}}}author")
            for name_el in [author_el.find(f"{{{_ATOM}}}name")]
            if name_el is not None
        ]

        published_el = entry.find(f"{{{_ATOM}}}published")
        year = 0
        if published_el is not None and published_el.text:
            try:
                year = int(published_el.text[:4])
            except ValueError:
                year = 0

        summary_el = entry.find(f"{{{_ATOM}}}summary")
        abstract = (summary_el.text or "").strip() if summary_el is not None else ""

        papers.append({
            "title": title,
            "authors": authors,
            "year": year,
            "doi": None,
            "venue": "arXiv",
            "abstract": abstract,
            "citation_count": 0,
            "source": "arxiv",
            "bibkey": "",
            "topics": [],
        })
    return papers


def search(query: str, limit: int = 100) -> list[dict]:
    """Search arXiv. Returns list of normalized paper dicts."""
    results: list[dict] = []
    start = 0
    batch = min(limit, 100)

    while len(results) < limit:
        params = {
            "search_query": f"all:{query}",
            "start": start,
            "max_results": batch,
        }
        resp = requests.get(_API_BASE, params=params)
        resp.raise_for_status()

        entries = _parse_feed(resp.text)
        if not entries:
            break
        results.extend(entries)
        start += len(entries)

        if len(entries) < batch:
            break
        if len(results) < limit:
            time.sleep(_COURTESY_DELAY)

    return results[:limit]
