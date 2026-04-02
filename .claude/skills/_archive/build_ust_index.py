#!/usr/bin/env python3
"""
build_ust_index.py - Build a Strong's number -> English rendering index
from published UST aligned USFM files.

Parses all data/published_ust/*.usfm files in a single pass, replicating the
stack-based zaln-s / zaln-e / \\w parsing from build_strongs_index.py.
Extracts every Strong's number -> English rendering mapping with occurrence counts.

UST renderings are typically longer and more varied than ULT because UST
unpacks meaning rather than preserving form.

Usage:
    python3 build_ust_index.py                 # Build if stale (daily check)
    python3 build_ust_index.py --force          # Force rebuild
    python3 build_ust_index.py --lookup H2617   # Print UST renderings from index
    python3 build_ust_index.py --stats          # Summary statistics
    python3 build_ust_index.py --compare H2617  # ULT vs UST renderings side-by-side

Output: data/cache/ust_index.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date

# Paths relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
SOURCE_DIR = os.path.join(PROJECT_ROOT, "data", "published_ust")
CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "cache")
INDEX_PATH = os.path.join(CACHE_DIR, "ust_index.json")
ULT_INDEX_PATH = os.path.join(CACHE_DIR, "strongs_index.json")
FETCH_SCRIPT = os.path.join(SCRIPT_DIR, "fetch_all_ust.py")

MAX_SAMPLE_REFS = 5  # Keep up to this many sample refs per rendering
MIN_SOURCE_FILES = 5  # Auto-fetch prompt threshold


def check_for_new_release():
    """Check Door43 for a new en_ust release. Returns release tag or None."""
    import urllib.request
    import urllib.error
    url = "https://git.door43.org/unfoldingWord/en_ust/releases/"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("tag_name", "unknown")
    except Exception:
        pass
    return None


def is_stale():
    """Check if the index needs rebuilding. Returns (stale: bool, reason: str)."""
    if not os.path.exists(INDEX_PATH):
        return True, "index does not exist"

    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            idx = json.load(f)
        meta = idx.get("_meta", {})
        built = meta.get("built", "")
        cached_release = meta.get("release", "")
    except (json.JSONDecodeError, KeyError):
        return True, "index is corrupt"

    # Check if built today already
    today = date.today().isoformat()
    if built == today:
        return False, f"built today ({today})"

    # Check if source files changed (count mismatch)
    source_count = len([f for f in os.listdir(SOURCE_DIR) if f.endswith(".usfm")]) if os.path.isdir(SOURCE_DIR) else 0
    if source_count != meta.get("file_count", 0):
        return True, f"file count changed ({meta.get('file_count', '?')} -> {source_count})"

    # Check for new upstream release
    latest_release = check_for_new_release()
    if latest_release and latest_release != cached_release:
        return True, f"new release ({cached_release} -> {latest_release})"

    return False, f"up to date (built {built}, release {cached_release})"


def check_source_files():
    """Check if we have enough source files. Prompt to fetch if sparse."""
    if not os.path.isdir(SOURCE_DIR):
        os.makedirs(SOURCE_DIR, exist_ok=True)

    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".usfm")]
    if len(files) < MIN_SOURCE_FILES:
        print(f"Only {len(files)} UST source file(s) in {SOURCE_DIR}.")
        print(f"Run fetch_all_ust.py to download all published books:")
        print(f"  python3 {FETCH_SCRIPT}")
        if len(files) == 0:
            print("Cannot build index without source files.")
            sys.exit(1)
        print(f"Proceeding with {len(files)} file(s)...\n")


def extract_zaln_attrs(attr_str):
    """Extract attributes from a zaln-s marker string."""
    attrs = {}
    m = re.search(r'x-strong="([^"]+)"', attr_str)
    if m:
        attrs["strong"] = m.group(1)
    m = re.search(r'x-content="([^"]+)"', attr_str)
    if m:
        attrs["content"] = m.group(1)
    m = re.search(r'x-lemma="([^"]+)"', attr_str)
    if m:
        attrs["lemma"] = m.group(1)
    return attrs


def normalize_strong(raw):
    """Strip morphological prefixes like 'b:d:H1234' -> 'H1234'.
    Returns None for bare prefixes with no Strong's number."""
    result = re.sub(r'^(?:[a-z]:)+', '', raw)
    if not re.match(r'^[HG]\d', result):
        return None
    return result


