import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib.arxiv_client as arxiv

_ATOM_NS = "http://www.w3.org/2005/Atom"

def _make_atom_xml(entries: list[dict]) -> str:
    """Build minimal Atom feed XML from list of entry dicts."""
    items = []
    for e in entries:
        authors = "".join(
            f"<author><name>{a}</name></author>" for a in e.get("authors", [])
        )
        items.append(
            f"<entry>"
            f"<id>http://arxiv.org/abs/{e.get('arxiv_id', '2401.00001')}</id>"
            f"<title>{e.get('title', 'Test Title')}</title>"
            f"{authors}"
            f"<published>{e.get('published', '2024-01-15T00:00:00Z')}</published>"
            f"<summary>{e.get('abstract', 'A summary.')}</summary>"
            f"</entry>"
        )
    return (
        f'<?xml version="1.0"?>'
        f'<feed xmlns="{_ATOM_NS}">'
        + "".join(items)
        + "</feed>"
    )


def _mock_response(xml: str):
    resp = MagicMock()
    resp.text = xml
    resp.raise_for_status = MagicMock()
    return resp


def test_search_parses_title_and_authors():
    xml = _make_atom_xml([{
        "title": "Hybrid Work and Attention",
        "authors": ["Smith J", "Jones A"],
        "published": "2024-03-01T00:00:00Z",
        "abstract": "We study attention.",
    }])
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("attention", limit=5)
    assert len(results) == 1
    p = results[0]
    assert p["title"] == "Hybrid Work and Attention"
    assert p["authors"] == ["Smith J", "Jones A"]
    assert p["year"] == 2024
    assert p["source"] == "arxiv"
    assert p["doi"] is None
    assert p["bibkey"] == ""
    assert p["topics"] == []


def test_search_empty_feed():
    xml = _make_atom_xml([])
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("nothing", limit=5)
    assert results == []


def test_search_respects_limit():
    entries = [{"title": f"Paper {i}", "authors": ["A B"]} for i in range(10)]
    xml = _make_atom_xml(entries)
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("test", limit=5)
    assert len(results) == 5


def test_search_abstract_defaults_empty():
    xml = _make_atom_xml([{"title": "No Abstract", "authors": ["X Y"], "abstract": ""}])
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("test", limit=5)
    assert results[0]["abstract"] == ""


def test_search_citation_count_zero():
    xml = _make_atom_xml([{"title": "T", "authors": ["A"]}])
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("test", limit=5)
    assert results[0]["citation_count"] == 0
