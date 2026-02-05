#!/usr/bin/env python3
"""
Convert straight quotes to curly quotes in USFM files.

Converts:
- Straight double quotes "..." to curly "..."
- Straight single quotes/apostrophes '...' to curly '...'

Usage:
    python3 curly_quotes.py <file.usfm> [--in-place]
    python3 curly_quotes.py <file.usfm> -o <output.usfm>
"""

import argparse
import re
import sys


def convert_quotes(text: str) -> str:
    """Convert straight quotes to curly quotes."""
    result = []
    i = 0
    in_double_quote = False
    in_single_quote = False

    while i < len(text):
        char = text[i]
        prev_char = text[i - 1] if i > 0 else ''
        next_char = text[i + 1] if i < len(text) - 1 else ''

        if char == '"':
            # Double quote handling
            if not in_double_quote:
                # Opening quote: after whitespace, line start, or opening punctuation
                if prev_char in ('', ' ', '\t', '\n', '(', '[', '{', '\u2018', '\u201C') or i == 0:
                    result.append('\u201C')  # Left double quote "
                    in_double_quote = True
                else:
                    # Default to opening if unclear
                    result.append('\u201C')
                    in_double_quote = True
            else:
                # Closing quote
                result.append('\u201D')  # Right double quote "
                in_double_quote = False

        elif char == "'":
            # Single quote / apostrophe handling
            # Check if it's an apostrophe within a word (contraction or possessive)
            if prev_char.isalpha() and next_char.isalpha():
                # Mid-word apostrophe (e.g., "don't", "it's")
                result.append('\u2019')  # Right single quote '
            elif prev_char.isalpha() and (next_char == 's' or next_char == ''):
                # Possessive or end contraction (e.g., "Jesus'", "James's")
                result.append('\u2019')  # Right single quote '
            elif not in_single_quote:
                # Opening single quote
                if prev_char in ('', ' ', '\t', '\n', '(', '[', '{', '\u201C', '\u2018') or i == 0:
                    result.append('\u2018')  # Left single quote '
                    in_single_quote = True
                else:
                    # Likely an apostrophe at word start or unclear context
                    # Check if followed by word characters (opening quote)
                    if next_char.isalpha():
                        result.append('\u2018')  # Left single quote
                        in_single_quote = True
                    else:
                        result.append('\u2019')  # Right single quote (apostrophe)
            else:
                # Closing single quote
                result.append('\u2019')  # Right single quote '
                in_single_quote = False

        else:
            result.append(char)
            # Reset quote tracking at line breaks
            if char == '\n':
                in_double_quote = False
                in_single_quote = False

        i += 1

    return ''.join(result)


def process_file(input_path: str, output_path: str = None, in_place: bool = False) -> None:
    """Process a USFM file, converting quotes."""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    converted = convert_quotes(content)

    if in_place:
        output_path = input_path

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted)
        print(f"Converted quotes in {input_path}" + (" (in-place)" if in_place else f" -> {output_path}"))
    else:
        # Print to stdout
        print(converted)


def main():
    parser = argparse.ArgumentParser(
        description='Convert straight quotes to curly quotes in USFM files.'
    )
    parser.add_argument('input', help='Input USFM file')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--in-place', action='store_true',
                        help='Modify file in place')

    args = parser.parse_args()

    if args.in_place and args.output:
        print("Error: Cannot use both --in-place and --output", file=sys.stderr)
        sys.exit(1)

    process_file(args.input, args.output, args.in_place)


if __name__ == '__main__':
    main()
