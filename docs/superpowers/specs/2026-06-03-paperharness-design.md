# Paperharness Design Spec
**Date:** 2026-06-03 (revised 2026-06-04)
**Status:** Approved

---

## Overview

Paperharness is a reusable template repository for writing scientific academic articles with Claude Code. Each new paper is a fresh `git clone` of this repo. The harness handles the full pipeline from raw voice ideas through literature discovery to a compiled LaTeX or Word document.

Primary user: an HCI researcher working across computer science, psychology, sociology, and computational social science, publishing in venues indexed by Scopus, ACM, IEEE, and arXiv. Final output is managed via Overleaf (LaTeX) or Word depending on the target journal.

---

## Architecture: Standalone Harness Folder

The harness IS the paper project. Each paper lives in its own clone:

```bash
git clone <paperharness-repo> my-paper-harness
```

Two git repositories live side by side per paper:

```
~/papers/my-paper/
├── my-paper-harness/     ← git clone of this template
└── my-paper-overleaf/    ← git clone of the Overleaf remote (optional)
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
│   └── transcripts/
│       ├── 2026-06-03_ideas.md      ← Whisper transcription (original language)
│       └── translated/
│           └── 2026-06-03_ideas.md  ← English translation (if non-English)
│
├── research/
│   ├── wiki/
│   │   ├── index.md                 ← root: research intent + topic map (replaces requirements.md)
│   │   ├── topics/
│   │   │   ├── attention.md         ← auto-created stub, links back to papers
│   │   │   └── hybrid-work.md
│   │   └── papers/
│   │       ├── smith2024attention.md
│   │       └── jones2023notifications.md
│   ├── candidates.md                ← auto-generated: papers + mini-summaries + relevance
│   ├── candidates.bib               ← auto-generated: ready to import into Zotero
│   ├── scopus-query.txt             ← auto-generated Scopus search query
│   ├── scopus-export.csv            ← drop Scopus CSV export here (optional)
│   ├── references.bib               ← Better BibTeX auto-export from Zotero collection
│   └── pdfs/                        ← PDFs resolved via Zotero
│
├── article/
│   ├── figures/                     ← figures referenced in Markdown sections
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
    ├── templates/
    │   ├── csl/                     ← bundled CSL files (APA default + HCI venues)
    │   ├── pandoc-defaults.yaml
    │   └── section-stub.md          ← template for new section files
    ├── prompts/                     ← Claude prompt templates per step
    ├── sync-state.json              ← last-synced hash per section pair
    └── .venv/                       ← isolated Python virtualenv (gitignored)
```

---

## Paper Configuration

```yaml
# paper.yaml
title: "My Paper Title"
target: overleaf                          # or: word
overleaf_repo: ../my-paper-overleaf       # relative path to Overleaf git clone
csl: apa.csl                              # default: apa.csl; replace with any bundled or custom CSL
citation_package: natbib                  # or: biblatex
language: en                              # Whisper transcription language (ISO 639-1)
whisper_model: large-v3-turbo             # tiny | base | small | medium | large-v3 | large-v3-turbo
research_max_results: 200                 # max candidates returned across all sources

zotero:
  collection: "my-paper-2025"
  bibtex_export: ~/Zotero/exports/my-paper.bib  # Better BibTeX auto-export path

exclude_sections:                         # sections to skip on deploy (drafts not ready)
  - 99_scratch
```

Sections are **auto-discovered** from `article/sections/` by scanning for `[0-9]+_*.md` files sorted numerically. No manual sections list needed.

---

## Pipeline Commands

### `/paper:kickoff`
Runs the full pipeline in sequence: **transcribe → ideate → research**.

- Stops with a clear message if `ideas/recordings/` is empty or contains no new MP3s.
- If `research/wiki/index.md` already exists, skips ideate and runs research directly.
- Ideate runs **non-interactively** in kickoff mode — generates a draft `index.md` without asking questions. Run `/paper:ideate` standalone for an interactive session.

### `/paper:transcribe`
Runs local Whisper (`large-v3-turbo` by default) on all new MP3s in `ideas/recordings/`. Skips already-transcribed files.

- Outputs one Markdown file per recording into `ideas/transcripts/`, named by date and source filename.
- If `language` in `paper.yaml` is not `en`, also produces an English translation via Whisper's built-in translation pass, saved to `ideas/transcripts/translated/`.

**Dependency:** `openai-whisper` (in `_harness/.venv/`)

### `/paper:ideate`
Reads all transcript files and generates `research/wiki/index.md`:

**YAML front matter:**
```yaml
---
research_question: "How do notification systems affect attention in hybrid work?"
keywords:
  - notification management
  - hybrid work
  - attention
  - interruption
contribution: "..."
---
```

**Followed by:**
- `## Summary` — 2–3 paragraph synthesis of all transcripts
- `## Anticipated Topics` — `[[topic]]` links Claude predicts will be relevant
- `## Open Questions` — questions to be answered by the literature

