# Research Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the autonomous literature search pipeline: Semantic Scholar + arXiv + Scopus CSV → wiki nodes + candidates.md + candidates.bib + scopus-query.txt + optional Zotero push.

**Architecture:** Five new library modules (`bibkey`, `wiki`, `semantic_scholar`, `arxiv_client`) feed a central `research.py` script. All modules follow existing patterns from Plan 1: `from __future__ import annotations`, `sys.path.insert` for imports, isolated temp-dir tests. The `/paper:research` Claude command is updated from a stub to call `research.py`.

**Tech Stack:** Python 3.10+, `requests` (already in requirements.txt), stdlib `xml.etree.ElementTree` for arXiv XML, `yaml` (already present), `csv` for Scopus import. No new dependencies.

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `_harness/scripts/lib/bibkey.py` | Generate `authorYEARkeyword` keys with collision suffix |
| Create | `_harness/scripts/lib/wiki.py` | Read/write paper nodes, topic stubs, index.md front matter |
| Create | `_harness/scripts/lib/semantic_scholar.py` | HTTP client for Semantic Scholar Graph API v1 |
| Create | `_harness/scripts/lib/arxiv_client.py` | HTTP client for arXiv API (Atom XML) |
| Create | `_harness/scripts/research.py` | Main pipeline: search → dedup → rank → write artifacts |
| Create | `_harness/tests/test_bibkey.py` | Unit tests for bibkey generation |
| Create | `_harness/tests/test_wiki.py` | Unit tests for wiki R/W |
| Create | `_harness/tests/test_semantic_scholar.py` | Mocked API tests |
| Create | `_harness/tests/test_arxiv_client.py` | Mocked API tests |
| Create | `_harness/tests/test_research.py` | Integration tests for research.py with mocked clients |
| Modify | `.claude/commands/paper/research.md` | Replace stub with real command that calls research.py |

**Shared paper dict format** (used across all modules — never deviate from this shape):
```python
{
    "title": str,
    "authors": list[str],        # ["Smith J", "Jones A"] — last-name-first or full name
    "year": int,                 # 0 if unknown
    "doi": str | None,
    "venue": str | None,         # journal/conference name
    "abstract": str,             # may be empty string, never None
    "citation_count": int,       # 0 if unknown
    "source": str,               # "semantic_scholar" | "arxiv" | "scopus"
    "bibkey": str,               # assigned by research.py after dedup; empty str until then
    "topics": list[str],         # slugified keywords found in abstract; populated by research.py
}
```

---

## Task 1: `lib/bibkey.py` — BibTeX key generation

**Files:**
- Create: `_harness/scripts/lib/bibkey.py`
- Create: `_harness/tests/test_bibkey.py`

- [ ] **Step 1: Write the failing tests**

```python
# _harness/tests/test_bibkey.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.bibkey import make_bibkey, resolve_collision


def test_basic_key():
    assert make_bibkey(["Smith J"], 2024, "Attention in Hybrid Work") == "smith2024attention"


def test_stop_words_skipped():
    # "The" is a stop word, "Role" is not
    assert make_bibkey(["Jones A"], 2023, "The Role of Notifications") == "jones2023role"


def test_unicode_normalized():
    assert make_bibkey(["Müller K"], 2022, "Über die Arbeit") == "muller2022uber"


def test_comma_separated_author():
    # "Smith, John" → last name is "Smith"
    assert make_bibkey(["Smith, John"], 2021, "Focus States") == "smith2021focus"


def test_no_authors_uses_unknown():
    key = make_bibkey([], 2020, "Some Paper")
    assert key.startswith("unknown2020")


def test_year_truncated_to_four_digits():
    key = make_bibkey(["Brown X"], "2024-01", "Deep Learning")
    assert "2024" in key
    assert "01" not in key


def test_collision_adds_suffix():
    existing = {"smith2024attention"}
    assert resolve_collision("smith2024attention", existing) == "smith2024attentiona"


def test_collision_chains():
    existing = {"smith2024attention", "smith2024attentiona"}
    assert resolve_collision("smith2024attention", existing) == "smith2024attentionb"
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd /path/to/repo && _harness/.venv/bin/pytest _harness/tests/test_bibkey.py -v 2>&1 | head -30
```
Expected: `ModuleNotFoundError: No module named 'lib.bibkey'`

- [ ] **Step 3: Implement `bibkey.py`**

