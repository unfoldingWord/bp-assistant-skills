#!/usr/bin/env node
// Checklist candidates for issue types that analysts under-note (issue #224).
//
// Reads one chapter of morph-tagged Hebrew USFM (UHB `\w ...|x-morph="..."`)
// and the plain ULT chapter, and prints candidate rows as TSV:
//   ref  issue_type  hint  reason
//
// Each check is calibrated against the published notes for NAM 1, JER 52,
// ISA 38 and EZK 3. Rows are candidates for the analysts to confirm or
// reject, the same way detect_abstract_nouns output is used.
//
// Usage:
//   node checklist_candidates.mjs --hebrew <hebrew_chapter.usfm> --ult <ult_plain.usfm>

import fs from 'node:fs';

function arg(name) {
  const i = process.argv.indexOf(`--${name}`);
  return i > 0 ? process.argv[i + 1] : null;
}

// --- Hebrew: verse -> [{ form, segs }] where segs are morph segments without "He,"
export function parseHebrew(text) {
  const verses = new Map();
  let chapter = null;
  let verse = null;
  const re = /\\c\s+(\d+)|\\v\s+(\d+)|\\w\s+([^|\\]+)\|[^\\]*?x-morph="([^"]+)"/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m[1]) { chapter = Number(m[1]); continue; }
    if (m[2]) { verse = Number(m[2]); verses.set(verse, []); continue; }
    if (verse == null) continue;
    const segs = m[4].replace(/^[A-Za-z]{2},/, '').split(':');
    verses.get(verse).push({ form: m[3].replace(/\u2060/g, ''), segs });
  }
  return { chapter, verses };
}

// --- ULT: verse -> { text, poetry } ; text keeps paragraph markers as "¶"
export function parseUlt(text) {
  const verses = new Map();
  const re = /\\v\s+(\d+)\s([\s\S]*?)(?=\\v\s+\d+|$)/g;
  let m;
  let prevTail = '';
  const body = text.replace(/\\c\s+\d+/g, '');
  while ((m = re.exec(body)) !== null) {
    const raw = m[2];
    const poetry = /\\q\d?\s*$/.test(prevTail) || /\\q/.test(raw.split(/\s+/).slice(0, 3).join(' '));
    const clean = raw
      .replace(/\\(p|m|q\d?|b|nb)\b\*?/g, ' ¶ ')
      .replace(/\\[a-z0-9-]+\*?/gi, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    verses.set(Number(m[1]), { text: clean, poetry });
    prevTail = raw.slice(-12);
  }
  return verses;
}

// Finite, non-imperative verb: perfect, sequential perfect/imperfect, imperfect,
// cohortative, jussive. "You, take" with an imperative is not noted in gold.
const FINITE = /^V[A-Za-z][pqiwhj](\d)([mfc])([sp])/;
const PRON = /^Pp(\d)([mfc])([sp])/;
const SECOND = /^(?:V[A-Za-z][a-z]|Sp|Pp)2([mfc])([sp])/;

// writing-pronouns: independent personal pronoun stated beside a finite verb
// of the same person and number (the verb already marks the subject).
export function emphaticPronouns(heb) {
  const out = [];
  for (const [v, words] of heb.verses) {
    words.forEach((w, i) => {
      if (w.segs.includes('Td')) return; // "those"/"these": demonstrative use
      const seg = w.segs.find((s) => PRON.test(s));
      if (!seg) return;
      const [, p, , n] = seg.match(PRON);
      // Stay inside the pronoun's clause: a vav-prefixed word starts a new one
      // (a standalone conjunction such as כִּי has the bare morph "C").
      const vav = (x) => x.segs.length > 1 && x.segs[0] === 'C';
      const win = [];
      for (let j = i + 1; j < Math.min(words.length, i + 5) && !vav(words[j]); j++) win.push(words[j]);
      if (!vav(w)) {
        for (let j = i - 1; j >= Math.max(0, i - 3); j--) {
          win.push(words[j]);
          if (vav(words[j])) break;
        }
      }
      const hit = win.find((x) => x.segs.some((s) => {
        const f = s.match(FINITE);
        return f && f[1] === p && f[3] === n;
      }));
      if (hit) out.push([v, 'writing-pronouns', w.form, `independent pronoun (${seg}) beside verb ${hit.form} - emphasis/contrast?`]);
    });
  }
  return out;
}

// figs-yousingular / writing-pronouns: second-person number and addressee
// changes, from verb, suffix and pronoun morphology.
export function secondPerson(heb) {
  const out = [];
  let prev = null;
  for (const [v, words] of heb.verses) {
    const counts = {};
    for (const w of words) for (const s of w.segs) {
      const m = s.match(SECOND);
      if (m) counts[m[1] + m[2]] = (counts[m[1] + m[2]] || 0) + 1;
    }
    // Dominant gender+number for the verse; a stray minority form is noise.
    const sig = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0];
    if (!sig) continue;
    const num = sig[1];
    const label = num === 'p' ? 'plural' : 'singular';
    if ((prev === null && num === 'p') || (prev !== null && num !== prev[1])) {
      out.push([v, 'figs-yousingular', `you (${sig})`, `second person is ${label}${prev ? ` after ${prev}` : ''}`]);
    }
    if (prev !== null && sig !== prev) {
      out.push([v, 'writing-pronouns', `you (${sig})`, `addressee may change (was ${prev})`]);
    }
    prev = sig;
  }
  return out;
}

