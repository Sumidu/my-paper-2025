from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import verifylibrary as vl


BIB_WITH_DOI = """
@article{smith2023attention,
  title = {Attention in Hybrid Work},
  author = {Smith J and Jones A},
  year = {2023},
  doi = {10.1145/abc},
  journal = {CHI},
}
"""

BIB_NO_DOI = """
@article{jones2022work,
  title = {Notifications and Work},
  author = {Jones A},
  year = {2022},
  journal = {CSCW},
}
"""

BIB_MULTIPLE = BIB_WITH_DOI + BIB_NO_DOI


# ---------------------------------------------------------------------------
# parse_bib
# ---------------------------------------------------------------------------

def test_parse_bib_extracts_bibkey():
    entries = vl.parse_bib(BIB_WITH_DOI)
    assert len(entries) == 1
    assert entries[0]["bibkey"] == "smith2023attention"


def test_parse_bib_extracts_doi():
    entries = vl.parse_bib(BIB_WITH_DOI)
    assert entries[0]["doi"] == "10.1145/abc"


def test_parse_bib_extracts_title():
    entries = vl.parse_bib(BIB_WITH_DOI)
    assert "Attention" in entries[0]["title"]


def test_parse_bib_no_doi_returns_empty_string():
    entries = vl.parse_bib(BIB_NO_DOI)
    assert entries[0]["doi"] == ""


def test_parse_bib_multiple_entries():
    entries = vl.parse_bib(BIB_MULTIPLE)
    assert len(entries) == 2


# ---------------------------------------------------------------------------
# patch_doi / patch_year
# ---------------------------------------------------------------------------

def test_patch_doi_adds_doi_field():
    result = vl.patch_doi(BIB_NO_DOI, "jones2022work", "10.1/new")
    assert "10.1/new" in result


def test_patch_doi_replaces_existing_doi():
    result = vl.patch_doi(BIB_WITH_DOI, "smith2023attention", "10.1/new")
    assert "10.1/new" in result
    assert "10.1145/abc" not in result


def test_patch_year_updates_year():
    result = vl.patch_year(BIB_WITH_DOI, "smith2023attention", 2024)
    assert "{2024}" in result
    assert "{2023}" not in result


# ---------------------------------------------------------------------------
# _verify_entry — DOI paths
# ---------------------------------------------------------------------------

CR_MATCH = {
    "doi": "10.1145/abc",
    "title": "Attention in Hybrid Work",
    "authors": ["Smith J"],
    "year": 2023,
    "venue": "CHI",
    "type": "journal-article",
}


def test_verify_entry_verified_when_doi_matches():
    with patch("verifylibrary.crossref.lookup_doi", return_value=CR_MATCH), \
         patch("verifylibrary.time.sleep"):
        result = vl._verify_entry(vl.parse_bib(BIB_WITH_DOI)[0])
    assert result["status"] == "verified"


def test_verify_entry_doi_not_found():
    with patch("verifylibrary.crossref.lookup_doi", return_value=None), \
         patch("verifylibrary.time.sleep"):
        result = vl._verify_entry(vl.parse_bib(BIB_WITH_DOI)[0])
    assert result["status"] == "doi_not_found"


def test_verify_entry_year_mismatch_minor():
    cr = {**CR_MATCH, "year": 2022}
    with patch("verifylibrary.crossref.lookup_doi", return_value=cr), \
         patch("verifylibrary.time.sleep"):
        result = vl._verify_entry(vl.parse_bib(BIB_WITH_DOI)[0])
    assert result["status"] == "year_mismatch_minor"
    assert result["crossref_year"] == 2022


def test_verify_entry_year_mismatch_major():
    cr = {**CR_MATCH, "year": 2019}
    with patch("verifylibrary.crossref.lookup_doi", return_value=cr), \
         patch("verifylibrary.time.sleep"):
        result = vl._verify_entry(vl.parse_bib(BIB_WITH_DOI)[0])
    assert result["status"] == "year_mismatch_major"


def test_verify_entry_title_mismatch():
    cr = {**CR_MATCH, "title": "A Completely Different Paper About Rockets"}
    with patch("verifylibrary.crossref.lookup_doi", return_value=cr), \
         patch("verifylibrary.time.sleep"):
        result = vl._verify_entry(vl.parse_bib(BIB_WITH_DOI)[0])
    assert result["status"] == "title_mismatch"


# ---------------------------------------------------------------------------
# _verify_entry — no DOI (title search) paths
# ---------------------------------------------------------------------------

CR_TITLE_MATCH = {
    "doi": "10.1/found",
    "title": "Notifications and Work",
    "authors": ["Jones A"],
    "year": 2022,
    "venue": "CSCW",
    "type": "proceedings-article",
}


def test_verify_entry_missing_doi_found_by_title():
    with patch("verifylibrary.crossref.search_title", return_value=[CR_TITLE_MATCH]), \
         patch("verifylibrary.time.sleep"):
        result = vl._verify_entry(vl.parse_bib(BIB_NO_DOI)[0])
    assert result["status"] == "missing_doi"
    assert result["crossref_doi"] == "10.1/found"


def test_verify_entry_not_found_when_no_title_match():
    poor_match = {**CR_TITLE_MATCH, "title": "Something Completely Unrelated"}
    with patch("verifylibrary.crossref.search_title", return_value=[poor_match]), \
         patch("verifylibrary.time.sleep"):
        result = vl._verify_entry(vl.parse_bib(BIB_NO_DOI)[0])
    assert result["status"] == "not_found"


def test_verify_entry_not_found_when_search_empty():
    with patch("verifylibrary.crossref.search_title", return_value=[]), \
         patch("verifylibrary.time.sleep"):
        result = vl._verify_entry(vl.parse_bib(BIB_NO_DOI)[0])
    assert result["status"] == "not_found"


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

@pytest.fixture
def paper_root(tmp_path):
    (tmp_path / "paper.yaml").write_text("title: Test\n")
    research = tmp_path / "research"
    research.mkdir()
    (research / "candidates.bib").write_text(BIB_WITH_DOI)
    return tmp_path


def test_run_writes_report(paper_root):
    with patch("verifylibrary.crossref.lookup_doi", return_value=CR_MATCH), \
         patch("verifylibrary.time.sleep"):
        vl.run(paper_root)
    report = paper_root / "research" / "verify-report.json"
    assert report.exists()
    data = json.loads(report.read_text())
    assert "verified" in data


def test_run_returns_empty_when_no_bib(tmp_path):
    (tmp_path / "paper.yaml").write_text("title: Test\n")
    result = vl.run(tmp_path)
    assert result == {}
