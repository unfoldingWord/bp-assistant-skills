#!/usr/bin/env python3
"""Build data/abstract_nouns_review.csv, the table the team uses to re-review
which English words get figs-abstractnouns notes (issue #234).

Inputs (all local paths; download the Door43 repos first):
  --en-tn       unpacked unfoldingWord/en_tn master (tn_*.tsv)
  --uhb         unpacked unfoldingWord/hbo_uhb master (*.usfm)
  --ugnt        unpacked unfoldingWord/el-x-koine_ugnt master (*.usfm)
  --ult         unpacked unfoldingWord/en_ult master (aligned *.usfm)
  --overnight   data/overnight-review dir (proposals.jsonl per night)
  --wordlist    data/abstract_nouns.txt
  --out         output CSV

For each English word that en_tn tags figs-abstractnouns (taken from the
**bold** words in the note's first sentence), the table shows how often it is
tagged (OT vs NT), the source lemma the ULT aligns that English word to
(falling back to the nouns in the note's Quote), and what editors did
to the bot's notes for that word. Overnight-review proposals only record
edits: dropped = editor deleted the bot note, reworded = editor kept it but
changed the wording or quote, added = editor wrote a note the bot missed.
Bot notes kept unchanged are not recorded, so en_tn_tags_in_bot_books (notes
published today in the books the bot drafted) stands in for "kept".
"""
import argparse, csv, glob, json, os, re, collections

NT = {"MAT","MRK","LUK","JHN","ACT","ROM","1CO","2CO","GAL","EPH","PHP","COL",
      "1TH","2TH","1TI","2TI","TIT","PHM","HEB","JAS","1PE","2PE","1JN","2JN",
      "3JN","JUD","REV"}

# Words the team asked to decide itself (meeting 2026-10-07). Never decided here.
BORDERLINE = {"disaster", "calamity", "abomination", "evil", "destruction"}

# Same Hebrew as "disaster" (רַע H7451c); grouped with the borderline words.
RA_FAMILY = {"trouble", "harm"}

# Tagged 5+ times in en_tn but not added to the list without a team ruling.
HOLD = {
    "kingdom": "realm (concrete) or reign (abstract) by context",
    "separation": "NUM Nazirite technical term",
    "keeping": "NUM guard-duty technical term",
    "plan": "often a concrete scheme; context-dependent",
    "vision": "often the thing seen; context-dependent",
    "cry": "often a spoken cry (communication)",
    "fortification": "usually a concrete place",
    "appetite": "renders נֶפֶשׁ; figurative rather than plain abstract",
    "petition": "spoken communication (see doc exclusions)",
    "request": "spoken communication (see doc exclusions)",
    "supplication": "spoken communication (see doc exclusions)",
}

# figs-abstractnouns.md "Words for spoken or written communication": not abstract.
NOT_ABSTRACT = {"commandment", "statute", "precept", "ordinance", "decree", "testimony", "law",
                "rule", "regulation", "word", "saying", "promise", "declaration", "instruction",
                "charge", "covenant", "oath"}
W_RE = re.compile(r'\\w ([^|]+)\|([^\\]*?)\\w\*')
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
BOLD_RE = re.compile(r'\*\*([^*]+)\*\*')
STRIP_MARKS = re.compile(r'[֑-ֽ֯׀׃׆⁠]')


def norm(tok):
    return STRIP_MARKS.sub("", tok).strip()


def book_files(*dirs):
    """book id -> usfm path."""
    out = {}
    for d in dirs:
        for f in glob.glob(os.path.join(d, "*.usfm")):
            with open(f, encoding="utf8") as fh:
                m = re.search(r'\\id (\w+)', fh.read(300))
            if m:
                out[m.group(1)] = f
    return out


def load_source_book(path):
    """(ch, vs) -> [(surface, lemma, strong, morph)] for one UHB/UGNT book."""
    verses = collections.defaultdict(list)
    if not path:
        return verses
    ch = vs = 0
    for line in open(path, encoding="utf8"):
        m = re.match(r'\\c (\d+)', line)
        if m:
            ch = int(m.group(1))
        m = re.search(r'\\v (\d+)', line)
        if m:
            vs = int(m.group(1))
        for w in W_RE.finditer(line):
            a = dict(ATTR_RE.findall(w.group(2)))
            verses[(ch, vs)].append(
                (norm(w.group(1)), a.get("lemma", ""), a.get("strong", ""), a.get("x-morph", "")))
    return verses


