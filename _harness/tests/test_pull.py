from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import pull
from lib.sync_state import update_section_state, file_hash


@pytest.fixture
def paper_root(tmp_path):
    (tmp_path / "paper.yaml").write_text("title: Test Paper\n")
    (tmp_path / "article" / "sections").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def overleaf_repo(tmp_path):
    repo = tmp_path / "overleaf"
    repo.mkdir()
    (repo / "sections").mkdir()
    return repo


@patch("pull.subprocess.run")
def test_pull_converts_tex_to_md(mock_run, paper_root, overleaf_repo):
    (paper_root / "paper.yaml").write_text(
        f"title: T\noverleaf_repo: {overleaf_repo}\n"
    )
    tex = overleaf_repo / "sections" / "11_introduction.tex"
    tex.write_text("\\section{Introduction}\nSome content.\n")

    git_mock = MagicMock(stdout="Already up to date.\n", returncode=0)
    pandoc_mock = MagicMock(stdout="# Introduction\n\nSome content.\n", returncode=0)
    mock_run.side_effect = [git_mock, pandoc_mock]

    result = pull.run(paper_root)

    assert result["pulled"] == 1
    md_path = paper_root / "article" / "sections" / "11_introduction.md"
    assert md_path.exists()
    assert "Introduction" in md_path.read_text()


@patch("pull.subprocess.run")
def test_pull_skips_unchanged_tex(mock_run, paper_root, overleaf_repo):
    (paper_root / "paper.yaml").write_text(
        f"title: T\noverleaf_repo: {overleaf_repo}\n"
    )
    tex = overleaf_repo / "sections" / "11_introduction.tex"
    tex.write_text("\\section{Introduction}\n")
    md = paper_root / "article" / "sections" / "11_introduction.md"
    md.write_text("# Introduction\n")
    state_path = paper_root / "article" / "sync-state.json"
    update_section_state("11_introduction", file_hash(md), file_hash(tex), state_path)

    mock_run.return_value = MagicMock(stdout="Already up to date.\n", returncode=0)

    result = pull.run(paper_root)

    assert result["skipped"] == 1
    assert result["pulled"] == 0
    assert mock_run.call_count == 1  # only git pull, pandoc never called


@patch("pull.subprocess.run")
def test_pull_detects_conflict(mock_run, paper_root, overleaf_repo):
    (paper_root / "paper.yaml").write_text(
        f"title: T\noverleaf_repo: {overleaf_repo}\n"
    )
    tex = overleaf_repo / "sections" / "11_introduction.tex"
    tex.write_text("original tex")
    md = paper_root / "article" / "sections" / "11_introduction.md"
    md.write_text("original md")
    state_path = paper_root / "article" / "sync-state.json"
    update_section_state("11_introduction", file_hash(md), file_hash(tex), state_path)

    # Both sides change after sync
    tex.write_text("changed in overleaf")
    md.write_text("changed in markdown")

    mock_run.return_value = MagicMock(stdout="Already up to date.\n", returncode=0)

    result = pull.run(paper_root)

    assert "11_introduction" in result["conflicts"]
    assert result["pulled"] == 0


@patch("pull.subprocess.run")
def test_pull_no_overleaf_repo_returns_empty(mock_run, paper_root):
    result = pull.run(paper_root)
    assert result == {}
    mock_run.assert_not_called()


@patch("pull.subprocess.run")
def test_pull_git_failure_returns_empty(mock_run, paper_root, overleaf_repo):
    (paper_root / "paper.yaml").write_text(
        f"title: T\noverleaf_repo: {overleaf_repo}\n"
    )
    mock_run.side_effect = subprocess.CalledProcessError(1, "git", stderr="merge conflict")

    result = pull.run(paper_root)

    assert result == {}


@patch("pull.subprocess.run")
def test_pull_pandoc_error_does_not_crash(mock_run, paper_root, overleaf_repo):
    (paper_root / "paper.yaml").write_text(
        f"title: T\noverleaf_repo: {overleaf_repo}\n"
    )
    tex = overleaf_repo / "sections" / "11_introduction.tex"
    tex.write_text("\\section{Introduction}\n")

    git_mock = MagicMock(stdout="Already up to date.\n", returncode=0)
    pandoc_error = subprocess.CalledProcessError(1, "pandoc", stderr="pandoc: error")
    mock_run.side_effect = [git_mock, pandoc_error]

    result = pull.run(paper_root)

    # Section not pulled, function returns valid dict
    assert result["pulled"] == 0
    assert result["conflicts"] == []
    assert isinstance(result["skipped"], int)


@patch("pull.subprocess.run")
def test_pull_no_sections_dir_returns_zeros(mock_run, paper_root, tmp_path):
    overleaf = tmp_path / "overleaf_no_sections"
    overleaf.mkdir()
    # No sections/ subdirectory
    (paper_root / "paper.yaml").write_text(
        f"title: T\noverleaf_repo: {overleaf}\n"
    )
    mock_run.return_value = MagicMock(stdout="Already up to date.\n", returncode=0)

    result = pull.run(paper_root)

    assert result == {"pulled": 0, "conflicts": [], "skipped": 0}
