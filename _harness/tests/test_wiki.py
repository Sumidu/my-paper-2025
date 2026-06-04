import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.wiki import (
    read_index_meta,
    write_paper_node,
    ensure_topic_stub,
    IndexMeta,
)


@pytest.fixture
def wiki_dir(tmp_path):
    d = tmp_path / "research" / "wiki"
    d.mkdir(parents=True)
    return d


def test_read_index_meta_parses_front_matter(wiki_dir):
    (wiki_dir / "index.md").write_text(
        "---\nresearch_question: How?\nkeywords:\n  - attention\n  - hybrid work\ncontribution: novel\n---\n\n## Summary\n"
    )
    meta = read_index_meta(wiki_dir)
    assert meta.research_question == "How?"
    assert meta.keywords == ["attention", "hybrid work"]
    assert meta.contribution == "novel"


def test_read_index_meta_missing_returns_none(wiki_dir):
    assert read_index_meta(wiki_dir) is None


def test_read_index_meta_no_front_matter_returns_none(wiki_dir):
    (wiki_dir / "index.md").write_text("# Just a heading\n")
    assert read_index_meta(wiki_dir) is None


def test_write_paper_node_creates_file(wiki_dir):
    paper = {
        "bibkey": "smith2024attention",
        "title": "Attention in Hybrid Work",
        "authors": ["Smith J", "Jones A"],
        "year": 2024,
        "doi": "10.1145/xyz",
        "venue": "CHI",
        "abstract": "A study of attention.",
        "topics": ["attention", "hybrid-work"],
    }
    write_paper_node(wiki_dir, paper)
    path = wiki_dir / "papers" / "smith2024attention.md"
    assert path.exists()
    content = path.read_text()
    assert "smith2024attention" in content
    assert "Attention in Hybrid Work" in content
    assert "[[attention]]" in content
    assert "[[hybrid-work]]" in content


def test_write_paper_node_idempotent(wiki_dir):
    paper = {
        "bibkey": "jones2023note",
        "title": "Notes",
        "authors": ["Jones B"],
        "year": 2023,
        "doi": None,
        "venue": None,
        "abstract": "Short.",
        "topics": [],
    }
    write_paper_node(wiki_dir, paper)
    write_paper_node(wiki_dir, paper)
    files = list((wiki_dir / "papers").glob("*.md"))
    assert len(files) == 1


def test_ensure_topic_stub_creates_file(wiki_dir):
    ensure_topic_stub(wiki_dir, "attention", "smith2024attention")
    path = wiki_dir / "topics" / "attention.md"
    assert path.exists()
    assert "[[smith2024attention]]" in path.read_text()


def test_ensure_topic_stub_appends_to_existing(wiki_dir):
    ensure_topic_stub(wiki_dir, "attention", "smith2024attention")
    ensure_topic_stub(wiki_dir, "attention", "jones2023note")
    content = (wiki_dir / "topics" / "attention.md").read_text()
    assert "[[smith2024attention]]" in content
    assert "[[jones2023note]]" in content


def test_ensure_topic_stub_no_duplicate_bibkey(wiki_dir):
    ensure_topic_stub(wiki_dir, "attention", "smith2024attention")
    ensure_topic_stub(wiki_dir, "attention", "smith2024attention")
    content = (wiki_dir / "topics" / "attention.md").read_text()
    assert content.count("[[smith2024attention]]") == 1


def test_topic_slug_replaces_spaces(wiki_dir):
    ensure_topic_stub(wiki_dir, "hybrid work", "smith2024attention")
    path = wiki_dir / "topics" / "hybrid-work.md"
    assert path.exists()
