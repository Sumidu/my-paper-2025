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
