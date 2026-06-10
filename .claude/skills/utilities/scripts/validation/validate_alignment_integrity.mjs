#!/usr/bin/env node
/**
 * validate_alignment_integrity.mjs - Field-level gate for aligned USFM.
 *
 * Verifies that the alignment milestones in a generated aligned USFM file are
 * faithful to the Hebrew source — the failure class behind the June 2026
 * lemma/x-content Unicode churn (#88-#91):
 *   - every \zaln-s has non-empty x-strong, x-lemma, x-content
 *   - x-content byte-matches a Hebrew word in the same verse
 *     (a match that only succeeds after Unicode normalization is reported as
 *     a normalization mismatch — visually identical, byte-different)
 *   - x-lemma byte-matches the lemma of the matched Hebrew word
 *   - Hebrew-side x-occurrence/x-occurrences are internally consistent
 *   - English-side \w x-occurrence/x-occurrences are internally consistent
 *   - ULT mode: every Hebrew word in the verse is covered by at least one milestone
 *     (UST mode with --ust allows unaligned Hebrew)
 *
 * Usage:
 *   node validate_alignment_integrity.mjs --aligned <file> --hebrew <file> [--chapter N] [--ust] [--json]
 *
 * Exit codes: 0 = clean, 1 = problems found, 2 = usage/IO error
 */

import { readFileSync } from 'fs';
import { stripFetchedHeader, parseStructure } from './validate_usfm_structure.mjs';

/** Extract per-verse Hebrew words {text, lemma, strong} from Hebrew source USFM. */
export function parseHebrewVerseWords(hebrewText) {
  const { chapters } = parseStructure(stripFetchedHeader(hebrewText));
  const result = new Map(); // "ch:v" -> [{text, lemma, strong}]
  const wordRe = /\\w\s+([^|\\]+)\|([^\\]*)\\w\*/g;
  for (const [chNum, ch] of chapters) {
    for (const v of ch.verses) {
      const words = [];
      let m;
      wordRe.lastIndex = 0;
      while ((m = wordRe.exec(v.raw)) !== null) {
        const text = m[1].trim();
        const attrs = m[2];
        const lemma = (attrs.match(/lemma="([^"]*)"/) || [])[1] || '';
        const strong = (attrs.match(/strong="([^"]*)"/) || [])[1] || '';
        words.push({ text, lemma, strong });
      }
      result.set(`${chNum}:${v.num}`, words);
    }
  }
  return result;
}

/** Extract per-verse milestones and English words from aligned USFM. */
export function parseAlignedVerses(alignedText) {
  const { chapters } = parseStructure(stripFetchedHeader(alignedText));
  const result = new Map(); // "ch:v" -> { milestones: [...], englishWords: [...] }
  const zalnRe = /\\zaln-s\s*\|([^\\]*)\\\*/g;
  const wordRe = /\\w\s+([^|\\]+)\|([^\\]*)\\w\*/g;
  for (const [chNum, ch] of chapters) {
    for (const v of ch.verses) {
      const milestones = [];
      let m;
      zalnRe.lastIndex = 0;
      while ((m = zalnRe.exec(v.raw)) !== null) {
        const attrs = m[1];
        const get = (name) => (attrs.match(new RegExp(`${name}="([^"]*)"`)) || [])[1];
        milestones.push({
          strong: get('x-strong') ?? '',
          lemma: get('x-lemma') ?? '',
          morph: get('x-morph') ?? '',
          occurrence: parseInt(get('x-occurrence') ?? '0', 10),
          occurrences: parseInt(get('x-occurrences') ?? '0', 10),
          content: get('x-content') ?? '',
        });
      }
      const englishWords = [];
      wordRe.lastIndex = 0;
      while ((m = wordRe.exec(v.raw)) !== null) {
        const text = m[1].trim();
        const attrs = m[2];
        englishWords.push({
          text,
          occurrence: parseInt((attrs.match(/x-occurrence="(\d+)"/) || [])[1] || '0', 10),
          occurrences: parseInt((attrs.match(/x-occurrences="(\d+)"/) || [])[1] || '0', 10),
        });
      }
      result.set(`${chNum}:${v.num}`, { milestones, englishWords });
    }
  }
  return result;
}

