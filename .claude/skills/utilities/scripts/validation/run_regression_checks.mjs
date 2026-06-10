#!/usr/bin/env node
/**
 * run_regression_checks.mjs - Re-test every closed quality bug against new output.
 *
 * Each closed GitHub issue in unfoldingWord/bp-assistant-skills that described
 * a checkable output mistake is encoded in ../regression/regression-checks.json.
 * This runner applies the applicable checks to a generated file so a fixed
 * mistake that quietly returns is caught before delivery.
 *
 * Usage:
 *   node run_regression_checks.mjs --stage ULT --file output/AI-ULT/ISA/ISA-51.usfm --book ISA --chapter 51
 *   node run_regression_checks.mjs --stage TQ  --file output/tq/PSA/PSA-018.tsv --book PSA --chapter 18
 *
 * Stages: ULT | UST | TN | TQ | alignment
 *
 * Check semantics:
 *   - global checks run for any book (or the issue's pinned book)
 *   - pinned checks run only when the verse named in the check is present in the file
 *   - "invariant" checks that need cross-file data are listed as advisory, not auto-run
 *
 * Exit codes: 0 = all enforced checks pass, 1 = failures, 2 = usage/IO error
 */

import { readFileSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';
import { parseStructure, stripFetchedHeader } from './validate_usfm_structure.mjs';
import { checkDuplicateIds } from './check_duplicate_ids.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DEFAULT_CHECKS = resolve(__dirname, '../regression/regression-checks.json');

const USFM_STAGES = new Set(['ULT', 'UST', 'alignment']);
const TSV_STAGES = new Set(['TN', 'TQ']);

/** Verse text with markers stripped but braces and punctuation kept (for pattern matching). */
function verseMatchText(raw) {
  return raw
    .replace(/\\zaln-s\s*\|[^\\]*\\\*/g, ' ')
    .replace(/\\zaln-e\\\*/g, ' ')
    .replace(/\\w\s+([^|\\]*)(?:\|[^\\]*)?\\w\*/g, '$1')
    .replace(/\\\+?[a-z0-9]+\*?\s*/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function usfmVerseTexts(text) {
  const { chapters } = parseStructure(stripFetchedHeader(text));
  const map = new Map(); // "ch:v" -> match text
  for (const [chNum, ch] of chapters) {
    for (const v of ch.verses) {
      map.set(`${chNum}:${v.num}`, verseMatchText(v.raw));
    }
  }
  return map;
}

function tsvRows(text) {
  const lines = text.split('\n').filter((l) => l.trim());
  const header = lines[0].split('\t');
  return lines.slice(1).map((line, i) => {
    const cells = line.split('\t');
    return { line, lineNo: i + 2, ref: cells[0] || '', cells, header };
  });
}

/** Parse verse scopes like "ISA 54:3:" or "PSA 18:9-10:" from a check explain string. */
export function explainVerseScope(explain) {
  const m = (explain || '').match(/^(?:[A-Z0-9]{3}\s+)?(\d+):(\d+)/);
  if (!m) return null;
  return { chapter: parseInt(m[1], 10), verse: parseInt(m[2], 10) };
}

export function runChecks({ stage, text, book = null, chapter = null, checksData }) {
  const results = []; // {status: pass|fail|skip|advisory, issue, explain, detail}
  const isUsfm = USFM_STAGES.has(stage);
  const verseTexts = isUsfm ? usfmVerseTexts(text) : null;
  const rows = !isUsfm ? tsvRows(text) : null;

  for (const issue of checksData) {
    const stages = [issue.stage, ...(issue.alsoStages || [])];
    if (!stages.includes(stage)) continue;
    if (issue.book && book && issue.book !== book) continue;
    if (issue.book && !book) continue; // book-scoped check needs a book to apply to

    for (const check of issue.checks) {
      const base = { issue: issue.issue, title: issue.title, explain: check.explain };

      if (check.type === 'invariant') {
        if (check.name === 'no_duplicate_ids' && !isUsfm) {
          const problems = checkDuplicateIds([{ label: 'file', text }]);
          const dupes = problems.filter((p) => p.code === 'duplicate_id' || p.code === 'id_format');
          results.push(dupes.length
            ? { ...base, status: 'fail', detail: dupes.map((d) => d.message).join('; ') }
            : { ...base, status: 'pass' });
        } else {
          results.push({ ...base, status: 'advisory', detail: `invariant "${check.name}" needs cross-file data — review manually or via tn-quality-check` });
        }
        continue;
      }

      const re = new RegExp(check.pattern, check.flags || '');
      const scope = check.wholeFile ? null : explainVerseScope(check.explain);

      if (check.wholeFile) {
        if (check.onlyChapter && chapter && check.onlyChapter !== chapter) {
          results.push({ ...base, status: 'skip', detail: `only applies to chapter ${check.onlyChapter}` });
          continue;
        }
        const matched = re.test(text);
        const ok = check.type === 'must_match' ? matched : !matched;
        results.push({ ...base, status: ok ? 'pass' : 'fail' });
        continue;
      }

      if (scope) {
        // Verse-scoped check: only enforce when that verse is in this file
        if (isUsfm) {
          const vt = verseTexts.get(`${scope.chapter}:${scope.verse}`);
          if (vt === undefined) {
            results.push({ ...base, status: 'skip', detail: `verse ${scope.chapter}:${scope.verse} not in file` });
            continue;
          }
          const matched = re.test(vt);
          const ok = check.type === 'must_match' ? matched : !matched;
          results.push({ ...base, status: ok ? 'pass' : 'fail', detail: ok ? undefined : `verse ${scope.chapter}:${scope.verse}: "${vt.slice(0, 120)}..."` });
        } else {
          const verseRows = rows.filter((r) => r.ref === `${scope.chapter}:${scope.verse}` || r.ref.startsWith(`${scope.chapter}:${scope.verse}-`));
          if (verseRows.length === 0) {
            results.push({ ...base, status: 'skip', detail: `no rows for ${scope.chapter}:${scope.verse}` });
            continue;
          }
          const joined = verseRows.map((r) => r.line).join('\n');
          const matched = re.test(joined);
          const ok = check.type === 'must_match' ? matched : !matched;
          results.push({ ...base, status: ok ? 'pass' : 'fail' });
        }
        continue;
      }

      // Global pattern check
      if (isUsfm) {
        const failures = [];
        for (const [ref, vt] of verseTexts) {
          if (re.test(vt)) failures.push(ref);
        }
        if (check.type === 'must_match') {
          results.push({ ...base, status: failures.length ? 'pass' : 'fail' });
        } else {
          results.push(failures.length
            ? { ...base, status: 'fail', detail: `matched in verse(s): ${failures.join(', ')}` }
            : { ...base, status: 'pass' });
        }
      } else {
        const skipRe = check.skipRowMatching ? new RegExp(check.skipRowMatching) : null;
        const failures = [];
        for (const r of rows) {
          if (skipRe && skipRe.test(r.line)) continue;
          if (re.test(r.line)) failures.push(`${r.ref} (line ${r.lineNo})`);
        }
        if (check.type === 'must_match') {
          results.push({ ...base, status: failures.length ? 'pass' : 'fail' });
        } else {
          results.push(failures.length
            ? { ...base, status: 'fail', detail: `matched rows: ${failures.slice(0, 10).join('; ')}${failures.length > 10 ? '…' : ''}` }
            : { ...base, status: 'pass' });
        }
      }
    }
  }

  return results;
}

function main() {
  const args = process.argv.slice(2);
  let stage = null, file = null, book = null, chapter = null, checksFile = DEFAULT_CHECKS, asJson = false;
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--stage': stage = args[++i]; break;
      case '--file': file = args[++i]; break;
      case '--book': book = args[++i]?.toUpperCase(); break;
      case '--chapter': chapter = parseInt(args[++i], 10); break;
      case '--checks': checksFile = args[++i]; break;
      case '--json': asJson = true; break;
      case '--help': case '-h':
        console.log('Usage: node run_regression_checks.mjs --stage ULT|UST|TN|TQ|alignment --file <path> [--book ISA] [--chapter 51] [--json]');
        process.exit(0);
        break;
      default:
        console.error(`Unknown argument: ${args[i]}`);
        process.exit(2);
    }
  }
  if (!stage || !file) {
    console.error('Error: --stage and --file are required');
    process.exit(2);
  }
  if (!USFM_STAGES.has(stage) && !TSV_STAGES.has(stage)) {
    console.error(`Error: unknown stage "${stage}"`);
    process.exit(2);
  }

  let text, checksData;
  try {
    text = readFileSync(file, 'utf8');
    checksData = JSON.parse(readFileSync(checksFile, 'utf8'));
  } catch (e) {
    console.error(`Error reading input: ${e.message}`);
    process.exit(2);
  }

  const results = runChecks({ stage, text, book, chapter, checksData });
  const failed = results.filter((r) => r.status === 'fail');
  const passed = results.filter((r) => r.status === 'pass');
  const advisory = results.filter((r) => r.status === 'advisory');

  if (asJson) {
    console.log(JSON.stringify({ file, stage, book, chapter, summary: { pass: passed.length, fail: failed.length, advisory: advisory.length }, results }, null, 2));
  } else {
    for (const r of failed) {
      console.log(`FAIL [#${r.issue}] ${r.explain}${r.detail ? ` — ${r.detail}` : ''}`);
    }
    for (const r of advisory) {
      console.log(`ADVISORY [#${r.issue}] ${r.detail}`);
    }
    console.log(failed.length === 0
      ? `OK: ${passed.length} regression check(s) passed (${advisory.length} advisory, ${results.filter((r) => r.status === 'skip').length} skipped) for ${file}`
      : `FAIL: ${failed.length} regression check(s) failed for ${file} — a previously fixed mistake has returned`);
  }
  process.exit(failed.length === 0 ? 0 : 1);
}

import { pathToFileURL } from 'url';
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
