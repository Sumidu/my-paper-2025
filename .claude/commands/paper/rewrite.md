Propose a full rewrite of a paper section.

Arguments: $ARGUMENTS (section name, e.g. "20_related_work")

1. Read `article/sections/$ARGUMENTS.md`
2. Read `sota/summary.md` if it exists
3. Read all files in `ideas/transcripts/` and `ideas/transcripts/translated/`
4. Read linked wiki nodes reachable from `research/wiki/index.md`
5. Draft a complete rewrite of the section incorporating all available context
6. Show the proposed rewrite as a diff against the current content
7. Ask: "Apply this rewrite? (yes / no / edit first)"
8. Only overwrite the file if the user confirms with "yes"
9. Preserve all `<!-- NOTE: -->` annotations in the rewritten version