ZALN_TOK = re.compile(r'\\c (\d+)|\\v (\d+)|\\zaln-s \|([^\\]*)\\\*|\\zaln-e\\\*|\\w ([^|\\]+)\|')


def load_ult_book(path):
    """(ch, vs) -> [(english word lower, lemma, strong)] for one aligned ULT book."""
    verses = collections.defaultdict(list)
    if not path:
        return verses
    text = open(path, encoding="utf8").read()
    ch = vs = 0
    stack = []
    for t in ZALN_TOK.finditer(text):
        if t.group(1):
            ch, stack = int(t.group(1)), []
        elif t.group(2):
            vs, stack = int(t.group(2)), []
        elif t.group(3) is not None:
            a = dict(ATTR_RE.findall(t.group(3)))
            stack.append((a.get("x-lemma", ""), a.get("x-strong", ""), a.get("x-morph", "")))
        elif t.group(4):
            if stack:
                nouns = [x for x in stack if re.match(r'(He|Ar),(Nc|A)|Gr,[NA],', x[2])]
                lemma, strong, _ = (nouns or stack)[-1]
                verses[(ch, vs)].append((t.group(4).lower(), lemma, strong))
        elif stack:
            stack.pop()
    return verses


STOP = {"a", "an", "the", "his", "her", "their", "my", "your", "our", "its", "of", "to", "and", "in", "for"}


def head_word(phrase):
    """Drop leading determiners/possessives: 'a desolation' -> 'desolation'."""
    ws = phrase.split()
    while len(ws) > 1 and ws[0] in STOP:
        ws = ws[1:]
    return " ".join(ws)


def ult_lemmas(verses, ref, phrase):
    for w in reversed(phrase.split()):
        if w in STOP:
            continue
        for cand in (w, singular(w), w + "s"):
            got = collections.Counter(
                (lemma, strong) for cv in verses_for(ref)
                for word, lemma, strong in verses.get(cv, []) if word == cand)
            if got:
                return [got.most_common(1)[0][0]]
    return []


def verses_for(ref):
    m = re.match(r'(\d+):(\d+)(?:-(\d+))?$', ref)
    if not m:
        return []
    c, v1 = int(m.group(1)), int(m.group(2))
    v2 = int(m.group(3)) if m.group(3) else v1
    return [(c, v) for v in range(v1, v2 + 1)]


def quote_lemmas(words, ref, quote):
    toks = {norm(t) for t in re.split(r'[\s־&]+', quote) if norm(t)}
    hits = []
    for cv in verses_for(ref):
        for surf, lemma, strong, morph in words.get(cv, []):
            if surf in toks:
                hits.append((lemma, strong, morph))
    # Only common nouns and adjectives; other quote words are context.
    return [(l, st) for l, st, m in hits if re.match(r'(He|Ar),(Nc|A)|Gr,[NA],', m)]


def english_words(note):
    first = re.split(r'(?:you could|you can|Alternate translation)', note, maxsplit=1)[0]
    out = []
    for b in BOLD_RE.findall(first):
        w = b.strip().lower().strip(".,;:!?\"'’‘“”")
        if w and len(w.split()) <= 3:
            out.append(head_word(w))
    return out


NOT_PLURAL = {"does", "news", "gracious", "glorious", "righteous", "riches"}


