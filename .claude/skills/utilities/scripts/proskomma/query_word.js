#!/usr/bin/env node
// query_word.js - Look up all occurrences of a Strong's number across published ULT USFM files
// Usage: node query_word.js <strong_number> [--format table|json|csv] [--book <pattern>]

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.resolve(__dirname, '../../../../..', 'data/published_ult');

function parseArgs(argv) {
  const args = argv.slice(2);
  const opts = { format: 'table', book: null, strong: null };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--format' && args[i + 1]) {
      opts.format = args[i + 1];
      i++;
    } else if (args[i] === '--book' && args[i + 1]) {
      opts.book = args[i + 1].toUpperCase();
      i++;
    } else if (!args[i].startsWith('--')) {
      opts.strong = args[i].toUpperCase();
    }
  }

  if (!opts.strong) {
    console.error('Usage: node query_word.js <strong_number> [--format table|json|csv] [--book <pattern>]');
    console.error('Example: node query_word.js H3607');
    process.exit(1);
  }

  if (!['table', 'json', 'csv'].includes(opts.format)) {
    console.error(`Invalid format: ${opts.format}. Use table, json, or csv.`);
    process.exit(1);
  }

  return opts;
}

function getUsfmFiles(bookFilter) {
  if (!fs.existsSync(DATA_DIR)) {
    console.error(`Data directory not found: ${DATA_DIR}`);
    process.exit(1);
  }

  let files = fs.readdirSync(DATA_DIR)
    .filter(f => f.endsWith('.usfm'))
    .sort();

  if (bookFilter) {
    files = files.filter(f => {
      const upper = f.toUpperCase();
      return upper.includes(bookFilter);
    });
  }

  return files.map(f => path.join(DATA_DIR, f));
}

// Build a regex that matches the Strong's number in x-strong attribute,
// allowing for optional prefixes like "b:", "c:", "d:", "l:", "m:" etc.
function buildStrongRegex(strong) {
  const escaped = strong.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // Match x-strong="..." where the value contains our Strong's number,
  // possibly preceded by prefix(es) like "b:d:" separated by colons
  return new RegExp(`x-strong="(?:[a-z]:)*${escaped}"`, 'i');
}

function extractZalnAttributes(zalnStr) {
  const attrs = {};
  const strongMatch = zalnStr.match(/x-strong="([^"]+)"/);
  if (strongMatch) attrs.strong = strongMatch[1];

  const contentMatch = zalnStr.match(/x-content="([^"]+)"/);
  if (contentMatch) attrs.content = contentMatch[1];

  const lemmaMatch = zalnStr.match(/x-lemma="([^"]+)"/);
  if (lemmaMatch) attrs.lemma = lemmaMatch[1];

  const morphMatch = zalnStr.match(/x-morph="([^"]+)"/);
  if (morphMatch) attrs.morph = morphMatch[1];

  return attrs;
}

