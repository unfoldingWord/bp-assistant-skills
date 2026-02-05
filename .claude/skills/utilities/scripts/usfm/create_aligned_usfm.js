#!/usr/bin/env node
/**
 * create_aligned_usfm.js - Convert simple alignment mapping to aligned USFM3
 *
 * Takes a simple mapping JSON (Hebrew indices -> English words) and Hebrew source,
 * produces properly formatted aligned USFM using usfm-js.
 *
 * Usage:
 *   node create_aligned_usfm.js --hebrew <hebrew.usfm> --mapping <mapping.json> [options]
 *
 * Options:
 *   --hebrew <file>     Hebrew source USFM file
 *   --mapping <file>    Simple mapping JSON file from AI
 *   --output <file>     Output aligned USFM file (default: stdout)
 *   --chapter <num>     Process only this chapter
 *   --verse <num>       Process only this verse (requires --chapter)
 */

import { readFileSync, writeFileSync } from 'fs';
import usfm from 'usfm-js';

// Parse command line arguments
const args = process.argv.slice(2);
let hebrewFile = null;
let mappingFile = null;
let outputFile = null;
let filterChapter = null;
let filterVerse = null;

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--hebrew':
      hebrewFile = args[++i];
      break;
    case '--mapping':
      mappingFile = args[++i];
      break;
    case '--output':
      outputFile = args[++i];
      break;
    case '--chapter':
      filterChapter = parseInt(args[++i], 10);
      break;
    case '--verse':
      filterVerse = parseInt(args[++i], 10);
      break;
    case '--help':
    case '-h':
      console.log(`
Usage: node create_aligned_usfm.js --hebrew <hebrew.usfm> --mapping <mapping.json> [options]

Options:
  --hebrew <file>     Hebrew source USFM file (required)
  --mapping <file>    Simple mapping JSON file from AI (required)
  --output <file>     Output aligned USFM file (default: stdout)
  --chapter <num>     Process only this chapter
  --verse <num>       Process only this verse (requires --chapter)
  --help, -h          Show this help message

Mapping JSON format:
  {
    "reference": "GEN 1:1",
    "hebrew_words": [
      {"index": 0, "word": "בְּ⁠רֵאשִׁ֖ית", "strong": "b:H7225", "lemma": "רֵאשִׁית"}
    ],
    "english_text": "In the beginning...",
    "alignments": [
      {"hebrew_indices": [0], "english": ["In", "the", "beginning"]}
    ]
  }

Example:
  node create_aligned_usfm.js \\
    --hebrew data/hebrew_bible/01-GEN.usfm \\
    --mapping /tmp/alignments/GEN-01-01.json \\
    --output /tmp/aligned.usfm \\
    --chapter 1 --verse 1
`);
      process.exit(0);
    default:
      if (!args[i].startsWith('-')) {
        console.error(`Unknown argument: ${args[i]}`);
        process.exit(1);
      }
  }
}

if (!hebrewFile || !mappingFile) {
  console.error('Error: Both --hebrew and --mapping are required');
  process.exit(1);
}

// Read inputs
const hebrewContent = readFileSync(hebrewFile, 'utf8');
const mappingData = JSON.parse(readFileSync(mappingFile, 'utf8'));

// Parse Hebrew USFM
const hebrewParsed = usfm.toJSON(hebrewContent);

/**
 * Extract Hebrew word metadata from parsed Hebrew USFM
 */
function extractHebrewWords(hebrewParsed, chapter, verse) {
  const words = [];
  const chapterData = hebrewParsed.chapters?.[chapter];
  if (!chapterData) return words;

  const verseData = chapterData[verse];
  if (!verseData?.verseObjects) return words;

  for (const obj of verseData.verseObjects) {
    if (obj.tag === 'w' && obj.type === 'word') {
      words.push({
        word: obj.text,
        lemma: obj.lemma || '',
        strong: obj.strong || '',
        morph: obj.morph || ''
      });
    }
  }

  return words;
}

/**
 * Count occurrences of each English word in the alignments
 */
function countWordOccurrences(alignments) {
  const counts = {};
  for (const align of alignments) {
    for (const word of align.english) {
      // Strip brackets for counting
      const cleanWord = word.replace(/[{}]/g, '');
      counts[cleanWord] = (counts[cleanWord] || 0) + 1;
    }
  }
  return counts;
}

/**
 * Build aligned verse objects from mapping data
 */