```python
# _harness/scripts/lib/bibkey.py
from __future__ import annotations

import re
import unicodedata

_STOP_WORDS = {
    "a", "an", "the", "of", "in", "on", "for", "to", "and", "or",
    "with", "by", "from", "at", "as", "is", "are", "was", "were",
    "be", "been", "being", "its", "their", "this", "that", "into",
    "via", "through", "across", "using", "toward", "towards",
}


def _normalize(s: str) -> str:
    """NFKD normalize → strip non-ASCII → keep only a-z0-9."""
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def make_bibkey(authors: list[str], year: int | str, title: str) -> str:
    """Generate authorYEARkeyword key. No collision check — use resolve_collision for that."""
    # First author last name
    if not authors:
        first_author = "unknown"
    else:
        author = authors[0]
        if "," in author:
            last = author.split(",")[0]
        else:
            parts = author.split()
            last = parts[-1] if parts else author
        first_author = _normalize(last) or "unknown"

    year_str = str(year)[:4]

    # First non-stop meaningful title word
    title_words = re.sub(r"[^a-zA-Z\s]", " ", title).split()
    keyword = ""
    for word in title_words:
        w = _normalize(word)
        if w and w not in _STOP_WORDS and len(w) > 1:
            keyword = w
            break
    if not keyword and title_words:
        keyword = _normalize(title_words[0])

    return f"{first_author}{year_str}{keyword}"


def resolve_collision(base_key: str, existing_keys: set[str]) -> str:
    """Return base_key if unique, else base_key + 'a', 'b', … until unique."""
    if base_key not in existing_keys:
        return base_key
    for suffix in "abcdefghijklmnopqrstuvwxyz":
        candidate = base_key + suffix
        if candidate not in existing_keys:
            return candidate
    return base_key + "z"
```

- [ ] **Step 4: Run tests and confirm all pass**

```bash
_harness/.venv/bin/pytest _harness/tests/test_bibkey.py -v
```
Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add _harness/scripts/lib/bibkey.py _harness/tests/test_bibkey.py
git commit -m "feat: add BibTeX key generation with collision resolution"
```

---

## Task 2: `lib/wiki.py` — Wiki R/W helpers

**Files:**
- Create: `_harness/scripts/lib/wiki.py`
- Create: `_harness/tests/test_wiki.py`

- [ ] **Step 1: Write the failing tests**

```python
# _harness/tests/test_wiki.py
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
_harness/.venv/bin/pytest _harness/tests/test_wiki.py -v 2>&1 | head -15
```
Expected: `ModuleNotFoundError: No module named 'lib.wiki'`

- [ ] **Step 3: Implement `wiki.py`**

```python
# _harness/scripts/lib/wiki.py
from __future__ import annotations

import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class IndexMeta:
    research_question: str
    keywords: list[str]
    contribution: str = ""


def _extract_front_matter(content: str) -> Optional[dict]:
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1)) or {}
    return None


def read_index_meta(wiki_dir: Path) -> Optional[IndexMeta]:
    """Parse YAML front matter from research/wiki/index.md."""
    index_path = wiki_dir / "index.md"
    if not index_path.exists():
        return None
    content = index_path.read_text()
    fm = _extract_front_matter(content)
    if fm is None:
        return None
    return IndexMeta(
        research_question=fm.get("research_question", ""),
        keywords=fm.get("keywords", []),
        contribution=fm.get("contribution", ""),
    )


def _author_et_al(authors: list[str]) -> str:
    if not authors:
        return "Unknown"
    if len(authors) == 1:
        return authors[0]
    return f"{authors[0]} et al."


def write_paper_node(wiki_dir: Path, paper: dict) -> None:
    """Write research/wiki/papers/<bibkey>.md. Overwrites if exists."""
    papers_dir = wiki_dir / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)

    bibkey = paper["bibkey"]
    front_matter = {
        "bibkey": bibkey,
        "title": paper["title"],
        "authors": paper["authors"],
        "year": paper["year"],
        "doi": paper.get("doi"),
        "venue": paper.get("venue"),
    }
    fm_text = yaml.dump(front_matter, default_flow_style=False, allow_unicode=True).rstrip()
    topics_text = "\n".join(f"- [[{t}]]" for t in paper.get("topics", []))
    summary = paper.get("abstract", "").strip() or "_No abstract available._"
    author_label = _author_et_al(paper["authors"])
    year = paper["year"]

    content = (
        f"---\n{fm_text}\n---\n\n"
        f"# {author_label} ({year})\n\n"
        f"{summary}\n\n"
        f"**Relevance:** _See candidates.md for relevance note._\n\n"
        f"## Topics\n{topics_text}\n"
    )
    (papers_dir / f"{bibkey}.md").write_text(content)


def ensure_topic_stub(wiki_dir: Path, topic: str, bibkey: str) -> None:
    """Create or append-to research/wiki/topics/<topic-slug>.md."""
    topics_dir = wiki_dir / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    path = topics_dir / f"{slug}.md"
    link = f"[[{bibkey}]]"

    if not path.exists():
        heading = topic.title()
        path.write_text(f"# {heading}\n\n## Papers\n- {link}\n")
    else:
        content = path.read_text()
        if link not in content:
            path.write_text(content.rstrip() + f"\n- {link}\n")
