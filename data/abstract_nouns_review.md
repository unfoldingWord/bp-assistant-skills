# Abstract-noun word review (issue #234)

`abstract_nouns_review.csv` lists every English word that en_tn tags `figs-abstractnouns`, plus every word on `abstract_nouns.txt`. Use it to decide which words the bot should flag. Fill in the `team_decision` column (`abstract` / `not abstract` / `context`) for the rows below. The detector change (bp-assistant#465) will follow those decisions.

**Rule (editors' meeting 2026-10-07):** whether a note is needed depends on whether the ULT's *English* word is abstract, not on the Hebrew.

## Columns

| Column | Meaning |
|---|---|
| `english_word` | Bold word from the note's first sentence, singular, without a leading article or possessive |
| `in_abstract_nouns_txt` | On `data/abstract_nouns.txt` now |
| `en_tn_tags_total` / `_ot` / `_nt` | Number of en_tn master notes (2026-09-26, v91) tagging the word. Most OT notes were written 2022–2025; most NT notes are from 2018–2022 (lower quality) |
| `ult_occurrences`, `tag_rate` | How often the word appears in the aligned ULT, and tags ÷ occurrences |
| `top_source_lemmas` | The Hebrew/Greek lemma the ULT aligns the word to in the tagged verses (Strong's, count) |
| `en_tn_tags_in_bot_books` | Notes published today in the books the bot drafted and editors reviewed (JER, DAN, 1CH, AMO, ZEC, EZK, MIC). Bot notes kept unchanged aren't logged, so this stands in for "kept" |
| `bot_notes_reworded` / `bot_notes_dropped` / `editor_added_bot_missed` | Editor edits to bot notes, from `data/overnight-review/*/proposals.jsonl` (2026-07-28 to 2026-10-08) |
| `status` | Why the row needs attention (see below) |

## Rows that need a team decision

- **borderline** (raised at the meeting): disaster, calamity, abomination, evil, destruction. Also trouble and harm, which render the same רַע (H7451c) as disaster.
  - disaster: 6 notes (JER 5, EZK 1), all רַע H7451c. It occurs 51 times in the ULT, so it is tagged inconsistently. One bot note was dropped (JER 28:8).
  - calamity: 16 notes, mostly אֵיד H0343 and רַע H7451c.
  - evil: 133 notes, 2 bot notes dropped in JER.
- **conflict**: en_tn tags these words, but `figs-abstractnouns.md` says communication words are not abstract: instruction (24 notes, mostly מוּסָר "discipline"), testimony, commandment, promise, word, declaration, statute, covenant, law, decree, regulation, ordinance, rule. `abstract_nouns.txt` still lists commandment(s), decrees, and doctrines.
- **hold**: tagged 5+ times, but not added to the list until the team rules: kingdom, separation, keeping, plan, vision, cry, fortification, appetite, petition, request, supplication.
- **review: listed but never tagged**: 28 list words that en_tn never tags (e.g., seeing, fight, testing, provision).

## Changes made to `abstract_nouns.txt` in #234

- **Added** (tagged 5+ times in en_tn, clearly abstract, not borderline): pride, delight, insight, youth, horror, quarrel, valor, escape, profit, rebellion, stubbornness, discretion, prostitution, hatred, perpetuity, prosperity, toil, arrogance, contention, devastation, fury, happiness, meditation.
- **Removed**: `tribulatron` (typo; `tribulation` is already listed) and `profitable` (an adjective).
- **Deleted** the stale copy at `.claude/skills/issue-identification/scripts/detection/abstract_nouns.txt`; nothing read it.

## Rebuild

```bash
# Download and unpack en_tn, hbo_uhb, el-x-koine_ugnt, en_ult (Door43 master archives), then:
python3 scripts/build_abstract_noun_review.py --en-tn en_tn --uhb hbo_uhb \
  --ugnt el-x-koine_ugnt --ult en_ult --overnight data/overnight-review \
  --wordlist data/abstract_nouns.txt --out data/abstract_nouns_review.csv
```

The script loads one book at a time (it runs in under 200 MB). Rebuilding clears the `team_decision` column, so copy decisions over before you rebuild.
