from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import deploy


@pytest.fixture
def paper_root(tmp_path):
    (tmp_path / "paper.yaml").write_text(
        "title: Test Paper\ntarget: overleaf\ncitation_package: natbib\n"
    )
    (tmp_path / "article" / "sections").mkdir(parents=True)
    (tmp_path / "article" / "output").mkdir(parents=True)
    (tmp_path / "article" / "figures").mkdir()
    (tmp_path / "research").mkdir()
    return tmp_path


def make_section(root, name, content="# Test\n\nContent.\n"):
    (root / "article" / "sections" / f"{name}.md").write_text(content)


@patch("deploy.subprocess.run")
def test_compile_abstract_wraps_in_env(mock_run, tmp_path):
    mock_run.return_value = MagicMock(stdout="This is my abstract.\n", returncode=0)
    abstract = tmp_path / "10_abstract.md"
    abstract.write_text("# Abstract\n\nThis is my abstract.\n")
    result = deploy._compile_abstract(abstract)
    assert result.startswith("\\begin{abstract}")
    assert "\\end{abstract}" in result
    body = result.split("\\begin{abstract}")[1].split("\\end{abstract}")[0]
    assert "# Abstract" not in body


@patch("deploy.subprocess.run")
def test_compile_abstract_strips_html_comments(mock_run, tmp_path):
    mock_run.return_value = MagicMock(stdout="Real content.\n", returncode=0)
    abstract = tmp_path / "10_abstract.md"
    abstract.write_text("# Abstract\n\n<!-- NOTE: constraint -->\n<!-- TODO: fill -->\n\nReal content.\n")
    result = deploy._compile_abstract(abstract)
    assert "NOTE" not in result
    assert "TODO" not in result


def test_compile_abstract_empty_body_no_pandoc_call(tmp_path):
    abstract = tmp_path / "10_abstract.md"
    abstract.write_text("# Abstract\n\n<!-- TODO: Write abstract -->\n")
    result = deploy._compile_abstract(abstract)
    assert "\\begin{abstract}" in result
    assert "\\end{abstract}" in result


def test_write_harness_inputs_all_stems(tmp_path):
    stems = ["10_abstract", "11_introduction", "20_related_work"]
    out = deploy._write_harness_inputs(tmp_path, stems)
    content = out.read_text()
    assert "\\input{sections/10_abstract}" in content
    assert "\\input{sections/11_introduction}" in content
    assert "\\input{sections/20_related_work}" in content
    assert "Auto-generated" in content
    assert out.name == "harness-inputs.tex"


@patch("deploy.subprocess.run")
def test_run_no_overleaf_repo_returns_empty(mock_run, paper_root):
    mock_run.return_value = MagicMock(stdout="pandoc 3.0\n", returncode=0)
    result = deploy.run(paper_root)
    assert result == {}


@patch("deploy.subprocess.run")
def test_run_overleaf_compiles_section_and_creates_tex(mock_run, paper_root, tmp_path):
    overleaf = tmp_path / "overleaf_repo"
    overleaf.mkdir()
    (paper_root / "paper.yaml").write_text(
        f"title: T\ntarget: overleaf\ncitation_package: natbib\noverleaf_repo: {overleaf}\n"
    )
    make_section(paper_root, "11_introduction")
    (paper_root / "research" / "candidates.bib").write_text(
        "@article{a,title={T},author={X},year={2024}}\n"
    )
    mock_run.return_value = MagicMock(stdout="\\section{Introduction}\n", returncode=0)
    result = deploy.run(paper_root)
    assert result["compiled"] >= 1
    assert result["target"] == "overleaf"
    assert (overleaf / "sections" / "11_introduction.tex").exists()


@patch("deploy.subprocess.run")
def test_run_copies_references_bib(mock_run, paper_root, tmp_path):
    overleaf = tmp_path / "overleaf"
    overleaf.mkdir()
    (paper_root / "paper.yaml").write_text(
        f"title: T\ntarget: overleaf\ncitation_package: natbib\noverleaf_repo: {overleaf}\n"
    )
    make_section(paper_root, "11_introduction")
    bib = paper_root / "research" / "candidates.bib"
    bib.write_text("@article{a,title={T},year={2024}}\n")
    mock_run.return_value = MagicMock(stdout="\\section{Introduction}\n", returncode=0)
    deploy.run(paper_root)
    assert (overleaf / "references.bib").read_text() == bib.read_text()


@patch("deploy.subprocess.run")
def test_run_word_target_calls_pandoc_with_docx(mock_run, paper_root):
    (paper_root / "paper.yaml").write_text(
        "title: T\ntarget: word\ncitation_package: natbib\ncsl: apa.csl\n"
    )
    make_section(paper_root, "11_introduction")
    (paper_root / "research" / "candidates.bib").write_text("")
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    result = deploy.run(paper_root)
    assert result["target"] == "word"
    # Check that pandoc was called with --to docx in some call
    all_calls = [str(c) for c in mock_run.call_args_list]
    assert any("--to" in c and "docx" in c for c in all_calls)


@patch("deploy.subprocess.run")
def test_run_skips_section_on_conflict(mock_run, paper_root, tmp_path):
    from lib.sync_state import update_section_state, file_hash as fhash
    overleaf = tmp_path / "overleaf_conflict"
    overleaf.mkdir()
    (overleaf / "sections").mkdir()
    (paper_root / "paper.yaml").write_text(
        f"title: T\ntarget: overleaf\ncitation_package: natbib\noverleaf_repo: {overleaf}\n"
    )
    make_section(paper_root, "11_introduction")
    md_path = paper_root / "article" / "sections" / "11_introduction.md"
    tex_path = overleaf / "sections" / "11_introduction.tex"
    tex_path.write_text("old tex content")
    state_path = paper_root / "article" / "sync-state.json"
    # Record a sync state so both sides appear changed since last sync
    update_section_state("11_introduction", "old_md_hash", fhash(tex_path), state_path)
    # md already has different content from old_md_hash, tex will also change
    tex_path.write_text("changed tex content")

    mock_run.return_value = MagicMock(stdout="pandoc 3.0\n", returncode=0)
    result = deploy.run(paper_root)

    assert "11_introduction" in result["conflicts"]
    assert result["compiled"] == 0
