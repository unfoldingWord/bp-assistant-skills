#!/usr/bin/env python3
"""
Test suite: Prompt-Over-Code vs Previous Workflow

Compares old script-based approaches against new prompt-over-code approaches
for Hebrew quote extraction, passive voice detection, and AT fit quality.
Also validates against published translation notes where available.

Usage:
    # Run all tests on PSA 78
    python3 test_prompt_over_code.py --test all --chapter 78

    # Just Hebrew quote comparison
    python3 test_prompt_over_code.py --test quote \
        --aligned-usfm output/AI-ULT/PSA/PSA-078-aligned.usfm \
        --issues output/issues/PSA/PSA-078.tsv

    # Just passive detection on published chapters
    python3 test_prompt_over_code.py --test published --chapter 1

    # AT fit check on existing output
    python3 test_prompt_over_code.py --test at-fit --notes output/notes/PSA-078.tsv
"""

import argparse
import glob
import json
import os
import re
import sys
import unicodedata

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))

def _project_root():
    """Resolve project root (4 levels up from scripts/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_script_dir()))))

def _find_data_root():
    """Find the data root -- could be in this repo or the sibling cSkillBP repo."""
    root = _project_root()
    # Check for data in this repo first
    if os.path.isdir(os.path.join(root, 'data', 'hebrew_bible')):
        return root
    # Fall back to sibling repo
    sibling = os.path.join(os.path.dirname(root), 'cSkillBP')
    if os.path.isdir(os.path.join(sibling, 'data', 'hebrew_bible')):
        return sibling
    return root

def _find_output_root():
    """Find the output root -- could be in this repo or sibling."""
    root = _project_root()
    if os.path.isdir(os.path.join(root, 'output', 'AI-ULT')):
        return root
    sibling = os.path.join(os.path.dirname(root), 'cSkillBP')
    if os.path.isdir(os.path.join(sibling, 'output', 'AI-ULT')):
        return sibling
    return root

# ---------------------------------------------------------------------------
# Hebrew source parsing
# ---------------------------------------------------------------------------

def parse_hebrew_source(usfm_path):
    r"""Parse Hebrew source USFM into {chapter:verse -> full_verse_text}.

    Returns the raw text of each verse, preserving inter-word characters
    (maqaf, joiners, punctuation) so that substring matching against
    published TN OrigQuote values works correctly.
    """
    if not usfm_path or not os.path.exists(usfm_path):
        return {}

    verses = {}
    current_chapter = None
    current_verse = None

    for line in open(usfm_path, 'r', encoding='utf-8'):
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            current_chapter = ch_match.group(1)
            current_verse = None
            continue

        v_match = re.match(r'.*\\v\s+(\d+[-\d]*|front)\s*(.*)', line)
        if v_match and current_chapter:
            current_verse = v_match.group(1)

        if not current_chapter or not current_verse:
            continue

        key = f"{current_chapter}:{current_verse}"
        verses.setdefault(key, '')

        # Strip USFM markers but preserve Hebrew text and inter-word chars.
        # Extract \w surface|attrs\w* -> surface, keep text between markers.
        raw = line
        # Remove \v marker
        raw = re.sub(r'\\v\s+\d+[-\d]*\s*', '', raw)
        # Replace \w surface|...\w* with just surface
        raw = re.sub(r'\\w\s+([^|\\]+)\|[^\\]*\\w\*', r'\1', raw)
        # Remove remaining USFM markers
        raw = re.sub(r'\\[a-z]+\d*\s*', '', raw)
        # Remove sof pasuq and similar punctuation marks that aren't in quotes
        raw = raw.replace('\u05c3', '')  # sof pasuq
        # Collapse runs of whitespace
        raw = re.sub(r'\s+', ' ', raw).strip()
        if raw:
            if verses[key]:
                verses[key] += ' ' + raw
            else:
                verses[key] = raw

    return verses

def parse_hebrew_source_words(usfm_path):
    """Parse Hebrew source into {chapter:verse -> [word_surface, ...]}."""
    if not usfm_path or not os.path.exists(usfm_path):
        return {}

    verses = {}
    current_chapter = None
    current_verse = None

    for line in open(usfm_path, 'r', encoding='utf-8'):
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            current_chapter = ch_match.group(1)
            current_verse = None
            continue

        v_match = re.match(r'.*\\v\s+(\d+[-\d]*|front)\s*(.*)', line)
        if v_match and current_chapter:
            current_verse = v_match.group(1)

        if not current_chapter or not current_verse:
            continue

        key = f"{current_chapter}:{current_verse}"
        verses.setdefault(key, [])

        for m in re.finditer(r'\\w\s+([^|\\]+)\|[^\\]*\\w\*', line):
            word_text = m.group(1).strip()
            if word_text:
                verses[key].append(word_text)

    return verses

# ---------------------------------------------------------------------------
# ULT plain text extraction
# ---------------------------------------------------------------------------

def extract_ult_verses(usfm_path):
    """Extract plain English text per verse from ULT USFM.

    Returns { "chapter:verse" -> "plain text" }.
    """
    if not usfm_path or not os.path.exists(usfm_path):
        return {}

    verses = {}
    current_chapter = None
    current_verse = None
    current_text = []

    for line in open(usfm_path, 'r', encoding='utf-8'):
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            if current_chapter and current_verse and current_text:
                key = f"{current_chapter}:{current_verse}"
                verses[key] = ' '.join(current_text)
            current_chapter = ch_match.group(1)
            current_verse = None
            current_text = []
            continue

        v_match = re.match(r'(.*?)\\v\s+(\d+[-\d]*|front)\s*(.*)', line)
        if v_match and current_chapter:
            if current_verse and current_text:
                key = f"{current_chapter}:{current_verse}"
                verses[key] = ' '.join(current_text)
            current_verse = v_match.group(2)
            current_text = []
            line = v_match.group(3)

        if not current_chapter or not current_verse:
            continue

        # Strip USFM markers and extract readable text
        text = line
        # Remove alignment markers
        text = re.sub(r'\\zaln-[se][^*]*\*', '', text)
        # Extract word content from \w markers
        text = re.sub(r'\\w\s+([^|\\]+)\|[^\\]*\\w\*', r'\1', text)
        # Remove remaining markers
        text = re.sub(r'\\[a-z]+\d*\s*', '', text)
        # Clean up braces (implied words)
        text = re.sub(r'\{([^}]*)\}', r'\1', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            current_text.append(text)

    if current_chapter and current_verse and current_text:
        key = f"{current_chapter}:{current_verse}"
        verses[key] = ' '.join(current_text)

    return verses

# ---------------------------------------------------------------------------
# Published TN parsing
# ---------------------------------------------------------------------------

def parse_published_tns(tsv_path, chapter=None):
    """Parse published TN TSV.

    Returns list of dicts with keys:
        book, chapter, verse, id, support_ref, orig_quote, occurrence, gl_quote, note
    If chapter is provided, filters to that chapter only.
    """
    if not tsv_path or not os.path.exists(tsv_path):
        return []

    rows = []
    with open(tsv_path, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split('\t')
        for line in f:
            cols = line.rstrip('\n').split('\t')
            while len(cols) < len(header):
                cols.append('')

            # Parse the reference format -- could be "PSA 1 1" or "1:1"
            # Published TN format: Book Chapter Verse ID SupportReference OrigQuote Occurrence GLQuote OccurrenceNote
            row_chapter = cols[1] if len(cols) > 1 else ''
            row_verse = cols[2] if len(cols) > 2 else ''

            if chapter is not None and row_chapter != str(chapter):
                continue

            # Skip intro rows for verse-level analysis
            if 'intro' in row_verse or 'intro' in row_chapter:
                continue

            rows.append({
                'book': cols[0] if len(cols) > 0 else '',
                'chapter': row_chapter,
                'verse': row_verse,
                'id': cols[3] if len(cols) > 3 else '',
                'support_ref': cols[4] if len(cols) > 4 else '',
                'orig_quote': cols[5] if len(cols) > 5 else '',
                'occurrence': cols[6] if len(cols) > 6 else '',
                'gl_quote': cols[7] if len(cols) > 7 else '',
                'note': cols[8] if len(cols) > 8 else '',
            })

    return rows

# ---------------------------------------------------------------------------
# Issue TSV parsing
# ---------------------------------------------------------------------------

def parse_issue_tsv(tsv_path):
    """Parse issue TSV (7-col format: Book, Ref, SRef, GLQuote, Go?, AT, Explanation).

    Returns list of dicts.
    """
    if not tsv_path or not os.path.exists(tsv_path):
        return []

    items = []
    with open(tsv_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            cols = line.split('\t')
            while len(cols) < 7:
                cols.append('')
            # Skip header
            if line_num == 1 and cols[0].lower() == 'book':
                continue
            # Skip intro rows
            if ':intro' in cols[1]:
                continue
            items.append({
                'book': cols[0].strip(),
                'ref': cols[1].strip(),
                'sref': cols[2].strip(),
                'gl_quote': cols[3].strip(),
                'go': cols[4].strip(),
                'at': cols[5].strip(),
                'explanation': cols[6].strip(),
            })
    return items

# ---------------------------------------------------------------------------
# Output notes TSV parsing
# ---------------------------------------------------------------------------

def parse_notes_tsv(tsv_path):
    """Parse output notes TSV (Reference, ID, Tags, SupportReference, Quote, Occurrence, Note).

    Returns list of dicts.
    """
    if not tsv_path or not os.path.exists(tsv_path):
        return []

    rows = []
    with open(tsv_path, 'r', encoding='utf-8') as f:
        header_line = f.readline().strip()
        for line in f:
            cols = line.rstrip('\n').split('\t')
            while len(cols) < 7:
                cols.append('')
            rows.append({
                'reference': cols[0],
                'id': cols[1],
                'tags': cols[2],
                'support_ref': cols[3],
                'quote': cols[4],
                'occurrence': cols[5],
                'note': cols[6],
            })
    return rows

# ---------------------------------------------------------------------------
# Hebrew substring validation
# ---------------------------------------------------------------------------

def normalize_hebrew(text):
    """Normalize Hebrew text for comparison.

    Removes joiner chars, applies Unicode NFC to canonically order
    combining marks (vowels/cantillation can appear in different orders
    across USFM sources).
    """
    text = text.replace('\u2060', '').replace('\u200f', '').replace('\u200e', '')
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def is_hebrew_substring(word, verse_text):
    """Check if a Hebrew word (from alignment/quote) is an exact Unicode substring of the verse."""
    word_clean = normalize_hebrew(word)
    verse_clean = normalize_hebrew(verse_text)
    if not word_clean:
        return False
    return word_clean in verse_clean

def check_hebrew_word_order(words, verse_text):
    """Check if Hebrew words appear in the correct order in the verse text.

    Returns True if all found words appear in left-to-right order within the verse.
    """
    verse_clean = normalize_hebrew(verse_text)
    last_pos = -1
    for word in words:
        word_clean = normalize_hebrew(word)
        if not word_clean:
            continue
        pos = verse_clean.find(word_clean, last_pos + 1 if last_pos >= 0 else 0)
        if pos < 0:
            # Word not found -- can't verify order
            return False
        if pos < last_pos:
            return False
        last_pos = pos
    return True

# ===========================================================================
# TEST 1: Hebrew Quote Extraction Comparison
# ===========================================================================

def test_hebrew_quotes(aligned_usfm, issues_tsv, hebrew_source_path):
    """Compare old extract_quotes_from_alignment.py vs new extract_alignment_data.py."""

    # Import old script
    old_script_dir = os.path.join(_script_dir(), '.old')
    sys.path.insert(0, old_script_dir)
    try:
        from extract_quotes_from_alignment import extract_quotes, parse_aligned_usfm as old_parse
    finally:
        sys.path.pop(0)

    # Import new script
    sys.path.insert(0, _script_dir())
    try:
        from extract_alignment_data import parse_aligned_usfm as new_parse
    finally:
        sys.path.pop(0)

    # Parse issue items
    items = parse_issue_tsv(issues_tsv)
    if not items:
        return {'test': 'hebrew_quotes', 'error': f'No items found in {issues_tsv}', 'results': []}

    # Load Hebrew source for validation
    hebrew_verses = parse_hebrew_source(hebrew_source_path)

    # Run OLD script
    old_items = [{'ref': it['ref'], 'gl_quote': it['gl_quote'], 'book': it['book']} for it in items]
    old_results = extract_quotes(aligned_usfm, old_items)

    # Run NEW script (just alignment data extraction)
    new_alignment = new_parse(aligned_usfm)

    results = []
    old_success = 0
    old_fail = 0
    new_coverage = 0

    for i, item in enumerate(items):
        ref = item['ref']
        gl_quote = item['gl_quote']
        old_hebrew = old_results[i]['Quote'] if i < len(old_results) else ''
        verse_text = hebrew_verses.get(ref, '')

        # Validate old Hebrew quote
        old_valid = True
        old_order_correct = True
        if old_hebrew:
            old_words = old_hebrew.split()
            for w in old_words:
                if not is_hebrew_substring(w, verse_text):
                    old_valid = False
                    break
            if old_valid and len(old_words) > 1:
                old_order_correct = check_hebrew_word_order(old_words, verse_text)
        else:
            old_valid = False
            old_order_correct = False

        if old_valid:
            old_success += 1
        else:
            old_fail += 1

        # Check new alignment data coverage
        new_words = new_alignment.get(ref, [])
        alignment_word_count = len(new_words)

        # Check if alignment covers the gl_quote words
        alignment_eng_words = {w['eng'].lower().strip('.,;:!?\'"{}[]') for w in new_words}
        quote_tokens = re.findall(r'[{}\w]+(?:[-\'][{}\w]+)*', gl_quote.lower())
        # Simple coverage check: are most quote words present in alignment?
        covered = sum(1 for t in quote_tokens if t in alignment_eng_words)
        covers_quote = covered >= len(quote_tokens) * 0.7 if quote_tokens else False

        if covers_quote:
            new_coverage += 1

        # Validate alignment Hebrew words against source
        alignment_heb_valid = True
        for w in new_words:
            if w.get('heb') and verse_text:
                if not is_hebrew_substring(w['heb'], verse_text):
                    alignment_heb_valid = False
                    break

        results.append({
            'ref': ref,
            'gl_quote': gl_quote,
            'old_hebrew': old_hebrew,
            'old_valid': old_valid,
            'old_order_correct': old_order_correct,
            'alignment_word_count': alignment_word_count,
            'alignment_covers_quote': covers_quote,
            'alignment_heb_valid': alignment_heb_valid,
        })

    total = len(items)
    return {
        'test': 'hebrew_quotes',
        'total_items': total,
        'old_success': old_success,
        'old_fail': old_fail,
        'old_success_rate': old_success / total if total else 0,
        'new_coverage': new_coverage,
        'new_coverage_rate': new_coverage / total if total else 0,
        'results': results,
    }

# ===========================================================================
# TEST 2: Passive Voice Detection Comparison
# ===========================================================================

# New detection pattern (mirrors the prompt instructions in figs-activepassive.md)
PASSIVE_AUXILIARIES = {'be', 'is', 'are', 'am', 'was', 'were', 'been', 'being'}

STATIVE_ADJECTIVES = {
    'ashamed', 'afraid', 'alone', 'afflicted', 'angry', 'anxious',
    'aware', 'alive', 'asleep', 'awake', 'absent', 'able',
    'blessed', 'blameless',
    'clean', 'certain', 'content',
    'dead', 'drunk',
    'empty', 'evil',
    'full', 'faithful', 'free',
    'glad', 'good', 'great', 'guilty', 'gracious',
    'holy', 'humble', 'hungry', 'happy',
    'innocent', 'ill',
    'jealous', 'just', 'joyful',
    'kind',
    'like', 'lost', 'low',
    'merciful', 'mighty',
    'naked', 'near',
    'obedient', 'old',
    'perfect', 'pleasant', 'poor', 'present', 'proud', 'pure',
    'quick', 'quiet',
    'ready', 'rich', 'righteous', 'right',
    'sad', 'safe', 'sick', 'silent', 'sinful', 'sorry', 'strong', 'sure', 'still',
    'true', 'troubled',
    'unclean', 'unworthy', 'upright',
    'weary', 'weak', 'well', 'whole', 'wicked', 'wise', 'worthy', 'wrong',
    'young',
}

# Same participle endings / irregulars as old script for apples-to-apples comparison
PARTICIPLE_ENDINGS = ('ed', 'en', 'wn', 'ung', 'orn', 'oken', 'osen',
                      'otten', 'iven', 'aken', 'tten')

IRREGULAR_PARTICIPLES = {
    'been', 'done', 'gone', 'seen', 'known', 'shown', 'given', 'taken',
    'made', 'said', 'told', 'found', 'thought', 'brought', 'bought',
    'caught', 'taught', 'sought', 'felt', 'left', 'held', 'kept', 'slept',
    'met', 'sent', 'spent', 'built', 'lent', 'lost', 'meant', 'heard',
    'born', 'borne', 'worn', 'torn', 'sworn', 'chosen', 'frozen', 'spoken',
    'broken', 'stolen', 'woken', 'written', 'hidden', 'ridden', 'driven',
    'risen', 'forgiven', 'forgotten', 'begotten', 'bitten', 'eaten', 'beaten',
    'shaken', 'forsaken', 'mistaken', 'undertaken', 'struck', 'stuck', 'stung',
    'swung', 'hung', 'sung', 'rung', 'sprung', 'begun', 'run', 'won', 'spun',
    'put', 'cut', 'shut', 'set', 'let', 'hit', 'hurt', 'cast', 'burst', 'cost',
    'spread', 'shed', 'split', 'spit', 'quit', 'rid', 'bid', 'read', 'led',
    'fed', 'bled', 'bred', 'sped', 'fled', 'paid', 'laid', 'called', 'filled',
    'killed', 'named', 'blessed', 'cursed', 'gathered', 'scattered', 'covered',
    'revealed', 'fulfilled', 'proclaimed', 'announced', 'established',
    'justified', 'sanctified', 'glorified', 'baptized', 'circumcised',
}

NOT_PARTICIPLES = {
    'not', 'that', 'what', 'but', 'just', 'about', 'out', 'without',
    'light', 'right', 'night', 'might', 'sight', 'fight', 'eight',
    'great', 'heart', 'part', 'start', 'apart', 'art',
    'in', 'then', 'when', 'often', 'even', 'open', 'seven', 'eleven',
    'own', 'down', 'town', 'brown', 'grown', 'known',
    'men', 'women', 'children', 'brethren',
    'heaven', 'garden', 'burden', 'sudden', 'golden', 'wooden', 'hidden',
    'often', 'listen', 'hasten', 'fasten', 'lessen', 'lesson',
    'and', 'hand', 'land', 'stand', 'understand', 'command', 'demand',
    'around', 'ground', 'sound', 'found', 'bound', 'round', 'wound',
    'hundred', 'kindred',
}

def _is_past_participle(word):
    """Check if a word is likely a past participle (new pattern, with stative exclusion)."""
    wl = word.lower()
    if wl in STATIVE_ADJECTIVES:
        return False
    if wl in NOT_PARTICIPLES:
        return False
    if wl in IRREGULAR_PARTICIPLES:
        return True
    for ending in PARTICIPLE_ENDINGS:
        if wl.endswith(ending) and len(wl) > len(ending) + 2:
            return True
    return False

def find_passives_new(text):
    """New-pattern passive detection (mirrors prompt instructions)."""
    passives = []
    clean_text = re.sub(r'\\[a-z]+\s*', '', text)
    words = clean_text.split()

    i = 0
    while i < len(words):
        word = words[i].lower().strip('.,;:!?"\'"{}[]')
        if word in PASSIVE_AUXILIARIES:
            for j in range(i + 1, min(i + 4, len(words))):
                next_word = words[j].strip('.,;:!?"\'"{}[]')
                if _is_past_participle(next_word):
                    phrase_words = words[i:j+1]
                    phrase = ' '.join(w.strip('.,;:!?"\'"{}[]') for w in phrase_words)
                    passives.append(phrase)
                    i = j
                    break
        i += 1
    return passives

def test_passive_detection(ult_verses, chapter=None):
    """Compare old detect_activepassive.py vs new prompt-based pattern."""

    # Import old script
    old_script_dir = os.path.join(
        _project_root(), '.claude', 'skills', 'issue-identification',
        'scripts', 'detection', '.old'
    )
    sys.path.insert(0, old_script_dir)
    try:
        from detect_activepassive import find_passives_in_text as old_find_passives
    finally:
        sys.path.pop(0)

    results = []
    both_count = 0
    old_only_count = 0
    new_only_count = 0
    agree_count = 0

    for ref in sorted(ult_verses.keys(), key=_ref_sort_key):
        if chapter is not None:
            ref_ch = ref.split(':')[0]
            if ref_ch != str(chapter):
                continue

        text = ult_verses[ref]

        # Old script
        old_detections = old_find_passives(text)
        old_phrases = set(d['phrase'] for d in old_detections)

        # New pattern
        new_phrases = set(find_passives_new(text))

        both = old_phrases & new_phrases
        old_only = old_phrases - new_phrases
        new_only = new_phrases - old_phrases

        match = old_phrases == new_phrases

        both_count += len(both)
        old_only_count += len(old_only)
        new_only_count += len(new_only)
        if match:
            agree_count += 1

        results.append({
            'verse': ref,
            'text': text[:120] + ('...' if len(text) > 120 else ''),
            'old_passives': sorted(old_phrases),
            'new_passives': sorted(new_phrases),
            'match': match,
            'old_only': sorted(old_only),
            'new_only': sorted(new_only),
        })

    total_verses = len(results)
    return {
        'test': 'passive_detection',
        'total_verses': total_verses,
        'agreement_count': agree_count,
        'agreement_rate': agree_count / total_verses if total_verses else 0,
        'both_count': both_count,
        'old_only_count': old_only_count,
        'new_only_count': new_only_count,
        'results': results,
    }

# ===========================================================================
# TEST 3: AT Fit Quality Check
# ===========================================================================

def strip_braces(text):
    """Remove {curly braces} used for implied words in ULT."""
    return re.sub(r'\{([^}]*)\}', r'\1', text)

CONJUNCTIONS = {'and', 'but', 'so', 'then', 'or'}
PREPOSITIONS = {'in', 'to', 'from', 'by', 'for', 'with', 'on', 'at', 'of'}

def test_at_fit(notes_source, ult_verses=None, prepared_json=None, generated_json=None):
    """Check AT substitution quality in output notes.

    Can accept either:
    - A notes TSV path (notes_source)
    - prepared_json + generated_json paths
    """

    items_to_check = []

    # Load from prepared + generated JSON
    if prepared_json and generated_json and os.path.exists(prepared_json) and os.path.exists(generated_json):
        with open(prepared_json) as f:
            prepared = json.load(f)
        with open(generated_json) as f:
            generated = json.load(f)

        for item in prepared.get('items', []):
            note_text = generated.get(item.get('id', ''), '')
            if not note_text:
                continue
            items_to_check.append({
                'ref': item.get('reference', ''),
                'gl_quote': item.get('gl_quote_roundtripped') or item.get('gl_quote', ''),
                'ult_verse': item.get('ult_verse', ''),
                'note': note_text,
            })

    # Load from notes TSV
    elif notes_source and os.path.exists(notes_source):
        rows = parse_notes_tsv(notes_source)
        for row in rows:
            # We need gl_quote and ult_verse -- extract what we can from the note
            items_to_check.append({
                'ref': row['reference'],
                'gl_quote': '',  # Not directly available in output TSV
                'ult_verse': '',
                'note': row['note'],
                'quote': row['quote'],
            })

    results = []
    orphaned_conj_count = 0
    orphaned_prep_count = 0
    cap_error_count = 0

    for item in items_to_check:
        note = item.get('note', '')
        # Extract AT text from [square brackets]
        at_matches = re.findall(r'Alternate translation: \[([^\]]+)\]', note)
        if not at_matches:
            # Try broader pattern
            at_matches = re.findall(r'\[([^\]]+)\]', note)

        gl_quote = item.get('gl_quote', '')
        ult_verse = item.get('ult_verse', '')
        ref = item.get('ref', '')

        for at_text in at_matches:
            result_entry = {
                'ref': ref,
                'gl_quote': gl_quote,
                'at': at_text,
                'substitution': '',
                'orphaned_conjunction': False,
                'orphaned_preposition': False,
                'capitalization_ok': True,
            }

            if gl_quote and ult_verse:
                clean_ult = strip_braces(ult_verse)
                clean_quote = strip_braces(gl_quote)

                # Try substitution
                if clean_quote in clean_ult:
                    sub = clean_ult.replace(clean_quote, f'[{at_text}]', 1)
                    result_entry['substitution'] = sub

                    # Find position of AT in substituted text
                    at_pos = sub.find(f'[{at_text}]')
                    if at_pos > 0:
                        # Get word immediately before [AT]
                        before = sub[:at_pos].rstrip()
                        prev_word = before.split()[-1].lower().strip('.,;:!?') if before.split() else ''

                        if prev_word in CONJUNCTIONS:
                            result_entry['orphaned_conjunction'] = True
                            orphaned_conj_count += 1

                        if prev_word in PREPOSITIONS:
                            result_entry['orphaned_preposition'] = True
                            orphaned_prep_count += 1

                    # Check capitalization at verse start
                    if clean_ult.startswith(clean_quote) and at_text and at_text[0].islower():
                        result_entry['capitalization_ok'] = False
                        cap_error_count += 1
                else:
                    # Case-insensitive fallback
                    idx = clean_ult.lower().find(clean_quote.lower())
                    if idx >= 0:
                        sub = clean_ult[:idx] + f'[{at_text}]' + clean_ult[idx + len(clean_quote):]
                        result_entry['substitution'] = sub

                        if idx > 0:
                            before = clean_ult[:idx].rstrip()
                            prev_word = before.split()[-1].lower().strip('.,;:!?') if before.split() else ''
                            if prev_word in CONJUNCTIONS:
                                result_entry['orphaned_conjunction'] = True
                                orphaned_conj_count += 1
                            if prev_word in PREPOSITIONS:
                                result_entry['orphaned_preposition'] = True
                                orphaned_prep_count += 1

                        if idx == 0 and at_text and at_text[0].islower():
                            result_entry['capitalization_ok'] = False
                            cap_error_count += 1

            results.append(result_entry)

    return {
        'test': 'at_fit',
        'total_checked': len(results),
        'orphaned_conjunctions': orphaned_conj_count,
        'orphaned_prepositions': orphaned_prep_count,
        'capitalization_errors': cap_error_count,
        'results': results,
    }

# ===========================================================================
# TEST 4: Comparison Against Published TNs
# ===========================================================================

def test_vs_published(published_tsv, hebrew_source_path, ult_usfm_path, chapter=None):
    """Compare old passive detection against published TN ground truth."""

    # Import old script
    old_script_dir = os.path.join(
        _project_root(), '.claude', 'skills', 'issue-identification',
        'scripts', 'detection', '.old'
    )
    sys.path.insert(0, old_script_dir)
    try:
        from detect_activepassive import find_passives_in_text as old_find_passives
    finally:
        sys.path.pop(0)

    # Load published TNs
    pub_rows = parse_published_tns(published_tsv, chapter=chapter)
    if not pub_rows:
        return {'test': 'vs_published', 'error': f'No published TN rows for chapter {chapter}', 'results': []}

    # Load Hebrew source for quote validation
    hebrew_verses = parse_hebrew_source(hebrew_source_path)

    # Load ULT for passive detection
    ult_verses = extract_ult_verses(ult_usfm_path)

    # Group published rows by chapter
    chapters_seen = set()
    for row in pub_rows:
        chapters_seen.add(row['chapter'])

    results_by_chapter = []

    for ch in sorted(chapters_seen, key=lambda x: int(x) if x.isdigit() else 0):
        ch_rows = [r for r in pub_rows if r['chapter'] == ch]

        # 1. Hebrew quote validation
        heb_quote_valid = 0
        heb_quote_invalid = 0
        for row in ch_rows:
            oq = row['orig_quote']
            if not oq:
                continue
            ref = f"{ch}:{row['verse']}"
            verse_text = hebrew_verses.get(ref, '')
            if not verse_text:
                continue
            # Split on spaces and check each word
            words = oq.split()
            all_valid = True
            for w in words:
                w_clean = w.strip()
                if w_clean == '&':  # separator for split quotes
                    continue
                if w_clean and not is_hebrew_substring(w_clean, verse_text):
                    all_valid = False
                    break
            if all_valid:
                heb_quote_valid += 1
            else:
                heb_quote_invalid += 1

        # 2. Published passive entries (ground truth)
        published_passives = {}  # verse -> [gl_quote, ...]
        for row in ch_rows:
            sr = row['support_ref']
            if 'figs-activepassive' in sr:
                v = row['verse']
                published_passives.setdefault(v, [])
                published_passives[v].append(row['gl_quote'])

        # 3. Run old passive detection on ULT for this chapter
        old_passives = {}  # verse -> [phrase, ...]
        for ref, text in ult_verses.items():
            ref_ch, ref_v = ref.split(':') if ':' in ref else (ref, '')
            if ref_ch != ch:
                continue
            detections = old_find_passives(text)
            if detections:
                old_passives[ref_v] = [d['phrase'] for d in detections]

        # 4. Calculate recall/precision
        all_verses = set(list(published_passives.keys()) + list(old_passives.keys()))
        true_positives = 0
        false_negatives = 0
        false_positives = 0

        for v in all_verses:
            pub_count = len(published_passives.get(v, []))
            old_count = len(old_passives.get(v, []))

            if pub_count > 0 and old_count > 0:
                true_positives += min(pub_count, old_count)
                if old_count < pub_count:
                    false_negatives += pub_count - old_count
                elif old_count > pub_count:
                    false_positives += old_count - pub_count
            elif pub_count > 0:
                false_negatives += pub_count
            elif old_count > 0:
                false_positives += old_count

        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0

        results_by_chapter.append({
            'chapter': int(ch) if ch.isdigit() else ch,
            'published_passive_count': sum(len(v) for v in published_passives.values()),
            'published_passives': {k: v for k, v in published_passives.items()},
            'old_script_passives': {k: v for k, v in old_passives.items()},
            'old_script_recall': round(recall, 3),
            'old_script_precision': round(precision, 3),
            'heb_quote_valid': heb_quote_valid,
            'heb_quote_invalid': heb_quote_invalid,
        })

    return {
        'test': 'vs_published',
        'chapters_tested': len(results_by_chapter),
        'results': results_by_chapter,
    }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ref_sort_key(ref):
    """Sort key for chapter:verse references."""
    parts = ref.split(':')
    try:
        ch = int(parts[0])
    except (ValueError, IndexError):
        ch = 0
    try:
        v = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        v = 0
    return (ch, v)

def _find_file(pattern_or_path, root=None):
    """Resolve a file path, trying as-is, then under root, then glob."""
    if os.path.exists(pattern_or_path):
        return pattern_or_path
    if root:
        candidate = os.path.join(root, pattern_or_path)
        if os.path.exists(candidate):
            return candidate
    matches = sorted(glob.glob(pattern_or_path))
    return matches[0] if matches else None

# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(all_results):
    """Print human-readable summary to stdout."""
    print("=" * 70)
    print("  Prompt-Over-Code Test Suite Results")
    print("=" * 70)
    print()

    for result in all_results:
        test_name = result.get('test', 'unknown')

        # Handle error results first
        if 'error' in result:
            name_map = {
                'hebrew_quotes': 'Hebrew Quote Extraction',
                'passive_detection': 'Passive Voice Detection',
                'at_fit': 'AT Fit Quality',
                'vs_published': 'Published TN Comparison',
            }
            label = name_map.get(test_name, test_name)
            print(f"--- {label} ---")
            print(f"  Error: {result['error']}")
            print()
            continue

        if test_name == 'hebrew_quotes':
            print("--- Hebrew Quote Extraction ---")
            total = result.get('total_items', 0)
            print(f"  Items tested:           {total}")
            print(f"  Old script success:     {result.get('old_success', 0)} / {total}"
                  f"  ({result.get('old_success_rate', 0):.1%})")
            print(f"  Old script failures:    {result.get('old_fail', 0)}")
            print(f"  New alignment coverage: {result.get('new_coverage', 0)} / {total}"
                  f"  ({result.get('new_coverage_rate', 0):.1%})")

            # Show failures
            failures = [r for r in result.get('results', []) if not r['old_valid']]
            if failures:
                print(f"\n  Old script failures ({len(failures)}):")
                for f in failures[:10]:
                    print(f"    {f['ref']}: {f['gl_quote']}")
                    if f['old_hebrew']:
                        print(f"      hebrew: {f['old_hebrew']} (invalid substring)")

            order_issues = [r for r in result.get('results', []) if r['old_valid'] and not r['old_order_correct']]
            if order_issues:
                print(f"\n  Old script order issues ({len(order_issues)}):")
                for f in order_issues[:10]:
                    print(f"    {f['ref']}: {f['gl_quote']}")

            print()

        elif test_name == 'passive_detection':
            print("--- Passive Voice Detection ---")
            total = result.get('total_verses', 0)
            print(f"  Verses tested:     {total}")
            print(f"  Full agreement:    {result.get('agreement_count', 0)} / {total}"
                  f"  ({result.get('agreement_rate', 0):.1%})")
            print(f"  Both found:        {result.get('both_count', 0)}")
            print(f"  Old-only:          {result.get('old_only_count', 0)}")
            print(f"  New-only:          {result.get('new_only_count', 0)}")

            disagreements = [r for r in result.get('results', []) if not r['match']]
            if disagreements:
                print(f"\n  Disagreements ({len(disagreements)}):")
                for d in disagreements[:15]:
                    print(f"    {d['verse']}:")
                    if d['old_only']:
                        print(f"      old-only: {d['old_only']}")
                    if d['new_only']:
                        print(f"      new-only: {d['new_only']}")
            print()

        elif test_name == 'at_fit':
            print("--- AT Fit Quality ---")
            print(f"  Items checked:            {result.get('total_checked', 0)}")
            print(f"  Orphaned conjunctions:    {result.get('orphaned_conjunctions', 0)}")
            print(f"  Orphaned prepositions:    {result.get('orphaned_prepositions', 0)}")
            print(f"  Capitalization errors:     {result.get('capitalization_errors', 0)}")

            issues = [r for r in result.get('results', [])
                      if r.get('orphaned_conjunction') or r.get('orphaned_preposition')
                      or not r.get('capitalization_ok')]
            if issues:
                print(f"\n  Flagged items ({len(issues)}):")
                for item in issues[:15]:
                    flags = []
                    if item.get('orphaned_conjunction'):
                        flags.append('conj')
                    if item.get('orphaned_preposition'):
                        flags.append('prep')
                    if not item.get('capitalization_ok'):
                        flags.append('cap')
                    print(f"    {item['ref']}: [{', '.join(flags)}] AT=\"{item['at']}\"")
                    if item.get('substitution'):
                        print(f"      -> {item['substitution'][:100]}")
            print()

        elif test_name == 'vs_published':
            print("--- Published TN Comparison ---")
            print(f"  Chapters tested: {result.get('chapters_tested', 0)}")
            for ch_result in result.get('results', []):
                ch = ch_result['chapter']
                pub_count = ch_result.get('published_passive_count', 0)
                recall = ch_result.get('old_script_recall', 0)
                precision = ch_result.get('old_script_precision', 0)
                hv = ch_result.get('heb_quote_valid', 0)
                hi = ch_result.get('heb_quote_invalid', 0)
                passive_info = f"  passives: recall={recall:.1%} precision={precision:.1%}" if pub_count > 0 else ""
                print(f"  Ch {ch:>3}: heb_quotes={hv} valid, {hi} invalid{passive_info}")
            print()

    print("=" * 70)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Test suite: Prompt-Over-Code vs Previous Workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--test', choices=['quote', 'passive', 'at-fit', 'published', 'all'],
                        default='all', help='Which test to run (default: all)')
    parser.add_argument('--chapter', type=int, default=78,
                        help='Chapter number (default: 78)')
    parser.add_argument('--aligned-usfm', help='Path to aligned USFM file')
    parser.add_argument('--issues', help='Path to issue TSV file')
    parser.add_argument('--notes', help='Path to output notes TSV')
    parser.add_argument('--prepared-json', help='Path to prepared_notes.json')
    parser.add_argument('--generated-json', help='Path to generated_notes.json')
    parser.add_argument('--report', default='/tmp/claude/poc_test_report.json',
                        help='Output JSON report path')
    parser.add_argument('--data-root', help='Override data root directory')
    parser.add_argument('--output-root', help='Override output root directory')

    args = parser.parse_args()

    data_root = args.data_root or _find_data_root()
    output_root = args.output_root or _find_output_root()
    chapter = args.chapter
    ch_str = f"{chapter:03d}"

    # Resolve common paths
    hebrew_source = os.path.join(data_root, 'data', 'hebrew_bible', '19-PSA.usfm')
    published_tns = os.path.join(data_root, 'data', 'published-tns', 'tn_PSA.tsv')
    published_ult = os.path.join(data_root, 'data', 'published_ult_english', '19-PSA.usfm')

    aligned_usfm = args.aligned_usfm or os.path.join(
        output_root, 'output', 'AI-ULT', 'PSA', f'PSA-{ch_str}-aligned.usfm')
    issues_tsv = args.issues or os.path.join(
        output_root, 'output', 'issues', 'PSA', f'PSA-{ch_str}.tsv')
    notes_tsv = args.notes

    prepared_json = args.prepared_json or '/tmp/claude/prepared_notes.json'
    generated_json = args.generated_json or '/tmp/claude/generated_notes.json'

    # Find notes TSV if not specified -- look in several places
    if not notes_tsv:
        candidates = [
            os.path.join(output_root, 'output', 'notes', f'PSA-{ch_str}.tsv'),
            os.path.join(output_root, 'output', 'notes', 'PSA', f'PSA-{ch_str}.tsv'),
        ]
        for c in candidates:
            if os.path.exists(c):
                notes_tsv = c
                break

    all_results = []
    tests_to_run = [args.test] if args.test != 'all' else ['quote', 'passive', 'at-fit', 'published']

    print(f"Data root:   {data_root}")
    print(f"Output root: {output_root}")
    print(f"Chapter:     {chapter}")
    print()

    # --- Test 1: Hebrew Quote Extraction ---
    if 'quote' in tests_to_run:
        print(f"Running Hebrew quote test...")
        if os.path.exists(aligned_usfm) and os.path.exists(issues_tsv):
            result = test_hebrew_quotes(aligned_usfm, issues_tsv, hebrew_source)
            all_results.append(result)
        else:
            missing = []
            if not os.path.exists(aligned_usfm):
                missing.append(f'aligned USFM: {aligned_usfm}')
            if not os.path.exists(issues_tsv):
                missing.append(f'issues TSV: {issues_tsv}')
            all_results.append({
                'test': 'hebrew_quotes',
                'error': f"Missing files: {'; '.join(missing)}",
                'results': [],
            })

    # --- Test 2: Passive Detection ---
    if 'passive' in tests_to_run:
        print(f"Running passive detection test...")
        ult_path = published_ult
        if os.path.exists(aligned_usfm):
            # Prefer aligned USFM for chapters we generated
            ult_path = aligned_usfm
        if os.path.exists(ult_path):
            ult_verses = extract_ult_verses(ult_path)
            result = test_passive_detection(ult_verses, chapter=chapter)
            all_results.append(result)
        else:
            all_results.append({
                'test': 'passive_detection',
                'error': f"ULT file not found: {ult_path}",
                'results': [],
            })

    # --- Test 3: AT Fit ---
    if 'at-fit' in tests_to_run:
        print(f"Running AT fit test...")
        # Try prepared+generated JSON first, then notes TSV
        has_json = (os.path.exists(prepared_json) and os.path.exists(generated_json))
        has_tsv = notes_tsv and os.path.exists(notes_tsv)

        if has_json or has_tsv:
            ult_verses = extract_ult_verses(published_ult) if os.path.exists(published_ult) else {}
            result = test_at_fit(
                notes_tsv,
                ult_verses=ult_verses,
                prepared_json=prepared_json if has_json else None,
                generated_json=generated_json if has_json else None,
            )
            all_results.append(result)
        else:
            all_results.append({
                'test': 'at_fit',
                'error': 'No notes TSV or prepared/generated JSON found',
                'results': [],
            })

    # --- Test 4: Published TN Comparison ---
    if 'published' in tests_to_run:
        print(f"Running published TN comparison...")
        if os.path.exists(published_tns) and os.path.exists(hebrew_source):
            result = test_vs_published(
                published_tns, hebrew_source, published_ult, chapter=chapter)
            all_results.append(result)
        else:
            missing = []
            if not os.path.exists(published_tns):
                missing.append(f'published TNs: {published_tns}')
            if not os.path.exists(hebrew_source):
                missing.append(f'Hebrew source: {hebrew_source}')
            all_results.append({
                'test': 'vs_published',
                'error': f"Missing files: {'; '.join(missing)}",
                'results': [],
            })

    # Print summary
    print()
    print_summary(all_results)

    # Write JSON report
    report_dir = os.path.dirname(args.report)
    if report_dir:
        os.makedirs(report_dir, exist_ok=True)
    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Full report written to: {args.report}")

if __name__ == '__main__':
    main()
