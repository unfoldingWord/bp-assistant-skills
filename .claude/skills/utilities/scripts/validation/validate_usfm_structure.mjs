#!/usr/bin/env node
/**
 * validate_usfm_structure.mjs - Structural gate for generated USFM (plain or aligned).
 *
 * Checks that a generated chapter is structurally sound before it moves to the
 * next pipeline stage:
 *   - \id header present
 *   - verse numbers start at 1, ascend contiguously, no duplicates (ranges like \v 1-2 count as both)
 *   - optional --source comparison: verse set must match the source (e.g. Hebrew) chapter
 *   - paired markers balance: \w/\w*, \zaln-s/\zaln-e, \f/\f*, \qs/\qs*
 *   - no empty verses (a \v with no text before the next verse/chapter)
 *   - balanced {curly braces} used for supplied words
 *   - no known debug artifacts (e.g. stray "Start words:" lines)
 *
 * Usage:
 *   node validate_usfm_structure.mjs --usfm <file> [--source <file>] [--chapter N] [--json]
 *
 * Exit codes: 0 = clean, 1 = problems found, 2 = usage/IO error
 */

import { readFileSync } from 'fs';

export function stripFetchedHeader(text) {
  if (text.startsWith('# Fetched:')) {
    return text.slice(text.indexOf('\n') + 1);
  }
  return text;
}

/**
 * Parse chapter/verse structure out of USFM text.
 * Returns { id, chapters: Map<chapterNum, { verses: [{num, endNum, raw}] }> }
 * Verse ranges ("\v 1-2") are recorded as covering each verse in the range.
 * Token-based: \c and \v markers are recognized anywhere in the text, not
 * only at line starts (USFM permits inline verse markers in prose output).
 */
export function parseStructure(text) {
  const chapters = new Map();
  const idMatch = text.match(/\\id\s+(\S+)/);
  const id = idMatch ? idMatch[1] : null;

  const markerRe = /\\c\s+(\d+)|\\v\s+(\d+)(?:-(\d+))?\s?/g;
  const markers = [];
  let m;
  while ((m = markerRe.exec(text)) !== null) {
    if (m[1] !== undefined) {
      markers.push({ kind: 'c', num: parseInt(m[1], 10), end: markerRe.lastIndex });
    } else {
      markers.push({
        kind: 'v',
        num: parseInt(m[2], 10),
        endNum: m[3] ? parseInt(m[3], 10) : parseInt(m[2], 10),
        end: markerRe.lastIndex,
      });
    }
  }

  let currentChapter = null;
  for (let i = 0; i < markers.length; i++) {
    const mk = markers[i];
    if (mk.kind === 'c') {
      currentChapter = mk.num;
      if (!chapters.has(currentChapter)) {
        chapters.set(currentChapter, { verses: [] });
      }
      continue;
    }
    if (currentChapter === null) continue;
    const next = markers[i + 1];
    // Verse content runs from the end of this marker to the start of the next
    // marker's backslash (or end of text). Strip a trailing poetry-marker
    // prefix that belongs to the next verse line (e.g. "\q1 " before "\v 3").
    let raw = text.slice(mk.end, next ? findMarkerStart(text, next) : text.length);
    raw = raw.replace(/\\q[12s]?\s*$/, '');
    chapters.get(currentChapter).verses.push({ num: mk.num, endNum: mk.endNum, raw });
  }

  return { id, chapters };
}

function findMarkerStart(text, marker) {
  // marker.end is the regex lastIndex (just past the marker); back up to the
  // backslash that starts it.
  const upto = text.slice(0, marker.end);
  return upto.lastIndexOf('\\');
}