// figs-quotemarks: a quotation opened while two are already open (level 3+).
export function quoteLevels(ult) {
  const out = [];
  const stack = [];
  for (const [v, { text }] of ult) {
    let maxDepth = 0;
    let atPara = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (c === '¶') { atPara = true; continue; }
      if (c === ' ') continue;
      if (c === '“' || c === '‘') {
        // A new paragraph inside a long speech re-opens the outer quote.
        if (atPara && stack.length && stack[0] === c) { atPara = false; continue; }
        stack.push(c);
        maxDepth = Math.max(maxDepth, stack.length);
      } else if (c === '”') {
        const k = stack.lastIndexOf('“');
        if (k >= 0) stack.length = k;
      } else if (c === '’') {
        const apostrophe = /\p{L}/u.test(text[i - 1] || '') && /\p{L}/u.test(text[i + 1] || '');
        // Closing an outer level also closes any level the ULT left open.
        const k = stack.lastIndexOf('‘');
        if (!apostrophe && k >= 0) stack.length = k;
      }
      atPara = false;
    }
    if (maxDepth >= 3) out.push([v, 'figs-quotemarks', '“ ‘ “', `${maxDepth} levels of quotation`]);
  }
  return out;
}

// grammar-connect-logic-result: a poetic sentence that opens with "For"/"Because",
// giving the reason for what came before (reason after result).
export function sentenceInitialReason(ult) {
  const out = [];
  for (const [v, { text, poetry }] of ult) {
    if (!poetry) continue;
    const re = /(?:^|[.?!;:]\s*[”’]*)[\s¶“‘]*(For|Because)\b(?! because\b)/g;
    let m;
    while ((m = re.exec(text)) !== null) {
      out.push([v, 'grammar-connect-logic-result', m[1], 'sentence-initial reason for the preceding statement']);
    }
  }
  return out;
}

export function checklistCandidates(hebrewText, ultText) {
  const heb = parseHebrew(hebrewText);
  const ult = parseUlt(ultText);
  const ch = heb.chapter ?? '';
  const rows = [
    ...emphaticPronouns(heb),
    ...secondPerson(heb),
    ...quoteLevels(ult),
    ...sentenceInitialReason(ult),
  ].sort((a, b) => a[0] - b[0]);
  return rows.map(([v, ...rest]) => [`${ch}:${v}`, ...rest]);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const hebrew = arg('hebrew');
  const ult = arg('ult');
  if (!hebrew || !ult) {
    console.error('Usage: checklist_candidates.mjs --hebrew <hebrew_chapter.usfm> --ult <ult_plain.usfm>');
    process.exit(2);
  }
  const rows = checklistCandidates(fs.readFileSync(hebrew, 'utf8'), fs.readFileSync(ult, 'utf8'));
  console.log(['ref', 'issue_type', 'hint', 'reason'].join('\t'));
  for (const r of rows) console.log(r.join('\t'));
}
