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
            last = parts[0] if parts else author
        first_author = _normalize(last) or "unknown"

    year_str = str(year)[:4]

    # First non-stop meaningful title word
    title_words = re.sub(r"[^\w\s]", " ", title, flags=re.UNICODE).split()
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
