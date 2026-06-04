# Foundation + Transcription Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A working, clonable paperharness scaffold with environment setup, `paper.yaml` config parsing, section auto-discovery, sync state tracking, all Claude slash command stubs, and a functional `/paper:transcribe` pipeline including multilingual support.

**Architecture:** Python lib modules in `_harness/scripts/lib/` handle all shared concerns (config, sections, sync state). Scripts in `_harness/scripts/` are thin entry points that import from lib. Claude commands in `.claude/commands/paper/` are prompt files that invoke scripts via Bash. Tests live in `_harness/tests/` and run inside the `_harness/.venv/` virtualenv.

**Tech Stack:** Python 3.10+, openai-whisper, PyYAML, pytest, Pandoc (checked by setup.sh), Bash

---

## File Map

| File | Responsibility |
|---|---|
| `paper.yaml` | Per-paper configuration template |
| `.env.example` | API key template |
| `.gitignore` | Ignore venv, output, env, PDFs |
| `_harness/requirements.txt` | Python dependencies |
| `_harness/setup.sh` | Create venv, install deps, check Pandoc |
| `_harness/scripts/lib/__init__.py` | Empty |
| `_harness/scripts/lib/config.py` | Load + validate `paper.yaml`, apply defaults |
| `_harness/scripts/lib/sections.py` | Auto-discover `article/sections/*.md` sorted numerically |
| `_harness/scripts/lib/sync_state.py` | Read/write `_harness/sync-state.json`, hash files, detect conflicts |
| `_harness/scripts/transcribe.py` | Whisper transcription + translation entry point |
| `_harness/tests/__init__.py` | Empty |
| `_harness/tests/test_config.py` | Config loading, defaults, validation |
| `_harness/tests/test_sections.py` | Section discovery, sorting, exclusion |
| `_harness/tests/test_sync_state.py` | State R/W, hash, conflict detection |
| `_harness/tests/test_transcribe.py` | Transcription logic (mocked Whisper) |
| `.claude/commands/paper/transcribe.md` | `/paper:transcribe` prompt |
| `.claude/commands/paper/kickoff.md` | `/paper:kickoff` prompt |
| `.claude/commands/paper/ideate.md` | `/paper:ideate` stub prompt |
| `.claude/commands/paper/research.md` | `/paper:research` stub prompt |
| `.claude/commands/paper/sota.md` | `/paper:sota` stub prompt |
| `.claude/commands/paper/write.md` | `/paper:write` stub prompt |
| `.claude/commands/paper/rewrite.md` | `/paper:rewrite` stub prompt |
| `.claude/commands/paper/deploy.md` | `/paper:deploy` stub prompt |
| `.claude/commands/paper/pull.md` | `/paper:pull` stub prompt |

---

## Task 1: Repository skeleton

**Files:**
- Create: `paper.yaml`
- Create: `.env.example`
- Create: `.gitignore`
- Create all `ideas/`, `research/wiki/`, `article/`, `sota/` subdirectories with `.gitkeep`
- Create: `_harness/templates/csl/` with bundled CSL files
- Create: `_harness/templates/section-stub.md`
- Create: `_harness/templates/pandoc-defaults.yaml`

- [ ] **Step 1: Create `paper.yaml` template**

```yaml
# paper.yaml — copy this to your paper project and fill in the fields

title: "Untitled Paper"

# Compilation target: overleaf or word
target: overleaf

# Path to cloned Overleaf git repo (only needed for overleaf target)
# overleaf_repo: ../my-paper-overleaf

# Citation style — filename from _harness/templates/csl/ or article/csl/
csl: apa.csl

# Citation package for LaTeX: natbib or biblatex
citation_package: natbib

# Whisper transcription language (ISO 639-1, e.g. en, de, nl, es)
language: en

# Whisper model size: tiny | base | small | medium | large-v3 | large-v3-turbo
whisper_model: large-v3-turbo

# Max literature candidates to return across all sources
research_max_results: 200

# Zotero integration (optional)
# zotero:
#   collection: "my-paper-2025"
#   bibtex_export: ~/Zotero/exports/my-paper.bib

# Sections to skip on deploy (draft sections not ready to compile)
exclude_sections: []
#  - 99_scratch
```

