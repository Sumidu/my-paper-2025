Generate or update `research/wiki/index.md` from the transcripts in `ideas/transcripts/`.

Arguments: $ARGUMENTS

If $ARGUMENTS contains "noninteractive", run without asking questions — generate a best-effort draft directly from the transcripts.

Otherwise, run interactively:
1. Read all files in `ideas/transcripts/` (and `ideas/transcripts/translated/` if present)
2. Ask the user one question at a time to clarify: research question, intended contribution, target audience, key concepts
3. After each answer, incorporate it into your understanding
4. When you have enough clarity, write `research/wiki/index.md` with:

---
research_question: "<the research question>"
keywords:
  - <keyword 1>
  - <keyword 2>
  - <keyword 3>
  - <keyword 4>
  - <keyword 5>
contribution: "<one sentence on the contribution>"
---

Followed by:
- `## Summary` — 2–3 paragraph synthesis of the transcripts
- `## Anticipated Topics` — `[[topic]]` wiki links for concepts likely to appear in the literature
- `## Open Questions` — questions the literature search should answer

In non-interactive mode: add this comment at the top of the file:
`<!-- NOTE: Auto-generated draft. Review and refine keywords before running /paper:research again. -->`
