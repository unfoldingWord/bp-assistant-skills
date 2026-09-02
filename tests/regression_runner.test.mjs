/**
 * Tests for run_regression_checks.mjs — closed bugs must stay fixed.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { runChecks, explainVerseScope } from '../.claude/skills/utilities/scripts/validation/run_regression_checks.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const CHECKS = JSON.parse(readFileSync(
  resolve(here, '../.claude/skills/utilities/regression/regression-checks.json'), 'utf8'));

test('explain verse scope parsing', () => {
  assert.deepEqual(explainVerseScope('ISA 54:3: adjective used'), { chapter: 54, verse: 3 });
  assert.deepEqual(explainVerseScope('51:7: jussive'), { chapter: 51, verse: 7 });
  assert.equal(explainVerseScope('AT must not end with punctuation'), null);
});

test('ISA 51:7 jussive-as-imperative regression is caught', () => {
  const bad = '\\id ISA\n\\c 51\n\\v 7 Listen to me. Do not fear the reproach of man.\n';
  const results = runChecks({ stage: 'ULT', text: bad, book: 'ISA', chapter: 51, checksData: CHECKS });
  const fails = results.filter((r) => r.status === 'fail');
  assert.ok(fails.some((r) => r.issue === 24 && /imperative/.test(r.explain)), JSON.stringify(fails, null, 2));
});

test('ISA 51:7 corrected jussive passes', () => {
  const good = '\\id ISA\n\\c 51\n\\v 7 Listen to me. May you not fear the reproach of man, and may you not be dismayed.\n';
  const results = runChecks({ stage: 'ULT', text: good, book: 'ISA', chapter: 51, checksData: CHECKS });
  const issue24 = results.filter((r) => r.issue === 24);
  assert.ok(issue24.length > 0);
  assert.ok(issue24.every((r) => r.status === 'pass'), JSON.stringify(issue24, null, 2));
});

test('checks for verses not in the file are skipped, not failed', () => {
  const onlyV1 = '\\id ISA\n\\c 51\n\\v 1 Listen to me, pursuers of righteousness.\n';
  const results = runChecks({ stage: 'ULT', text: onlyV1, book: 'ISA', chapter: 51, checksData: CHECKS });
  const issue24 = results.filter((r) => r.issue === 24);
  assert.ok(issue24.every((r) => r.status === 'skip'), JSON.stringify(issue24, null, 2));
});

test('global ULT check: "Yahweh of hosts" fails anywhere', () => {
  const bad = '\\id NAM\n\\c 1\n\\v 1 The word of Yahweh of hosts.\n';
  const results = runChecks({ stage: 'ULT', text: bad, book: 'NAM', chapter: 1, checksData: CHECKS });
  assert.ok(results.some((r) => r.issue === 27 && r.status === 'fail'), JSON.stringify(results.filter((r) => r.issue === 27)));
});

test('ISA pinned checks do not fire for other books', () => {
  const nam = '\\id NAM\n\\c 1\n\\v 7 Do not fear, for Yahweh of Armies is good.\n';
  const results = runChecks({ stage: 'ULT', text: nam, book: 'NAM', chapter: 1, checksData: CHECKS });
  assert.ok(!results.some((r) => r.issue === 24), 'ISA-pinned issue 24 must not apply to NAM');
});

test('UST body-part idiom "hand over" is caught', () => {
  const bad = '\\id JER\n\\c 20\n\\v 5 I will hand over to the enemy everything valuable.\n';
  const results = runChecks({ stage: 'UST', text: bad, book: 'JER', chapter: 20, checksData: CHECKS });
  assert.ok(results.some((r) => r.issue === 70 && r.status === 'fail'), JSON.stringify(results.filter((r) => r.issue === 70)));
});

test('UST literal "stretched his hand over" is not a false positive', () => {
  const good = '\\id EXO\n\\c 14\n\\v 21 Moses stretched out his hand over the sea.\n';
  const results = runChecks({ stage: 'UST', text: good, book: 'EXO', chapter: 14, checksData: CHECKS });
  assert.ok(results.filter((r) => r.issue === 70).every((r) => r.status === 'pass'), JSON.stringify(results.filter((r) => r.issue === 70)));
});

test('PSA TQ "the writer" is caught; duplicate IDs are caught', () => {
  const tsv = 'Reference\tID\tTags\tQuote\tOccurrence\tQuestion\tResponse\n'
    + '3:1\tab12\t\t\t1\tWhat did the writer say?\tHe cried out.\n'
    + '3:2\tab12\t\t\t1\tWho helped?\tYahweh helped.\n';
  const results = runChecks({ stage: 'TQ', text: tsv, book: 'PSA', chapter: 3, checksData: CHECKS });
  assert.ok(results.some((r) => r.issue === 68 && r.status === 'fail'), 'the writer should fail');
  assert.ok(results.some((r) => r.issue === 74 && r.status === 'fail'), 'duplicate IDs should fail');
});

test('TN zero-width unicode is caught', () => {
  const tsv = 'Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote\n'
    + '1:intro\tab12\t\t\t\t0\tThis chapter has​ hidden junk.\n';
  const results = runChecks({ stage: 'TN', text: tsv, book: 'ZEC', chapter: 1, checksData: CHECKS });
  assert.ok(results.some((r) => r.issue === 53 && r.status === 'fail'), JSON.stringify(results.filter((r) => r.issue === 53)));
});

test('TN AT final punctuation caught, but figs-rquestion rows exempt', () => {
  const bad = 'Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote\n'
    + '1:2\tab12\t\trc://*/ta/man/translate/figs-metaphor\tq\t1\tSome note. Alternate translation: [he is angry.]\n';
  let results = runChecks({ stage: 'TN', text: bad, book: 'NAM', chapter: 1, checksData: CHECKS });
  assert.ok(results.some((r) => r.issue === 80 && r.status === 'fail'), 'AT trailing period should fail');

  const rq = 'Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote\n'
    + '1:2\tcd34\t\trc://*/ta/man/translate/figs-rquestion\tq\t1\tQuestion note. Alternate translation: [He is angry!]\n';
  results = runChecks({ stage: 'TN', text: rq, book: 'NAM', chapter: 1, checksData: CHECKS });
  assert.ok(results.filter((r) => r.issue === 80).every((r) => r.status !== 'fail'), 'rquestion AT punctuation must be exempt');
});

