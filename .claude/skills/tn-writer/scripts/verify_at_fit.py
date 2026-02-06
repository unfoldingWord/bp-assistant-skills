#!/usr/bin/env python3
"""
Verify that alternate translations fit seamlessly into ULT verses.

For each generated note containing an AT (text in [square brackets]):
1. Extract the AT text
2. Find the gl_quote in the ULT verse
3. Substitute the AT for the gl_quote
4. Print the result for review

Shows all substitutions so the AI can review them. Flags hard errors
(gl_quote not found in verse) separately.

Usage:
    python3 verify_at_fit.py /tmp/claude/prepared_notes.json \
        /tmp/claude/generated_notes.json
"""

import argparse
import json
import re
import sys


def extract_ats(note_text):
    """Extract alternate translation texts from [square brackets]."""
    return re.findall(r'\[([^\]]+)\]', note_text)


def strip_braces(text):
    """Remove {curly braces} used for implied words in ULT."""
    return re.sub(r'\{([^}]*)\}', r'\1', text)


def substitute(ult_verse, gl_quote, at_text):
    """Try to substitute AT for gl_quote in ULT verse.

    Returns (result_string, success).
    """
    clean_ult = strip_braces(ult_verse)
    clean_quote = strip_braces(gl_quote)

    if not clean_quote or not clean_ult:
        return None, False

    # Direct match
    if clean_quote in clean_ult:
        return clean_ult.replace(clean_quote, at_text, 1), True

    # Case-insensitive match
    idx = clean_ult.lower().find(clean_quote.lower())
    if idx >= 0:
        return clean_ult[:idx] + at_text + clean_ult[idx + len(clean_quote):], True

    return None, False


def main():
    parser = argparse.ArgumentParser(description='Verify AT fit in ULT verses')
    parser.add_argument('prepared_json', help='Path to prepared_notes.json')
    parser.add_argument('generated_json', help='Path to generated_notes.json')
    args = parser.parse_args()

    with open(args.prepared_json) as f:
        prepared = json.load(f)

    with open(args.generated_json) as f:
        generated = json.load(f)

    items_by_id = {item['id']: item for item in prepared['items']}

    errors = []
    checked = 0

    for item_id, note_text in generated.items():
        item = items_by_id.get(item_id)
        if not item:
            errors.append(f"  {item_id}: item ID not found in prepared JSON")
            continue

        ats = extract_ats(note_text)
        if not ats:
            continue

        gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')
        ult_verse = item.get('ult_verse', '')
        ref = item.get('reference', '???')
        sref = item.get('sref', '???')

        if not ult_verse or not gl_quote:
            continue

        checked += 1

        for at_text in ats:
            result, success = substitute(ult_verse, gl_quote, at_text)

            if success:
                print(f"{ref} ({item_id}) [{sref}]")
                print(f"  [{at_text}]")
                print(f"  -> {result}")
                print()
            else:
                errors.append(f"  {ref} ({item_id}) [{sref}]: gl_quote not found in ULT")
                errors.append(f"    gl_quote: {gl_quote}")
                errors.append(f"    ULT: {strip_braces(ult_verse)}")
                errors.append(f"    AT: [{at_text}]")

    print(f"--- Checked {checked} notes with alternate translations ---")

    if errors:
        print(f"\nERRORS ({len([e for e in errors if not e.startswith('    ')])}):")
        for e in errors:
            print(e)
        return 1
    else:
        print("No errors.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
