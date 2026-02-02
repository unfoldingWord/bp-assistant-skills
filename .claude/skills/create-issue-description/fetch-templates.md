# Skill: Fetch TN Templates

## Purpose
Fetch the TN Templates Google Spreadsheet containing official templates for translation notes, including templates for metaphors and other figures of speech.

## When to Use
- When you need the exact wording for a translation note template
- When checking how to format a specific type of note (figs-metaphor, figs-idiom, etc.)
- When verifying available alternate translation patterns

## Usage

### Fetch with daily caching (recommended):
```bash
python .claude\skills\utilities\scripts\fetch_templates.py
```

### Force re-fetch even if cached today:
```bash
python .claude\skills\utilities\scripts\fetch_templates.py --force
```

### Fetch with custom output path:
```bash
python .claude\skills\utilities\scripts\fetch_templates.py -o templates.csv
```

### Fetch specific sheet by gid:
```bash
python .claude\skills\utilities\scripts\fetch_templates.py --gid 0 -o main_templates.csv
```

### Fetch as TSV:
```bash
python .claude\skills\utilities\scripts\fetch_templates.py -f tsv -o templates.tsv
```

### List known sheets:
```bash
python .claude\skills\utilities\scripts\fetch_templates.py --list
```

### Custom spreadsheet:
```bash
python .claude\skills\utilities\scripts\fetch_templates.py --sheet-id YOUR_SHEET_ID --gid 0 -o output.csv
```

## Default Spreadsheet
ID: `1ot6A7RxcsxM_Wv94sauoTAaRPO5Q-gynFqMHeldnM64` (Sample TN Templates)

## Known Sheet GIDs
- Default (no gid): AI templates tab

To find other gids, look at the spreadsheet URL - the gid appears as `#gid=NUMBER`

## Output Format
CSV or TSV with template columns saved to `data\templates.csv`. Parse as needed for your workflow.

## Example Workflow
1. Fetch the templates spreadsheet
2. Filter/search for the relevant support reference (e.g., figs-metaphor)
3. Use the template text as a starting point for your note
