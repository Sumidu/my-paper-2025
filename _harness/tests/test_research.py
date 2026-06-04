import sys
import csv
from pathlib import Path
from unittest.mock import patch
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import research


@pytest.fixture
def paper_root(tmp_path):
    (tmp_path / "paper.yaml").write_text("title: Test Paper\n")
    wiki_dir = tmp_path / "research" / "wiki"
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "index.md").write_text(
        "---\nresearch_question: How?\nkeywords:\n  - attention\n  - notifications\ncontribution: novel\n---\n\n## Summary\nText.\n"
    )
    return tmp_path


def _fake_paper(title: str, doi: str | None = None, citations: int = 0, source: str = "semantic_scholar") -> dict:
    return {
        "title": title,
        "authors": ["Smith J"],
        "year": 2024,
        "doi": doi,
        "venue": "CHI",
        "abstract": f"We study attention and notifications in {title}.",
        "citation_count": citations,
        "source": source,
        "bibkey": "",
        "topics": [],
    }


def test_first_sentences_returns_two_sentences():
    text = "This is the first sentence. This is the second. This is the third."
    assert research._first_sentences(text, n=2) == "This is the first sentence. This is the second."


def test_first_sentences_handles_short_abstract():
    text = "Only one sentence here."
    assert research._first_sentences(text, n=2) == "Only one sentence here."


def test_first_sentences_handles_empty():
    assert research._first_sentences("", n=2) == ""


def test_candidates_md_shows_first_two_sentences(paper_root):
    abstract = "First claim. Second claim. Third claim that should be omitted."
    fake = _fake_paper("Abstract Test")
    fake["abstract"] = abstract

    with patch("research.semantic_scholar.search", return_value=[fake]), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        research.run(paper_root)

    md = (paper_root / "research" / "candidates.md").read_text()
    assert "First claim. Second claim." in md
    assert "Third claim" not in md


def test_candidates_md_no_abstract_shows_placeholder(paper_root):
    fake = _fake_paper("No Abstract")
    fake["abstract"] = ""

    with patch("research.semantic_scholar.search", return_value=[fake]), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        research.run(paper_root)

    md = (paper_root / "research" / "candidates.md").read_text()
    assert "_No abstract available._" in md


def test_run_creates_candidates_files(paper_root):
    fake_ss = [_fake_paper("Attention Study", doi="10.1145/1", citations=10)]
    fake_arxiv = [_fake_paper("Notification Study", source="arxiv")]

    with patch("research.semantic_scholar.search", return_value=fake_ss), \
         patch("research.arxiv_client.search", return_value=fake_arxiv), \
         patch("research.google_scholar.search", return_value=[]):
        result = research.run(paper_root)

    assert (paper_root / "research" / "candidates.md").exists()
    assert (paper_root / "research" / "candidates.bib").exists()
    assert (paper_root / "research" / "scopus-query.txt").exists()
    assert result["papers"] == 2


def test_run_creates_wiki_nodes(paper_root):
    fake_ss = [_fake_paper("Attention Study", doi="10.1145/1")]

    with patch("research.semantic_scholar.search", return_value=fake_ss), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        research.run(paper_root)

    papers_dir = paper_root / "research" / "wiki" / "papers"
    assert len(list(papers_dir.glob("*.md"))) == 1


def test_deduplication_by_doi(paper_root):
    p1 = _fake_paper("Paper A", doi="10.1/same", citations=5)
    p2 = _fake_paper("Paper A different title", doi="10.1/same", citations=3)

    with patch("research.semantic_scholar.search", return_value=[p1, p2]), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        result = research.run(paper_root)

    assert result["papers"] == 1


def test_deduplication_by_normalized_title(paper_root):
    p1 = _fake_paper("Attention and Work")
    p2 = _fake_paper("Attention and Work")  # exact duplicate, no DOI

    with patch("research.semantic_scholar.search", return_value=[p1, p2]), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        result = research.run(paper_root)

    assert result["papers"] == 1


def test_scopus_csv_merged(paper_root):
    scopus_path = paper_root / "research" / "scopus-export.csv"
    scopus_path.parent.mkdir(parents=True, exist_ok=True)
    with scopus_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Authors", "Year", "DOI", "Source title", "Abstract", "Cited by"])
        writer.writeheader()
        writer.writerow({
            "Title": "Scopus Paper",
            "Authors": "Brown C",
            "Year": "2023",
            "DOI": "10.1/scopus",
            "Source title": "CSCW",
            "Abstract": "A Scopus paper about notifications.",
            "Cited by": "7",
        })

    with patch("research.semantic_scholar.search", return_value=[]), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        result = research.run(paper_root)

    assert result["papers"] == 1
    bib = (paper_root / "research" / "candidates.bib").read_text()
    assert "brown2023scopus" in bib


def test_scopus_single_initial_author_formatted_with_comma(paper_root):
    scopus_path = paper_root / "research" / "scopus-export.csv"
    scopus_path.parent.mkdir(parents=True, exist_ok=True)
    with scopus_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Authors", "Year", "DOI", "Source title", "Abstract", "Cited by"])
        writer.writeheader()
        writer.writerow({
            "Title": "Test Paper",
            "Authors": "Jiang F.",
            "Year": "2026",
            "DOI": "10.1/test",
            "Source title": "IEEE JSAC",
            "Abstract": "An abstract about attention.",
            "Cited by": "0",
        })

    with patch("research.semantic_scholar.search", return_value=[]), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        research.run(paper_root)

    bib = (paper_root / "research" / "candidates.bib").read_text()
    assert "author = {Jiang, F.}" in bib


def test_scopus_multi_initial_author_formatted_with_comma(paper_root):
    scopus_path = paper_root / "research" / "scopus-export.csv"
    scopus_path.parent.mkdir(parents=True, exist_ok=True)
    with scopus_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Authors", "Year", "DOI", "Source title", "Abstract", "Cited by"])
        writer.writeheader()
        writer.writerow({
            "Title": "Multi Initial Paper",
            "Authors": "Dobre O.A.",
            "Year": "2026",
            "DOI": "10.1/multi",
            "Source title": "IEEE JSAC",
            "Abstract": "An abstract about notifications.",
            "Cited by": "0",
        })

    with patch("research.semantic_scholar.search", return_value=[]), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        research.run(paper_root)

    bib = (paper_root / "research" / "candidates.bib").read_text()
    assert "author = {Dobre, O.A.}" in bib


def test_no_index_md_returns_empty(paper_root):
    (paper_root / "research" / "wiki" / "index.md").unlink()
    result = research.run(paper_root)
    assert result == {}


def test_scopus_query_contains_keywords(paper_root):
    with patch("research.semantic_scholar.search", return_value=[]), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        research.run(paper_root)

    query = (paper_root / "research" / "scopus-query.txt").read_text()
    assert "attention" in query
    assert "notifications" in query


def test_candidates_bib_valid_bibtex(paper_root):
    fake_ss = [_fake_paper("BibTeX Test", doi="10.1/bib", citations=1)]
    with patch("research.semantic_scholar.search", return_value=fake_ss), \
         patch("research.arxiv_client.search", return_value=[]), \
         patch("research.google_scholar.search", return_value=[]):
        research.run(paper_root)

    bib = (paper_root / "research" / "candidates.bib").read_text()
    assert "@" in bib
    assert "title" in bib.lower()