```

- [ ] **Step 4: Run tests and confirm all pass**

```bash
_harness/.venv/bin/pytest _harness/tests/test_wiki.py -v
```
Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
git add _harness/scripts/lib/wiki.py _harness/tests/test_wiki.py
git commit -m "feat: add wiki R/W helpers for paper nodes and topic stubs"
```

---

## Task 3: `lib/semantic_scholar.py` — API client

**Files:**
- Create: `_harness/scripts/lib/semantic_scholar.py`
- Create: `_harness/tests/test_semantic_scholar.py`

- [ ] **Step 1: Write the failing tests**

```python
# _harness/tests/test_semantic_scholar.py
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib.semantic_scholar as ss


def _mock_response(data: dict, status: int = 200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


SS_PAPER = {
    "paperId": "abc123",
    "title": "Attention in Hybrid Work",
    "authors": [{"name": "Smith J"}, {"name": "Jones A"}],
    "year": 2024,
    "abstract": "We study attention.",
    "venue": "CHI",
    "citationCount": 42,
    "externalIds": {"DOI": "10.1145/xyz"},
}


def test_search_returns_normalized_papers():
    mock_resp = _mock_response({"data": [SS_PAPER], "total": 1})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        results = ss.search("attention hybrid work", limit=10)

    assert len(results) == 1
    p = results[0]
    assert p["title"] == "Attention in Hybrid Work"
    assert p["authors"] == ["Smith J", "Jones A"]
    assert p["year"] == 2024
    assert p["doi"] == "10.1145/xyz"
    assert p["citation_count"] == 42
    assert p["source"] == "semantic_scholar"
    assert p["bibkey"] == ""
    assert p["topics"] == []


def test_search_empty_results():
    mock_resp = _mock_response({"data": [], "total": 0})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        results = ss.search("nothing matches", limit=10)
    assert results == []


def test_search_graceful_on_missing_api_key(capsys):
    mock_resp = _mock_response({"data": [SS_PAPER], "total": 1})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        with patch.dict("os.environ", {}, clear=True):
            ss.search("test", limit=5)
    captured = capsys.readouterr()
    assert "SEMANTIC_SCHOLAR_API_KEY" in captured.out


def test_search_retries_on_429():
    rate_limited = MagicMock()
    rate_limited.status_code = 429
    rate_limited.raise_for_status = MagicMock()

    ok_resp = _mock_response({"data": [SS_PAPER], "total": 1})

    with patch("lib.semantic_scholar.requests.get", side_effect=[rate_limited, ok_resp]):
        with patch("lib.semantic_scholar.time.sleep"):
            results = ss.search("test", limit=5)
    assert len(results) == 1


def test_search_abstract_defaults_to_empty_string():
    paper_no_abstract = {**SS_PAPER, "abstract": None}
    mock_resp = _mock_response({"data": [paper_no_abstract], "total": 1})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        results = ss.search("test", limit=5)
    assert results[0]["abstract"] == ""


def test_search_missing_doi_is_none():
    paper_no_doi = {**SS_PAPER, "externalIds": {}}
    mock_resp = _mock_response({"data": [paper_no_doi], "total": 1})
    with patch("lib.semantic_scholar.requests.get", return_value=mock_resp):
        results = ss.search("test", limit=5)
    assert results[0]["doi"] is None
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
_harness/.venv/bin/pytest _harness/tests/test_semantic_scholar.py -v 2>&1 | head -15
```
Expected: `ModuleNotFoundError: No module named 'lib.semantic_scholar'`

- [ ] **Step 3: Implement `semantic_scholar.py`**

```python
# _harness/scripts/lib/semantic_scholar.py
from __future__ import annotations

import os
import time
import requests
from typing import Optional

_API_BASE = "https://api.semanticscholar.org/graph/v1"
_SIGNUP_URL = "https://www.semanticscholar.org/product/api"
_FIELDS = "title,authors,year,abstract,externalIds,venue,citationCount"


def _get_api_key() -> Optional[str]:
    return os.environ.get("SEMANTIC_SCHOLAR_API_KEY")


def _request_with_retry(
    url: str, params: dict, headers: dict, max_retries: int = 3
) -> requests.Response:
    for attempt in range(max_retries):
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 429:
            wait = 2 ** attempt
            print(f"Semantic Scholar rate limited. Waiting {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp
    resp.raise_for_status()
    return resp  # unreachable, satisfies type checkers


def _normalize(raw: dict) -> dict:
    """Convert Semantic Scholar API paper dict to shared paper dict format."""
    external = raw.get("externalIds") or {}
    return {
        "title": raw.get("title") or "",
        "authors": [a["name"] for a in (raw.get("authors") or [])],
        "year": raw.get("year") or 0,
        "doi": external.get("DOI"),
        "venue": raw.get("venue") or None,
        "abstract": raw.get("abstract") or "",
        "citation_count": raw.get("citationCount") or 0,
        "source": "semantic_scholar",
        "bibkey": "",
        "topics": [],
    }


def search(query: str, limit: int = 100) -> list[dict]:
    """Search Semantic Scholar. Returns list of normalized paper dicts."""
    api_key = _get_api_key()
    if api_key is None:
        print(
            f"No SEMANTIC_SCHOLAR_API_KEY found in environment. "
            f"Requests will be rate-limited.\n"
            f"Get a free key at: {_SIGNUP_URL}"
        )

    headers = {"x-api-key": api_key} if api_key else {}
    results: list[dict] = []
    offset = 0
    batch = min(limit, 100)

    while len(results) < limit:
        params = {
            "query": query,
            "limit": batch,
            "offset": offset,
            "fields": _FIELDS,
        }
        resp = _request_with_retry(
            f"{_API_BASE}/paper/search", params=params, headers=headers
        )
        data = resp.json()
        papers = data.get("data") or []
        if not papers:
            break
        results.extend(_normalize(p) for p in papers)
        offset += len(papers)
        if offset >= (data.get("total") or 0):
            break

    return results[:limit]
```

