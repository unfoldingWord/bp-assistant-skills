#!/usr/bin/env python3
"""
Validate bracketed words in aligned ULT against Hebrew prefix Strong's numbers.

In aligned ULT, words in {curly braces} are implied (not directly in Hebrew).
But sometimes a word like "in" IS in the Hebrew as a prefix (bet preposition,
Strong's "b:..."). Bracketing such words is an error -- they aren't implied,
they're translated from the prefix.

This script cross-references {word} entries against their aligned Strong's
number to flag incorrectly bracketed words.

Usage:
    python3 validate_ult_brackets.py output/AI-ULT/PSA-078-aligned.usfm

Output: list of flagged entries with verse ref, word, Strong's, and fix.
Exit code: 0 if no issues, 1 if issues found.
"""

import argparse
import os
import re
import sys

# Hebrew prefix -> expected English translations
# When a Strong's number has one of these prefixes and the bracketed word
# matches, the brackets should be removed (the word comes from the prefix).
PREFIX_TRANSLATIONS = {
    'b': ['in', 'by', 'with', 'at', 'among', 'on', 'against', 'through',
           'when', 'while'],
    'd': ['the'],
    'c': ['and', 'but', 'or', 'then', 'so', 'now', 'yet'],
    'k': ['like', 'as'],
    'l': ['to', 'for', 'of', 'belonging'],
    'm': ['from', 'out', 'than'],
}


def parse_aligned_usfm_brackets(usfm_path):
    """Parse aligned USFM and find all bracketed words with their alignments.

    Returns list of dicts:
        [{verse_ref, word, strong, line_num}, ...]
    for every {word} found inside a zaln-s milestone.
    """
    with open(usfm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    findings = []
    current_chapter = None
    current_verse = None

    for line_num, line in enumerate(content.split('\n'), start=1):
        # Chapter marker
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            current_chapter = ch_match.group(1)
            current_verse = None
            continue

        # Verse marker
        v_match = re.search(r'\\v\s+(\d+[-\d]*|front)', line)
        if v_match and current_chapter:
            current_verse = v_match.group(1)

        if current_verse is None:
            continue

        # Walk the line looking for zaln-s milestones followed by \w markers
        pos = 0
        active_strong = None

        while pos < len(line):
            # zaln-s milestone
            zaln_match = re.match(
                r'\\zaln-s\s+\|([^\\]*?)\\?\*',
                line[pos:]
            )
            if zaln_match:
                attrs = zaln_match.group(1)
                sm = re.search(r'x-strong="([^"]*)"', attrs)
                if sm:
                    active_strong = sm.group(1)
                pos += zaln_match.end()
                continue

            # \w word marker -- check if word is bracketed
            w_match = re.match(r'\\w\s+([^|\\]+)\|[^\\]*\\w\*', line[pos:])
            if w_match:
                word = w_match.group(1).strip()
                if word.startswith('{') and word.endswith('}') and active_strong:
                    findings.append({
                        'verse_ref': f"{current_chapter}:{current_verse}",
                        'word': word,
                        'strong': active_strong,
                        'line_num': line_num,
                    })
                pos += w_match.end()
                continue

            # zaln-e milestone
            zaln_e_match = re.match(r'\\zaln-e\\?\*', line[pos:])
            if zaln_e_match:
                active_strong = None
                pos += zaln_e_match.end()
                continue

            pos += 1

    return findings


def check_bracket_errors(findings):
    """Check each bracketed word against its Strong's prefix.

    Returns list of flagged items (subset of findings with added 'prefix' key).
    """
    flagged = []

    for item in findings:
        strong = item['strong']
        word_clean = item['word'].strip('{}').lower()

        # Check if Strong's has a prefix (e.g. "b:H6951" -> prefix "b")
        prefix_match = re.match(r'^([a-z]):(.+)', strong)
        if not prefix_match:
            continue

        prefix = prefix_match.group(1)
        expected_words = PREFIX_TRANSLATIONS.get(prefix, [])

        if word_clean in expected_words:
            item['prefix'] = prefix
            item['fix'] = f"Remove brackets: {item['word']} -> {word_clean}"
            flagged.append(item)

    return flagged


def main():
    parser = argparse.ArgumentParser(
        description='Validate bracketed words in aligned ULT against Hebrew prefixes.'
    )
    parser.add_argument('aligned_usfm', help='Path to aligned ULT USFM file')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if not os.path.exists(args.aligned_usfm):
        print(f"ERROR: File not found: {args.aligned_usfm}", file=sys.stderr)
        sys.exit(2)

    findings = parse_aligned_usfm_brackets(args.aligned_usfm)
    flagged = check_bracket_errors(findings)

    if args.json:
        import json
        print(json.dumps(flagged, indent=2, ensure_ascii=False))
    else:
        if not flagged:
            print(f"No bracket errors found in {args.aligned_usfm}")
        else:
            print(f"Found {len(flagged)} bracket error(s) in {args.aligned_usfm}:\n")
            for item in flagged:
                print(f"  {item['verse_ref']}  {item['word']}  "
                      f"Strong's: {item['strong']}  "
                      f"prefix: {item['prefix']}  "
                      f"-> {item['fix']}")

    sys.exit(1 if flagged else 0)


if __name__ == '__main__':
    main()
