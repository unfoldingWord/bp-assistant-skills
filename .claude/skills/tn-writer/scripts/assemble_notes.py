#!/usr/bin/env python3
"""
Assemble a TN-ready TSV from prepared notes JSON and generated notes JSON.

Deterministic assembly: metadata comes from prepare_notes.py output,
note text comes from AI-generated keyed JSON. Matching by item ID
prevents row/note misalignment regardless of generation order.

Usage:
    python3 assemble_notes.py /tmp/claude/prepared_notes.json \
        /tmp/claude/generated_notes.json \
        --output output/notes/PSA-061.tsv
"""

import argparse
import json
import os
import random
import re
import string
import sys


def ref_sort_key(ref):
    """Sort references: 'front' first, then numerically by verse."""
    parts = ref.split(':')
    if len(parts) == 2 and parts[1] == 'front':
        return (int(parts[0]), -1)
    elif len(parts) == 2:
        try:
            return (int(parts[0]), int(parts[1].split('-')[0]))
        except ValueError:
            return (int(parts[0]), 9999)
    return (9999, 9999)


def intra_verse_sort_key(item):
    """Within a verse, sort by ULT position (first to last), then longest first.

    This produces note order matching reading order in the ULT, with
    containing phrases before their sub-phrases.
    """
    gl_quote = item.get('gl_quote', '')
    ult_verse = item.get('ult_verse', '')

    if not gl_quote or not ult_verse:
        return (9998, 0)

    # Find position of gl_quote in ULT verse (case-insensitive)
    pos = ult_verse.lower().find(gl_quote.lower())
    if pos < 0:
        # Try without curly braces
        clean_ult = re.sub(r'\{([^}]*)\}', r'\1', ult_verse)
        clean_quote = re.sub(r'\{([^}]*)\}', r'\1', gl_quote)
        pos = clean_ult.lower().find(clean_quote.lower())
    if pos < 0:
        pos = 9999

    # Negative length so longer phrases sort first
    return (pos, -len(gl_quote))


def generate_short_id():
    """Generate a 4-character ID (first char letter, rest alphanumeric)."""
    first = random.choice(string.ascii_lowercase)
    rest = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
    return first + rest


def main():
    parser = argparse.ArgumentParser(description='Assemble TN TSV from prepared + generated notes')
    parser.add_argument('prepared_json', help='Path to prepared_notes.json from prepare_notes.py')
    parser.add_argument('generated_json', help='Path to generated_notes.json (id -> note text)')
    parser.add_argument('--output', '-o', required=True, help='Output TSV path')
    args = parser.parse_args()

    with open(args.prepared_json) as f:
        prepared = json.load(f)

    with open(args.generated_json) as f:
        generated = json.load(f)

    items = prepared['items']
    intro_rows = prepared.get('intro_rows', [])
    missing = []
    rows = []

    for item in items:
        item_id = item['id']
        note_text = generated.get(item_id)

        if note_text is None:
            missing.append(item_id)
            continue

        # Build Quote column
        quote = item.get('orig_quote', '')
        if quote.startswith('QUOTE_NOT_FOUND:') and 'hebrew_front_words' in item:
            # Front items: match gl_quote to the right Hebrew word
            gl = item['gl_quote'].lower()
            for hw in item['hebrew_front_words']:
                lemma = hw.get('lemma', '').lower()
                # Simple heuristic matching
                if 'musician' in gl and hw['strong'].endswith('H5329'):
                    quote = hw['word']
                    break
                elif 'stringed' in gl and hw['strong'].endswith('H5058'):
                    quote = hw['word']
                    break
                elif 'david' in gl and hw['strong'].endswith('H1732'):
                    quote = hw['word']
                    break
            else:
                # Fallback: use first unmatched word
                quote = item['hebrew_front_words'][0]['word'] if item['hebrew_front_words'] else quote

        ref = item['reference']
        sref = f"rc://*/ta/man/translate/{item['sref']}"

        rows.append({
            'reference': ref,
            'id': item_id,
            'tags': '',
            'support_reference': sref,
            'quote': quote,
            'occurrence': '1',
            'note': note_text.strip(),
            'ref_key': ref_sort_key(ref),
            'verse_key': intra_verse_sort_key(item)
        })

    # Sort by reference, then within each verse by ULT position (first to last, longest first)
    rows.sort(key=lambda r: (r['ref_key'], r['verse_key']))

    # Write TSV
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    intro_count = 0
    with open(args.output, 'w', newline='') as f:
        f.write('Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote\n')

        # Write intro rows first (passthrough, no AI processing)
        for intro in intro_rows:
            intro_id = generate_short_id()
            # Use the reference from the source TSV (e.g. "78:intro"),
            # NOT "front:intro" which is the book-level intro slot
            intro_ref = intro.get('reference', 'front:intro')
            # Intro content must be a single TSV line with literal \n for newlines
            intro_content = intro.get('content', '')
            intro_content = intro_content.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
            f.write('\t'.join([
                intro_ref,
                intro_id,
                '',
                '',
                '',
                '0',
                intro_content
            ]) + '\n')
            intro_count += 1

        for row in rows:
            f.write('\t'.join([
                row['reference'],
                row['id'],
                row['tags'],
                row['support_reference'],
                row['quote'],
                row['occurrence'],
                row['note']
            ]) + '\n')

    total = len(rows) + intro_count
    print(f"Wrote {total} rows to {args.output} ({intro_count} intro, {len(rows)} notes)")
    if missing:
        print(f"WARNING: {len(missing)} items missing from generated notes: {', '.join(missing)}", file=sys.stderr)

    return 0 if not missing else 1


if __name__ == '__main__':
    sys.exit(main())
