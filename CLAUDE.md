# Paperharness

AI-assisted academic writing scaffold. Each command below is a slash command in Claude Code.

## Commands

| Command | Description |
|---|---|
| `/paper:kickoff` | Transcribe recordings → ideate → research (full pipeline) |
| `/paper:transcribe` | Transcribe new MP3s in `ideas/recordings/` via Whisper |
| `/paper:ideate` | Distill transcripts into `research/wiki/index.md` |
| `/paper:research` | Autonomous literature search, builds wiki + candidates.bib |
| `/paper:sota` | Generate state-of-the-art summary from wiki |
| `/paper:write [section]` | Fill gaps and TODO markers in a section |
| `/paper:rewrite [section]` | Propose full rewrite of a section with diff preview |
| `/paper:deploy` | Compile Markdown → LaTeX/Word and sync to Overleaf repo |
| `/paper:pull` | Pull Overleaf changes back to Markdown |

## Conventions

- `<!-- NOTE: ... -->` — constraint annotation, preserved through all rewrites
- `<!-- TODO: ... -->` — writing agenda item, surfaced by `/paper:write`
- Section files: `article/sections/<number>_<name>.md` (auto-discovered by number)
- Wiki links: `[[topic-name]]` (Obsidian/Foam style, links to `research/wiki/`)
- Citations: `[@bibkey]` (Pandoc/BibTeX style)
- Figures: `![Caption](../figures/name.png){#fig:label}`

## Setup

Run once per paper clone: `bash _harness/setup.sh`