In **standalone (interactive) mode**: Claude asks clarifying questions to sharpen the research question and keywords before writing.  
In **kickoff (non-interactive) mode**: Claude generates a best-effort draft directly from transcripts. A `<!-- NOTE: Auto-generated draft. Review and refine before running /paper:research again. -->` header marks it as a first pass.

### `/paper:research`
Performs autonomous literature discovery and prepares Zotero import artifacts:

1. Reads keywords from the YAML front matter of `research/wiki/index.md`
2. Searches **Semantic Scholar API** and **arXiv API** (both free)
3. Merges `research/scopus-export.csv` if present
4. Returns up to `research_max_results` candidates (default 200), ranked by relevance, deduplicated by DOI and title similarity
5. Generates `research/candidates.md` — one entry per paper with title, authors, year, abstract summary, and relevance explanation
6. Generates `research/candidates.bib` — ready to import into Zotero
7. Generates `research/scopus-query.txt` — a Scopus-formatted `TITLE-ABS-KEY(...)` query for manual use
8. Creates `research/wiki/papers/<bibkey>.md` for each candidate (see Paper Node structure below)
9. Auto-creates `research/wiki/topics/<topic>.md` stubs for each `[[topic]]` link encountered
10. If Zotero is running (local API on port 23119), optionally pushes candidates to the configured collection

**Semantic Scholar API key:** Optional but recommended. Without a key the script degrades gracefully — slower, with automatic retries and a printed message with the signup URL. Store the key in `.env` (gitignored).

**Dependencies:** `requests` (in `_harness/.venv/`)

#### Paper Node structure (`research/wiki/papers/<bibkey>.md`)
```markdown
---
bibkey: smith2024attention
title: "Attention and Notifications in Hybrid Work"
authors: [Smith J, Jones A]
year: 2024
doi: 10.1145/xyz
venue: CHI
---

# Smith et al. (2024)

One-paragraph summary of the paper's contribution.

**Relevance:** One sentence on why this paper connects to the current research question.

## Topics
- [[attention]]
- [[notifications]]
- [[hybrid-work]]
```

#### Topic Node structure (`research/wiki/topics/<topic>.md`)
Auto-created as a stub on first encounter. Additional papers are appended automatically:

```markdown
# Attention

## Papers
- [[smith2024attention]]
- [[jones2023distraction]]
```

#### BibTeX Key Convention
Keys follow `authorYEARkeyword` format: first author last name (lowercase ASCII) + 4-digit year + first meaningful title word (lowercase, articles/prepositions stripped). Collisions get `a`, `b` suffixes.

Configure Better BibTeX in Zotero to match: `[auth:lower][year][title:select:1:1:fold:lower]`. This aligns with Google Scholar's BibTeX export format.

### `/paper:sota`
Claude traverses the wiki via link graph starting from `research/wiki/index.md`, pulling in topic nodes and paper nodes dynamically as it decides they're relevant. Generates `sota/summary.md` — a structured state-of-the-art narrative grouped by theme with inline `[@bibkey]` citations.

Papers not yet linked to any topic in `index.md` are listed at the end as "unclassified."

### `/paper:write [section]`
- **With section name**: opens that section, reads `sota/summary.md`, linked wiki nodes, and all `ideas/transcripts/` as context. Fills empty areas and `<!-- TODO: -->` markers. Preserves all existing prose. Treats `<!-- NOTE: -->` annotations as constraints.
- **Without section name**: audits all sections, lists which are empty / have TODO items / look complete, asks which to work on.

### `/paper:rewrite [section]`
Proposes a full rewrite of an existing section incorporating new information from transcripts, updated wiki, and new papers. Shows the proposed version as a diff and asks for confirmation before overwriting. Never rewrites silently.

### `/paper:deploy`
Compiles Markdown sections and syncs to the Overleaf repo (or produces Word output):

**LaTeX target:**
1. Auto-discovers sections in `article/sections/` sorted numerically, skipping `exclude_sections`
2. Compiles each `<number>_<name>.md` to `<overleaf_repo>/sections/<number>_<name>.tex` via Pandoc (`--no-standalone`, with `references.bib` and configured CSL)
3. On first deploy: creates `sections/` in the Overleaf repo, generates `harness-inputs.tex` containing all `\input{sections/...}` commands in order plus `\bibliography{references}` at the end. Add `\input{harness-inputs}` once to `main.tex`.
4. On subsequent deploys: updates `harness-inputs.tex` if sections were added or reordered
5. Copies `research/references.bib` to `<overleaf_repo>/references.bib`
6. Copies `article/figures/` to `<overleaf_repo>/figures/`
7. Checks `sync-state.json` for conflicts — warns rather than overwrites
8. Updates `sync-state.json`
9. Stages all changes in the Overleaf repo (user controls `git push`)

**Word target:**
Concatenates all section `.md` files in numeric order into a temporary combined file, runs a single Pandoc pass to produce `article/output/paper.docx`. Figures are embedded inline.

The harness never touches `main.tex`, style files, or anything else in the Overleaf repo beyond `sections/`, `figures/`, `references.bib`, and `harness-inputs.tex`.

