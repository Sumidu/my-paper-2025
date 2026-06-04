# Paperharness

AI-assisted academic writing scaffold for [Claude Code](https://claude.com/claude-code). One clone per paper — record ideas, search literature, write sections, and compile to LaTeX or Word, all from slash commands.

---

## How it works

You clone this repo once for each paper you're writing. Claude Code's slash commands drive the full pipeline:

```
Record ideas → Transcribe → Distill into research wiki → Search literature
     → Generate state-of-the-art summary → Write sections → Deploy to Overleaf or Word
```

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.10+ | [python.org](https://python.org) |
| Pandoc | any recent | `brew install pandoc` |
| pandoc-crossref | any | `brew install pandoc-crossref` |
| Claude Code | latest | [claude.ai/code](https://claude.ai/code) |
| Whisper (optional) | — | installed automatically via pip |
| Tor (optional) | any | `brew install tor` — faster, safer Google Scholar scraping |

**Literature search API keys** — all optional, each source is skipped gracefully if unavailable:

| Source | Key / setup | Notes |
|---|---|---|
| Google Scholar | none — scraped via `scholarly` | Rate-limited without Tor; install Tor for safer scraping |
| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` in `.env` | Free unauthenticated access disabled; [request a key](https://www.semanticscholar.org/product/api) |
| arXiv | none | Public API, no key needed |
| Scopus | manual CSV export | Drop `research/scopus-export.csv` to merge (paid Scopus subscription required) |

---

## Starting a new paper

### 1. Clone the scaffold

```bash
git clone https://github.com/Sumidu/paperharness.git my-paper-2025
cd my-paper-2025
```

The `my-paper-2025` directory becomes your paper's working directory. You can rename it to anything.

### 2. Disconnect from the upstream repo

```bash
git remote remove origin
git init   # optional: start fresh history
```

Or keep the remote if you want to pull future harness improvements:

```bash
git remote rename origin paperharness
git remote add origin https://github.com/YOUR_ORG/my-paper-2025.git
```

### 3. Run setup

```bash
bash _harness/setup.sh
```

This creates `_harness/.venv`, installs Python dependencies, checks for Pandoc, and copies `.env.example` → `.env`.

### 4. Configure your paper

Edit `paper.yaml` at the root:

```yaml
title: "My Paper Title"
target: overleaf        # or: word
overleaf_repo: ../my-paper-overleaf   # path to cloned Overleaf git repo (if target: overleaf)
csl: apa.csl            # citation style (see _harness/templates/csl/)
citation_package: natbib
language: en            # ISO 639-1 code for Whisper transcription
scholar_max_results: 20 # Google Scholar results per run (default: 20)
enrich_min_papers: 2    # min papers a term must appear in to auto-create a wiki stub (default: 2)
```

Optionally edit `.env` to add a Semantic Scholar API key (skipped without one):

```
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

### 5. Open in Claude Code

```bash
claude
```

All `/paper:*` commands are now available.

---

## Commands

| Command | What it does |
|---|---|
| `/paper:kickoff` | Full pipeline in one shot: transcribe → distill → search literature |
| `/paper:transcribe` | Transcribe new MP3s and M4As in `ideas/recordings/` via Whisper |
| `/paper:ideate` | Distill transcripts into `research/wiki/index.md` (research question + keywords) |
| `/paper:research` | Autonomous literature search → `research/candidates.md` + `candidates.bib` + wiki nodes |
| `/paper:enrich` | Enrich wiki topic pages with Definition + Synthesis blocks; auto-create stubs for frequent terms |
| `/paper:verifylibrary` | Verify `candidates.bib` against CrossRef; auto-fix missing DOIs and minor year mismatches |
| `/paper:sota` | Generate state-of-the-art summary from wiki → `sota/summary.md` |
| `/paper:write [section]` | Fill empty areas and `<!-- TODO: -->` markers in a section |
| `/paper:rewrite [section]` | Propose a full rewrite with diff preview — confirm before overwriting |
| `/paper:deploy` | Compile Markdown → LaTeX (Overleaf) or Word, copy bib + figures |
| `/paper:pull` | Pull Overleaf changes back to Markdown, detect conflicts |

---

## Quick-start walkthrough

**1. Record an idea** — drop an MP3 or M4A into `ideas/recordings/` (voice memo, Zoom recording, anything).

**2. Transcribe and distill:**
```
/paper:kickoff
```
This transcribes the recording, extracts your research question and keywords into `research/wiki/index.md`, and searches Google Scholar, arXiv, and Semantic Scholar (if API key set) for relevant papers.

**3. Review candidates** — open `research/candidates.md` and `research/candidates.bib`. Import the bib into Zotero if you use it.

**4. Generate state-of-the-art summary:**
```
/paper:sota
```
Reads the wiki and writes `sota/summary.md` — a literature synthesis grouped by theme with `[@bibkey]` citations.

**5. Write a section:**
```
/paper:write 20_related_work
```
Fills in the section using `sota/summary.md` and linked wiki nodes as context. Preserves all `<!-- NOTE: -->` constraints.

**6. Deploy:**
```
/paper:deploy
```
Compiles all sections to LaTeX in your Overleaf repo (or to `article/output/paper.docx` for Word). Adds `\input{harness-inputs}` instructions.

**7. Edit in Overleaf, then pull back:**
```
/paper:pull
```
Git-pulls the Overleaf repo and converts changed `.tex` files back to Markdown.

---

## File layout

```
my-paper-2025/
├── paper.yaml                   ← paper config (title, target, CSL, language)
├── .env                         ← API keys (not committed)
│
├── ideas/
│   ├── recordings/              ← drop MP3s or M4As here for /paper:transcribe
│   └── transcripts/             ← auto-generated Markdown transcripts
│       └── translated/          ← auto-translated transcripts (non-English papers)
│
├── research/
│   ├── candidates.md            ← ranked literature search results (human-readable)
│   ├── candidates.bib           ← BibTeX for Zotero import
│   ├── scopus-export.csv        ← optional: drop Scopus CSV here to merge
│   ├── scopus-query.txt         ← generated Scopus advanced search query
│   └── wiki/
│       ├── index.md             ← research question, keywords, contribution
│       ├── papers/              ← one .md per paper (bibkey.md)
│       └── topics/              ← one .md per topic cluster
│
├── sota/
│   └── summary.md               ← state-of-the-art synthesis (/paper:sota output)
│
├── article/
│   ├── sections/                ← paper sections (10_abstract.md, 11_introduction.md, …)
│   ├── figures/                 ← figures (copied to Overleaf on /paper:deploy)
│   ├── output/                  ← paper.docx (Word target)
│   └── sync-state.json          ← deploy/pull conflict tracking (auto-managed)
│
└── _harness/                    ← the scaffold (do not edit)
    ├── setup.sh
    ├── scripts/                 ← Python pipeline scripts
    ├── templates/               ← Pandoc defaults, CSL styles
    └── tests/                   ← 81 unit tests
```

---

## Section naming convention

Sections are Markdown files named `<number>_<name>.md` in `article/sections/`. They are compiled in numeric order. The abstract section **must** be named with `abstract` as the name part (e.g. `10_abstract.md`) — it compiles to `\begin{abstract}...\end{abstract}` rather than `\section{Abstract}`.

Default sections:

| File | Content |
|---|---|
| `10_abstract.md` | Abstract (special LaTeX handling) |
| `11_introduction.md` | Introduction |
| `20_related_work.md` | Related Work |
| `30_methodology.md` | Methodology |
| `40_results.md` | Results |
| `50_discussion.md` | Discussion |
| `60_conclusion.md` | Conclusion |

Add, remove, or renumber freely. Set `exclude_sections` in `paper.yaml` to skip draft sections on deploy.

---

## Annotations

Two HTML comment conventions are preserved through all rewrites:

- `<!-- NOTE: ... -->` — constraint annotation, never overwritten by `/paper:write` or `/paper:rewrite`
- `<!-- TODO: ... -->` — writing agenda item, surfaced and filled by `/paper:write`

---

## Literature search

`/paper:research` queries three sources and merges, deduplicates, and ranks the results:

| Source | Access | Rate limiting |
|---|---|---|
| **Google Scholar** | Always attempted — no key needed | Tor (5s/req) if installed; otherwise 60s/req to avoid IP ban |
| **arXiv** | Always attempted — no key needed | Built-in 3s courtesy delay |
| **Semantic Scholar** | Skipped if no API key in `.env` | API key required (free unauthenticated access disabled) |
| **Scopus CSV** | Drop `research/scopus-export.csv` to merge | Manual export from Scopus (paid subscription) |

### Google Scholar and Tor

Google Scholar does not have a public API and blocks scrapers. Paperharness uses the [`scholarly`](https://github.com/scholarly-python-package/scholarly) library with two modes:

- **With Tor** (recommended): each request goes through a different Tor circuit, reducing ban risk. Install with `brew install tor` — it's auto-detected on each run.
- **Without Tor** (fallback): requests are spaced 60 seconds apart. A 20-result run takes ~20 minutes. A CAPTCHA or IP block stops the run early and returns whatever was collected.

To cap how many Scholar results are fetched (default 20), set in `paper.yaml`:

```yaml
scholar_max_results: 10
```

### Semantic Scholar

Free unauthenticated access has been disabled by Semantic Scholar. To enable it:

1. Request an API key at [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api)
2. Add to `.env`: `SEMANTIC_SCHOLAR_API_KEY=your_key_here`

Without a key, Semantic Scholar is silently skipped — the other sources still run.

---

## Wiki enrichment

`/paper:enrich` deepens the research wiki after `/paper:research` has populated it:

- **Topic pages** — adds a `Definition` block (one-sentence gloss) and a `Synthesis` block (what the collected papers say about this topic).
- **Paper pages** — adds a `Related topics` section linking to other wiki nodes that share papers.
- **Auto-stubs** — scans all abstracts and creates stub topic pages for any term that appears in at least `enrich_min_papers` papers (default: 2). Configure in `paper.yaml`:

```yaml
enrich_min_papers: 3   # raise to reduce noise, lower to cast a wider net
```

Run enrichment any time after `/paper:research`. Re-running is safe — existing blocks are updated, not duplicated.

---

## Reference verification

`/paper:verifylibrary` checks every entry in `research/candidates.bib` against the [CrossRef](https://www.crossref.org/) API:

| Issue | Action |
|---|---|
| Missing DOI | Auto-filled if CrossRef finds a match |
| Year off by ±1 | Auto-corrected |
| Title mismatch | Flagged for your review |
| DOI 404 / not found | Flagged for your review |

Run it before deploying to catch stale or incorrect metadata. No API key required.

---

## Overleaf setup

1. Create a project in Overleaf and clone its git repo locally:
   ```bash
   git clone https://git.overleaf.com/YOUR_PROJECT_ID ../my-paper-overleaf
   ```
2. Set `overleaf_repo: ../my-paper-overleaf` in `paper.yaml`.
3. Run `/paper:deploy` — it writes compiled `.tex` files to `sections/`, copies `references.bib` and figures, and creates `harness-inputs.tex`.
4. In your Overleaf `main.tex`, add `\input{harness-inputs}` where you want the sections to appear.
5. Push from the Overleaf repo: `cd ../my-paper-overleaf && git push`

---

## Citation styles

Built-in CSL styles (in `_harness/templates/csl/`):

- `apa.csl` — APA 7th edition
- `ieee.csl` — IEEE
- `nature.csl` — Nature
- `acm-general.csl` — ACM general
- `acm-sigchi.csl` — ACM CHI

Drop a custom `.csl` file into `article/csl/` and reference it by filename in `paper.yaml`.

---

## Running tests

```bash
cd _harness && .venv/bin/pytest tests/ -v
```

125 tests, covering transcription, literature search (Google Scholar, arXiv, Semantic Scholar, Scopus CSV), wiki R/W, BibTeX key generation, section discovery, sync-state, deployment, Overleaf round-trip, wiki enrichment, and CrossRef verification.
