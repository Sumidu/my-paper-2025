Run the autonomous literature search pipeline.

```bash
cd "$(git rev-parse --show-toplevel)" && _harness/.venv/bin/python _harness/scripts/research.py
```

After the script finishes:
- If it printed "No research/wiki/index.md found", tell the user to run `/paper:ideate` first to create the research wiki index.
- If it printed "No keywords", tell the user to add `keywords:` to the YAML front matter of `research/wiki/index.md`.
- If successful, report:
  - How many papers were found and from which sources
  - How many topic nodes were created in `research/wiki/topics/`
  - That `research/candidates.md` is ready to review
  - That `research/candidates.bib` is ready to import into Zotero (drag-and-drop or File → Import)
  - If a `research/scopus-export.csv` was merged, mention how many papers it contributed
- Suggest next steps: review `research/candidates.md`, import `candidates.bib` into Zotero, then run `/paper:sota` to generate the state-of-the-art summary.
