from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib.google_scholar as gs


def _make_pub(title="Test Paper", year="2023", abstract="Some abstract", citations=5, doi=None):
    return {
        "bib": {
            "title": title,
            "author": "Smith J and Jones A",
            "pub_year": year,
            "abstract": abstract,
            "venue": "CHI",
        },
        "num_citations": citations,
        "doi": doi,
    }


def _mock_scholarly_module(pubs: list[dict], fill_raises: Exception | None = None):
    mock = MagicMock()
    mock.search_pubs.return_value = iter(pubs)
    if fill_raises:
        mock.fill.side_effect = fill_raises
    else:
        mock.fill.side_effect = lambda pub: pub
    return mock


def test_search_returns_normalized_papers():
    pub = _make_pub(title="Attention in Hybrid Work", citations=42)
    mock_s = _mock_scholarly_module([pub])

    with patch.object(gs, "_SCHOLARLY_AVAILABLE", True), \
         patch.object(gs, "_scholarly", mock_s), \
         patch.object(gs, "_try_enable_tor", return_value=False), \
         patch("lib.google_scholar.time.sleep"):
        results = gs.search("attention hybrid work", limit=1)

    assert len(results) == 1
    p = results[0]
    assert p["title"] == "Attention in Hybrid Work"
    assert p["authors"] == ["Smith J", "Jones A"]
    assert p["year"] == 2023
    assert p["citation_count"] == 42
    assert p["source"] == "google_scholar"


def test_search_returns_empty_when_scholarly_unavailable(capsys):
    with patch.object(gs, "_SCHOLARLY_AVAILABLE", False):
        results = gs.search("test", limit=5)
    assert results == []
    assert "scholarly not installed" in capsys.readouterr().out


def test_fill_failure_returns_partial_data():
    pub = _make_pub(title="Partial Paper")
    mock_s = _mock_scholarly_module([pub], fill_raises=Exception("connection error"))

    with patch.object(gs, "_SCHOLARLY_AVAILABLE", True), \
         patch.object(gs, "_scholarly", mock_s), \
         patch.object(gs, "_try_enable_tor", return_value=False), \
         patch("lib.google_scholar.time.sleep"):
        results = gs.search("test", limit=1)

    assert len(results) == 1
    assert results[0]["title"] == "Partial Paper"


def test_captcha_returns_partial_results(capsys):
    def search_pubs_with_captcha(query):
        yield _make_pub(title="Paper 0")
        yield _make_pub(title="Paper 1")
        raise Exception("CAPTCHA detected")

    mock_s = MagicMock()
    mock_s.search_pubs.side_effect = search_pubs_with_captcha
    mock_s.fill.side_effect = lambda pub: pub

    with patch.object(gs, "_SCHOLARLY_AVAILABLE", True), \
         patch.object(gs, "_scholarly", mock_s), \
         patch.object(gs, "_try_enable_tor", return_value=False), \
         patch("lib.google_scholar.time.sleep"):
        results = gs.search("test", limit=10)

    assert len(results) == 2
    assert "CAPTCHA" in capsys.readouterr().out


def test_tor_enabled_uses_shorter_delay():
    pub = _make_pub()
    mock_s = _mock_scholarly_module([pub])
    sleep_calls = []

    with patch.object(gs, "_SCHOLARLY_AVAILABLE", True), \
         patch.object(gs, "_scholarly", mock_s), \
         patch.object(gs, "_try_enable_tor", return_value=True), \
         patch("lib.google_scholar.time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        gs.search("test", limit=1)

    # limit=1 means no sleep after the only result
    assert all(s <= gs._TOR_DELAY for s in sleep_calls)


def test_fallback_delay_used_without_tor():
    pubs = [_make_pub(title=f"Paper {i}") for i in range(2)]
    mock_s = _mock_scholarly_module(pubs)
    sleep_calls = []

    with patch.object(gs, "_SCHOLARLY_AVAILABLE", True), \
         patch.object(gs, "_scholarly", mock_s), \
         patch.object(gs, "_try_enable_tor", return_value=False), \
         patch("lib.google_scholar.time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        gs.search("test", limit=2)

    assert len(sleep_calls) == 1
    assert sleep_calls[0] == gs._FALLBACK_DELAY


def test_normalize_handles_list_authors():
    pub = {
        "bib": {
            "title": "Paper",
            "author": ["Alice", "Bob"],
            "pub_year": "2022",
            "abstract": "",
            "venue": None,
        },
        "num_citations": 0,
        "doi": None,
    }
    result = gs._normalize(pub)
    assert result["authors"] == ["Alice", "Bob"]


def test_normalize_missing_year_defaults_to_zero():
    pub = {"bib": {"title": "X", "author": ""}, "num_citations": 0, "doi": None}
    result = gs._normalize(pub)
    assert result["year"] == 0
