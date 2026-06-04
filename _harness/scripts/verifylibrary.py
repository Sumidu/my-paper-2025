from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from lib import crossref

_HARNESS_ROOT = Path(__file__).parent.parent.parent
_TITLE_MATCH_THRESHOLD = 0.60   # min Jaccard similarity to call it a title match
_YEAR_TOLERANCE = 1             # years difference still considered auto-fixable


# ---------------------------------------------------------------------------
# BibTeX parser
# ---------------------------------------------------------------------------

def _extract_field(body: str, field: str) -> Optional[str]:
    """Extract a single BibTeX field value from an entry body."""
    pattern = re.compile(
        rf'\b{field}\s*=\s*(?:\{{((?:[^{{}}]|\{{[^{{}}]*\}})*)\}}|"([^"]*)"|([\w\d]+))',
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(body)
    if not m:
        return None
    return (m.group(1) or m.group(2) or m.group(3) or "").strip()


def parse_bib(bib_text: str) -> list[dict]:
    """Parse a BibTeX file into a list of entry dicts."""
    entries = []
    for m in re.finditer(r"@(\w+)\{([^,]+),([^@]*)\}", bib_text, re.DOTALL):
        entry_type = m.group(1).lower()
        bibkey = m.group(2).strip()
        body = m.group(3)
        entries.append({
            "bibkey": bibkey,
            "type": entry_type,
            "title": (_extract_field(body, "title") or "").replace("\\{", "{").replace("\\}", "}"),
            "year": _extract_field(body, "year") or "",
            "doi": _extract_field(body, "doi") or "",
            "authors": _extract_field(body, "author") or "",
            "_body": body,
        })
    return entries


# ---------------------------------------------------------------------------
# Verification logic
# ---------------------------------------------------------------------------

def _verify_entry(entry: dict) -> dict:
    """Check a single BibTeX entry against CrossRef. Returns a result dict."""
    bibkey = entry["bibkey"]
    title = entry["title"]
    doi = entry["doi"].strip()
    bib_year = int(entry["year"]) if entry["year"].isdigit() else 0

    if doi:
        print(f"  [{bibkey}] checking DOI {doi} …", end="\r", flush=True)
        cr = crossref.lookup_doi(doi)
        time.sleep(crossref._COURTESY_DELAY)

        if cr is None:
            return {"bibkey": bibkey, "status": "doi_not_found", "doi": doi, "title": title}

        sim = crossref.title_similarity(title, cr["title"])
        cr_year = cr["year"]

        if sim < _TITLE_MATCH_THRESHOLD:
            return {
                "bibkey": bibkey,
                "status": "title_mismatch",
                "doi": doi,
                "bib_title": title,
                "crossref_title": cr["title"],
                "similarity": round(sim, 2),
                "crossref_year": cr_year,
                "crossref_doi": cr["doi"],
            }

        year_diff = abs(bib_year - cr_year) if bib_year and cr_year else 0
        if year_diff > 0:
            fix_type = "year_mismatch_minor" if year_diff <= _YEAR_TOLERANCE else "year_mismatch_major"
            return {
                "bibkey": bibkey,
                "status": fix_type,
                "doi": doi,
                "bib_year": bib_year,
                "crossref_year": cr_year,
                "title": title,
            }

        return {"bibkey": bibkey, "status": "verified", "doi": doi, "title": title}

    else:
        # No DOI — search by title
        print(f"  [{bibkey}] no DOI, searching by title …", end="\r", flush=True)
        candidates = crossref.search_title(title, rows=3)
        time.sleep(crossref._COURTESY_DELAY)

        if not candidates:
            return {"bibkey": bibkey, "status": "not_found", "title": title}

        best = max(candidates, key=lambda c: crossref.title_similarity(title, c["title"]))
        sim = crossref.title_similarity(title, best["title"])

        if sim >= _TITLE_MATCH_THRESHOLD:
            return {
                "bibkey": bibkey,
                "status": "missing_doi",
                "title": title,
                "crossref_doi": best["doi"],
                "crossref_year": best["year"],
                "crossref_title": best["title"],
                "similarity": round(sim, 2),
            }

        return {
            "bibkey": bibkey,
            "status": "not_found",
            "title": title,
            "best_candidate": best["title"],
            "best_similarity": round(sim, 2),
        }


# ---------------------------------------------------------------------------
# Bib file patch helpers
# ---------------------------------------------------------------------------

def _entry_pattern(bibkey: str) -> re.Pattern:
    return re.compile(r'(@\w+\{' + re.escape(bibkey) + r',[^@]*)(\})', re.DOTALL)


def patch_doi(bib_text: str, bibkey: str, doi: str) -> str:
    """Add or replace the doi field for a given bibkey in bib_text."""
    doi_value = "{" + doi + "}"

    def replacer(m):
        body = m.group(1)
        if re.search(r'\bdoi\s*=', body, re.IGNORECASE):
            body = re.sub(r'\bdoi\s*=\s*(?:\{[^}]*\}|"[^"]*"|\w+)', f'doi = {doi_value}', body, flags=re.IGNORECASE)
        else:
            body = body.rstrip().rstrip(",") + f",\n  doi = {doi_value},"
        return body + m.group(2)

    return _entry_pattern(bibkey).sub(replacer, bib_text)


def patch_year(bib_text: str, bibkey: str, year: int) -> str:
    """Replace the year field for a given bibkey in bib_text."""
    year_value = "{" + str(year) + "}"
    def replacer(m):
        body = re.sub(r'\byear\s*=\s*(?:\{[^}]*\}|"[^"]*"|\w+)', f'year = {year_value}', m.group(1), flags=re.IGNORECASE)
        return body + m.group(2)
    return _entry_pattern(bibkey).sub(replacer, bib_text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(root: Path = _HARNESS_ROOT) -> dict:
    bib_path = root / "research" / "candidates.bib"
    if not bib_path.exists():
        print("No research/candidates.bib found. Run /paper:research first.")
        return {}

    bib_text = bib_path.read_text()
    entries = parse_bib(bib_text)
    if not entries:
        print("No BibTeX entries found in candidates.bib.")
        return {}

    print(f"Verifying {len(entries)} entries against CrossRef …\n")

    results: dict[str, list] = {
        "verified": [],
        "missing_doi": [],
        "year_mismatch_minor": [],
        "year_mismatch_major": [],
        "title_mismatch": [],
        "doi_not_found": [],
        "not_found": [],
    }

    for entry in entries:
        result = _verify_entry(entry)
        status = result["status"]
        results.setdefault(status, []).append(result)

    # Write report
    report_path = root / "research" / "verify-report.json"
    report_path.write_text(json.dumps(results, indent=2))

    total = len(entries)
    n_ok = len(results["verified"])
    n_issues = total - n_ok
    print(f"\nVerification complete: {n_ok}/{total} entries verified, {n_issues} issues found.")
    print(f"Report written to research/verify-report.json")

    return results


if __name__ == "__main__":
    results = run()
    if not results:
        sys.exit(1)
    # Pretty summary for CLI use
    for status, items in results.items():
        if items:
            print(f"\n{status.upper().replace('_', ' ')} ({len(items)}):")
            for r in items:
                print(f"  {r['bibkey']}: {r.get('title', '')[:60]}")
