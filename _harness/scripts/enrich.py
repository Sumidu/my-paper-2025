from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.config import load_config

_HARNESS_ROOT = Path(__file__).parent.parent.parent


def _call_claude(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _is_enriched(topic_path: Path) -> bool:
    return "## Definition" in topic_path.read_text()


def _collect_abstracts(wiki_dir: Path, topic_path: Path) -> list[str]:
    content = topic_path.read_text()
    bibkeys = re.findall(r"\[\[([^\]]+)\]\]", content)
    abstracts = []
    for key in bibkeys:
        paper_path = wiki_dir / "papers" / f"{key}.md"
        if paper_path.exists():
            text = paper_path.read_text()
            m = re.search(r"^# .+\n\n(.+?)\n\n##", text, re.DOTALL | re.MULTILINE)
            if m:
                abstracts.append(m.group(1).strip())
    return abstracts


def _enrich_topic(topic_path: Path, wiki_dir: Path) -> None:
    abstracts = _collect_abstracts(wiki_dir, topic_path)
    topic_name = topic_path.stem.replace("-", " ").title()
    abstracts_block = "\n\n".join(abstracts) or "No abstracts available."
    prompt = (
        f"Topic: {topic_name}\n\n"
        f"Abstracts of papers on this topic:\n{abstracts_block}\n\n"
        f"Write a ## Definition section (1-3 sentences defining the topic) "
        f"followed by a ## Synthesis section (1 paragraph on how these papers "
        f"collectively advance the concept). Use plain academic prose."
    )
    synthesis = _call_claude(prompt)
    original = topic_path.read_text()
    topic_path.write_text(synthesis + "\n\n" + original)


def _ngrams(text: str, n: int) -> set[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def _detect_and_create_stubs(wiki_dir: Path, min_papers: int) -> None:
    papers_dir = wiki_dir / "papers"
    topics_dir = wiki_dir / "topics"
    if not papers_dir.exists():
        return
    topics_dir.mkdir(parents=True, exist_ok=True)
    existing_topics = {p.stem for p in topics_dir.glob("*.md")}

    phrase_counts: dict[str, int] = {}
    for paper_path in papers_dir.glob("*.md"):
        text = paper_path.read_text()
        m = re.search(r"^# .+\n\n(.+?)\n\n##", text, re.DOTALL | re.MULTILINE)
        abstract = m.group(1).strip() if m else ""
        seen_in_this_paper: set[str] = set()
        for n in (2, 3):
            for phrase in _ngrams(abstract, n):
                if phrase not in seen_in_this_paper:
                    phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
                    seen_in_this_paper.add(phrase)

    for phrase, count in phrase_counts.items():
        if count < min_papers:
            continue
        slug = re.sub(r"\s+", "-", phrase).strip("-")
        if slug in existing_topics:
            continue
        stub_path = topics_dir / f"{slug}.md"
        if not stub_path.exists():
            stub_path.write_text(f"# {phrase.title()}\n\n## Papers\n")
            existing_topics.add(slug)


def _enrich_paper_crossrefs(wiki_dir: Path) -> None:
    papers_dir = wiki_dir / "papers"
    topics_dir = wiki_dir / "topics"
    if not papers_dir.exists() or not topics_dir.exists():
        return
    existing_topics = {p.stem for p in topics_dir.glob("*.md")}
    for paper_path in papers_dir.glob("*.md"):
        content = paper_path.read_text()
        if "## Related topics" in content:
            continue
        m = re.search(r"^# .+\n\n(.+?)\n\n##", content, re.DOTALL | re.MULTILINE)
        abstract = m.group(1).strip() if m else ""
        linked = [t for t in existing_topics if t.replace("-", " ") in abstract.lower()]
        if not linked:
            continue
        links = "\n".join(f"- [[{t}]]" for t in sorted(linked))
        paper_path.write_text(content.rstrip() + f"\n\n## Related topics\n{links}\n")


def run(root: Path = _HARNESS_ROOT, force: bool = False) -> dict:
    config = load_config(root)
    wiki_dir = root / "research" / "wiki"
    topics_dir = wiki_dir / "topics"

    _detect_and_create_stubs(wiki_dir, config.enrich_min_papers)

    if not topics_dir.exists():
        return {"enriched": 0, "skipped": 0}

    enriched = skipped = 0
    for topic_path in sorted(topics_dir.glob("*.md")):
        if not force and _is_enriched(topic_path):
            skipped += 1
            continue
        _enrich_topic(topic_path, wiki_dir)
        enriched += 1

    _enrich_paper_crossrefs(wiki_dir)
    return {"enriched": enriched, "skipped": skipped}


if __name__ == "__main__":
    force = "--force" in sys.argv
    result = run(force=force)
    print(f"Enriched {result['enriched']} topics, skipped {result['skipped']}.")
