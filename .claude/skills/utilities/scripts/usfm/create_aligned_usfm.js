#!/usr/bin/env node
/**
 * create_aligned_usfm.js - Convert simple alignment mapping to aligned USFM3
 *
 * Takes a simple mapping JSON (Hebrew indices -> English words) and Hebrew source,
 * produces properly formatted aligned USFM using usfm-js.
 *
 * Usage:
 *   node create_aligned_usfm.js --hebrew <hebrew.usfm> --mapping <mapping.json> --source <source.usfm> [options]
 *
 * Required:
 *   --hebrew <file>     Hebrew source USFM file
 *   --mapping <file>    Simple mapping JSON file from AI
 *   --source <file>     Source ULT/UST file (preserves poetry markers like \q1, \q2)
 *                       (--ult is accepted as an alias for backward compatibility)
 *   --output <file>     Output aligned USFM file (default: stdout)
 *   --chapter <num>     Process only this chapter
 *   --verse <num>       Process only this verse (requires --chapter)
 *   --ust               UST mode: brackets placed outside milestones, contiguous groups wrapped
 */

import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname } from 'path';
import usfm from 'usfm-js';

// Parse command line arguments
const args = process.argv.slice(2);
let hebrewFile = null;
let mappingFile = null;
let ultFile = null;
let outputFile = null;
let filterChapter = null;
let filterVerse = null;
let ustMode = false;

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--hebrew':
      hebrewFile = args[++i];
      break;
    case '--mapping':
      mappingFile = args[++i];
      break;
    case '--ult':
    case '--source':
      ultFile = args[++i];
      break;
    case '--ust':
      ustMode = true;
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
Usage: node create_aligned_usfm.js --hebrew <hebrew.usfm> --mapping <mapping.json> --source <source.usfm> [options]

Required:
  --hebrew <file>     Hebrew source USFM file
  --mapping <file>    Simple mapping JSON file from AI
  --source <file>     Source ULT/UST file (preserves poetry markers)
                      (--ult is accepted as an alias)
  --output <file>     Output aligned USFM file (default: stdout)
  --chapter <num>     Process only this chapter
  --verse <num>       Process only this verse (requires --chapter)
  --ust               UST mode: brackets outside milestones, contiguous groups wrapped
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
    --source output/AI-ULT/GEN-01.usfm \\
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
  console.error('Error: --hebrew, --mapping, and --ult are all required');
  process.exit(1);
}

if (!ultFile) {
  console.error('Error: --ult is required (source ULT file for preserving poetry markers)');
  process.exit(1);
}

// Sanity check: catch common mistake of passing the wrong source file for the mode
if (ultFile) {
  const isUltPath = /[/\\]AI-ULT[/\\]/.test(ultFile);
  const isUstPath = /[/\\]AI-UST[/\\]/.test(ultFile);
  if (ustMode && isUltPath) {
    console.error(`Error: --ust mode is active but --source appears to be a ULT file: ${ultFile}`);
    console.error('UST alignment requires --source to point to the UST file (output/AI-UST/BOOK/BOOK-CH.usfm)');
    process.exit(1);
  }
  if (!ustMode && isUstPath) {
    console.error(`Warning: --source appears to be a UST file but --ust flag is not set: ${ultFile}`);
    console.error('If aligning UST, add the --ust flag. If aligning ULT, use --source output/AI-ULT/... instead.');
    process.exit(1);
  }
}

// Read inputs
let hebrewContent = readFileSync(hebrewFile, 'utf8');
if (hebrewContent.startsWith('# Fetched:')) {
  hebrewContent = hebrewContent.slice(hebrewContent.indexOf('\n') + 1);
}
const mappingData = JSON.parse(readFileSync(mappingFile, 'utf8'));
let ultContent = ultFile ? readFileSync(ultFile, 'utf8') : null;
if (ultContent && ultContent.startsWith('# Fetched:')) {
  ultContent = ultContent.slice(ultContent.indexOf('\n') + 1);
}

// Parse Hebrew USFM
const hebrewParsed = usfm.toJSON(hebrewContent);

/**
 * Extract USFM markers from source ULT for a specific verse
 * Returns array of marker objects:
 * [{marker: 'q1', position: 0, startWords: []},           // before \v on same line
 *  {marker: 'q2', position: -1, startWords: ['and', 'their']},  // mid-verse poetry
 *  {markerLine: '\\qa Nun', position: -2},                // inter-verse marker (own line)
 *  {markerLine: '\\s1 Section', position: -2}]             // inter-verse marker (own line)
 * position  0 = before verse marker on same line
 * position -1 = mid-verse (use startWords to match)
 * position -2 = own line before verse
 *
 * @param {boolean} hasDText - if true, skip \d as inter-verse marker (handled as aligned superscription)
 */
