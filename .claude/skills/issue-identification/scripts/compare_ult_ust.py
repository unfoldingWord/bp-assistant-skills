#!/usr/bin/env python3
"""
compare_ult_ust.py - Compare ULT and UST to identify potential translation issues

Where UST diverges from ULT (beyond simple synonym/clarity changes), there may be
a translation issue worth noting.

Usage:
  python compare_ult_ust.py <ult_file> <ust_file> [options]
  python compare_ult_ust.py /tmp/book_ult.usfm /tmp/book_ust.usfm --chapter 58
  python compare_ult_ust.py /tmp/book_ult.usfm /tmp/book_ust.usfm --output /tmp/diff.tsv

Options:
  --chapter <N>      Filter to specific chapter
  --output <path>    Output file path (default: stdout)
  --format <tsv|json>  Output format (default: tsv)

Output columns (TSV):
  verse, ult_text, ust_text, diff_type, suggested_issue

Difference patterns detected:
  - added_words: UST adds clarifying words -> figs-explicit
  - removed_repetition: UST removes repeated elements -> figs-doublet, figs-parallelism
  - restructured: UST changes clause order -> figs-infostructure
  - replaced_metaphor: UST replaces figurative language -> figs-metaphor
  - unpacked_abstract: UST expands abstract noun -> figs-abstractnouns
  - voice_change: UST changes passive to active -> figs-activepassive
  - expanded_phrase: UST explains idiom/phrase -> figs-idiom
"""

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from typing import Optional

def parse_usfm_verses(content: str, chapter: Optional[int] = None) -> dict:
    """
    Parse USFM content and extract verses as {chapter:verse: text}.

    Handles basic USFM markers: \\c, \\v, \\p, \\q, etc.
    """
    verses = {}
    current_chapter = 0
    current_verse = ""
    current_text = []

    # Remove alignment markers like \zaln-s and \zaln-e
    content = re.sub(r'\\zaln-[se][^\\]*', '', content)
    # Remove word markers like \w ... \w*
    content = re.sub(r'\\w\s+([^|\\]+)\|[^\\]*\\w\*', r'\1', content)
    # Remove any remaining \w markers without content
    content = re.sub(r'\\w\*', '', content)

    for line in content.split('\n'):
        line = line.strip()

        # Chapter marker
        if line.startswith('\\c '):
            # Save previous verse if any
            if current_verse and current_text:
                verses[current_verse] = ' '.join(current_text).strip()

            try:
                current_chapter = int(line.split()[1])
            except (IndexError, ValueError):
                continue
            current_verse = ""
            current_text = []
            continue

        # Skip if filtering by chapter and not in target chapter
        if chapter is not None and current_chapter != chapter:
            continue

        # Verse marker
        verse_match = re.match(r'\\v\s+(\d+(?:-\d+)?)\s*(.*)', line)
        if verse_match:
            # Save previous verse
            if current_verse and current_text:
                verses[current_verse] = ' '.join(current_text).strip()

            verse_num = verse_match.group(1)
            current_verse = f"{current_chapter}:{verse_num}"
            remaining = verse_match.group(2)
            current_text = [clean_usfm(remaining)] if remaining else []
            continue

        # Skip header/metadata lines
        if line.startswith('\\id ') or line.startswith('\\h ') or line.startswith('\\toc'):
            continue
        if line.startswith('\\mt') or line.startswith('\\ms'):
            continue

        # Paragraph/poetry markers - just clean and add text
        if current_verse:
            cleaned = clean_usfm(line)
            if cleaned:
                current_text.append(cleaned)

    # Don't forget last verse
    if current_verse and current_text:
        verses[current_verse] = ' '.join(current_text).strip()

    return verses

