Pull Overleaf changes back to Markdown.

```bash
cd "$(git rev-parse --show-toplevel)" && _harness/.venv/bin/python _harness/scripts/pull.py
```

After the script finishes:

- If it printed `overleaf_repo not set`, tell the user to add `overleaf_repo: ../my-overleaf-repo` to `paper.yaml`.
- If it printed `git pull failed`, show the error and ask if they want to resolve the git conflict manually.
- If there were CONFLICT lines, tell the user which sections are in conflict and explain:
  - A conflict means both the Markdown file (this repo) and the LaTeX file (Overleaf) changed since the last sync.
  - To resolve: open the conflicting section `.md` and the corresponding `.tex` side by side. Merge the changes, update the `.md`, then run `/paper:deploy` to push the resolved version back to Overleaf.
- If successful, report:
  - How many sections were updated (pulled and converted from `.tex`)
  - How many sections were unchanged (skipped)
  - Remind the user that round-trip conversion preserves prose and citations well, but complex LaTeX macros and custom environments may need manual review.
- Suggest next steps: review any pulled sections for conversion artifacts, then continue writing with `/paper:write`.