- [ ] **Step 4: Run tests and confirm all pass**

```bash
_harness/.venv/bin/pytest _harness/tests/test_semantic_scholar.py -v
```
Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add _harness/scripts/lib/semantic_scholar.py _harness/tests/test_semantic_scholar.py
git commit -m "feat: add Semantic Scholar API client with graceful key degradation"
```

---

## Task 4: `lib/arxiv_client.py` — arXiv API client

**Files:**
- Create: `_harness/scripts/lib/arxiv_client.py`
- Create: `_harness/tests/test_arxiv_client.py`

- [ ] **Step 1: Write the failing tests**

Build a minimal Atom XML response to feed to the parser. The arXiv API returns Atom 1.0 XML.

```python
# _harness/tests/test_arxiv_client.py
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib.arxiv_client as arxiv

_ATOM_NS = "http://www.w3.org/2005/Atom"
_ARXIV_NS = "http://arxiv.org/schemas/atom"

def _make_atom_xml(entries: list[dict]) -> str:
    """Build minimal Atom feed XML from list of entry dicts."""
    items = []
    for e in entries:
        authors = "".join(
            f"<author><name>{a}</name></author>" for a in e.get("authors", [])
        )
        items.append(
            f"<entry>"
            f"<id>http://arxiv.org/abs/{e.get('arxiv_id', '2401.00001')}</id>"
            f"<title>{e.get('title', 'Test Title')}</title>"
            f"{authors}"
            f"<published>{e.get('published', '2024-01-15T00:00:00Z')}</published>"
            f"<summary>{e.get('abstract', 'A summary.')}</summary>"
            f"</entry>"
        )
    return (
        f'<?xml version="1.0"?>'
        f'<feed xmlns="{_ATOM_NS}">'
        + "".join(items)
        + "</feed>"
    )


def _mock_response(xml: str):
    resp = MagicMock()
    resp.text = xml
    resp.raise_for_status = MagicMock()
    return resp


def test_search_parses_title_and_authors():
    xml = _make_atom_xml([{
        "title": "Hybrid Work and Attention",
        "authors": ["Smith J", "Jones A"],
        "published": "2024-03-01T00:00:00Z",
        "abstract": "We study attention.",
    }])
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("attention", limit=5)
    assert len(results) == 1
    p = results[0]
    assert p["title"] == "Hybrid Work and Attention"
    assert p["authors"] == ["Smith J", "Jones A"]
    assert p["year"] == 2024
    assert p["source"] == "arxiv"
    assert p["doi"] is None
    assert p["bibkey"] == ""
    assert p["topics"] == []


def test_search_empty_feed():
    xml = _make_atom_xml([])
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("nothing", limit=5)
    assert results == []


def test_search_respects_limit():
    entries = [{"title": f"Paper {i}", "authors": ["A B"]} for i in range(10)]
    xml = _make_atom_xml(entries)
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("test", limit=5)
    assert len(results) == 5


def test_search_abstract_defaults_empty():
    xml = _make_atom_xml([{"title": "No Abstract", "authors": ["X Y"], "abstract": ""}])
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("test", limit=5)
    assert results[0]["abstract"] == ""


def test_search_citation_count_zero():
    xml = _make_atom_xml([{"title": "T", "authors": ["A"]}])
    with patch("lib.arxiv_client.requests.get", return_value=_mock_response(xml)):
        results = arxiv.search("test", limit=5)
    assert results[0]["citation_count"] == 0
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
_harness/.venv/bin/pytest _harness/tests/test_arxiv_client.py -v 2>&1 | head -15
```
Expected: `ModuleNotFoundError: No module named 'lib.arxiv_client'`

- [ ] **Step 3: Implement `arxiv_client.py`**

```python
# _harness/scripts/lib/arxiv_client.py
from __future__ import annotations

import time
import requests
import xml.etree.ElementTree as ET