function extractUsfmMarkers(ultContent, chapter, verse, hasDText = false) {
  if (!ultContent) return [];

  const markers = [];

  // Find this verse and subsequent lines until next verse
  const chapterPattern = new RegExp(`\\\\c\\s+${chapter}[^\\d]`);
  const chapterMatch = ultContent.match(chapterPattern);
  if (!chapterMatch) return markers;

  const chapterStart = chapterMatch.index;
  const nextChapterMatch = ultContent.slice(chapterStart + 5).match(/\\c\s+\d/);
  const chapterEnd = nextChapterMatch ? chapterStart + 5 + nextChapterMatch.index : ultContent.length;
  const chapterContent = ultContent.slice(chapterStart, chapterEnd);

  // --- Inter-verse markers (position -2) ---
  // Find the position of \v <verse> in chapterContent
  // Also capture any \q1/\q2 prefix on the same line by looking for the line start
  let versePos = chapterContent.search(new RegExp(`\\\\v\\s+${verse}\\s`));
  if (versePos === -1) return markers;

  // Back up versePos to include \q1/\q2 prefix on the same line
  const lineStart = chapterContent.lastIndexOf('\n', versePos - 1);
  const linePrefix = chapterContent.slice(lineStart + 1, versePos);
  if (linePrefix.trim().match(/^\\q[12]\s*$/)) {
    versePos = lineStart + 1;
  }

  // Find end of previous verse's content (or chapter start line for verse 1)
  let prevEnd;
  if (verse === 1) {
    // For verse 1, look after the \c line
    const cLineEnd = chapterContent.indexOf('\n');
    prevEnd = cLineEnd !== -1 ? cLineEnd + 1 : 0;
  } else {
    // Find the next verse marker after the previous verse
    const prevVersePattern = new RegExp(`\\\\v\\s+${verse - 1}\\s`);
    const prevVerseMatch = chapterContent.match(prevVersePattern);
    if (prevVerseMatch) {
      // Find the end of the previous verse's content by looking for the next newline
      // that starts an inter-verse marker or blank line
      const prevVerseStart = prevVerseMatch.index;
      // Find the next \v after prev verse (which is our current verse position)
      // Everything between prev verse and current verse that isn't verse/poetry text content
      const betweenRegion = chapterContent.slice(prevVerseStart, versePos);
      const betweenLines = betweenRegion.split('\n');
      // Find where the previous verse's text content ends
      // Text content lines: \v lines, \q lines with text after, or plain text continuation
      // Inter-verse markers: \qa, \s1, \s2, \b, \cl, \d, or blank lines
      let lastTextLine = 0;
      for (let i = 0; i < betweenLines.length; i++) {
        const trimmed = betweenLines[i].trim();
        if (!trimmed) continue;  // skip blank lines
        const isInterVerseMarker = trimmed.match(/^\\(qa\s|s[12]\s|d\s|d$|b\s*$|cl\s|p\s*$)/);
        if (!isInterVerseMarker) {
          lastTextLine = i;
        }
      }
      prevEnd = prevVerseStart + betweenLines.slice(0, lastTextLine + 1).join('\n').length + 1;
    } else {
      prevEnd = 0;
    }
  }

  // Extract text between previous verse end and current verse position
  const interVerseText = chapterContent.slice(prevEnd, versePos);
  const interVerseLines = interVerseText.split('\n');

  // Match inter-verse markers
  const interVerseMarkerPattern = /^(\\qa\s+.+|\\s[12]\s+.+|\\b\s*$|\\cl\s+.+|\\d\s+.+|\\d\s*$|\\p\s*$)/;
  for (const line of interVerseLines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const markerMatch = trimmed.match(interVerseMarkerPattern);
    if (markerMatch) {
      // Skip \d when mapping has d_text (aligned superscription handled separately)
      if (hasDText && trimmed.startsWith('\\d ')) continue;
      markers.push({ markerLine: trimmed, position: -2 });
    }
  }

  // --- Poetry markers (position 0 and -1) ---
  // Find this verse within the chapter
  const versePattern = new RegExp(`((?:\\\\q[12]\\s+)?)\\\\v\\s+${verse}\\s+(.+?)(?=\\\\v\\s+\\d|\\\\c\\s+\\d|$)`, 's');
  const verseMatch = chapterContent.match(versePattern);
  if (!verseMatch) return markers;

  const prefixMarker = verseMatch[1]?.trim();
  const verseContent = verseMatch[2];

  // Check for marker before \v
  if (prefixMarker) {
    markers.push({ marker: prefixMarker.replace('\\', ''), position: 0, startWords: [] });
  }

  // Look for \q1, \q2 markers within verse content
  // Split by newlines and look for markers at start of continuation lines
  const lines = verseContent.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Check for poetry marker at start of line (continuation)
    const lineMarkerMatch = line.match(/^\\(q[12])\s+(.+)/);
    if (lineMarkerMatch && i > 0) {
      // Extract first 3 words after the marker to use for matching
      const textAfterMarker = lineMarkerMatch[2]
        .replace(/\\[a-z0-9*]+\s*/g, '')  // Remove USFM markers
        .replace(/[{}\[\]]/g, '')          // Remove brackets
        .trim();
      const startWords = textAfterMarker.split(/\s+/).slice(0, 3).map(w =>
        w.replace(/[.,;:!?'"\u201C\u201D\u2018\u2019]/g, '').toLowerCase()
      );
      markers.push({ marker: lineMarkerMatch[1], position: -1, startWords });
    }
  }

  return markers;
}

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
 * Reorder alignments to match English word order from english_text
 * This ensures output follows English word order even if alignments were
 * created in Hebrew word order.
 */
function reorderAlignmentsByEnglishText(alignments, englishText) {
  // Tokenize english_text
  const englishWords = englishText
    .replace(/[.,;:!?"']/g, ' ')  // Remove punctuation
    .replace(/[{}]/g, '')          // Remove brackets
    .split(/\s+/)
    .filter(w => w.length > 0)
    .map(w => w.toLowerCase());

  // Build position lookup: word -> [indices where it appears]
  const wordPositions = {};
  for (let i = 0; i < englishWords.length; i++) {
    const word = englishWords[i];
    if (!wordPositions[word]) {
      wordPositions[word] = [];
    }
    wordPositions[word].push(i);
  }

  // Track which positions in englishWords have been claimed
  const claimedPositions = new Set();

  // For each alignment, find positions for ALL its words and use the minimum
  // This handles cases where alignment words are not consecutive in english_text
  const alignmentsWithPosition = alignments.map((align, originalIndex) => {
    const alignWords = align.english.map(w => w.replace(/[{}]/g, '').toLowerCase());

    if (alignWords.length === 0) {
      return { align, position: -1, claimedPos: [] };
    }

    // Find unclaimed positions for each word in the alignment
    const foundPositions = [];
    for (const word of alignWords) {
      const positions = wordPositions[word] || [];
      // Find first unclaimed position for this word
      const pos = positions.find(p => !claimedPositions.has(p));
      if (pos !== undefined) {
        foundPositions.push(pos);
      }
    }

    if (foundPositions.length === 0) {
      return { align, position: -1, claimedPos: [], originalIndex };
    }

    // Use minimum position as sort key
    const minPosition = Math.min(...foundPositions);

    return { align, position: minPosition, claimedPos: foundPositions, originalIndex };
  });

  // Now claim positions in sorted order to handle duplicates correctly
  // First, sort by the tentative position, using original alignment index as tiebreaker
  // This ensures that when duplicate words (e.g., "And" and "and") get the same position,
  // the one from earlier in the alignment array claims the earlier english_text position
  alignmentsWithPosition.sort((a, b) => {
    if (a.position === -1 && b.position === -1) return 0;
    if (a.position === -1) return 1;
    if (b.position === -1) return -1;
    if (a.position !== b.position) return a.position - b.position;
    return a.originalIndex - b.originalIndex;
  });

  // Re-process in sorted order to correctly assign positions for duplicates
  claimedPositions.clear();
  for (const item of alignmentsWithPosition) {
    if (item.position === -1) continue;

    const alignWords = item.align.english.map(w => w.replace(/[{}]/g, '').toLowerCase());
    const newPositions = [];

    for (const word of alignWords) {
      const positions = wordPositions[word] || [];
      const pos = positions.find(p => !claimedPositions.has(p));
      if (pos !== undefined) {
        newPositions.push(pos);
        claimedPositions.add(pos);
      }
    }

    if (newPositions.length > 0) {
      item.position = Math.min(...newPositions);
    }
  }

  // Final sort by recalculated positions
  alignmentsWithPosition.sort((a, b) => {
    if (a.position === -1 && b.position === -1) return 0;
    if (a.position === -1) return 1;
    if (b.position === -1) return -1;
    if (a.position !== b.position) return a.position - b.position;
    return a.originalIndex - b.originalIndex;
  });

  return alignmentsWithPosition.map(item => item.align);
}

/**
 * Build aligned verse objects from mapping data
 *
 * This function outputs English words in the exact order they appear in english_text,
 * wrapping each word (or group of consecutive aligned words) in appropriate zaln milestones.
 */
function buildAlignedVerseObjects(mapping, hebrewWords, ustMode = false) {
  // Normalize a word for matching: strip brackets and punctuation, lowercase
  const normalizeWord = (w) => w.replace(/[{}.,;:!?"']/g, '').toLowerCase();
  // Case-sensitive key for occurrence counting: strip brackets and punctuation, keep case
  const occurrenceKey = (w) => w.replace(/[{}.,;:!?"']/g, '');

  // Tokenize english_text to get the authoritative word order
  // Keep original words with punctuation for output
  const englishTextWordsRaw = mapping.english_text
    .split(/\s+/)
    .filter(w => w.length > 0);
  const englishTextWords = englishTextWordsRaw.map(normalizeWord);

  // Build a map: normalized word -> alignment info
  // Handle duplicates by tracking which occurrence we're on
  const wordToAlignments = {};
  for (const align of mapping.alignments) {
    for (const word of align.english) {
      const normalized = normalizeWord(word);
      if (!wordToAlignments[normalized]) {
        wordToAlignments[normalized] = [];
      }
      wordToAlignments[normalized].push({
        align,
        originalWord: word,
        hebrewIndices: align.hebrew_indices
      });
    }
  }

  // Count total occurrences of each word for x-occurrences attribute (case-sensitive)
  const englishTextOccKeys = englishTextWordsRaw.map(occurrenceKey);
  const wordTotalOccurrences = {};
  for (const key of englishTextOccKeys) {
    wordTotalOccurrences[key] = (wordTotalOccurrences[key] || 0) + 1;
  }

  // Track current occurrence for x-occurrence attribute
  const currentOccurrence = {};

  const buildWordObject = (text, occurrence, occurrences) => ({
    text: text.replace(/[{}]/g, ''),
    tag: 'w',
    type: 'word',
    occurrence: occurrence.toString(),
    occurrences: occurrences.toString()
  });

  // Count total occurrences of each Hebrew source word as it will be emitted.
  // Count from alignment entries (not hebrew_words array), because the same
  // Hebrew word index can be referenced by multiple alignment groups in UST,
  // and each reference produces a \zaln-s milestone.
  const hebrewWordTotalOccurrences = {};
  for (const align of (mapping.alignments || [])) {
    for (const idx of (align.hebrew_indices || [])) {
      const hw = (mapping.hebrew_words || [])[idx];
      if (hw && hw.word) {
        hebrewWordTotalOccurrences[hw.word] = (hebrewWordTotalOccurrences[hw.word] || 0) + 1;
      }
    }
  }
  // Track current occurrence per Hebrew word as we process alignments
  const hebrewCurrentOccurrence = {};

  const buildZalnMilestone = (hw, sourceWord, children) => {
    // Track which occurrence of this Hebrew word we're emitting
    hebrewCurrentOccurrence[sourceWord] = (hebrewCurrentOccurrence[sourceWord] || 0) + 1;
    return {
      tag: 'zaln',
      type: 'milestone',
      strong: hw.strong,
      lemma: hw.lemma,
      morph: hw.morph || '',
      occurrence: hebrewCurrentOccurrence[sourceWord].toString(),
      occurrences: (hebrewWordTotalOccurrences[sourceWord] || 1).toString(),
      content: sourceWord,
      children: children,
      endTag: 'zaln-e\\*'
    };
  };

  // Pre-compute bracket status for each word position
  // Do a dry-run of occurrence counting to determine bracket status
  const bracketStatus = [];
  const dryRunOccIdx = {};
  for (let i = 0; i < englishTextWords.length; i++) {
    const normalized = englishTextWords[i];
    const rawWord = englishTextWordsRaw[i];
    const occIdx = dryRunOccIdx[normalized] || 0;
    dryRunOccIdx[normalized] = occIdx + 1;
    const alignInfo = wordToAlignments[normalized]?.[occIdx];
    const originalWord = alignInfo?.originalWord || rawWord;
    const isBracketed = originalWord.startsWith('{') || (rawWord.startsWith('{') && rawWord.endsWith('}'));
    bracketStatus.push(isBracketed);
  }

  const verseObjects = [];

  // Build a list of items in English text order, where each item is either:
  //   { type: 'aligned', alignIdx, wordIndices: [i, ...] }  — one alignment group
  //   { type: 'unaligned', wordIndex: i }                   — unaligned word
  // This ensures multiple English words sharing one alignment entry are grouped
  // into a single zaln milestone block.

  // Map each english_text word position to its alignment
  const wordAlignmentGroup = new Array(englishTextWords.length).fill(null);
  const tempOccIdx = {};
  for (let i = 0; i < englishTextWords.length; i++) {
    const normalized = englishTextWords[i];
    const occIdx = tempOccIdx[normalized] || 0;
    tempOccIdx[normalized] = occIdx + 1;
    const alignInfo = wordToAlignments[normalized]?.[occIdx];
    if (alignInfo) {
      wordAlignmentGroup[i] = alignInfo.align; // reference to the alignment object
    }
  }

  // Walk english_text positions and group consecutive words that share the same
  // alignment object (by identity) into one group item.
  const groupedItems = [];
  let pos = 0;
  while (pos < englishTextWords.length) {
    const alignObj = wordAlignmentGroup[pos];
    if (!alignObj) {
      groupedItems.push({ type: 'unaligned', wordIndex: pos });
      pos++;
    } else {
      // Collect all consecutive positions that belong to this same alignment object
      const wordIndices = [pos];
      let next = pos + 1;
      while (next < englishTextWords.length && wordAlignmentGroup[next] === alignObj) {
        wordIndices.push(next);
        next++;
      }
      groupedItems.push({ type: 'aligned', align: alignObj, wordIndices });
      pos = next;
    }
  }

  // Now emit each group item
  let isFirstEmitted = true;

  for (const item of groupedItems) {
    if (item.type === 'unaligned') {
      const i = item.wordIndex;
      const rawWord = englishTextWordsRaw[i];
      const isBracketed = bracketStatus[i];
      const isGroupStart = isBracketed && (i === 0 || !bracketStatus[i - 1]);
      const isGroupEnd = isBracketed && (i === englishTextWords.length - 1 || !bracketStatus[i + 1]);

      const occKey = englishTextOccKeys[i];
      currentOccurrence[occKey] = (currentOccurrence[occKey] || 0) + 1;
      const occurrence = currentOccurrence[occKey];
      const occurrences = wordTotalOccurrences[occKey];

      const strippedBrackets = rawWord.replace(/[{}]/g, '');
      const punctMatch = strippedBrackets.match(/^(.*?)([.,;:!?]+)$/);
      const cleanWord = punctMatch ? punctMatch[1] : strippedBrackets;
      const trailingPunct = punctMatch ? punctMatch[2] : '';

      const wordObj = buildWordObject(cleanWord, occurrence, occurrences);

      if (!isFirstEmitted) {
        verseObjects.push({ type: 'text', text: isBracketed ? ' ' : '\n' });
      }
      isFirstEmitted = false;

      if (ustMode && isGroupStart) verseObjects.push({ type: 'text', text: '{' });
      if (!ustMode && isBracketed) verseObjects.push({ type: 'text', text: '{' });

      verseObjects.push(wordObj);

      if (!ustMode && isBracketed) verseObjects.push({ type: 'text', text: '}' });
      if (ustMode && isGroupEnd) verseObjects.push({ type: 'text', text: '}' });

      if (trailingPunct) verseObjects.push({ type: 'text', text: trailingPunct });

    } else {
      // Aligned group: one or more English words sharing one alignment entry
      const { align, wordIndices } = item;

      // Build word objects for all words in the group
      const childWordObjs = [];
      for (let k = 0; k < wordIndices.length; k++) {
        const i = wordIndices[k];
        const rawWord = englishTextWordsRaw[i];

        const occKey = englishTextOccKeys[i];
        currentOccurrence[occKey] = (currentOccurrence[occKey] || 0) + 1;
        const occurrence = currentOccurrence[occKey];
        const occurrences = wordTotalOccurrences[occKey];

        const strippedBrackets = rawWord.replace(/[{}]/g, '');
        const punctMatch = strippedBrackets.match(/^(.*?)([.,;:!?]+)$/);
        const cleanWord = punctMatch ? punctMatch[1] : strippedBrackets;
        const trailingPunct = punctMatch ? punctMatch[2] : '';

        childWordObjs.push({ wordObj: buildWordObject(cleanWord, occurrence, occurrences), trailingPunct, i });
      }

      // Bracket logic: per-word awareness for ULT, group-level for UST
      const firstI = wordIndices[0];
      const lastI = wordIndices[wordIndices.length - 1];
      const firstWordBracketed = bracketStatus[firstI];
      const anyBracketed = wordIndices.some(idx => bracketStatus[idx]);
      // UST group-level bracket tracking (contiguous cross-group runs)
      const isGroupStart = anyBracketed && (firstI === 0 || !bracketStatus[firstI - 1]);
      const isGroupEnd = anyBracketed && (lastI === englishTextWords.length - 1 || !bracketStatus[lastI + 1]);

      // Separator before the group
      if (!isFirstEmitted) {
        verseObjects.push({ type: 'text', text: firstWordBracketed ? ' ' : '\n' });
      }
      isFirstEmitted = false;

      if (ustMode && isGroupStart) verseObjects.push({ type: 'text', text: '{' });

      // Build children array with bracket handling
      const children = [];

      if (!ustMode) {
        // ULT mode: per-word brackets inside the milestone children.
        // If the first child is bracketed, emit { before the milestone (in verseObjects)
        // so brackets appear as {zaln-s ... word} matching published ULT format.
        const firstChildBracketed = bracketStatus[childWordObjs[0].i];
        if (firstChildBracketed) {
          verseObjects.push({ type: 'text', text: '{' });
        }

        let inBracketRun = firstChildBracketed;

        for (let k = 0; k < childWordObjs.length; k++) {
          const childBracketed = bracketStatus[childWordObjs[k].i];

          if (k > 0) {
            if (inBracketRun && !childBracketed) {
              // Transition bracketed → non-bracketed: close bracket, then separator
              children.push({ type: 'text', text: '}' });
              inBracketRun = false;
              children.push({ type: 'text', text: '\n' });
            } else if (!inBracketRun && childBracketed) {
              // Transition non-bracketed → bracketed: separator, then open bracket
              children.push({ type: 'text', text: '\n' });
              children.push({ type: 'text', text: '{' });
              inBracketRun = true;
            } else {
              children.push({ type: 'text', text: '\n' });
            }
          }

          children.push(childWordObjs[k].wordObj);
          if (childWordObjs[k].trailingPunct) {
            children.push({ type: 'text', text: childWordObjs[k].trailingPunct });
          }
        }

        // Close bracket run if it extends to end of children
        if (inBracketRun) {
          children.push({ type: 'text', text: '}' });
        }
      } else {
        // UST mode: standard children building (group-level brackets handled outside)
        for (let k = 0; k < childWordObjs.length; k++) {
          if (k > 0) children.push({ type: 'text', text: '\n' });
          children.push(childWordObjs[k].wordObj);
          if (childWordObjs[k].trailingPunct) {
            children.push({ type: 'text', text: childWordObjs[k].trailingPunct });
          }
        }
      }

      // Get Hebrew metadata
      const hebrewMeta = [];
      for (const idx of align.hebrew_indices) {
        const hw = hebrewWords[idx] || mapping.hebrew_words?.[idx];
        if (hw) {
          hebrewMeta.push({ hw, idx });
        }
      }

      if (hebrewMeta.length === 0) {
        // No Hebrew metadata — use children array (has bracket nodes in ULT mode)
        for (const child of children) {
          verseObjects.push(child);
        }
      } else if (hebrewMeta.length === 1) {
        // Single Hebrew word — all English children go inside one milestone
        const { hw, idx } = hebrewMeta[0];
        const sourceWord = mapping.hebrew_words?.[idx]?.word || hw.word;
        verseObjects.push(buildZalnMilestone(hw, sourceWord, children));
      } else {
        // Multiple Hebrew words — nest milestones, innermost holds the children
        let innermost = children;
        for (let j = hebrewMeta.length - 1; j >= 0; j--) {
          const { hw, idx } = hebrewMeta[j];
          const sourceWord = mapping.hebrew_words?.[idx]?.word || hw.word;
          innermost = [buildZalnMilestone(hw, sourceWord, innermost)];
        }
        verseObjects.push(...innermost);
      }

      if (ustMode && isGroupEnd) verseObjects.push({ type: 'text', text: '}' });

      // Trailing punctuation for the LAST word in the group is already inside children.
      // Nothing extra needed here.
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

// Normalize mapping data — support two AI-produced compact formats in addition to the
// canonical {reference, english_text, alignments:[{english:[], hebrew_indices:[]}]} format.
//
// Compact format 1 — verse-keyed object (produced by ULT-alignment skill):
//   {"1": [{hebrew_indices, hebrew_words, english_words, bracketed}], "2": [...]}
//
// Compact format 2 — flat array with verse field (produced by UST-alignment skill):
//   [{verse:1, hebrew_indices, hebrew_words, english_words, bracketed}, ...]
//
// Both compacts are grouped by verse and expanded to the canonical per-verse format.
function applyBrackets(words, bracketed) {
  if (!Array.isArray(bracketed) || bracketed.length === 0) return words;
  return words.map((w, i) => (bracketed[i] ? `{${w}}` : w));
}

function compactGroupsToCanonical(groups, bookCode, chapterNum) {
  // groups: array of {verse, hebrew_indices, hebrew_words, english_words, bracketed}
  const byVerse = {};
  for (const g of groups) {
    const v = g.verse;
    if (!byVerse[v]) byVerse[v] = [];
    byVerse[v].push(g);
  }
  return Object.entries(byVerse)
    .sort(([a], [b]) => parseInt(a) - parseInt(b))
    .map(([verseStr, entries]) => {
      const verseNum = parseInt(verseStr, 10);
      const alignments = entries.map(e => ({
        english: applyBrackets(e.english_words || [], e.bracketed),
        hebrew_indices: e.hebrew_indices || [],
      }));
      const english_text = alignments.map(a => a.english.join(' ')).join(' ');
      return {
        reference: `${bookCode} ${chapterNum || verseNum}:${verseNum}`,
        english_text,
        alignments,
      };
    });
}

function normalizeMapping(raw, bookCode, chapter) {
  // Already canonical: array of per-verse objects with reference + english_text + alignments
  if (Array.isArray(raw) && raw.length > 0 && raw[0].reference && raw[0].alignments) return raw;

  // Single canonical object (not in array)
  if (!Array.isArray(raw) && raw && raw.reference && raw.alignments) return [raw];

  // Compact format 2: flat array with verse + english_words fields (no alignments wrapper)
  if (Array.isArray(raw) && raw.length > 0 && raw[0].verse !== undefined && raw[0].english_words !== undefined) {
    return compactGroupsToCanonical(raw, bookCode, chapter);
  }

  // Compact format 1: verse-keyed object {"1": [...groups...], "2": [...]}
  if (!Array.isArray(raw) && typeof raw === 'object') {
    const flatGroups = [];
    for (const [verseStr, entries] of Object.entries(raw)) {
      const verseNum = parseInt(verseStr, 10);
      if (!Array.isArray(entries)) continue;
      for (const entry of entries) {
        flatGroups.push({ ...entry, verse: verseNum });
      }
    }
    return compactGroupsToCanonical(flatGroups, bookCode, chapter);
  }

  // Fallback: wrap single object
  return Array.isArray(raw) ? raw : [raw];
}

// Extract book code from Hebrew USFM headers (e.g. "ZEC")
const hebrewBookCode = (() => {
  const idHeader = (hebrewParsed.headers || []).find(h => h.tag === 'id');
  if (!idHeader) return 'UNK';
  return idHeader.content.trim().split(/\s+/)[0].toUpperCase();
})();

// Process mapping data
const mappings = normalizeMapping(mappingData, hebrewBookCode, filterChapter);

// Build output structure
const outputJson = {
  headers: [],
  chapters: {}
};

// Copy headers from Hebrew source (modify id tag, skip toc/mt — they cause
// duplicates when per-verse outputs are combined via sed)
const SKIP_HEADER_TAGS = new Set(['toc1', 'toc2', 'toc3', 'mt']);
for (const header of hebrewParsed.headers || []) {
  if (header.tag === 'id') {
    const bookId = header.content.split(' ')[0];
    outputJson.headers.push({
      tag: 'id',
      content: `${bookId} ${ustMode ? 'EN_UST' : 'EN_ULT'} - Aligned`
    });
  } else if (!SKIP_HEADER_TAGS.has(header.tag)) {
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

// Store USFM markers for post-processing (poetry, inter-verse, etc.)
const versePoetryMarkers = {};

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

  // Handle d_text (aligned superscription) if present
  const hasDText = !!mapping.d_text;
  let dLineUsfm = null;

  if (hasDText) {
    // Split alignments: section==="d" goes to \d line, rest goes to \v line
    const dAlignments = mapping.alignments.filter(a => a.section === 'd');
    const bodyAlignments = mapping.alignments.filter(a => a.section !== 'd');

    // Build \d line aligned objects
    const dMapping = {
      ...mapping,
      english_text: mapping.d_text,
      alignments: dAlignments
    };
    const dVerseObjects = buildAlignedVerseObjects(dMapping, hebrewWords, ustMode);

    // Convert \d objects to USFM string for post-processing insertion
    // Build a temporary structure to get the USFM
    const tempJson = {
      headers: [{ tag: 'id', content: 'TEMP' }],
      chapters: { [ref.chapter]: { 1: { verseObjects: dVerseObjects } } }
    };
    const tempUsfm = usfm.toUSFM(tempJson);
    // Extract just the aligned content (after \v 1 )
    const vMatch = tempUsfm.match(/\\v\s+1\s+([\s\S]*?)$/);
    if (vMatch) {
      // Clean up: trim trailing whitespace, remove trailing empty lines
      dLineUsfm = vMatch[1].replace(/\n+$/, '');
    }

    // Build \v line aligned objects (body only)
    const bodyMapping = {
      ...mapping,
      alignments: bodyAlignments
    };
    const verseObjects = buildAlignedVerseObjects(bodyMapping, hebrewWords, ustMode);

    // Extract USFM markers from source ULT
    const usfmMarkers = extractUsfmMarkers(ultContent, ref.chapter, ref.verse, hasDText);
    // Add d_line marker for post-processing
    if (dLineUsfm) {
      usfmMarkers.unshift({ dLine: dLineUsfm, position: -3 });
    }
    if (usfmMarkers.length > 0) {
      versePoetryMarkers[`${ref.chapter}:${ref.verse}`] = usfmMarkers;
    }

    outputJson.chapters[ref.chapter][ref.verse] = { verseObjects };
  } else {
    // Standard processing (no superscription)
    const verseObjects = buildAlignedVerseObjects(mapping, hebrewWords, ustMode);

    // Extract USFM markers from source ULT/UST (poetry, inter-verse, etc.)
    const usfmMarkers = extractUsfmMarkers(ultContent, ref.chapter, ref.verse, hasDText);
    if (usfmMarkers.length > 0) {
      versePoetryMarkers[`${ref.chapter}:${ref.verse}`] = usfmMarkers;
    }

    outputJson.chapters[ref.chapter][ref.verse] = { verseObjects };
  }
}

// Convert to USFM
let outputUsfm = usfm.toUSFM(outputJson);

// Post-process to add USFM markers (poetry, inter-verse, aligned \d)
// This is more reliable than trying to inject them into the JSON structure
const verseLastMatchIdx = {};  // verseRef → last matched word index (for ordered matching)

for (const [verseRef, markers] of Object.entries(versePoetryMarkers)) {
  const [, verse] = verseRef.split(':');

  for (const markerObj of markers) {
    const { position } = markerObj;

    if (position === -3 && markerObj.dLine) {
      // Aligned \d superscription line - insert before the verse line
      const versePattern = new RegExp(`(^|\\n)((?:\\\\q[12]\\s+)?\\\\v\\s+${verse}\\s)`, 'm');
      const dContent = `\\d ${markerObj.dLine}`;
      outputUsfm = outputUsfm.replace(versePattern, `$1${dContent}\n$2`);

    } else if (position === -2 && markerObj.markerLine) {
      // Inter-verse marker - insert on its own line before the verse line
      // Must go before any \q1/\q2 prefix on the verse line
      // In prose chapters, usfm-js may render \v N inline after previous verse content.
      // Ensure \v N is on its own line first before inserting the marker.
      const inlineVersePattern = new RegExp(`([^\\n])\\s+((?:\\\\q[12]\\s+)?\\\\v\\s+${verse}\\s)`, 'g');
      outputUsfm = outputUsfm.replace(inlineVersePattern, `$1\n$2`);
      const versePattern = new RegExp(`(^|\\n)((?:\\\\q[12]\\s+)?\\\\v\\s+${verse}\\s)`, 'm');
      outputUsfm = outputUsfm.replace(versePattern, `$1${markerObj.markerLine}\n$2`);

    } else if (position === 0 && markerObj.marker) {
      // Marker before verse - add before \v on same line
      const versePattern = new RegExp(`(\\\\v\\s+${verse}\\s)`);
      outputUsfm = outputUsfm.replace(versePattern, `\\${markerObj.marker} $1`);

    } else if (position === -1 && markerObj.startWords && markerObj.startWords.length > 0) {
      // Mid-verse marker - find alignment line where word sequence begins
      const verseStart = outputUsfm.indexOf(`\\v ${verse} `);
      if (verseStart === -1) continue;

      // Find next verse or end
      const nextVerseMatch = outputUsfm.slice(verseStart + 5).match(/\\v\s+\d/);
      const verseEnd = nextVerseMatch ? verseStart + 5 + nextVerseMatch.index : outputUsfm.length;
      const verseContent = outputUsfm.slice(verseStart, verseEnd);

      const lines = verseContent.split('\n');

      // Collect all aligned words with their line indices and character offsets
      // Lines may contain multiple words (e.g. supplied {words} adjacent to aligned words)
      const alignedWords = [];
      for (let i = 1; i < lines.length; i++) {  // Start at 1 to skip verse line
        const line = lines[i];
        if (!line.includes('\\w ')) continue;

        const wordMatches = line.matchAll(/\\w\s+([^|]+)\|/g);
        for (const match of wordMatches) {
          alignedWords.push({
            word: match[1].toLowerCase().replace(/[.,;:!?'"\u201C\u201D\u2018\u2019]/g, ''),
            lineIndex: i,
            matchOffset: match.index
          });
        }
      }

      // Find where startWords sequence begins (starting after last match for this verse)
      const minIdx = verseLastMatchIdx[verseRef] || 0;
      let targetLineIndex = -1;
      let targetWordIdx = -1;
      for (let i = minIdx; i <= alignedWords.length - markerObj.startWords.length; i++) {
        let matches = true;
        for (let j = 0; j < markerObj.startWords.length; j++) {
          if (alignedWords[i + j].word !== markerObj.startWords[j]) {
            matches = false;
            break;
          }
        }
        if (matches) {
          targetLineIndex = alignedWords[i].lineIndex;
          targetWordIdx = i;
          break;
        }
      }

      if (targetLineIndex > 0) {
        // Update last match position for ordered matching within this verse
        verseLastMatchIdx[verseRef] = targetWordIdx + markerObj.startWords.length;

        // Skip if line already has a \q marker (e.g., from position-0 insertion)
        if (lines[targetLineIndex].match(/^\\q[12]\s/)) continue;

        // Check if the target word shares its line with earlier words
        const targetOffset = alignedWords[targetWordIdx].matchOffset;
        let hasEarlierWords = false;
        for (let k = 0; k < targetWordIdx; k++) {
          if (alignedWords[k].lineIndex === targetLineIndex) {
            hasEarlierWords = true;
            break;
          }
        }

        if (hasEarlierWords) {
          // The target word is not the first word on its line - need to split
          // Find the outermost \zaln-s for the target word by scanning backward
          // Stop when we hit a \zaln-e (which closes a different word's alignment)
          const line = lines[targetLineIndex];
          let groupStart = targetOffset;
          let searchPos = targetOffset;

          while (searchPos > 0) {
            const zalnPos = line.lastIndexOf('\\zaln-s', searchPos - 1);
            if (zalnPos === -1) break;
            const between = line.substring(zalnPos, groupStart);
            if (between.includes('\\zaln-e')) break;
            groupStart = zalnPos;
            searchPos = zalnPos;
          }

          // Check for preceding { (supplied text marker)
          if (groupStart > 0) {
            let checkPos = groupStart - 1;
            while (checkPos >= 0 && line[checkPos] === ' ') checkPos--;
            if (checkPos >= 0 && line[checkPos] === '{') {
              groupStart = checkPos;
            }
          }

          // Split: previous words stay on current line, target starts new line with marker
          const firstPart = line.substring(0, groupStart).replace(/\s+$/, '');
          const secondPart = line.substring(groupStart);

          lines[targetLineIndex] = firstPart;
          lines.splice(targetLineIndex + 1, 0, `\\${markerObj.marker} ` + secondPart);
        } else {
          lines[targetLineIndex] = `\\${markerObj.marker} ` + lines[targetLineIndex];
        }

        const newVerseContent = lines.join('\n');
        outputUsfm = outputUsfm.slice(0, verseStart) + newVerseContent + outputUsfm.slice(verseEnd);
      }
    }
  }
}

// Write output
if (outputFile) {
  mkdirSync(dirname(outputFile), { recursive: true });
  writeFileSync(outputFile, outputUsfm);
  console.error(`Wrote aligned USFM to ${outputFile}`);
} else {
  console.log(outputUsfm);
}
