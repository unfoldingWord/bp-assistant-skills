#!/usr/bin/env python3
"""
build_tn_index.py - Build an index of published translation notes by issue type
and keyword for fast agent lookups.

Parses all data/published-tns/tn_*.tsv files in a single pass. Builds two indexes:
  - by_issue: issue type -> count, books, sample notes
  - by_keyword: content word -> [{issue, count, sample_ref}]

Usage:
    python3 build_tn_index.py              # Build if stale (daily check)
    python3 build_tn_index.py --force       # Force rebuild
    python3 build_tn_index.py --issue figs-metaphor  # List examples for an issue type
    python3 build_tn_index.py --lookup "hand"        # Find how a keyword was classified
    python3 build_tn_index.py --stats       # Summary statistics

Output: data/cache/tn_index.json (~2-4MB vs 28MB source TSVs)
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date

# Paths relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
SOURCE_DIR = os.path.join(PROJECT_ROOT, "data", "published-tns")
CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "cache")
INDEX_PATH = os.path.join(CACHE_DIR, "tn_index.json")

MAX_SAMPLES = 5          # Sample notes per issue type
MAX_KEYWORD_ISSUES = 10  # Top-N issue types per keyword
MIN_KEYWORD_LEN = 3      # Skip very short words

# Common function words to skip when extracting keywords
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "shall", "should", "may", "might", "can", "could", "not",
    "no", "nor", "so", "if", "then", "than", "that", "this", "these",
    "those", "it", "its", "he", "him", "his", "she", "her", "hers",
    "they", "them", "their", "theirs", "we", "us", "our", "ours",
    "you", "your", "yours", "i", "me", "my", "mine", "who", "whom",
    "whose", "which", "what", "when", "where", "how", "why", "all",
    "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "only", "own", "same", "also", "very", "just", "about",
    "up", "out", "into", "over", "after", "before", "between", "under",
    "again", "there", "here", "once", "during", "while", "through",
    "because", "until", "against", "above", "below", "down", "off",
    "any", "too", "now", "even", "still", "yet", "already", "always",
    "never", "often", "sometimes", "much", "many", "well", "back",
    "away", "upon", "among", "along", "across", "around", "within",
    "without", "toward", "towards", "whether", "though", "although",
    "however", "therefore", "thus", "hence", "else", "instead",
    "rather", "quite", "perhaps", "certainly", "indeed", "especially",
    "merely", "simply", "actually", "apparently", "anyway",
}


def extract_issue_type(support_ref):
    """Extract issue type from SupportReference like 'rc://*/ta/man/translate/figs-metaphor'."""
    if not support_ref:
        return None
    # Strip the rc:// URI prefix
    m = re.search(r'translate/(.+)$', support_ref)
    if m:
        return m.group(1)
    # If no URI prefix, it might already be bare
    if support_ref.startswith("figs-") or support_ref.startswith("grammar-") or \
       support_ref.startswith("writing-") or support_ref.startswith("translate-"):
        return support_ref
    return None


def extract_keywords(text):
    """Extract content words from GLQuote text. Returns set of lowercased words."""
    if not text:
        return set()
    # Remove punctuation, split on whitespace
    words = re.findall(r"[a-zA-Z']+", text.lower())
    # Filter stop words and short words
    return {w for w in words if w not in STOP_WORDS and len(w) >= MIN_KEYWORD_LEN}


def parse_reference_format(row, header_fields, filename):
    """Parse a TSV row based on the detected header format.
    Returns (book, ref_str, issue_type, gl_quote, note_preview) or None."""

    if len(row) < len(header_fields):
        return None

    field_map = {h: i for i, h in enumerate(header_fields)}

    # Detect format: PSA/RUT use Book,Chapter,Verse; others use Reference
    if "Book" in field_map:
        # PSA/RUT format: Book, Chapter, Verse, ID, SupportReference, OrigQuote, Occurrence, GLQuote, OccurrenceNote
        book = row[field_map["Book"]]
        chapter = row[field_map.get("Chapter", 1)]
        verse = row[field_map.get("Verse", 2)]
        ref_str = f"{chapter}:{verse}"
        support_ref = row[field_map.get("SupportReference", 4)]
        # GLQuote may not exist in this format -- check for it
        gl_quote_idx = field_map.get("GLQuote", None)
        gl_quote = row[gl_quote_idx] if gl_quote_idx is not None and gl_quote_idx < len(row) else ""
        note_idx = field_map.get("OccurrenceNote", field_map.get("Note", None))
        note = row[note_idx] if note_idx is not None and note_idx < len(row) else ""
    else:
        # Standard format: Reference, ID, Tags, SupportReference, Quote, Occurrence, GLQuote, GLOccurrence, Note
        book = os.path.basename(filename).replace("tn_", "").replace(".tsv", "")
        ref_str = row[field_map.get("Reference", 0)]
        support_ref = row[field_map.get("SupportReference", 3)]
        gl_quote_idx = field_map.get("GLQuote", None)
        gl_quote = row[gl_quote_idx] if gl_quote_idx is not None and gl_quote_idx < len(row) else ""
        note_idx = field_map.get("Note", None)
        note = row[note_idx] if note_idx is not None and note_idx < len(row) else ""

    # Skip intro rows
    if "intro" in ref_str:
        return None

    issue_type = extract_issue_type(support_ref)
    if not issue_type:
        return None

    # Truncate note preview to first 120 chars
    note_preview = ""
    if note:
        # Unescape TSV newlines
        clean = note.replace("\\n", " ").strip()
        # Remove markdown links
        clean = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', clean)
        # Remove rc:// links
        clean = re.sub(r'\[\[rc://[^\]]*\]\]', '', clean)
        note_preview = clean[:120].strip()

    return (book, ref_str, issue_type, gl_quote, note_preview)


def parse_file(filepath):
    """Parse a single TN TSV file. Returns list of parsed records."""
    records = []
    filename = os.path.basename(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return records

    # Parse header
    header_fields = lines[0].strip().split("\t")

    for line in lines[1:]:
        row = line.strip().split("\t")
        result = parse_reference_format(row, header_fields, filepath)
        if result:
            records.append(result)

    return records


def build_index(source_dir):
    """Parse all TN TSV files and build the aggregated index."""
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(f for f in os.listdir(source_dir) if f.startswith("tn_") and f.endswith(".tsv"))
    if not files:
        print(f"Error: No tn_*.tsv files in {source_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {len(files)} TN files from {source_dir}")

    # Aggregation structures
    # by_issue: issue -> {count, books(set), samples[]}
    issue_agg = defaultdict(lambda: {"count": 0, "books": set(), "samples": []})
    # by_keyword: keyword -> {issue -> {count, sample_ref}}
    keyword_agg = defaultdict(lambda: defaultdict(lambda: {"count": 0, "sample_ref": ""}))

    total_notes = 0

    for filename in files:
        filepath = os.path.join(source_dir, filename)
        records = parse_file(filepath)
        total_notes += len(records)
        print(f"  {filename}: {len(records)} notes with issue types")

        for book, ref_str, issue_type, gl_quote, note_preview in records:
            full_ref = f"{book} {ref_str}"

            # Aggregate by issue
            entry = issue_agg[issue_type]
            entry["count"] += 1
            entry["books"].add(book)
            if len(entry["samples"]) < MAX_SAMPLES:
                entry["samples"].append({
                    "ref": full_ref,
                    "quote": gl_quote[:80] if gl_quote else "",
                    "note_preview": note_preview,
                })

            # Aggregate by keyword (from GLQuote)
            keywords = extract_keywords(gl_quote)
            for kw in keywords:
                kw_entry = keyword_agg[kw][issue_type]
                kw_entry["count"] += 1
                if not kw_entry["sample_ref"]:
                    kw_entry["sample_ref"] = full_ref

    # Build output
    index = {
        "_meta": {
            "built": date.today().isoformat(),
            "source_dir": "data/published-tns/",
            "file_count": len(files),
            "total_notes": total_notes,
            "unique_issues": len(issue_agg),
            "unique_keywords": len(keyword_agg),
        },
        "by_issue": {},
        "by_keyword": {},
    }

    # Sort issues by count desc
    for issue, data in sorted(issue_agg.items(), key=lambda x: -x[1]["count"]):
        index["by_issue"][issue] = {
            "count": data["count"],
            "books": sorted(data["books"]),
            "samples": data["samples"],
        }

    # Sort keywords alphabetically, keep top-N issues per keyword by count
    for kw in sorted(keyword_agg.keys()):
        issues = keyword_agg[kw]
        top_issues = sorted(issues.items(), key=lambda x: -x[1]["count"])[:MAX_KEYWORD_ISSUES]
        # Only include keywords that appear with at least 2 notes total
        total = sum(info["count"] for _, info in top_issues)
        if total < 2:
            continue
        index["by_keyword"][kw] = [
            {"issue": issue, "count": info["count"], "sample_ref": info["sample_ref"]}
            for issue, info in top_issues
        ]

    # Update meta with final keyword count (after filtering)
    index["_meta"]["unique_keywords"] = len(index["by_keyword"])

    return index


def is_stale():
    """Check if the index needs rebuilding. Returns (stale: bool, reason: str)."""
    if not os.path.exists(INDEX_PATH):
        return True, "index does not exist"

    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            idx = json.load(f)
        meta = idx.get("_meta", {})
        built = meta.get("built", "")
    except (json.JSONDecodeError, KeyError):
        return True, "index is corrupt"

    # Check if built today already
    today = date.today().isoformat()
    if built == today:
        return False, f"built today ({today})"

    # Check if source files changed (count mismatch)
    if os.path.isdir(SOURCE_DIR):
        source_count = len([f for f in os.listdir(SOURCE_DIR) if f.startswith("tn_") and f.endswith(".tsv")])
    else:
        source_count = 0
    if source_count != meta.get("file_count", 0):
        return True, f"file count changed ({meta.get('file_count', '?')} -> {source_count})"

    return False, f"up to date (built {built})"


def do_build(force=False):
    """Build the index, with staleness check unless forced."""
    if not force:
        stale, reason = is_stale()
        if not stale:
            print(f"Index is {reason}. Use --force to rebuild.")
            return

    os.makedirs(CACHE_DIR, exist_ok=True)
    index = build_index(SOURCE_DIR)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    size_mb = os.path.getsize(INDEX_PATH) / (1024 * 1024)
    meta = index["_meta"]
    print(f"\nIndex built: {INDEX_PATH}")
    print(f"  Files: {meta['file_count']}")
    print(f"  Notes with issue types: {meta['total_notes']}")
    print(f"  Unique issue types: {meta['unique_issues']}")
    print(f"  Unique keywords: {meta['unique_keywords']}")
    print(f"  Size: {size_mb:.2f} MB")


def load_index():
    """Load the index, with helpful error if missing."""
    if not os.path.exists(INDEX_PATH):
        print(f"Error: Index not found at {INDEX_PATH}", file=sys.stderr)
        print("Run: python3 build_tn_index.py  (to build)", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def do_issue(issue_type):
    """Look up examples for a specific issue type."""
    index = load_index()
    by_issue = index.get("by_issue", {})

    # Try exact match, then partial match
    if issue_type in by_issue:
        matches = [issue_type]
    else:
        matches = sorted(k for k in by_issue if issue_type.lower() in k.lower())

    if not matches:
        print(f"No entries for '{issue_type}' in index.")
        print(f"\nAvailable issue types ({len(by_issue)}):")
        for k in sorted(by_issue.keys()):
            print(f"  {k} ({by_issue[k]['count']})")
        sys.exit(0)

    for issue in matches:
        data = by_issue[issue]
        print(f"Issue: {issue}")
        print(f"  Total notes: {data['count']}")
        print(f"  Books ({len(data['books'])}): {', '.join(data['books'][:15])}")
        if len(data['books']) > 15:
            print(f"    ... and {len(data['books']) - 15} more")
        print(f"  Samples:")
        for s in data["samples"]:
            quote = s.get("quote", "")
            preview = s.get("note_preview", "")
            print(f"    {s['ref']:15s}  \"{quote}\"")
            if preview:
                print(f"{'':19s}{preview[:100]}")
        if issue != matches[-1]:
            print()


def do_lookup(keyword):
    """Look up how a keyword was classified in published notes."""
    index = load_index()
    by_keyword = index.get("by_keyword", {})

    kw_lower = keyword.lower().strip()

    # Try exact match first
    if kw_lower in by_keyword:
        matches = {kw_lower: by_keyword[kw_lower]}
    else:
        # Partial match
        matches = {k: v for k, v in by_keyword.items() if kw_lower in k}

    if not matches:
        print(f"No entries for '{keyword}' in keyword index.")
        # Suggest similar
        close = sorted(
            (k for k in by_keyword if k.startswith(kw_lower[:3])),
            key=lambda k: -sum(e["count"] for e in by_keyword[k])
        )[:10]
        if close:
            print(f"\nSimilar keywords: {', '.join(close)}")
        sys.exit(0)

    for kw, entries in sorted(matches.items()):
        total = sum(e["count"] for e in entries)
        print(f"Keyword: \"{kw}\" ({total} total notes)")
        for e in entries:
            pct = (e["count"] / total * 100) if total > 0 else 0
            print(f"  {e['issue']:40s}  {e['count']:4d}  ({pct:5.1f}%)  [{e['sample_ref']}]")
        if kw != list(matches.keys())[-1]:
            print()


def do_stats():
    """Print summary statistics from the index."""
    index = load_index()
    meta = index.get("_meta", {})
    size_mb = os.path.getsize(INDEX_PATH) / (1024 * 1024)

    print("Published TN Index Statistics")
    print("=" * 50)
    print(f"  Built:            {meta.get('built', '?')}")
    print(f"  Source:           {meta.get('source_dir', '?')}")
    print(f"  Source files:     {meta.get('file_count', '?')}")
    print(f"  Notes (w/ issue): {meta.get('total_notes', '?')}")
    print(f"  Unique issues:    {meta.get('unique_issues', '?')}")
    print(f"  Unique keywords:  {meta.get('unique_keywords', '?')}")
    print(f"  Index size:       {size_mb:.2f} MB")

    by_issue = index.get("by_issue", {})
    if by_issue:
        print(f"\nTop 15 issue types by frequency:")
        for issue, data in list(by_issue.items())[:15]:
            book_count = len(data.get("books", []))
            print(f"  {issue:40s}  {data['count']:5d} notes  ({book_count} books)")

    by_keyword = index.get("by_keyword", {})
    if by_keyword:
        # Find keywords with most diverse issue classifications
        diverse = sorted(
            by_keyword.items(),
            key=lambda x: (-len(x[1]), -sum(e["count"] for e in x[1]))
        )[:10]
        print(f"\nTop 10 keywords by issue-type diversity:")
        for kw, entries in diverse:
            total = sum(e["count"] for e in entries)
            issues = ", ".join(e["issue"] for e in entries[:3])
            print(f"  \"{kw:15s}\"  {total:4d} notes  {len(entries)} types  ({issues})")


def main():
    parser = argparse.ArgumentParser(
        description="Build and query published TN index by issue type and keyword",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Build if stale (daily check)
  %(prog)s --force                # Force rebuild
  %(prog)s --issue figs-metaphor  # List examples for an issue type
  %(prog)s --lookup "hand"        # Find how a keyword was classified
  %(prog)s --stats                # Summary statistics
"""
    )
    parser.add_argument("--force", "-f", action="store_true",
                        help="Force rebuild even if fresh")
    parser.add_argument("--issue", "-i", metavar="TYPE",
                        help="Look up examples for an issue type (e.g., figs-metaphor)")
    parser.add_argument("--lookup", "-l", metavar="KEYWORD",
                        help="Find how a keyword was classified (e.g., hand)")
    parser.add_argument("--stats", "-s", action="store_true",
                        help="Print index statistics")

    args = parser.parse_args()

    if args.issue:
        do_issue(args.issue)
    elif args.lookup:
        do_lookup(args.lookup)
    elif args.stats:
        do_stats()
    else:
        do_build(force=args.force)


if __name__ == "__main__":
    main()