_API_BASE = "https://export.arxiv.org/api/query"
_ATOM = "http://www.w3.org/2005/Atom"
_COURTESY_DELAY = 3  # seconds between paginated requests (arXiv policy)


def _parse_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall(f"{{{_ATOM}}}entry"):
        title_el = entry.find(f"{{{_ATOM}}}title")
        title = (title_el.text or "").strip() if title_el is not None else ""

        authors = [
            (name_el.text or "").strip()
            for author_el in entry.findall(f"{{{_ATOM}}}author")
            for name_el in [author_el.find(f"{{{_ATOM}}}name")]
            if name_el is not None
        ]

        published_el = entry.find(f"{{{_ATOM}}}published")
        year = 0
        if published_el is not None and published_el.text:
            try:
                year = int(published_el.text[:4])
            except ValueError:
                year = 0

        summary_el = entry.find(f"{{{_ATOM}}}summary")
        abstract = (summary_el.text or "").strip() if summary_el is not None else ""

        papers.append({
            "title": title,
            "authors": authors,
            "year": year,
            "doi": None,
            "venue": "arXiv",
            "abstract": abstract,
            "citation_count": 0,
            "source": "arxiv",
            "bibkey": "",
            "topics": [],
        })
    return papers


def search(query: str, limit: int = 100) -> list[dict]:
    """Search arXiv. Returns list of normalized paper dicts."""
    results: list[dict] = []
    start = 0
    batch = min(limit, 100)

    while len(results) < limit:
        params = {
            "search_query": f"all:{query}",
            "start": start,
            "max_results": batch,
        }
        resp = requests.get(_API_BASE, params=params)
        resp.raise_for_status()

        entries = _parse_feed(resp.text)
        if not entries:
            break
        results.extend(entries)
        start += len(entries)

        if len(entries) < batch:
            break
        if len(results) < limit:
            time.sleep(_COURTESY_DELAY)

    return results[:limit]
```

- [ ] **Step 4: Run tests and confirm all pass**

```bash
_harness/.venv/bin/pytest _harness/tests/test_arxiv_client.py -v
```
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add _harness/scripts/lib/arxiv_client.py _harness/tests/test_arxiv_client.py
git commit -m "feat: add arXiv API client with Atom XML parsing"
```

---

## Task 5: `research.py` — Main pipeline

**Files:**
- Create: `_harness/scripts/research.py`
- Create: `_harness/tests/test_research.py`

The pipeline reads keywords from `research/wiki/index.md`, searches both APIs, merges Scopus CSV if present, deduplicates, ranks, writes `candidates.md` / `candidates.bib` / `scopus-query.txt`, writes wiki paper nodes and topic stubs, attempts Zotero push.

**Paper dict flow:**
1. API clients return normalized dicts (bibkey="", topics=[])
2. `_deduplicate` removes duplicates by DOI or normalized title
3. `_rank` scores by `citation_count + (keyword_hits * 10)`, sorts descending
4. `_extract_topics` populates `topics` for each paper (keywords found in abstract)
5. `_assign_bibkeys` populates `bibkey` for each paper
6. Output functions write the artifacts

- [ ] **Step 1: Write the failing tests**

```python
# _harness/tests/test_research.py
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


def test_run_creates_candidates_files(paper_root):
    fake_ss = [_fake_paper("Attention Study", doi="10.1145/1", citations=10)]
    fake_arxiv = [_fake_paper("Notification Study", source="arxiv")]

    with patch("research.semantic_scholar.search", return_value=fake_ss), \
         patch("research.arxiv_client.search", return_value=fake_arxiv):
        result = research.run(paper_root)

    assert (paper_root / "research" / "candidates.md").exists()
    assert (paper_root / "research" / "candidates.bib").exists()
    assert (paper_root / "research" / "scopus-query.txt").exists()
    assert result["papers"] == 2


def test_run_creates_wiki_nodes(paper_root):
    fake_ss = [_fake_paper("Attention Study", doi="10.1145/1")]

    with patch("research.semantic_scholar.search", return_value=fake_ss), \
         patch("research.arxiv_client.search", return_value=[]):
        research.run(paper_root)

    papers_dir = paper_root / "research" / "wiki" / "papers"
    assert len(list(papers_dir.glob("*.md"))) == 1


def test_deduplication_by_doi(paper_root):
    p1 = _fake_paper("Paper A", doi="10.1/same", citations=5)
    p2 = _fake_paper("Paper A different title", doi="10.1/same", citations=3)

    with patch("research.semantic_scholar.search", return_value=[p1, p2]), \
         patch("research.arxiv_client.search", return_value=[]):
        result = research.run(paper_root)

    assert result["papers"] == 1


def test_deduplication_by_normalized_title(paper_root):
    p1 = _fake_paper("Attention and Work")
    p2 = _fake_paper("Attention and Work")  # exact duplicate, no DOI

    with patch("research.semantic_scholar.search", return_value=[p1, p2]), \
         patch("research.arxiv_client.search", return_value=[]):
        result = research.run(paper_root)

    assert result["papers"] == 1


def test_scopus_csv_merged(paper_root):
    # Write a minimal Scopus CSV
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
         patch("research.arxiv_client.search", return_value=[]):
        result = research.run(paper_root)

    assert result["papers"] == 1
    bib = (paper_root / "research" / "candidates.bib").read_text()
    assert "brown2023scopus" in bib


def test_no_index_md_returns_empty(paper_root):
    (paper_root / "research" / "wiki" / "index.md").unlink()
    result = research.run(paper_root)
    assert result == {}


def test_scopus_query_contains_keywords(paper_root):
    with patch("research.semantic_scholar.search", return_value=[]), \
         patch("research.arxiv_client.search", return_value=[]):
        research.run(paper_root)

    query = (paper_root / "research" / "scopus-query.txt").read_text()
    assert "attention" in query
    assert "notifications" in query


def test_candidates_bib_valid_bibtex(paper_root):
    fake_ss = [_fake_paper("BibTeX Test", doi="10.1/bib", citations=1)]
    with patch("research.semantic_scholar.search", return_value=fake_ss), \
         patch("research.arxiv_client.search", return_value=[]):
        research.run(paper_root)

    bib = (paper_root / "research" / "candidates.bib").read_text()
    assert "@" in bib
    assert "title" in bib.lower()
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
_harness/.venv/bin/pytest _harness/tests/test_research.py -v 2>&1 | head -20
```
Expected: `ModuleNotFoundError: No module named 'research'`

