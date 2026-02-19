#!/usr/bin/env python3
"""
Run Gemini CLI as an independent reviewer for pipeline output.

Constructs a stage-specific review prompt, invokes Gemini in headless mode,
and writes structured findings to the review output directory.

Usage:
    python3 gemini_review.py --stage ult --book PSA --chapter 65
    python3 gemini_review.py --stage notes --book PSA --chapter 65 --dry-run

Exit codes:
    0 = no findings
    1 = findings present
    2 = Gemini invocation failed (rate limit, timeout, etc.)
"""

import argparse
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
PROMPT_DIR = os.path.join(PROJECT_ROOT, '.claude', 'skills', 'utilities', 'prompts', 'gemini-review')
OUTPUT_BASE = os.path.join(PROJECT_ROOT, 'output')


def pad_chapter(book: str, chapter: int) -> str:
    """Zero-pad chapter: 3 digits for PSA, 2 digits otherwise."""
    width = 3 if book.upper() == 'PSA' else 2
    return str(chapter).zfill(width)


def resolve_paths(stage: str, book: str, chapter: int) -> dict:
    """Return dict with 'review_target', 'cross_refs', 'guidelines', 'output'."""
    b = book.upper()
    ch = pad_chapter(b, chapter)

    ult_usfm = os.path.join(OUTPUT_BASE, 'AI-ULT', b, f'{b}-{ch}.usfm')
    ust_usfm = os.path.join(OUTPUT_BASE, 'AI-UST', b, f'{b}-{ch}.usfm')
    issues_tsv = os.path.join(OUTPUT_BASE, 'issues', b, f'{b}-{ch}.tsv')
    notes_tsv = os.path.join(OUTPUT_BASE, 'notes', b, f'{b}-{ch}.tsv')
    ult_aligned = os.path.join(OUTPUT_BASE, 'AI-ULT', b, f'{b}-{ch}-aligned.usfm')
    ust_aligned = os.path.join(OUTPUT_BASE, 'AI-UST', b, f'{b}-{ch}-aligned.usfm')

    # Guideline paths (relative to project root for Gemini to read)
    gl_guidelines = '.claude/skills/reference/gl_guidelines.md'
    literalness = '.claude/skills/ULT-gen/reference/literalness_patterns.md'
    ust_patterns = '.claude/skills/UST-gen/reference/ust_patterns.md'
    issue_skill = '.claude/skills/issue-identification/SKILL.md'
    note_style = '.claude/skills/tn-writer/reference/note-style-guide.md'
    prompt_templates = '.claude/skills/tn-writer/reference/prompt-templates.md'
    alignment_rules = '.claude/skills/ULT-alignment/reference/alignment_rules.md'
    ust_alignment_rules = '.claude/skills/UST-alignment/reference/ust_alignment_rules.md'

    stage_map = {
        'ult': {
            'review_target': ult_usfm,
            'cross_refs': [],
            'guidelines': [literalness, gl_guidelines],
        },
        'issues': {
            'review_target': issues_tsv,
            'cross_refs': [ult_usfm],
            'guidelines': [issue_skill],
        },
        'ust': {
            'review_target': ust_usfm,
            'cross_refs': [ult_usfm],
            'guidelines': [ust_patterns, gl_guidelines],
        },
        'notes': {
            'review_target': notes_tsv,
            'cross_refs': [],
            'guidelines': [note_style, prompt_templates],
        },
        'alignment-ult': {
            'review_target': ult_aligned,
            'cross_refs': [],
            'guidelines': [alignment_rules],
        },
        'alignment-ust': {
            'review_target': ust_aligned,
            'cross_refs': [],
            'guidelines': [ust_alignment_rules],
        },
    }

    if stage not in stage_map:
        print(f"ERROR: Unknown stage '{stage}'", file=sys.stderr)
        sys.exit(2)

    info = stage_map[stage]
    review_dir = os.path.join(OUTPUT_BASE, 'review', b)
    info['output'] = os.path.join(review_dir, f'{b}-{ch}-{stage}-gemini.md')
    return info


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def build_prompt(stage: str, paths: dict) -> str:
    """Load the stage prompt template and append file-read instructions."""
    prompt_file = os.path.join(PROMPT_DIR, f'{stage}.md')
    # alignment stages share one prompt file
    if stage.startswith('alignment'):
        prompt_file = os.path.join(PROMPT_DIR, 'alignment.md')

    if not os.path.exists(prompt_file):
        print(f"ERROR: Prompt file not found: {prompt_file}", file=sys.stderr)
        sys.exit(2)

    with open(prompt_file, 'r', encoding='utf-8') as f:
        template = f.read()

    # Build the file list section
    lines = [template, '', '---', '', 'Read these files:']
    lines.append(f'- {paths["review_target"]} (THE FILE TO REVIEW)')
    for ref in paths.get('cross_refs', []):
        lines.append(f'- {ref} (CROSS-REFERENCE)')
    for gl in paths.get('guidelines', []):
        lines.append(f'- {gl} (GUIDELINES TO CHECK AGAINST)')

    # For alignment stages, tell it which type
    if stage == 'alignment-ult':
        lines.append('')
        lines.append('This is a ULT alignment (word-level precision).')
    elif stage == 'alignment-ust':
        lines.append('')
        lines.append('This is a UST alignment (phrase-level, meaning-based).')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Gemini invocation
