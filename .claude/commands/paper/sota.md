Generate the state-of-the-art summary.

## Steps

1. Read `research/wiki/index.md`. If it doesn't exist, stop and tell the user to run `/paper:ideate` first.
2. Parse the YAML front matter to get `research_question`, `keywords`, and `contribution`.
3. List all files in `research/wiki/topics/`. If there are none, stop and tell the user to run `/paper:research` first.
4. Read each topic file in `research/wiki/topics/`. Collect all `[[bibkey]]` references.
5. Read each referenced paper node from `research/wiki/papers/<bibkey>.md`.
6. If `sota/summary.md` already exists, read it before writing — preserve the section structure where it makes sense.

## Output

Write `sota/summary.md`. The file MUST start with YAML front matter:

---
generated: <today's ISO date, e.g. 2026-06-04>
sources: <N> papers, <M> topics
---

# State of the Art: <research_question from index.md>

## Overview

<2–3 paragraph synthesis of the field: what problem does this literature address,
what are the dominant approaches, and where is the frontier? Do not cite here —
this is orientation prose. Draw from the abstracts and the research question.>

## <Theme Name>

<Narrative paragraph(s) covering papers that cluster around this theme.
Use inline [@bibkey] citations after claims you draw from a specific paper.
Draw on paper abstracts. Aim for 150–250 words per theme.>

## <Theme Name>

...

## Research Gaps

<One focused paragraph identifying what the existing literature does NOT address
in relation to the `contribution` field from index.md. This is the space your
paper occupies. Be specific — name the missing methods, datasets, or evaluations.>

## References

<One bullet per cited paper: `- [@bibkey] Author et al. (year) — Title.`>

## Guidelines

- Identify 3–5 themes by clustering papers that share methods, datasets, or research questions. Merge similar topics if fewer emerge naturally.
- A paper can appear under multiple themes.
- Every paper referenced in a topic node should be cited at least once in the body.
- Do NOT use section headings that match keyword slugs directly (e.g., "Deep Learning"). Choose descriptive theme names like "Attention-Based Models for Sequential Data".
- Keep `sota/summary.md` as flat Pandoc-compatible Markdown (no Obsidian directives, no `[[links]]` in the body — only `[@bibkey]` citations).
- After writing, report: how many papers were cited, how many themes, and the output path.
