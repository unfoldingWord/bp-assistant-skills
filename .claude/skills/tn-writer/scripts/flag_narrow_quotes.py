#!/usr/bin/env python3
"""
Flag items in prepared_notes.json where gl_quote is likely too narrow
for a seamless AT substitution.

Heuristics:
  - Single-word gl_quote
  - Pronoun gl_quote (he, she, they, it, my, his, her, their, we, you)
  - figs-abstractnouns with single-word quote (usually inside a phrase)
  - figs-activepassive with single-word quote (participle without object)

Outputs flagged items with ID, reference, gl_quote, sref, and ULT verse
so the note writer can anticipate which ATs will need wider boundaries.

Usage:
    python3 flag_narrow_quotes.py /tmp/claude/prepared_notes.json
"""

import argparse
import json
import sys

PRONOUNS = {
    'he', 'she', 'they', 'it', 'we', 'you',
    'him', 'her', 'them', 'us',
    'my', 'his', 'her', 'their', 'our', 'your', 'its',
    'mine', 'hers', 'theirs', 'ours', 'yours',
    'i', 'me', 'myself', 'himself', 'herself', 'itself',
    'themselves', 'ourselves', 'yourself', 'yourselves',
}

# Issue types where single-word quotes are especially likely to be too narrow
NARROW_PRONE_SREFS = {
    'figs-abstractnouns',
    'figs-activepassive',
}


def is_narrow(item):
    """Return a reason string if the gl_quote looks too narrow, else None."""
    gl = item.get('gl_quote', '').strip()
    if not gl:
        return None
    if not item.get('needs_at', False):
        return None

    words = gl.split()
    sref = item.get('sref', '')

    # Single-word quote
    if len(words) == 1:
        word_lower = words[0].lower().strip('.,;:!?')
        if word_lower in PRONOUNS:
            return f"pronoun-only quote ({gl})"
        if sref in NARROW_PRONE_SREFS:
            return f"single-word {sref} ({gl})"
        return f"single-word quote ({gl})"

    # Two-word pronoun-led quote (e.g. "my distress")
    if len(words) == 2:
        first_lower = words[0].lower().strip('.,;:!?')
        if first_lower in PRONOUNS:
            return f"pronoun + noun ({gl})"

    return None


def main():
    parser = argparse.ArgumentParser(description='Flag narrow gl_quotes')
    parser.add_argument('prepared_json', help='Path to prepared_notes.json')
    args = parser.parse_args()

    with open(args.prepared_json) as f:
        data = json.load(f)

    flagged = []
    for item in data.get('items', []):
        reason = is_narrow(item)
        if reason:
            flagged.append((item, reason))

    if not flagged:
        print("No narrow quotes flagged.")
        return 0

    print(f"Flagged {len(flagged)} item(s) with potentially narrow gl_quotes:\n")
    for item, reason in flagged:
        print(f"  {item['id']}  {item['reference']}  [{item['sref']}]")
        print(f"    gl_quote: {item['gl_quote']}")
        print(f"    reason:   {reason}")
        ult = item.get('ult_verse', '')
        if ult:
            print(f"    ULT:      {ult}")
        print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
