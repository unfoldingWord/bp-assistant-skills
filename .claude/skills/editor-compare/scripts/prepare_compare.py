#!/usr/bin/env python3
"""
prepare_compare.py - Prepare verse-by-verse comparison between editor and AI USFM

Compares editor-edited text (from Door43 master or editor-feedback files) against
AI-generated output, producing structured JSON for analysis.

Usage:
  python3 prepare_compare.py PSA 65 --type ult
  python3 prepare_compare.py PSA 66 --type ult --editor-file "data/editor-feedback/Psalm 66 ULT.usfm"
  python3 prepare_compare.py PSA 67 --type ult --output /tmp/claude/compare.json

Editor source resolution (in order):
  1. --editor-file if provided
  2. Local git clone at $DOOR43_REPOS_PATH/en_{type}/ (from .env)
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

from extract_ult_english import strip_alignment_markers
from fetch_door43 import BOOK_NUMBERS, normalize_book, get_filename, build_url, fetch_usfm


def load_env():
    """Read .env file from project root, return dict of key=value pairs."""
    env = {}
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def extract_chapter(content, chapter_num):
    """Extract a single chapter from full-book USFM content.

    Returns the text from \\c N up to the next \\c or end of file.
    """
    pattern = rf"\\c\s+{chapter_num}\b"
    match = re.search(pattern, content)
    if not match:
        return None

    start = match.start()
    # Find next \c marker
    next_c = re.search(r"\\c\s+\d+", content[match.end():])
    if next_c:
        end = match.end() + next_c.start()
    else:
        end = len(content)

    return content[start:end]


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

    # Filter out blank lines, return cleaned text
    lines = [l.strip() for l in preamble.splitlines() if l.strip()]
    if not lines:
        return None

    return "\n".join(lines)


def parse_verses(chapter_text):
    """Parse \\v markers from chapter text into {verse_num: plain_text} dict.

    Strips USFM formatting markers to produce plain text for comparison.
    """
    verses = {}

    # Split on \v markers
    parts = re.split(r"\\v\s+(\d+)\s+", chapter_text)
    # parts[0] is before first \v (chapter header, \d, etc.)
    # Then alternating: verse_num, verse_text, verse_num, verse_text...

    for i in range(1, len(parts) - 1, 2):
        verse_num = int(parts[i])
        verse_text = parts[i + 1]

        # Strip USFM formatting markers but keep text content
        plain = strip_usfm_to_plain(verse_text)
        verses[verse_num] = plain

    return verses


def strip_usfm_to_plain(text):
    """Strip USFM formatting markers, leaving plain text with {implied} words."""
    # Remove \qs ...\qs* (Selah markers) - keep the text inside
    text = re.sub(r"\\qs\s*\*?", "", text)
    text = re.sub(r"\\qs\*", "", text)

    # Remove \ts\* markers
    text = re.sub(r"\\ts\\\*", "", text)

    # Remove common formatting markers: \q1, \q2, \q, \p, \m, \d, \b, \nb, \pi
    text = re.sub(r"\\(?:q[12]?|p|m|d|b|nb|pi|li\d?|s\d?)\s*", "", text)

    # Remove \f ... \f* (footnotes)
    text = re.sub(r"\\f\s.*?\\f\*", "", text)

    # Remove remaining backslash markers we might have missed
    text = re.sub(r"\\[a-z]+\d?\s*\*?", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


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


def resolve_editor_source(book, chapter, text_type, editor_file=None):
    """Resolve editor USFM content. Returns (content, source_label).

    Resolution order:
    1. --editor-file if provided
    2. Local git clone (with git pull)
    3. HTTP fetch from Door43
    """
    normalized = normalize_book(book)
    filename = get_filename(book)
    repo_name = f"en_{text_type}"

    # 1. Explicit editor file
    if editor_file:
        if not os.path.exists(editor_file):
            print(f"Error: Editor file not found: {editor_file}", file=sys.stderr)
            sys.exit(1)
        with open(editor_file, "r", encoding="utf-8") as f:
            return f.read(), "editor_file"

    # 2. Local git clone
    env = load_env()
    repos_path = env.get("DOOR43_REPOS_PATH")
    if repos_path:
        local_repo = os.path.join(repos_path, repo_name)
        local_file = os.path.join(local_repo, filename)
        if os.path.isdir(local_repo):
            # Pull latest
            try:
                subprocess.run(
                    ["git", "-C", local_repo, "pull"],
                    capture_output=True, timeout=30
                )
            except Exception as e:
                print(f"Warning: git pull failed for {local_repo}: {e}", file=sys.stderr)

            if os.path.exists(local_file):
                with open(local_file, "r", encoding="utf-8") as f:
                    return f.read(), "local_clone"

    # 3. HTTP fetch
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
""",
    )
    parser.add_argument("book", help="Book abbreviation (e.g., PSA, GEN, 1JN)")
    parser.add_argument("chapter", type=int, help="Chapter number")
    parser.add_argument("--type", "-t", default="ult", choices=["ult", "ust"],
                        help="Text type (default: ult)")
    parser.add_argument("--output", "-o", help="Output JSON path (default: stdout)")
    parser.add_argument("--editor-file", help="Explicit path to editor USFM file")

    args = parser.parse_args()

    normalized_book = normalize_book(args.book)

    # Resolve editor source
    editor_raw, source = resolve_editor_source(
        args.book, args.chapter, args.type, args.editor_file
    )

    # Extract prose comments (only meaningful for editor-feedback files)
    editor_comments = None
    if args.editor_file:
        editor_comments = extract_prose_comments(editor_raw, args.chapter)

    # Strip alignment markers (master has zaln markers; no-op if already plain)
    editor_clean = strip_alignment_markers(editor_raw)

    # Extract target chapter from editor
    editor_chapter = extract_chapter(editor_clean, args.chapter)
    if not editor_chapter:
        print(f"Error: Chapter {args.chapter} not found in editor source", file=sys.stderr)
        sys.exit(1)

    # Read AI source
    ai_raw = resolve_ai_source(args.book, args.chapter, args.type)
    ai_chapter = extract_chapter(ai_raw, args.chapter)
    if not ai_chapter:
        print(f"Error: Chapter {args.chapter} not found in AI output", file=sys.stderr)
        sys.exit(1)

    # Parse verses
    editor_verses = parse_verses(editor_chapter)
    ai_verses = parse_verses(ai_chapter)

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
        os.makedirs(os.path.dirname(args.output), exist_ok=True) if os.path.dirname(args.output) else None
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