def parse_file(filepath):
    """Parse a single aligned USFM file. Returns list of alignment records.

    Replicates the stack-based parsing from build_strongs_index.py.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    book_id = ""
    chapter = 0
    verse = 0
    results = []

    # Stack of open alignment entries
    stack = []

    # Regex to find zaln-s, zaln-e, and \w markers in order
    marker_re = re.compile(
        r'\\zaln-s\s+\|([^\\]*?)\\?\*'   # group(1): zaln-s attributes
        r'|\\zaln-e\\?\*'                  # zaln-e closing
        r'|\\w\s+([^|]*?)\|[^\\]*?\\w\*'  # group(2): word text
    )

    for line in lines:
        # Track book ID
        m = re.search(r'\\id\s+(\w+)', line)
        if m:
            book_id = m.group(1)

        # Track chapter
        m = re.search(r'\\c\s+(\d+)', line)
        if m:
            chapter = int(m.group(1))

        # Track verse
        m = re.search(r'\\v\s+(\d+)', line)
        if m:
            verse = int(m.group(1))

        # Process markers
        for match in marker_re.finditer(line):
            if match.group(0).startswith("\\zaln-s"):
                attr_str = match.group(1)
                attrs = extract_zaln_attrs(attr_str)
                stack.append({"attrs": attrs, "words": []})
            elif match.group(0).startswith("\\zaln-e"):
                if stack:
                    closed = stack.pop()
                    english = " ".join(closed["words"])
                    # Propagate words up to parent
                    if stack:
                        stack[-1]["words"].extend(closed["words"])
                    # Record the alignment
                    strong_raw = closed["attrs"].get("strong", "")
                    strong_norm = normalize_strong(strong_raw) if strong_raw else None
                    if strong_norm and english:
                        results.append({
                            "strong": strong_norm,
                            "lemma": closed["attrs"].get("lemma", ""),
                            "content": closed["attrs"].get("content", ""),
                            "english": english,
                            "ref": f"{book_id} {chapter}:{verse}",
                        })
            elif match.group(2) is not None:
                word = match.group(2).strip()
                if word and stack:
                    stack[-1]["words"].append(word)

    return results


def build_index(source_dir):
    """Parse all USFM files and build the aggregated index."""
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(f for f in os.listdir(source_dir) if f.endswith(".usfm"))
    if not files:
        print(f"Error: No .usfm files in {source_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {len(files)} UST USFM files from {source_dir}")

    # Aggregate: strong -> {lemma, content, renderings: {text -> {count, refs}}}
    agg = defaultdict(lambda: {"lemma": "", "content": "", "renderings": defaultdict(lambda: {"count": 0, "refs": []})})
    total_alignments = 0

    for filename in files:
        filepath = os.path.join(source_dir, filename)
        records = parse_file(filepath)
        total_alignments += len(records)
        print(f"  {filename}: {len(records)} alignments")

        for rec in records:
            strong = rec["strong"]
            entry = agg[strong]
            # Keep first non-empty lemma/content
            if not entry["lemma"] and rec["lemma"]:
                entry["lemma"] = rec["lemma"]
            if not entry["content"] and rec["content"]:
                entry["content"] = rec["content"]
            rendering = entry["renderings"][rec["english"]]
            rendering["count"] += 1
            if len(rendering["refs"]) < MAX_SAMPLE_REFS:
                rendering["refs"].append(rec["ref"])

    # Check for latest release tag
    release_tag = check_for_new_release() or "unknown"

    # Build output structure
    index = {
        "_meta": {
            "built": date.today().isoformat(),
            "source_dir": "data/published_ust/",
            "file_count": len(files),
            "total_alignments": total_alignments,
            "unique_strongs": len(agg),
            "release": release_tag,
        }
    }

    for strong, data in sorted(agg.items()):
        renderings = sorted(
            [{"text": text, "count": info["count"], "refs": info["refs"]}
             for text, info in data["renderings"].items()],
            key=lambda r: -r["count"]
        )
        total = sum(r["count"] for r in renderings)
        index[strong] = {
            "lemma": data["lemma"],
            "total": total,
            "renderings": renderings,
        }

    return index


def do_build(force=False):
    """Build the index, with staleness check unless forced."""
    check_source_files()

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
    print(f"\nUST index built: {INDEX_PATH}")
    print(f"  Files: {meta['file_count']}")
    print(f"  Alignments: {meta['total_alignments']}")
    print(f"  Unique Strong's: {meta['unique_strongs']}")
    print(f"  Size: {size_mb:.2f} MB")


def do_lookup(strong_num):
    """Look up a Strong's number in the UST index and print renderings."""
    if not os.path.exists(INDEX_PATH):
        print(f"Error: UST index not found at {INDEX_PATH}", file=sys.stderr)
        print("Run: python3 build_ust_index.py  (to build)", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)

    # Try exact match first, then base-number match
    matches = []
    if strong_num in index:
        matches = [strong_num]
    else:
        base = strong_num.upper().rstrip("ABCDEFabcdef")
        matches = sorted(k for k in index if k != "_meta" and k.upper().startswith(base.upper()))

    if not matches:
        print(f"No entry for {strong_num} in UST index.")
        sys.exit(0)

    for key in matches:
        entry = index[key]
        print(f"Strong's: {key} (lemma: {entry.get('lemma', '?')})")
        print(f"Total occurrences (UST): {entry['total']}")
        print()

        for r in entry["renderings"]:
            pct = (r["count"] / entry["total"] * 100) if entry["total"] > 0 else 0
            refs_str = ", ".join(r["refs"][:5])
            print(f"  {r['text']:40s}  {r['count']:4d}  ({pct:5.1f}%)  [{refs_str}]")

        if key != matches[-1]:
            print()


