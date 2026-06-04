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
