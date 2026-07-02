#!/usr/bin/env node
/**
 * build_calibration.mjs - Build the note-density calibration dataset from
 * published Door43 data.
 *
 * Fetches en_tn (master) and en_ult (pinned release tag) for a corpus of
 * well-edited published books, then emits golden/calibration.json with:
 *   - per-book, per-chapter note counts, verse counts, and notes/verse
 *   - per-genre density bands (across chapters and whole books)
 *   - per-type base rates (notes per 100 verses) and note-share by genre
 *
 * The output feeds the selectivity contract in issue-identification and the
 * calibration scorecard used for unpublished-book evaluation.
 *
 * Usage (from repo root):
 *   node .claude/skills/golden-benchmark/scripts/build_calibration.mjs
 *
 * Corpus: JOS, NAM, MAL (gold trio - recent, minimal AI, top editors
 * end-to-end) plus HAG, SNG, ZEP, JOB, 1SA (approved additions).
 * Intro rows (front:intro, N:intro) are excluded from note counts; the
 * calibration is about verse-anchored translator notes.
 */

import { writeFileSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { httpGet } from './fetch_golden.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const GOLDEN_DIR = resolve(__dirname, '../golden');

const DOOR43_RAW = 'https://git.door43.org/unfoldingWord';
const ULT_REF = 'tag/v88';

const CORPUS = [
  { book: 'JOS', fileNum: '06', genre: 'narrative' },
  { book: '1SA', fileNum: '09', genre: 'narrative' },
  { book: 'JOB', fileNum: '18', genre: 'poetry' },
  { book: 'SNG', fileNum: '22', genre: 'poetry' },
  { book: 'NAM', fileNum: '34', genre: 'prophecy' },
  { book: 'ZEP', fileNum: '36', genre: 'prophecy' },
  { book: 'HAG', fileNum: '37', genre: 'prophecy' },
  { book: 'MAL', fileNum: '39', genre: 'prophecy' },
];

const GOLD_TRIO = new Set(['JOS', 'NAM', 'MAL']);

/** Verse count per chapter from whole-book USFM (max verse number seen). */
function verseCounts(usfm) {
  const counts = {};
  let chapter = null;
  for (const line of usfm.split('\n')) {
    const c = line.match(/^\\c\s+(\d+)/);
    if (c) { chapter = c[1]; counts[chapter] = 0; continue; }
    if (!chapter) continue;
    for (const v of line.matchAll(/\\v\s+(\d+)(?:-(\d+))?/g)) {
      const hi = parseInt(v[2] || v[1], 10);
      if (hi > counts[chapter]) counts[chapter] = hi;
    }
  }
  return counts;
}

/** Parse en_tn TSV into verse-anchored note records (intro rows excluded). */
function parseNotes(tsv) {
  const lines = tsv.split('\n');
  const header = lines[0].split('\t');
  const refIdx = header.indexOf('Reference');
  const srIdx = header.indexOf('SupportReference');
  const notes = [];
  let introRows = 0;
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    const cols = lines[i].split('\t');
    const ref = cols[refIdx] || '';
    if (/:intro\b/.test(ref) || ref.startsWith('front:')) { introRows++; continue; }
    const m = ref.match(/^(\d+):(\d+)/);
    if (!m) continue;
    const sr = cols[srIdx] || '';
    const type = sr ? sr.split('/').pop() : '';
    notes.push({ chapter: m[1], type });
  }
  return { notes, introRows };
}

function round(n, places = 2) {
  const f = 10 ** places;
  return Math.round(n * f) / f;
}

