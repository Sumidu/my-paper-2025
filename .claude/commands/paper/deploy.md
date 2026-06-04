Compile Markdown sections and sync to Overleaf (or produce Word output).

```bash
cd "$(git rev-parse --show-toplevel)" && _harness/.venv/bin/python _harness/scripts/deploy.py
```

After the script finishes:

- If it printed `pandoc not found`, tell the user to install Pandoc from https://pandoc.org/installing.html.
- If it printed `overleaf_repo not set`, tell the user to add `overleaf_repo: ../my-overleaf-repo` to `paper.yaml`, pointing to a locally cloned Overleaf git repo.
- If it printed `Overleaf repo not found`, tell the user the path in `paper.yaml` doesn't exist — they may need to clone the repo first.
- If there were CONFLICT lines, tell the user which sections are in conflict and explain:
  - A conflict means both the `.md` (in this repo) and the `.tex` (in the Overleaf repo) changed since the last deploy.
  - To resolve: decide which version is authoritative and manually copy the content across, then run `/paper:deploy` again.
- If successful (Overleaf target), report:
  - How many sections were compiled to `.tex`
  - That `harness-inputs.tex` was written/updated in the Overleaf repo
  - That `references.bib` was copied from `research/candidates.bib`
  - Suggest: add `\input{harness-inputs}` to the main `.tex` file in Overleaf if not already there
- If successful (Word target), report:
  - The output path (`article/output/paper.docx`)
  - That citations were processed inline using the CSL style from `paper.yaml`