def do_stats():
    """Print summary statistics from the UST index."""
    if not os.path.exists(INDEX_PATH):
        print(f"Error: UST index not found at {INDEX_PATH}", file=sys.stderr)
        print("Run: python3 build_ust_index.py  (to build)", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)

    meta = index.get("_meta", {})
    size_mb = os.path.getsize(INDEX_PATH) / (1024 * 1024)

    print("UST Strong's Index Statistics")
    print("=" * 40)
    print(f"  Built:            {meta.get('built', '?')}")
    print(f"  Source:           {meta.get('source_dir', '?')}")
    print(f"  Source files:     {meta.get('file_count', '?')}")
    print(f"  Total alignments: {meta.get('total_alignments', '?')}")
    print(f"  Unique Strong's:  {meta.get('unique_strongs', '?')}")
    print(f"  Release:          {meta.get('release', '?')}")
    print(f"  Index size:       {size_mb:.2f} MB")

    # Top 10 most frequent Strong's numbers
    entries = [(k, v) for k, v in index.items() if k != "_meta"]
    entries.sort(key=lambda x: -x[1]["total"])

    print(f"\nTop 10 most frequent Strong's numbers:")
    for strong, data in entries[:10]:
        top_rendering = data["renderings"][0]["text"] if data["renderings"] else "?"
        print(f"  {strong:8s}  {data['total']:5d} occ  lemma={data.get('lemma','?'):15s}  top=\"{top_rendering}\"")

    # Count entries with multiple renderings
    multi = sum(1 for _, v in entries if len(v.get("renderings", [])) > 1)
    print(f"\nStrong's with multiple renderings: {multi}/{len(entries)}")


def do_compare(strong_num):
    """Show ULT vs UST renderings side-by-side for a Strong's number."""
    # Load both indexes
    ult_index = {}
    ust_index = {}

    if os.path.exists(ULT_INDEX_PATH):
        with open(ULT_INDEX_PATH, "r", encoding="utf-8") as f:
            ult_index = json.load(f)
    else:
        print(f"Warning: ULT index not found at {ULT_INDEX_PATH}", file=sys.stderr)

    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            ust_index = json.load(f)
    else:
        print(f"Error: UST index not found at {INDEX_PATH}", file=sys.stderr)
        print("Run: python3 build_ust_index.py  (to build)", file=sys.stderr)
        sys.exit(1)

    # Find matching keys in both indexes
    def find_matches(index, num):
        if num in index:
            return [num]
        base = num.upper().rstrip("ABCDEFabcdef")
        return sorted(k for k in index if k != "_meta" and k.upper().startswith(base.upper()))

    ult_matches = find_matches(ult_index, strong_num)
    ust_matches = find_matches(ust_index, strong_num)
    all_keys = sorted(set(ult_matches + ust_matches))

    if not all_keys:
        print(f"No entry for {strong_num} in either index.")
        sys.exit(0)

    for key in all_keys:
        ult_entry = ult_index.get(key)
        ust_entry = ust_index.get(key)

        lemma = "?"
        if ult_entry:
            lemma = ult_entry.get("lemma", "?")
        elif ust_entry:
            lemma = ust_entry.get("lemma", "?")

        print(f"=== {key} (lemma: {lemma}) ===")
        print()

        # ULT renderings
        print("  ULT (literal):")
        if ult_entry:
            for r in ult_entry["renderings"][:10]:
                pct = (r["count"] / ult_entry["total"] * 100) if ult_entry["total"] > 0 else 0
                print(f"    {r['text']:40s}  {r['count']:4d}  ({pct:5.1f}%)")
        else:
            print("    (not in ULT index)")

        print()

        # UST renderings
        print("  UST (meaning-based):")
        if ust_entry:
            for r in ust_entry["renderings"][:10]:
                pct = (r["count"] / ust_entry["total"] * 100) if ust_entry["total"] > 0 else 0
                print(f"    {r['text']:40s}  {r['count']:4d}  ({pct:5.1f}%)")
        else:
            print("    (not in UST index)")

        if key != all_keys[-1]:
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Build and query Strong's number index from published UST",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # Build if stale (daily check)
  %(prog)s --force              # Force rebuild
  %(prog)s --lookup H2617       # Print UST renderings for H2617
  %(prog)s --stats              # Summary statistics
  %(prog)s --compare H2617      # ULT vs UST renderings side-by-side
"""
    )
    parser.add_argument("--force", "-f", action="store_true",
                        help="Force rebuild even if fresh")
    parser.add_argument("--lookup", "-l", metavar="STRONG",
                        help="Look up a Strong's number (e.g., H2617)")
    parser.add_argument("--stats", "-s", action="store_true",
                        help="Print index statistics")
    parser.add_argument("--compare", "-c", metavar="STRONG",
                        help="Compare ULT vs UST renderings for a Strong's number")

    args = parser.parse_args()

    if args.lookup:
        do_lookup(args.lookup)
    elif args.stats:
        do_stats()
    elif args.compare:
        do_compare(args.compare)
    else:
        do_build(force=args.force)


if __name__ == "__main__":
    main()
