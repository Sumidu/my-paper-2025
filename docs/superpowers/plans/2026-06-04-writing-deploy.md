# Writing + Deploy Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement section compilation (Markdown → LaTeX/Word), Overleaf round-trip sync, and the `/paper:sota`, `/paper:deploy`, and `/paper:pull` Claude commands.

**Architecture:** Two new Python scripts (`deploy.py`, `pull.py`) wrap Pandoc for compilation and git for sync. Both reuse existing `lib.sections`, `lib.sync_state`, and `lib.config`. The `/paper:sota` command is a pure Claude instruction file — no Python. Commands `/paper:deploy` and `/paper:pull` call their respective scripts and report results.

**Tech Stack:** Python 3.10+, `subprocess` (stdlib), `shutil` (stdlib), Pandoc CLI (external, must be installed), git CLI (external). No new pip dependencies.

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `_harness/scripts/deploy.py` | Discover sections → compile .md → .tex (LaTeX) or .docx (Word), copy bib + figures, write harness-inputs.tex, detect conflicts |
| Create | `_harness/scripts/pull.py` | git pull Overleaf repo → convert changed .tex → .md, detect conflicts, update sync-state |
| Create | `_harness/tests/test_deploy.py` | Unit tests for deploy.py (subprocess mocked) |
| Create | `_harness/tests/test_pull.py` | Unit tests for pull.py (subprocess mocked) |
| Modify | `.claude/commands/paper/sota.md` | Replace stub with full Claude instruction for wiki traversal + sota/summary.md synthesis |
| Modify | `.claude/commands/paper/deploy.md` | Replace stub with command that calls deploy.py + reports results |
| Modify | `.claude/commands/paper/pull.md` | Replace stub with command that calls pull.py + reports results |

**Key invariants** (read before touching any file):

- All scripts use `sys.path.insert(0, str(Path(__file__).parent))` for local imports
- All lib modules start with `from __future__ import annotations`
- `lib.sections.discover_sections(article_dir)` returns `list[tuple[int, str, Path]]` sorted by number prefix
- `lib.sync_state.detect_conflict(name, md_path, tex_path, state_path)` → `bool` — True only when both sides changed since last sync
- `lib.sync_state.update_section_state(name, md_hash, tex_hash, state_path)` — persists hashes
- `lib.sync_state.file_hash(path)` → 12-char SHA-256 string or None
- `lib.config.load_config(root)` returns `PaperConfig` with fields: `title`, `target` ("overleaf"|"word"), `overleaf_repo` (Optional[str]), `citation_package` ("natbib"|"biblatex"), `csl` (filename), `exclude_sections` (list[str])
- Abstract section `10_abstract.md` MUST compile to `\begin{abstract}...\end{abstract}`, not `\section{Abstract}`
- `sync-state.json` lives at `article/sync-state.json`
- Overleaf compiled `.tex` files go in `<overleaf_repo>/sections/`
- `harness-inputs.tex` goes in `<overleaf_repo>/` (root of Overleaf repo)

---

## Task 1: `deploy.py` — Section Compilation

**Files:**
- Create: `_harness/scripts/deploy.py`
- Create: `_harness/tests/test_deploy.py`

- [ ] **Step 1: Write the failing tests**

Create `_harness/tests/test_deploy.py`:

