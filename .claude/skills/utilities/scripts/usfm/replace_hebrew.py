import re
import unicodedata
import shutil
import tempfile
import os
import sys

def canonical_hebrew(text):
    """
    Normalize ONLY for matching.

    - preserves all Hebrew marks
    - preserves MAHAPAKH vs MUNAH in stored text
    - standardizes combining-mark order
    - removes invisible joiners only
    """

    # Remove invisible joiners
    text = text.replace("\u2060", "")
    text = text.replace("\u200d", "")
    text = text.replace("\ufeff", "")

    # Normalize ONLY for lookup matching
    return unicodedata.normalize("NFD", text)

def strip_hebrew_marks(text):
    result = []

    for ch in unicodedata.normalize("NFD", text):
        name = unicodedata.name(ch, "")

        if (
            "HEBREW POINT" in name or
            "HEBREW ACCENT" in name or
            name == "HEBREW MARK MASORA CIRCLE"
        ):
            continue

        result.append(ch)

    return unicodedata.normalize("NFC", "".join(result))

def read_usfm_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_heb_data(heb_file):

    lookup = {}
    stripped_lookup = {}
    current_chapter = 0
    current_verse = 0

    usfm_data = read_usfm_file(heb_file)

    for line in usfm_data.splitlines():
        if line.startswith('\\c'):
            chapter = re.search(r'\\c (\d+)', line)
            if chapter:
                current_chapter = int(chapter.group(1))

        elif line.startswith('\\v'):
            verse = re.search(r'\\v (\d+)', line)
            if verse:
                current_verse = int(verse.group(1))
        
        elif line.startswith('\\w'):
            words = re.findall(r'\\w ([^\|]+)\|lemma="([^"]*)" strong="([^"]*)" x-morph="([^"]+)"\\w\*', line)
            if words:
                for word in words:
                    form = word[0]
                    normalized_form = canonical_hebrew(form)
                    stripped_form = strip_hebrew_marks(form)
                    lemma = word[1]
                    normalized_lemma = canonical_hebrew(lemma)
                    stripped_lemma = strip_hebrew_marks(lemma)
                    strong = word[2]
                    xmorph = word[3]

                    key = (
                        current_chapter,
                        current_verse,
                        normalized_lemma,
                        normalized_form,
                        xmorph
                    )

                    lookup[key] = {
                        "lemma": lemma,
                        "form": form
                    }

                    stripped_key = (
                        current_chapter,
                        current_verse,
                        stripped_lemma,
                        stripped_form,
                        xmorph
                    )

                    stripped_lookup[stripped_key] = {
                        "lemma": lemma,
                        "form": form
                    }

    return lookup, stripped_lookup

def update_usfm(usfm_file, heb_data, stripped_heb_data):

    chapter = None
    verse = None

    # Match attributes inside \zaln-s
    pattern = re.compile(
        r'x-lemma="([^"]+)"'
        r'.*?x-morph="([^"]+)"'
        r'.*?x-occurrence="([^"]+)"'
        r'.*?x-occurrences="[^"]+"'
        r'.*?x-content="([^"]+)"',
        re.DOTALL
    )

    def fill_verses(verse1, verse2):
        return list(range(verse1, verse2 + 1))

    with open(usfm_file, encoding="utf-8") as f:
        text = f.read()

    text = re.sub(r'(\\v\s+\d+)', r'\n\1', text)

    lines = text.splitlines(True)

    updated_lines = []

    for line in lines:

        # Track chapter
        chapter_match = re.match(r'\\c\s+(\d+)', line)
        if chapter_match:
            chapter = int(chapter_match.group(1))

        # Track verse
        verse_match = re.match(r'\\v\s+([\d–—-]+)', line)
        if verse_match:
            verse = verse_match.group(1)
            if "–" in verse or "—" in verse or "-" in verse:
                parts = re.split(r"[—–-]", verse)
                if len(parts) == 2:
                    verse1, verse2 = map(int, parts)
                    verseRange = True
                else:
                    verse1 = verse2 = int(parts[0])
                verse_range = fill_verses(verse1, verse2)
            else:
                verse_range = [int(verse)]
                verseRange = False

        def replace_match(match):

            original_lemma = match.group(1)
            original_morph = match.group(2)
            original_content = match.group(4)

            normalized_lemma = canonical_hebrew(original_lemma)
            stripped_lemma = strip_hebrew_marks(original_lemma)
            normalized_form = canonical_hebrew(original_content)
            stripped_form = strip_hebrew_marks(original_content)

            for verse in verse_range:

                key = (
                    chapter,
                    verse,
                    normalized_lemma,
                    normalized_form,
                    original_morph
                )
            
                if key not in heb_data:
                    print(f"NOT FOUND: {key}")
                    if verseRange is True:
                        print(f"Verse range, skipping stripped lookup for {key}")
                        return match.group(0)
                    
                    stripped_key = (
                        chapter,
                        verse,
                        stripped_lemma,
                        stripped_form,
                        original_morph
                    )

                    if stripped_key not in stripped_heb_data:
                        print(f"ALSO NOT FOUND (stripped): {stripped_key}")
                        return match.group(0)
                    
                    print(f"FOUND with stripped key: {stripped_key}")
                    
                    replacement_data = stripped_heb_data[stripped_key]

                    new_lemma = replacement_data["lemma"]
                    new_form = replacement_data["form"]

                    updated = match.group(0)

                    # Replace x-lemma only
                    updated = re.sub(
                        r'x-lemma="[^"]+"',
                        f'x-lemma="{new_lemma}"',
                        updated
                    )

                    # Replace x-content only
                    updated = re.sub(
                        r'x-content="[^"]+"',
                        f'x-content="{new_form}"',
                        updated
                    )

                    return updated

                replacement_data = heb_data[key]

                new_lemma = replacement_data["lemma"]
                new_form = replacement_data["form"]

                updated = match.group(0)

                # Replace x-lemma only
                updated = re.sub(
                    r'x-lemma="[^"]+"',
                    f'x-lemma="{new_lemma}"',
                    updated
                )

                # Replace x-content only
                updated = re.sub(
                    r'x-content="[^"]+"',
                    f'x-content="{new_form}"',
                    updated
                )

            return updated

        updated_line = pattern.sub(replace_match, line)

        updated_lines.append(updated_line)

    output = ''.join(updated_lines)

    output = re.sub(r'\n(\\v\s+\d+)', r'\1', output)

    def safe_write_usfm(usfm_file, usfm_text):
        # 1. Write to temp file in same directory
        dir_name = os.path.dirname(usfm_file)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=dir_name
        ) as tmp:
            tmp.write(usfm_text)
            temp_path = tmp.name

        # 2. Backup old file (only AFTER successful write)
        if os.path.exists(usfm_file):
            backup_file = usfm_file + ".bak"
            shutil.move(usfm_file, backup_file)

        # 3. Atomic replace
        shutil.move(temp_path, usfm_file)
    
    safe_write_usfm(usfm_file, output)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise ValueError("Usage: script.py heb_file usfm_file")

    heb_file = sys.argv[1]
    usfm_file = sys.argv[2]

    # RUN
    heb_data, stripped_heb_data = extract_heb_data(heb_file)
    update_usfm(usfm_file, heb_data, stripped_heb_data)