### `/paper:pull`
Pulls Overleaf changes back to Markdown:

1. Runs `git pull` in the Overleaf repo
2. For each section changed since last sync: converts `<number>_<name>.tex` → `<number>_<name>.md` via Pandoc
3. Presents conflicts (both `.md` and `.tex` changed) interactively — Claude shows a diff per section and asks which version wins. Pass `--prefer-md` or `--prefer-tex` to resolve all conflicts in one direction without prompting.
4. Warns about sections with complex LaTeX where round-trip fidelity may be reduced
5. Updates `sync-state.json`

Round-trip fidelity is high for prose, `[@citations]`, and `$math$`. Custom macros and complex tables require manual review after pull.

---

## Section Naming Convention

| Prefix range | Usage |
|---|---|
| 10–19 | Front matter (abstract, intro) |
| 20–29 | Background / related work |
| 30–39 | Methodology |
| 40–49 | Results / findings |
| 50–59 | Discussion |
| 60–69 | Conclusion, limitations, future work |
| 70–79 | Appendices |

Add a section by creating the file — no config to update. Use gaps in the numbering to insert sections between existing ones.

---

## Comment Conventions

Two harness-wide Markdown comment conventions using HTML comments (stripped from all compiled output):

- `<!-- NOTE: ... -->` — author annotation explaining WHY something exists. Claude reads these as constraints and will not remove or rewrite annotated content without explicit instruction.
- `<!-- TODO: ... -->` — items to return to. `/paper:write` surfaces all TODO comments at the start of a session as a writing agenda.

---

## Document Format

Articles are authored in **Pandoc-flavored Markdown**:
- `[@citation-key]` — BibTeX citations
- `![Caption](../figures/name.png){#fig:label}` — figure captions (path relative to section file; VS Code preview resolves correctly)
- `@fig:label`, `@tbl:label`, `@eq:label` — cross-references (via `pandoc-crossref`)
- `$...$` and `$$...$$` — math
- `[[wiki-link]]` — Obsidian-style links in wiki files (rendered by Foam in VS Code)

Figure files live in `article/figures/`. Pandoc resolves paths relative to the section file during compile.

---

## Zotero Integration

| Direction | Mechanism |
|---|---|
| Harness → Zotero | Drag-and-drop `candidates.bib` import, or local API push if Zotero is running |
| Zotero → Harness | Better BibTeX plugin auto-exports collection to `research/references.bib` |
| PDF resolution | Zotero's "Find available PDFs" feature |

Configure Better BibTeX key pattern: `[auth:lower][year][title:select:1:1:fold:lower]`

If Zotero is not installed, the harness falls back to using `candidates.bib` directly as `references.bib`.

---

## Overleaf Integration

Sync state is tracked in `_harness/sync-state.json`:

```json
{
  "last_sync": "2026-06-04T10:30:00Z",
  "sections": {
    "20_related_work": {
      "md_hash": "abc123",
      "tex_hash": "def456",
      "synced_at": "2026-06-04T10:30:00Z"
    }
  }
}
```

New sections (no entry in sync-state) are always compiled on the next deploy.

---

## CSL Files

Bundled in `_harness/templates/csl/`:
- `apa.csl` — default
- `acm-sigchi.csl`
- `acm-general.csl`
- `ieee.csl`
- `nature.csl`

Paper-specific overrides: place any CSL file in `article/csl/` and reference it by filename in `paper.yaml`. For unlisted venues, the Zotero CSL repository (github.com/citation-style-language/styles) has 10,000+ styles.

---

## Recommended VS Code Extensions

| Extension | Purpose |
|---|---|
| Foam | `[[wiki-link]]` rendering, graph view for `research/wiki/` |
| Markdown Preview Enhanced | Pandoc-flavored Markdown preview with math, figure captions, cross-references |
| Citation Picker for Zotero | Insert `[@bibkey]` citations from your Zotero library without leaving VS Code |

---

## Dependencies

| Tool | Purpose | Install |
|---|---|---|
| Python 3.10+ | All scripts | pre-installed on macOS |
| `openai-whisper` | MP3 transcription | via `setup.sh` into `_harness/.venv/` |
| `requests` | Literature search API calls | via `setup.sh` into `_harness/.venv/` |
| `pandoc` | Markdown ↔ LaTeX/Word compile | `brew install pandoc` |
| `pandoc-crossref` | Figure/table/equation cross-refs | `brew install pandoc-crossref` |
| Zotero + Better BibTeX | Reference library management | manual install |

`_harness/setup.sh` creates an isolated virtualenv at `_harness/.venv/`, installs all Python dependencies, checks for Pandoc/pandoc-crossref, and prints instructions for anything missing. All scripts activate the virtualenv automatically.

---

## Out of Scope

- Automated `git push` to Overleaf (user controls when to push)
- Downloading PDFs for paywalled papers (Zotero handles open-access resolution)
- Multi-user conflict resolution beyond hash-based warnings and interactive Claude prompts
- Propagating harness script improvements across existing paper clones (manual copy)