function buildAlignedVerseObjects(mapping, hebrewWords) {
  const verseObjects = [];
  const wordOccurrences = countWordOccurrences(mapping.alignments);
  const currentOccurrence = {};

  for (const align of mapping.alignments) {
    // Get Hebrew word metadata for this alignment
    const hebrewMeta = [];
    for (const idx of align.hebrew_indices) {
      const hw = hebrewWords[idx] || mapping.hebrew_words[idx];
      if (hw) {
        hebrewMeta.push(hw);
      }
    }

    // Build zaln milestones for each Hebrew word
    // For nested alignments (multiple Hebrew words), we nest the zaln-s tags
    const buildWordObject = (text, occurrence, occurrences) => ({
      text: text.replace(/[{}]/g, ''), // Remove brackets for the word text
      tag: 'w',
      type: 'word',
      occurrence: occurrence.toString(),
      occurrences: occurrences.toString()
    });

    // Build English word objects with occurrence tracking
    const englishObjs = [];
    for (let i = 0; i < align.english.length; i++) {
      const word = align.english[i];
      const cleanWord = word.replace(/[{}]/g, '');
      currentOccurrence[cleanWord] = (currentOccurrence[cleanWord] || 0) + 1;

      // Add space between words (except first)
      if (i > 0) {
        englishObjs.push({ type: 'text', text: ' ' });
      }

      // Check if this is a bracketed word
      if (word.startsWith('{') && word.endsWith('}')) {
        // Bracketed words get wrapped in { }
        englishObjs.push({ type: 'text', text: '{' });
        englishObjs.push(buildWordObject(cleanWord, currentOccurrence[cleanWord], wordOccurrences[cleanWord]));
        englishObjs.push({ type: 'text', text: '}' });
      } else {
        englishObjs.push(buildWordObject(cleanWord, currentOccurrence[cleanWord], wordOccurrences[cleanWord]));
      }
    }

    // Build nested zaln structure for Hebrew words
    if (hebrewMeta.length === 0) {
      // No Hebrew source - just add the English words directly (shouldn't happen with new rules)
      verseObjects.push(...englishObjs);
    } else if (hebrewMeta.length === 1) {
      // Single Hebrew word
      const hw = hebrewMeta[0];
      const sourceWord = mapping.hebrew_words[align.hebrew_indices[0]]?.word || hw.word;
      verseObjects.push({
        tag: 'zaln',
        type: 'milestone',
        strong: hw.strong,
        lemma: hw.lemma,
        morph: hw.morph || '',
        occurrence: '1', // TODO: track Hebrew word occurrences
        occurrences: '1',
        content: sourceWord,
        children: englishObjs,
        endTag: 'zaln-e\\*'
      });
    } else {
      // Multiple Hebrew words - nest the zaln milestones
      let innermost = englishObjs;
      // Build from inside out (last Hebrew word wraps innermost)
      for (let i = hebrewMeta.length - 1; i >= 0; i--) {
        const hw = hebrewMeta[i];
        const sourceWord = mapping.hebrew_words[align.hebrew_indices[i]]?.word || hw.word;
        innermost = [{
          tag: 'zaln',
          type: 'milestone',
          strong: hw.strong,
          lemma: hw.lemma,
          morph: hw.morph || '',
          occurrence: '1',
          occurrences: '1',
          content: sourceWord,
          children: innermost,
          endTag: 'zaln-e\\*'
        }];
      }
      verseObjects.push(...innermost);
    }

    // Add space after alignment (except for last)
    if (align !== mapping.alignments[mapping.alignments.length - 1]) {
      verseObjects.push({ type: 'text', text: '\n' });
    }
  }

  return verseObjects;
}

/**
 * Parse reference string like "GEN 1:1" into parts
 */
function parseReference(ref) {
  const match = ref.match(/^(\w+)\s+(\d+):(\d+)$/);
  if (!match) return null;
  return {
    book: match[1],
    chapter: parseInt(match[2], 10),
    verse: parseInt(match[3], 10)
  };
}

// Process mapping data
const mappings = Array.isArray(mappingData) ? mappingData : [mappingData];

// Build output structure
const outputJson = {
  headers: [],
  chapters: {}
};

// Copy headers from Hebrew source (modify id tag)
for (const header of hebrewParsed.headers || []) {
  if (header.tag === 'id') {
    const bookId = header.content.split(' ')[0];
    outputJson.headers.push({
      tag: 'id',
      content: `${bookId} EN_ULT - Aligned`
    });
  } else {
    outputJson.headers.push(header);
  }
}

// Add required headers if missing
const hasTags = outputJson.headers.map(h => h.tag);
if (!hasTags.includes('usfm')) {
  outputJson.headers.splice(1, 0, { tag: 'usfm', content: '3.0' });
}
if (!hasTags.includes('ide')) {
  outputJson.headers.splice(2, 0, { tag: 'ide', content: 'UTF-8' });
}

// Process each mapping
for (const mapping of mappings) {
  const ref = parseReference(mapping.reference);
  if (!ref) {
    console.error(`Invalid reference: ${mapping.reference}`);
    continue;
  }

  // Apply filters
  if (filterChapter && ref.chapter !== filterChapter) continue;
  if (filterVerse && ref.verse !== filterVerse) continue;

  // Initialize chapter if needed
  if (!outputJson.chapters[ref.chapter]) {
    outputJson.chapters[ref.chapter] = {};
  }

  // Get Hebrew words for this verse
  const hebrewWords = extractHebrewWords(hebrewParsed, ref.chapter, ref.verse);

  // Build aligned verse objects
  const verseObjects = buildAlignedVerseObjects(mapping, hebrewWords);

  // Add to output
  outputJson.chapters[ref.chapter][ref.verse] = {
    verseObjects
  };
}

// Convert to USFM
const outputUsfm = usfm.toUSFM(outputJson);

// Write output
if (outputFile) {
  writeFileSync(outputFile, outputUsfm);
  console.error(`Wrote aligned USFM to ${outputFile}`);
} else {
  console.log(outputUsfm);
}
