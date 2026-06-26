/**
 * Tests for create_aligned_usfm.js — the fragile heart of the alignment stage.
 *
 * Covers the failure classes behind the June 2026 fix/revert churn (#88-#91):
 * Hebrew Unicode byte preservation in x-content/x-lemma, occurrence counting
 * for repeated words, bracket handling, nesting, and stdout purity.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { validateAlignmentIntegrity } from '../.claude/skills/utilities/scripts/validation/validate_alignment_integrity.mjs';
import { validateStructure } from '../.claude/skills/utilities/scripts/validation/validate_usfm_structure.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(here, '..');
const SCRIPT = join(ROOT, '.claude/skills/utilities/scripts/usfm/create_aligned_usfm.js');
const HEBREW = join(here, 'fixtures/hebrew_mini.usfm');
const SOURCE = join(here, 'fixtures/source_mini.usfm');
const MAPPING = join(here, 'fixtures/mapping_ch1.json');

const hebrewText = readFileSync(HEBREW, 'utf8');

function runScript(args, { captureStdout = false } = {}) {
  const out = execFileSync('node', [SCRIPT, ...args], { encoding: 'utf8' });
  return out;
}

function generateAligned(extraArgs = [], mappingFile = MAPPING) {
  const dir = mkdtempSync(join(tmpdir(), 'aligned-test-'));
  const outFile = join(dir, 'out.usfm');
  execFileSync('node', [
    SCRIPT,
    '--hebrew', HEBREW,
    '--mapping', mappingFile,
    '--source', SOURCE,
    '--output', outFile,
    '--chapter', '1',
    ...extraArgs,
  ], { encoding: 'utf8' });
  return readFileSync(outFile, 'utf8');
}

test('x-content and x-lemma are byte-exact copies of the Hebrew source', () => {
  const aligned = generateAligned();
  // Word 0 of verse 1, exactly as it appears in the Hebrew fixture
  const word0 = 'בְּ⁠רֵאשִׁ֖ית';
  const lemma0 = 'רֵאשִׁית';
  assert.match(aligned, new RegExp(`x-lemma="${lemma0}"`), 'lemma must be byte-exact');
  assert.match(aligned, new RegExp(`x-content="${word0}"`), 'x-content must be byte-exact');
  // Every milestone must carry non-empty lemma and content
  for (const m of aligned.matchAll(/\\zaln-s\s*\|([^\\]*)\\\*/g)) {
    assert.match(m[1], /x-lemma="[^"]+"/, `milestone has empty x-lemma: ${m[1]}`);
    assert.match(m[1], /x-content="[^"]+"/, `milestone has empty x-content: ${m[1]}`);
  }
});

test('repeated English words get correct case-sensitive occurrence numbering', () => {
  const aligned = generateAligned();
  // "the" appears twice in verse 1
  assert.match(aligned, /\\w the\|x-occurrence="1" x-occurrences="2"/);
  assert.match(aligned, /\\w the\|x-occurrence="2" x-occurrences="2"/);
  // "And" (capitalized) and "and" are distinct words, one each
  assert.match(aligned, /\\w And\|x-occurrence="1" x-occurrences="1"/);
  assert.match(aligned, /\\w and\|x-occurrence="1" x-occurrences="1"/);
  // "peace" appears twice in verse 2
  assert.match(aligned, /\\w peace\|x-occurrence="1" x-occurrences="2"/);
  assert.match(aligned, /\\w peace\|x-occurrence="2" x-occurrences="2"/);
});

test('repeated Hebrew source words get correct milestone occurrence numbering', () => {
  const aligned = generateAligned();
  const peaceMilestones = [...aligned.matchAll(/\\zaln-s\s*\|[^\\]*x-occurrence="(\d+)" x-occurrences="(\d+)"[^\\]*x-content="וְ⁠שָׁלוֹם"/g)];
  assert.equal(peaceMilestones.length, 2, 'expected two milestones for the repeated Hebrew word');
  const occs = peaceMilestones.map((m) => m[1]).sort();
  assert.deepEqual(occs, ['1', '2']);
  assert.ok(peaceMilestones.every((m) => m[2] === '2'), 'x-occurrences must be 2 for both');
});

