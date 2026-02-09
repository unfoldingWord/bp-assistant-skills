#!/usr/bin/env node
/**
 * parse_usfm.js - Parse aligned USFM3 files using usfm-js library
 *
 * Usage:
 *   node parse_usfm.js <input.usfm> [--output-json alignments.json] [--output-plain plain.usfm]
 *   cat input.usfm | node parse_usfm.js --stdin [--output-json alignments.json]
 *
 * Output modes:
 *   --output-json <file>   Write alignment JSON to file (default: stdout)
 *   --output-plain <file>  Write unaligned English USFM to file
 *   --json-only           Only output JSON (no plain text)
 *   --plain-only          Only output plain text (no JSON)
 *   --chapter <num>       Extract only specified chapter
 *   --verse <ref>         Extract only specified verse (e.g., "3" or "3-5")
 */

import { readFileSync, writeFileSync } from 'fs';
import usfm from 'usfm-js';

// Parse command line arguments
const args = process.argv.slice(2);
let inputFile = null;
let outputJsonFile = null;
let outputPlainFile = null;
let useStdin = false;
let jsonOnly = false;
let plainOnly = false;
let filterChapter = null;
let filterVerse = null;

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--stdin':
      useStdin = true;
      break;
    case '--output-json':
      outputJsonFile = args[++i];
      break;
    case '--output-plain':
      outputPlainFile = args[++i];
      break;
    case '--json-only':
      jsonOnly = true;
      break;
    case '--plain-only':
      plainOnly = true;
      break;
    case '--chapter':
      filterChapter = parseInt(args[++i], 10);
      break;
    case '--verse':
      filterVerse = args[++i];
      break;
    case '--help':
    case '-h':
      console.log(`
Usage: node parse_usfm.js <input.usfm> [options]

Options:
  --stdin              Read USFM from stdin
  --output-json <file> Write alignment JSON to file (default: stdout)
  --output-plain <file> Write unaligned English USFM to file
  --json-only          Only output JSON (no plain text)
  --plain-only         Only output plain text (no JSON)
  --chapter <num>      Extract only specified chapter
  --verse <ref>        Extract only specified verse (e.g., "3" or "3-5")
  --help, -h           Show this help message

Output format (JSON):
  {
    "book": "1JN",
    "totalAlignments": 123,
    "alignments": [
      {
        "ref": "1JN 1:1",
        "chapter": 1,
        "verse": 1,
        "source": {
          "word": "arches",
          "lemma": "arche",
          "strong": "G07460",
          "morph": "Gr,N,,,,,GFS,"
        },
        "english": "the beginning",
        "englishWords": ["the", "beginning"]
      }
    ]
  }

Examples:
  node parse_usfm.js 63-1JN.usfm --output-json alignments.json
  cat 63-1JN.usfm | node parse_usfm.js --stdin --chapter 1
  node parse_usfm.js 63-1JN.usfm --plain-only > plain.usfm
`);
      process.exit(0);
    default:
      if (!args[i].startsWith('-')) {
        inputFile = args[i];
      }
  }
}

// Read input
let usfmContent;
if (useStdin) {
  usfmContent = readFileSync(0, 'utf8');
} else if (inputFile) {
  usfmContent = readFileSync(inputFile, 'utf8');
} else {
  console.error('Error: No input file specified. Use --stdin or provide a file path.');
  process.exit(1);
}

/**
 * Extract alignments from usfm-js parsed structure
 */
function extractAlignments(parsed, bookId, filterChapter, filterVerse) {
  const alignments = [];

  for (const [chapterNum, chapterData] of Object.entries(parsed.chapters || {})) {
    const chapter = parseInt(chapterNum, 10);

    // Skip if filtering and doesn't match chapter
    if (filterChapter && chapter !== filterChapter) continue;

    for (const [verseNum, verseData] of Object.entries(chapterData)) {
      const verse = parseInt(verseNum, 10);

      // Skip if filtering and doesn't match verse
      if (filterVerse) {
        const [startV, endV] = filterVerse.split('-').map(v => parseInt(v, 10));
        if (endV) {
          if (verse < startV || verse > endV) continue;
        } else {
          if (verse !== startV) continue;
        }
      }

      // Process verse objects
      if (verseData.verseObjects) {
        processVerseObjects(verseData.verseObjects, bookId, chapter, verse, alignments);
      }
    }
  }

  return alignments;
}