# ---------------------------------------------------------------------------

def call_gemini(prompt: str, model: str, timeout: int) -> tuple:
    """Call Gemini CLI. Returns (exit_code, stdout_text)."""
    cmd = ['gemini', '-p', prompt, '-o', 'text', '-y', '-m', model]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT,
        )
        # Filter stderr (deprecation warnings, etc.) -- just use stdout
        return result.returncode, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return -1, 'Gemini timed out'
    except FileNotFoundError:
        return -1, 'Gemini CLI not found -- is it installed?'


def has_findings(text: str) -> bool:
    """Check if the review output contains actual findings."""
    if not text:
        return False
    lower = text.lower()
    # Look for the findings table or explicit "0 findings"
    if '0 findings' in lower or 'no findings' in lower:
        if '| ref' not in lower and '| severity' not in lower:
            return False
    # If there is a markdown table with at least one data row, there are findings
    table_rows = [l for l in text.split('\n')
                  if l.strip().startswith('|') and not l.strip().startswith('| ---')
                  and not l.strip().startswith('|---')]
    # Subtract the header row if present
    header_count = sum(1 for l in table_rows if 'Ref' in l or 'Severity' in l or 'Finding' in l)
    data_rows = len(table_rows) - header_count
    return data_rows > 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Run Gemini CLI as independent reviewer for pipeline output.'
    )
    parser.add_argument('--stage', required=True,
                        choices=['ult', 'issues', 'ust', 'notes', 'alignment-ult', 'alignment-ust'],
                        help='Pipeline stage to review')
    parser.add_argument('--book', required=True, help='3-letter book abbreviation')
    parser.add_argument('--chapter', required=True, type=int, help='Chapter number')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print assembled prompt without calling Gemini')
    parser.add_argument('--output', help='Override output file path')
    parser.add_argument('--model', default='gemini-2.5-flash',
                        help='Gemini model (default: gemini-2.5-flash)')
    parser.add_argument('--timeout', type=int, default=600,
                        help='Subprocess timeout in seconds (default: 600)')

    args = parser.parse_args()
    book = args.book.upper()

    # Resolve file paths
    paths = resolve_paths(args.stage, book, args.chapter)
    if args.output:
        paths['output'] = args.output

    # Check that the target file exists
    if not os.path.exists(paths['review_target']):
        print(f"ERROR: Review target not found: {paths['review_target']}", file=sys.stderr)
        sys.exit(2)

    # Build prompt
    prompt = build_prompt(args.stage, paths)

    if args.dry_run:
        print('=== ASSEMBLED PROMPT ===')
        print(prompt)
        print(f'\n=== OUTPUT WOULD GO TO ===')
        print(paths['output'])
        sys.exit(0)

    # Call Gemini
    ret, output = call_gemini(prompt, args.model, args.timeout)

    if ret != 0 or not output:
        reason = output if output else f'exit code {ret}'
        print(f"Gemini review failed: {reason}", file=sys.stderr)
        sys.exit(2)

    # Write output
    out_dir = os.path.dirname(paths['output'])
    os.makedirs(out_dir, exist_ok=True)
    with open(paths['output'], 'w', encoding='utf-8') as f:
        f.write(output)

    # Determine exit code based on findings
    findings = has_findings(output)
    ch = pad_chapter(book, args.chapter)
    if findings:
        print(f"Gemini review ({args.stage}): findings for {book} {args.chapter} -> {paths['output']}")
        sys.exit(1)
    else:
        print(f"Gemini review ({args.stage}): clean for {book} {args.chapter}")
        sys.exit(0)


if __name__ == '__main__':
    main()
