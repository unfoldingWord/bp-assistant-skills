Don't use emojis, it breaks windows terminal.

## Primary Tasks
You are either being asked to:
1) Assist with creation of unfoldingWord Book Package items including the unfoldingWord Literal Text, unfoldingword Simplified Text, translation notes, or possibly translation questions. You will have skills for each of these, the top level skills may lead you to other skills.
2) Develop or improve the skills markdown files for task 1.

## Workflow
- **Lead with the results**: Put the most important summary, file links, or links to GatewayEdit/tcCreate at the top.
- **Be concise**: Use bullet points for findings. Avoid preambles and do NOT end with suggestions or questions.
- **Editor Review**: For editor-compare, specifically list the preferences identified and which instructions or glossary items were updated.

## Data Directories
All paths relative to project root:

- `data/en_tw/` - English Translation Words
- `data/published-tns/` - Published Translation Notes
- `data/ta-flat/` - Translation Academy (flat format)
- `data/published_ult/` - Published ULT (Hebrew)
- `data/published_ult_english/` - Published ULT (English)
- `data/published_ust/` - Published UST (Hebrew)
- `data/published_ust_english/` - Published UST (English)
- `data/hebrew_bible/` - Hebrew source texts
- `data/glossary/` - Glossary data
- `data/editor-feedback/` - Editor feedback and corrections
- `data/t4t/` - Translation for Translators data
- `data/cache/` - Generated indexes (Strong's index JSON, ~4MB)
- `data/quick-ref/` - Accumulated decisions from ULT-gen runs (CSV)
- `translation-issues.csv` - All 94 translation issues (complete)

## Output
- `output/` - Generated files and reports
- `tmp/` - Temporary processing files

**Output Folder Organization**: Always use book subfolders (e.g., `output/AI-ULT/HAB/HAB-03.usfm`, `output/issues/PSA/PSA-119.tsv`, `output/notes/PSA/PSA-065.tsv`). Never put files flat in the type directory. This applies to all output subdirectories: `AI-ULT`, `AI-UST`, `AI-UST/hints`, `issues`, `notes`, `tq`, `quality`, `review`, `editor-compare`.
