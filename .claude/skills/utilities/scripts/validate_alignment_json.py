#!/usr/bin/env python3
"""Validate alignment JSON files for the ULT-alignment workflow.

Checks:
1. Every Hebrew word index (0 to n-1) appears in at least one alignment
2. Every English word from english_text appears exactly once across alignments
3. Required fields are present

Usage:
    python3 validate_alignment_json.py FILE [FILE ...]
    python3 validate_alignment_json.py alignments/*.json
"""

import json
import sys
from collections import Counter
from pathlib import Path


def validate_file(filepath):
    """Validate a single alignment JSON file. Returns list of error strings."""
    errors = []

    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return [f"File not found"]

    # Check required fields
    for field in ("reference", "hebrew_words", "english_text", "alignments"):
        if field not in data:
            errors.append(f"Missing required field: {field}")
    if errors:
        return errors

    # Check hebrew word indices are sequential 0..n-1
    hebrew_words = data["hebrew_words"]
    for i, hw in enumerate(hebrew_words):
        if hw.get("index") != i:
            errors.append(f"Hebrew word at position {i} has index {hw.get('index')}, expected {i}")

    # Check every hebrew index appears in at least one alignment
    aligned_indices = set()
    for a in data["alignments"]:
        for idx in a.get("hebrew_indices", []):
            aligned_indices.add(idx)

    expected_indices = set(range(len(hebrew_words)))
    missing = expected_indices - aligned_indices
    extra = aligned_indices - expected_indices
    if missing:
        errors.append(f"Hebrew indices not aligned: {sorted(missing)}")
    if extra:
        errors.append(f"Hebrew indices out of range: {sorted(extra)}")

    # Check every english word appears exactly once
    eng_from_text = data["english_text"].split()
    eng_from_alignments = []
    for a in data["alignments"]:
        eng_from_alignments.extend(a.get("english", []))

    text_counts = Counter(eng_from_text)
    align_counts = Counter(eng_from_alignments)

    if text_counts != align_counts:
        for word in sorted(set(text_counts.keys()) | set(align_counts.keys())):
            tc = text_counts[word]
            ac = align_counts[word]
            if tc != ac:
                if ac == 0:
                    errors.append(f"Word \"{word}\" in english_text but not in alignments")
                elif tc == 0:
                    errors.append(f"Word \"{word}\" in alignments but not in english_text")
                else:
                    errors.append(f"Word \"{word}\": {ac} in alignments, {tc} in english_text")

    return errors


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} FILE [FILE ...]", file=sys.stderr)
        sys.exit(1)

    files = sys.argv[1:]
    all_pass = True

    for filepath in sorted(files):
        name = Path(filepath).name
        errors = validate_file(filepath)
        if errors:
            all_pass = False
            print(f"FAIL  {name}")
            for e in errors:
                print(f"      {e}")
        else:
            print(f"OK    {name}")

    if all_pass:
        print(f"\nAll {len(files)} file(s) passed.")
    else:
        print(f"\nValidation errors found.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
