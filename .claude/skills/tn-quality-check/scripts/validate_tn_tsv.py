#!/usr/bin/env python3
"""Validate TN TSV files against Door43 CI rules.

Adapted from unfoldingWord/en_tn/.gitea/workflows/validate_tn_files.py
to work on individual chapter TSV files (not just book-level tn_*.tsv).

Usage:
  python3 validate_tn_tsv.py <file.tsv> [--check N] [--max-errors 100] [--json output.json]

Runs checks 3-13 (skips manifest and project-file-existence checks).
Exit code 0 = pass, 1 = errors found, 2 = argument error.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


EXPECTED_HEADER = [
    "Reference",
    "ID",
    "Tags",
    "SupportReference",
    "Quote",
    "Occurrence",
    "Note",
]

ID_RE = re.compile(r"^[a-z][a-z0-9]{3}$")
REFERENCE_RE = re.compile(
    r"^(?:front:intro|\d+:intro|\d+:front|\d+:\d+(?:[,-][\d,:-]*\d+)*)$"
)
SUPPORT_REFERENCE_RE = re.compile(r"^rc://[^/]+/[^/]+/[^/]+/[^ \\]+$")
OCCURRENCE_RE = re.compile(r"^(?:-1|[0-9]+)$")
ALT_TRANSLATION_LABEL_RE = re.compile(r"Alternat(e|ive)( *)([Tt])ranslation")
DUPLICATE_ALT_TRANSLATION_LABEL_RE = re.compile(r"Alternate translation.{0,2} [Aa]lternat")

# Check names (matching upstream numbering, skipping 1-2 which are manifest checks)
CHECK_NUM_COLUMNS = "3. Number of Columns Check"
CHECK_TSV_HEADER = "4. TSV Header Check"
CHECK_ID = "5. ID Check"
CHECK_REFERENCE = "6. Reference Check"
CHECK_SUPPORT_REFERENCE = "7. SupportReference Check"
CHECK_LITERAL_BACKSLASH_N = r"8. Literal \n Check"
CHECK_OCCURRENCE = "9. Occurrence Check"
CHECK_NOTE_ENDING = "10. Note Ending Check"
CHECK_REFERENCE_ORDER = "11. Reference Order Check"
CHECK_ALT_TRANSLATION_LABEL = "12. Alternate translation Label Check"
CHECK_PAIRED_SQUARE_BRACKET = "13. Paired Square Bracket Check"

ALL_CHECKS = [
    CHECK_NUM_COLUMNS, CHECK_TSV_HEADER, CHECK_ID, CHECK_REFERENCE,
    CHECK_SUPPORT_REFERENCE, CHECK_LITERAL_BACKSLASH_N, CHECK_OCCURRENCE,
    CHECK_NOTE_ENDING, CHECK_REFERENCE_ORDER, CHECK_ALT_TRANSLATION_LABEL,
    CHECK_PAIRED_SQUARE_BRACKET,
]

CHECK_NUMBER_TO_NAME = {
    3: CHECK_NUM_COLUMNS, 4: CHECK_TSV_HEADER, 5: CHECK_ID,
    6: CHECK_REFERENCE, 7: CHECK_SUPPORT_REFERENCE,
    8: CHECK_LITERAL_BACKSLASH_N, 9: CHECK_OCCURRENCE,
    10: CHECK_NOTE_ENDING, 11: CHECK_REFERENCE_ORDER,
    12: CHECK_ALT_TRANSLATION_LABEL, 13: CHECK_PAIRED_SQUARE_BRACKET,
}


@dataclass
class ValidationError:
    rule: str
    message: str
    file: str | None = None
    line: int | None = None
    row_id: str | None = None
    reference: str | None = None

    def display(self) -> str:
        parts = [f"[{self.rule}]"]
        if self.file is not None:
            parts.append(f"File: {self.file}")
        if self.line is not None:
            parts.append(f"Line: {self.line}")
        if self.row_id is not None:
            parts.append(f"ID: {self.row_id if self.row_id != '' else '(blank)'}")
        if self.reference is not None:
            parts.append(f"Ref: {self.reference if self.reference != '' else '(blank)'}")
        parts.append(self.message)
        return " | ".join(parts)


class ErrorCollector:
    def __init__(self, max_errors: int, enabled_checks: set[str]) -> None:
        self.max_errors = max_errors
        self.enabled_checks = enabled_checks
        self.errors: list[ValidationError] = []
        self.truncated = False

    def add(self, *, rule: str, message: str, file: str | None = None,
            line: int | None = None, row_id: str | None = None,
            reference: str | None = None) -> None:
        if rule not in self.enabled_checks:
            return
        if len(self.errors) >= self.max_errors:
            self.truncated = True
            return
        self.errors.append(ValidationError(
            rule=rule, message=message, file=file,
            line=line, row_id=row_id, reference=reference,
        ))

    def has_errors(self) -> bool:
        return bool(self.errors) or self.truncated


@dataclass
class ReferenceOrderKey:
    chapter_value: int
    verse_rank: int
    verse_number: int
    original: str
    line_number: int


def parse_reference_order_key(reference: str, line_number: int) -> ReferenceOrderKey | None:
    if ":" not in reference:
        return None
    chapter_text, verse_raw = reference.split(":", 1)
    if chapter_text == "front":
        chapter_value = -1
    elif chapter_text.isdigit():
        chapter_value = int(chapter_text)
    else:
        return None

    if verse_raw == "intro":
        verse_rank, verse_number = 0, -1
    elif verse_raw == "front":
        verse_rank, verse_number = 1, -1
    else:
        match = re.match(r"^(\d+)", verse_raw)
        if not match:
            return None
        verse_rank, verse_number = 2, int(match.group(1))

    return ReferenceOrderKey(
        chapter_value=chapter_value, verse_rank=verse_rank,
        verse_number=verse_number, original=reference, line_number=line_number,
    )


def is_reference_in_order(prev: ReferenceOrderKey, curr: ReferenceOrderKey) -> bool:
    if curr.chapter_value != prev.chapter_value:
        return curr.chapter_value > prev.chapter_value
    if curr.verse_rank != prev.verse_rank:
        return curr.verse_rank > prev.verse_rank
    if curr.verse_rank == 2 and curr.verse_number < prev.verse_number:
        return False
    return True


def validate_alternate_translation_label(note, errors, row_context):
    for match in ALT_TRANSLATION_LABEL_RE.finditer(note):
        label_start = match.start()
        label_end = match.end()
        raw_match = match.group(0)

        if label_start != 0:
            preceding_two = note[max(0, label_start - 2):label_start]
            if preceding_two == "  ":
                errors.add(rule=CHECK_ALT_TRANSLATION_LABEL, **row_context,
                           message=f"Matched label '{raw_match}': too many spaces before the Alternate translation label.")
            elif not re.fullmatch(r"[^a-z] ", preceding_two or ""):
                errors.add(rule=CHECK_ALT_TRANSLATION_LABEL, **row_context,
                           message=f"Matched label '{raw_match}': the previous sentence does not have punctuation at the end.")

        if match.group(1) != "e":
            errors.add(rule=CHECK_ALT_TRANSLATION_LABEL, **row_context,
                       message=f"Matched label '{raw_match}': use 'Alternate', not 'Alternative'.")
        if match.group(2) != " ":
            errors.add(rule=CHECK_ALT_TRANSLATION_LABEL, **row_context,
                       message=f"Matched label '{raw_match}': use exactly one space between 'Alternate' and 'translation'.")
        if match.group(3) != "t":
            errors.add(rule=CHECK_ALT_TRANSLATION_LABEL, **row_context,
                       message=f"Matched label '{raw_match}': use lowercase 't' in 'Alternate translation'.")

        if label_end >= len(note):
            next_char = ""
        else:
            next_char = note[label_end]
        if next_char not in {":", ",", " "}:
            pretty_next = next_char if next_char else "(end of note)"
            errors.add(rule=CHECK_ALT_TRANSLATION_LABEL, **row_context,
                       message=f"Matched label '{raw_match}': Alternate translation label must be followed by ':', ',' or a space (found '{pretty_next}').")

    dup = DUPLICATE_ALT_TRANSLATION_LABEL_RE.search(note)
    if dup:
        errors.add(rule=CHECK_ALT_TRANSLATION_LABEL, **row_context,
                   message=f"Matched text '{dup.group(0)}': Duplicate Alternate translation labels.")


def validate_paired_square_brackets(note, errors, row_context):
    stack = []
    i = 0
    while i < len(note):
        char = note[i]
        if char not in "[]":
            i += 1
            continue
        j = i
        while j < len(note) and note[j] == char:
            j += 1
        run_len = j - i
        token = char * run_len

        if char == "[":
            stack.append((run_len, i))
        else:
            if not stack:
                errors.add(rule=CHECK_PAIRED_SQUARE_BRACKET, **row_context,
                           message=f"Closing bracket '{token}' at character {i + 1} does not have a matching opening bracket.")
            else:
                open_len, open_pos = stack.pop()
                if open_len != run_len:
                    errors.add(rule=CHECK_PAIRED_SQUARE_BRACKET, **row_context,
                               message=f"Opening bracket '{'[' * open_len}' at character {open_pos + 1} is closed by '{token}' at character {i + 1}. Bracket sizes must match.")
        i = j

    while stack:
        open_len, open_pos = stack.pop()
        errors.add(rule=CHECK_PAIRED_SQUARE_BRACKET, **row_context,
                   message=f"Opening bracket '{'[' * open_len}' at character {open_pos + 1} does not have a matching closing bracket.")


def validate_tsv_file(tsv_path: Path, errors: ErrorCollector) -> None:
    file_name = tsv_path.name
    try:
        content = tsv_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        errors.add(rule=CHECK_NUM_COLUMNS, file=file_name,
                   message=f"File is not valid UTF-8 text: {exc}")
        return

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = content.split("\n")

    if len(lines) == 0 or (len(lines) == 1 and lines[0] == ""):
        errors.add(rule=CHECK_NUM_COLUMNS, file=file_name, line=1, message="TSV file is empty.")
        return

    header_line = lines[0]
    try:
        header_row = next(csv.reader([header_line], delimiter="\t"))
    except Exception as exc:
        errors.add(rule=CHECK_NUM_COLUMNS, file=file_name, line=1,
                   message=f"Header is not parseable as TSV: {exc}")
        return

    if header_row != EXPECTED_HEADER:
        errors.add(rule=CHECK_TSV_HEADER, file=file_name, line=1,
                   message=f"Header must be: {'\\t'.join(EXPECTED_HEADER)} (found: {' | '.join(header_row)})")

    seen_ids: set[str] = set()
    previous_ref_key: ReferenceOrderKey | None = None
    seen_blank = False

    for zero_idx, raw_line in enumerate(lines[1:], start=1):
        line_number = zero_idx + 1

        if raw_line == "":
            seen_blank = True
            continue

        if seen_blank:
            errors.add(rule=CHECK_NUM_COLUMNS, file=file_name, line=line_number,
                       message="Blank lines are only allowed at the very end of the file.")
            seen_blank = False

        try:
            row = next(csv.reader([raw_line], delimiter="\t"))
        except Exception as exc:
            errors.add(rule=CHECK_NUM_COLUMNS, file=file_name, line=line_number,
                       message=f"Line is not parseable as TSV: {exc}")
            continue

        if len(row) != 7:
            errors.add(rule=CHECK_NUM_COLUMNS, file=file_name, line=line_number,
                       row_id=row[1] if len(row) > 1 else None,
                       reference=row[0] if len(row) > 0 else None,
                       message=f"Expected 7 columns but found {len(row)}.")
            continue

        reference, row_id, _tags, support_reference, _quote, occurrence, note = row
        ctx = {"file": file_name, "line": line_number, "row_id": row_id, "reference": reference}

        # Literal \n check
        for col_name, col_val in [("Reference", reference), ("ID", row_id), ("Tags", _tags),
                                   ("SupportReference", support_reference), ("Quote", _quote),
                                   ("Occurrence", occurrence)]:
            if "\\n" in col_val:
                errors.add(rule=CHECK_LITERAL_BACKSLASH_N, **ctx,
                           message=f"{col_name} column contains literal \\n.")

        # ID check
        if not row_id:
            errors.add(rule=CHECK_ID, **ctx, message="ID cannot be blank.")
        elif not ID_RE.fullmatch(row_id):
            errors.add(rule=CHECK_ID, **ctx,
                       message=f"ID '{row_id}' must match: first char [a-z], then 3 chars [a-z0-9].")
        elif row_id in seen_ids:
            errors.add(rule=CHECK_ID, **ctx, message=f"ID '{row_id}' is duplicated in this file.")
        else:
            seen_ids.add(row_id)

        # Reference check
        if not reference:
            errors.add(rule=CHECK_REFERENCE, **ctx, message="Reference column cannot be blank.")
        elif not REFERENCE_RE.fullmatch(reference):
            errors.add(rule=CHECK_REFERENCE, **ctx,
                       message=f"Reference '{reference}' is invalid.")
        else:
            curr_key = parse_reference_order_key(reference, line_number)
            if curr_key is not None:
                if previous_ref_key is not None and not is_reference_in_order(previous_ref_key, curr_key):
                    errors.add(rule=CHECK_REFERENCE_ORDER, **ctx,
                               message=f"Reference '{reference}' is out of order (after '{previous_ref_key.original}' on line {previous_ref_key.line_number}).")
                previous_ref_key = curr_key

        # SupportReference check
        if support_reference and not SUPPORT_REFERENCE_RE.fullmatch(support_reference):
            errors.add(rule=CHECK_SUPPORT_REFERENCE, **ctx,
                       message=f"SupportReference '{support_reference}' is not a valid RC link.")

        # Occurrence check
        occ_blank_ok = (occurrence == "" and _quote == "")
        if not occ_blank_ok and not OCCURRENCE_RE.fullmatch(occurrence):
            errors.add(rule=CHECK_OCCURRENCE, **ctx,
                       message=f"Occurrence '{occurrence}' must be a non-negative integer or -1.")

        # Note ending check
        if note.endswith("\\n"):
            errors.add(rule=CHECK_NOTE_ENDING, **ctx, message="Note must not end with literal \\n.")

        # Note content checks
        if note:
            validate_alternate_translation_label(note, errors, ctx)
            validate_paired_square_brackets(note, errors, ctx)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a TN TSV file against Door43 CI rules.")
    parser.add_argument("tsv_file", help="Path to TN TSV file to validate")
    parser.add_argument("--check", dest="checks", action="append", type=int,
                        help="Check number to run (repeatable, default: all). Valid: 3-13.")
    parser.add_argument("--max-errors", type=int, default=200,
                        help="Maximum errors before truncating (default: 200)")
    parser.add_argument("--json", dest="json_output", default=None,
                        help="Write results as JSON to this path")
    args = parser.parse_args()

    tsv_path = Path(args.tsv_file)
    if not tsv_path.is_file():
        print(f"ERROR: File not found: {args.tsv_file}", file=sys.stderr)
        return 2

    if args.checks:
        valid_nums = set(CHECK_NUMBER_TO_NAME.keys())
        invalid = [n for n in args.checks if n not in valid_nums]
        if invalid:
            print(f"ERROR: Unknown check number(s): {invalid}. Valid: {sorted(valid_nums)}", file=sys.stderr)
            return 2
        enabled = {CHECK_NUMBER_TO_NAME[n] for n in args.checks}
    else:
        enabled = set(ALL_CHECKS)

    errors = ErrorCollector(max_errors=args.max_errors, enabled_checks=enabled)
    validate_tsv_file(tsv_path, errors)

    # Print summary
    if errors.has_errors():
        print(f"FAIL: {len(errors.errors)} error(s) in {tsv_path.name}", file=sys.stderr)
        for err in errors.errors:
            print(f"  {err.display()}", file=sys.stderr)
        if errors.truncated:
            print(f"  (truncated at {args.max_errors} errors)", file=sys.stderr)
    else:
        print(f"PASS: {tsv_path.name} -- all Door43 CI checks passed", file=sys.stderr)

    # JSON output
    if args.json_output:
        result = {
            "file": str(tsv_path),
            "passed": not errors.has_errors(),
            "error_count": len(errors.errors),
            "truncated": errors.truncated,
            "errors": [asdict(e) for e in errors.errors],
        }
        Path(args.json_output).write_text(json.dumps(result, indent=2, ensure_ascii=False))

    return 1 if errors.has_errors() else 0


if __name__ == "__main__":
    sys.exit(main())
