#!/usr/bin/env python3
"""
prepare_compare.py - Prepare verse-by-verse comparison between editor and AI USFM

Compares editor-edited text (from Door43 master or editor-feedback files) against
AI-generated output, producing structured JSON for analysis.

Uses parse_usfm.js (AST-based) for USFM plain text extraction instead of regex.

Usage:
  python3 prepare_compare.py PSA 65 --type ult
  python3 prepare_compare.py PSA 66 --type ult --editor-file "data/editor-feedback/Psalm 66 ULT.usfm"
  python3 prepare_compare.py PSA 67 --type ult --output /tmp/claude/compare.json
  python3 prepare_compare.py PSA 81 --type ult --editor-usfm /tmp/claude/editor_ult.usfm

Editor source resolution (in order):
  1. --editor-file if provided (editor-feedback file with possible prose comments)
  2. --editor-usfm if provided (pre-fetched full-book USFM, for multi-chapter mode)
  3. HTTP fetch from unfoldingWord/en_{type} master
"""

import argparse
import difflib
import json
import os
import re
import subprocess
import sys

# Resolve project root and add utilities to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILLS_DIR = os.path.dirname(SKILL_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(SKILLS_DIR))

UTILITIES_SCRIPTS = os.path.join(SKILLS_DIR, "utilities", "scripts")
sys.path.insert(0, UTILITIES_SCRIPTS)

PARSE_USFM_JS = os.path.join(SKILLS_DIR, "utilities", "scripts", "usfm", "parse_usfm.js")

from fetch_door43 import normalize_book, fetch_usfm


def usfm_to_verses(usfm_content, chapter_num):
    """Convert USFM content to {verse_num_int: plain_text} dict using parse_usfm.js.

    Pipes content through `node parse_usfm.js --stdin --plain-only --chapter N`
    and parses the plain text output into a verse dictionary.

    Handles both aligned USFM (with \\zaln markers) and unaligned USFM.
    """
    result = subprocess.run(
        ["node", PARSE_USFM_JS, "--stdin", "--plain-only", "--chapter", str(chapter_num)],
        input=usfm_content, capture_output=True, text=True, timeout=30
    )

    if result.returncode != 0:
        print(f"Warning: parse_usfm.js stderr: {result.stderr}", file=sys.stderr)
        if not result.stdout.strip():
            return {}

    return _parse_plain_verses(result.stdout)


def _parse_plain_verses(plain_output):
    """Parse plain USFM output from parse_usfm.js into {verse_int: text} dict.

    Adapted from compare_ult_ust.py:parse_plain_usfm_verses(). Filters out
    \\v front pseudo-verse (psalm superscriptions).
    """
    verses = {}
    current_verse = None
    current_text = []

    for line in plain_output.split('\n'):
        line = line.strip()

        # Skip chapter/paragraph markers
        if line.startswith('\\c ') or line.startswith('\\p'):
            continue

        # Verse marker
        verse_match = re.match(r'\\v\s+(\S+)\s*(.*)', line)
        if verse_match:
            # Save previous verse
            if current_verse is not None and current_text:
                verses[current_verse] = ' '.join(current_text).strip()

            verse_id = verse_match.group(1)

            # Filter out \v front (psalm superscription pseudo-verse)
            if verse_id == 'front':
                current_verse = None
                current_text = []
                continue

            try:
                current_verse = int(verse_id.split('-')[0])
            except ValueError:
                current_verse = None
                current_text = []
                continue

            remaining = verse_match.group(2)
            current_text = [_clean_plain(remaining)] if remaining else []
            continue

        # Continuation lines (poetry markers, etc.)
        if current_verse is not None:
            cleaned = _clean_plain(line)
            if cleaned:
                current_text.append(cleaned)

    # Don't forget last verse
    if current_verse is not None and current_text:
        verses[current_verse] = ' '.join(current_text).strip()

    return verses


