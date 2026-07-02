#!/usr/bin/env node
/**
 * fetch_golden.mjs - Fetch published golden chapters from Door43 into committed fixtures.
 *
 * Downloads the published (human-polished) ULT, UST, and TN for the benchmark
 * chapters and stores single-chapter extracts under golden/. These fixtures are
 * committed so the benchmark target is stable even if Door43 master moves.
 *
 * Usage:
 *   node fetch_golden.mjs [--book NAM --chapter 1]   # default: all golden chapters
 *
 * Golden set (best published books, H1-2025 era polish):
 *   JOS 1 (narrative), NAM 1 (poetry/prophecy), MAL 1 (prophetic disputation)
 */

import { writeFileSync, mkdirSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';
import https from 'https';

const __dirname = dirname(fileURLToPath(import.meta.url));
const GOLDEN_DIR = resolve(__dirname, '../golden');

const DOOR43_API = 'https://git.door43.org/api/v1';
const DOOR43_RAW = 'https://git.door43.org/unfoldingWord';

const GOLDEN_SET = [
  { book: 'JOS', chapter: 1, fileNum: '06' },
  { book: 'NAM', chapter: 1, fileNum: '34' },
  { book: 'MAL', chapter: 1, fileNum: '39' },
];

export function httpGet(url) {
  return new Promise((resolvePromise, reject) => {
    https.get(url, { headers: { 'User-Agent': 'golden-benchmark-fetch/1.0' } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return resolvePromise(httpGet(res.headers.location));
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error(`HTTP ${res.statusCode} for ${url}`));
      }
      let data = '';
      res.setEncoding('utf8');
      res.on('data', (c) => { data += c; });
      res.on('end', () => resolvePromise(data));
    }).on('error', reject).setTimeout(30000, function () { this.destroy(); reject(new Error('Timeout: ' + url)); });
  });
}

/** Extract one chapter (with the \id line) from a whole-book USFM. */
export function extractChapter(usfm, chapter) {
  const idLine = (usfm.match(/^\\id .*$/m) || [''])[0];
  const startRe = new RegExp(`\\\\c\\s+${chapter}(?=\\s)`);
  const start = usfm.search(startRe);
  if (start === -1) throw new Error(`Chapter ${chapter} not found`);
  const rest = usfm.slice(start);
  const next = rest.slice(4).search(/\\c\s+\d/);
  const chapterText = next === -1 ? rest : rest.slice(0, next + 4);
  return `${idLine}\n${chapterText.trimEnd()}\n`;
}

/** Extract one chapter's rows (plus header) from a whole-book TN/TQ TSV. */
export function extractTsvChapter(tsv, chapter) {
  const lines = tsv.split('\n');
  const out = [lines[0]];
  const prefix = `${chapter}:`;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].startsWith(prefix)) out.push(lines[i]);
  }
  return out.join('\n') + '\n';
}

async function resolveUltUstRef() {
  try {
    const releases = JSON.parse(await httpGet(`${DOOR43_API}/repos/unfoldingWord/en_ult/releases?limit=1`));
    const rel = releases[0];
    if (rel?.tag_name) return { ref: `tag/${rel.tag_name}`, label: rel.tag_name };
    if (rel?.target_commitish) return { ref: `branch/${rel.target_commitish}`, label: rel.target_commitish };
  } catch (e) {
    console.error(`Release lookup failed (${e.message}); falling back to master`);
  }
  return { ref: 'branch/master', label: 'master' };
}

async function fetchOne({ book, chapter, fileNum }, ref) {
  const dir = join(GOLDEN_DIR, book);
  mkdirSync(dir, { recursive: true });
  const ch2 = String(chapter).padStart(2, '0');
  const results = {};

  for (const [repo, kind] of [['en_ult', 'ult'], ['en_ust', 'ust']]) {
    const url = `${DOOR43_RAW}/${repo}/raw/${ref.ref}/${fileNum}-${book}.usfm`;
    const usfm = await httpGet(url);
    const chapterUsfm = extractChapter(usfm, chapter);
    const dest = join(dir, `${book}-${ch2}.${kind}.usfm`);
    writeFileSync(dest, chapterUsfm);
    results[kind] = { url, bytes: chapterUsfm.length };
    console.error(`fetched ${kind}: ${dest} (${chapterUsfm.length} bytes)`);
  }

  const tnUrl = `${DOOR43_RAW}/en_tn/raw/branch/master/tn_${book}.tsv`;
  const tn = await httpGet(tnUrl);
  const tnChapter = extractTsvChapter(tn, chapter);
  const tnDest = join(dir, `${book}-${ch2}.tn.tsv`);
  writeFileSync(tnDest, tnChapter);
  results.tn = { url: tnUrl, bytes: tnChapter.length, rows: tnChapter.trim().split('\n').length - 1 };
  console.error(`fetched tn: ${tnDest} (${results.tn.rows} rows)`);

  return results;
}

async function main() {
  const args = process.argv.slice(2);
  let onlyBook = null, onlyChapter = null;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--book') onlyBook = args[++i]?.toUpperCase();
    else if (args[i] === '--chapter') onlyChapter = parseInt(args[++i], 10);
  }

  const set = GOLDEN_SET.filter((g) =>
    (!onlyBook || g.book === onlyBook) && (!onlyChapter || g.chapter === onlyChapter));
  if (set.length === 0) {
    console.error('No matching golden chapters. Known set: ' + GOLDEN_SET.map((g) => `${g.book} ${g.chapter}`).join(', '));
    process.exit(2);
  }

  const ref = await resolveUltUstRef();
  console.error(`Using ULT/UST ref: ${ref.label}`);

  const meta = { fetchedAt: new Date().toISOString(), ultUstRef: ref.label, chapters: {} };
  for (const g of set) {
    meta.chapters[`${g.book} ${g.chapter}`] = await fetchOne(g, ref);
  }
  mkdirSync(GOLDEN_DIR, { recursive: true });
  writeFileSync(join(GOLDEN_DIR, 'meta.json'), JSON.stringify(meta, null, 2));
  console.error(`Wrote ${join(GOLDEN_DIR, 'meta.json')}`);
}

import { pathToFileURL } from 'url';
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((e) => { console.error(e.message); process.exit(1); });
}