def singular(w):
    if w in NOT_PLURAL or w.endswith(("ous", "us", "is")):
        return w
    for suf, rep in (("ies", "y"), ("sses", "ss"), ("ches", "ch"), ("shes", "sh"), ("s", "")):
        if w.endswith(suf) and len(w) > len(suf) + 2 and not w.endswith("ss") and not w.endswith("ness"):
            return w[: -len(suf)] + rep
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--en-tn", required=True)
    ap.add_argument("--uhb", required=True)
    ap.add_argument("--ugnt", required=True)
    ap.add_argument("--ult", required=True)
    ap.add_argument("--overnight", required=True)
    ap.add_argument("--wordlist", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    wordlist = {l.strip().lower() for l in open(a.wordlist, encoding="utf8") if l.strip()}
    src_files = book_files(a.uhb, a.ugnt)
    ult_files = book_files(a.ult)
    ult_occ = collections.Counter()

    stats = collections.defaultdict(lambda: {
        "ot": 0, "nt": 0, "lemmas": collections.Counter(), "books": collections.Counter(),
        "dropped": 0, "kept": 0, "added": 0, "bot_books": 0})

    proposals = []
    for f in sorted(glob.glob(os.path.join(a.overnight, "*", "proposals.jsonl"))):
        for line in open(f, encoding="utf8"):
            try:
                proposals.append(json.loads(line))
            except ValueError:
                continue
    # Books the bot drafted and editors reviewed (10+ recorded note edits).
    edits = collections.Counter(j.get("book") for j in proposals if j.get("kind") == "tn-edit")
    bot_books = {b for b, n in edits.items() if n >= 10}

    def key(w):
        return singular(w)

    for f in sorted(glob.glob(os.path.join(a.en_tn, "tn_*.tsv"))):
        book = os.path.basename(f)[3:6]
        ult = load_ult_book(ult_files.get(book))
        src = load_source_book(src_files.get(book))
        for ws_ in ult.values():
            ult_occ.update(singular(w) for w, _, _ in ws_)
        with open(f, encoding="utf8") as fh:
            for row in csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
                if len(row) < 7 or "figs-abstractnouns" not in row[3]:
                    continue
                ref, quote, note = row[0], row[4], row[6]
                ws = english_words(note)
                for w in ws:
                    s = stats[key(w)]
                    s["nt" if book in NT else "ot"] += 1
                    s["books"][book] += 1
                    if book in bot_books:
                        s["bot_books"] += 1
                    lem = ult_lemmas(ult, ref, w)
                    if not lem and len(ws) == 1:
                        lem = quote_lemmas(src, ref, quote)
                    for lemma, strong in set(lem):
                        if not lemma:
                            continue
                        s["lemmas"][f"{lemma} {strong.split(':')[-1]}"] += 1

    seen = set()
    for j in proposals:
        if "figs-abstractnouns" not in (j.get("supportReference") or ""):
            continue
        cat = j.get("category")
        side = j.get("before") if cat == "dropped" else j.get("after")
        if not side:
            continue
        for w in english_words(side.get("note", "")):
            ident = (j.get("book"), j.get("reference"), key(w), cat)
            if ident in seen:
                continue
            seen.add(ident)
            s = stats[key(w)]
            if cat == "dropped":
                s["dropped"] += 1
            elif cat == "added":
                s["added"] += 1
            else:
                s["kept"] += 1

    listed = {singular(w) for w in wordlist}
    for w in listed:
        stats[w]  # words on the list that en_tn never tags still get a row

    rows = []
    for w, s in stats.items():
        total = s["ot"] + s["nt"]
        in_list = w in listed
        occ = ult_occ.get(w, 0) if " " not in w else ""
        rate = f"{min(total / occ, 1):.2f}" if occ else ""
        if w in BORDERLINE:
            status = "borderline: team decides"
        elif w in RA_FAMILY:
            status = "borderline: team decides (same Hebrew as disaster)"
        elif w in HOLD:
            status = f"hold: team decides ({HOLD[w]})"
        elif w in NOT_ABSTRACT:
            status = "conflict: doc says not abstract"
        elif in_list and total == 0:
            status = "review: listed but never tagged"
        elif s["dropped"] >= 2 and s["dropped"] >= s["bot_books"]:
            status = "review: editors drop bot notes"
        elif in_list:
            status = "in list"
        elif total >= 5 and s["ot"] >= 1:
            status = "candidate: add to list"
        else:
            status = "rare"
        rows.append([
            w, "yes" if in_list else "no", total, s["ot"], s["nt"], occ, rate,
            "; ".join(f"{k} ×{v}" for k, v in s["lemmas"].most_common(3)),
            " ".join(f"{b}:{n}" for b, n in s["books"].most_common(4)),
            s["bot_books"], s["kept"], s["dropped"], s["added"], status, ""])
    order = ["borderline", "conflict", "review: editors", "hold", "candidate",
             "review: listed", "in list", "rare"]
    rank = lambda st: next(i for i, o in enumerate(order) if st.startswith(o))
    rows.sort(key=lambda r: (rank(r[13]), -r[2], r[0]))

    with open(a.out, "w", encoding="utf8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["english_word", "in_abstract_nouns_txt", "en_tn_tags_total", "en_tn_tags_ot",
                     "en_tn_tags_nt", "ult_occurrences", "tag_rate", "top_source_lemmas", "top_books", "en_tn_tags_in_bot_books",
                     "bot_notes_reworded", "bot_notes_dropped", "editor_added_bot_missed", "status", "team_decision"])
        wr.writerows(rows)
    print(f"wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()
