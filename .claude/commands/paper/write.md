Write or fill in a paper section.

Arguments: $ARGUMENTS

If $ARGUMENTS specifies a section name (e.g. "20_related_work"):
1. Read `article/sections/$ARGUMENTS.md`
2. Read `sota/summary.md` if it exists
3. Read all files in `ideas/transcripts/` and `ideas/transcripts/translated/` as context
4. Read all linked wiki nodes reachable from any `[[topic]]` references in the section
5. Find all `<!-- TODO: -->` markers in the section
6. Fill in empty areas and TODO markers with new content
7. Preserve all existing prose exactly
8. Treat `<!-- NOTE: -->` annotations as constraints — do not rewrite annotated content

If no section is specified:
- Read all section files in `article/sections/`
- List which sections are empty, which have TODO markers, and which appear complete
- Ask the user which section to work on
