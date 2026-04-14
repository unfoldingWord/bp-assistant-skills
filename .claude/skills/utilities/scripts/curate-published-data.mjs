#!/usr/bin/env node
/**
 * curate-published-data.js — Unified curation script for workspace/data/
 *
 * Replaces 6+ Python fetch/build scripts with a single Node.js entry point.
 * Discovers published books from Door43 releases API, fetches ULT/UST/TN/Hebrew/T4T,
 * fetches Google Sheets/Docs, extracts unaligned English via usfm-js, resolves
 * GL quotes on TNs, and builds search indexes.
 *
 * Usage:
 *   node curate-published-data.js                        # Full run (all steps)
 *   node curate-published-data.js --check                # Dry run: report changes
 *   node curate-published-data.js --step fetch-door43    # Just Door43 fetch
 *   node curate-published-data.js --step fetch-google    # Just Google fetch
 *   node curate-published-data.js --step extract-english # Just unaligned extraction
 *   node curate-published-data.js --step resolve-quotes  # Just GLQuote resolution
 *   node curate-published-data.js --step build-indexes   # Just rebuild indexes
 *   node curate-published-data.js --force                # Ignore cache, refetch all
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'fs';
import { resolve, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import https from 'https';
import http from 'http';

// ESM __dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Project root: workspace/
const PROJECT_ROOT = resolve(__dirname, '..', '..', '..', '..');
const DATA_DIR = resolve(PROJECT_ROOT, 'data');
const CACHE_DIR = resolve(DATA_DIR, 'cache');
const MANIFEST_PATH = resolve(CACHE_DIR, 'published_manifest.json');

// Import usfm-js for proper USFM parsing (same package used by parse_usfm.js)
import usfm from 'usfm-js';

// ── Configuration ──────────────────────────────────────────────────────────

const DOOR43_API = 'https://git.door43.org/api/v1';
const DOOR43_RAW = 'https://git.door43.org/unfoldingWord';

const REPOS = {
  ult: 'en_ult',
  ust: 'en_ust',
  tn:  'en_tn',
  uhb: 'hbo_uhb',
  t4t: 'en_t4t',
};

// Google Sheets/Docs IDs
const GOOGLE = {
  glossary: {
    sheetId: '1pop2F61kRCRBgUvf8zHVwx9s-CBE8x3PyXojrTjJ3Lc',
    tabs: {
      hebrew_ot_glossary:    1711192506,
      biblical_measurements: 1835633752,
      psalms_reference:      1739562476,
      sacrifice_terminology: 243454428,
      biblical_phrases:      1459152614,
    },
  },
  templates: {
    sheetId: '1ot6A7RxcsxM_Wv94sauoTAaRPO5Q-gynFqMHeldnM64',
    gid: 0,
  },
  issuesResolved: {
    docId: '1C0C7Qsm78fM0tuLyVZEAs-IWtClNo9nqbsAZkAFeFio',
  },
};

// OT books only (01-39)
const MAX_OT_NUMBER = 39;

// Index settings
const MAX_SAMPLE_REFS = 5;
const MAX_SAMPLES = 5;
const MAX_KEYWORD_ISSUES = 10;
const MIN_KEYWORD_LEN = 3;

const STOP_WORDS = new Set([
  'the','a','an','and','or','but','in','on','at','to','for','of','with','by',
  'from','as','is','was','are','were','be','been','being','have','has','had',
  'do','does','did','will','would','shall','should','may','might','can','could',
  'not','no','nor','so','if','then','than','that','this','these','those','it',
  'its','he','him','his','she','her','hers','they','them','their','theirs','we',
  'us','our','ours','you','your','yours','i','me','my','mine','who','whom',
  'whose','which','what','when','where','how','why','all','each','every','both',
  'few','more','most','other','some','such','only','own','same','also','very',
  'just','about','up','out','into','over','after','before','between','under',
  'again','there','here','once','during','while','through','because','until',
  'against','above','below','down','off','any','too','now','even','still','yet',
  'already','always','never','often','sometimes','much','many','well','back',
  'away','upon','among','along','across','around','within','without','toward',
  'towards','whether','though','although','however','therefore','thus','hence',
  'else','instead','rather','quite','perhaps','certainly','indeed','especially',
  'merely','simply','actually','apparently','anyway',
]);

// ── HTTP helpers ───────────────────────────────────────────────────────────

function httpFetch(url, { maxRedirects = 5 } = {}) {
  return new Promise((resolvePromise, reject) => {
    const client = url.startsWith('https') ? https : http;
    const req = client.get(url, { headers: { 'User-Agent': 'curate-published-data/1.0' } }, (res) => {
      // Follow redirects
      if ((res.statusCode === 301 || res.statusCode === 302 || res.statusCode === 303) && res.headers.location) {
        if (maxRedirects <= 0) return reject(new Error('Too many redirects for ' + url));
        return resolvePromise(httpFetch(res.headers.location, { maxRedirects: maxRedirects - 1 }));
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error('HTTP ' + res.statusCode + ' for ' + url));
      }
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => resolvePromise(Buffer.concat(chunks).toString('utf-8')));
    });
    req.on('error', reject);
    req.setTimeout(30000, () => { req.destroy(); reject(new Error('Timeout fetching ' + url)); });
  });
}

function fetchJSON(url) {
  return httpFetch(url).then(JSON.parse);
}

// ── Utility ────────────────────────────────────────────────────────────────

function ensureDir(dir) {
  mkdirSync(dir, { recursive: true });
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function readManifest() {
  if (!existsSync(MANIFEST_PATH)) return { release: null, books: [], lastRun: null };
  try {
    return JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
  } catch {
    return { release: null, books: [], lastRun: null };
  }
}

function writeManifest(manifest) {
  ensureDir(CACHE_DIR);
  writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2));
}

function log(msg) {
  console.log('[curate] ' + msg);
}

function stripBom(text) {
  return text.replace(/^\uFEFF/, '');
}

function getCachedDate(filepath) {
  if (!existsSync(filepath)) return null;
  const first = readFileSync(filepath, 'utf-8').split('\n')[0];
  if (first.startsWith('# Fetched: ')) return first.replace('# Fetched: ', '');
  return null;
}

function shouldRefreshWeekly(cachedDateStr) {
  if (!cachedDateStr) return true;
  const cached = new Date(cachedDateStr);
  if (isNaN(cached.getTime())) return true;
  const now = new Date();
  const daysSinceThursday = (now.getDay() - 4 + 7) % 7;
  const lastThursday = new Date(now);
  lastThursday.setDate(now.getDate() - daysSinceThursday);
  lastThursday.setHours(0, 0, 0, 0);
  return cached < lastThursday;
}

// ── Step 1: Discover published books from releases API ─────────────────────

async function discoverPublishedBooks() {
  log('Checking Door43 releases...');
  const releases = await fetchJSON(DOOR43_API + '/repos/unfoldingWord/' + REPOS.ult + '/releases?limit=1');
  if (!releases.length) throw new Error('No releases found for en_ult');

  const release = releases[0];
  const tag = release.tag_name;
  // target_commitish is the branch the release was cut from (e.g. "release_v88").
  // This is what we use to fetch USFM — it resolves correctly via raw/branch/ URLs.
  const releaseBranch = release.target_commitish || 'master';
  log('Latest release: ' + tag + ' (branch: ' + releaseBranch + ', ' + release.published_at + ')');

  // Extract book codes from asset names: en_ult_01-GEN_v88_A4.html
  // Only OT books (num <= MAX_OT_NUMBER). Do not hardcode additional books —
  // if a book is not in the release assets it is not published.
  const bookSet = new Set();
  for (const asset of release.assets || []) {
    const m = asset.name.match(/en_ult_(\d+)-(\w+)_v\d+/);
    if (m) {
      const num = parseInt(m[1], 10);
      if (num <= MAX_OT_NUMBER) {
        bookSet.add(m[1] + '-' + m[2]);
      }
    }
  }

  const books = [...bookSet].sort();
  log('Published OT books: ' + books.length + ' (' + books.map(b => b.split('-')[1]).join(', ') + ')');
  return { tag, releaseBranch, books };
}

// ── Step 2-3: Fetch Door43 data (ULT, UST, TN, Hebrew, T4T) ───────────────

async function fetchDoor43Data(books, force, manifest, releaseBranch) {
  const dirs = {
    ult:    resolve(DATA_DIR, 'published_ult'),
    ust:    resolve(DATA_DIR, 'published_ust'),
    tn:     resolve(DATA_DIR, 'published-tns'),
    hebrew: resolve(DATA_DIR, 'hebrew_bible'),
    t4t:    resolve(DATA_DIR, 't4t'),
  };

  for (const d of Object.values(dirs)) ensureDir(d);

  const previousBooks = new Set(manifest.books || []);
  const newBooks = books.filter(b => !previousBooks.has(b));
  if (newBooks.length) {
    log('New books detected: ' + newBooks.map(b => b.split('-')[1]).join(', '));
  }

  let fetched = 0;

  for (const book of books) {
    const parts = book.split('-');
    const num = parts[0];
    const code = parts[1];
    const filename = num + '-' + code + '.usfm';
    const tnFilename = 'tn_' + code + '.tsv';

    // ULT and UST are fetched from the release branch (target_commitish) so
    // published_* folders contain officially released content, not whatever
    // happens to be on master. TN, Hebrew Bible, and T4T do not follow the
    // same release discipline, so they continue to pull from master.
    const ultUstRef = releaseBranch ? 'branch/' + releaseBranch : 'branch/master';
    const targets = [
      { url: DOOR43_RAW + '/' + REPOS.ult + '/raw/' + ultUstRef + '/' + filename, dest: resolve(dirs.ult, filename) },
      { url: DOOR43_RAW + '/' + REPOS.ust + '/raw/' + ultUstRef + '/' + filename, dest: resolve(dirs.ust, filename) },
      { url: DOOR43_RAW + '/' + REPOS.tn + '/raw/branch/master/' + tnFilename, dest: resolve(dirs.tn, tnFilename) },
      { url: DOOR43_RAW + '/' + REPOS.uhb + '/raw/branch/master/' + filename, dest: resolve(dirs.hebrew, filename) },
      { url: DOOR43_RAW + '/' + REPOS.t4t + '/raw/branch/master/' + filename, dest: resolve(dirs.t4t, filename) },
    ];

    for (const target of targets) {
      // Skip if cached and not forcing
      if (!force && existsSync(target.dest)) {
        const first = readFileSync(target.dest, 'utf-8').split('\n')[0];
        if (first.startsWith('# Fetched:') && !newBooks.includes(book)) continue;
      }

      try {
        const content = await httpFetch(target.url);
        writeFileSync(target.dest, '# Fetched: ' + today() + '\n' + content);
        fetched++;
      } catch (err) {
        // T4T may not exist for all books
        if (!target.dest.includes('/t4t/')) {
          log('  Warning: Failed to fetch ' + basename(target.dest) + ': ' + err.message);
        }
      }
    }

    process.stdout.write('  ' + code + ' ');
  }

  console.log();
  log('Fetched ' + fetched + ' files from Door43');
  return newBooks;
}

// ── Step 4: Fetch Google Sheets/Docs ───────────────────────────────────────

async function fetchGoogleData(force) {
  log('Fetching Google Sheets/Docs...');

  // Glossary sheets
  const glossaryDir = resolve(DATA_DIR, 'glossary');
  ensureDir(glossaryDir);

  for (const [name, gid] of Object.entries(GOOGLE.glossary.tabs)) {
    const dest = resolve(glossaryDir, name + '.csv');

    if (!force && existsSync(dest)) {
      const cached = getCachedDate(dest);
      if (cached && !shouldRefreshWeekly(cached)) continue;
    }

    try {
      const url = 'https://docs.google.com/spreadsheets/d/' + GOOGLE.glossary.sheetId + '/export?format=csv&gid=' + gid;
      const content = stripBom(await httpFetch(url));
      writeFileSync(dest, '# Fetched: ' + today() + '\n' + content);
      log('  ' + name + '.csv fetched');
    } catch (err) {
      log('  Warning: ' + name + '.csv failed: ' + err.message);
    }
  }

  // Templates CSV
  const templatesDest = resolve(DATA_DIR, 'templates.csv');
  if (force || !existsSync(templatesDest) || shouldRefreshWeekly(getCachedDate(templatesDest))) {
    try {
      const url = 'https://docs.google.com/spreadsheets/d/' + GOOGLE.templates.sheetId + '/export?format=csv&gid=' + GOOGLE.templates.gid;
      const content = stripBom(await httpFetch(url));
      writeFileSync(templatesDest, '# Fetched: ' + today() + '\n' + content);
      log('  templates.csv fetched');
    } catch (err) {
      log('  Warning: templates.csv failed: ' + err.message);
    }
  }

  // Issues resolved
  const issuesDest = resolve(DATA_DIR, 'issues_resolved.txt');
  if (force || !existsSync(issuesDest) || shouldRefreshWeekly(getCachedDate(issuesDest))) {
    try {
      const url = 'https://docs.google.com/document/d/' + GOOGLE.issuesResolved.docId + '/export?format=txt';
      const content = stripBom(await httpFetch(url));
      writeFileSync(issuesDest, '# Fetched: ' + today() + '\n' + content);
      log('  issues_resolved.txt fetched');
    } catch (err) {
      log('  Warning: issues_resolved.txt failed: ' + err.message);
    }
  }
}

// ── Step 5: Extract unaligned English ULT & UST via usfm-js ───────────────

function extractPlainText(parsed) {
  const lines = [];

  for (const header of parsed.headers || []) {
    if (header.tag && header.content) {
      lines.push('\\' + header.tag + ' ' + header.content);
    }
  }

  for (const [chapterNum, chapterData] of Object.entries(parsed.chapters || {})) {
    lines.push('\\c ' + chapterNum);
    lines.push('\\p');

    for (const [verseNum, verseData] of Object.entries(chapterData)) {
      const verseText = extractVerseText(verseData.verseObjects || []);
      lines.push('\\v ' + verseNum + ' ' + verseText);
    }
  }

  return lines.join('\n');
}

function extractVerseText(objects) {
  const parts = [];
  for (const obj of objects) {
    if (obj.type === 'quote' && obj.tag) {
      if (obj.text) {
        parts.push('\n\\' + obj.tag + ' ' + obj.text.replace(/\n$/, ''));
      }
    } else if (obj.type === 'text' && obj.text) {
      parts.push(obj.text);
    } else if (obj.tag === 'w' && obj.type === 'word' && obj.text) {
      parts.push(obj.text);
    } else if (obj.children) {
      parts.push(extractVerseText(obj.children));
    }
  }
  return parts.join('');
}

function extractAlignmentsFromParsed(parsed, bookId) {
  const alignments = [];

  for (const [chapterNum, chapterData] of Object.entries(parsed.chapters || {})) {
    const chapter = parseInt(chapterNum, 10);
    for (const [verseNum, verseData] of Object.entries(chapterData)) {
      const verse = parseInt(verseNum, 10);
      if (verseData.verseObjects) {
        collectAlignments(verseData.verseObjects, bookId, chapter, verse, alignments);
      }
    }
  }

  return alignments;
}

function collectAlignments(objects, bookId, chapter, verse, alignments) {
  for (const obj of objects) {
    if (obj.tag === 'zaln' && obj.type === 'milestone') {
      const englishWords = gatherEnglishWords(obj.children || []);
      alignments.push({
        ref: bookId + ' ' + chapter + ':' + verse,
        chapter,
        verse,
        source: {
          word: obj.content || '',
          lemma: obj.lemma || '',
          strong: obj.strong || '',
          morph: obj.morph || '',
        },
        english: englishWords.join(' '),
        englishWords,
      });
      if (obj.children) {
        collectAlignments(obj.children, bookId, chapter, verse, alignments);
      }
    } else if (obj.children) {
      collectAlignments(obj.children, bookId, chapter, verse, alignments);
    }
  }
}

function gatherEnglishWords(children) {
  const words = [];
  for (const child of children) {
    if (child.tag === 'w' && child.type === 'word' && child.text) {
      words.push(child.text);
    }
    if (child.children && child.tag !== 'zaln') {
      words.push(...gatherEnglishWords(child.children));
    }
  }
  return words;
}

function extractUnalignedEnglish() {
  log('Extracting unaligned English ULT & UST...');

  const sources = [
    { dir: resolve(DATA_DIR, 'published_ult'), outDir: resolve(DATA_DIR, 'published_ult_english'), label: 'ULT' },
    { dir: resolve(DATA_DIR, 'published_ust'), outDir: resolve(DATA_DIR, 'published_ust_english'), label: 'UST' },
  ];

  // Also collect alignment data from ULT for step 6 (GL quote resolution)
  const ultAlignments = new Map(); // book code -> alignments[]

  for (const source of sources) {
    ensureDir(source.outDir);

    const files = existsSync(source.dir) ? readdirSync(source.dir).filter(f => f.endsWith('.usfm')).sort() : [];
    let count = 0;

    for (const filename of files) {
      const inPath = resolve(source.dir, filename);
      const outPath = resolve(source.outDir, filename);

      let content = readFileSync(inPath, 'utf-8');
      // Skip the "# Fetched:" header line
      if (content.startsWith('# Fetched:')) {
        content = content.split('\n').slice(1).join('\n');
      }

      try {
        const parsed = usfm.toJSON(content);

        // Extract book ID
        let bookId = '';
        for (const header of parsed.headers || []) {
          if (header.tag === 'id') { bookId = header.content.split(' ')[0]; break; }
        }

        // Extract plain text
        const plain = extractPlainText(parsed);
        writeFileSync(outPath, '# Extracted: ' + today() + '\n' + plain);

        // Collect alignment data from ULT for step 6
        if (source.label === 'ULT' && bookId) {
          ultAlignments.set(bookId, extractAlignmentsFromParsed(parsed, bookId));
        }

        count++;
      } catch (err) {
        log('  Warning: Failed to parse ' + filename + ': ' + err.message);
      }
    }

    log('  ' + source.label + ': ' + count + ' files extracted');
  }

  return ultAlignments;
}

// ── Step 6: Resolve GL quotes on TNs ──────────────────────────────────────

function resolveGlQuotes(ultAlignments) {
  log('Resolving GL quotes on TNs...');

  const tnDir = resolve(DATA_DIR, 'published-tns');
  if (!existsSync(tnDir)) { log('  No TN directory found, skipping'); return; }

  const files = readdirSync(tnDir).filter(f => f.startsWith('tn_') && f.endsWith('.tsv')).sort();
  let totalResolved = 0;
  let totalEmpty = 0;

  for (const filename of files) {
    const bookCode = filename.replace('tn_', '').replace('.tsv', '');
    const alignments = ultAlignments.get(bookCode);
    if (!alignments) continue;

    // Build lookup: "chapter:verse" -> alignments
    const alignByVerse = new Map();
    for (const a of alignments) {
      const key = a.chapter + ':' + a.verse;
      if (!alignByVerse.has(key)) alignByVerse.set(key, []);
      alignByVerse.get(key).push(a);
    }

    const filepath = resolve(tnDir, filename);
    const lines = readFileSync(filepath, 'utf-8').split('\n');
    if (lines.length < 2) continue;

    const header = lines[0].split('\t');
    const glQuoteIdx = header.indexOf('GLQuote');
    const quoteIdx = header.indexOf('Quote');
    const refIdx = header.indexOf('Reference');

    if (glQuoteIdx === -1 || quoteIdx === -1 || refIdx === -1) continue;

    let fileResolved = 0;
    let fileChanged = false;

    for (let i = 1; i < lines.length; i++) {
      const fields = lines[i].split('\t');
      if (fields.length <= glQuoteIdx) continue;

      // Skip if GLQuote already populated
      if (fields[glQuoteIdx] && fields[glQuoteIdx].trim()) continue;

      // Skip if no Hebrew quote
      const hebrewQuote = fields[quoteIdx];
      if (!hebrewQuote || !hebrewQuote.trim()) continue;

      // Parse reference
      const ref = fields[refIdx];
      if (!ref || ref.includes('intro')) continue;
      const refMatch = ref.match(/(\d+):(\d+)/);
      if (!refMatch) continue;

      totalEmpty++;
      const verseKey = parseInt(refMatch[1], 10) + ':' + parseInt(refMatch[2], 10);
      const verseAligns = alignByVerse.get(verseKey);
      if (!verseAligns) continue;

      // Strip Hebrew cantillation marks for matching
      const stripCantillation = (s) => s.replace(/[\u0591-\u05C7]/g, '');

      // Match Hebrew tokens to English
      const hebrewTokens = hebrewQuote.split(/\s*\u2026\s*|\s+/).filter(Boolean);
      const matchedEnglish = [];

      for (const token of hebrewTokens) {
        const stripped = stripCantillation(token);
        const match = verseAligns.find(a =>
          a.source.word === token || stripCantillation(a.source.word) === stripped
        );
        if (match && match.english) {
          matchedEnglish.push(match.english);
        }
      }

      if (matchedEnglish.length > 0) {
        fields[glQuoteIdx] = matchedEnglish.join(' ... ');
        lines[i] = fields.join('\t');
        fileChanged = true;
        fileResolved++;
        totalResolved++;
      }
    }

    if (fileChanged) {
      writeFileSync(filepath, lines.join('\n'));
      log('  ' + filename + ': resolved ' + fileResolved + ' GL quotes');
    }
  }

  log('  Resolved ' + totalResolved + '/' + totalEmpty + ' empty GL quotes');
}

// ── Step 7: Build indexes ──────────────────────────────────────────────────

function normalizeStrong(raw) {
  const result = raw.replace(/^(?:[a-z]:)+/, '');
  if (!/^[HG]\d/.test(result)) return null;
  return result;
}

function buildStrongsIndex(sourceDir, label, releaseTag) {
  log('Building ' + label + " Strong's index...");

  if (!existsSync(sourceDir)) { log('  Source not found: ' + sourceDir); return null; }

  const files = readdirSync(sourceDir).filter(f => f.endsWith('.usfm')).sort();
  if (!files.length) { log('  No USFM files found'); return null; }

  // Aggregate: strong -> {lemma, content, renderings: Map(text -> {count, refs})}
  const agg = new Map();
  let totalAlignments = 0;

  for (const filename of files) {
    let content = readFileSync(resolve(sourceDir, filename), 'utf-8');
    if (content.startsWith('# Fetched:')) content = content.split('\n').slice(1).join('\n');

    // Stack-based zaln parsing (same approach as query_word.js)
    const lines = content.split('\n');
    let bookId = '', chapter = 0, verse = 0;
    const stack = [];

    const markerRe = /\\zaln-s\s+\|([^\\]*?)\\\*|\\zaln-e\\\*|\\w\s+([^|]*?)\|[^\\]*?\\w\*/g;

    for (const line of lines) {
      let m;
      if ((m = line.match(/\\id\s+(\w+)/))) bookId = m[1];
      if ((m = line.match(/\\c\s+(\d+)/))) chapter = parseInt(m[1], 10);
      if ((m = line.match(/\\v\s+(\d+)/))) verse = parseInt(m[1], 10);

      let match;
      markerRe.lastIndex = 0;
      while ((match = markerRe.exec(line)) !== null) {
        if (match[0].startsWith('\\zaln-s')) {
          const attrStr = match[1];
          const attrs = {};
          let am;
          if ((am = attrStr.match(/x-strong="([^"]+)"/))) attrs.strong = am[1];
          if ((am = attrStr.match(/x-content="([^"]+)"/))) attrs.content = am[1];
          if ((am = attrStr.match(/x-lemma="([^"]+)"/))) attrs.lemma = am[1];
          stack.push({ attrs, words: [] });
        } else if (match[0].startsWith('\\zaln-e')) {
          if (stack.length) {
            const closed = stack.pop();
            const english = closed.words.join(' ');
            if (stack.length) stack[stack.length - 1].words.push(...closed.words);

            const strongRaw = closed.attrs.strong || '';
            const strongNorm = strongRaw ? normalizeStrong(strongRaw) : null;
            if (strongNorm && english) {
              totalAlignments++;
              if (!agg.has(strongNorm)) {
                agg.set(strongNorm, { lemma: '', content: '', renderings: new Map() });
              }
              const entry = agg.get(strongNorm);
              if (!entry.lemma && closed.attrs.lemma) entry.lemma = closed.attrs.lemma;
              if (!entry.content && closed.attrs.content) entry.content = closed.attrs.content;

              if (!entry.renderings.has(english)) {
                entry.renderings.set(english, { count: 0, refs: [] });
              }
              const rendering = entry.renderings.get(english);
              rendering.count++;
              if (rendering.refs.length < MAX_SAMPLE_REFS) {
                rendering.refs.push(bookId + ' ' + chapter + ':' + verse);
              }
            }
          }
        } else if (match[2] !== undefined) {
          const word = match[2].trim();
          if (word && stack.length) stack[stack.length - 1].words.push(word);
        }
      }
    }
  }

  // Build output
  const index = {
    _meta: {
      built: today(),
      source_dir: sourceDir.replace(PROJECT_ROOT + '/', ''),
      file_count: files.length,
      total_alignments: totalAlignments,
      unique_strongs: agg.size,
      release: releaseTag || 'unknown',
    },
  };

  const sorted = [...agg.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  for (const [strong, data] of sorted) {
    const renderings = [...data.renderings.entries()]
      .map(([text, info]) => ({ text, count: info.count, refs: info.refs }))
      .sort((a, b) => b.count - a.count);
    index[strong] = {
      lemma: data.lemma,
      total: renderings.reduce((s, r) => s + r.count, 0),
      renderings,
    };
  }

  log('  ' + label + ': ' + files.length + ' files, ' + totalAlignments + ' alignments, ' + agg.size + " unique Strong's");
  return index;
}

function buildTnIndex() {
  log('Building TN index...');

  const sourceDir = resolve(DATA_DIR, 'published-tns');
  if (!existsSync(sourceDir)) { log('  Source not found'); return null; }

  const files = readdirSync(sourceDir).filter(f => f.startsWith('tn_') && f.endsWith('.tsv')).sort();
  if (!files.length) { log('  No TN files found'); return null; }

  // by_issue: issue -> {count, books(Set), samples[]}
  const issueAgg = new Map();
  // by_keyword: keyword -> Map(issue -> {count, sample_ref})
  const keywordAgg = new Map();
  let totalNotes = 0;

  for (const filename of files) {
    const bookCode = filename.replace('tn_', '').replace('.tsv', '');
    const lines = readFileSync(resolve(sourceDir, filename), 'utf-8').split('\n');
    if (lines.length < 2) continue;

    const headerFields = lines[0].split('\t');
    const fieldMap = {};
    headerFields.forEach((h, i) => { fieldMap[h] = i; });

    for (let i = 1; i < lines.length; i++) {
      const row = lines[i].split('\t');
      if (row.length < 4) continue;

      // Detect format (PSA/RUT vs standard)
      let book, refStr, supportRef, glQuote, note;
      if (fieldMap.Book !== undefined) {
        book = row[fieldMap.Book] || bookCode;
        refStr = (row[fieldMap.Chapter] || '') + ':' + (row[fieldMap.Verse] || '');
        supportRef = row[fieldMap.SupportReference] || '';
        glQuote = fieldMap.GLQuote !== undefined ? (row[fieldMap.GLQuote] || '') : '';
        note = row[fieldMap.OccurrenceNote !== undefined ? fieldMap.OccurrenceNote : fieldMap.Note] || '';
      } else {
        book = bookCode;
        refStr = row[fieldMap.Reference !== undefined ? fieldMap.Reference : 0] || '';
        supportRef = row[fieldMap.SupportReference !== undefined ? fieldMap.SupportReference : 3] || '';
        glQuote = fieldMap.GLQuote !== undefined ? (row[fieldMap.GLQuote] || '') : '';
        note = fieldMap.Note !== undefined ? (row[fieldMap.Note] || '') : '';
      }

      if (refStr.includes('intro')) continue;

      // Extract issue type from SupportReference
      const issueMatch = supportRef.match(/translate\/(.+)$/);
      let issueType = issueMatch ? issueMatch[1] : null;
      if (!issueType && /^(figs-|grammar-|writing-|translate-)/.test(supportRef)) {
        issueType = supportRef;
      }
      if (!issueType) continue;

      totalNotes++;
      const fullRef = book + ' ' + refStr;

      // Aggregate by issue
      if (!issueAgg.has(issueType)) issueAgg.set(issueType, { count: 0, books: new Set(), samples: [] });
      const issueEntry = issueAgg.get(issueType);
      issueEntry.count++;
      issueEntry.books.add(book);
      if (issueEntry.samples.length < MAX_SAMPLES) {
        let notePreview = (note || '').replace(/\\n/g, ' ').trim();
        notePreview = notePreview.replace(/\[([^\]]*)\]\([^)]*\)/g, '$1');
        notePreview = notePreview.replace(/\[\[rc:\/\/[^\]]*\]\]/g, '');
        notePreview = notePreview.slice(0, 120).trim();

        issueEntry.samples.push({
          ref: fullRef,
          quote: glQuote.slice(0, 80),
          note_preview: notePreview,
        });
      }

      // Aggregate by keyword from GLQuote
      const words = (glQuote || '').toLowerCase().match(/[a-z']+/g) || [];
      for (const w of words) {
        if (STOP_WORDS.has(w) || w.length < MIN_KEYWORD_LEN) continue;
        if (!keywordAgg.has(w)) keywordAgg.set(w, new Map());
        const kwIssues = keywordAgg.get(w);
        if (!kwIssues.has(issueType)) kwIssues.set(issueType, { count: 0, sample_ref: '' });
        const kwEntry = kwIssues.get(issueType);
        kwEntry.count++;
        if (!kwEntry.sample_ref) kwEntry.sample_ref = fullRef;
      }
    }
  }

  // Build output
  const index = {
    _meta: {
      built: today(),
      source_dir: 'data/published-tns/',
      file_count: files.length,
      total_notes: totalNotes,
      unique_issues: issueAgg.size,
      unique_keywords: keywordAgg.size,
    },
    by_issue: {},
    by_keyword: {},
  };

  // Sort issues by count desc
  const sortedIssues = [...issueAgg.entries()].sort((a, b) => b[1].count - a[1].count);
  for (const [issue, data] of sortedIssues) {
    index.by_issue[issue] = {
      count: data.count,
      books: [...data.books].sort(),
      samples: data.samples,
    };
  }

  // Sort keywords alpha, top-N issues per keyword
  for (const kw of [...keywordAgg.keys()].sort()) {
    const issues = keywordAgg.get(kw);
    const topIssues = [...issues.entries()]
      .sort((a, b) => b[1].count - a[1].count)
      .slice(0, MAX_KEYWORD_ISSUES);
    const total = topIssues.reduce((s, e) => s + e[1].count, 0);
    if (total < 2) continue;
    index.by_keyword[kw] = topIssues.map(([issue, info]) => ({
      issue, count: info.count, sample_ref: info.sample_ref,
    }));
  }

  log('  ' + files.length + ' files, ' + totalNotes + ' notes, ' + issueAgg.size + ' issues, ' + keywordAgg.size + ' keywords');
  return index;
}

function buildAllIndexes(releaseTag) {
  ensureDir(CACHE_DIR);

  const ultIndex = buildStrongsIndex(resolve(DATA_DIR, 'published_ult'), 'ULT', releaseTag);
  if (ultIndex) {
    writeFileSync(resolve(CACHE_DIR, 'strongs_index.json'), JSON.stringify(ultIndex));
  }

  const ustIndex = buildStrongsIndex(resolve(DATA_DIR, 'published_ust'), 'UST', releaseTag);
  if (ustIndex) {
    writeFileSync(resolve(CACHE_DIR, 'ust_index.json'), JSON.stringify(ustIndex));
  }

  const tnIndex = buildTnIndex();
  if (tnIndex) {
    writeFileSync(resolve(CACHE_DIR, 'tn_index.json'), JSON.stringify(tnIndex));
  }
}

// ── CLI ────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const force = args.includes('--force');
  const check = args.includes('--check');
  const stepIdx = args.indexOf('--step');
  const step = stepIdx !== -1 ? args[stepIdx + 1] : null;

  const manifest = readManifest();

  // Step 1: Discover
  let releaseInfo;
  try {
    releaseInfo = await discoverPublishedBooks();
  } catch (err) {
    log('Failed to check releases: ' + err.message);
    log('Using cached manifest');
    releaseInfo = { tag: manifest.release, books: manifest.books || [] };
  }

  if (check) {
    const prevBooks = new Set(manifest.books || []);
    const newBooks = releaseInfo.books.filter(b => !prevBooks.has(b));
    const tagChanged = releaseInfo.tag !== manifest.release;
    log('Release: ' + (manifest.release || 'none') + ' -> ' + releaseInfo.tag + (tagChanged ? ' (CHANGED)' : ''));
    log('Books: ' + releaseInfo.books.length + ' published, ' + newBooks.length + ' new');
    if (newBooks.length) log('  New: ' + newBooks.map(b => b.split('-')[1]).join(', '));
    return;
  }

  const runStep = (name) => !step || step === name;

  // Step 2-3: Fetch Door43 data
  let newBooks = [];
  if (runStep('fetch-door43')) {
    newBooks = await fetchDoor43Data(releaseInfo.books, force, { ...manifest, _pendingTag: releaseInfo.tag }, releaseInfo.releaseBranch);
  }

  // Step 4: Fetch Google data
  if (runStep('fetch-google')) {
    await fetchGoogleData(force);
  }

  // Step 5: Extract unaligned English (also collects alignments for step 6)
  let ultAlignments = new Map();
  if (runStep('extract-english') || runStep('resolve-quotes')) {
    ultAlignments = extractUnalignedEnglish();
  }

  // Step 6: Resolve GL quotes
  if (runStep('resolve-quotes')) {
    resolveGlQuotes(ultAlignments);
  }

  // Step 7-8: Build indexes
  if (runStep('build-indexes')) {
    buildAllIndexes(releaseInfo.tag);
    if (newBooks.length) {
      log('New books imported: ' + newBooks.map(b => b.split('-')[1]).join(', '));
    }
  }

  // Update manifest
  writeManifest({
    release: releaseInfo.tag,
    releaseBranch: releaseInfo.releaseBranch,
    books: releaseInfo.books,
    lastRun: today(),
    lastNewBooks: newBooks.length ? newBooks : (manifest.lastNewBooks || []),
  });

  log('Done.');
}

main().catch(err => {
  console.error('[curate] Fatal: ' + err.message);
  process.exit(1);
});
