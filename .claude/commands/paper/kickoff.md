Run the full kickoff pipeline. Steps:

1. **Transcribe** — run `/paper:transcribe` first
2. Check if `ideas/recordings/` has any MP3 files. If not, stop here and tell the user to add recordings before proceeding.
3. **Ideate** — if `research/wiki/index.md` already exists, skip this step and tell the user why. Otherwise run `/paper:ideate` in non-interactive mode.
4. **Research** — run `/paper:research`

Report clearly at each step what happened and what was produced.
