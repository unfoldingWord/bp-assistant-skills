# UST Strong's Index for Vocabulary Lookups

## Context

ULT-gen has a triage hierarchy for vocabulary: issues_resolved -> quick-ref/ult_decisions.csv -> Strong's index (`build_strongs_index.py`) -> glossaries -> fallback grep. The Strong's index maps Hebrew Strong's numbers to published ULT English renderings, turning 43MB of aligned USFM into a 4MB JSON lookup.

UST-gen has no equivalent. When agents need to check "how does published UST render H2617 (chesed)?" they either grep raw aligned USFM or just guess. This means:
- No fast way to see UST precedent for a Hebrew word
- No consistency check between new UST output and published patterns
- No ULT-vs-UST comparison for the same Strong's number (literal vs meaning-based)

The published UST uses the same aligned USFM format as ULT (zaln-s/zaln-e with x-strong), so the same parsing approach works. Currently 3 books local (1KI, PSA, NAM), 25 available via `fetch_all_ust.py`.

## Deliverables

### 1. UST Strong's Index Builder Script

**Create**: `.claude/skills/utilities/scripts/build_ust_index.py`
**Output**: `data/cache/ust_index.json`

Reuses the parsing architecture from `build_strongs_index.py` (zaln-s/zaln-e stack parsing, Strong's normalization) but targets `data/published_ust/`. Same CLI:

- `python3 build_ust_index.py` -- build if stale (daily check)
- `python3 build_ust_index.py --force` -- force rebuild
- `python3 build_ust_index.py --lookup H2617` -- print UST renderings
- `python3 build_ust_index.py --stats` -- summary statistics
- `python3 build_ust_index.py --compare H2617` -- show ULT vs UST renderings side-by-side (reads both indexes)

The `--compare` mode is the key new feature: it loads both `strongs_index.json` and `ust_index.json` and shows literal (ULT) vs meaning-based (UST) renderings for the same Strong's number. This helps agents understand the gap they need to bridge.

Output structure matches `strongs_index.json`:
```json
{
  "_meta": { "built": "2026-02-06", "file_count": 3, "total_alignments": 12000 },
  "H2617": {
    "lemma": "חֶסֶד",
    "total": 45,
    "renderings": [
      { "text": "faithful love", "count": 30, "refs": ["PSA 5:7", "PSA 6:4"] },
      { "text": "kind to me as you promised", "count": 8, "refs": ["PSA 13:5"] }
    ]
  }
}
```

Note: UST renderings will often be longer/more varied than ULT because UST unpacks meaning. This is expected.

The script should also auto-fetch if `data/published_ust/` has fewer than 5 files, using `fetch_all_ust.py` (with a prompt/flag so it's not surprising).

### 2. UST Decisions Quick-Ref File

**Create on first use**: `data/quick-ref/ust_decisions.csv`

Same pattern as `data/quick-ref/ult_decisions.csv`:
```csv
Strong,Hebrew,Rendering,Book,Context,Notes,Date
H2617,chesed,faithful love,PSA,dominant UST rendering 67%,,2026-02-06
```

Rules:
- Append-only
- Only record decisions that required checking published precedent
- Check for existing entry before appending
- Header created on first use

### 3. UST-gen SKILL.md Updates

**Modify**: `.claude/skills/UST-gen/SKILL.md`

**A.** Add UST index to the vocabulary lookup cascade in Step 3 / Scripts Reference section. Insert after the glossary check:

```bash
# Check UST Strong's index for published UST precedent
python3 .claude/skills/utilities/scripts/build_ust_index.py --lookup H2617

# Compare ULT vs UST renderings
python3 .claude/skills/utilities/scripts/build_ust_index.py --compare H2617

# Check prior UST decisions
grep "H2617" data/quick-ref/ust_decisions.csv 2>/dev/null
```

**B.** Add to Data Sources table:
- UST Strong's Index | `data/cache/ust_index.json` | Published UST renderings by Strong's number
- UST Decisions | `data/quick-ref/ust_decisions.csv` | Prior UST vocabulary decisions

**C.** Add `build_ust_index.py` to Scripts Reference section.

**D.** Add step for recording non-trivial vocabulary decisions to ust_decisions.csv.

### 4. Initial-Pipeline SKILL.md Note

**Modify**: `.claude/skills/initial-pipeline/SKILL.md`

Add a brief note under Wave 6 (UST Generation) that the UST-gen agent should use the UST index for rendering precedent.

## Key Files

| File | Action | Purpose |
|------|--------|---------|
| `.claude/skills/utilities/scripts/build_ust_index.py` | Create | Index builder script |
| `.claude/skills/utilities/scripts/build_strongs_index.py` | Read (reuse pattern) | Parsing architecture to follow |
| `data/published_ust/*.usfm` | Read (source) | 3 aligned USFM files (25 available to fetch) |
| `.claude/skills/UST-gen/SKILL.md` | Edit (3-4 spots) | Wire in triage hierarchy |
| `.claude/skills/initial-pipeline/SKILL.md` | Edit (1 line) | Note about index usage in wave 6 |
| `.claude/skills/utilities/scripts/fetch_all_ust.py` | Read (reference) | Auto-fetch if source sparse |

## Verification

1. **Script correctness**: Run `--stats`, verify file count matches `data/published_ust/` directory. Spot-check 3 Strong's numbers (H3068/Yahweh, H2617/chesed, H4428/king) -- renderings should reflect meaning-based translations.

2. **Compare mode**: `--compare H3068` should show ULT "Yahweh" vs UST "Yahweh" (same). `--compare H2617` should show ULT "covenant faithfulness" vs UST "faithful love" or similar (different).

3. **Staleness**: Run twice without `--force` -- second run should say "up to date."
