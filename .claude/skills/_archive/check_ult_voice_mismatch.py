#!/usr/bin/env python3
"""
check_ult_voice_mismatch.py - Detect English passive voice aligned to active Hebrew verbs in ULT.

For each zaln block in aligned ULT USFM: if the Hebrew verb stem is active (Qal, Piel,
Hiphil, Hitpael) but the aligned English words contain a passive construction
(be-auxiliary + past participle), report the mismatch.

Note: checks within each zaln block. Passive constructions split across two zaln blocks
(auxiliary aligned to one Hebrew word, participle to another) may be missed.

Usage:
  python3 check_ult_voice_mismatch.py <ult_aligned_file.usfm>

Exit code 0 if no mismatches, 1 if mismatches found.
Findings printed to stderr.
"""

import re
import sys


# ---------------------------------------------------------------------------
# Hebrew morphology
# ---------------------------------------------------------------------------

def is_active_hebrew_verb(morph):
    """Return True if x-morph is an active-stem Hebrew verb that should not
    be rendered with an English passive.

    In unfoldingWord x-morph codes (e.g. "He,Vqp3fs"):
      V = verb, next char = stem.
      Active stems flagged (lowercase, excluding t): q=Qal, p=Piel, h=Hiphil
      Excluded from check: t=Hitpael (reflexive/reciprocal — English passive is
        often a legitimate rendering, e.g. "are intertwined" for Hitpael of שׂרג)
      Passive stems (uppercase, not flagged): N=Niphal, P=Pual, H=Hophal
    """
    m = re.search(r'He,V([a-zA-Z])', morph)
    if not m:
        return False
    stem = m.group(1)
    # Hitpael (t) is reflexive — exclude from check
    if stem == 't':
        return False
    return stem.islower()


# ---------------------------------------------------------------------------
# English passive detection (shared with check_ust_passives.py)
# ---------------------------------------------------------------------------

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
    'justified', 'sanctified', 'glorified', 'baptized', 'circumcised',
    'violated', 'humiliated', 'destroyed', 'consumed', 'exiled',
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
    'hundred', 'kindred',
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
    'young',
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


def find_passive(words):
    """Find the first passive construction in a list of words.
    Returns the phrase string, or None.
    """
    for i, word in enumerate(words):
        w = word.lower().strip('.,;:!?\u201c\u201d\u2018\u2019"\'{}[]')
        if w in PASSIVE_AUXILIARIES:
            for j in range(i + 1, min(i + 4, len(words))):
                candidate = words[j].strip('.,;:!?\u201c\u201d\u2018\u2019"\'{}[]')
                if is_past_participle(candidate):
                    return ' '.join(words[i:j + 1])
    return None


# ---------------------------------------------------------------------------
# USFM parser
# ---------------------------------------------------------------------------

def parse_mismatches(content):
    """Parse aligned ULT USFM and return list of mismatch dicts.

    Each dict: {ref, lemma, hebrew, english_phrase}
    """
    mismatches = []
    book = 'UNK'
    id_match = re.search(r'\\id\s+(\S+)', content)
    if id_match:
        book = id_match.group(1)

    chapter = '0'
    verse = '0'
    current_ref = f"{book} {chapter}:{verse}"

    # State for the active-verb zaln block we're currently tracking
    in_active_zaln = False
    active_morph = None
    active_lemma = ''
    active_content = ''
    active_english = []
    zaln_depth = 0  # nesting depth within the tracked block

    for line in content.split('\n'):
        # Track chapter
        ch_match = re.match(r'\\c\s+(\d+)', line)
        if ch_match:
            chapter = ch_match.group(1)
            current_ref = f"{book} {chapter}:{verse}"

        # Track verse (may appear embedded in alignment line)
        v_match = re.search(r'\\v\s+(\d+)', line)
        if v_match:
            verse = v_match.group(1)
            current_ref = f"{book} {chapter}:{verse}"

        # If we're inside an active-verb zaln block, count nested opens/closes
        if in_active_zaln:
            nested_opens = len(re.findall(r'\\zaln-s\b', line))
            closes = len(re.findall(r'\\zaln-e\\\*', line))
            zaln_depth += nested_opens - closes

            # Collect English words on this line
            words = re.findall(r'\\w\s+([^|{}\\\n]+?)\|', line)
            active_english.extend(w.strip() for w in words)

            if zaln_depth <= 0:
                # Block is complete — check for passive
                phrase = find_passive(active_english)
                if phrase:
                    mismatches.append({
                        'ref': current_ref,
                        'lemma': active_lemma,
                        'hebrew': active_content,
                        'english_phrase': phrase,
                        'english_context': ' '.join(active_english),
                    })
                in_active_zaln = False
                active_english = []
            continue

        # Look for a new zaln-s with an active Hebrew verb
        zaln_match = re.search(r'\\zaln-s\s*\|([^*]*)\\\*', line)
        if zaln_match:
            attrs = zaln_match.group(1)
            morph_match = re.search(r'x-morph="([^"]+)"', attrs)
            if morph_match:
                morph = morph_match.group(1)
                if is_active_hebrew_verb(morph):
                    lemma_match = re.search(r'x-lemma="([^"]+)"', attrs)
                    content_match = re.search(r'x-content="([^"]+)"', attrs)
                    in_active_zaln = True
                    active_morph = morph
                    active_lemma = lemma_match.group(1) if lemma_match else ''
                    active_content = content_match.group(1) if content_match else ''
                    active_english = []
                    # Count the opening zaln-s on this line (depth starts at 1)
                    # plus any additional opens minus closes on the same line
                    opens_on_line = len(re.findall(r'\\zaln-s\b', line))
                    closes_on_line = len(re.findall(r'\\zaln-e\\\*', line))
                    zaln_depth = opens_on_line - closes_on_line
                    # Collect any English words on the same line as zaln-s
                    words = re.findall(r'\\w\s+([^|{}\\\n]+?)\|', line)
                    active_english.extend(w.strip() for w in words)
                    if zaln_depth <= 0:
                        # Single-line block — check immediately
                        phrase = find_passive(active_english)
                        if phrase:
                            mismatches.append({
                                'ref': current_ref,
                                'lemma': active_lemma,
                                'hebrew': active_content,
                                'english_phrase': phrase,
                                'english_context': ' '.join(active_english),
                            })
                        in_active_zaln = False
                        active_english = []

    return mismatches


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: check_ult_voice_mismatch.py <ult_aligned_file.usfm>", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    mismatches = parse_mismatches(content)

    if mismatches:
        print(f"Voice mismatches in {filepath}:", file=sys.stderr)
        for m in mismatches:
            print(
                f"  {m['ref']}: Hebrew {m['hebrew']} ({m['lemma']}) — "
                f"active stem but English \"{m['english_phrase']}\" "
                f"[context: {m['english_context']}]",
                file=sys.stderr
            )
        print(f"\nFound {len(mismatches)} mismatch(es).", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"No voice mismatches found in {filepath}.", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
