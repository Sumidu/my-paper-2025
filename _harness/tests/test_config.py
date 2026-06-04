import pytest
from pathlib import Path
import yaml
import tempfile
import os

# Add scripts to path so lib imports work
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.config import load_config, PaperConfig, ZoteroConfig


@pytest.fixture
def tmp_root(tmp_path):
    """A temp directory with a minimal paper.yaml."""
    (tmp_path / "paper.yaml").write_text("title: Test Paper\n")
    return tmp_path


def test_load_minimal_config(tmp_root):
    config = load_config(tmp_root)
    assert config.title == "Test Paper"


def test_defaults_applied(tmp_root):
    config = load_config(tmp_root)
    assert config.target == "overleaf"
    assert config.csl == "apa.csl"
    assert config.citation_package == "natbib"
    assert config.language == "en"
    assert config.whisper_model == "large-v3-turbo"
    assert config.research_max_results == 200
    assert config.exclude_sections == []


def test_custom_values_override_defaults(tmp_root):
    (tmp_root / "paper.yaml").write_text(
        "title: My Paper\n"
        "language: de\n"
        "whisper_model: medium\n"
        "research_max_results: 50\n"
    )
    config = load_config(tmp_root)
    assert config.language == "de"
    assert config.whisper_model == "medium"
    assert config.research_max_results == 50


def test_missing_title_raises(tmp_root):
    (tmp_root / "paper.yaml").write_text("target: word\n")
    with pytest.raises(ValueError, match="title"):
        load_config(tmp_root)


def test_missing_yaml_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path)


def test_zotero_config_parsed(tmp_root):
    (tmp_root / "paper.yaml").write_text(
        "title: My Paper\n"
        "zotero:\n"
        "  collection: my-paper-2025\n"
        "  bibtex_export: ~/Zotero/exports/my-paper.bib\n"
    )
    config = load_config(tmp_root)
    assert config.zotero.collection == "my-paper-2025"
    assert config.zotero.bibtex_export == "~/Zotero/exports/my-paper.bib"


def test_exclude_sections_parsed(tmp_root):
    (tmp_root / "paper.yaml").write_text(
        "title: My Paper\nexclude_sections:\n  - 99_scratch\n"
    )
    config = load_config(tmp_root)
    assert config.exclude_sections == ["99_scratch"]


def test_word_target(tmp_root):
    (tmp_root / "paper.yaml").write_text("title: My Paper\ntarget: word\n")
    config = load_config(tmp_root)
    assert config.target == "word"
    assert config.overleaf_repo is None
