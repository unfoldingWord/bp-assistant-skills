#!/usr/bin/env python3
"""
check_ust_passives.py - Detect passive voice in UST USFM output.

Strips USFM markup (alignment tags, word-level markup, markers) to get plain text,
then checks each verse for passive constructions.

Usage:
  python3 check_ust_passives.py <ust_file.usfm>

Exit code 0 if no passives found, 1 if passives found.
Findings printed to stderr for immediate visibility.
"""

import re
import sys


# --- Passive detection data (from detect_activepassive.py) ---

PASSIVE_AUXILIARIES = {'be', 'is', 'are', 'am', 'was', 'were', 'been', 'being'}

PARTICIPLE_ENDINGS = ('ed', 'en', 'wn', 'ung', 'orn', 'oken', 'osen',
                      'otten', 'iven', 'aken', 'tten')

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

NOT_PARTICIPLES = {
    'not', 'that', 'what', 'but', 'just', 'about', 'out', 'without',
    'light', 'right', 'night', 'might', 'sight', 'fight', 'eight',
    'great', 'heart', 'part', 'start', 'apart', 'art',
    'in', 'then', 'when', 'often', 'even', 'open', 'seven', 'eleven',
    'own', 'down', 'town', 'brown', 'grown',
    'men', 'women', 'children', 'brethren',
    'heaven', 'garden', 'burden', 'sudden', 'golden', 'wooden',
    'listen', 'hasten', 'fasten', 'lessen', 'lesson',
    'and', 'hand', 'land', 'stand', 'understand', 'command', 'demand',
    'around', 'ground', 'sound', 'found', 'bound', 'round', 'wound',
    'hundred', 'kindred'
}

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


def is_past_participle(word):
    w = word.lower()
    if w in STATIVE_ADJECTIVES:
        return False
    if w in NOT_PARTICIPLES:
        return False
    if w in IRREGULAR_PARTICIPLES:
        return True
    for ending in PARTICIPLE_ENDINGS:
        if w.endswith(ending) and len(w) > len(ending) + 2:
            return True
    return False


def find_passives(text):
    """Find passive constructions in plain text. Returns list of phrase strings."""
    words = text.split()
    results = []
    i = 0
    while i < len(words):
        w = words[i].lower().strip('.,;:!?\u201c\u201d\u2018\u2019"\'{}[]')
        if w in PASSIVE_AUXILIARIES:
            for j in range(i + 1, min(i + 4, len(words))):
                candidate = words[j].strip('.,;:!?\u201c\u201d\u2018\u2019"\'{}[]')
                if is_past_participle(candidate):
                    phrase = ' '.join(
                        ww.strip('.,;:!?\u201c\u201d\u2018\u2019"\'{}[]')
                        for ww in words[i:j+1]
                    )
                    results.append(phrase)
                    i = j
                    break
        i += 1
    return results


def strip_usfm(text):
    """Strip USFM markup to plain text."""
    # Remove alignment milestones: \zaln-s |...\* and \zaln-e\*
    text = re.sub(r'\\zaln-s\s*\|[^*]*\\\*', '', text)
    text = re.sub(r'\\zaln-e\\\*', '', text)
    # Remove word-level markup: \w word|attrs\w*  ->  word
    text = re.sub(r'\\w\s+([^|]*?)\|[^*]*\\w\*', r'\1', text)
    # Remove remaining USFM markers (but keep text after \v N, \d, etc.)
    text = re.sub(r'\\(ts|qs)\\\*', '', text)
    text = re.sub(r'\\(id|usfm|ide|h|toc\d|mt|c|p|q\d?|d|s\d?|b|nb|pi|mi|ms\d?)\b[^\n]*', '', text)
    # Remove \v marker but keep verse number and text
    # (handled per-verse in parse_verses)
    text = re.sub(r'\\[a-z]+\d?\s*', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_verses(content):
    """Parse USFM content into {ref: plain_text} dict.

    Handles aligned USFM where a verse spans many lines: tracks the
    current verse reference and accumulates all text until the next
    \\v or \\c marker.
    """
    verses = {}
    book = 'UNK'
    id_match = re.search(r'\\id\s+(\S+)', content)
    if id_match:
        book = id_match.group(1)

    chapter = '0'
    current_ref = None

    for line in content.split('\n'):
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            chapter = ch_match.group(1)
            current_ref = None
            continue

        # Check for \v markers -- a line can contain multiple (poetry)
        parts = re.split(r'\\v\s+(\d+)\s', line)
        if len(parts) > 1:
            # parts[0] is text before first \v (continuation of previous verse)
            if current_ref and parts[0].strip():
                plain = strip_usfm(parts[0])
                if plain:
                    verses[current_ref] = verses.get(current_ref, '') + ' ' + plain
            # Process each \v in the line
            for idx in range(1, len(parts), 2):
                vnum = parts[idx]
                current_ref = f"{book} {chapter}:{vnum}"
                vtext = parts[idx + 1] if idx + 1 < len(parts) else ''
                plain = strip_usfm(vtext)
                if plain:
                    verses[current_ref] = verses.get(current_ref, '') + ' ' + plain
        elif current_ref:
            # Continuation line belonging to current verse
            plain = strip_usfm(line)
            if plain:
                verses[current_ref] = verses.get(current_ref, '') + ' ' + plain

    # Clean up leading/trailing whitespace
    return {ref: text.strip() for ref, text in verses.items()}


def main():
    if len(sys.argv) != 2:
        print("Usage: check_ust_passives.py <ust_file.usfm>", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    verses = parse_verses(content)
    total_found = 0

    for ref in sorted(verses.keys(), key=lambda r: (r.split()[0], int(r.split(':')[0].split()[-1]), int(r.split(':')[1]))):
        passives = find_passives(verses[ref])
        if passives:
            for phrase in passives:
                print(f"  {ref}: \"{phrase}\"", file=sys.stderr)
                total_found += 1

    if total_found:
        print(f"\nFound {total_found} passive construction(s) in {filepath}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"No passives found in {filepath}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
