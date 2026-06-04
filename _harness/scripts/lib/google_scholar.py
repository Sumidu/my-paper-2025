from __future__ import annotations

import time

_FALLBACK_DELAY = 60  # seconds between requests when not using Tor
_TOR_DELAY = 5        # courtesy delay between requests over Tor

try:
    from scholarly import scholarly as _scholarly, ProxyGenerator as _ProxyGenerator
    _SCHOLARLY_AVAILABLE = True
except ImportError:
    _scholarly = None  # type: ignore[assignment]
    _ProxyGenerator = None  # type: ignore[assignment]
    _SCHOLARLY_AVAILABLE = False


def _try_enable_tor() -> bool:
    """Attempt to configure scholarly to use Tor. Returns True on success."""
    if not _SCHOLARLY_AVAILABLE:
        return False
    try:
        pg = _ProxyGenerator()
        if pg.Tor_Internal(tor_cmd="tor"):
            _scholarly.use_proxy(pg)
            return True
    except Exception:
        pass
    return False


def _normalize(pub: dict) -> dict:
    bib = pub.get("bib") or {}
    authors_raw = bib.get("author", "")
    if isinstance(authors_raw, list):
        authors = authors_raw
    else:
        authors = [a.strip() for a in authors_raw.split(" and ") if a.strip()]

    try:
        year = int(bib.get("pub_year") or 0)
    except (ValueError, TypeError):
        year = 0

    return {
        "title": bib.get("title") or "",
        "authors": authors,
        "year": year,
        "doi": pub.get("doi") or None,
        "venue": bib.get("venue") or bib.get("journal") or None,
        "abstract": bib.get("abstract") or "",
        "citation_count": pub.get("num_citations") or 0,
        "source": "google_scholar",
        "bibkey": "",
        "topics": [],
    }


def search(query: str, limit: int = 20) -> list[dict]:
    """Search Google Scholar. Returns normalized paper dicts, or [] on hard failure."""
    if not _SCHOLARLY_AVAILABLE:
        print("scholarly not installed — skipping Google Scholar. Run: pip install scholarly")
        return []

    using_tor = _try_enable_tor()

    if using_tor:
        delay = _TOR_DELAY
        print("Google Scholar: using Tor proxy")
    else:
        print(
            f"Google Scholar: Tor not available — falling back to direct requests "
            f"with {_FALLBACK_DELAY}s delay between requests (safe but slow).\n"
            f"Install Tor for faster searches: brew install tor"
        )
        delay = _FALLBACK_DELAY

    results: list[dict] = []
    try:
        search_gen = _scholarly.search_pubs(query)
        for _ in range(limit):
            try:
                pub = next(search_gen)
            except StopIteration:
                break

            try:
                pub = _scholarly.fill(pub)
            except Exception:
                pass  # accept partial data rather than failing

            results.append(_normalize(pub))
            print(f"  Google Scholar: fetched {len(results)}/{limit}", end="\r", flush=True)

            if len(results) < limit:
                time.sleep(delay)

    except Exception as exc:
        msg = str(exc).lower()
        if "captcha" in msg or "maxtries" in msg or "blocked" in msg:
            print(
                f"\nGoogle Scholar: CAPTCHA or IP block detected after {len(results)} results. "
                f"Returning what was collected. Try again later or install Tor."
            )
        else:
            print(f"\nGoogle Scholar: stopped early — {exc}. Returning {len(results)} results.")

    if results:
        print(f"\nGoogle Scholar: {len(results)} results")
    return results
