/**
 * Tests for the issue-identification checklist candidate detector (#224).
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { checklistCandidates } from '../.claude/skills/issue-identification/scripts/detection/checklist_candidates.mjs';

const w = (form, morph) => `\\w ${form}|lemma="x" strong="H0001" x-morph="He,${morph}"\\w*`;

const HEBREW = [
  '\\c 3',
  // v1: "you, you will warn" -> independent pronoun beside a same-person verb
  `\\v 1 ${w('וְאַתָּה', 'C:Pp2ms')} ${w('כִּי', 'C')} ${w('הִזְהַרְתָּ', 'Vhp2ms')}`,
  // v2: "you are dying, and you will not live" -> vav starts a new clause
  `\\v 2 ${w('מֵת', 'Vqrmsa')} ${w('אַתָּה', 'Pp2ms')} ${w('וְלֹא', 'C:Tn')} ${w('תִחְיֶה', 'Vqi2ms')}`,
  // v3: "you, take" -> imperatives are not flagged
  `\\v 3 ${w('וְאַתָּה', 'C:Pp2ms')} ${w('קַח', 'Vqv2ms')}`,
  // v4: plural you after singular
  `\\v 4 ${w('תְּחַשְּׁבוּן', 'Vpi2mp')}`,
  // v5: still plural, no new row
  `\\v 5 ${w('לָכֶם', 'R:Sp2mp')}`,
  // v6: back to singular (feminine)
  `\\v 6 ${w('מִמֵּךְ', 'R:Sp2fs')}`,
].join('\n');

const ULT = [
  '\\c 3',
  '\\p',
  '\\v 1 “And you, if you warn him, ‘Thus says Yahweh, “Turn back.”’”',
  '\\q1 \\v 2 What shall I say?',
  '\\q2 For he has spoken to me.',
  '\\p \\v 3 For the king’s men came.',
  '\\v 4 You plan.',
  '\\v 5 For you.',
  '\\v 6 From you.',
].join('\n');

const rows = checklistCandidates(HEBREW, ULT);
const has = (ref, type) => rows.some((r) => r[0] === ref && r[1] === type);

test('emphatic pronoun beside a finite verb in its clause', () => {
  assert.ok(has('3:1', 'writing-pronouns'), JSON.stringify(rows));
  assert.ok(!has('3:2', 'writing-pronouns'), 'vav-prefixed word ends the clause');
  assert.ok(!has('3:3', 'writing-pronouns'), 'imperative is not flagged');
});

test('second-person number switches', () => {
  assert.ok(!has('3:1', 'figs-yousingular'), 'first second person is singular: no row');
  assert.ok(has('3:4', 'figs-yousingular'));
  assert.ok(!has('3:5', 'figs-yousingular'));
  assert.ok(has('3:6', 'figs-yousingular'));
  assert.ok(has('3:6', 'writing-pronouns'), 'addressee change');
});

test('third-level quotation and apostrophes', () => {
  assert.ok(has('3:1', 'figs-quotemarks'));
  assert.ok(!has('3:3', 'figs-quotemarks'));
});

test('sentence-initial For in poetry only', () => {
  assert.ok(has('3:2', 'grammar-connect-logic-result'));
  assert.ok(!has('3:3', 'grammar-connect-logic-result'), 'prose verse');
});
