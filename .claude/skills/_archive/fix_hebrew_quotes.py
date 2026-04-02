#!/usr/bin/env python3
"""
Extract Hebrew superscription words from the Hebrew Bible source.

For front/superscription items, lang_convert.js cannot produce the
Hebrew orig_quote. This script extracts the exact Hebrew words
(with Strong's numbers) from the source USFM so they can be used
directly in the TN output.

Usage:
    python3 fix_hebrew_quotes.py PSA 65

    Output (JSON):
    [
      {"word": "...", "strong": "l:H5329", "lemma": "..."},
      ...
    ]

Also usable as a library via extract_front_words().
"""

import argparse
import glob
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
HEBREW_DIR = os.path.join(PROJECT_ROOT, 'data', 'hebrew_bible')


def find_hebrew_usfm(book_code):
    """Find the Hebrew USFM file for a book code (e.g. PSA -> 19-PSA.usfm)."""
    pattern = os.path.join(HEBREW_DIR, f'*-{book_code.upper()}.usfm')
    matches = glob.glob(pattern)
    return matches[0] if matches else None


def extract_front_words(usfm_path, chapter):
    """Extract superscription words from a Hebrew USFM chapter.

    Parses the \\d section and returns a list of dicts:
      [{word, strong, lemma}, ...]

    Each word is the exact Hebrew text from the source.
    """
    with open(usfm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    current_chapter = None
    in_front = False
    words = []

    for line in content.split('\n'):
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            if current_chapter == chapter and words:
                break  # Already collected, done
            current_chapter = ch_match.group(1)
            in_front = False
            continue

        if current_chapter != chapter:
            continue

        # \d marks the superscription
        if line.strip() == '\\d':
            in_front = True
            continue

        # \v or \p ends the superscription
        if re.match(r'\\[vp]\b', line.strip()):
            if in_front and words:
                break
            in_front = False
            continue

        if not in_front:
            continue

        # Extract \w word|attributes\w* entries
        for m in re.finditer(r'\\w\s+([^|]+)\|([^\\]*?)\\w\*', line):
            word_text = m.group(1).strip()
            attrs_str = m.group(2).strip()

            # Parse attributes
            strong = ''
            lemma = ''
            s_match = re.search(r'strong="([^"]*)"', attrs_str)
            if s_match:
                strong = s_match.group(1)
            l_match = re.search(r'lemma="([^"]*)"', attrs_str)
            if l_match:
                lemma = l_match.group(1)

            words.append({
                'word': word_text,
                'strong': strong,
                'lemma': lemma,
            })

    return words


def main():
    parser = argparse.ArgumentParser(
        description='Extract Hebrew superscription words from source USFM.'
    )
    parser.add_argument('book', help='Book code (e.g. PSA)')
    parser.add_argument('chapter', help='Chapter number (e.g. 65)')
    parser.add_argument('--hebrew-usfm', help='Hebrew USFM path (auto-detected if omitted)')

    args = parser.parse_args()

    hebrew_path = args.hebrew_usfm or find_hebrew_usfm(args.book)
    if not hebrew_path:
        print(f"ERROR: No Hebrew USFM found for {args.book} in {HEBREW_DIR}", file=sys.stderr)
        sys.exit(1)

    chapter = args.chapter.lstrip('0') or '0'
    words = extract_front_words(hebrew_path, chapter)

    if not words:
        print(f"No superscription found for {args.book} {chapter}", file=sys.stderr)
        sys.exit(0)

    print(json.dumps(words, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