```python
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
    # heading line not in abstract body
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
    # No mock needed — empty body exits before calling pandoc
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
    # _check_pandoc passes, but no overleaf_repo in paper.yaml
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
    calls_str = str(mock_run.call_args_list)
    assert "docx" in calls_str
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /path/to/paper && _harness/.venv/bin/pytest _harness/tests/test_deploy.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'deploy'` (file doesn't exist yet).

- [ ] **Step 3: Implement `deploy.py`**

Create `_harness/scripts/deploy.py`:

```python
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.config import load_config
from lib.sections import discover_sections
from lib.sync_state import detect_conflict, update_section_state, file_hash

_HARNESS_ROOT = Path(__file__).parent.parent.parent


def _check_pandoc() -> bool:
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _compile_abstract(md_path: Path) -> str:
    """Strip # heading + HTML comments, compile body through pandoc, wrap in abstract env."""
    content = md_path.read_text()
    body_lines = [l for l in content.splitlines() if not l.strip().startswith("# ")]
    body = re.sub(r"<!--.*?-->", "", "\n".join(body_lines), flags=re.DOTALL).strip()
    if not body:
        return "\\begin{abstract}\n\\end{abstract}\n"
    result = subprocess.run(
        ["pandoc", "--no-standalone", "--from", "markdown", "--to", "latex"],
        input=body, capture_output=True, text=True, check=True,
    )
    return f"\\begin{{abstract}}\n{result.stdout.strip()}\n\\end{{abstract}}\n"


def _compile_section_to_tex(md_path: Path, citation_package: str) -> str:
    """Compile a section .md to LaTeX using natbib or biblatex citation mode."""
    result = subprocess.run(
        [
            "pandoc", "--no-standalone",
            "--from", "markdown",
            "--to", "latex",
            f"--{citation_package}",
            str(md_path),
        ],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def _write_harness_inputs(dest_dir: Path, section_stems: list[str]) -> Path:
    """Write/update harness-inputs.tex with \\input commands for each stem."""
    out = dest_dir / "harness-inputs.tex"
    lines = ["% Auto-generated by /paper:deploy — do not edit manually\n"]
    for stem in section_stems:
        lines.append(f"\\input{{sections/{stem}}}\n")
    out.write_text("".join(lines))
    return out


def _compile_word(
    sections: list,
    out_path: Path,
    bib_path: Path,
    csl_path: Path,
) -> None:
    """Concatenate all section .md files and compile to .docx via pandoc stdin."""
    combined = "\n\n".join(p.read_text() for _, _, p in sections)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "pandoc", "--standalone",
        "--from", "markdown",
        "--to", "docx",
        "--output", str(out_path),
        "-",
    ]
    if bib_path.exists():
        cmd += ["--citeproc", f"--bibliography={bib_path}", f"--csl={csl_path}"]
    subprocess.run(cmd, input=combined, capture_output=True, text=True, check=True)


def run(root: Path = _HARNESS_ROOT) -> dict:
    """Compile all sections. Returns summary dict or {} on unrecoverable error."""
    if not _check_pandoc():
        print("pandoc not found. Install: https://pandoc.org/installing.html")
        return {}

    config = load_config(root)
    article_dir = root / "article"
    bib_path = root / "research" / "candidates.bib"
    state_path = article_dir / "sync-state.json"

    sections = discover_sections(article_dir, exclude=config.exclude_sections)
    if not sections:
        print("No sections found in article/sections/")
        return {}

    if config.target == "word":
        csl_path = article_dir / "csl" / config.csl
        if not csl_path.exists():
            csl_path = root / "_harness" / "templates" / "csl" / config.csl
        out_path = article_dir / "output" / "paper.docx"
        try:
            _compile_word(sections, out_path, bib_path, csl_path)
            print(f"Word output: {out_path}")
        except subprocess.CalledProcessError as e:
            print(f"pandoc error: {e.stderr[:300]}")
            return {}
        return {
            "compiled": len(sections),
            "conflicts": [],
            "target": "word",
            "output": str(out_path),
        }

    # Overleaf target
    if not config.overleaf_repo:
        print("overleaf_repo not set in paper.yaml. Add the path to your cloned Overleaf repo.")
        return {}

    overleaf = Path(config.overleaf_repo).expanduser().resolve()
    if not overleaf.exists():
        print(f"Overleaf repo not found at: {overleaf}")
        return {}

    tex_dir = overleaf / "sections"
    tex_dir.mkdir(exist_ok=True)

    compiled: list[str] = []
    conflicts: list[str] = []

    for _, stem, md_path in sections:
        tex_path = tex_dir / f"{stem}.tex"

        if detect_conflict(stem, md_path, tex_path, state_path):
            print(f"  CONFLICT {stem}: both .md and .tex changed since last sync — skipping")
            conflicts.append(stem)
            continue

        try:
            if stem == "10_abstract":
                tex_content = _compile_abstract(md_path)
            else:
                tex_content = _compile_section_to_tex(md_path, config.citation_package)
            tex_path.write_text(tex_content)
            update_section_state(stem, file_hash(md_path), file_hash(tex_path), state_path)
            compiled.append(stem)
            print(f"  compiled: {stem}.tex")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR compiling {stem}: {e.stderr[:200]}")

    if bib_path.exists():
        shutil.copy(bib_path, overleaf / "references.bib")
        print(f"  copied: references.bib")

    figures_src = article_dir / "figures"
    if figures_src.exists():
        figures_dst = overleaf / "figures"
        figures_dst.mkdir(exist_ok=True)
        for fig in figures_src.iterdir():
            if fig.is_file() and not fig.name.startswith("."):
                shutil.copy(fig, figures_dst / fig.name)

    # Write harness-inputs.tex for all sections that have a compiled .tex
    stems_with_tex = [
        stem for _, stem, _ in sections
        if (tex_dir / f"{stem}.tex").exists()
    ]
    _write_harness_inputs(overleaf, stems_with_tex)

    return {
        "compiled": len(compiled),
        "conflicts": conflicts,
        "target": "overleaf",
        "overleaf_repo": str(overleaf),
    }


if __name__ == "__main__":
    result = run()
    if not result:
        sys.exit(1)
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
_harness/.venv/bin/pytest _harness/tests/test_deploy.py -v
```

Expected: `8 passed` (all green).

- [ ] **Step 5: Run full test suite for regressions**

```bash
_harness/.venv/bin/pytest _harness/tests/ -v 2>&1 | tail -10
```

Expected: all previous 65 tests still pass.

- [ ] **Step 6: Commit**

```bash
git add _harness/scripts/deploy.py _harness/tests/test_deploy.py
git commit -m "feat: add deploy.py for LaTeX/Word compilation with Pandoc"
```

---

## Task 2: `pull.py` — Overleaf Round-Trip

**Files:**
- Create: `_harness/scripts/pull.py`
- Create: `_harness/tests/test_pull.py`

- [ ] **Step 1: Write the failing tests**

Create `_harness/tests/test_pull.py`:

```python
from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call
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
    # pandoc should NOT have been called for the unchanged file
    assert mock_run.call_count == 1  # only git pull


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

    # Simulate both sides changing after sync
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
_harness/.venv/bin/pytest _harness/tests/test_pull.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'pull'`.

- [ ] **Step 3: Implement `pull.py`**

Create `_harness/scripts/pull.py`:

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.config import load_config
from lib.sync_state import (
    detect_conflict, update_section_state,
    file_hash, get_section_state,
)

_HARNESS_ROOT = Path(__file__).parent.parent.parent


def _git_pull(repo_path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "pull"], cwd=repo_path,
            capture_output=True, text=True, check=True,
        )
        print(result.stdout.strip() or "Already up to date.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"git pull failed: {e.stderr.strip()}")
        return False


def _tex_to_md(tex_path: Path) -> str:
    result = subprocess.run(
        [
            "pandoc", "--from", "latex", "--to", "markdown",
            "--wrap=none", "--atx-headers",
            str(tex_path),
        ],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def _tex_changed_since_sync(stem: str, tex_path: Path, state_path: Path) -> bool:
    """True if tex hash differs from last-synced hash (or was never synced)."""
    prev = get_section_state(stem, state_path)
    if not prev:
        return True
    return file_hash(tex_path) != prev.get("tex_hash")


def run(root: Path = _HARNESS_ROOT) -> dict:
    """Pull Overleaf changes and convert changed .tex → .md. Returns summary or {}."""
    config = load_config(root)
    if not config.overleaf_repo:
        print("overleaf_repo not set in paper.yaml.")
        return {}

    overleaf = Path(config.overleaf_repo).expanduser().resolve()
    if not overleaf.exists():
        print(f"Overleaf repo not found at: {overleaf}")
        return {}

    if not _git_pull(overleaf):
        return {}

    article_dir = root / "article"
    state_path = article_dir / "sync-state.json"
    tex_dir = overleaf / "sections"

    if not tex_dir.exists():
        print("No sections/ directory in Overleaf repo. Nothing to pull.")
        return {"pulled": 0, "conflicts": [], "skipped": 0}

    pulled: list[str] = []
    conflicts: list[str] = []
    skipped: list[str] = []

    for tex_path in sorted(tex_dir.glob("*.tex")):
        stem = tex_path.stem
        md_path = article_dir / "sections" / f"{stem}.md"

        if not _tex_changed_since_sync(stem, tex_path, state_path):
            skipped.append(stem)
            continue

        if detect_conflict(stem, md_path, tex_path, state_path):
            print(
                f"  CONFLICT {stem}: both .md and .tex changed since last sync — "
                "resolve manually, then re-run /paper:pull"
            )
            conflicts.append(stem)
            continue

        try:
            md_content = _tex_to_md(tex_path)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md_content)
            update_section_state(stem, file_hash(md_path), file_hash(tex_path), state_path)
            pulled.append(stem)
            print(f"  pulled: {stem}.md")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR converting {stem}: {e.stderr[:200]}")

    return {"pulled": len(pulled), "conflicts": conflicts, "skipped": len(skipped)}


if __name__ == "__main__":
    result = run()
    if not result:
        sys.exit(1)
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
_harness/.venv/bin/pytest _harness/tests/test_pull.py -v
```

Expected: `5 passed`.

- [ ] **Step 5: Run full test suite for regressions**

```bash
_harness/.venv/bin/pytest _harness/tests/ -v 2>&1 | tail -10
```

Expected: all 73 tests pass (65 previous + 8 deploy + 5 pull).

- [ ] **Step 6: Commit**

```bash
git add _harness/scripts/pull.py _harness/tests/test_pull.py
git commit -m "feat: add pull.py for Overleaf round-trip with conflict detection"
```

---

## Task 3: `/paper:sota` Command

**Files:**
- Modify: `.claude/commands/paper/sota.md`

This is a pure Claude instruction file. No Python script. No automated tests.

- [ ] **Step 1: Write the command file**

Overwrite `.claude/commands/paper/sota.md` with:

```markdown
Generate the state-of-the-art summary.

## Steps

1. Read `research/wiki/index.md`. If it doesn't exist, stop and tell the user to run `/paper:ideate` first.
2. Parse the YAML front matter to get `research_question`, `keywords`, and `contribution`.
3. List all files in `research/wiki/topics/`. If there are none, stop and tell the user to run `/paper:research` first.
4. Read each topic file in `research/wiki/topics/`. Collect all `[[bibkey]]` references.
5. Read each referenced paper node from `research/wiki/papers/<bibkey>.md`.
6. If `sota/summary.md` already exists, read it before writing — preserve the section structure where it makes sense.

## Output

Write `sota/summary.md`. The file MUST start with YAML front matter:

```markdown
---
generated: <today's ISO date, e.g. 2026-06-04>
sources: <N> papers, <M> topics
---

# State of the Art: <research_question from index.md>

## Overview

<2–3 paragraph synthesis of the field: what problem does this literature address,
what are the dominant approaches, and where is the frontier? Do not cite here —
this is orientation prose. Draw from the abstracts and the research question.>

## <Theme Name>

<Narrative paragraph(s) covering papers that cluster around this theme.
Use inline [@bibkey] citations after claims you draw from a specific paper.
Draw on paper abstracts. Aim for 150–250 words per theme.>

## <Theme Name>

...

## Research Gaps

<One focused paragraph identifying what the existing literature does NOT address
in relation to the `contribution` field from index.md. This is the space your
paper occupies. Be specific — name the missing methods, datasets, or evaluations.>

## References

<One bullet per cited paper: `- [@bibkey] Author et al. (year) — Title.`>
```

## Guidelines

- Identify 3–5 themes by clustering papers that share methods, datasets, or research questions. Merge similar topics if fewer emerge naturally.
- A paper can appear under multiple themes.
- Every paper referenced in a topic node should be cited at least once in the body.
- Do NOT use section headings that match the keyword slugs directly (e.g., "Deep Learning"). Choose descriptive theme names like "Attention-Based Models for Sequential Data".
- Keep `sota/summary.md` as a flat Pandoc-compatible Markdown file (no Obsidian directives, no `[[links]]` in the body — only `[@bibkey]` citations).
- After writing, report: how many papers were cited, how many themes, and the output path.
```

- [ ] **Step 2: Verify the command is well-formed**

```bash
cat .claude/commands/paper/sota.md
```

Visually confirm: file has the Steps section, Output template with YAML front matter, Guidelines section, and no leftover "Plan 3 stub" text.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/paper/sota.md
git commit -m "feat: implement /paper:sota command for wiki traversal and sota synthesis"
```

---

## Task 4: `/paper:deploy` Command

**Files:**
- Modify: `.claude/commands/paper/deploy.md`

- [ ] **Step 1: Write the command file**

Overwrite `.claude/commands/paper/deploy.md` with:

```markdown
Compile Markdown sections and sync to Overleaf (or produce Word output).

```bash
cd "$(git rev-parse --show-toplevel)" && _harness/.venv/bin/python _harness/scripts/deploy.py
```

After the script finishes:

- If it printed `pandoc not found`, tell the user to install Pandoc from https://pandoc.org/installing.html.
- If it printed `overleaf_repo not set`, tell the user to add `overleaf_repo: ../my-overleaf-repo` to `paper.yaml`, pointing to a locally cloned Overleaf git repo.
- If it printed `Overleaf repo not found`, tell the user the path in `paper.yaml` doesn't exist — they may need to clone the repo first.
- If there were CONFLICT lines, tell the user which sections are in conflict and explain:
  - A conflict means both the `.md` (in this repo) and the `.tex` (in the Overleaf repo) changed since the last deploy.
  - To resolve: decide which version is authoritative and manually copy the content across, then run `/paper:deploy` again.
- If successful (Overleaf target), report:
  - How many sections were compiled to `.tex`
  - That `harness-inputs.tex` was written/updated in the Overleaf repo
  - That `references.bib` was copied from `research/candidates.bib`
  - Suggest: add `\input{harness-inputs}` to the main `.tex` file in Overleaf if not already there
- If successful (Word target), report:
  - The output path (`article/output/paper.docx`)
  - That citations were processed inline using the CSL style from `paper.yaml`
```

- [ ] **Step 2: Verify no leftover stub text**

```bash
grep -n "Plan 3" .claude/commands/paper/deploy.md
```

Expected: no output (grep finds nothing).

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/paper/deploy.md
git commit -m "feat: wire /paper:deploy command to deploy.py pipeline"
```

---

## Task 5: `/paper:pull` Command

**Files:**
- Modify: `.claude/commands/paper/pull.md`

- [ ] **Step 1: Write the command file**

Overwrite `.claude/commands/paper/pull.md` with:

```markdown
Pull Overleaf changes back to Markdown.

```bash
cd "$(git rev-parse --show-toplevel)" && _harness/.venv/bin/python _harness/scripts/pull.py
```

After the script finishes:

- If it printed `overleaf_repo not set`, tell the user to add `overleaf_repo: ../my-overleaf-repo` to `paper.yaml`.
- If it printed `git pull failed`, show the error and ask if they want to resolve the git conflict manually.
- If there were CONFLICT lines, tell the user which sections are in conflict and explain:
  - A conflict means both the Markdown file (this repo) and the LaTeX file (Overleaf) changed since the last sync.
  - To resolve: open the conflicting section `.md` and the corresponding `.tex` side by side. Merge the changes, update the `.md`, then run `/paper:deploy` to push the resolved version back to Overleaf.
- If successful, report:
  - How many sections were updated (pulled and converted from `.tex`)
  - How many sections were unchanged (skipped)
  - Remind the user that round-trip conversion preserves prose and citations well, but complex LaTeX macros and custom environments may need manual review.
- Suggest next steps: review any pulled sections for conversion artifacts, then continue writing with `/paper:write`.
```

- [ ] **Step 2: Verify no leftover stub text**

```bash
grep -n "Plan 3" .claude/commands/paper/pull.md
```

Expected: no output.

- [ ] **Step 3: Run full test suite one final time**

```bash
_harness/.venv/bin/pytest _harness/tests/ -v 2>&1 | tail -15
```

Expected: all 78 tests pass (65 + 8 + 5). This is the final check before the finishing step.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/paper/pull.md
git commit -m "feat: wire /paper:pull command to pull.py Overleaf round-trip"
```
