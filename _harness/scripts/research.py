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
from lib import semantic_scholar, arxiv_client, google_scholar

_HARNESS_ROOT = Path(__file__).parent.parent.parent


def _load_env(root: Path) -> None:
    """Load .env key=value pairs into os.environ (no extra deps needed)."""
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
    """Remove duplicates: prefer first occurrence."""
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


def _format_scopus_author(author: str) -> str:
    """Convert 'Last F.' or 'Last O.A.' → 'Last, F.' / 'Last, O.A.' for BibTeX."""
    m = re.match(r"^(.+?)\s+([A-Z](?:\.[A-Z])*\.)$", author)
    return f"{m.group(1)}, {m.group(2)}" if m else author


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
            authors = [_format_scopus_author(a.strip()) for a in authors_raw.split(";") if a.strip()]
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


def _first_sentences(text: str, n: int = 2) -> str:
    """Return the first n sentences of text, preserving trailing punctuation."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:n])


def _write_candidates_md(path: Path, papers: list[dict]) -> None:
    lines = ["# Research Candidates\n", f"_{len(papers)} papers found._\n\n---\n"]
    for i, p in enumerate(papers, 1):
        authors_str = ", ".join(p["authors"][:3])
        if len(p["authors"]) > 3:
            authors_str += " et al."
        doi_str = f" DOI: {p['doi']}" if p.get("doi") else ""
        abstract = _first_sentences(p.get("abstract") or "", n=2) or "_No abstract available._"
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

    ss_results = semantic_scholar.search(query, limit=per_source)
    if ss_results:
        print(f"Semantic Scholar: {len(ss_results)} results")

    print(f"Searching arXiv for: {query}")
    ax_results = arxiv_client.search(query, limit=per_source)
    print(f"  → {len(ax_results)} results")

    print(f"Searching Google Scholar for: {query}")
    gs_results = google_scholar.search(query, limit=config.scholar_max_results)

    papers: list[dict] = ss_results + ax_results + gs_results

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
