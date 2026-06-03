# Paperharness Design Spec
**Date:** 2026-06-03  
**Status:** Approved

---

## Overview

Paperharness is a reusable template repository for writing scientific academic articles with Claude Code. Each new paper gets its own copy of the harness. The harness handles the full pipeline from raw voice ideas through literature discovery to a compiled LaTeX or Word document.

Primary user: an HCI researcher working across computer science, psychology, sociology, and computational social science, publishing in venues indexed by Scopus, ACM, IEEE, and arXiv. Final document output is managed via Overleaf (LaTeX) or Word depending on the target journal.

---

## Architecture: Option A — Standalone Harness Folder

The harness IS the paper project. Each paper lives in its own folder, created by copying the harness template. No submodules, no globally installed CLI. The harness folder structure is self-contained and portable.

Two git repositories live side by side per paper:

```
~/papers/my-paper-title/
├── my-paper-title-harness/   ← git repo (this template, copied per paper)
└── my-paper-title-overleaf/  ← git clone of the Overleaf remote (optional)
```

For Word-target papers, the Overleaf repo is absent. The target is configured in `paper.yaml`.

---

## Folder Structure

```
my-paper-harness/
├── CLAUDE.md                        ← Claude Code config and slash commands
├── paper.yaml                       ← per-paper configuration
├── .gitignore
│
├── ideas/
│   ├── recordings/                  ← drop MP3 files here
│   ├── transcripts/                 ← auto-generated Markdown from Whisper
│   └── requirements.md              ← distilled research question, contribution, outline
│
├── research/
│   ├── candidates.md                ← auto-generated: papers + mini-summaries + relevance
│   ├── candidates.bib               ← auto-generated: ready to import into Zotero
│   ├── scopus-query.txt             ← auto-generated Scopus search query
│   ├── scopus-export.csv            ← drop Scopus CSV export here (optional)
│   ├── references.bib               ← Better BibTeX auto-export from Zotero collection
│   └── pdfs/                        ← PDFs resolved via Zotero local API
│
├── article/
│   ├── sections/
│   │   ├── 10_abstract.md
│   │   ├── 11_introduction.md
│   │   ├── 20_related_work.md
│   │   ├── 30_methodology.md
│   │   ├── 40_results.md
│   │   ├── 50_discussion.md
│   │   └── 60_conclusion.md
│   └── output/                      ← compiled .tex / .docx / .pdf
│
├── sota/
│   └── summary.md                   ← AI-generated state-of-the-art narrative
│
└── _harness/
    ├── scripts/                     ← Python/shell scripts for each pipeline step
    ├── templates/                   ← Pandoc defaults, article skeleton, section stubs
    ├── prompts/                     ← Claude prompt templates per step
    └── sync-state.json              ← last-synced hash per section (for conflict detection)
```

---

## Paper Configuration

Each paper has a `paper.yaml` at its root:

```yaml
title: "My Paper Title"
target: overleaf                          # or: word
overleaf_repo: ../my-paper-title-overleaf # relative path to Overleaf git clone
csl: acm-sig-proceedings.csl              # citation style

zotero:
  collection: "my-paper-2025"
  bibtex_export: ~/Zotero/exports/my-paper.bib  # Better BibTeX auto-export path

sections:
  - 10_abstract
  - 11_introduction
  - 20_related_work
  - 30_methodology
  - 40_results
  - 50_discussion
  - 60_conclusion
```

For Word target, omit `overleaf_repo`. Compiled `.docx` is written to `article/output/`.

---

## Pipeline Commands

### `/paper:new "title" [--overleaf <url>]`
Creates a new paper folder from the harness template. Copies the full structure to `../title-harness/`, initializes a fresh git repo, writes a blank `paper.yaml`. If `--overleaf` is passed, clones the Overleaf repo to `../title-overleaf/` alongside it.

### `/paper:kickoff`
Runs the full pipeline in sequence: transcribe → ideate → research. Designed to be run after dropping in MP3 recordings so the workspace is populated before a writing session begins.

### `/paper:transcribe`
Runs local Whisper on all new MP3s in `ideas/recordings/`. Outputs one Markdown file per recording into `ideas/transcripts/`, named by date and source filename. Skips already-transcribed files.

**Dependency:** `openai-whisper`

### `/paper:ideate`
Claude reads all transcript files and existing notes, then interactively distills them into `ideas/requirements.md` — structured as: research question, proposed contribution, scope, and rough section outline. This is a conversational step.

### `/paper:research`
Performs autonomous literature discovery and prepares Zotero import artifacts:

1. Extracts keywords from `ideas/requirements.md`
2. Searches Semantic Scholar API and arXiv API (both free, no key required)
3. If `research/scopus-export.csv` is present, merges those results
4. Generates `research/candidates.md` — one entry per paper with: title, authors, year, abstract summary, and a relevance explanation tied to the research question
5. Generates `research/candidates.bib` — ready to drag-and-drop import into Zotero
6. Generates `research/scopus-query.txt` — a Scopus-formatted query (`TITLE-ABS-KEY(...)`) for the user to run manually in the Scopus web interface
7. If Zotero is running (detected via local API on port 23119), optionally pushes candidates directly to the configured Zotero collection