- [ ] **Step 3: Implement `research.py`**

Implement all helper functions plus `run()`. The full file:

```python
# _harness/scripts/research.py
from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.config import load_config
from lib.wiki import read_index_meta, write_paper_node, ensure_topic_stub
from lib.bibkey import make_bibkey, resolve_collision
from lib import semantic_scholar, arxiv_client

_HARNESS_ROOT = Path(__file__).parent.parent.parent


def _load_env(root: Path) -> None:
    """Load .env key=value pairs into os.environ (simple, no extra deps)."""
    env_path = root / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, remove articles — for fuzzy dedup."""
    title = title.lower()
    title = re.sub(r"\b(the|a|an)\b", " ", title)
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def _deduplicate(papers: list[dict]) -> list[dict]:
    """Remove duplicates: prefer first occurrence (highest citation count if pre-sorted)."""
    seen_doi: set[str] = set()
    seen_title: set[str] = set()
    unique: list[dict] = []
    for p in papers:
        doi = p.get("doi")
        if doi:
            if doi in seen_doi:
                continue
            seen_doi.add(doi)
        norm = _normalize_title(p.get("title", ""))
        if norm and norm in seen_title:
            continue
        if norm:
            seen_title.add(norm)
        unique.append(p)
    return unique


def _rank(papers: list[dict], keywords: list[str]) -> list[dict]:
    """Score = citation_count + (keyword_hits_in_abstract * 10). Sort descending."""
    kw_lower = [k.lower() for k in keywords]

    def score(p: dict) -> int:
        abstract = (p.get("abstract") or "").lower()
        hits = sum(1 for k in kw_lower if k in abstract)
        return p.get("citation_count", 0) + hits * 10

    return sorted(papers, key=score, reverse=True)


def _extract_topics(papers: list[dict], keywords: list[str]) -> None:
    """Populate paper['topics'] in-place based on keyword presence in abstract."""
    for paper in papers:
        abstract = (paper.get("abstract") or "").lower()
        topics = []
        for kw in keywords:
            if kw.lower() in abstract:
                slug = re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")
                topics.append(slug)
        paper["topics"] = topics


def _assign_bibkeys(papers: list[dict]) -> None:
    """Assign paper['bibkey'] in-place, resolving collisions."""
    existing: set[str] = set()
    for paper in papers:
        base = make_bibkey(paper["authors"], paper["year"], paper["title"])
        key = resolve_collision(base, existing)
        existing.add(key)
        paper["bibkey"] = key


def _read_scopus_csv(path: Path) -> list[dict]:
    """Parse a Scopus CSV export into normalized paper dicts."""
    papers = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("Title", "").strip()
            if not title:
                continue
            try:
                year = int(str(row.get("Year", "0"))[:4])
            except ValueError:
                year = 0
            try:
                cited = int(str(row.get("Cited by", "0") or "0"))
            except ValueError:
                cited = 0
            authors_raw = row.get("Authors", "")
            authors = [a.strip() for a in authors_raw.split(";") if a.strip()]
            papers.append({
                "title": title,
                "authors": authors,
                "year": year,
                "doi": row.get("DOI", "").strip() or None,
                "venue": row.get("Source title", "").strip() or None,
                "abstract": row.get("Abstract", "").strip(),
                "citation_count": cited,
                "source": "scopus",
                "bibkey": "",
                "topics": [],
            })
    return papers


def _write_candidates_md(path: Path, papers: list[dict]) -> None:
    lines = ["# Research Candidates\n", f"_{len(papers)} papers found._\n\n---\n"]
    for i, p in enumerate(papers, 1):
        authors_str = ", ".join(p["authors"][:3])
        if len(p["authors"]) > 3:
            authors_str += " et al."
        doi_str = f" DOI: {p['doi']}" if p.get("doi") else ""
        abstract = (p.get("abstract") or "")[:300].rstrip()
        if len(p.get("abstract", "")) > 300:
            abstract += "…"
        topics_str = ", ".join(f"[[{t}]]" for t in p.get("topics", []))
        lines.append(
            f"## {i}. {p['title']}\n\n"
            f"**{authors_str} ({p['year']})** · {p.get('venue') or p['source']}{doi_str}\n\n"
            f"{abstract}\n\n"
            f"**Relevance:** Matches keywords: {topics_str or '_none detected_'}\n\n---\n"
        )
    path.write_text("".join(lines))


def _write_candidates_bib(path: Path, papers: list[dict]) -> None:
    entries = []
    for p in papers:
        bibkey = p["bibkey"]
        title = p["title"].replace("{", "\\{").replace("}", "\\}")
        authors_str = " and ".join(p["authors"])
        entry_type = "article" if p.get("venue") else "misc"
        lines = [
            f"@{entry_type}{{{bibkey},",
            f"  title = {{{title}}},",
            f"  author = {{{authors_str}}},",
            f"  year = {{{p['year']}}},",
        ]
        if p.get("venue"):
            field = "journal" if entry_type == "article" else "howpublished"
            lines.append(f"  {field} = {{{p['venue']}}},")
        if p.get("doi"):
            lines.append(f"  doi = {{{p['doi']}}},")
        abstract = (p.get("abstract") or "")[:500]
        if abstract:
            abstract = abstract.replace("{", "\\{").replace("}", "\\}")
            lines.append(f"  abstract = {{{abstract}}},")
        lines.append("}")
        entries.append("\n".join(lines))
    path.write_text("\n\n".join(entries) + "\n")


def _write_scopus_query(path: Path, keywords: list[str]) -> None:
    kw_parts = " OR ".join(f'"{k}"' for k in keywords)
    query = f"TITLE-ABS-KEY({kw_parts})"
    path.write_text(
        f"# Scopus Search Query\n\n"
        f"Copy this into Scopus Advanced Search:\n\n"
        f"```\n{query}\n```\n\n"
        f"Export results as CSV and save to research/scopus-export.csv\n"
    )


def _try_zotero_push(papers: list[dict], config) -> None:
    """Attempt to push to Zotero local API. Silently skip if not running."""
    try:
        import socket
        s = socket.create_connection(("localhost", 23119), timeout=1)
        s.close()
    except OSError:
        return  # Zotero not running

    if not config.zotero.collection:
        print("Zotero is running. To auto-import, set zotero.collection in paper.yaml.")
        print("Or drag candidates.bib into Zotero manually.")
        return

    print(f"Zotero detected. candidates.bib is ready to import into collection: {config.zotero.collection}")
    print("Drag research/candidates.bib into Zotero, or use File → Import.")


def run(root: Path = _HARNESS_ROOT) -> dict:
    """Run the research pipeline. Returns summary dict or {} on early exit."""
    _load_env(root)
    config = load_config(root)
    wiki_dir = root / "research" / "wiki"
    research_dir = root / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    meta = read_index_meta(wiki_dir)
    if meta is None:
        print("No research/wiki/index.md found. Run /paper:ideate first.")
        return {}
    if not meta.keywords:
        print("No keywords in index.md front matter. Add keywords and retry.")
        return {}

    limit = config.research_max_results
    per_source = max(limit // 2, 10)
    query = " ".join(meta.keywords)

    print(f"Searching Semantic Scholar for: {query}")
    ss_results = semantic_scholar.search(query, limit=per_source)
    print(f"  → {len(ss_results)} results")

    print(f"Searching arXiv for: {query}")
    ax_results = arxiv_client.search(query, limit=per_source)
    print(f"  → {len(ax_results)} results")

    papers: list[dict] = ss_results + ax_results

    scopus_path = research_dir / "scopus-export.csv"
    if scopus_path.exists():
        scopus_papers = _read_scopus_csv(scopus_path)
        print(f"Merged {len(scopus_papers)} Scopus papers from {scopus_path.name}")
        papers.extend(scopus_papers)

    papers = _deduplicate(papers)
    papers = _rank(papers, meta.keywords)[:limit]
    _extract_topics(papers, meta.keywords)
    _assign_bibkeys(papers)

    _write_candidates_md(research_dir / "candidates.md", papers)
    _write_candidates_bib(research_dir / "candidates.bib", papers)
    _write_scopus_query(research_dir / "scopus-query.txt", meta.keywords)

    topic_set: set[str] = set()
    for paper in papers:
        write_paper_node(wiki_dir, paper)
        for topic in paper.get("topics", []):
            ensure_topic_stub(wiki_dir, topic, paper["bibkey"])
            topic_set.add(topic)

    _try_zotero_push(papers, config)

    summary = {
        "papers": len(papers),
        "wiki_nodes": len(papers),
        "topics": len(topic_set),
    }
    print(
        f"\nResearch complete: {summary['papers']} papers, "
        f"{summary['topics']} topics, "
        f"wiki nodes written to research/wiki/papers/"
    )
    return summary


if __name__ == "__main__":
    result = run()
    if not result:
        sys.exit(1)
```

