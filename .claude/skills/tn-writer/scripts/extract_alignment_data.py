#!/usr/bin/env python3
"""
Extract alignment data from aligned USFM as structured JSON.

Parses zaln-s milestones to produce per-verse English-to-Hebrew word mappings.
This is the mechanical/deterministic part of Hebrew quote extraction -- the
semantic matching (which English words correspond to a gl_quote) and Hebrew
word ordering are handled by Claude via prompt instructions in SKILL.md.

Usage:
    python3 extract_alignment_data.py <aligned.usfm> [--output <path>]

Output format:
    {
      "3:1": [
        {"eng": "Hear", "heb": "שִׁמְעָ֣⁠ה", "heb_pos": 0, "strong": "H8085"},
        {"eng": "my", "heb": "רִנָּתִ֑⁠י", "heb_pos": 2, "strong": "H7440"}
      ]
    }
"""

import argparse
import json
import os
import re
import sys

def parse_aligned_usfm(usfm_path):
    """Parse aligned USFM into per-verse word-to-Hebrew mappings.

    Returns dict: { "chapter:verse" -> [word_record, ...] }
    Each word_record: { eng, heb, heb_pos, strong }
    """
    with open(usfm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    verses = {}
    current_chapter = None
    current_verse = None
    current_words = []
    english_pos_counter = 0
    hebrew_pos_counter = 0
    active_milestones = []

    def save_verse():
        nonlocal current_words
        if current_chapter and current_verse and current_words:
            key = f"{current_chapter}:{current_verse}"
            verses[key] = current_words
        current_words = []

    for line in content.split('\n'):
        # Chapter marker
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            save_verse()
            current_chapter = ch_match.group(1)
            current_verse = None
            current_words = []
            english_pos_counter = 0
            hebrew_pos_counter = 0
            active_milestones = []
            continue

        # Verse marker
        v_match = re.match(r'.*\\v\s+(\d+[-\d]*|front)\s*(.*)', line)
        if v_match and current_chapter:
            save_verse()
            current_verse = v_match.group(1)
            current_words = []
            english_pos_counter = 0
            hebrew_pos_counter = 0
            active_milestones = []
            line_rest = line
        else:
            line_rest = line

        if current_verse is None:
            continue

        # Walk the line tracking zaln-s milestones and \w word markers
        pos = 0
        while pos < len(line_rest):
            # zaln-s milestone (alignment start)
            zaln_match = re.match(
                r'\\zaln-s\s+\|([^\\]*?)\\?\*',
                line_rest[pos:]
            )
            if zaln_match:
                attrs = zaln_match.group(1)
                x_content = ''
                x_strong = ''
                cm = re.search(r'x-content="([^"]*)"', attrs)
                if cm:
                    x_content = cm.group(1)
                sm = re.search(r'x-strong="([^"]*)"', attrs)
                if sm:
                    x_strong = sm.group(1)
                x_pos = hebrew_pos_counter
                hebrew_pos_counter += 1
                active_milestones.append((x_content, x_strong, x_pos))
                pos += zaln_match.end()
                continue

            # \w word marker (English word)
            w_match = re.match(r'\\w\s+([^|\\]+)\|[^\\]*\\w\*', line_rest[pos:])
            if w_match:
                eng_word = w_match.group(1).strip()
                if active_milestones:
                    hebrew, strong, hpos = active_milestones[-1]
                    current_words.append({
                        'eng': eng_word,
                        'heb': hebrew,
                        'heb_pos': hpos,
                        'strong': strong,
                    })
                english_pos_counter += 1
                pos += w_match.end()
                continue

            # zaln-e (alignment end) - pop milestone
            zaln_e_match = re.match(r'\\zaln-e\\?\*', line_rest[pos:])
            if zaln_e_match:
                if active_milestones:
                    active_milestones.pop()
                pos += zaln_e_match.end()
                continue

            pos += 1

    # Save last verse
    save_verse()

    return verses

def main():
    parser = argparse.ArgumentParser(
        description='Extract alignment data from aligned USFM as structured JSON.'
    )
    parser.add_argument('aligned_usfm', help='Path to aligned USFM file')
    parser.add_argument('--output', '-o', help='Output JSON file (default: stdout)')

    args = parser.parse_args()

    if not os.path.exists(args.aligned_usfm):
        print(f"ERROR: File not found: {args.aligned_usfm}", file=sys.stderr)
        sys.exit(1)

    verses = parse_aligned_usfm(args.aligned_usfm)

    output_json = json.dumps(verses, indent=2, ensure_ascii=False)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        total_words = sum(len(words) for words in verses.values())
        print(f"Wrote {len(verses)} verses ({total_words} aligned words) to {args.output}",
              file=sys.stderr)
    else:
        print(output_json)

if __name__ == '__main__':
    main()