- [ ] **Step 2: Create `.env.example`**

```bash
# Copy to .env and fill in your API key
# Get a free Semantic Scholar key at: https://www.semanticscholar.org/product/api
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

- [ ] **Step 3: Create `.gitignore`**

```gitignore
# Python
_harness/.venv/
__pycache__/
*.pyc
.pytest_cache/

# Environment
.env

# Compiled output
article/output/

# PDFs (large binaries)
research/pdfs/

# Sync state (generated)
_harness/sync-state.json

# macOS
.DS_Store
```

- [ ] **Step 4: Create directory stubs**

```bash
mkdir -p ideas/recordings
mkdir -p ideas/transcripts/translated
mkdir -p research/wiki/topics
mkdir -p research/wiki/papers
mkdir -p research/pdfs
mkdir -p article/sections
mkdir -p article/figures
mkdir -p article/output
mkdir -p article/csl
mkdir -p sota
mkdir -p _harness/scripts/lib
mkdir -p _harness/tests
mkdir -p _harness/templates/csl
mkdir -p _harness/prompts
mkdir -p .claude/commands/paper

touch ideas/recordings/.gitkeep
touch ideas/transcripts/.gitkeep
touch ideas/transcripts/translated/.gitkeep
touch research/wiki/topics/.gitkeep
touch research/wiki/papers/.gitkeep
touch research/pdfs/.gitkeep
touch article/figures/.gitkeep
touch article/output/.gitkeep
touch article/csl/.gitkeep
touch sota/.gitkeep
touch _harness/prompts/.gitkeep
```

- [ ] **Step 5: Create default section stubs in `article/sections/`**

Create these files with empty content (just a heading):

`article/sections/10_abstract.md`:
```markdown
# Abstract

<!-- TODO: Write abstract -->
```

`article/sections/11_introduction.md`:
```markdown
# Introduction

<!-- TODO: Write introduction -->
```

`article/sections/20_related_work.md`:
```markdown
# Related Work

<!-- TODO: Write related work -->
```

`article/sections/30_methodology.md`:
```markdown
# Methodology

<!-- TODO: Write methodology -->
```

`article/sections/40_results.md`:
```markdown
# Results

<!-- TODO: Write results -->
```

`article/sections/50_discussion.md`:
```markdown
# Discussion

<!-- TODO: Write discussion -->
```

`article/sections/60_conclusion.md`:
```markdown
# Conclusion

<!-- TODO: Write conclusion -->
```

- [ ] **Step 6: Create `_harness/templates/section-stub.md`**

```markdown
# $SECTION_TITLE

<!-- TODO: Write this section -->
```

- [ ] **Step 7: Create `_harness/templates/pandoc-defaults.yaml`**

```yaml
# Pandoc defaults for section compilation
# Used by /paper:deploy for LaTeX output

standalone: false
citeproc: true
pdf-engine: pdflatex

variables:
  graphics: true

filters:
  - pandoc-crossref
```

- [ ] **Step 8: Download bundled CSL files**

```bash
CSL_DIR="_harness/templates/csl"
BASE="https://raw.githubusercontent.com/citation-style-language/styles/master"

curl -sL "$BASE/apa.csl" -o "$CSL_DIR/apa.csl"
curl -sL "$BASE/acm-sig-proceedings.csl" -o "$CSL_DIR/acm-sigchi.csl"
curl -sL "$BASE/acm-sigchi-proceedings.csl" -o "$CSL_DIR/acm-general.csl"
curl -sL "$BASE/ieee.csl" -o "$CSL_DIR/ieee.csl"
curl -sL "$BASE/nature.csl" -o "$CSL_DIR/nature.csl"
```

- [ ] **Step 9: Commit skeleton**

```bash
git add .
git commit -m "feat: add repository skeleton, paper.yaml template, section stubs"
```

---

## Task 2: Python lib — `config.py`

**Files:**
- Create: `_harness/requirements.txt`
- Create: `_harness/scripts/lib/__init__.py`
- Create: `_harness/scripts/lib/config.py`
- Create: `_harness/tests/__init__.py`
- Test: `_harness/tests/test_config.py`

- [ ] **Step 1: Create `_harness/requirements.txt`**

```
openai-whisper>=20231117
PyYAML>=6.0
requests>=2.31
pytest>=7.4
```

- [ ] **Step 2: Create empty `__init__.py` files**

```bash
touch _harness/scripts/__init__.py
touch _harness/scripts/lib/__init__.py
touch _harness/tests/__init__.py
```

- [ ] **Step 3: Write failing tests for `config.py`**

Create `_harness/tests/test_config.py`:

```python
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
```

- [ ] **Step 4: Run tests — expect failure**

```bash
cd _harness && .venv/bin/pytest tests/test_config.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'lib.config'`

- [ ] **Step 5: Implement `_harness/scripts/lib/config.py`**

```python
from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ZoteroConfig:
    collection: Optional[str] = None
    bibtex_export: Optional[str] = None


