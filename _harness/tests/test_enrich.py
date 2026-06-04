import sys
from pathlib import Path
from unittest.mock import patch
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import enrich


@pytest.fixture
def wiki_root(tmp_path):
    (tmp_path / "paper.yaml").write_text("title: Test Paper\n")
    wiki_dir = tmp_path / "research" / "wiki"
    (wiki_dir / "topics").mkdir(parents=True)
    (wiki_dir / "papers").mkdir(parents=True)
    return tmp_path


def _make_topic(wiki_root, slug, bibkeys=("smith2024a",)):
    path = wiki_root / "research" / "wiki" / "topics" / f"{slug}.md"
    papers_list = "\n".join(f"- [[{k}]]" for k in bibkeys)
    path.write_text(f"# {slug.title()}\n\n## Papers\n{papers_list}\n")
    return path


def _make_paper(wiki_root, bibkey, abstract="A study of attention in hybrid work.", topics=()):
    path = wiki_root / "research" / "wiki" / "papers" / f"{bibkey}.md"
    topics_text = "\n".join(f"- [[{t}]]" for t in topics)
    path.write_text(
        f"---\nbibkey: {bibkey}\ntitle: Test\nauthors: []\nyear: 2024\n---\n\n"
        f"# Author (2024)\n\n{abstract}\n\n## Topics\n{topics_text}\n"
    )
    return path


_STUB_ENRICHMENT = "## Definition\nAttention is selective focus.\n\n## Synthesis\nPapers explore attention broadly."


def test_topic_without_definition_gets_definition_section(wiki_root):
    _make_topic(wiki_root, "attention", bibkeys=("smith2024a",))
    _make_paper(wiki_root, "smith2024a", abstract="Attention is the focus of this study.")

    with patch("enrich._call_claude", return_value=_STUB_ENRICHMENT):
        enrich.run(wiki_root)

    content = (wiki_root / "research" / "wiki" / "topics" / "attention.md").read_text()
    assert "## Definition" in content


def test_topic_without_synthesis_gets_synthesis_section(wiki_root):
    _make_topic(wiki_root, "attention", bibkeys=("smith2024a",))
    _make_paper(wiki_root, "smith2024a", abstract="Attention is the focus of this study.")

    with patch("enrich._call_claude", return_value=_STUB_ENRICHMENT):
        enrich.run(wiki_root)

    content = (wiki_root / "research" / "wiki" / "topics" / "attention.md").read_text()
    assert "## Synthesis" in content


def test_papers_section_preserved_after_enrichment(wiki_root):
    _make_topic(wiki_root, "attention", bibkeys=("smith2024a",))
    _make_paper(wiki_root, "smith2024a", abstract="Attention is the focus of this study.")

    with patch("enrich._call_claude", return_value=_STUB_ENRICHMENT):
        enrich.run(wiki_root)

    content = (wiki_root / "research" / "wiki" / "topics" / "attention.md").read_text()
    assert "## Papers" in content
    assert "[[smith2024a]]" in content


def test_already_enriched_topic_is_skipped(wiki_root):
    topic_path = _make_topic(wiki_root, "attention", bibkeys=("smith2024a",))
    topic_path.write_text(_STUB_ENRICHMENT + "\n\n# Attention\n\n## Papers\n- [[smith2024a]]\n")

    with patch("enrich._call_claude") as mock_claude:
        result = enrich.run(wiki_root)

    mock_claude.assert_not_called()
    assert result["skipped"] == 1
    assert result["enriched"] == 0


def test_force_flag_reenriches_already_enriched_topic(wiki_root):
    topic_path = _make_topic(wiki_root, "attention", bibkeys=("smith2024a",))
    topic_path.write_text(_STUB_ENRICHMENT + "\n\n# Attention\n\n## Papers\n- [[smith2024a]]\n")
    _make_paper(wiki_root, "smith2024a", abstract="Attention is the focus of this study.")

    with patch("enrich._call_claude", return_value=_STUB_ENRICHMENT) as mock_claude:
        result = enrich.run(wiki_root, force=True)

    mock_claude.assert_called_once()
    assert result["enriched"] == 1
    assert result["skipped"] == 0


def test_paper_gets_related_topics_section(wiki_root):
    _make_topic(wiki_root, "attention", bibkeys=("smith2024a",))
    paper_path = _make_paper(
        wiki_root, "smith2024a",
        abstract="Attention is the focus of this study.",
        topics=("attention",),
    )

    with patch("enrich._call_claude", return_value=_STUB_ENRICHMENT):
        enrich.run(wiki_root)

    content = paper_path.read_text()
    assert "## Related topics" in content
    assert "[[attention]]" in content


def test_related_topics_not_duplicated_on_second_run(wiki_root):
    _make_topic(wiki_root, "attention", bibkeys=("smith2024a",))
    _make_paper(
        wiki_root, "smith2024a",
        abstract="Attention is the focus of this study.",
        topics=("attention",),
    )

    with patch("enrich._call_claude", return_value=_STUB_ENRICHMENT):
        enrich.run(wiki_root)
        enrich.run(wiki_root, force=True)

    content = (wiki_root / "research" / "wiki" / "papers" / "smith2024a.md").read_text()
    assert content.count("## Related topics") == 1


def test_term_in_two_abstracts_creates_stub_topic(wiki_root):
    _make_paper(wiki_root, "paper1", abstract="Transformer models are widely used.")
    _make_paper(wiki_root, "paper2", abstract="Transformer models enable new applications.")

    with patch("enrich._call_claude", return_value=_STUB_ENRICHMENT):
        enrich.run(wiki_root)

    stub = wiki_root / "research" / "wiki" / "topics" / "transformer-models.md"
    assert stub.exists()


def test_term_in_one_abstract_does_not_create_stub(wiki_root):
    _make_paper(wiki_root, "paper1", abstract="Transformer models are widely used.")
    _make_paper(wiki_root, "paper2", abstract="An unrelated study of networks.")

    with patch("enrich._call_claude", return_value=_STUB_ENRICHMENT):
        enrich.run(wiki_root)

    stub = wiki_root / "research" / "wiki" / "topics" / "transformer-models.md"
    assert not stub.exists()


def test_enrich_min_papers_config_overrides_threshold(wiki_root):
    (wiki_root / "paper.yaml").write_text("title: Test\nenrich_min_papers: 1\n")
    _make_paper(wiki_root, "paper1", abstract="Transformer models are widely used.")

    with patch("enrich._call_claude", return_value=_STUB_ENRICHMENT):
        enrich.run(wiki_root)

    stub = wiki_root / "research" / "wiki" / "topics" / "transformer-models.md"
    assert stub.exists()
