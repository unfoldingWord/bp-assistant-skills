#!/usr/bin/env python3
"""Validate alignment JSON files for the ULT/UST-alignment workflow.

Checks:
1. Every Hebrew word index (0 to n-1) appears in at least one alignment
   (UST mode: unaligned Hebrew indices are allowed)
2. Every English word from english_text appears exactly once across alignments
3. Required fields are present
4. UST mode: entries with hebrew_indices: [] must have all words bracketed

Usage:
    python3 validate_alignment_json.py FILE [FILE ...]
    python3 validate_alignment_json.py --ust FILE [FILE ...]
    python3 validate_alignment_json.py alignments/*.json
"""

import json
import sys
from collections import Counter
from pathlib import Path


def validate_file(filepath, ust_mode=False):
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
    extra = aligned_indices - expected_indices
    if extra:
        errors.append(f"Hebrew indices out of range: {sorted(extra)}")

    if not ust_mode:
        # ULT mode: every Hebrew index must be aligned
        missing = expected_indices - aligned_indices
        if missing:
            errors.append(f"Hebrew indices not aligned: {sorted(missing)}")
    else:
        # UST mode: unaligned Hebrew indices are allowed (report as info, not error)
        missing = expected_indices - aligned_indices
        if missing:
            # Just informational -- not an error in UST mode
            pass

    # UST mode: entries with hebrew_indices: [] must have all words bracketed
    if ust_mode:
        for i, a in enumerate(data["alignments"]):
            if a.get("hebrew_indices") == []:
                for word in a.get("english", []):
                    if not (word.startswith("{") and word.endswith("}")):
                        # Strip trailing punctuation before checking
                        stripped = word.rstrip(".,;:!?")
                        if not (stripped.startswith("{") and stripped.endswith("}")):
                            errors.append(
                                f"Alignment {i}: word \"{word}\" has hebrew_indices: [] "
                                f"but is not bracketed"
                            )

    # Check every english word appears exactly once
    # If d_text is present, section:"d" words validate against d_text,
    # remaining words validate against english_text
    has_d_text = "d_text" in data

    if has_d_text:
        d_alignments = [a for a in data["alignments"] if a.get("section") == "d"]
        body_alignments = [a for a in data["alignments"] if a.get("section") != "d"]

        # Validate d_text words
        d_from_text = data["d_text"].split()
        d_from_alignments = []
        for a in d_alignments:
            d_from_alignments.extend(a.get("english", []))

        d_text_counts = Counter(d_from_text)
        d_align_counts = Counter(d_from_alignments)

        if d_text_counts != d_align_counts:
            for word in sorted(set(d_text_counts.keys()) | set(d_align_counts.keys())):
                tc = d_text_counts[word]
                ac = d_align_counts[word]
                if tc != ac:
                    if ac == 0:
                        errors.append(f"d_text: Word \"{word}\" in d_text but not in section:d alignments")
                    elif tc == 0:
                        errors.append(f"d_text: Word \"{word}\" in section:d alignments but not in d_text")
                    else:
                        errors.append(f"d_text: Word \"{word}\": {ac} in section:d alignments, {tc} in d_text")

        # Validate english_text words (body only)
        eng_from_text = data["english_text"].split()
        eng_from_alignments = []
        for a in body_alignments:
            eng_from_alignments.extend(a.get("english", []))
    else:
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
        print(f"Usage: {sys.argv[0]} [--ust] FILE [FILE ...]", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]
    ust_mode = False

    if "--ust" in args:
        ust_mode = True
        args.remove("--ust")

    if not args:
        print(f"Usage: {sys.argv[0]} [--ust] FILE [FILE ...]", file=sys.stderr)
        sys.exit(1)

    files = args
    all_pass = True

    for filepath in sorted(files):
        name = Path(filepath).name
        errors = validate_file(filepath, ust_mode=ust_mode)
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