After running `/paper:research`, the user reviews candidates in Zotero, curates the collection, and Better BibTeX auto-exports to `research/references.bib`.

**Dependencies:** `requests`, Semantic Scholar API, arXiv API

### `/paper:sota`
Claude reads `research/candidates.md` (and `research/references.bib` if present) and generates `sota/summary.md` — a structured state-of-the-art narrative grouped by theme, with inline citations. Serves as reference material during writing.

### `/paper:deploy`
Compiles each Markdown section to LaTeX via Pandoc and syncs to the Overleaf repo:

1. Reads `paper.yaml` to determine target and Overleaf repo path
2. For each section in `sections[]`: compiles `article/sections/<number>_<name>.md` → `<overleaf_repo>/sections/<number>_<name>.tex` using Pandoc with `references.bib` and the configured CSL
3. Checks `sync-state.json` for conflicts (section changed in both `.md` and `.tex` since last sync) — warns rather than overwrites
4. Updates `sync-state.json` with new hashes
5. Stages the changed `.tex` files in the Overleaf repo (does not auto-push — user controls the `git push`)

For Word target: compiles all sections into a single `.docx` in `article/output/`.

The harness never touches `main.tex`, figures, style files, or anything else in the Overleaf repo.

### `/paper:pull`
Pulls changes from the Overleaf repo back to Markdown:

1. Runs `git pull` in the Overleaf repo
2. For each section that changed since last sync: converts `<number>_<name>.tex` → `<number>_<name>.md` via Pandoc (`pandoc -f latex -t markdown`)
3. Warns about sections with complex LaTeX (custom macros, non-standard environments) where round-trip fidelity may be reduced
4. Updates `sync-state.json`

Round-trip fidelity is high for prose, equations (`$...$`), and `[@citations]`. Custom LaTeX macros and complex tables require manual review after pull.

---

## Section Naming Convention

Sections are numbered with a prefix to control ordering and leave room for insertions:

| Prefix range | Usage |
|---|---|
| 10–19 | Front matter (abstract, intro) |
| 20–29 | Background / related work |
| 30–39 | Methodology |
| 40–49 | Results / findings |
| 50–59 | Discussion |
| 60–69 | Conclusion, limitations, future work |
| 70–79 | Appendices |

A section can be inserted between existing ones by using an unused number in the range (e.g., `21_background.md` between `20_related_work.md` and the next 30s section).

---

## Zotero Integration

Zotero is the source of truth for the curated bibliography. The harness feeds into it (via `candidates.bib` import or local API push) and reads from it (via Better BibTeX auto-export to `references.bib`).

| Direction | Mechanism |
|---|---|
| Harness → Zotero | Drag-and-drop `candidates.bib` import, or local API push if Zotero is running |
| Zotero → Harness | Better BibTeX plugin auto-exports collection to `research/references.bib` |
| PDF resolution | Zotero's "Find available PDFs" feature; harness locates attachments via Zotero local API |

`paper.yaml` configures the Zotero collection name and the Better BibTeX export path. If Zotero is not installed, the harness falls back to using `candidates.bib` directly as `references.bib`.

---

## Overleaf Integration

The Overleaf repo is a standard git clone. The harness writes only to `sections/*.tex` — never to `main.tex`, figures, or style files. `main.tex` is set up once by the user with `\input{sections/10_abstract}` etc. and is not modified by the harness thereafter.

Sync state is tracked in `_harness/sync-state.json` as a map of section name → last-synced SHA of both the `.md` and `.tex` files. Conflicts (both changed since last sync) produce a warning with a diff; the user chooses which version wins.

---

## Document Format

Articles are authored in **Pandoc-flavored Markdown**, which supports:
- `[@citation-key]` BibTeX citations
- `![Caption text](figure.png){#fig:label}` figure captions
- `@fig:label`, `@tbl:label`, `@eq:label` cross-references (via `pandoc-crossref`)
- `$...$` and `$$...$$` math
- Standard heading hierarchy

Pandoc compiles to LaTeX (for Overleaf) or `.docx` (for Word) via a `_harness/templates/pandoc-defaults.yaml` that pins the Pandoc settings per paper. Citation style is set by the `csl` field in `paper.yaml`.

---

## Dependencies

| Tool | Purpose | Install |
|---|---|---|
| Python 3.10+ | All scripts | pre-installed on macOS |
| `openai-whisper` | MP3 transcription | `pip install openai-whisper` |
| `pandoc` | Markdown ↔ LaTeX/Word compile | `brew install pandoc` |
| `pandoc-crossref` | Figure/table/equation cross-refs | `brew install pandoc-crossref` |
| `requests` | Literature search API calls | `pip install requests` |
| Zotero + Better BibTeX | Reference library management | manual install |

A `_harness/setup.sh` script checks for all dependencies and prints installation instructions for anything missing.

---

## Out of Scope

- Automated `git push` to Overleaf (the user controls when to push)
- Full-document Markdown → Word round-trip (sections only, no `main.tex` equivalent for Word)
- Downloading PDFs for papers behind paywalls (Zotero's "Find available PDFs" handles open-access resolution)
- Multi-user conflict resolution beyond hash-based warnings