test('TN TCM note with pooled ATs is caught; per-option ATs and AT-free TCM pass', () => {
  const head = 'Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote\n';
  const sref = 'rc://*/ta/man/translate/figs-idiom';

  const pooled = head
    + `1:2\tab12\t\t${sref}\tq\t1\tThis could mean: (1) he is guilty or (2) he is afraid. Alternate translation: [he is guilty]\n`;
  let results = runChecks({ stage: 'TN', text: pooled, book: 'NAM', chapter: 1, checksData: CHECKS });
  assert.ok(results.some((r) => r.issue === 173 && r.status === 'fail'),
    `pooled AT should fail: ${JSON.stringify(results.filter((r) => r.issue === 173), null, 2)}`);

  const perOption = head
    + `1:2\tcd34\t\t${sref}\tq\t1\tThis could mean: (1) he is guilty. Alternate translation: [he is guilty] or (2) he is afraid. Alternate translation: [he is terrified]\n`;
  results = runChecks({ stage: 'TN', text: perOption, book: 'NAM', chapter: 1, checksData: CHECKS });
  assert.ok(results.filter((r) => r.issue === 173).every((r) => r.status !== 'fail'),
    `one AT per option must pass: ${JSON.stringify(results.filter((r) => r.issue === 173), null, 2)}`);

  const noAts = head
    + `1:2\tef56\t\t${sref}\tq\t1\tThe phrase **from God** could mean (1) sent by God or (2) having God as its source.\n`;
  results = runChecks({ stage: 'TN', text: noAts, book: 'NAM', chapter: 1, checksData: CHECKS });
  assert.ok(results.filter((r) => r.issue === 173).every((r) => r.status !== 'fail'),
    'AT-free TCM notes must not be flagged by the AT-placement check');
});

test('golden published TN chapters pass all enforced global TN checks', () => {
  // Checks flagged generatedOnly encode rules stricter than the published
  // corpus (set by closed issues for new output); they are excluded here.
  const generatedOnlyExplains = new Set(
    CHECKS.flatMap((i) => i.checks.filter((c) => c.generatedOnly).map((c) => c.explain)));
  for (const [book, file] of [['NAM', 'NAM/NAM-01.tn.tsv'], ['MAL', 'MAL/MAL-01.tn.tsv'], ['JOS', 'JOS/JOS-01.tn.tsv']]) {
    const text = readFileSync(resolve(here, '../.claude/skills/golden-benchmark/golden', file), 'utf8');
    const results = runChecks({ stage: 'TN', text, book, chapter: 1, checksData: CHECKS });
    const fails = results.filter((r) => r.status === 'fail' && !generatedOnlyExplains.has(r.explain));
    assert.deepEqual(fails, [], `${book}: published notes must pass: ${JSON.stringify(fails, null, 2)}`);
  }
});
