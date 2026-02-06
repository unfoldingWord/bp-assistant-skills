#!/usr/bin/env python3
"""
Convert straight quotes to curly quotes in text files.

Usage:
    python3 curly_quotes.py input.usfm [--output output.usfm] [--in-place]

If --output is not specified and --in-place is not set, outputs to stdout.
"""

import argparse
import re
import sys
from pathlib import Path


def convert_to_curly_quotes(text: str) -> str:
    """
    Convert straight quotes to curly quotes.

    Rules:
    - Opening quote: after whitespace, at start of line, after opening punctuation
    - Closing quote: before whitespace, at end of line, before closing punctuation

    Double quotes: " -> " or "
    Single quotes: ' -> ' or '
    """
    result = []
    i = 0

    while i < len(text):
        char = text[i]

        if char == '"':
            # Determine if opening or closing
            if is_opening_quote(text, i):
                result.append('\u201c')
            else:
                result.append('\u201d')
        elif char == "'":
            # Check if it's an apostrophe (within a word) or a quote
            if is_apostrophe(text, i):
                result.append('\u2019')  # Curly apostrophe
            elif is_opening_quote(text, i):
                result.append('\u2018')
            else:
                result.append('\u2019')
        else:
            result.append(char)

        i += 1

    return ''.join(result)


def is_opening_quote(text: str, pos: int) -> bool:
    """Determine if quote at position is an opening quote."""
    if pos == 0:
        return True

    prev_char = text[pos - 1]

    # Opening after whitespace or opening punctuation
    if prev_char in ' \t\n\r([{':
        return True

    # Opening after em-dash or en-dash
    if prev_char in '—–':
        return True

    # Check for USFM markers - quote after \v 1, \q1, etc.
    # Look back for backslash pattern
    look_back = text[max(0, pos-10):pos]
    if re.search(r'\\[a-z0-9]+\s*\*?\s*$', look_back):
        return True

    return False


def is_apostrophe(text: str, pos: int) -> bool:
    """Determine if single quote at position is an apostrophe (within a word)."""
    if pos == 0 or pos == len(text) - 1:
        return False

    prev_char = text[pos - 1]
    next_char = text[pos + 1]

    # Apostrophe if surrounded by letters (contractions, possessives)
    if prev_char.isalpha() and next_char.isalpha():
        return True

    # Possessive 's at end of word: "David's"
    if prev_char.isalpha() and next_char == 's':
        # Check if 's is at word end
        if pos + 2 >= len(text) or not text[pos + 2].isalpha():
            return True

    # Trailing apostrophe for plurals: peoples'
    if prev_char == 's' and not next_char.isalpha():
        return True

    return False


def process_file(input_path: Path, output_path: Path = None, in_place: bool = False) -> str:
    """Process a file and convert quotes."""
    text = input_path.read_text(encoding='utf-8')
    converted = convert_to_curly_quotes(text)

    if in_place:
        input_path.write_text(converted, encoding='utf-8')
        return f"Converted {input_path} in place"
    elif output_path:
        output_path.write_text(converted, encoding='utf-8')
        return f"Wrote converted text to {output_path}"
    else:
        return converted


def main():
    parser = argparse.ArgumentParser(
        description='Convert straight quotes to curly quotes in text files.'
    )
    parser.add_argument('input', type=Path, help='Input file path')
    parser.add_argument('--output', '-o', type=Path, help='Output file path')
    parser.add_argument('--in-place', '-i', action='store_true',
                        help='Modify file in place')

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: {args.input} does not exist", file=sys.stderr)
        sys.exit(1)

    result = process_file(args.input, args.output, args.in_place)

    if not args.in_place and not args.output:
        # Output to stdout
        print(result)
    else:
        print(result, file=sys.stderr)


if __name__ == '__main__':
    main()
