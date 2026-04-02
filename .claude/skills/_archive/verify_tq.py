#!/usr/bin/env python3
"""
Verify TQ output TSV for format correctness.

Quick format check on AI-generated TQ output:
- Correct column count (7 per row)
- References are valid (chapter:verse format)
- No empty Question fields
- Row count comparison vs input
- Flags potential direct quotes in questions/answers

Usage:
    python3 verify_tq.py output/tq/PSA-150.tsv
    python3 verify_tq.py output/tq/PSA-150.tsv --input-json /tmp/claude/prepared_tq.json
"""

import argparse
import os
import re
import sys


def verify_tsv(filepath, input_json_path=None):
    """Verify a TQ TSV file and report issues.

    Returns (errors, warnings) as lists of strings.
    """
    errors = []
    warnings = []

    if not os.path.exists(filepath):
        errors.append(f"File not found: {filepath}")
        return errors, warnings

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.read().rstrip('\n').split('\n')

    if not lines:
        errors.append("File is empty")
        return errors, warnings

    # Check header
    header = lines[0]
    expected_header = "Reference\tID\tTags\tQuote\tOccurrence\tQuestion\tResponse"
    if header != expected_header:
        warnings.append(f"Header mismatch. Expected: {expected_header}")
        warnings.append(f"  Got: {header}")

    header_cols = header.split('\t')
    expected_col_count = len(header_cols)

    data_rows = lines[1:]
    if not data_rows:
        errors.append("No data rows found")
        return errors, warnings

    # Check each row
    direct_quote_pattern = re.compile(r'["\u201c\u201d]')
    ref_pattern = re.compile(r'^\d+:\d+(-\d+)?$')

    for i, row in enumerate(data_rows, start=2):
        cols = row.split('\t')

        # Column count
        if len(cols) != expected_col_count:
            errors.append(f"Row {i}: Expected {expected_col_count} columns, got {len(cols)}")
            continue

        ref = cols[0]
        row_id = cols[1]
        question = cols[5] if len(cols) > 5 else ''
        response = cols[6] if len(cols) > 6 else ''

        # Reference format
        if not ref_pattern.match(ref):
            errors.append(f"Row {i}: Invalid reference format: '{ref}'")

        # Empty question
        if not question.strip():
            errors.append(f"Row {i} ({ref}): Empty Question field")

        # Empty response
        if not response.strip():
            warnings.append(f"Row {i} ({ref}): Empty Response field")

        # Empty ID
        if not row_id.strip():
            warnings.append(f"Row {i} ({ref}): Empty ID field")

        # Direct quotes in question (flag for review)
        if direct_quote_pattern.search(question):
            warnings.append(f"Row {i} ({ref}): Question contains quotation marks (review for direct quotes)")

        # Direct quotes in response
        if direct_quote_pattern.search(response):
            warnings.append(f"Row {i} ({ref}): Response contains quotation marks (review for direct quotes)")

    # Row count comparison with input
    if input_json_path and os.path.exists(input_json_path):
        try:
            import json
            with open(input_json_path, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
            input_rows = sum(len(v) for v in input_data.get('tq_rows_by_chapter', {}).values())
            output_rows = len(data_rows)
            diff = abs(output_rows - input_rows)
            if diff > 0:
                pct = (diff / max(input_rows, 1)) * 100
                if pct > 30:
                    warnings.append(
                        f"Row count difference: input had {input_rows} rows, "
                        f"output has {output_rows} rows ({pct:.0f}% change)"
                    )
                else:
                    print(f"  Row count: {input_rows} input -> {output_rows} output", file=sys.stderr)
        except (json.JSONDecodeError, KeyError):
            pass

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description='Verify TQ output TSV format')
    parser.add_argument('tsv_file', help='Path to TQ TSV file to verify')
    parser.add_argument('--input-json', help='Path to prepared_tq.json for row count comparison')

    args = parser.parse_args()

    print(f"Verifying: {args.tsv_file}", file=sys.stderr)
    errors, warnings = verify_tsv(args.tsv_file, args.input_json)

    if warnings:
        print(f"\nWarnings ({len(warnings)}):", file=sys.stderr)
        for w in warnings:
            print(f"  WARNING: {w}", file=sys.stderr)

    if errors:
        print(f"\nErrors ({len(errors)}):", file=sys.stderr)
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nAll checks passed.", file=sys.stderr)


if __name__ == '__main__':
    main()
