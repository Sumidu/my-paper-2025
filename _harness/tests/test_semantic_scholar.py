import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib.semantic_scholar as ss


def _mock_response(data: dict, status: int = 200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


SS_PAPER = {
    "paperId": "abc123",
    "title": "Attention in Hybrid Work",
    "authors": [{"name": "Smith J"}, {"name": "Jones A"}],
    "year": 2024,
    "abstract": "We study attention.",
    "venue": "CHI",
    "citationCount": 42,
    "externalIds": {"DOI": "10.1145/xyz"},
}


def test_search_returns_normalized_papers():
    mock_resp = _mock_response({"data": [SS_PAPER], "total": 1})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        results = ss.search("attention hybrid work", limit=10)

    assert len(results) == 1
    p = results[0]
    assert p["title"] == "Attention in Hybrid Work"
    assert p["authors"] == ["Smith J", "Jones A"]
    assert p["year"] == 2024
    assert p["doi"] == "10.1145/xyz"
    assert p["citation_count"] == 42
    assert p["source"] == "semantic_scholar"
    assert p["bibkey"] == ""
    assert p["topics"] == []


def test_search_empty_results():
    mock_resp = _mock_response({"data": [], "total": 0})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        results = ss.search("nothing matches", limit=10)
    assert results == []


def test_search_graceful_on_missing_api_key(capsys):
    mock_resp = _mock_response({"data": [SS_PAPER], "total": 1})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        with patch.dict("os.environ", {}, clear=True):
            ss.search("test", limit=5)
    captured = capsys.readouterr()
    assert "SEMANTIC_SCHOLAR_API_KEY" in captured.out


def test_search_retries_on_429():
    rate_limited = MagicMock()
    rate_limited.status_code = 429
    rate_limited.raise_for_status = MagicMock()

    ok_resp = _mock_response({"data": [SS_PAPER], "total": 1})

    with patch("lib.semantic_scholar.requests.get", side_effect=[rate_limited, ok_resp]):
        with patch("lib.semantic_scholar.time.sleep"):
            results = ss.search("test", limit=5)
    assert len(results) == 1


def test_search_abstract_defaults_to_empty_string():
    paper_no_abstract = {**SS_PAPER, "abstract": None}
    mock_resp = _mock_response({"data": [paper_no_abstract], "total": 1})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        results = ss.search("test", limit=5)
    assert results[0]["abstract"] == ""


def test_search_missing_doi_is_none():
    paper_no_doi = {**SS_PAPER, "externalIds": {}}
    mock_resp = _mock_response({"data": [paper_no_doi], "total": 1})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        results = ss.search("test", limit=5)
    assert results[0]["doi"] is None
