import csv
import re
from collections import defaultdict

# 1. Read USFM to get verse text
verse_text = defaultdict(str)
current_v = None
with open('/srv/bot/workspace/output/.stash/HAB-02-claude/AI-ULT/HAB-02.usfm', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        v_match = re.match(r'\\v\s+(\d+)\s*(.*)', line)
        if v_match:
            current_v = v_match.group(1)
            text = v_match.group(2)
        else:
            text = line
        
        if current_v:
            # remove markers
            text = re.sub(r'\\[a-z0-9*-]+(\s+[^|]+|)(\|[^|*]+\*|\*)', '', text)
            text = re.sub(r'\\[a-z0-9*-]+(\s+|$)', '', text)
            text = re.sub(r'\{[^}]+\}', '', text)
            text = re.sub(r'[\*\\]', '', text)
            verse_text[current_v] += " " + text

for v in verse_text:
    verse_text[v] = re.sub(r'\s+', ' ', verse_text[v]).strip()

def read_tsv(path):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if row and len(row) >= 4:
                rows.append((row[0], row[1], row[2], row[3], row[4] if len(row) > 4 else ""))
    return rows

structure = read_tsv('/srv/bot/workspace/tmp/deep-issue-id/HAB-02/wave2_structure.tsv')
rhetoric = read_tsv('/srv/bot/workspace/tmp/deep-issue-id/HAB-02/wave2_rhetoric.tsv')

rulings = {}
with open('/srv/bot/workspace/tmp/deep-issue-id/HAB-02/wave3_rulings.tsv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        if len(row) >= 4:
            verse, text, issue, ruling = row[0], row[1], row[2], row[3]
            if ruling:
                rulings[(verse, issue, text)] = (ruling, row[4] if len(row)>4 else "")

def apply_rulings(items):
    out = []
    for row in items:
        bk, v_str, issue, text, note = row
        verse = v_str.split(':')[1] if ':' in v_str else v_str
        key = (v_str, issue, text)
        ruling_info = rulings.get(key)
        if ruling_info:
            ruling, new_val = ruling_info
            if ruling == 'DROP':
                continue
            elif ruling == 'RECLASSIFY':
                issue = new_val
        out.append((bk, v_str, issue, text, note))
    return out

all_items = apply_rulings(structure) + apply_rulings(rhetoric)

# Deduplicate
dedup = {}
for item in all_items:
    bk, v_str, issue, text, note = item
    key = (v_str, issue, text)
    if key not in dedup:
        dedup[key] = item
    else:
        # if the existing has no note but the new one does, prefer the new one
        if not dedup[key][4] and note:
            dedup[key] = item

final_items = list(dedup.values())

# Order: first-to-last by ULT position, longest-to-shortest when nested
def get_sort_key(item):
    bk, v_str, issue, text, note = item
    verse = v_str.split(':')[1] if ':' in v_str else v_str
    
    # normalize text for searching
    clean_text = text.lower()
    clean_text = re.sub(r'[{}]', '', clean_text)
    clean_text = re.sub(r'[^\w\s]', '', clean_text)
    
    vt = verse_text.get(verse, "").lower()
    vt = re.sub(r'[^\w\s]', '', vt)
    
    pos = vt.find(clean_text)
    if pos == -1:
        # try word intersection or just fallback
        words = clean_text.split()
        if words:
            pos = vt.find(words[0])
    
    if pos == -1:
        pos = 9999
        
    # Extract the first integer from the verse string to handle ranges (e.g., "10-11" -> 10)
    verse_num_match = re.search(r'\d+', verse)
    verse_num = int(verse_num_match.group(0)) if verse_num_match else 9999

    return (verse_num, pos, -len(text))

final_items.sort(key=get_sort_key)

with open('/srv/bot/workspace/output/issues/HAB/HAB-02.tsv', 'w', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter='\t')
    for item in final_items:
        writer.writerow(item)
