#!/usr/bin/env node
/**
 * CLI Bridge for TSV Quote Converters with roundtrip support.
 *
 * Adapted from tnwriter-dev/cli_for_lang_conversion.js.
 * Adds a `roundtrip` command that chains gl2ol + addgl internally.
 *
 * USAGE:
 *   node lang_convert.js gl2ol <bible_link> <book_code> <tsv_content_or_->
 *   node lang_convert.js addgl <bible_links> <book_code> <tsv_content_or_->
 *   node lang_convert.js roundtrip <bible_link> <book_code> <tsv_content_or_->
 */

const CONVERTER_PATH = '/workspace/.claude/skills/tn-writer/scripts/tsv-quote-converters.mjs';

const fs = require('fs');

// Minimal HTML entity decoding (no DOM dependency)
function decodeEntities(str) {
  if (!str) return str;
  return str
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

// Preprocess TSV: normalize split quotes and decode entities in Quote column
function preprocessTSVForGLtoOL(tsvContent) {
  if (!tsvContent) return tsvContent;

  const lines = tsvContent.split(/\r?\n/);
  if (lines.length === 0) return tsvContent;

  const header = lines[0];
  const headers = header.split('\t');
  const quoteIdx = headers.indexOf('Quote');

  if (quoteIdx === -1) return tsvContent;

  const out = [header];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line) { out.push(line); continue; }
    const cols = line.split('\t');
    if (cols.length <= quoteIdx) { out.push(line); continue; }

    let q = cols[quoteIdx] || '';
    q = decodeEntities(q);
    cols[quoteIdx] = q;
    out.push(cols.join('\t'));
  }

  return out.join('\n');
}

// Helper to read TSV content from arg/stdin/file
function getTsvContent(tsvArg) {
  if (tsvArg === '-') {
    return new Promise((resolve, reject) => {
      try {
        let data = '';
        process.stdin.setEncoding('utf8');
        process.stdin.on('data', chunk => (data += chunk));
        process.stdin.on('end', () => resolve(data));
        process.stdin.resume();
      } catch (e) {
        reject(e);
      }
    });
  }

  if (tsvArg && tsvArg.startsWith('@')) {
    const path = tsvArg.slice(1);
    return Promise.resolve(fs.readFileSync(path, 'utf8'));
  }

  return Promise.resolve(tsvArg || '');
}

import(CONVERTER_PATH).then(({ convertGLQuotes2OLQuotes, addGLQuoteCols }) => {
  const originalLog = console.log;
  const originalError = console.error;
  const suppressedLogs = [];

  console.log = (...args) => suppressedLogs.push(args);
  console.error = (...args) => suppressedLogs.push(args);

  const command = process.argv[2];

  (async () => {
    if (command === 'gl2ol') {
      const bibleLink = process.argv[3] || 'unfoldingWord/en_ult/master';
      const bookCode = process.argv[4];
      const tsvArg = process.argv[5];
      let tsvContent = await getTsvContent(tsvArg);
      tsvContent = preprocessTSVForGLtoOL(tsvContent);

      const result = await convertGLQuotes2OLQuotes({
        bibleLink,
        bookCode,
        tsvContent,
        trySeparatorsAndOccurrences: true,
        quiet: true
      });

      console.log = originalLog;
      console.error = originalError;
      originalLog(JSON.stringify(result));

    } else if (command === 'addgl') {
      const bibleLinks = process.argv[3].split(',');
      const bookCode = process.argv[4];
      const tsvArg = process.argv[5];
      const tsvContent = await getTsvContent(tsvArg);

      const result = await addGLQuoteCols({
        bibleLinks,
        bookCode,
        tsvContent,
        trySeparatorsAndOccurrences: true,
        quiet: true
      });

      console.log = originalLog;
      console.error = originalError;
      originalLog(JSON.stringify(result));

    } else if (command === 'roundtrip') {
      // Roundtrip: gl2ol then addgl in one step
      const bibleLink = process.argv[3] || 'unfoldingWord/en_ult/master';
      const bookCode = process.argv[4];
      const tsvArg = process.argv[5];
      let tsvContent = await getTsvContent(tsvArg);
      tsvContent = preprocessTSVForGLtoOL(tsvContent);

      // Step 1: GL to OL
      const result1 = await convertGLQuotes2OLQuotes({
        bibleLink,
        bookCode,
        tsvContent,
        trySeparatorsAndOccurrences: true,
        quiet: true
      });

      if (!result1 || !result1.output) {
        console.log = originalLog;
        console.error = originalError;
        originalError(JSON.stringify({ error: 'gl2ol step failed', details: result1 }));
        process.exit(1);
        return;
      }

      // Step 2: Add GL columns back
      const result2 = await addGLQuoteCols({
        bibleLinks: [bibleLink],
        bookCode,
        tsvContent: result1.output,
        trySeparatorsAndOccurrences: true,
        quiet: true
      });

      console.log = originalLog;
      console.error = originalError;
      originalLog(JSON.stringify(result2));

    } else {
      console.log = originalLog;
      console.error = originalError;
      originalError('Usage: node lang_convert.js [gl2ol|addgl|roundtrip] [args...]');
      process.exit(1);
    }
  })().catch(error => {
    console.log = originalLog;
    console.error = originalError;
    originalError(JSON.stringify({ error: error.toString() }));
    process.exit(1);
  });
}).catch(error => {
  console.error(`Error loading converter module from ${CONVERTER_PATH}`);
  console.error('Make sure:');
  console.error('  1. The path in CONVERTER_PATH is correct');
  console.error('  2. You have run "npm run build" in tsv-quote-converters directory');
  console.error(`\nError: ${error.message}`);
  process.exit(1);
});