- [ ] **Step 4: Run tests and confirm all pass**

```bash
_harness/.venv/bin/pytest _harness/tests/test_research.py -v
```
Expected: `8 passed`

- [ ] **Step 5: Run the full test suite to catch regressions**

```bash
_harness/.venv/bin/pytest _harness/tests/ -v
```
Expected: all tests pass (previous 29 + new 28 = 57 total)

- [ ] **Step 6: Commit**

```bash
git add _harness/scripts/research.py _harness/tests/test_research.py
git commit -m "feat: add research pipeline with dedup, ranking, wiki nodes, and candidates output"
```

---

## Task 6: Wire up the `/paper:research` command

**Files:**
- Modify: `.claude/commands/paper/research.md`

- [ ] **Step 1: Read the current stub**

Current content of `.claude/commands/paper/research.md`:
```
Run the literature research pipeline.

This command is implemented in Plan 2. For now, tell the user:
"The /paper:research command is not yet implemented. It will be available after Plan 2 is complete."
```

- [ ] **Step 2: Write the real command**

Replace the entire file with:

```markdown
Run the autonomous literature search pipeline.

Steps:
1. Run the research script:
   ```bash
   cd $(git rev-parse --show-toplevel) && _harness/.venv/bin/python _harness/scripts/research.py
   ```
2. Read the script output carefully.
3. If the script exits with an error (e.g. "No index.md found"), tell the user and suggest the fix (e.g. run `/paper:ideate` first).
4. If successful, report:
   - How many papers were found
   - How many topics were discovered
   - That `research/candidates.md` is ready to review
   - That `research/candidates.bib` is ready to import into Zotero
   - If a Scopus CSV was merged, mention how many papers it contributed
5. Suggest next steps: review `research/candidates.md`, then run `/paper:sota` to generate the state-of-the-art summary.
```

