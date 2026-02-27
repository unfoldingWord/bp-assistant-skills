#!/usr/bin/env python3
"""
Reverse-lookup: given filled orig_quote (Hebrew), find the corresponding
ULT English span using alignment data and update gl_quote in prepared_notes.json.

For each item where orig_quote is filled:
1. Split orig_quote into Hebrew words
2. Find alignment entries whose 'heb' matches any of those words
3. Collect the English words from those entries
4. Locate the contiguous span in the ULT verse (including {supply} words)
5. Update gl_quote to that span

Usage:
    python3 resolve_gl_quotes.py /tmp/claude/prepared_notes.json \
        /tmp/claude/alignment_data.json
"""

import argparse
import json
import re
import sys


def strip_cantillation(word):
    """Strip cantillation marks and joiners for matching purposes."""
    # Remove Unicode cantillation marks (0x0591-0x05AF) and joiners (0x2060, 0x05BE)
    return re.sub(r'[\u0591-\u05AF\u2060\u05BE⁠]', '', word)


def find_english_for_hebrew(hebrew_words, alignment_data, verse_ref):
    """Find English words aligned to the given Hebrew words.

    Groups alignment entries by heb_pos. Uses exact Hebrew matching first
    to disambiguate words that differ only in cantillation marks (e.g.,
    two occurrences of the same root in one verse). Falls back to
    cantillation-stripped matching only for words with no exact match.

    Returns list of English words in alignment-data order.
    """
    if verse_ref not in alignment_data:
        return []

    verse_alignments = alignment_data[verse_ref]

    # Group alignment entries by heb_pos (each position = one Hebrew word)
    from collections import defaultdict
    heb_groups = defaultdict(list)
    for entry in verse_alignments:
        heb_groups[entry['heb_pos']].append(entry)

    # Build group info: {heb_pos: (exact_heb, stripped_heb, [eng_words])}
    group_info = {}
    for pos, entries in heb_groups.items():
        exact_heb = entries[0]['heb']
        stripped_heb = strip_cantillation(exact_heb)
        eng_words = [e['eng'] for e in entries]
        group_info[pos] = (exact_heb, stripped_heb, eng_words)

    used_positions = set()
    matched_english = []

    for heb_word in hebrew_words:
        # Try exact match first (preserves cantillation disambiguation)
        found = False
        for pos in sorted(group_info.keys()):
            if pos in used_positions:
                continue
            exact, stripped, engs = group_info[pos]
            if exact == heb_word:
                matched_english.extend(engs)
                used_positions.add(pos)
                found = True
                break

        if not found:
            # Fallback: stripped match (first unused group with same root)
            target_stripped = strip_cantillation(heb_word)
            for pos in sorted(group_info.keys()):
                if pos in used_positions:
                    continue
                exact, stripped, engs = group_info[pos]
                if stripped == target_stripped:
                    matched_english.extend(engs)
                    used_positions.add(pos)
                    found = True
                    break

    return matched_english


def find_contiguous_span(ult_verse, english_words):
    """Find the contiguous span in the ULT verse covering all english_words.

    Includes any {supply} words that fall between matched words.
    Returns the span text, or None if not found.
    """
    if not english_words or not ult_verse:
        return None

    # Tokenize the ULT verse preserving {supply} tokens
    # Split on whitespace but keep track of positions
    tokens = ult_verse.split()
    if not tokens:
        return None

    # For each token, strip punctuation and quote marks for matching
    def clean_token(t):
        return re.sub(r'[{},;:.!?\u0027\u0022\u2018\u2019\u201C\u201D\u2014\u2013]', '', t)

    # Find positions of all matched english words in the token list
    target_words = set(english_words)
    matched_positions = []

    for i, token in enumerate(tokens):
        cleaned = clean_token(token)
        if cleaned in target_words:
            matched_positions.append(i)

    if not matched_positions:
        return None

    # Take the contiguous span from first to last matched position
    start = min(matched_positions)
    end = max(matched_positions)

    # Extend start backwards to include adjacent {supply} words
    while start > 0 and re.match(r'^\{.*\}', tokens[start - 1]):
        start -= 1

    span_tokens = tokens[start:end + 1]
    return ' '.join(span_tokens)


def main():
    parser = argparse.ArgumentParser(
        description='Reverse-lookup Hebrew orig_quote to ULT English gl_quote'
    )
    parser.add_argument('prepared_json', help='Path to prepared_notes.json')
    parser.add_argument('alignment_json', help='Path to alignment_data.json')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show changes without writing')

    args = parser.parse_args()

    with open(args.prepared_json, 'r', encoding='utf-8') as f:
        prepared = json.load(f)

    with open(args.alignment_json, 'r', encoding='utf-8') as f:
        alignment_data = json.load(f)

    updated = 0
    skipped = 0
    errors = 0

    for item in prepared['items']:
        orig_quote = item.get('orig_quote', '')
        if not orig_quote:
            skipped += 1
            continue

        ref = item.get('reference', '')
        ult_verse = item.get('ult_verse', '')

        if not ult_verse:
            skipped += 1
            continue

        # Split Hebrew quote into words
        hebrew_words = orig_quote.split()

        # Find English words from alignment
        english_words = find_english_for_hebrew(hebrew_words, alignment_data, ref)

        if not english_words:
            print(f"  WARNING: {ref} ({item.get('id', '?')}): no alignment match "
                  f"for Hebrew: {orig_quote}", file=sys.stderr)
            errors += 1
            continue

        # Find contiguous span in ULT verse
        span = find_contiguous_span(ult_verse, english_words)

        if not span:
            print(f"  WARNING: {ref} ({item.get('id', '?')}): could not locate "
                  f"English span in ULT for: {english_words}", file=sys.stderr)
            errors += 1
            continue

        old_gl = item.get('gl_quote', '')
        if span != old_gl:
            print(f"  {ref} ({item.get('id', '?')}): {old_gl!r} -> {span!r}",
                  file=sys.stderr)
            item['gl_quote'] = span
            updated += 1

    print(f"\nResolved: {updated} updated, {skipped} skipped (no orig_quote), "
          f"{errors} errors", file=sys.stderr)

    if not args.dry_run:
        with open(args.prepared_json, 'w', encoding='utf-8') as f:
            json.dump(prepared, f, indent=2, ensure_ascii=False)
        print(f"Wrote updated prepared_notes.json", file=sys.stderr)


if __name__ == '__main__':
    main()
