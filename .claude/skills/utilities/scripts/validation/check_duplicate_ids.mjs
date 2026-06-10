#!/usr/bin/env node
/**
 * check_duplicate_ids.mjs - ID uniqueness and format gate for TN/TQ TSV files.
 *
 * Duplicate row IDs break downstream merge/delete operations (see closed
 * issue #74). This check is mandatory before insertion.
 *
 * Checks:
 *   - every ID matches [a-z][a-z0-9]{3}
 *   - no duplicate IDs within a file
 *   - no duplicate IDs across all files given in one invocation
 *   - optional --against <published.tsv>: no collisions with an existing
 *     published file (e.g. the Door43 master copy of the book)
 *
 * Usage:
 *   node check_duplicate_ids.mjs <file.tsv> [more.tsv ...] [--against <published.tsv>] [--json]
 *
 * Exit codes: 0 = clean, 1 = problems found, 2 = usage/IO error
 */

import { readFileSync } from 'fs';

const ID_RE = /^[a-z][a-z0-9]{3}$/;

export function parseTsvIds(text, label) {
  const lines = text.split('\n').filter((l) => l.trim() !== '');
  if (lines.length === 0) return { ids: [], problems: [{ level: 'error', code: 'empty_file', message: `${label}: file is empty` }] };
  const header = lines[0].split('\t');
  const idCol = header.indexOf('ID');
  if (idCol === -1) {
    return { ids: [], problems: [{ level: 'error', code: 'no_id_column', message: `${label}: no "ID" column in header` }] };
  }
  const ids = [];
  const problems = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = lines[i].split('\t');
    const id = (cells[idCol] || '').trim();
    const ref = (cells[0] || '').trim();
    if (!id) {
      problems.push({ level: 'error', code: 'missing_id', message: `${label} line ${i + 1} (${ref}): empty ID` });
      continue;
    }
    if (!ID_RE.test(id)) {
      problems.push({ level: 'error', code: 'id_format', message: `${label} line ${i + 1} (${ref}): ID "${id}" does not match [a-z][a-z0-9]{3}` });
    }
    ids.push({ id, line: i + 1, ref, label });
  }
  return { ids, problems };
}

export function checkDuplicateIds(files, againstFiles = []) {
  const problems = [];
  const seen = new Map(); // id -> first {label, line, ref}

  for (const { label, text } of files) {
    const { ids, problems: parseProblems } = parseTsvIds(text, label);
    problems.push(...parseProblems);
    for (const entry of ids) {
      if (seen.has(entry.id)) {
        const first = seen.get(entry.id);
        problems.push({
          level: 'error', code: 'duplicate_id',
          message: `Duplicate ID "${entry.id}": ${first.label} line ${first.line} (${first.ref}) and ${entry.label} line ${entry.line} (${entry.ref})`,
        });
      } else {
        seen.set(entry.id, entry);
      }
    }
  }

  for (const { label, text } of againstFiles) {
    const { ids } = parseTsvIds(text, label);
    const publishedIds = new Set(ids.map((e) => e.id));
    for (const [id, entry] of seen) {
      if (publishedIds.has(id)) {
        problems.push({
          level: 'error', code: 'id_collision',
          message: `ID "${id}" (${entry.label} line ${entry.line}, ${entry.ref}) collides with an existing ID in ${label}`,
        });
      }
    }
  }

  return problems;
}

function main() {
  const args = process.argv.slice(2);
  const files = [];
  const againstFiles = [];
  let asJson = false;
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--against': againstFiles.push(args[++i]); break;
      case '--json': asJson = true; break;
      case '--help': case '-h':
        console.log('Usage: node check_duplicate_ids.mjs <file.tsv> [more.tsv ...] [--against <published.tsv>] [--json]');
        process.exit(0);
        break;
      default:
        if (args[i].startsWith('-')) {
          console.error(`Unknown argument: ${args[i]}`);
          process.exit(2);
        }
        files.push(args[i]);
    }
  }
  if (files.length === 0) {
    console.error('Error: at least one TSV file is required');
    process.exit(2);
  }

  let loaded, loadedAgainst;
  try {
    loaded = files.map((f) => ({ label: f, text: readFileSync(f, 'utf8') }));
    loadedAgainst = againstFiles.map((f) => ({ label: f, text: readFileSync(f, 'utf8') }));
  } catch (e) {
    console.error(`Error reading input: ${e.message}`);
    process.exit(2);
  }

  const problems = checkDuplicateIds(loaded, loadedAgainst);
  if (asJson) {
    console.log(JSON.stringify({ files, problems }, null, 2));
  } else {
    for (const p of problems) {
      console.log(`${p.level.toUpperCase()} [${p.code}] ${p.message}`);
    }
    console.log(problems.length === 0
      ? `OK: no duplicate or malformed IDs across ${files.length} file(s)`
      : `FAIL: ${problems.length} problem(s)`);
  }
  process.exit(problems.length === 0 ? 0 : 1);
}

import { pathToFileURL } from 'url';
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