- [ ] **Step 3: Run a smoke test — confirm the command works end-to-end with a real index.md**

Create a minimal test index.md in the actual repo (not tmp_path) to verify the script runs:

```bash
# Create a test index.md if research/wiki/index.md doesn't exist
if [ ! -f research/wiki/index.md ]; then
  mkdir -p research/wiki
  cat > research/wiki/index.md << 'EOF'
---
research_question: "Test question for smoke test"
keywords:
  - attention
  - notifications
contribution: "TBD"
---

## Summary
Smoke test.
EOF
fi

# Run with a very small limit to avoid long waits
RESEARCH_MAX_RESULTS=5 _harness/.venv/bin/python _harness/scripts/research.py
```

Expected: script runs, prints progress, creates `research/candidates.md`, `research/candidates.bib`, `research/scopus-query.txt`, and at least one file in `research/wiki/papers/`.

If the test index.md was created for smoke testing only, remove it after:
```bash
# Only remove if you created it above and it wasn't already there
# git restore research/wiki/index.md   # if you want to revert
```

- [ ] **Step 4: Run full test suite one more time**

```bash
_harness/.venv/bin/pytest _harness/tests/ -v
```
Expected: all 57 tests pass.

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/paper/research.md
git commit -m "feat: wire /paper:research command to research.py pipeline"
```

---

## Final State

After Plan 2:
- **57 tests** passing (29 from Plan 1 + 28 new)
- `/paper:research` is fully functional: reads `research/wiki/index.md`, searches Semantic Scholar + arXiv, merges Scopus CSV, writes `candidates.md`, `candidates.bib`, `scopus-query.txt`, wiki paper nodes, and topic stubs
- `/paper:kickoff` works end-to-end: transcribe → ideate (if needed) → research
- Zotero integration: graceful detection, instructions for manual import if not configured
- `.env` auto-loaded by `research.py` (no shell setup needed)

## Ready for Plan 3
Plan 3 will implement:
- `/paper:sota` — link traversal from index.md, dynamic wiki context, generates `sota/summary.md`
- `/paper:write` — fills TODO markers using transcripts + wiki + sota as context
- `/paper:rewrite` — full section rewrite with diff + confirmation
- `/paper:deploy` — Pandoc compile to LaTeX (Overleaf) or Word, harness-inputs.tex, sync-state update
- `/paper:pull` — Overleaf → Markdown round-trip with conflict resolution
