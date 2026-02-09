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
import json
import os
import re
import sys


def parse_aligned_usfm(usfm_path):
    """Parse aligned USFM into per-verse word-to-Hebrew mappings.

    Returns dict: { "chapter:verse" -> [ (english_word, hebrew_content, strong) ] }

    Each entry is an English word with its aligned Hebrew x-content and
    Strong's number from the enclosing zaln-s milestone.
    """
    with open(usfm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    verses = {}
    current_chapter = None
    current_verse = None
    current_words = []

    # Process line by line
    for line in content.split('\n'):
        # Chapter marker
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            # Save previous verse
            if current_chapter and current_verse and current_words:
                key = f"{current_chapter}:{current_verse}"
                verses[key] = current_words
            current_chapter = ch_match.group(1)
            current_verse = None
            current_words = []
            continue

        # Verse marker
        v_match = re.match(r'.*\\v\s+(\d+[-\d]*|front)\s*(.*)', line)
        if v_match and current_chapter:
            # Save previous verse
            if current_verse and current_words:
                key = f"{current_chapter}:{current_verse}"
                verses[key] = current_words
            current_verse = v_match.group(1)
            current_words = []
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
        active_milestones = []

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
                active_milestones.append((x_content, x_strong))
                pos += zaln_match.end()
                continue

            # Look for \w word marker
            w_match = re.match(r'\\w\s+([^|\\]+)\|[^\\]*\\w\*', line_rest[pos:])
            if w_match:
                eng_word = w_match.group(1).strip()
                # Use the innermost (last) active milestone
                if active_milestones:
                    hebrew, strong = active_milestones[-1]
                    current_words.append((eng_word, hebrew, strong))
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
        verses[key] = current_words

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
        verse_clean = [clean_word(w[0]) for w in verse_words]

        # Find the best matching window in the verse
        best_start, best_end = find_matching_span(clean_tokens, verse_clean)

        if best_start is None:
            print(f"  WARNING: Could not match gl_quote '{gl_quote}' in {ref}",
                  file=sys.stderr)
            results.append({'Quote': '', 'GLQuote': gl_quote})
            continue

        # Collect Hebrew words from the matched span
        matched_words = verse_words[best_start:best_end]
        hebrew_words = []
        seen_hebrew = set()
        for eng, hebrew, strong in matched_words:
            if hebrew and hebrew not in seen_hebrew:
                hebrew_words.append(hebrew)
                seen_hebrew.add(hebrew)

        # Build roundtripped English from the matched span
        roundtripped_english = ' '.join(w[0] for w in matched_words)

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

    # Try fuzzy: allow one missing/extra token
    best_score = 0
    best_span = (None, None)

    # Try windows of size n_query-1 to n_query+1
    for window_size in [n_query, n_query + 1, n_query - 1, n_query + 2]:
        if window_size < 1 or window_size > n_verse:
            continue
        for start in range(n_verse - window_size + 1):
            window = verse_tokens[start:start + window_size]
            score = _match_score(query_tokens, window)
            if score > best_score:
                best_score = score
                best_span = (start, start + window_size)

    # Require at least 70% match
    if best_score >= 0.7:
        return best_span

    return None, None


def _match_score(query, window):
    """Score how well query tokens match window tokens (0-1 scale)."""
    if not query:
        return 0

    matched = 0
    window_set = set(window)
    for qt in query:
        if qt in window_set:
            matched += 1

    return matched / len(query)


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
