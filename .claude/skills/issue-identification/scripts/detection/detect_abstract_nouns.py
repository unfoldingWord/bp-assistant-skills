#!/usr/bin/env python3
"""
detect_abstract_nouns.py - Detect abstract nouns in aligned USFM or plain text

This script identifies potential figs-abstractnouns issues by:
1. Matching English words against the abstract_nouns.txt word list
2. Checking source language morphology for additional signals (when available)
3. Flagging Hebrew/Greek adjectives translated as English abstract nouns

Usage:
  # With alignment JSON (full morphology support)
  python detect_abstract_nouns.py <alignments.json>
  cat alignments.json | python detect_abstract_nouns.py --stdin

  # With raw English text (word list matching only, skips morphology checks)
  python detect_abstract_nouns.py --text "The righteousness of God brings salvation"

Options:
  --stdin           Read alignment JSON from stdin
  --text <string>   Analyze raw English text directly
  --wordlist <file> Custom word list (default: data/abstract_nouns.txt)
  --format <fmt>    Output format: json (default), tsv, or csv
  --verbose         Show additional detection details

Input format (from parse_usfm.js):
  {
    "book": "1JN",
    "alignments": [
      {
        "ref": "1JN 1:1",
        "source": {"word": "...", "lemma": "...", "morph": "..."},
        "english": "the beginning",
        "englishWords": ["the", "beginning"]
      }
    ]
  }

Output format (JSON):
  [
    {
      "ref": "1JN 1:2",
      "english_word": "life",
      "source_word": "zoe",
      "morph": "Gr,N,,,,,GFS,",
      "issue_type": "figs-abstractnouns",
      "confidence": "high",
      "reason": "word in abstract noun list"
    }
  ]
"""

import argparse
import json
import re
import sys
import os
from pathlib import Path


def load_wordlist(filepath: str) -> set:
    """Load abstract nouns word list."""
    words = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip().lower()
            if word:
                words.add(word)
    return words


def is_source_adjective(morph: str) -> bool:
    """Check if source word is an adjective based on morphology code."""
    if not morph:
        return False
    # Hebrew adjective: He,A... or second position A
    # Greek adjective: Gr,A... (adjective) or Gr,AR (restrictive adjective)
    if morph.startswith('He,A') or morph.startswith('Gr,A'):
        return True
    # Check for adjective in morph parts
    parts = morph.split(',')
    if len(parts) >= 2 and parts[1].startswith('A'):
        return True
    return False


def is_source_noun(morph: str) -> bool:
    """Check if source word is a noun based on morphology code."""
    if not morph:
        return False
    # Hebrew noun: He,N... or He,Nc (common noun)
    # Greek noun: Gr,N...
    if morph.startswith('He,N') or morph.startswith('Gr,N'):
        return True
    parts = morph.split(',')
    if len(parts) >= 2 and parts[1].startswith('N'):
        return True
    return False


def parse_text_to_alignments(text: str) -> list:
    """
    Parse raw text (no USFM) into alignment-like structures.
    """
    alignments = []
    words = re.findall(r'\w+', text)

    for word in words:
        alignments.append({
            'ref': 'text',
            'source': {},
            'english': text,
            'englishWords': [word]
        })

    return alignments


def detect_abstract_nouns(alignments: list, wordlist: set, verbose: bool = False) -> list:
    """Detect abstract nouns in alignment data."""
    results = []

    for alignment in alignments:
        ref = alignment.get('ref', '')
        source = alignment.get('source', {})
        english = alignment.get('english', '')
        english_words = alignment.get('englishWords', [])

        source_word = source.get('word', '')
        lemma = source.get('lemma', '')
        morph = source.get('morph', '')

        # Check each English word
        for eng_word in english_words:
            word_lower = eng_word.lower()

            if word_lower in wordlist:
                # Determine confidence and reason
                confidence = 'medium'
                reasons = ['word in abstract noun list']

                # Higher confidence if source is also a noun
                if is_source_noun(morph):
                    confidence = 'high'
                    reasons.append('source is noun')

                # Flag adjective-to-noun translations
                if is_source_adjective(morph):
                    confidence = 'high'
                    reasons.append('source adjective translated as noun')

                result = {
                    'ref': ref,
                    'english_word': eng_word,
                    'english_phrase': english,
                    'source_word': source_word,
                    'lemma': lemma,
                    'morph': morph,
                    'issue_type': 'figs-abstractnouns',
                    'confidence': confidence,
                    'reason': '; '.join(reasons)
                }

                if verbose:
                    result['alignment'] = alignment

                results.append(result)

    return results


def output_results(results: list, fmt: str):
    """Output results in specified format."""
    if fmt == 'json':
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif fmt == 'tsv':
        if results:
            headers = ['ref', 'english_word', 'english_phrase', 'source_word',
                      'lemma', 'morph', 'confidence', 'reason']
            print('\t'.join(headers))
            for r in results:
                row = [str(r.get(h, '')) for h in headers]
                print('\t'.join(row))
    elif fmt == 'csv':
        import csv
        if results:
            headers = ['ref', 'english_word', 'english_phrase', 'source_word',
                      'lemma', 'morph', 'confidence', 'reason']
            writer = csv.DictWriter(sys.stdout, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)


def find_wordlist() -> str:
    """Find the abstract_nouns.txt file."""
    # Look in same directory as script first
    script_dir = Path(__file__).parent.resolve()
    wordlist = script_dir / 'abstract_nouns.txt'
    if wordlist.exists():
        return str(wordlist)
    raise FileNotFoundError(f"Could not find abstract_nouns.txt in {script_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Detect abstract nouns in aligned USFM or plain text',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('input', nargs='?', help='Alignment JSON file')
    parser.add_argument('--stdin', action='store_true', help='Read from stdin')
    parser.add_argument('--text', '-t', help='Analyze raw English text directly')
    parser.add_argument('--wordlist', '-w', help='Custom word list file')
    parser.add_argument('--format', '-f', choices=['json', 'tsv', 'csv'],
                        default='json', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Include full alignment data in output')

    args = parser.parse_args()

    # Load word list
    wordlist_path = args.wordlist if args.wordlist else find_wordlist()
    try:
        wordlist = load_wordlist(wordlist_path)
        print(f"Loaded {len(wordlist)} abstract nouns from {wordlist_path}", file=sys.stderr)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine input mode and get alignments
    if args.text:
        # Raw English text input
        alignments = parse_text_to_alignments(args.text)
    elif args.stdin:
        data = json.load(sys.stdin)
        alignments = data.get('alignments', [])
    elif args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        alignments = data.get('alignments', [])
    else:
        parser.error("Provide input file, use --stdin, or use --text")

    # Detect abstract nouns
    results = detect_abstract_nouns(alignments, wordlist, args.verbose)

    print(f"Found {len(results)} potential abstract nouns", file=sys.stderr)

    # Output results
    output_results(results, args.format)


if __name__ == '__main__':
    main()
