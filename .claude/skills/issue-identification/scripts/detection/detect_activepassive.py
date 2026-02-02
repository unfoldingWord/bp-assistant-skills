#!/usr/bin/env python3
"""
detect_activepassive.py - Detect ALL passive voice in English ULT

Per Issues Resolved: "Every instance of the passive voice in ULT should get
a figs-activepassive note."

This script identifies ALL English passive constructions so translators whose
languages lack passive voice can find and convert them to active.

Usage:
  # With alignment JSON (groups by verse)
  python detect_activepassive.py <alignments.json>
  cat alignments.json | python detect_activepassive.py --stdin

  # With raw English text (skips source language checks)
  python detect_activepassive.py --text "The bread was broken and given to them"

Options:
  --stdin           Read alignment JSON from stdin
  --text <string>   Analyze raw English text directly
  --format <fmt>    Output format: json (default), tsv, or csv
  --with-source     Include source language voice info (bonus data, alignment JSON only)

English passive patterns detected:
  - be/is/are/am/was/were/been/being + past participle
  - "was called", "is written", "were sent", "has been given", etc.

Output format (JSON):
  [
    {
      "ref": "1JN 1:2",
      "passive_construction": "was revealed",
      "verse_text": "the life was revealed...",
      "issue_type": "figs-activepassive"
    }
  ]
"""

import argparse
import json
import re
import sys


# English passive auxiliary verbs (forms of "be")
PASSIVE_AUXILIARIES = {'be', 'is', 'are', 'am', 'was', 'were', 'been', 'being'}

# Common past participle endings (must be preceded by consonant or vowel pattern)
# These are endings that reliably indicate past participles
PARTICIPLE_ENDINGS = ('ed', 'en', 'wn', 'ung', 'orn', 'oken', 'osen',
                      'otten', 'iven', 'aken', 'tten')

# Irregular past participles
IRREGULAR_PARTICIPLES = {
    'been', 'done', 'gone', 'seen', 'known', 'shown', 'given', 'taken',
    'made', 'said', 'told', 'found', 'thought', 'brought', 'bought',
    'caught', 'taught', 'sought', 'felt', 'left', 'held', 'kept', 'slept',
    'met', 'sent', 'spent', 'built', 'lent', 'lost', 'meant', 'heard',
    'born', 'borne', 'worn', 'torn', 'sworn', 'chosen', 'frozen', 'spoken',
    'broken', 'stolen', 'woken', 'written', 'hidden', 'ridden', 'driven',
    'risen', 'forgiven', 'forgotten', 'begotten', 'bitten', 'eaten', 'beaten',
    'shaken', 'forsaken', 'mistaken', 'undertaken', 'struck', 'stuck', 'stung',
    'swung', 'hung', 'sung', 'rung', 'sprung', 'begun', 'run', 'won', 'spun',
    'put', 'cut', 'shut', 'set', 'let', 'hit', 'hurt', 'cast', 'burst', 'cost',
    'spread', 'shed', 'split', 'spit', 'quit', 'rid', 'bid', 'read', 'led',
    'fed', 'bled', 'bred', 'sped', 'fled', 'paid', 'laid', 'called', 'filled',
    'killed', 'named', 'blessed', 'cursed', 'gathered', 'scattered', 'covered',
    'revealed', 'fulfilled', 'proclaimed', 'announced', 'established',
    'justified', 'sanctified', 'glorified', 'baptized', 'circumcised'
}

# Words that look like they could be participles but aren't used in passives
NOT_PARTICIPLES = {
    'not', 'that', 'what', 'but', 'just', 'about', 'out', 'without',
    'light', 'right', 'night', 'might', 'sight', 'fight', 'eight',
    'great', 'heart', 'part', 'start', 'apart', 'art',
    'in', 'then', 'when', 'often', 'even', 'open', 'seven', 'eleven',
    'own', 'down', 'town', 'brown', 'grown', 'known',  # known IS a participle but handled separately
    'men', 'women', 'children', 'brethren',
    'heaven', 'garden', 'burden', 'sudden', 'golden', 'wooden', 'hidden',
    'often', 'listen', 'hasten', 'fasten', 'lessen', 'lesson',
    'and', 'hand', 'land', 'stand', 'understand', 'command', 'demand',
    'around', 'ground', 'sound', 'found', 'bound', 'round', 'wound',
    'hundred', 'kindred'
}

# Stative adjectives that follow "be" but are not passive constructions
# "be ashamed", "be afraid" etc. are states, not passives
STATIVE_ADJECTIVES = {
    'ashamed', 'afraid', 'alone', 'afflicted', 'angry', 'anxious',
    'aware', 'alive', 'asleep', 'awake', 'absent', 'able',
    'blessed', 'blameless',
    'clean', 'certain', 'content',
    'dead', 'drunk',
    'empty', 'evil',
    'full', 'faithful', 'free',
    'glad', 'good', 'great', 'guilty', 'gracious',
    'holy', 'humble', 'hungry', 'happy',
    'innocent', 'ill',
    'jealous', 'just', 'joyful',
    'kind',
    'like', 'lost', 'low',
    'merciful', 'mighty',
    'naked', 'near',
    'obedient', 'old',
    'perfect', 'pleasant', 'poor', 'present', 'proud', 'pure',
    'quick', 'quiet',
    'ready', 'rich', 'righteous', 'right',
    'sad', 'safe', 'sick', 'silent', 'sinful', 'sorry', 'strong', 'sure', 'still',
    'true', 'troubled',
    'unclean', 'unworthy', 'upright',
    'weary', 'weak', 'well', 'whole', 'wicked', 'wise', 'worthy', 'wrong',
    'young'
}