test('multiple Hebrew indices produce nested milestones', () => {
  const aligned = generateAligned();
  // Verse 1: alignment [3,4] -> nested zaln-s for אֵת and הַשָּׁמַיִם, double close
  assert.match(aligned, /x-strong="H0853"/);
  assert.match(aligned, /x-strong="d:H8064"/);
  assert.match(aligned, /\\zaln-e\\\*\\zaln-e\\\*/, 'expected a double zaln-e close for nested milestones');
});

test('bracketed supplied words keep their braces in ULT mode', () => {
  const aligned = generateAligned();
  assert.match(aligned, /\{/);
  assert.match(aligned, /\\w is\|x-occurrence="1" x-occurrences="1"/);
  const verse2 = aligned.slice(aligned.indexOf('\\v 2'));
  const opens = (verse2.match(/{/g) || []).length;
  const closes = (verse2.match(/}/g) || []).length;
  assert.equal(opens, closes, 'braces must balance in verse 2');
});

test('poetry markers from the source are preserved', () => {
  const aligned = generateAligned();
  assert.match(aligned, /\\q1 \\v 2/, 'verse-initial \\q1 must precede \\v 2');
  assert.match(aligned, /^\\q2 /m, 'mid-verse \\q2 must be inserted');
});

test('stdout contains only USFM — no debug output', () => {
  // Without --output the USFM goes to stdout; any stray console.log corrupts it
  const stdout = runScript([
    '--hebrew', HEBREW,
    '--mapping', MAPPING,
    '--source', SOURCE,
    '--chapter', '1',
  ]);
  assert.ok(!stdout.includes('Start words:'), 'debug "Start words:" output must not appear on stdout');
  assert.match(stdout.trimStart(), /^\\id /, 'stdout must begin with the USFM \\id header');
});

test('generated output passes alignment integrity validation against the Hebrew source', () => {
  const aligned = generateAligned();
  const problems = validateAlignmentIntegrity(aligned, hebrewText, {});
  assert.deepEqual(problems, [], `expected clean validation, got: ${JSON.stringify(problems, null, 2)}`);
});

test('generated output passes structure validation', () => {
  const aligned = generateAligned();
  const problems = validateStructure(aligned, { sourceText: hebrewText, chapter: 1 });
  assert.deepEqual(problems, [], `expected clean structure, got: ${JSON.stringify(problems, null, 2)}`);
});

test('Unicode presentation-form drift in the mapping is caught by the integrity validator', () => {
  // Simulate the #88-#91 failure class: the AI mapping carries a visually
  // identical but byte-different Hebrew word (U+FB2A precomposed shin-with-dot
  // instead of shin + qamats + shin-dot as in the source).
  const mapping = JSON.parse(readFileSync(MAPPING, 'utf8'));
  const v2 = mapping[1];
  // vav+sheva+WJ + U+FB2A (precomposed shin-with-dot) + qamats+lamed+holam-vav+mem
  const driftWord = '\u05D5\u05B0\u2060\uFB2A\u05B8\u05DC\u05D5\u05B9\u05DD';
  const sourceWord = v2.hebrew_words[0].word;
  assert.notEqual(driftWord, sourceWord, 'drift word must differ in bytes');
  assert.equal(driftWord.normalize('NFC'), sourceWord.normalize('NFC'), 'drift word must be canonically equivalent');
  v2.hebrew_words[0].word = driftWord;
  v2.hebrew_words[2].word = driftWord;

  const dir = mkdtempSync(join(tmpdir(), 'aligned-drift-'));
  const driftMapping = join(dir, 'mapping_drift.json');
  writeFileSync(driftMapping, JSON.stringify([v2], null, 2));

  const aligned = generateAligned(['--verse', '2'], driftMapping);
  const problems = validateAlignmentIntegrity(aligned, hebrewText, {});
  const normalization = problems.filter((p) => p.code === 'content_normalization_mismatch');
  assert.ok(normalization.length >= 1,
    `expected content_normalization_mismatch, got: ${JSON.stringify(problems, null, 2)}`);
});