@dataclass
class PaperConfig:
    title: str
    target: str = "overleaf"
    overleaf_repo: Optional[str] = None
    csl: str = "apa.csl"
    citation_package: str = "natbib"
    language: str = "en"
    whisper_model: str = "large-v3-turbo"
    research_max_results: int = 200
    exclude_sections: list = field(default_factory=list)
    zotero: ZoteroConfig = field(default_factory=ZoteroConfig)


_DEFAULTS = {
    "target": "overleaf",
    "csl": "apa.csl",
    "citation_package": "natbib",
    "language": "en",
    "whisper_model": "large-v3-turbo",
    "research_max_results": 200,
    "exclude_sections": [],
}


def load_config(root: Path) -> PaperConfig:
    config_path = root / "paper.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"paper.yaml not found at {config_path}")

    data = yaml.safe_load(config_path.read_text()) or {}

    if "title" not in data:
        raise ValueError("paper.yaml must contain a 'title' field")

    zotero_data = data.pop("zotero", {}) or {}
    zotero = ZoteroConfig(**{k: v for k, v in zotero_data.items()
                             if k in ZoteroConfig.__dataclass_fields__})

    for key, default in _DEFAULTS.items():
        data.setdefault(key, default)

    known_fields = set(PaperConfig.__dataclass_fields__) - {"zotero"}
    filtered = {k: v for k, v in data.items() if k in known_fields}

    return PaperConfig(zotero=zotero, **filtered)
```

- [ ] **Step 6: Run tests — expect pass**

```bash
cd _harness && .venv/bin/pytest tests/test_config.py -v
```

Expected: `8 passed`

- [ ] **Step 7: Commit**

```bash
git add _harness/scripts/lib/config.py _harness/tests/test_config.py _harness/requirements.txt _harness/scripts/__init__.py _harness/scripts/lib/__init__.py _harness/tests/__init__.py
git commit -m "feat: add paper.yaml config loader with defaults and validation"
```

---

## Task 3: Python lib — `sections.py`

**Files:**
- Create: `_harness/scripts/lib/sections.py`
- Test: `_harness/tests/test_sections.py`

- [ ] **Step 1: Write failing tests**

Create `_harness/tests/test_sections.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd _harness && .venv/bin/pytest tests/test_sections.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'lib.sections'`

- [ ] **Step 3: Implement `_harness/scripts/lib/sections.py`**

```python
from __future__ import annotations

import re
from pathlib import Path

_PATTERN = re.compile(r'^(\d+)_(.+)\.md$')


def discover_sections(
    article_dir: Path,
    exclude: list[str] | None = None,
) -> list[tuple[int, str, Path]]:
    """Return (number, stem, path) tuples for sections, sorted numerically.

    Scans article_dir/sections/ for files matching [0-9]+_*.md.
    Files whose stem appears in exclude are omitted.
    """
    exclude = set(exclude or [])
    sections_dir = article_dir / "sections"

    if not sections_dir.exists():
        return []

    results = []
    for f in sections_dir.iterdir():
        m = _PATTERN.match(f.name)
        if m and f.stem not in exclude:
            results.append((int(m.group(1)), f.stem, f))

    return sorted(results, key=lambda x: x[0])
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd _harness && .venv/bin/pytest tests/test_sections.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add _harness/scripts/lib/sections.py _harness/tests/test_sections.py
git commit -m "feat: add section auto-discovery sorted by numeric prefix"
```

---

## Task 4: Python lib — `sync_state.py`

**Files:**
- Create: `_harness/scripts/lib/sync_state.py`
- Test: `_harness/tests/test_sync_state.py`

- [ ] **Step 1: Write failing tests**

Create `_harness/tests/test_sync_state.py`:

```python
import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.sync_state import (
    file_hash, load_state, save_state,
    update_section_state, get_section_state, detect_conflict
)