/** Visible text of a verse with markers/attributes stripped (for emptiness check). */
export function verseVisibleText(raw) {
  return raw
    .replace(/\\zaln-s\s*\|[^\\]*\\\*/g, ' ')   // zaln-s with attributes
    .replace(/\\zaln-e\\\*/g, ' ')
    .replace(/\\w\s+([^|\\]*)(?:\|[^\\]*)?\\w\*/g, '$1') // keep word text
    .replace(/\\\+?[a-z0-9]+\*?\s*/g, ' ')       // any remaining markers
    .replace(/[{}]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function countOccurrences(text, regex) {
  const m = text.match(regex);
  return m ? m.length : 0;
}

/**
 * Validate one USFM text. Returns array of problem objects {level, chapter, verse, code, message}.
 * sourceText (optional): a reference USFM (e.g. Hebrew) whose verse set per chapter must match.
 */
export function validateStructure(text, { sourceText = null, chapter = null } = {}) {
  const problems = [];
  const t = stripFetchedHeader(text);
  const { id, chapters } = parseStructure(t);

  if (!id) {
    problems.push({ level: 'error', code: 'missing_id', message: 'No \\id header found' });
  }
  if (chapters.size === 0) {
    problems.push({ level: 'error', code: 'no_chapters', message: 'No \\c chapter markers found' });
    return problems;
  }

  const wanted = chapter !== null
    ? [...chapters.keys()].filter((c) => c === chapter)
    : [...chapters.keys()];
  if (chapter !== null && wanted.length === 0) {
    problems.push({ level: 'error', code: 'chapter_missing', message: `Chapter ${chapter} not found in file` });
    return problems;
  }

  let sourceChapters = null;
  if (sourceText) {
    sourceChapters = parseStructure(stripFetchedHeader(sourceText)).chapters;
  }

  for (const chNum of wanted) {
    const ch = chapters.get(chNum);
    const seen = new Set();
    let prevEnd = 0;

    for (const v of ch.verses) {
      for (let n = v.num; n <= v.endNum; n++) {
        if (seen.has(n)) {
          problems.push({ level: 'error', chapter: chNum, verse: n, code: 'duplicate_verse', message: `Verse ${chNum}:${n} appears more than once` });
        }
        seen.add(n);
      }
      if (v.num <= prevEnd) {
        problems.push({ level: 'error', chapter: chNum, verse: v.num, code: 'verse_out_of_order', message: `Verse ${chNum}:${v.num} is out of order (previous verse was ${prevEnd})` });
      }
      prevEnd = Math.max(prevEnd, v.endNum);

      const visible = verseVisibleText(v.raw);
      if (!visible) {
        problems.push({ level: 'error', chapter: chNum, verse: v.num, code: 'empty_verse', message: `Verse ${chNum}:${v.num} has no text content` });
      }

      const open = countOccurrences(v.raw, /{/g);
      const close = countOccurrences(v.raw, /}/g);
      if (open !== close) {
        problems.push({ level: 'error', chapter: chNum, verse: v.num, code: 'unbalanced_braces', message: `Verse ${chNum}:${v.num} has ${open} '{' but ${close} '}'` });
      }
    }

    // Contiguity from 1
    const nums = [...seen].sort((a, b) => a - b);
    if (nums.length > 0) {
      if (nums[0] !== 1) {
        problems.push({ level: 'error', chapter: chNum, code: 'missing_first_verse', message: `Chapter ${chNum} starts at verse ${nums[0]}, not 1 (use --source to validate partial files against the source verse range instead)` });
      }
      for (let i = 1; i < nums.length; i++) {
        if (nums[i] !== nums[i - 1] + 1) {
          for (let missing = nums[i - 1] + 1; missing < nums[i]; missing++) {
            problems.push({ level: 'error', chapter: chNum, verse: missing, code: 'missing_verse', message: `Verse ${chNum}:${missing} is missing (gap between ${nums[i - 1]} and ${nums[i]})` });
          }
        }
      }
    }

    // Source comparison: verse sets must match exactly
    if (sourceChapters) {
      const src = sourceChapters.get(chNum);
      if (!src) {
        problems.push({ level: 'error', chapter: chNum, code: 'source_chapter_missing', message: `Chapter ${chNum} not present in source file` });
      } else {
        const srcSet = new Set();
        for (const v of src.verses) {
          for (let n = v.num; n <= v.endNum; n++) srcSet.add(n);
        }
        for (const n of srcSet) {
          if (!seen.has(n)) {
            problems.push({ level: 'error', chapter: chNum, verse: n, code: 'missing_vs_source', message: `Verse ${chNum}:${n} exists in source but not in output` });
          }
        }
        for (const n of seen) {
          if (!srcSet.has(n)) {
            problems.push({ level: 'error', chapter: chNum, verse: n, code: 'extra_vs_source', message: `Verse ${chNum}:${n} exists in output but not in source` });
          }
        }
      }
    }
  }

  // Whole-file paired-marker balance
  const pairs = [
    ['\\w ', /\\w\s/g, /\\w\*/g, 'w_markers'],
    ['\\zaln-s', /\\zaln-s/g, /\\zaln-e/g, 'zaln_markers'],
    ['\\f ', /\\f\s/g, /\\f\*/g, 'footnote_markers'],
    ['\\qs', /\\qs\s/g, /\\qs\*/g, 'selah_markers'],
  ];
  for (const [label, openRe, closeRe, code] of pairs) {
    const opens = countOccurrences(t, openRe);
    const closes = countOccurrences(t, closeRe);
    if (opens !== closes) {
      problems.push({ level: 'error', code, message: `Unbalanced ${label} markers: ${opens} opening vs ${closes} closing` });
    }
  }

  // Known debug artifacts
  if (/^Start words:/m.test(t)) {
    problems.push({ level: 'error', code: 'debug_artifact', message: 'Debug output ("Start words:") found inside USFM content' });
  }

  return problems;
}

function main() {
  const args = process.argv.slice(2);
  let usfmFile = null, sourceFile = null, chapter = null, asJson = false;
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--usfm': usfmFile = args[++i]; break;
      case '--source': sourceFile = args[++i]; break;
      case '--chapter': chapter = parseInt(args[++i], 10); break;
      case '--json': asJson = true; break;
      case '--help': case '-h':
        console.log('Usage: node validate_usfm_structure.mjs --usfm <file> [--source <file>] [--chapter N] [--json]');
        process.exit(0);
        break;
      default:
        console.error(`Unknown argument: ${args[i]}`);
        process.exit(2);
    }
  }
  if (!usfmFile) {
    console.error('Error: --usfm <file> is required');
    process.exit(2);
  }

  let text, sourceText = null;
  try {
    text = readFileSync(usfmFile, 'utf8');
    if (sourceFile) sourceText = readFileSync(sourceFile, 'utf8');
  } catch (e) {
    console.error(`Error reading input: ${e.message}`);
    process.exit(2);
  }

  const problems = validateStructure(text, { sourceText, chapter });
  if (asJson) {
    console.log(JSON.stringify({ file: usfmFile, problems }, null, 2));
  } else {
    for (const p of problems) {
      const loc = p.chapter ? ` ${p.chapter}${p.verse ? ':' + p.verse : ''}` : '';
      console.log(`${p.level.toUpperCase()}${loc} [${p.code}] ${p.message}`);
    }
    console.log(problems.length === 0
      ? `OK: ${usfmFile} passed structure validation`
      : `FAIL: ${problems.length} problem(s) in ${usfmFile}`);
  }
  process.exit(problems.length === 0 ? 0 : 1);
}

import { pathToFileURL } from 'url';
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