function median(arr) {
  const s = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

async function buildBook({ book, fileNum, genre }) {
  const ultUrl = `${DOOR43_RAW}/en_ult/raw/${ULT_REF}/${fileNum}-${book}.usfm`;
  const tnUrl = `${DOOR43_RAW}/en_tn/raw/branch/master/tn_${book}.tsv`;
  const [usfm, tsv] = [await httpGet(ultUrl), await httpGet(tnUrl)];

  const verses = verseCounts(usfm);
  const { notes, introRows } = parseNotes(tsv);

  const chapters = {};
  for (const [ch, vCount] of Object.entries(verses)) {
    const nCount = notes.filter((n) => n.chapter === ch).length;
    chapters[ch] = {
      verses: vCount,
      notes: nCount,
      notesPerVerse: vCount ? round(nCount / vCount) : 0,
    };
  }

  const totalVerses = Object.values(verses).reduce((a, b) => a + b, 0);
  const typeCounts = {};
  for (const n of notes) {
    if (!n.type) continue;
    typeCounts[n.type] = (typeCounts[n.type] || 0) + 1;
  }

  return {
    book, genre, introRows,
    totals: {
      verses: totalVerses,
      notes: notes.length,
      notesPerVerse: round(notes.length / totalVerses),
    },
    chapters,
    typeCounts,
    typeRatesPer100Verses: Object.fromEntries(
      Object.entries(typeCounts)
        .sort((a, b) => b[1] - a[1])
        .map(([t, c]) => [t, round((c / totalVerses) * 100)])),
  };
}

function genreSummary(books) {
  const chapterDensities = books.flatMap((b) =>
    Object.values(b.chapters).map((c) => c.notesPerVerse));
  const totalVerses = books.reduce((a, b) => a + b.totals.verses, 0);
  const totalNotes = books.reduce((a, b) => a + b.totals.notes, 0);
  const typeCounts = {};
  for (const b of books) {
    for (const [t, c] of Object.entries(b.typeCounts)) {
      typeCounts[t] = (typeCounts[t] || 0) + c;
    }
  }
  const familyShare = (prefix) => round(
    Object.entries(typeCounts)
      .filter(([t]) => t.startsWith(prefix))
      .reduce((a, [, c]) => a + c, 0) / totalNotes * 100, 1);
  return {
    books: books.map((b) => b.book),
    verses: totalVerses,
    notes: totalNotes,
    notesPerVerse: round(totalNotes / totalVerses),
    chapterDensity: {
      min: round(Math.min(...chapterDensities)),
      median: round(median(chapterDensities)),
      max: round(Math.max(...chapterDensities)),
    },
    familyShareOfNotesPct: {
      'grammar-connect-*': familyShare('grammar-connect-'),
      'writing-*': familyShare('writing-'),
      'figs-*': familyShare('figs-'),
      'translate-*': familyShare('translate-'),
    },
    typeRatesPer100Verses: Object.fromEntries(
      Object.entries(typeCounts)
        .sort((a, b) => b[1] - a[1])
        .map(([t, c]) => [t, round((c / totalVerses) * 100)])),
  };
}

async function main() {
  const bookResults = [];
  for (const entry of CORPUS) {
    console.error(`fetching ${entry.book}...`);
    bookResults.push(await buildBook(entry));
  }

  const genres = {};
  for (const genre of [...new Set(CORPUS.map((c) => c.genre))]) {
    genres[genre] = genreSummary(bookResults.filter((b) => b.genre === genre));
  }

  const trio = bookResults.filter((b) => GOLD_TRIO.has(b.book));
  const trioNotes = trio.reduce((a, b) => a + b.totals.notes, 0);
  const trioFamily = (prefix) => round(
    trio.reduce((a, b) => a + Object.entries(b.typeCounts)
      .filter(([t]) => t.startsWith(prefix))
      .reduce((s, [, c]) => s + c, 0), 0) / trioNotes * 100, 1);

  const calibration = {
    generatedBy: 'golden-benchmark/scripts/build_calibration.mjs',
    fetchedAt: new Date().toISOString(),
    sources: { tn: 'en_tn branch/master', ult: `en_ult ${ULT_REF}` },
    countingRules: 'verse-anchored notes only; front:intro and chapter :intro rows excluded; chapter verse count = highest verse number in published ULT',
    goldTrio: {
      books: [...GOLD_TRIO],
      notes: trioNotes,
      familyShareOfNotesPct: {
        'grammar-connect-*': trioFamily('grammar-connect-'),
        'writing-*': trioFamily('writing-'),
      },
    },
    genres,
    books: Object.fromEntries(bookResults.map((b) => [b.book, b])),
  };

  const dest = join(GOLDEN_DIR, 'calibration.json');
  writeFileSync(dest, JSON.stringify(calibration, null, 2) + '\n');
  console.error(`wrote ${dest}`);

  for (const b of bookResults) {
    console.error(`  ${b.book} (${b.genre}): ${b.totals.notes} notes / ${b.totals.verses} verses = ${b.totals.notesPerVerse}/v`);
  }
  console.error(`  gold trio: ${trioNotes} notes; grammar-connect ${calibration.goldTrio.familyShareOfNotesPct['grammar-connect-*']}%, writing ${calibration.goldTrio.familyShareOfNotesPct['writing-*']}%`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((e) => { console.error(e.message); process.exit(1); });
}