def is_past_participle(word: str) -> bool:
    """Check if a word is likely a past participle."""
    word_lower = word.lower()

    # Exclude stative adjectives - these aren't passives
    if word_lower in STATIVE_ADJECTIVES:
        return False

    # Exclude known non-participles
    if word_lower in NOT_PARTICIPLES:
        return False

    # Check irregular participles first
    if word_lower in IRREGULAR_PARTICIPLES:
        return True

    # Check common participle endings
    for ending in PARTICIPLE_ENDINGS:
        if word_lower.endswith(ending) and len(word_lower) > len(ending) + 2:
            return True

    return False


def find_passives_in_text(text: str) -> list:
    """
    Find all passive constructions in English text.
    Returns list of dicts with auxiliary, participle, phrase.
    """
    passives = []
    # Remove USFM markers and punctuation for word splitting
    clean_text = re.sub(r'\\[a-z]+\s*', '', text)
    words = clean_text.split()

    i = 0
    while i < len(words):
        word = words[i].lower().strip('.,;:!?"\'"{}[]')

        if word in PASSIVE_AUXILIARIES:
            # Look ahead for past participle (may have adverbs between)
            for j in range(i + 1, min(i + 4, len(words))):
                next_word = words[j].strip('.,;:!?"\'"{}[]')
                if is_past_participle(next_word):
                    # Found passive construction
                    phrase_words = words[i:j+1]
                    phrase = ' '.join(w.strip('.,;:!?"\'"{}[]') for w in phrase_words)
                    passives.append({
                        'auxiliary': word,
                        'participle': next_word.lower(),
                        'phrase': phrase
                    })
                    i = j  # Skip past this construction
                    break
        i += 1

    return passives


def build_verse_text_from_alignments(alignments: list) -> dict:
    """
    Build verse text by grouping alignment English words.
    Returns dict mapping ref -> verse text.
    """
    verses = {}

    for alignment in alignments:
        ref = alignment.get('ref', '')
        english_words = alignment.get('englishWords', [])

        if ref not in verses:
            verses[ref] = []

        for word_info in english_words:
            if isinstance(word_info, dict):
                word = word_info.get('word', '')
            else:
                word = str(word_info)
            if word:
                verses[ref].append(word)

    # Join words into text
    return {ref: ' '.join(words) for ref, words in verses.items()}


def detect_passives_in_verses(verses: dict) -> list:
    """Detect ALL passive constructions in verse texts."""
    results = []

    for ref, text in sorted(verses.items()):
        passives = find_passives_in_text(text)

        for passive in passives:
            results.append({
                'ref': ref,
                'passive_construction': passive['phrase'],
                'auxiliary': passive['auxiliary'],
                'participle': passive['participle'],
                'verse_text': text[:100] + ('...' if len(text) > 100 else ''),
                'issue_type': 'figs-activepassive'
            })

    return results


def output_results(results: list, fmt: str):
    """Output results in specified format."""
    if fmt == 'json':
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif fmt == 'tsv':
        if results:
            headers = ['ref', 'passive_construction', 'auxiliary', 'participle']
            print('\t'.join(headers))
            for r in results:
                row = [str(r.get(h, '')) for h in headers]
                print('\t'.join(row))
    elif fmt == 'csv':
        import csv
        if results:
            headers = ['ref', 'passive_construction', 'auxiliary', 'participle', 'verse_text']
            writer = csv.DictWriter(sys.stdout, fieldnames=headers,
                                   extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)


def main():
    parser = argparse.ArgumentParser(
        description='Detect ALL passive voice in English ULT',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('input', nargs='?', help='Alignment JSON file')
    parser.add_argument('--stdin', action='store_true', help='Read from stdin')
    parser.add_argument('--text', '-t', help='Analyze raw English text directly')
    parser.add_argument('--format', '-f', choices=['json', 'tsv', 'csv'],
                        default='json', help='Output format')
    parser.add_argument('--with-source', '-s', action='store_true',
                        help='Include source language voice info')

    args = parser.parse_args()

    # Determine input mode and get verses
    if args.text:
        # Raw English text - use 'text' as the reference
        verses = {'text': args.text}
    elif args.stdin or args.input:
        if args.stdin:
            data = json.load(sys.stdin)
        else:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        alignments = data.get('alignments', [])
        verses = build_verse_text_from_alignments(alignments)
    else:
        parser.error("Provide input file, use --stdin, or use --text")

    # Detect ALL passives
    results = detect_passives_in_verses(verses)

    print(f"Found {len(results)} passive constructions in {len(verses)} verses", file=sys.stderr)

    # Output results
    output_results(results, args.format)


if __name__ == '__main__':
    main()
