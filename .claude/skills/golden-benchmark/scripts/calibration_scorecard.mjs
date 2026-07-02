#!/usr/bin/env node
/**
 * calibration_scorecard.mjs - Score a generated notes TSV against the
 * published-density calibration bands.
 *
 * For unpublished books (no golden chapter to diff against), this gives an
 * objective density and type-mix readout beside human judgment.
 *
 * Usage (from repo root):
 *   node .claude/skills/golden-benchmark/scripts/calibration_scorecard.mjs \
 *     --tsv <notes.tsv> --verses <count> [--genre narrative|poetry|prophecy]
 *
 * Reads golden/calibration.json (built by build_calibration.mjs).
 */

import { readFileSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CALIBRATION = resolve(__dirname, '../golden/calibration.json');

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { genre: 'narrative' };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--tsv') out.tsv = args[++i];
    else if (args[i] === '--verses') out.verses = parseInt(args[++i], 10);
    else if (args[i] === '--genre') out.genre = args[++i];
  }
  if (!out.tsv || !out.verses) {
    console.error('Usage: calibration_scorecard.mjs --tsv <notes.tsv> --verses <count> [--genre narrative|poetry|prophecy]');
    process.exit(2);
  }
  return out;
}

function round(n, p = 2) { return Math.round(n * 10 ** p) / 10 ** p; }

function main() {
  const { tsv, verses, genre } = parseArgs();
  const cal = JSON.parse(readFileSync(CALIBRATION, 'utf8'));
  const band = cal.genres[genre];
  if (!band) {
    console.error(`Unknown genre "${genre}". Known: ${Object.keys(cal.genres).join(', ')}`);
    process.exit(2);
  }

  const lines = readFileSync(tsv, 'utf8').split('\n').filter((l) => l.trim());
  const header = lines[0].split('\t');
  const refIdx = header.indexOf('Reference');
  const srIdx = header.indexOf('SupportReference');
  const hasHeader = refIdx !== -1;

  const notes = [];
  for (let i = hasHeader ? 1 : 0; i < lines.length; i++) {
    const cols = lines[i].split('\t');
    const ref = hasHeader ? cols[refIdx] : cols[0];
    if (!ref || /:intro\b/.test(ref) || ref.startsWith('front:')) continue;
    const sr = (hasHeader ? cols[srIdx] : cols[3]) || '';
    notes.push({ ref, type: sr.split('/').pop() });
  }

  const perVerse = notes.length / verses;
  const family = (prefix) => notes.filter((n) => n.type.startsWith(prefix)).length;
  const gc = family('grammar-connect-');
  const wr = family('writing-');
  const discoursePct = notes.length ? round(((gc + wr) / notes.length) * 100, 1) : 0;
  const publishedShare = band.familyShareOfNotesPct['grammar-connect-*'] + band.familyShareOfNotesPct['writing-*'];

  const typeCounts = {};
  for (const n of notes) typeCounts[n.type] = (typeCounts[n.type] || 0) + 1;

  console.log(`Calibration scorecard: ${tsv}`);
  console.log(`Genre band: ${genre} (published books: ${band.books.join(', ')})`);
  console.log('');
  console.log(`Notes: ${notes.length} over ${verses} verses = ${round(perVerse)} notes/verse`);
  console.log(`Published ${genre} band: ${band.chapterDensity.min}-${band.chapterDensity.max} per chapter (median ${band.chapterDensity.median}, book-level ${band.notesPerVerse})`);
  console.log(`Ratio vs published median: ${round(perVerse / band.chapterDensity.median)}x   (target ceiling: 1.5x)`);
  console.log('');
  console.log(`Discourse families (grammar-connect-* + writing-*): ${gc + wr} notes = ${discoursePct}% of output`);
  console.log(`Published ${genre} share: ${round(publishedShare, 1)}%`);
  console.log('');
  console.log('Type mix (generated vs published per 100 verses):');
  const rates = band.typeRatesPer100Verses;
  for (const [t, c] of Object.entries(typeCounts).sort((a, b) => b[1] - a[1])) {
    const genRate = round((c / verses) * 100, 1);
    const pubRate = rates[t] ?? 0;
    const flag = pubRate === 0 ? ' (not in published ' + genre + ')' : genRate > pubRate * 1.5 ? ' (over 1.5x published rate)' : '';
    console.log(`  ${t}: ${c} (${genRate}/100v vs published ${pubRate}/100v)${flag}`);
  }
}

main();