def _clean_plain(text):
    """Strip residual USFM markers from parse_usfm.js plain output."""
    # Remove Selah markers: \qs...\qs* (paired) then \qs (unpaired from parse_usfm.js)
    text = re.sub(r'\\qs\s+(.*?)\\qs\*', r'\1', text)
    text = re.sub(r'\\qs\s+', '', text)
    # Remove paragraph/poetry/section markers (\p, \q1, \q2, \s, \m, \d, \b, \r)
    text = re.sub(r'\\[pqsmd]\d?\s*', '', text)
    text = re.sub(r'\\b\s*', '', text)
    text = re.sub(r'\\r\s*', '', text)
    # Remove footnotes and cross-references
    text = re.sub(r'\\f\s+.*?\\f\*', '', text)
    text = re.sub(r'\\x\s+.*?\\x\*', '', text)
    # Catch-all for remaining markers
    text = re.sub(r'\\[a-z]+\*?', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_prose_comments(content, chapter_num):
    """Extract prose comments before the first \\c marker in editor-feedback files.

    Editor-feedback files may have free-text notes before the USFM begins.
    Returns the comment text or None.
    """
    first_c = re.search(r"\\c\s+\d+", content)
    if not first_c:
        return None

    preamble = content[:first_c.start()].strip()
    if not preamble:
        return None

    lines = [l.strip() for l in preamble.splitlines() if l.strip()]
    if not lines:
        return None

    return "\n".join(lines)


def word_diff(ai_text, editor_text):
    """Compute word-level diff between AI and editor text.

    Returns list of diff operations: ('equal'|'replace'|'insert'|'delete', ai_words, editor_words)
    """
    ai_words = ai_text.split()
    ed_words = editor_text.split()

    sm = difflib.SequenceMatcher(None, ai_words, ed_words)
    ops = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        ops.append({
            "op": tag,
            "ai_words": ai_words[i1:i2],
            "editor_words": ed_words[j1:j2],
        })
    return ops


def resolve_editor_source(book, chapter, text_type, editor_file=None, editor_usfm=None):
    """Resolve editor USFM content. Returns (content, source_label).

    Resolution order:
    1. --editor-file if provided (editor-feedback file)
    2. --editor-usfm if provided (pre-fetched full-book USFM)
    3. HTTP fetch from unfoldingWord/en_{type} master
    """
    repo_name = f"en_{text_type}"

    # 1. Explicit editor-feedback file
    if editor_file:
        if not os.path.exists(editor_file):
            print(f"Error: Editor file not found: {editor_file}", file=sys.stderr)
            sys.exit(1)
        with open(editor_file, "r", encoding="utf-8") as f:
            return f.read(), "editor_file"

    # 2. Pre-fetched full-book USFM (multi-chapter mode)
    if editor_usfm:
        if not os.path.exists(editor_usfm):
            print(f"Error: Editor USFM file not found: {editor_usfm}", file=sys.stderr)
            sys.exit(1)
        with open(editor_usfm, "r", encoding="utf-8") as f:
            return f.read(), "pre_fetched"

    # 3. HTTP fetch from unfoldingWord Door43 master
    try:
        content = fetch_usfm(book, repo=repo_name, branch="master")
        return content, "http_fetch"
    except Exception as e:
        print(f"Error: Could not fetch editor USFM: {e}", file=sys.stderr)
        sys.exit(1)


def resolve_ai_source(book, chapter, text_type):
    """Read AI-generated USFM from output directory.

    Expected path: output/AI-{ULT|UST}/{BOOK}/{BOOK}-{CHAPTER:03d}.usfm
    """
    normalized = normalize_book(book)
    type_upper = text_type.upper()
    filename = f"{normalized}-{int(chapter):03d}.usfm"
    ai_path = os.path.join(PROJECT_ROOT, "output", f"AI-{type_upper}", normalized, filename)

    if not os.path.exists(ai_path):
        print(f"Error: AI output not found: {ai_path}", file=sys.stderr)
        sys.exit(1)

    with open(ai_path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(
        description="Prepare verse-by-verse comparison between editor and AI USFM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s PSA 65 --type ult
  %(prog)s PSA 66 --type ult --editor-file "data/editor-feedback/Psalm 66 ULT.usfm"
  %(prog)s PSA 67 --type ult --output /tmp/claude/compare.json
  %(prog)s PSA 81 --type ult --editor-usfm /tmp/claude/editor_ult.usfm
""",
    )
    parser.add_argument("book", help="Book abbreviation (e.g., PSA, GEN, 1JN)")
    parser.add_argument("chapter", type=int, help="Chapter number")
    parser.add_argument("--type", "-t", default="ult", choices=["ult", "ust"],
                        help="Text type (default: ult)")
    parser.add_argument("--output", "-o", help="Output JSON path (default: stdout)")
    parser.add_argument("--editor-file", help="Explicit path to editor-feedback USFM file")
    parser.add_argument("--editor-usfm",
                        help="Path to pre-fetched full-book editor USFM (multi-chapter mode)")

    args = parser.parse_args()

    normalized_book = normalize_book(args.book)

    # Resolve editor source
    editor_raw, source = resolve_editor_source(
        args.book, args.chapter, args.type, args.editor_file, args.editor_usfm
    )

    # Extract prose comments (only meaningful for editor-feedback files)
    editor_comments = None
    if args.editor_file:
        editor_comments = extract_prose_comments(editor_raw, args.chapter)

    # Parse verses via parse_usfm.js (handles aligned and unaligned USFM)
    editor_verses = usfm_to_verses(editor_raw, args.chapter)
    if not editor_verses:
        print(f"Error: No verses found for chapter {args.chapter} in editor source",
              file=sys.stderr)
        sys.exit(1)

    # Read AI source and parse verses
    ai_raw = resolve_ai_source(args.book, args.chapter, args.type)
    ai_verses = usfm_to_verses(ai_raw, args.chapter)
    if not ai_verses:
        print(f"Error: No verses found for chapter {args.chapter} in AI output",
              file=sys.stderr)
        sys.exit(1)

    # Build comparison
    all_verse_nums = sorted(set(list(editor_verses.keys()) + list(ai_verses.keys())))
    verses_output = []
    changed_count = 0
    unchanged_count = 0

    for v in all_verse_nums:
        ai_text = ai_verses.get(v, "")
        ed_text = editor_verses.get(v, "")

        changed = ai_text != ed_text
        if changed:
            changed_count += 1
        else:
            unchanged_count += 1

        verse_entry = {
            "verse": v,
            "ai": ai_text,
            "editor": ed_text,
            "changed": changed,
        }

        # Include word diff for changed verses
        if changed and ai_text and ed_text:
            verse_entry["diff"] = word_diff(ai_text, ed_text)

        verses_output.append(verse_entry)

    result = {
        "book": normalized_book,
        "chapter": args.chapter,
        "type": args.type,
        "source": source,
        "editor_comments": editor_comments,
        "verses": verses_output,
        "summary": {
            "total": len(all_verse_nums),
            "changed": changed_count,
            "unchanged": unchanged_count,
        },
    }

    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        if os.path.dirname(args.output):
            os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
