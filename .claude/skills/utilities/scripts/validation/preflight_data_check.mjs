#!/usr/bin/env node
/**
 * preflight_data_check.mjs - Loud failure when runtime reference data is missing.
 *
 * The generation skills treat data/issues_resolved.txt as final authority and
 * consult glossaries, quick-ref decisions, and the Strong's index — but all of
 * these are fetched at runtime and generation proceeds silently if a fetch
 * failed. This gate makes the absence loud *before* generation starts.
 *
 * Usage:
 *   node preflight_data_check.mjs --book NAM [--stage ult|ust|tn|all] [--root <repo root>] [--json]
 *
 * Exit codes: 0 = all required data present, 1 = something required is missing, 2 = usage error
 */

import { existsSync, statSync, readFileSync, readdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Canonical book order; USFM file numbers are index+1 for OT, index+2 for NT (40 is unused).
const BOOKS = [
  'GEN','EXO','LEV','NUM','DEU','JOS','JDG','RUT','1SA','2SA','1KI','2KI',
  '1CH','2CH','EZR','NEH','EST','JOB','PSA','PRO','ECC','SNG','ISA','JER',
  'LAM','EZK','DAN','HOS','JOL','AMO','OBA','JON','MIC','NAM','HAB','ZEP',
  'HAG','ZEC','MAL',
  'MAT','MRK','LUK','JHN','ACT','ROM','1CO','2CO','GAL','EPH','PHP','COL',
  '1TH','2TH','1TI','2TI','TIT','PHM','HEB','JAS','1PE','2PE','1JN','2JN',
  '3JN','JUD','REV',
];

export function bookFileNumber(book) {
  const idx = BOOKS.indexOf(book.toUpperCase());
  if (idx === -1) return null;
  const num = idx < 39 ? idx + 1 : idx + 2; // MAT is 41
  return String(num).padStart(2, '0');
}

function checkFile(root, relPath, { minBytes = 1, required = true, note = '' } = {}) {
  const full = resolve(root, relPath);
  if (!existsSync(full)) {
    return { path: relPath, status: required ? 'MISSING' : 'WARN', required, note: note || 'not found' };
  }
  const st = statSync(full);
  if (st.size < minBytes) {
    return { path: relPath, status: required ? 'MISSING' : 'WARN', required, note: `present but only ${st.size} bytes (expected >= ${minBytes})` };
  }
  const ageDays = (Date.now() - st.mtimeMs) / 86400000;
  return { path: relPath, status: 'OK', required, note: `${(st.size / 1024).toFixed(0)} KB, ${ageDays.toFixed(1)}d old`, ageDays };
}

function checkDirNonEmpty(root, relPath, { required = true, note = '' } = {}) {
  const full = resolve(root, relPath);
  if (!existsSync(full)) {
    return { path: relPath, status: required ? 'MISSING' : 'WARN', required, note: note || 'directory not found' };
  }
  const entries = readdirSync(full).filter((e) => !e.startsWith('.'));
  if (entries.length === 0) {
    return { path: relPath, status: required ? 'MISSING' : 'WARN', required, note: 'directory is empty' };
  }
  return { path: relPath, status: 'OK', required, note: `${entries.length} file(s)` };
}

export function preflightCheck({ book, stage = 'all', root }) {
  const results = [];
  const num = bookFileNumber(book);
  if (!num) {
    return { results: [{ path: `(book ${book})`, status: 'MISSING', required: true, note: `unknown book code "${book}"` }], ok: false };
  }
  const bookFile = `${num}-${book.toUpperCase()}.usfm`;
  const wantUlt = stage === 'all' || stage === 'ult';
  const wantUst = stage === 'all' || stage === 'ust';
  const wantTn = stage === 'all' || stage === 'tn';

  // Shared sources
  results.push(checkFile(root, `data/hebrew_bible/${bookFile}`, { minBytes: 10_000, note: 'Hebrew source for the book (fetch_hebrew_bible)' }));
  results.push(checkFile(root, 'data/glossary/project_glossary.md', { minBytes: 1_000, note: 'editorial overrides (fetch_glossary)' }));
  results.push(checkFile(root, 'data/quick-ref/ult_decisions.csv', { minBytes: 100, note: 'accumulated ULT decisions' }));

  if (wantUlt) {
    const ir = checkFile(root, 'data/issues_resolved.txt', { minBytes: 1_000, note: 'final authority — content team decisions' });
    results.push(ir);
    for (const g of ['hebrew_ot_glossary.csv', 'psalms_reference.csv', 'sacrifice_terminology.csv', 'biblical_measurements.csv', 'biblical_phrases.csv']) {
      results.push(checkFile(root, `data/glossary/${g}`, { minBytes: 100, note: 'standard glossary (fetch_glossary)' }));
    }
    const idx = checkFile(root, 'data/cache/strongs_index.json', { minBytes: 100_000, note: 'Strong\'s precedent index (build_strongs_index)' });
    if (idx.status === 'OK' && idx.ageDays > 7) {
      idx.status = 'WARN';
      idx.note += ' — over a week old, consider rebuilding';
    }
    results.push(idx);
    results.push(checkDirNonEmpty(root, 'data/published_ult_english', { required: false, note: 'published precedent (not required for unpublished books, but lookups will be weaker)' }));
  }

  if (wantUst) {
    const opt = checkFile(root, 'data/issues_resolved_optimized.txt', { minBytes: 1_000, required: false });
    const plain = checkFile(root, 'data/issues_resolved.txt', { minBytes: 1_000, required: false });
    if (opt.status !== 'OK' && plain.status !== 'OK') {
      results.push({ path: 'data/issues_resolved_optimized.txt (or issues_resolved.txt)', status: 'MISSING', required: true, note: 'neither the optimized nor the plain issues-resolved file is present' });
    } else {
      results.push(opt.status === 'OK' ? opt : plain);
    }
    results.push(checkFile(root, `data/t4t/${bookFile}`, { minBytes: 10_000, note: 'T4T base text for UST (fetch_t4t)' }));
    results.push(checkFile(root, 'data/quick-ref/ust_decisions.csv', { minBytes: 50, note: 'accumulated UST decisions' }));
    results.push(checkDirNonEmpty(root, 'data/published_ust_english', { required: false, note: 'published UST precedent' }));
  }

  if (wantTn) {
    results.push(checkDirNonEmpty(root, 'data/ta-flat', { note: 'Translation Academy articles (SupportReference targets)' }));
    results.push(checkDirNonEmpty(root, 'data/published-tns', { required: false, note: 'published TN precedent index' }));
  }

  const ok = !results.some((r) => r.status === 'MISSING');
  return { results, ok };
}

function main() {
  const args = process.argv.slice(2);
  let book = null, stage = 'all', root = null, asJson = false;
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--book': book = args[++i]; break;
      case '--stage': stage = (args[++i] || '').toLowerCase(); break;
      case '--root': root = args[++i]; break;
      case '--json': asJson = true; break;
      case '--help': case '-h':
        console.log('Usage: node preflight_data_check.mjs --book NAM [--stage ult|ust|tn|all] [--root <repo root>] [--json]');
        process.exit(0);
        break;
      default:
        console.error(`Unknown argument: ${args[i]}`);
        process.exit(2);
    }
  }
  if (!book) {
    console.error('Error: --book is required (e.g. --book NAM)');
    process.exit(2);
  }
  if (!['ult', 'ust', 'tn', 'all'].includes(stage)) {
    console.error(`Error: unknown stage "${stage}" (expected ult, ust, tn, or all)`);
    process.exit(2);
  }
  if (!root) {
    // script lives at .claude/skills/utilities/scripts/validation/ — repo root is five levels up
    root = resolve(__dirname, '../../../../..');
  }

  const { results, ok } = preflightCheck({ book, stage, root });
  if (asJson) {
    console.log(JSON.stringify({ book, stage, root, ok, results }, null, 2));
  } else {
    const width = Math.max(...results.map((r) => r.path.length));
    for (const r of results) {
      console.log(`${r.status.padEnd(8)} ${r.path.padEnd(width)}  ${r.note}`);
    }
    if (ok) {
      console.log(`\nOK: required reference data for ${book} (${stage}) is present.`);
    } else {
      const missing = results.filter((r) => r.status === 'MISSING');
      console.log(`\nFAIL: ${missing.length} required data source(s) missing for ${book} (${stage}).`);
      console.log('Fetch them before generating (curate-published-data.mjs / fetch_* workspace tools).');
      console.log('Generating without them will silently diverge from content-team decisions.');
    }
  }
  process.exit(ok ? 0 : 1);
}

import { pathToFileURL } from 'url';
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
