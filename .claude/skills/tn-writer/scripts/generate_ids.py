#!/usr/bin/env python3
"""
Generate unique 4-character IDs for translation notes.

Fetches existing IDs from upstream Door43 TN TSV to avoid collisions.
Adapted from tnwriter-dev/modules/tsv_notes_cache.py.

Usage:
    python3 generate_ids.py <BOOK> <count>
    python3 generate_ids.py PSA 50

Output: One ID per line on stdout.
"""

import os
import sys
import json
import random
import string
import hashlib
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '.cache', 'tsv_notes')


def get_cache_path(book_code):
    return os.path.join(CACHE_DIR, f"tn_{book_code.upper()}.json")


def get_latest_commit_sha(book_code):
    """Get the latest commit SHA for a TN TSV file."""
    if requests is None:
        return None
    try:
        url = "https://git.door43.org/api/v1/repos/unfoldingWord/en_tn/commits"
        params = {'path': f'tn_{book_code.upper()}.tsv', 'sha': 'master', 'limit': 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        commits = resp.json()
        if commits:
            c = commits[0]
            return {'sha': c['sha'], 'date': c['commit']['committer']['date']}
        return None
    except Exception:
        return None


def fetch_upstream_ids(book_code, force_refresh=False):
    """Fetch upstream TN TSV and extract existing IDs, with caching."""
    book_code = book_code.upper()
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = get_cache_path(book_code)

    # Check cache
    if not force_refresh and os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            latest = get_latest_commit_sha(book_code)
            if latest and cached.get('commit_sha') == latest['sha']:
                return set(cached.get('ids', []))
            elif not latest:
                return set(cached.get('ids', []))
        except Exception:
            pass

    if requests is None:
        print("Warning: requests library not available, cannot fetch upstream IDs", file=sys.stderr)
        return set()

    try:
        url = f"https://git.door43.org/unfoldingWord/en_tn/raw/branch/master/tn_{book_code}.tsv"
        print(f"Fetching upstream TN TSV: {url}", file=sys.stderr)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        content = resp.text

        # Parse IDs from TSV
        ids = set()
        lines = content.strip().split('\n')
        if len(lines) < 2:
            return ids

        headers = lines[0].split('\t')
        id_idx = headers.index('ID') if 'ID' in headers else -1
        if id_idx < 0:
            return ids

        for line in lines[1:]:
            if not line.strip():
                continue
            cols = line.split('\t')
            if id_idx < len(cols) and cols[id_idx].strip():
                ids.add(cols[id_idx].strip())

        # Cache
        latest = get_latest_commit_sha(book_code)
        cache_data = {
            'book_code': book_code,
            'ids': list(ids),
            'commit_sha': latest['sha'] if latest else 'unknown',
            'cached_at': datetime.now().isoformat()
        }
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except Exception:
            pass

        return ids

    except Exception as e:
        print(f"Warning: Could not fetch upstream IDs: {e}", file=sys.stderr)
        return set()


def generate_unique_id(existing_ids, max_attempts=100):
    """Generate a unique 4-char ID: [a-z][a-z0-9]{3}."""
    first_chars = string.ascii_lowercase
    other_chars = string.ascii_lowercase + string.digits
    for _ in range(max_attempts):
        new_id = random.choice(first_chars) + ''.join(random.choices(other_chars, k=3))
        if new_id not in existing_ids:
            return new_id
    # Fallback: timestamp-based
    ts = str(int(datetime.now().timestamp() * 1000))
    h = hashlib.md5(ts.encode()).hexdigest()
    fallback = 'x' + ''.join(c for c in h if c in string.ascii_lowercase)[:3].ljust(3, 'z')
    return fallback


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_ids.py <BOOK> <count>", file=sys.stderr)
        sys.exit(1)

    book_code = sys.argv[1].upper()
    count = int(sys.argv[2])

    existing_ids = fetch_upstream_ids(book_code)
    print(f"Found {len(existing_ids)} existing IDs for {book_code}", file=sys.stderr)

    for _ in range(count):
        new_id = generate_unique_id(existing_ids)
        existing_ids.add(new_id)
        print(new_id)


if __name__ == '__main__':
    main()
