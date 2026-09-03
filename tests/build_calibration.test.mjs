/**
 * Tests for loadSeeHowSharePct() in build_calibration.mjs — regenerating
 * calibration.json must carry the seeHowSharePct block forward, not drop it
 * (build_calibration.mjs has no way to recompute it from the CORPUS fetch,
 * which only sees counts, not note text).
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { loadSeeHowSharePct, DEFAULT_SEE_HOW_SHARE_PCT } from '../.claude/skills/golden-benchmark/scripts/build_calibration.mjs';

test('falls back to the default when calibration.json does not exist', () => {
  const dir = mkdtempSync(join(tmpdir(), 'calib-test-'));
  const dest = join(dir, 'calibration.json');
  assert.deepEqual(loadSeeHowSharePct(dest), DEFAULT_SEE_HOW_SHARE_PCT);
  rmSync(dir, { recursive: true, force: true });
});

test('falls back to the default when the existing file has no seeHowSharePct', () => {
  const dir = mkdtempSync(join(tmpdir(), 'calib-test-'));
  const dest = join(dir, 'calibration.json');
  writeFileSync(dest, JSON.stringify({ generatedBy: 'x' }));
  assert.deepEqual(loadSeeHowSharePct(dest), DEFAULT_SEE_HOW_SHARE_PCT);
  rmSync(dir, { recursive: true, force: true });
});

test('carries forward an existing seeHowSharePct block instead of the default', () => {
  const dir = mkdtempSync(join(tmpdir(), 'calib-test-'));
  const dest = join(dir, 'calibration.json');
  const custom = { description: 'custom', gate: false, corpusReference: { narrative_JOS: 99 } };
  writeFileSync(dest, JSON.stringify({ generatedBy: 'x', seeHowSharePct: custom }));
  assert.deepEqual(loadSeeHowSharePct(dest), custom);
  rmSync(dir, { recursive: true, force: true });
});

test('falls back to the default when the existing file is not valid JSON', () => {
  const dir = mkdtempSync(join(tmpdir(), 'calib-test-'));
  const dest = join(dir, 'calibration.json');
  writeFileSync(dest, 'not json{');
  assert.deepEqual(loadSeeHowSharePct(dest), DEFAULT_SEE_HOW_SHARE_PCT);
  rmSync(dir, { recursive: true, force: true });
});