def test_file_hash_returns_string(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello")
    h = file_hash(f)
    assert isinstance(h, str)
    assert len(h) == 12


def test_file_hash_missing_file_returns_none(tmp_path):
    assert file_hash(tmp_path / "missing.md") is None


def test_file_hash_changes_with_content(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello")
    h1 = file_hash(f)
    f.write_text("world")
    h2 = file_hash(f)
    assert h1 != h2


def test_load_state_missing_file_returns_empty(tmp_path):
    state = load_state(tmp_path / "sync-state.json")
    assert state == {"sections": {}}


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "sync-state.json"
    state = {"sections": {"10_abstract": {"md_hash": "abc", "tex_hash": "def"}}}
    save_state(state, path)
    loaded = load_state(path)
    assert loaded["sections"]["10_abstract"]["md_hash"] == "abc"
    assert "last_sync" in loaded


def test_update_section_state(tmp_path):
    path = tmp_path / "sync-state.json"
    update_section_state("20_related_work", "aaa", "bbb", path)
    state = load_state(path)
    assert state["sections"]["20_related_work"]["md_hash"] == "aaa"
    assert state["sections"]["20_related_work"]["tex_hash"] == "bbb"
    assert "synced_at" in state["sections"]["20_related_work"]


def test_detect_conflict_both_changed(tmp_path):
    md = tmp_path / "section.md"
    tex = tmp_path / "section.tex"
    state_path = tmp_path / "sync-state.json"

    md.write_text("original md")
    tex.write_text("original tex")

    # Record initial state
    update_section_state("20_related_work", file_hash(md), file_hash(tex), state_path)

    # Simulate both files changing
    md.write_text("updated md")
    tex.write_text("updated tex")

    assert detect_conflict("20_related_work", md, tex, state_path) is True


def test_detect_conflict_only_md_changed(tmp_path):
    md = tmp_path / "section.md"
    tex = tmp_path / "section.tex"
    state_path = tmp_path / "sync-state.json"

    md.write_text("original md")
    tex.write_text("original tex")
    update_section_state("20_related_work", file_hash(md), file_hash(tex), state_path)

    md.write_text("updated md")
    # tex unchanged

    assert detect_conflict("20_related_work", md, tex, state_path) is False


def test_detect_conflict_never_synced_returns_false(tmp_path):
    md = tmp_path / "section.md"
    tex = tmp_path / "section.tex"
    state_path = tmp_path / "sync-state.json"
    md.write_text("content")
    tex.write_text("content")

    assert detect_conflict("new_section", md, tex, state_path) is False
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd _harness && .venv/bin/pytest tests/test_sync_state.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'lib.sync_state'`

- [ ] **Step 3: Implement `_harness/scripts/lib/sync_state.py`**

```python
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def file_hash(path: Path) -> Optional[str]:
    """SHA-256 of file contents, truncated to 12 chars. None if file missing."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"sections": {}}
    return json.loads(path.read_text())


def save_state(state: dict, path: Path) -> None:
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(state, indent=2))


def get_section_state(name: str, path: Path) -> dict:
    return load_state(path).get("sections", {}).get(name, {})


def update_section_state(
    name: str, md_hash: str, tex_hash: str, path: Path
) -> None:
    state = load_state(path)
    state.setdefault("sections", {})[name] = {
        "md_hash": md_hash,
        "tex_hash": tex_hash,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
    save_state(state, path)


def detect_conflict(name: str, md_path: Path, tex_path: Path, path: Path) -> bool:
    """True only when both .md and .tex changed since last sync."""
    prev = get_section_state(name, path)
    if not prev:
        return False
    md_changed = file_hash(md_path) != prev.get("md_hash")
    tex_changed = file_hash(tex_path) != prev.get("tex_hash")
    return md_changed and tex_changed
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd _harness && .venv/bin/pytest tests/test_sync_state.py -v
```

Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
git add _harness/scripts/lib/sync_state.py _harness/tests/test_sync_state.py
git commit -m "feat: add sync state tracking with conflict detection"
```

---

## Task 5: `setup.sh`

**Files:**
- Create: `_harness/setup.sh`

- [ ] **Step 1: Create `_harness/setup.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$HARNESS_DIR/.venv"
ROOT="$(dirname "$HARNESS_DIR")"

echo "==> Setting up paperharness environment"

# Python 3.10+
PYTHON=$(command -v python3 || true)
if [ -z "$PYTHON" ]; then
  echo "ERROR: python3 not found. Install Python 3.10+ from https://python.org"
  exit 1
fi

PY_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
  echo "ERROR: Python 3.10+ required (found $PY_VERSION)"
  exit 1
fi

# Virtual environment
if [ ! -d "$VENV" ]; then
  echo "==> Creating virtualenv at _harness/.venv"
  "$PYTHON" -m venv "$VENV"
fi

echo "==> Installing Python dependencies"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$HARNESS_DIR/requirements.txt"

# Pandoc
if ! command -v pandoc &>/dev/null; then
  echo "WARNING: pandoc not found. Install with: brew install pandoc"
else
  echo "    pandoc $(pandoc --version | head -1 | awk '{print $2}') OK"
fi

# pandoc-crossref
if ! command -v pandoc-crossref &>/dev/null; then
  echo "WARNING: pandoc-crossref not found. Install with: brew install pandoc-crossref"
else
  echo "    pandoc-crossref OK"
fi

# .env file
if [ ! -f "$ROOT/.env" ]; then
  if [ -f "$ROOT/.env.example" ]; then
    cp "$ROOT/.env.example" "$ROOT/.env"
    echo "==> Created .env from .env.example"
    echo "    Edit .env and add your Semantic Scholar API key"
    echo "    (Get one free at https://www.semanticscholar.org/product/api)"
  fi
fi

echo ""
echo "Setup complete. To verify:"
echo "  cd _harness && .venv/bin/pytest tests/ -v"
```

- [ ] **Step 2: Make executable and run**

```bash
chmod +x _harness/setup.sh
bash _harness/setup.sh
```

Expected output ends with: `Setup complete. To verify:`

- [ ] **Step 3: Run full test suite to verify environment**

```bash
cd _harness && .venv/bin/pytest tests/ -v
```

Expected: all existing tests pass (17+ passed)

- [ ] **Step 4: Commit**

```bash
git add _harness/setup.sh
git commit -m "feat: add setup.sh — creates venv, installs deps, checks Pandoc"
```

---

## Task 6: Claude slash commands

**Files:**
- Create: `.claude/commands/paper/kickoff.md`
- Create: `.claude/commands/paper/transcribe.md`
- Create: `.claude/commands/paper/ideate.md`
- Create: `.claude/commands/paper/research.md`
- Create: `.claude/commands/paper/sota.md`
- Create: `.claude/commands/paper/write.md`
- Create: `.claude/commands/paper/rewrite.md`
- Create: `.claude/commands/paper/deploy.md`
- Create: `.claude/commands/paper/pull.md`

- [ ] **Step 1: Create `.claude/commands/paper/transcribe.md`**

```markdown
Run the transcription pipeline:

```bash
bash _harness/setup.sh 2>/dev/null || true
_harness/.venv/bin/python _harness/scripts/transcribe.py
```

After the script finishes:
- Report which files were transcribed (or that no new recordings were found)
- If any translation files were created, mention them too
- If there were errors, explain them clearly
```

- [ ] **Step 2: Create `.claude/commands/paper/kickoff.md`**

```markdown
Run the full kickoff pipeline. Steps:

1. **Transcribe** — run `/paper:transcribe` first
2. Check if `ideas/recordings/` has any MP3 files. If not, stop here and tell the user to add recordings before proceeding.
3. **Ideate** — if `research/wiki/index.md` already exists, skip this step and tell the user why. Otherwise run `/paper:ideate` in non-interactive mode.
4. **Research** — run `/paper:research`

Report clearly at each step what happened and what was produced.
```

- [ ] **Step 3: Create `.claude/commands/paper/ideate.md`**

```markdown
Generate or update `research/wiki/index.md` from the transcripts in `ideas/transcripts/`.

Arguments: $ARGUMENTS

If $ARGUMENTS contains "noninteractive", run without asking questions — generate a best-effort draft directly from the transcripts.

Otherwise, run interactively:
1. Read all files in `ideas/transcripts/` (and `ideas/transcripts/translated/` if present)
2. Ask the user one question at a time to clarify: research question, intended contribution, target audience, key concepts
3. After each answer, incorporate it into your understanding
4. When you have enough clarity, write `research/wiki/index.md` with:

```yaml
---
research_question: "<the research question>"
keywords:
  - <keyword 1>
  - <keyword 2>
  - <keyword 3>
  - <keyword 4>
  - <keyword 5>
contribution: "<one sentence on the contribution>"
---
```

Followed by:
- `## Summary` — 2–3 paragraph synthesis of the transcripts
- `## Anticipated Topics` — `[[topic]]` wiki links for concepts likely to appear in the literature
- `## Open Questions` — questions the literature search should answer

In non-interactive mode: add this comment at the top of the file:
`<!-- NOTE: Auto-generated draft. Review and refine keywords before running /paper:research again. -->`
```

- [ ] **Step 4: Create `.claude/commands/paper/research.md`**

```markdown
Run the literature research pipeline.

This command is implemented in Plan 2. For now, tell the user:
"The /paper:research command is not yet implemented. It will be available after Plan 2 is complete."
```

- [ ] **Step 5: Create `.claude/commands/paper/sota.md`**

```markdown
Generate the state-of-the-art summary.

This command is implemented in Plan 3. For now, tell the user:
"The /paper:sota command is not yet implemented. It will be available after Plan 3 is complete."
```

- [ ] **Step 6: Create `.claude/commands/paper/write.md`**

```markdown
Write or fill in a paper section.

Arguments: $ARGUMENTS

If $ARGUMENTS specifies a section name (e.g. "20_related_work"):
1. Read `article/sections/$ARGUMENTS.md`
2. Read `sota/summary.md` if it exists
3. Read all files in `ideas/transcripts/` and `ideas/transcripts/translated/` as context
4. Read all linked wiki nodes reachable from any `[[topic]]` references in the section
5. Find all `<!-- TODO: -->` markers in the section
6. Fill in empty areas and TODO markers with new content
7. Preserve all existing prose exactly
8. Treat `<!-- NOTE: -->` annotations as constraints — do not rewrite annotated content

If no section is specified:
- Read all section files in `article/sections/`
- List which sections are empty, which have TODO markers, and which appear complete
- Ask the user which section to work on
```

- [ ] **Step 7: Create `.claude/commands/paper/rewrite.md`**

```markdown
Propose a full rewrite of a paper section.

Arguments: $ARGUMENTS (section name, e.g. "20_related_work")

1. Read `article/sections/$ARGUMENTS.md`
2. Read `sota/summary.md` if it exists
3. Read all files in `ideas/transcripts/` and `ideas/transcripts/translated/`
4. Read linked wiki nodes reachable from `research/wiki/index.md`
5. Draft a complete rewrite of the section incorporating all available context
6. Show the proposed rewrite as a diff against the current content
7. Ask: "Apply this rewrite? (yes / no / edit first)"
8. Only overwrite the file if the user confirms with "yes"
9. Preserve all `<!-- NOTE: -->` annotations in the rewritten version
```

- [ ] **Step 8: Create `.claude/commands/paper/deploy.md`**

```markdown
Compile Markdown sections and sync to Overleaf (or produce Word output).

This command is implemented in Plan 3. For now, tell the user:
"The /paper:deploy command is not yet implemented. It will be available after Plan 3 is complete."
```

- [ ] **Step 9: Create `.claude/commands/paper/pull.md`**

```markdown
Pull Overleaf changes back to Markdown.

This command is implemented in Plan 3. For now, tell the user:
"The /paper:pull command is not yet implemented. It will be available after Plan 3 is complete."
```

- [ ] **Step 10: Create `CLAUDE.md` with project-level instructions**

```markdown
# Paperharness

AI-assisted academic writing scaffold. Each command below is a slash command in Claude Code.

## Commands

| Command | Description |
|---|---|
| `/paper:kickoff` | Transcribe recordings → ideate → research (full pipeline) |
| `/paper:transcribe` | Transcribe new MP3s in `ideas/recordings/` via Whisper |
| `/paper:ideate` | Distill transcripts into `research/wiki/index.md` |
| `/paper:research` | Autonomous literature search, builds wiki + candidates.bib |
| `/paper:sota` | Generate state-of-the-art summary from wiki |
| `/paper:write [section]` | Fill gaps and TODO markers in a section |
| `/paper:rewrite [section]` | Propose full rewrite of a section with diff preview |
| `/paper:deploy` | Compile Markdown → LaTeX/Word and sync to Overleaf repo |
| `/paper:pull` | Pull Overleaf changes back to Markdown |

## Conventions

- `<!-- NOTE: ... -->` — constraint annotation, preserved through all rewrites
- `<!-- TODO: ... -->` — writing agenda item, surfaced by `/paper:write`
- Section files: `article/sections/<number>_<name>.md` (auto-discovered by number)
- Wiki links: `[[topic-name]]` (Obsidian/Foam style, links to `research/wiki/`)
- Citations: `[@bibkey]` (Pandoc/BibTeX style)
- Figures: `![Caption](../figures/name.png){#fig:label}`

## Setup

Run once per paper clone: `bash _harness/setup.sh`
```

- [ ] **Step 11: Commit**

```bash
git add .claude/commands/ CLAUDE.md
git commit -m "feat: add Claude slash command stubs and CLAUDE.md project instructions"
```

---

## Task 7: Transcription script

**Files:**
- Create: `_harness/scripts/transcribe.py`
- Test: `_harness/tests/test_transcribe.py`

- [ ] **Step 1: Write failing tests**

Create `_harness/tests/test_transcribe.py`:

```python
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import transcribe  # top-level import so patch("transcribe.load_whisper_model") works


@pytest.fixture
def paper_root(tmp_path):
    """Minimal paper project root with paper.yaml and recordings dir."""
    (tmp_path / "paper.yaml").write_text("title: Test Paper\n")
    (tmp_path / "ideas" / "recordings").mkdir(parents=True)
    (tmp_path / "ideas" / "transcripts" / "translated").mkdir(parents=True)
    return tmp_path


def make_mp3(root, name="test_recording.mp3"):
    path = root / "ideas" / "recordings" / name
    path.write_bytes(b"fake mp3 content")
    return path


def test_no_recordings_returns_empty(paper_root):
    result = transcribe.run(paper_root)
    assert result == []


def test_new_recording_is_transcribed(paper_root):
    make_mp3(paper_root)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "Hello world"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        result = transcribe.run(paper_root)

    assert len(result) == 1
    assert "transcripts" in result[0]
    assert result[0].endswith(".md")


def test_transcript_file_contains_text(paper_root):
    make_mp3(paper_root)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "My research idea"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        transcribe.run(paper_root)

    transcripts = list((paper_root / "ideas" / "transcripts").glob("*.md"))
    assert len(transcripts) == 1
    assert "My research idea" in transcripts[0].read_text()


def test_already_transcribed_file_skipped(paper_root):
    mp3 = make_mp3(paper_root)
    stem = f"{date.today().isoformat()}_{mp3.stem}"
    (paper_root / "ideas" / "transcripts" / f"{stem}.md").write_text("existing")

    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "should not run"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        result = transcribe.run(paper_root)

    assert result == []
    mock_model.transcribe.assert_not_called()


def test_non_english_produces_translation(paper_root):
    (paper_root / "paper.yaml").write_text("title: Test\nlanguage: de\n")
    make_mp3(paper_root)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "Meine Forschungsidee"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        result = transcribe.run(paper_root)

    assert len(result) == 2
    assert any("translated" in r for r in result)


def test_translation_calls_whisper_with_translate_task(paper_root):
    (paper_root / "paper.yaml").write_text("title: Test\nlanguage: de\n")
    make_mp3(paper_root)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "some text"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        transcribe.run(paper_root)

    tasks = [c.kwargs.get("task") for c in mock_model.transcribe.call_args_list]
    assert "translate" in tasks
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd _harness && .venv/bin/pytest tests/test_transcribe.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'transcribe'`

- [ ] **Step 3: Implement `_harness/scripts/transcribe.py`**

```python
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# Allow running directly or as module
sys.path.insert(0, str(Path(__file__).parent))
from lib.config import load_config

_HARNESS_ROOT = Path(__file__).parent.parent.parent


def load_whisper_model(model_name: str):
    """Thin wrapper — exists so tests can patch it."""
    import whisper
    return whisper.load_model(model_name)


def _find_new_recordings(recordings_dir: Path, transcripts_dir: Path) -> list[Path]:
    today = date.today().isoformat()
    existing = {p.stem for p in transcripts_dir.glob("*.md")}
    new = []
    for mp3 in sorted(recordings_dir.glob("*.mp3")):
        if f"{today}_{mp3.stem}" not in existing:
            new.append(mp3)
    return new


def _transcribe_file(
    model,
    mp3_path: Path,
    output_path: Path,
    language: str,
    task: str = "transcribe",
) -> None:
    result = model.transcribe(str(mp3_path), language=language, task=task)
    text = result["text"].strip()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    label = "Translation" if task == "translate" else "Transcript"
    output_path.write_text(f"# {label}: {mp3_path.name}\n\n{text}\n")


def run(root: Path = _HARNESS_ROOT) -> list[str]:
    """Transcribe new MP3s. Returns list of created file paths."""
    config = load_config(root)
    recordings_dir = root / "ideas" / "recordings"
    transcripts_dir = root / "ideas" / "transcripts"
    translated_dir = transcripts_dir / "translated"

    recordings_dir.mkdir(parents=True, exist_ok=True)
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    new = _find_new_recordings(recordings_dir, transcripts_dir)
    if not new:
        return []

    model = load_whisper_model(config.whisper_model)
    today = date.today().isoformat()
    created = []

    for mp3 in new:
        stem = f"{today}_{mp3.stem}"
        transcript_path = transcripts_dir / f"{stem}.md"
        _transcribe_file(model, mp3, transcript_path, config.language)
        created.append(str(transcript_path))

        if config.language != "en":
            translated_path = translated_dir / f"{stem}.md"
            _transcribe_file(model, mp3, translated_path, config.language, task="translate")
            created.append(str(translated_path))

    return created


if __name__ == "__main__":
    created = run()
    if created:
        print(f"Transcribed {len(created)} file(s):")
        for path in created:
            print(f"  {path}")
    else:
        print("No new recordings found in ideas/recordings/")
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd _harness && .venv/bin/pytest tests/test_transcribe.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Run full suite**

```bash
cd _harness && .venv/bin/pytest tests/ -v
```

Expected: all tests pass (no failures)

- [ ] **Step 6: Commit**

```bash
git add _harness/scripts/transcribe.py _harness/tests/test_transcribe.py
git commit -m "feat: add transcription pipeline with multilingual Whisper support"
```

---

## Task 8: Smoke test the full setup

- [ ] **Step 1: Verify `setup.sh` runs cleanly from scratch**

```bash
rm -rf _harness/.venv
bash _harness/setup.sh
```

Expected: ends with `Setup complete.`

- [ ] **Step 2: Run full test suite inside venv**

```bash
cd _harness && .venv/bin/pytest tests/ -v --tb=short
```

Expected: all tests pass

- [ ] **Step 3: Verify Claude commands are visible**

Open Claude Code in this project and type `/paper:` — you should see all 9 commands listed as autocomplete options.

- [ ] **Step 4: Test `/paper:transcribe` with no recordings**

In Claude Code, run `/paper:transcribe`.

Expected: Claude reports "No new recordings found in ideas/recordings/"

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: complete Plan 1 — foundation and transcription pipeline ready"
```

---

## What's Next

This plan produces a working scaffold with a tested transcription pipeline and all slash command stubs. The subsequent plans build on this foundation:

- **Plan 2: Research Pipeline** — `/paper:research` (Semantic Scholar + arXiv + Scopus CSV), wiki node generation, topic auto-creation, Zotero integration, `/paper:ideate` non-interactive mode, `/paper:kickoff` full sequence
- **Plan 3: Writing + Deploy** — `/paper:sota`, `/paper:write`, `/paper:rewrite`, `/paper:deploy` (Pandoc + Overleaf sync + harness-inputs.tex), `/paper:pull` (conflict resolution)
