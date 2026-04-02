#!/usr/bin/env python3
"""
Check terms against Translation Words (tW) headwords.

Usage:
    python check_tw_headwords.py "term1" "term2" ...
    echo "Yahweh\nbread\nAbimelech" | python check_tw_headwords.py --stdin

Returns JSON with matches and no_match lists.
"""

import json
import sys
import os
from pathlib import Path


def load_headwords():
    """Load tw_headwords.json from the data directory."""
    script_dir = Path(__file__).parent
    # Navigate from scripts/ to project root, then to data/
    data_path = script_dir.parent.parent.parent.parent / "data" / "tw_headwords.json"

    if not data_path.exists():
        # Try alternate path (if running from different location)
        alt_path = Path("data/tw_headwords.json")
        if alt_path.exists():
            data_path = alt_path
        else:
            print(f"Error: Could not find tw_headwords.json at {data_path}", file=sys.stderr)
            sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_term(term):
    """
    Generate normalized variants of a term for matching.
    Returns a list of variants to try (original + stripped versions).
    """
    term_lower = term.lower().strip()
    variants = [term_lower]

    # Try removing common suffixes (plural stripping)
    if term_lower.endswith("ites"):
        # Hittites -> Hittite
        variants.append(term_lower[:-1])  # Remove 's'
        variants.append(term_lower[:-4])  # Remove 'ites'
    elif term_lower.endswith("ies"):
        # cities -> city (change ies to y)
        variants.append(term_lower[:-3] + "y")
    elif term_lower.endswith("es"):
        # churches -> church
        variants.append(term_lower[:-2])
        # Also try just removing 's' for words like "Israelites"
        variants.append(term_lower[:-1])
    elif term_lower.endswith("s") and not term_lower.endswith("ss"):
        # Amorites -> Amorite, kings -> king
        variants.append(term_lower[:-1])

    return variants


def build_headword_index(tw_entries):
    """
    Build a case-insensitive index from headwords to their entries.
    Returns dict: lowercase_headword -> entry
    """
    index = {}
    for entry in tw_entries:
        for hw in entry.get("headwords", []):
            hw_lower = hw.lower()
            if hw_lower not in index:
                index[hw_lower] = (hw, entry)  # Store original case and entry
    return index


def check_terms(terms, tw_entries):
    """
    Check a list of terms against tW headwords.
    Returns dict with 'matches' and 'no_match' lists.
    """
    index = build_headword_index(tw_entries)

    matches = []
    no_match = []

    for term in terms:
        term = term.strip()
        if not term:
            continue

        found = False
        variants = normalize_term(term)

        for variant in variants:
            if variant in index:
                original_hw, entry = index[variant]
                match_info = {
                    "term": term,
                    "twarticle": entry["twarticle"],
                    "category": entry["category"],
                    "headwords": entry["headwords"],
                    "matched_headword": original_hw
                }
                # Note if we had to normalize
                if variant != term.lower():
                    match_info["normalized_from"] = term
                matches.append(match_info)
                found = True
                break

        if not found:
            no_match.append(term)

    return {"matches": matches, "no_match": no_match}


def main():
    # Parse arguments
    if "--stdin" in sys.argv:
        # Read terms from stdin, one per line
        terms = [line.strip() for line in sys.stdin if line.strip()]
    elif len(sys.argv) > 1:
        # Terms passed as arguments
        terms = [arg for arg in sys.argv[1:] if arg != "--stdin"]
    else:
        print("Usage: python check_tw_headwords.py [--stdin] [term1] [term2] ...", file=sys.stderr)
        print("  --stdin    Read terms from stdin (one per line)", file=sys.stderr)
        print("  term1...   Terms to check as command-line arguments", file=sys.stderr)
        sys.exit(1)

    # Load headwords and check terms
    tw_entries = load_headwords()
    results = check_terms(terms, tw_entries)

    # Output JSON
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
