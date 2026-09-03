#!/usr/bin/env node
/**
 * score_benchmark.mjs - Score generated ULT/UST/TN against a published golden chapter.
 *
 * Compares pipeline output for a golden chapter (JOS 1, NAM 1, MAL 1) against
 * the published human-polished version and produces a scorecard. The point is
 * regression tracking: run the pipeline on a golden chapter before and after a
 * skill change and compare scorecards. (Scores are an upper bound on quality
 * for unpublished books — generation can consult published precedent.)
 *
 * Usage:
 *   node score_benchmark.mjs --book NAM --chapter 1 [options]
 *
 * Options:
 *   --generated-ult <file>   default: output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm
 *   --generated-ust <file>   default: output/AI-UST/<BOOK>/<BOOK>-<CH>.usfm
 *   --generated-tn <file>    default: output/notes/<BOOK>/<BOOK>-<CH>.tsv
 *   --self-test              score the golden files against themselves (expect perfect scores)
 *   --json                   print scorecard JSON to stdout instead of writing files
 *
 * Output: output/benchmark/<BOOK>/<BOOK>-<CH>-scorecard.md and .json
 *
 * Exit codes: 0 = scored, 2 = missing inputs/usage error
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';
import { parseStructure, verseVisibleText, stripFetchedHeader } from '../../utilities/scripts/validation/validate_usfm_structure.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');
const REPO_ROOT = resolve(SKILL_DIR, '../../..');

const STOPWORDS = new Set(['the', 'a', 'an', 'of', 'and', 'to', 'in', 'is', 'are', 'was', 'were', 'will', 'be', 'it', 'he', 'she', 'they', 'them', 'his', 'her', 'their', 'you', 'your', 'i', 'my', 'me', 'we', 'us', 'our', 'for', 'with', 'on', 'at', 'by', 'from', 'that', 'this', 'who', 'whom', 'which', 'not', 'no', 'do', 'does', 'did', 'have', 'has', 'had', 'him', 'its', 'as', 'so', 'but', 'or', 'if', 'then', 'there', 'all']);

export function extractVerseTexts(usfm) {
  const { chapters } = parseStructure(stripFetchedHeader(usfm));
  const out = new Map(); // verseNum -> { text, braces }
  for (const [, ch] of chapters) {
    for (const v of ch.verses) {
      const text = verseVisibleText(v.raw);
      const braces = (v.raw.match(/{/g) || []).length;
      out.set(v.num, { text, braces });
    }
  }
  return out;
}

export function tokenize(text) {
  return text
    .toLowerCase()
    .replace(/[“”‘’"'.,;:!?…—–()\[\]{}]/g, ' ')
    .split(/\s+/)
    // Drop any residual USFM-marker fragments (backslash-bearing tokens such as
    // the self-closing "\*" left by a milestone like "\ts\*"). Translation prose
    // never contains a backslash, so this only removes leaked markup, not text.
    .filter((w) => w.length > 0 && !w.includes('\\'));
}

export function tokenF1(genTokens, goldTokens) {
  if (genTokens.length === 0 && goldTokens.length === 0) return { f1: 1, precision: 1, recall: 1 };
  if (genTokens.length === 0 || goldTokens.length === 0) return { f1: 0, precision: 0, recall: 0 };
  const goldCounts = new Map();
  for (const t of goldTokens) goldCounts.set(t, (goldCounts.get(t) || 0) + 1);
  let overlap = 0;
  for (const t of genTokens) {
    const c = goldCounts.get(t) || 0;
    if (c > 0) { overlap++; goldCounts.set(t, c - 1); }
  }
  const precision = overlap / genTokens.length;
  const recall = overlap / goldTokens.length;
  const f1 = precision + recall === 0 ? 0 : (2 * precision * recall) / (precision + recall);
  return { f1, precision, recall };
}

function diffTokens(genTokens, goldTokens) {
  const gold = new Map();
  for (const t of goldTokens) gold.set(t, (gold.get(t) || 0) + 1);
  const gen = new Map();
  for (const t of genTokens) gen.set(t, (gen.get(t) || 0) + 1);
  const missing = [], extra = [];
  for (const [t, c] of gold) {
    const g = gen.get(t) || 0;
    for (let i = 0; i < c - g; i++) missing.push(t);
  }
  for (const [t, c] of gen) {
    const g = gold.get(t) || 0;
    for (let i = 0; i < c - g; i++) extra.push(t);
  }
  return { missing, extra };
}

export function scoreText(generatedUsfm, goldenUsfm) {
  const gen = extractVerseTexts(generatedUsfm);
  const gold = extractVerseTexts(goldenUsfm);
  const verses = [];
  let f1Sum = 0, covered = 0;
  const genVocab = new Set(), goldVocab = new Set();
  let genBraces = 0, goldBraces = 0;

  for (const [num, g] of gold) {
    goldBraces += g.braces;
    const goldTokens = tokenize(g.text);
    for (const t of goldTokens) if (!STOPWORDS.has(t)) goldVocab.add(t);
    const genV = gen.get(num);
    if (!genV) {
      verses.push({ verse: num, f1: 0, missing: ['<verse missing>'], extra: [] });
      continue;
    }
    covered++;
    genBraces += genV.braces;
    const genTokens = tokenize(genV.text);
    for (const t of genTokens) if (!STOPWORDS.has(t)) genVocab.add(t);
    const { f1 } = tokenF1(genTokens, goldTokens);
    f1Sum += f1;
    const { missing, extra } = diffTokens(genTokens, goldTokens);
    verses.push({ verse: num, f1: Number(f1.toFixed(3)), missing, extra });
  }

  const vocabOverlap = [...genVocab].filter((t) => goldVocab.has(t)).length;
  const vocabUnion = new Set([...genVocab, ...goldVocab]).size;

  return {
    verseCoverage: `${covered}/${gold.size}`,
    meanF1: gold.size ? Number((f1Sum / gold.size).toFixed(3)) : 0,
    vocabJaccard: vocabUnion ? Number((vocabOverlap / vocabUnion).toFixed(3)) : 0,
    braces: { generated: genBraces, golden: goldBraces },
    worstVerses: verses.filter((v) => v.f1 < 1).sort((a, b) => a.f1 - b.f1).slice(0, 5),
    verses,
  };
}

export function parseTnRows(tsv) {
  // Split on \r?\n, not just \n: a CRLF-terminated TSV otherwise leaves a
  // stray \r on the last field of every line ("Note\r" in the header), which
  // breaks col('Note')'s exact-match lookup and silently makes every row's
  // `note` empty. Discovered while adding the seeHowSharePct metric — the
  // bundled golden fixtures are CRLF.
  const lines = tsv.split(/\r?\n/).filter((l) => l.trim());
  const header = lines[0].split('\t');
  const col = (name) => header.indexOf(name);
  const iRef = col('Reference'), iId = col('ID'), iTags = col('Tags'), iSr = col('SupportReference'), iQuote = col('Quote'), iNote = col('Note');
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const c = lines[i].split('\t');
    rows.push({
      ref: c[iRef] || '', id: c[iId] || '',
      tags: iTags >= 0 ? (c[iTags] || '') : '',
      type: ((c[iSr] || '').match(/([a-z-]+)\s*$/) || [])[1] || '',
      quote: c[iQuote] || '', note: c[iNote] || '',
    });
  }
  return rows;
}

export function scoreNotes(generatedTsv, goldenTsv, chapter) {
  const gen = parseTnRows(generatedTsv).filter((r) => r.ref.startsWith(`${chapter}:`));
  const gold = parseTnRows(goldenTsv).filter((r) => r.ref.startsWith(`${chapter}:`));
  const isIntro = (r) => r.ref.endsWith(':intro');
  const genNotes = gen.filter((r) => !isIntro(r));
  const goldNotes = gold.filter((r) => !isIntro(r));

  // (verse, type) multiset matching: did we note what the human team noted?
  const key = (r) => `${r.ref}|${r.type}`;
  const goldKeys = new Map();
  for (const r of goldNotes) goldKeys.set(key(r), (goldKeys.get(key(r)) || 0) + 1);
  let matched = 0;
  const genKeys = new Map();
  for (const r of genNotes) genKeys.set(key(r), (genKeys.get(key(r)) || 0) + 1);
  const unmatchedGolden = [], unmatchedGenerated = [];
  for (const [k, c] of goldKeys) {
    const g = genKeys.get(k) || 0;
    matched += Math.min(c, g);
    for (let i = 0; i < c - g; i++) unmatchedGolden.push(k);
  }
  for (const [k, c] of genKeys) {
    const g = goldKeys.get(k) || 0;
    for (let i = 0; i < c - g; i++) unmatchedGenerated.push(k);
  }

  // Verse-only matching (ignore type): "did we write a note on each verse the
  // humans noted?". Golden range refs (e.g. "3:3-4") are expanded to their
  // component verses so a range note can match single-verse generated notes;
  // without this a range key can never match and verse-recall is understated.
  const expandRef = (ref) => {
    const m = ref.match(/^(\d+):(\d+)(?:-(\d+))?$/);
    if (!m) return [ref];
    const [, ch, a, b] = m;
    const lo = parseInt(a, 10), hi = b ? parseInt(b, 10) : lo;
    const verses = [];
    for (let v = lo; v <= hi; v++) verses.push(`${ch}:${v}`);
    return verses;
  };
  // Each generated note is a single matchable unit even when its own ref is a
  // range (it may satisfy any one of its component verses, not one per verse) —
  // otherwise a generated range note could match twice and push precision > 1.
  const genUnits = genNotes.map((r) => ({ verses: new Set(expandRef(r.ref)), used: false }));
  let verseMatched = 0;
  for (const r of goldNotes) {
    const goldVerses = expandRef(r.ref);
    const unit = genUnits.find((u) => !u.used && goldVerses.some((v) => u.verses.has(v)));
    if (unit) {
      unit.used = true;
      verseMatched++;
    }
  }

  // Convention checks on generated notes
  const conventions = [];
  for (const r of genNotes) {
    if (r.tags && r.tags.trim()) {
      conventions.push({ ref: r.ref, id: r.id, problem: `non-empty Tags value "${r.tags.trim()}" (published golden Tags are always empty; internal tags like ISSUE:MATCH_FAIL must not ship)` });
    }
    if (/Alternate translation:/.test(r.note) && !/Alternate translation:\s*\[/.test(r.note)) {
      conventions.push({ ref: r.ref, id: r.id, problem: 'AT not in [square brackets]' });
    }
    if (/["']/.test(r.note)) {
      conventions.push({ ref: r.ref, id: r.id, problem: 'straight quote character in Note' });
    }
    if (!/^[a-z][a-z0-9]{3}$/.test(r.id)) {
      conventions.push({ ref: r.ref, id: r.id, problem: 'ID format invalid' });
    }
    if (r.type === 'figs-abstractnouns' && !/abstract noun/.test(r.note)) {
      conventions.push({ ref: r.ref, id: r.id, problem: 'figs-abstractnouns note missing template phrase "abstract noun"' });
    }
    if (r.type === 'figs-rquestion' && !/question/.test(r.note)) {
      conventions.push({ ref: r.ref, id: r.id, problem: 'figs-rquestion note missing the word "question"' });
    }
    if (r.type === 'figs-metaphor' && !/as if|as though|is using/.test(r.note)) {
      conventions.push({ ref: r.ref, id: r.id, problem: 'figs-metaphor note missing template phrasing ("as if" / "as though" / "is using")' });
    }
  }
  const ids = genNotes.map((r) => r.id);
  const dupes = ids.filter((id, i) => ids.indexOf(id) !== i);
  for (const d of [...new Set(dupes)]) {
    conventions.push({ ref: '-', id: d, problem: 'duplicate ID within generated notes' });
  }

  // Per-verse density table
  const density = new Map();
  for (const r of goldNotes) {
    const v = r.ref.split(':')[1];
    if (!density.has(v)) density.set(v, { golden: 0, generated: 0 });
    density.get(v).golden++;
  }
  for (const r of genNotes) {
    const v = r.ref.split(':')[1];
    if (!density.has(v)) density.set(v, { golden: 0, generated: 0 });
    density.get(v).generated++;
  }

  // REPORTED-ONLY metric: see-how coverage. See calibration.json `seeHowSharePct`.
  // see-how share and also-occurs count, generated vs golden. Not a pass/fail gate —
  // the see-how rule is the spec, not a calibration band — just visibility over time.
  const SEE_HOW_RE = /see how you translated/i;
  const ALSO_OCCURS_RE = /this also occurs in verses?/i;
  const seeHowSharePct = (rows) => (rows.length ? Number(((100 * rows.filter((r) => SEE_HOW_RE.test(r.note)).length) / rows.length).toFixed(1)) : 0);
  const alsoOccursCount = (rows) => rows.filter((r) => ALSO_OCCURS_RE.test(r.note)).length;

  return {
    counts: { generated: genNotes.length, golden: goldNotes.length, ratio: goldNotes.length ? Number((genNotes.length / goldNotes.length).toFixed(2)) : null },
    intro: { generated: gen.some(isIntro), golden: gold.some(isIntro) },
    typeRecall: goldNotes.length ? Number((matched / goldNotes.length).toFixed(3)) : null,
    typePrecision: genNotes.length ? Number((matched / genNotes.length).toFixed(3)) : null,
    verseRecall: goldNotes.length ? Number((verseMatched / goldNotes.length).toFixed(3)) : null,
    versePrecision: genNotes.length ? Number((verseMatched / genNotes.length).toFixed(3)) : null,
    unmatchedGolden,
    unmatchedGenerated,
    conventionProblems: conventions,
    density: Object.fromEntries([...density.entries()].sort((a, b) => Number(a[0]) - Number(b[0]))),
    seeHow: {
      seeHowSharePct: { generated: seeHowSharePct(genNotes), golden: seeHowSharePct(goldNotes) },
      alsoOccursCount: { generated: alsoOccursCount(genNotes), golden: alsoOccursCount(goldNotes) },
    },
  };
}

function renderMarkdown(scorecard) {
  const { book, chapter, ult, ust, tn } = scorecard;
  const lines = [];
  lines.push(`# Benchmark scorecard: ${book} ${chapter}`);
  lines.push('');
  lines.push(`Generated: ${scorecard.generatedAt} | Golden ref: ${scorecard.goldenRef}`);
  lines.push('');
  lines.push('| Metric | ULT | UST |');
  lines.push('|--------|-----|-----|');
  lines.push(`| Verse coverage | ${ult?.verseCoverage ?? 'n/a'} | ${ust?.verseCoverage ?? 'n/a'} |`);
  lines.push(`| Mean token F1 vs published | ${ult?.meanF1 ?? 'n/a'} | ${ust?.meanF1 ?? 'n/a'} |`);
  lines.push(`| Content-vocabulary overlap | ${ult?.vocabJaccard ?? 'n/a'} | ${ust?.vocabJaccard ?? 'n/a'} |`);
  lines.push(`| Supplied {braces} gen/golden | ${ult ? `${ult.braces.generated}/${ult.braces.golden}` : 'n/a'} | ${ust ? `${ust.braces.generated}/${ust.braces.golden}` : 'n/a'} |`);
  lines.push('');
  for (const [label, t] of [['ULT', ult], ['UST', ust]]) {
    if (!t || t.worstVerses.length === 0) continue;
    lines.push(`## ${label}: verses furthest from published`);
    for (const v of t.worstVerses) {
      lines.push(`- v${v.verse} (F1 ${v.f1}) — missing: ${v.missing.slice(0, 12).join(', ') || 'none'}${v.missing.length > 12 ? '…' : ''}; extra: ${v.extra.slice(0, 12).join(', ') || 'none'}${v.extra.length > 12 ? '…' : ''}`);
    }
    lines.push('');
  }
  if (tn) {
    lines.push('## Translation Notes');
    lines.push(`- Notes: ${tn.counts.generated} generated vs ${tn.counts.golden} published (ratio ${tn.counts.ratio})`);
    lines.push(`- Type@verse recall (published notes we also flagged): ${tn.typeRecall === null ? 'n/a' : (tn.typeRecall * 100).toFixed(0) + '%'}`);
    lines.push(`- Type@verse precision (our notes the humans also had): ${tn.typePrecision === null ? 'n/a' : (tn.typePrecision * 100).toFixed(0) + '%'}`);
    lines.push(`- Verse-only recall (verses the humans noted that we also noted): ${tn.verseRecall === null ? 'n/a' : (tn.verseRecall * 100).toFixed(0) + '%'}`);
    lines.push(`- Verse-only precision (our noted verses the humans also noted): ${tn.versePrecision === null ? 'n/a' : (tn.versePrecision * 100).toFixed(0) + '%'}`);
    lines.push(`- Chapter intro row: generated ${tn.intro.generated ? 'yes' : 'no'} / published ${tn.intro.golden ? 'yes' : 'no'}`);
    lines.push(`- See-how share (REPORTED, not gated): ${tn.seeHow.seeHowSharePct.generated}% generated vs ${tn.seeHow.seeHowSharePct.golden}% published; also-occurs sentences: ${tn.seeHow.alsoOccursCount.generated} generated vs ${tn.seeHow.alsoOccursCount.golden} published`);
    lines.push(`- Convention problems in generated notes: ${tn.conventionProblems.length}`);
    if (tn.conventionProblems.length) {
      for (const c of tn.conventionProblems.slice(0, 15)) lines.push(`  - ${c.ref} ${c.id}: ${c.problem}`);
    }
    if (tn.unmatchedGolden.length) {
      lines.push('');
      lines.push('### Published notes with no generated counterpart (verse|type)');
      for (const k of tn.unmatchedGolden.slice(0, 25)) lines.push(`- ${k}`);
      if (tn.unmatchedGolden.length > 25) lines.push(`- …and ${tn.unmatchedGolden.length - 25} more`);
    }
    if (tn.unmatchedGenerated.length) {
      lines.push('');
      lines.push('### Generated notes the humans did not have (verse|type)');
      for (const k of tn.unmatchedGenerated.slice(0, 25)) lines.push(`- ${k}`);
      if (tn.unmatchedGenerated.length > 25) lines.push(`- …and ${tn.unmatchedGenerated.length - 25} more`);
    }
  }
  lines.push('');
  return lines.join('\n');
}

function main() {
  const args = process.argv.slice(2);
  let book = null, chapter = null, genUlt = null, genUst = null, genTn = null, selfTest = false, asJson = false;
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--book': book = args[++i]?.toUpperCase(); break;
      case '--chapter': chapter = parseInt(args[++i], 10); break;
      case '--generated-ult': genUlt = args[++i]; break;
      case '--generated-ust': genUst = args[++i]; break;
      case '--generated-tn': genTn = args[++i]; break;
      case '--self-test': selfTest = true; break;
      case '--json': asJson = true; break;
      case '--help': case '-h':
        console.log('Usage: node score_benchmark.mjs --book NAM --chapter 1 [--generated-ult f] [--generated-ust f] [--generated-tn f] [--self-test] [--json]');
        process.exit(0);
        break;
      default:
        console.error(`Unknown argument: ${args[i]}`);
        process.exit(2);
    }
  }
  if (!book || !chapter) {
    console.error('Error: --book and --chapter are required');
    process.exit(2);
  }

  const ch2 = String(chapter).padStart(2, '0');
  const goldenDir = join(SKILL_DIR, 'golden', book);
  const goldUltFile = join(goldenDir, `${book}-${ch2}.ult.usfm`);
  const goldUstFile = join(goldenDir, `${book}-${ch2}.ust.usfm`);
  const goldTnFile = join(goldenDir, `${book}-${ch2}.tn.tsv`);
  if (!existsSync(goldUltFile)) {
    console.error(`No golden fixture for ${book} ${chapter} (${goldUltFile}). Run fetch_golden.mjs first or add the chapter to the golden set.`);
    process.exit(2);
  }

  if (selfTest) {
    genUlt = goldUltFile; genUst = goldUstFile; genTn = goldTnFile;
  } else {
    genUlt = genUlt || join(REPO_ROOT, `output/AI-ULT/${book}/${book}-${ch2}.usfm`);
    genUst = genUst || join(REPO_ROOT, `output/AI-UST/${book}/${book}-${ch2}.usfm`);
    genTn = genTn || join(REPO_ROOT, `output/notes/${book}/${book}-${ch2}.tsv`);
  }

  let goldenRef = 'unknown';
  try {
    goldenRef = JSON.parse(readFileSync(join(SKILL_DIR, 'golden/meta.json'), 'utf8')).ultUstRef;
  } catch { /* meta is informational */ }

  const scorecard = { book, chapter, generatedAt: new Date().toISOString(), goldenRef, selfTest };

  if (existsSync(genUlt)) {
    scorecard.ult = scoreText(readFileSync(genUlt, 'utf8'), readFileSync(goldUltFile, 'utf8'));
  } else {
    console.error(`note: generated ULT not found at ${genUlt} — skipping ULT scoring`);
  }
  if (existsSync(genUst) && existsSync(goldUstFile)) {
    scorecard.ust = scoreText(readFileSync(genUst, 'utf8'), readFileSync(goldUstFile, 'utf8'));
  } else if (!existsSync(genUst)) {
    console.error(`note: generated UST not found at ${genUst} — skipping UST scoring`);
  }
  if (existsSync(genTn) && existsSync(goldTnFile)) {
    scorecard.tn = scoreNotes(readFileSync(genTn, 'utf8'), readFileSync(goldTnFile, 'utf8'), chapter);
  } else if (!existsSync(genTn)) {
    console.error(`note: generated TN not found at ${genTn} — skipping TN scoring`);
  }

  if (!scorecard.ult && !scorecard.ust && !scorecard.tn) {
    console.error('Nothing to score — no generated files found.');
    process.exit(2);
  }

  if (asJson) {
    console.log(JSON.stringify(scorecard, null, 2));
  } else {
    const outDir = join(REPO_ROOT, `output/benchmark/${book}`);
    mkdirSync(outDir, { recursive: true });
    const mdFile = join(outDir, `${book}-${ch2}-scorecard.md`);
    const jsonFile = join(outDir, `${book}-${ch2}-scorecard.json`);
    writeFileSync(mdFile, renderMarkdown(scorecard));
    const { verses: _u, ...ultSlim } = scorecard.ult || {};
    const { verses: _s, ...ustSlim } = scorecard.ust || {};
    writeFileSync(jsonFile, JSON.stringify({ ...scorecard, ult: scorecard.ult ? ultSlim : undefined, ust: scorecard.ust ? ustSlim : undefined }, null, 2));
    console.log(renderMarkdown(scorecard));
    console.error(`Wrote ${mdFile} and ${jsonFile}`);
  }
}

import { pathToFileURL } from 'url';
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
