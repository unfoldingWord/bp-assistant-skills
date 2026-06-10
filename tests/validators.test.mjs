/**
 * Tests for the validation gates in .claude/skills/utilities/scripts/validation/.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { validateStructure } from '../.claude/skills/utilities/scripts/validation/validate_usfm_structure.mjs';
import { checkDuplicateIds } from '../.claude/skills/utilities/scripts/validation/check_duplicate_ids.mjs';
import { preflightCheck, bookFileNumber } from '../.claude/skills/utilities/scripts/validation/preflight_data_check.mjs';

// ---------- validate_usfm_structure ----------

const GOOD_PLAIN = `\\id TST EN_ULT
\\usfm 3.0
\\c 1
\\p
\\v 1 In the beginning God created the heavens.
\\q1 \\v 2 And peace {is} good,
\\q2 and peace endures.
\\v 3 The end.
`;

test('structure: clean plain USFM passes', () => {
  assert.deepEqual(validateStructure(GOOD_PLAIN), []);
});

test('structure: missing verse is reported', () => {
  const text = GOOD_PLAIN.replace(/\\q1 \\v 2 .*\n\\q2 .*\n/, '');
  const problems = validateStructure(text);
  assert.ok(problems.some((p) => p.code === 'missing_verse' && p.verse === 2), JSON.stringify(problems));
});

test('structure: duplicate verse is reported', () => {
  const text = GOOD_PLAIN + '\\v 3 Again.\n';
  const problems = validateStructure(text);
  assert.ok(problems.some((p) => p.code === 'duplicate_verse' && p.verse === 3), JSON.stringify(problems));
});

test('structure: chapter not starting at verse 1 is reported', () => {
  const text = '\\id TST\n\\c 1\n\\v 2 Starts late.\n';
  const problems = validateStructure(text);
  assert.ok(problems.some((p) => p.code === 'missing_first_verse'), JSON.stringify(problems));
});

test('structure: empty verse is reported', () => {
  const text = '\\id TST\n\\c 1\n\\v 1\n\\v 2 Real text.\n';
  const problems = validateStructure(text);
  assert.ok(problems.some((p) => p.code === 'empty_verse' && p.verse === 1), JSON.stringify(problems));
});

test('structure: unbalanced zaln milestones are reported', () => {
  const text = '\\id TST\n\\c 1\n\\v 1 \\zaln-s |x-strong="H1"\\*\\w word|x-occurrence="1" x-occurrences="1"\\w*\n';
  const problems = validateStructure(text);
  assert.ok(problems.some((p) => p.code === 'zaln_markers'), JSON.stringify(problems));
});

test('structure: unbalanced braces are reported', () => {
  const text = '\\id TST\n\\c 1\n\\v 1 The {word is here.\n';
  const problems = validateStructure(text);
  assert.ok(problems.some((p) => p.code === 'unbalanced_braces'), JSON.stringify(problems));
});

test('structure: verse range \\v 1-2 counts as both verses', () => {
  const text = '\\id TST\n\\c 1\n\\v 1-2 Bridged text.\n\\v 3 Third.\n';
  assert.deepEqual(validateStructure(text), []);
});

test('structure: source comparison catches missing and extra verses', () => {
  const source = '\\id TST\n\\c 1\n\\v 1 a\n\\v 2 b\n\\v 3 c\n';
  const missing = '\\id TST\n\\c 1\n\\v 1 a\n\\v 2 b\n';
  let problems = validateStructure(missing, { sourceText: source });
  assert.ok(problems.some((p) => p.code === 'missing_vs_source' && p.verse === 3), JSON.stringify(problems));

  const extra = '\\id TST\n\\c 1\n\\v 1 a\n\\v 2 b\n\\v 3 c\n\\v 4 d\n';
  problems = validateStructure(extra, { sourceText: source });
  assert.ok(problems.some((p) => p.code === 'extra_vs_source' && p.verse === 4), JSON.stringify(problems));
});

test('structure: debug artifacts are reported', () => {
  const text = '\\id TST\n\\c 1\nStart words: [ "and" ]\n\\v 1 Text.\n';
  const problems = validateStructure(text);
  assert.ok(problems.some((p) => p.code === 'debug_artifact'), JSON.stringify(problems));
});

// ---------- check_duplicate_ids ----------

const TSV_HEADER = 'Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote';
function tsv(rows) {
  return [TSV_HEADER, ...rows].join('\n') + '\n';
}

test('ids: clean files pass', () => {
  const a = tsv(['1:1\tab12\t\t\tq\t1\tn', '1:2\tcd34\t\t\tq\t1\tn']);
  const b = tsv(['2:1\tef56\t\t\tq\t1\tn']);
  assert.deepEqual(checkDuplicateIds([{ label: 'a.tsv', text: a }, { label: 'b.tsv', text: b }]), []);
});

test('ids: duplicate within a file is reported', () => {
  const a = tsv(['1:1\tab12\t\t\tq\t1\tn', '1:2\tab12\t\t\tq\t1\tn']);
  const problems = checkDuplicateIds([{ label: 'a.tsv', text: a }]);
  assert.ok(problems.some((p) => p.code === 'duplicate_id'), JSON.stringify(problems));
});

test('ids: duplicate across files is reported', () => {
  const a = tsv(['1:1\tab12\t\t\tq\t1\tn']);
  const b = tsv(['2:1\tab12\t\t\tq\t1\tn']);
  const problems = checkDuplicateIds([{ label: 'a.tsv', text: a }, { label: 'b.tsv', text: b }]);
  assert.ok(problems.some((p) => p.code === 'duplicate_id'), JSON.stringify(problems));
});

test('ids: bad format is reported', () => {
  const a = tsv(['1:1\tABCD\t\t\tq\t1\tn', '1:2\t1abc\t\t\tq\t1\tn', '1:3\tab1\t\t\tq\t1\tn']);
  const problems = checkDuplicateIds([{ label: 'a.tsv', text: a }]);
  assert.equal(problems.filter((p) => p.code === 'id_format').length, 3, JSON.stringify(problems));
});

test('ids: collision against published file is reported', () => {
  const mine = tsv(['1:1\tab12\t\t\tq\t1\tn']);
  const published = tsv(['9:9\tab12\t\t\tq\t1\tn']);
  const problems = checkDuplicateIds(
    [{ label: 'mine.tsv', text: mine }],
    [{ label: 'published.tsv', text: published }],
  );
  assert.ok(problems.some((p) => p.code === 'id_collision'), JSON.stringify(problems));
});

test('ids: missing ID column is reported', () => {
  const a = 'Reference\tNote\n1:1\thello\n';
  const problems = checkDuplicateIds([{ label: 'a.tsv', text: a }]);
  assert.ok(problems.some((p) => p.code === 'no_id_column'), JSON.stringify(problems));
});

// ---------- preflight_data_check ----------

test('preflight: book file numbering', () => {
  assert.equal(bookFileNumber('GEN'), '01');
  assert.equal(bookFileNumber('JOS'), '06');
  assert.equal(bookFileNumber('PSA'), '19');
  assert.equal(bookFileNumber('NAM'), '34');
  assert.equal(bookFileNumber('MAL'), '39');
  assert.equal(bookFileNumber('MAT'), '41');
  assert.equal(bookFileNumber('XXX'), null);
});

function scaffold(withData) {
  const root = mkdtempSync(join(tmpdir(), 'preflight-'));
  if (withData) {
    mkdirSync(join(root, 'data/hebrew_bible'), { recursive: true });
    mkdirSync(join(root, 'data/glossary'), { recursive: true });
    mkdirSync(join(root, 'data/quick-ref'), { recursive: true });
    mkdirSync(join(root, 'data/cache'), { recursive: true });
    writeFileSync(join(root, 'data/hebrew_bible/34-NAM.usfm'), 'x'.repeat(20_000));
    writeFileSync(join(root, 'data/issues_resolved.txt'), 'x'.repeat(2_000));
    writeFileSync(join(root, 'data/glossary/project_glossary.md'), 'x'.repeat(2_000));
    for (const g of ['hebrew_ot_glossary.csv', 'psalms_reference.csv', 'sacrifice_terminology.csv', 'biblical_measurements.csv', 'biblical_phrases.csv']) {
      writeFileSync(join(root, 'data/glossary', g), 'x'.repeat(500));
    }
    writeFileSync(join(root, 'data/quick-ref/ult_decisions.csv'), 'x'.repeat(500));
    writeFileSync(join(root, 'data/cache/strongs_index.json'), 'x'.repeat(150_000));
  }
  return root;
}

test('preflight: empty root fails loudly with missing entries', () => {
  const root = scaffold(false);
  const { results, ok } = preflightCheck({ book: 'NAM', stage: 'ult', root });
  assert.equal(ok, false);
  assert.ok(results.some((r) => r.status === 'MISSING' && r.path.includes('issues_resolved')), JSON.stringify(results));
  assert.ok(results.some((r) => r.status === 'MISSING' && r.path.includes('hebrew_bible')), JSON.stringify(results));
});

test('preflight: complete ULT data passes', () => {
  const root = scaffold(true);
  const { results, ok } = preflightCheck({ book: 'NAM', stage: 'ult', root });
  assert.equal(ok, true, JSON.stringify(results.filter((r) => r.status === 'MISSING'), null, 2));
});

test('preflight: UST stage requires T4T', () => {
  const root = scaffold(true);
  const { results, ok } = preflightCheck({ book: 'NAM', stage: 'ust', root });
  assert.equal(ok, false);
  assert.ok(results.some((r) => r.status === 'MISSING' && r.path.includes('t4t')), JSON.stringify(results));
});

test('preflight: unknown book code fails', () => {
  const root = scaffold(true);
  const { ok, results } = preflightCheck({ book: 'ZZZ', stage: 'ult', root });
  assert.equal(ok, false);
  assert.ok(results.some((r) => r.note.includes('unknown book code')), JSON.stringify(results));
});
