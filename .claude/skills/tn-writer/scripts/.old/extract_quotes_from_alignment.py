#!/usr/bin/env python3
"""
Extract Hebrew quotes from aligned USFM for translation note assembly.

Instead of roundtripping through lang_convert.js (which checks against
published Door43 master ULT), this script reads our own aligned ULT and
extracts Hebrew x-content directly from zaln-s milestones. This eliminates
QUOTE_NOT_FOUND errors caused by differences between AI-generated ULT and
published ULT.

Usage as a library:
    from extract_quotes_from_alignment import extract_quotes
    results = extract_quotes(aligned_usfm_path, items)

Usage standalone:
    python3 extract_quotes_from_alignment.py aligned.usfm issues.tsv
"""

import argparse
from collections import Counter
import glob
import json
import os
import re
import sys
import unicodedata

COMMON_FUNCTION_WORDS = {
    'a', 'an', 'and', 'as', 'at', 'by', 'for', 'from', 'he', 'her', 'his',
    'in', 'is', 'it', 'its', 'of', 'on', 'or', 'our', 'she', 'that', 'the',
    'their', 'them', 'they', 'to', 'was', 'we', 'were', 'who', 'with', 'you',
    'your'
}


def _project_root():
    """Resolve project root from this script location."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # .../.claude/skills/tn-writer/scripts
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))


def _normalize_hebrew_token(token):
    """Normalize Hebrew token for robust matching across USFM variants."""
    if not token:
        return ''
    # Remove formatting controls often present in aligned text
    token = token.replace('\u2060', '').replace('\u200f', '').replace('\u200e', '')
    # Remove combining marks (niqqud/cantillation), keep base letters
    token = ''.join(
        ch for ch in unicodedata.normalize('NFD', token)
        if unicodedata.category(ch) != 'Mn'
    )
    # Keep Hebrew letters only (drop punctuation/maqaf/sof-pasuq/etc)
    token = ''.join(ch for ch in token if '\u05d0' <= ch <= '\u05ea')
    return token


def _find_hebrew_source_file(book_code):
    """Find data/hebrew_bible/*-BOOK.usfm."""
    if not book_code:
        return None
    hebrew_dir = os.path.join(_project_root(), 'data', 'hebrew_bible')
    pattern = os.path.join(hebrew_dir, f'*-{book_code.upper()}.usfm')
    matches = sorted(glob.glob(pattern))
    return matches[0] if matches else None


def _parse_hebrew_source_verses(usfm_path):
    """Parse Hebrew source USFM into verse word lists.

    Returns dict: { "chapter:verse" -> [word_record, ...] }
    where word_record has:
      - surface
      - norm
      - abs_idx
      - occurrence
      - occurrences
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
        verses.setdefault(key, [])

        # Extract Hebrew surface tokens from \w ...|...\w*
        for m in re.finditer(r'\\w\s+([^|\\]+)\|[^\\]*\\w\*', line):
            word_text = m.group(1).strip()
            if word_text:
                verses[key].append({
                    'surface': word_text,
                    'norm': _normalize_hebrew_token(word_text),
                })

    # Add absolute and occurrence-of-occurrences indices
    for ref, words in verses.items():
        totals = Counter(w['norm'] for w in words if w.get('norm'))
        running = Counter()
        for idx, w in enumerate(words):
            norm = w.get('norm', '')
            w['abs_idx'] = idx
            if norm:
                running[norm] += 1
                w['occurrence'] = running[norm]
                w['occurrences'] = totals[norm]
            else:
                w['occurrence'] = 0
                w['occurrences'] = 0

    return verses


def _reorder_by_hebrew_source(ref, hebrew_items, hebrew_source_verses):
    """Reorder extracted Hebrew items by source Hebrew verse order."""
    if not hebrew_items:
        return hebrew_items

    src_words = hebrew_source_verses.get(ref, [])
    if not src_words:
        return hebrew_items

    # Build lookup keyed by (normalized Hebrew token, occurrence index)
    by_norm_occ = {}
    by_norm = {}
    for sw in src_words:
        norm = sw.get('norm', '')
        occ = sw.get('occurrence', 0)
        abs_idx = sw.get('abs_idx', 10**9)
        if norm:
            by_norm_occ[(norm, occ)] = abs_idx
            by_norm.setdefault(norm, []).append(abs_idx)

    used_abs = set()
    for item in hebrew_items:
        src_idx = None
        norm = item.get('heb_norm', '')
        occ = item.get('heb_occurrence', 0)

        # First try exact (token + occurrence/occurrences) anchor
        if norm and occ:
            src_idx = by_norm_occ.get((norm, occ))
            if src_idx in used_abs:
                src_idx = None

        # Fallback: first unused source token with same normalized form
        if src_idx is None and norm:
            for idx in by_norm.get(norm, []):
                if idx not in used_abs:
                    src_idx = idx
                    break

        if src_idx is not None:
            used_abs.add(src_idx)
        item['src_abs_idx'] = src_idx

    # Source-matched words first in source order, then unmatched by Hebrew abs index
    hebrew_items.sort(
        key=lambda x: (0, x['src_abs_idx'], x['heb_abs_idx'])
        if x.get('src_abs_idx') is not None else (1, 10**9, x['heb_abs_idx'])
    )
    return hebrew_items


def parse_aligned_usfm(usfm_path):
    """Parse aligned USFM into per-verse word-to-Hebrew mappings.

    Returns dict: { "chapter:verse" -> [word_record, ...] }.
    Each word_record includes:
      - eng_word, eng_norm, eng_abs_idx, eng_occurrence, eng_occurrences
      - hebrew, heb_norm, heb_abs_idx, heb_occurrence, heb_occurrences
      - strong
    """
    with open(usfm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    verses = {}
    current_chapter = None
    current_verse = None
    current_words = []
    english_pos_counter = 0
    hebrew_pos_counter = 0
    active_milestones = []

    def _finalize_verse_words(words):
        """Attach occurrence-of-occurrences metadata for English and Hebrew."""
        eng_totals = Counter(w['eng_norm'] for w in words if w.get('eng_norm'))
        heb_totals = Counter(w['heb_norm'] for w in words if w.get('heb_norm'))
        eng_running = Counter()
        heb_running = Counter()

        for w in words:
            eng = w.get('eng_norm', '')
            heb = w.get('heb_norm', '')

            if eng:
                eng_running[eng] += 1
                w['eng_occurrence'] = eng_running[eng]
                w['eng_occurrences'] = eng_totals[eng]
            else:
                w['eng_occurrence'] = 0
                w['eng_occurrences'] = 0

            if heb:
                heb_running[heb] += 1
                w['heb_occurrence'] = heb_running[heb]
                w['heb_occurrences'] = heb_totals[heb]
            else:
                w['heb_occurrence'] = 0
                w['heb_occurrences'] = 0

        return words

    # Process line by line
    for line in content.split('\n'):
        # Chapter marker
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            # Save previous verse
            if current_chapter and current_verse and current_words:
                key = f"{current_chapter}:{current_verse}"
                verses[key] = _finalize_verse_words(current_words)
            current_chapter = ch_match.group(1)
            current_verse = None
            current_words = []
            english_pos_counter = 0
            hebrew_pos_counter = 0
            active_milestones = []
            continue

        # Verse marker
        v_match = re.match(r'.*\\v\s+(\d+[-\d]*|front)\s*(.*)', line)
        if v_match and current_chapter:
            # Save previous verse
            if current_verse and current_words:
                key = f"{current_chapter}:{current_verse}"
                verses[key] = _finalize_verse_words(current_words)
            current_verse = v_match.group(1)
            current_words = []
            english_pos_counter = 0
            hebrew_pos_counter = 0
            active_milestones = []
            # Continue processing the rest of the line (don't skip it)
            line_rest = line
        else:
            line_rest = line

        if current_verse is None:
            continue

        # Find all zaln-s + \w pairs in this line
        # Pattern: zaln-s milestone(s) followed by \w word\w*
        # Handle nested milestones (multiple zaln-s before one \w)
        #
        # Strategy: walk the line and track active zaln-s milestones
        pos = 0

        while pos < len(line_rest):
            # Look for zaln-s milestone
            zaln_match = re.match(
                r'\\zaln-s\s+\|([^\\]*?)\\?\*',
                line_rest[pos:]
            )
            if zaln_match:
                attrs = zaln_match.group(1)
                x_content = ''
                x_strong = ''
                cm = re.search(r'x-content="([^"]*)"', attrs)
                if cm:
                    x_content = cm.group(1)
                sm = re.search(r'x-strong="([^"]*)"', attrs)
                if sm:
                    x_strong = sm.group(1)
                x_pos = hebrew_pos_counter
                hebrew_pos_counter += 1
                active_milestones.append((x_content, x_strong, x_pos))
                pos += zaln_match.end()
                continue

            # Look for \w word marker
            w_match = re.match(r'\\w\s+([^|\\]+)\|[^\\]*\\w\*', line_rest[pos:])
            if w_match:
                eng_word = w_match.group(1).strip()
                # Use the innermost (last) active milestone
                if active_milestones:
                    hebrew, strong, hpos = active_milestones[-1]
                    current_words.append({
                        'eng_word': eng_word,
                        'eng_norm': clean_word(eng_word),
                        'eng_abs_idx': english_pos_counter,
                        'hebrew': hebrew,
                        'heb_norm': _normalize_hebrew_token(hebrew),
                        'heb_abs_idx': hpos,
                        'strong': strong,
                    })
                english_pos_counter += 1
                pos += w_match.end()
                continue

            # Look for zaln-e (end milestone) - pop one milestone
            zaln_e_match = re.match(r'\\zaln-e\\?\*', line_rest[pos:])
            if zaln_e_match:
                if active_milestones:
                    active_milestones.pop()
                pos += zaln_e_match.end()
                continue

            # Skip any other character
            pos += 1

    # Save last verse
    if current_chapter and current_verse and current_words:
        key = f"{current_chapter}:{current_verse}"
        verses[key] = _finalize_verse_words(current_words)

    return verses


def clean_word(word):
    """Clean an English word for comparison: lowercase, strip braces/punctuation."""
    word = re.sub(r'[{}]', '', word)
    word = re.sub(r'[.,;:!?\'"()…\-]', '', word)
    return word.lower().strip()


def extract_quotes(aligned_usfm_path, items):
    """Extract Hebrew quotes for a list of issue items.

    Args:
        aligned_usfm_path: Path to aligned USFM file
        items: List of dicts with 'ref' and 'gl_quote' keys

    Returns:
        List of dicts with 'Quote' (Hebrew) and 'GLQuote' (roundtripped English)
        for each input item, parallel to the items list.
    """
    verses = parse_aligned_usfm(aligned_usfm_path)
    book_code = ''
    if items:
        book_code = (items[0].get('book') or '').upper()
    hebrew_source_file = _find_hebrew_source_file(book_code)
    hebrew_source_verses = _parse_hebrew_source_verses(hebrew_source_file)
    results = []

    for item in items:
        ref = item['ref']
        gl_quote = item['gl_quote'].strip()

        if not gl_quote:
            results.append({'Quote': '', 'GLQuote': ''})
            continue

        verse_words = verses.get(ref, [])
        if not verse_words:
            print(f"  WARNING: No aligned words for {ref}", file=sys.stderr)
            results.append({'Quote': '', 'GLQuote': gl_quote})
            continue

        # Tokenize the gl_quote for matching
        quote_tokens = re.findall(r'[{}\w]+(?:[-\'][{}\w]+)*', gl_quote)
        clean_tokens = [clean_word(t) for t in quote_tokens]

        # Build clean versions of verse words for matching
        verse_clean = [w['eng_norm'] for w in verse_words]

        # Find the best matching window in the verse
        best_start, best_end = find_matching_span(clean_tokens, verse_clean)

        if best_start is None:
            print(f"  WARNING: Could not match gl_quote '{gl_quote}' in {ref}",
                  file=sys.stderr)
            results.append({'Quote': '', 'GLQuote': gl_quote})
            continue

        # Collect Hebrew words from the matched span
        matched_words = verse_words[best_start:best_end]
        hebrew_items = []
        seen_positions = set()
        for w in matched_words:
            hebrew = w['hebrew']
            hpos = w['heb_abs_idx']
            if hebrew and hpos not in seen_positions:
                hebrew_items.append({
                    'hebrew': hebrew,
                    'heb_norm': w['heb_norm'],
                    'heb_abs_idx': hpos,
                    'heb_occurrence': w['heb_occurrence'],
                    'heb_occurrences': w['heb_occurrences'],
                })
                seen_positions.add(hpos)

        # First keep alignment order for stability...
        hebrew_items.sort(key=lambda x: x['heb_abs_idx'])
        # ...then reorder by actual Hebrew source verse sequence when available.
        hebrew_items = _reorder_by_hebrew_source(ref, hebrew_items, hebrew_source_verses)
        hebrew_words = [h['hebrew'] for h in hebrew_items]

        # Build roundtripped English from the matched span
        roundtripped_english = ' '.join(w['eng_word'] for w in matched_words)

        # Join Hebrew words with space (standard format for Quote column)
        orig_quote = ' '.join(hebrew_words)

        results.append({
            'Quote': orig_quote,
            'GLQuote': roundtripped_english,
        })

    return results


def find_matching_span(query_tokens, verse_tokens):
    """Find the span in verse_tokens that best matches query_tokens.

    Uses sliding window with fuzzy matching to handle minor differences.

    Returns (start_index, end_index) or (None, None) if no match.
    """
    if not query_tokens or not verse_tokens:
        return None, None

    n_query = len(query_tokens)
    n_verse = len(verse_tokens)

    # Try exact substring match first
    for start in range(n_verse - n_query + 1):
        window = verse_tokens[start:start + n_query]
        if window == query_tokens:
            return start, start + n_query

    # Try fuzzy with conservative confidence checks.
    best_score = 0
    best_span = (None, None)
    non_function_query = [t for t in query_tokens if t and t not in COMMON_FUNCTION_WORDS]

    # Try windows of size n_query-1 to n_query+1
    for window_size in [n_query, n_query + 1, n_query - 1, n_query + 2]:
        if window_size < 1 or window_size > n_verse:
            continue
        for start in range(n_verse - window_size + 1):
            window = verse_tokens[start:start + window_size]
            window_set = set(window)
            # Require all content tokens from query to appear in the candidate window.
            if non_function_query and not all(t in window_set for t in non_function_query):
                continue
            score = _match_score(query_tokens, window)
            occ_score = _occurrence_profile_score(query_tokens, window)
            score = (0.85 * score) + (0.15 * occ_score)
            if score > best_score:
                best_score = score
                best_span = (start, start + window_size)

    # Require high confidence to avoid cross-clause drift.
    if best_score >= 0.9:
        return best_span

    return None, None


def _match_score(query, window):
    """Score how well query tokens match window tokens (0-1 scale)."""
    if not query:
        return 0

    # Order-sensitive longest-common-subsequence match.
    lcs_len = _lcs_length(query, window)
    recall = lcs_len / len(query)
    precision = lcs_len / len(window) if window else 0

    # Slightly favor tighter windows when recall is similar.
    return (0.7 * recall) + (0.3 * precision)


def _lcs_length(a, b):
    """Return LCS length for two token lists."""
    if not a or not b:
        return 0

    rows = len(a) + 1
    cols = len(b) + 1
    dp = [[0] * cols for _ in range(rows)]
    for i in range(1, rows):
        ai = a[i - 1]
        for j in range(1, cols):
            if ai == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[-1][-1]


def _occurrence_profile_score(query, window):
    """Score overlap on token occurrence/occurrences profiles."""
    if not query or not window:
        return 0

    q_profile = set(_token_occurrence_profile(query))
    w_profile = set(_token_occurrence_profile(window))
    if not q_profile:
        return 0
    overlap = len(q_profile.intersection(w_profile))
    return overlap / len(q_profile)


def _token_occurrence_profile(tokens):
    """Return [(token, occurrence, occurrences), ...] for token list."""
    totals = Counter(tokens)
    running = Counter()
    profile = []
    for t in tokens:
        running[t] += 1
        profile.append((t, running[t], totals[t]))
    return profile


def main():
    parser = argparse.ArgumentParser(
        description='Extract Hebrew quotes from aligned USFM for TN items.'
    )
    parser.add_argument('aligned_usfm', help='Path to aligned USFM file')
    parser.add_argument('input_tsv', help='Input issue TSV file')
    parser.add_argument('--output', '-o', help='Output JSON file (default: stdout)')

    args = parser.parse_args()

    # Parse items from TSV (same format as prepare_notes.py)
    items = []
    with open(args.input_tsv, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            cols = line.split('\t')
            while len(cols) < 7:
                cols.append('')
            if line_num == 1 and cols[0].lower() == 'book':
                continue
            if ':intro' in cols[1]:
                continue
            items.append({
                'ref': cols[1].strip(),
                'gl_quote': cols[3].strip(),
            })

    results = extract_quotes(args.aligned_usfm, items)

    # Combine for output
    output = []
    for item, result in zip(items, results):
        output.append({
            'reference': item['ref'],
            'gl_quote': item['gl_quote'],
            'orig_quote': result['Quote'],
            'gl_quote_roundtripped': result['GLQuote'],
        })

    output_json = json.dumps(output, indent=2, ensure_ascii=False)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"Wrote {len(output)} results to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == '__main__':
    main()
