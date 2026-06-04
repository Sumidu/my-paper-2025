import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.sections import discover_sections


@pytest.fixture
def sections_dir(tmp_path):
    d = tmp_path / "article" / "sections"
    d.mkdir(parents=True)
    return tmp_path


def make_section(root, name):
    (root / "article" / "sections" / f"{name}.md").write_text(f"# {name}\n")


def test_discovers_sections_sorted(sections_dir):
    make_section(sections_dir, "20_related_work")
    make_section(sections_dir, "10_abstract")
    make_section(sections_dir, "30_methodology")

    sections = discover_sections(sections_dir / "article")
    names = [s[1] for s in sections]
    assert names == ["10_abstract", "20_related_work", "30_methodology"]


def test_returns_number_name_path(sections_dir):
    make_section(sections_dir, "10_abstract")
    sections = discover_sections(sections_dir / "article")
    number, name, path = sections[0]
    assert number == 10
    assert name == "10_abstract"
    assert path.name == "10_abstract.md"


def test_excludes_listed_sections(sections_dir):
    make_section(sections_dir, "10_abstract")
    make_section(sections_dir, "99_scratch")

    sections = discover_sections(sections_dir / "article", exclude=["99_scratch"])
    names = [s[1] for s in sections]
    assert "99_scratch" not in names
    assert "10_abstract" in names


def test_empty_dir_returns_empty(sections_dir):
    sections = discover_sections(sections_dir / "article")
    assert sections == []


def test_missing_dir_returns_empty(tmp_path):
    sections = discover_sections(tmp_path / "article")
    assert sections == []


def test_non_matching_files_ignored(sections_dir):
    (sections_dir / "article" / "sections" / "README.md").write_text("docs")
    (sections_dir / "article" / "sections" / "notes.txt").write_text("notes")
    make_section(sections_dir, "10_abstract")

    sections = discover_sections(sections_dir / "article")
    assert len(sections) == 1