def clean_usfm(text: str) -> str:
    """Remove USFM markers from text, keeping content."""
    # Remove common markers
    text = re.sub(r'\\[pqsm]\d?\s*', '', text)
    text = re.sub(r'\\d\s*', '', text)
    text = re.sub(r'\\b\s*', '', text)
    text = re.sub(r'\\r\s*', '', text)
    text = re.sub(r'\\f\s+.*?\\f\*', '', text)  # footnotes
    text = re.sub(r'\\x\s+.*?\\x\*', '', text)  # cross-refs
    text = re.sub(r'\\[a-z]+\*?', '', text)  # remaining markers
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def analyze_difference(ult_text: str, ust_text: str) -> tuple:
    """
    Analyze the difference between ULT and UST text.

    Returns (diff_type, suggested_issue, confidence)
    """
    if not ult_text or not ust_text:
        return ('missing', '', 0.0)

    ult_words = ult_text.lower().split()
    ust_words = ust_text.lower().split()

    # Calculate similarity
    matcher = SequenceMatcher(None, ult_words, ust_words)
    similarity = matcher.ratio()

    # Very similar - probably just synonym changes
    if similarity > 0.85:
        return ('minimal', '', 0.1)

    # Check for specific patterns

    # 1. Added words (UST longer) -> figs-explicit
    if len(ust_words) > len(ult_words) * 1.3:
        return ('added_words', 'figs-explicit', 0.7)

    # 2. Removed repetition (UST shorter with repeated elements in ULT)
    if len(ust_words) < len(ult_words) * 0.7:
        # Check for repeated words in ULT
        ult_unique = set(ult_words)
        if len(ult_unique) < len(ult_words) * 0.8:
            return ('removed_repetition', 'figs-doublet', 0.6)
        return ('condensed', 'figs-parallelism', 0.5)

    # 3. Voice change detection (passive -> active indicators)
    passive_markers = ['was', 'were', 'been', 'being', 'is', 'are']
    ult_has_passive = any(w in ult_words for w in passive_markers)
    ust_has_passive = any(w in ust_words for w in passive_markers)
    if ult_has_passive and not ust_has_passive:
        return ('voice_change', 'figs-activepassive', 0.6)

    # 4. Metaphor replacement (look for "like" or "as" changes)
    ult_has_comparison = any(w in ult_words for w in ['like', 'as'])
    ust_has_comparison = any(w in ust_words for w in ['like', 'as'])
    if ult_has_comparison != ust_has_comparison:
        if ult_has_comparison:
            return ('removed_comparison', 'figs-simile', 0.5)
        else:
            return ('added_comparison', 'figs-metaphor', 0.5)

    # 5. Significant restructuring (different word order)
    # Check if many words present in both but in different positions
    common = set(ult_words) & set(ust_words)
    if len(common) > min(len(ult_words), len(ust_words)) * 0.5:
        # Many words in common but low similarity = restructured
        if similarity < 0.6:
            return ('restructured', 'figs-infostructure', 0.6)

    # 6. Abstract noun unpacking (UST longer with same key terms)
    abstract_indicators = ['ness', 'tion', 'ment', 'ity', 'ance', 'ence']
    ult_abstracts = [w for w in ult_words if any(w.endswith(s) for s in abstract_indicators)]
    if ult_abstracts and len(ust_words) > len(ult_words):
        return ('unpacked_abstract', 'figs-abstractnouns', 0.5)

    # 7. Idiom expansion (UST significantly longer for short ULT phrase)
    if len(ult_words) <= 5 and len(ust_words) > len(ult_words) * 2:
        return ('expanded_phrase', 'figs-idiom', 0.5)

    # Default: significant difference but unclear type
    if similarity < 0.5:
        return ('divergent', '', 0.4)

    return ('moderate', '', 0.3)

def compare_verses(ult_verses: dict, ust_verses: dict) -> list:
    """
    Compare ULT and UST verse by verse.

    Returns list of dicts with comparison results.
    """
    results = []

    # Get all verses from both
    all_verses = sorted(set(ult_verses.keys()) | set(ust_verses.keys()),
                       key=lambda v: (int(v.split(':')[0]),
                                     int(v.split(':')[1].split('-')[0])))

    for verse in all_verses:
        ult_text = ult_verses.get(verse, '')
        ust_text = ust_verses.get(verse, '')

        diff_type, suggested, confidence = analyze_difference(ult_text, ust_text)

        # Skip minimal differences
        if diff_type == 'minimal':
            continue

        results.append({
            'verse': verse,
            'ult_text': ult_text,
            'ust_text': ust_text,
            'diff_type': diff_type,
            'suggested_issue': suggested,
            'confidence': confidence
        })

    return results

def format_tsv(results: list) -> str:
    """Format results as TSV."""
    lines = ['verse\tult_text\tust_text\tdiff_type\tsuggested_issue']
    for r in results:
        # Truncate long texts for readability
        ult = r['ult_text'][:100] + '...' if len(r['ult_text']) > 100 else r['ult_text']
        ust = r['ust_text'][:100] + '...' if len(r['ust_text']) > 100 else r['ust_text']
        lines.append(f"{r['verse']}\t{ult}\t{ust}\t{r['diff_type']}\t{r['suggested_issue']}")
    return '\n'.join(lines)

def format_json(results: list) -> str:
    """Format results as JSON."""
    return json.dumps(results, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description='Compare ULT and UST to identify translation issues',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /tmp/ult.usfm /tmp/ust.usfm
  %(prog)s /tmp/ult.usfm /tmp/ust.usfm --chapter 58
  %(prog)s /tmp/ult.usfm /tmp/ust.usfm --output diff.tsv
"""
    )
    parser.add_argument('ult_file', help='Path to ULT USFM file')
    parser.add_argument('ust_file', help='Path to UST USFM file')
    parser.add_argument('--chapter', '-c', type=int, help='Filter to specific chapter')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--format', '-f', choices=['tsv', 'json'], default='tsv',
                       help='Output format (default: tsv)')

    args = parser.parse_args()

    # Read files
    try:
        with open(args.ult_file, 'r', encoding='utf-8') as f:
            ult_content = f.read()
    except FileNotFoundError:
        print(f"Error: ULT file not found: {args.ult_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.ust_file, 'r', encoding='utf-8') as f:
            ust_content = f.read()
    except FileNotFoundError:
        print(f"Error: UST file not found: {args.ust_file}", file=sys.stderr)
        sys.exit(1)

    # Parse verses
    ult_verses = parse_usfm_verses(ult_content, args.chapter)
    ust_verses = parse_usfm_verses(ust_content, args.chapter)

    if not ult_verses:
        print("Warning: No verses found in ULT file", file=sys.stderr)
    if not ust_verses:
        print("Warning: No verses found in UST file", file=sys.stderr)

    # Compare
    results = compare_verses(ult_verses, ust_verses)

    # Format output
    if args.format == 'json':
        output = format_json(results)
    else:
        output = format_tsv(results)

    # Write output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Wrote {len(results)} differences to {args.output}", file=sys.stderr)
    else:
        print(output)

if __name__ == '__main__':
    main()