function checkOccurrenceSequence(items, keyFn, ref, side, problems) {
  const groups = new Map();
  for (const item of items) {
    const key = keyFn(item);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  for (const [key, group] of groups) {
    const total = group.length;
    const occs = group.map((g) => g.occurrence).sort((a, b) => a - b);
    const badTotals = group.filter((g) => g.occurrences !== total);
    if (badTotals.length > 0) {
      problems.push({ level: 'error', ref, code: `${side}_occurrences_wrong`, message: `${ref} ${side} "${key}": ${total} instance(s) but x-occurrences says ${badTotals[0].occurrences}` });
    }
    for (let i = 0; i < occs.length; i++) {
      if (occs[i] !== i + 1) {
        problems.push({ level: 'error', ref, code: `${side}_occurrence_sequence`, message: `${ref} ${side} "${key}": x-occurrence values are [${occs.join(', ')}], expected 1..${total}` });
        break;
      }
    }
  }
}

/**
 * Validate aligned USFM against Hebrew source.
 * Returns array of problem objects {level, ref, code, message}.
 */
export function validateAlignmentIntegrity(alignedText, hebrewText, { chapter = null, ustMode = false } = {}) {
  const problems = [];
  const aligned = parseAlignedVerses(alignedText);
  const hebrew = parseHebrewVerseWords(hebrewText);

  if (aligned.size === 0) {
    problems.push({ level: 'error', code: 'no_aligned_verses', message: 'No verses found in aligned file' });
    return problems;
  }

  for (const [ref, { milestones, englishWords }] of aligned) {
    if (chapter !== null && parseInt(ref.split(':')[0], 10) !== chapter) continue;

    const hebrewWords = hebrew.get(ref);
    if (!hebrewWords) {
      problems.push({ level: 'error', ref, code: 'hebrew_verse_missing', message: `${ref}: verse not found in Hebrew source` });
      continue;
    }
    if (milestones.length === 0) {
      problems.push({ level: 'error', ref, code: 'no_milestones', message: `${ref}: no alignment milestones in verse` });
      continue;
    }

    const hebrewByText = new Map();
    for (const hw of hebrewWords) {
      if (!hebrewByText.has(hw.text)) hebrewByText.set(hw.text, []);
      hebrewByText.get(hw.text).push(hw);
    }
    const hebrewByNFC = new Map();
    for (const hw of hebrewWords) {
      const n = hw.text.normalize('NFC');
      if (!hebrewByNFC.has(n)) hebrewByNFC.set(n, []);
      hebrewByNFC.get(n).push(hw);
    }

    const coveredTexts = new Set();

    for (const ms of milestones) {
      if (!ms.content) {
        problems.push({ level: 'error', ref, code: 'empty_x_content', message: `${ref}: milestone with empty x-content (strong=${ms.strong || '?'})` });
        continue;
      }
      if (!ms.strong) {
        problems.push({ level: 'error', ref, code: 'empty_x_strong', message: `${ref}: milestone with empty x-strong (content=${ms.content})` });
      }
      if (!ms.lemma) {
        problems.push({ level: 'error', ref, code: 'empty_x_lemma', message: `${ref}: milestone with empty x-lemma (content=${ms.content})` });
      }

      const exact = hebrewByText.get(ms.content);
      if (exact) {
        coveredTexts.add(ms.content);
        // lemma must byte-match at least one Hebrew word with this surface text
        if (ms.lemma && !exact.some((hw) => hw.lemma === ms.lemma)) {
          const nfcLemmaMatch = exact.some((hw) => hw.lemma.normalize('NFC') === ms.lemma.normalize('NFC'));
          problems.push({
            level: 'error', ref,
            code: nfcLemmaMatch ? 'lemma_normalization_mismatch' : 'lemma_mismatch',
            message: nfcLemmaMatch
              ? `${ref}: x-lemma "${ms.lemma}" differs from Hebrew source lemma only in Unicode byte form (visually identical)`
              : `${ref}: x-lemma "${ms.lemma}" does not match Hebrew source lemma(s) [${exact.map((h) => h.lemma).join(', ')}] for word ${ms.content}`,
          });
        }
      } else {
        const nfc = hebrewByNFC.get(ms.content.normalize('NFC'));
        if (nfc) {
          coveredTexts.add(nfc[0].text);
          problems.push({ level: 'error', ref, code: 'content_normalization_mismatch', message: `${ref}: x-content "${ms.content}" differs from Hebrew source only in Unicode byte form (visually identical, byte-different)` });
        } else {
          problems.push({ level: 'error', ref, code: 'content_not_in_hebrew', message: `${ref}: x-content "${ms.content}" not found among Hebrew words of this verse` });
        }
      }
    }

    // Hebrew-side and English-side occurrence consistency
    checkOccurrenceSequence(milestones.filter((m) => m.content), (m) => m.content, ref, 'hebrew', problems);
    checkOccurrenceSequence(englishWords, (w) => w.text, ref, 'english', problems);

    // Coverage (ULT only): every Hebrew word text must appear as x-content
    if (!ustMode) {
      for (const [text] of hebrewByText) {
        if (!coveredTexts.has(text)) {
          problems.push({ level: 'error', ref, code: 'hebrew_word_unaligned', message: `${ref}: Hebrew word "${text}" has no alignment milestone` });
        }
      }
    }
  }

  return problems;
}

function main() {
  const args = process.argv.slice(2);
  let alignedFile = null, hebrewFile = null, chapter = null, ustMode = false, asJson = false;
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--aligned': alignedFile = args[++i]; break;
      case '--hebrew': hebrewFile = args[++i]; break;
      case '--chapter': chapter = parseInt(args[++i], 10); break;
      case '--ust': ustMode = true; break;
      case '--json': asJson = true; break;
      case '--help': case '-h':
        console.log('Usage: node validate_alignment_integrity.mjs --aligned <file> --hebrew <file> [--chapter N] [--ust] [--json]');
        process.exit(0);
        break;
      default:
        console.error(`Unknown argument: ${args[i]}`);
        process.exit(2);
    }
  }
  if (!alignedFile || !hebrewFile) {
    console.error('Error: --aligned and --hebrew are required');
    process.exit(2);
  }

  let alignedText, hebrewText;
  try {
    alignedText = readFileSync(alignedFile, 'utf8');
    hebrewText = readFileSync(hebrewFile, 'utf8');
  } catch (e) {
    console.error(`Error reading input: ${e.message}`);
    process.exit(2);
  }

  const problems = validateAlignmentIntegrity(alignedText, hebrewText, { chapter, ustMode });
  if (asJson) {
    console.log(JSON.stringify({ file: alignedFile, problems }, null, 2));
  } else {
    for (const p of problems) {
      console.log(`${p.level.toUpperCase()} [${p.code}] ${p.message}`);
    }
    console.log(problems.length === 0
      ? `OK: ${alignedFile} passed alignment integrity validation`
      : `FAIL: ${problems.length} problem(s) in ${alignedFile}`);
  }
  process.exit(problems.length === 0 ? 0 : 1);
}

import { pathToFileURL } from 'url';
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