function parseFile(filePath, strongRegex) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');

  let bookId = '';
  let chapter = 0;
  let verse = 0;
  const results = [];

  // Track alignment nesting via a stack
  // Each entry: { attrs, words, isTarget }
  const stack = [];

  for (const line of lines) {
    // Track book ID
    const idMatch = line.match(/\\id\s+(\w+)/);
    if (idMatch) {
      bookId = idMatch[1];
    }

    // Track chapter
    const cMatch = line.match(/\\c\s+(\d+)/);
    if (cMatch) {
      chapter = parseInt(cMatch[1], 10);
    }

    // Track verse - can appear mid-line
    const vMatch = line.match(/\\v\s+(\d+)/);
    if (vMatch) {
      verse = parseInt(vMatch[1], 10);
    }

    // Process the line character by character for zaln-s, zaln-e, and \w markers
    // We use regex to find all markers in order
    const markerRegex = /\\zaln-s\s+\|([^\\]*?)\\?\*|\\zaln-e\\?\*|\\w\s+([^|]*?)\|[^\\]*?\\w\*/g;
    let match;

    while ((match = markerRegex.exec(line)) !== null) {
      if (match[0].startsWith('\\zaln-s')) {
        // Opening alignment marker
        const attrStr = match[1];
        const attrs = extractZalnAttributes(attrStr);
        const isTarget = strongRegex.test(attrStr);
        stack.push({ attrs, words: [], isTarget });
      } else if (match[0].startsWith('\\zaln-e')) {
        // Closing alignment marker - pop the stack
        if (stack.length > 0) {
          const closed = stack.pop();
          if (closed.isTarget) {
            results.push({
              book: bookId,
              reference: `${bookId} ${chapter}:${verse}`,
              chapter,
              verse,
              hebrew: closed.attrs.content || '',
              lemma: closed.attrs.lemma || '',
              morph: closed.attrs.morph || '',
              strong: closed.attrs.strong || '',
              english: closed.words.join(' ')
            });
          }
          // Propagate words up to parent if parent is target
          if (stack.length > 0) {
            stack[stack.length - 1].words.push(...closed.words);
          }
        }
      } else if (match[2] !== undefined) {
        // \w word - add to all open alignment entries
        const word = match[2].trim();
        if (word && stack.length > 0) {
          stack[stack.length - 1].words.push(word);
        }
      }
    }
  }

  return results;
}

function formatTable(results, strong) {
  if (results.length === 0) {
    console.log(`No occurrences found for Strong's number: ${strong}`);
    return;
  }

  // Find lemma from first result for header
  const lemma = results[0].lemma || '';
  const bookSet = new Set(results.map(r => r.book));

  console.log(`Strong's: ${strong} (${lemma})`);
  console.log(`Found ${results.length} occurrences across ${bookSet.size} books`);
  console.log();

  // Calculate column widths
  const cols = {
    book: Math.max(4, ...results.map(r => r.book.length)),
    ref: Math.max(9, ...results.map(r => r.reference.length)),
    hebrew: Math.max(6, ...results.map(r => r.hebrew.length)),
    morph: Math.max(10, ...results.map(r => r.morph.length)),
    english: Math.max(7, ...results.map(r => r.english.length))
  };

  const header = [
    'Book'.padEnd(cols.book),
    'Reference'.padEnd(cols.ref),
    'Hebrew'.padEnd(cols.hebrew),
    'Morphology'.padEnd(cols.morph),
    'English'.padEnd(cols.english)
  ].join('  ');

  const separator = [
    '-'.repeat(cols.book),
    '-'.repeat(cols.ref),
    '-'.repeat(cols.hebrew),
    '-'.repeat(cols.morph),
    '-'.repeat(cols.english)
  ].join('  ');

  console.log(header);
  console.log(separator);

  for (const r of results) {
    console.log([
      r.book.padEnd(cols.book),
      r.reference.padEnd(cols.ref),
      r.hebrew.padEnd(cols.hebrew),
      r.morph.padEnd(cols.morph),
      r.english
    ].join('  '));
  }
}

function formatJson(results) {
  console.log(JSON.stringify(results, null, 2));
}

function csvField(val) {
  if (val.includes(',') || val.includes('"')) {
    return `"${val.replace(/"/g, '""')}"`;
  }
  return val;
}

function formatCsv(results) {
  console.log('book,reference,hebrew,lemma,morphology,strong,english');
  for (const r of results) {
    const fields = [r.book, r.reference, r.hebrew, r.lemma, r.morph, r.strong, r.english];
    console.log(fields.map(csvField).join(','));
  }
}

function main() {
  const opts = parseArgs(process.argv);
  const strongRegex = buildStrongRegex(opts.strong);
  const files = getUsfmFiles(opts.book);

  if (files.length === 0) {
    console.error('No USFM files found' + (opts.book ? ` matching "${opts.book}"` : ''));
    process.exit(1);
  }

  let allResults = [];

  for (const file of files) {
    const results = parseFile(file, strongRegex);
    allResults.push(...results);
  }

  switch (opts.format) {
    case 'table': formatTable(allResults, opts.strong); break;
    case 'json': formatJson(allResults); break;
    case 'csv': formatCsv(allResults); break;
  }
}

main();