/**
 * Recursively process verse objects to extract alignments
 */
function processVerseObjects(objects, bookId, chapter, verse, alignments) {
  for (const obj of objects) {
    if (obj.tag === 'zaln' && obj.type === 'milestone') {
      // This is an alignment milestone
      const englishWords = extractEnglishWords(obj.children || []);

      alignments.push({
        ref: `${bookId} ${chapter}:${verse}`,
        chapter,
        verse,
        source: {
          word: obj.content || '',
          lemma: obj.lemma || '',
          strong: obj.strong || '',
          morph: obj.morph || ''
        },
        english: englishWords.join(' '),
        englishWords
      });

      // Also process nested alignments within children
      if (obj.children) {
        processVerseObjects(obj.children, bookId, chapter, verse, alignments);
      }
    } else if (obj.children) {
      // Recursively process any other objects with children
      processVerseObjects(obj.children, bookId, chapter, verse, alignments);
    }
  }
}

/**
 * Extract English words from alignment children
 */
function extractEnglishWords(children) {
  const words = [];
  for (const child of children) {
    if (child.tag === 'w' && child.type === 'word' && child.text) {
      words.push(child.text);
    }
    // Don't recurse into nested zaln milestones - they're separate alignments
    if (child.children && child.tag !== 'zaln') {
      words.push(...extractEnglishWords(child.children));
    }
  }
  return words;
}

/**
 * Extract plain English text from parsed USFM
 */
function extractPlainText(parsed, filterChap, filterVrs) {
  const lines = [];

  // Add headers only when not filtering to a specific chapter
  if (!filterChap) {
    for (const header of parsed.headers || []) {
      if (header.tag && header.content) {
        lines.push(`\\${header.tag} ${header.content}`);
      }
    }
  }

  for (const [chapterNum, chapterData] of Object.entries(parsed.chapters || {})) {
    const chapter = parseInt(chapterNum, 10);
    if (filterChap && chapter !== filterChap) continue;

    lines.push(`\\c ${chapterNum}`);
    lines.push('\\p');

    for (const [verseNum, verseData] of Object.entries(chapterData)) {
      if (filterVrs) {
        const vn = parseInt(verseNum, 10);
        if (!isNaN(vn) && !isNaN(filterVrs) && vn !== filterVrs) continue;
      }
      const verseText = extractVerseText(verseData.verseObjects || []);
      lines.push(`\\v ${verseNum} ${verseText}`);
    }
  }

  return lines.join('\n');
}

/**
 * Extract plain text from verse objects
 */
function extractVerseText(objects) {
  const parts = [];
  for (const obj of objects) {
    if (obj.type === 'quote' && obj.tag) {
      // Preserve \q1/\q2 markers for poetic line structure
      const marker = `\\${obj.tag}`;
      if (obj.text) {
        parts.push(`\n${marker} ${obj.text.replace(/\n$/, '')}`);
      } else {
        // Standalone marker (before next verse) -- skip, not useful in plain text
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

// Parse USFM using usfm-js
const parsed = usfm.toJSON(usfmContent);

// Extract book ID from headers
let bookId = '';
for (const header of parsed.headers || []) {
  if (header.tag === 'id') {
    bookId = header.content.split(' ')[0];
    break;
  }
}

// Extract alignments
const alignments = extractAlignments(parsed, bookId, filterChapter, filterVerse);

// Output JSON
if (!plainOnly) {
  const jsonOutput = JSON.stringify({
    book: bookId,
    totalAlignments: alignments.length,
    alignments
  }, null, 2);

  if (outputJsonFile) {
    writeFileSync(outputJsonFile, jsonOutput);
    console.error(`Wrote ${alignments.length} alignments to ${outputJsonFile}`);
  } else {
    console.log(jsonOutput);
  }
}

// Output plain text
const plainText = extractPlainText(parsed, filterChapter, filterVerse);
if (!jsonOnly && outputPlainFile) {
  writeFileSync(outputPlainFile, plainText);
  console.error(`Wrote plain USFM to ${outputPlainFile}`);
} else if (plainOnly) {
  console.log(plainText);
}
