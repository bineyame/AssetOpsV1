/**
 * POLISH PB-0: the client-vocabulary scan of tools/demo-combined-evidence.mjs, kept pure so guard 12 can test it
 * (tools/checks/test_mock_deviation_labels.mjs). Region rules (build sheet Addendum 5, correcting §5 PB-0 and Addendum 1):
 *   - id kinds (UUID, `Finding <8 hex>`, zero-padded record code, UPPER_SNAKE enum code, raw ISO timestamp) run on all
 *     visible <main> text; only `[data-technical-details]` hides them, for the strict and the `-open` capture alike;
 *   - `[data-vocabulary-exempt]` exempts only the product kinds (T028/w1 terms, Lab names, developer words);
 *   - `[data-time-zone-note]` exempts only `\bUTC\b`;
 *   - "MOCK DEVIATION" is never exempt and is scanned on the full <main> text;
 *   - every hit inside an exempt or Technical-details region is recorded in `exempt_hits` (never counted).
 */
import { readFileSync } from "node:fs";

/** Identifier kinds: exempt only inside Technical details. */
export const ID_KINDS = [
  ["enum code", /\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b/g],
  ["zero-padded record code", /\b(?:ACT|INC|WR|F|PLAN|CHG|PM|REC)-0{3,}\d+\b/g],
  ["uuid", /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/gi],
  ["raw timestamp", /\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?Z?\b/g],
  ["finding id label", /\bFinding [0-9a-f]{8}\b/g],
];
/** The time-zone suffix: exempt inside a time-zone note (and Technical details). */
export const UTC_KIND = [["time zone suffix", /\bUTC\b/g]];
/** Developer words and Lab names: exempt inside `[data-vocabulary-exempt]` (and Technical details). */
export const WORD_KINDS = [
  ["service actor", /\bservice:[\w-]+/g],
  ["register or slice id", /\b(?:R\d{3}|OUT-[A-E]\d?|S\d-\d\d[a-z]?|W\d-\d\d[a-z]?|DD-\d\d|CO-\d+)\b/g],
  ["dev term", /\b(?:producer|projection|fixture|payload|schema|cursor|known_at|seed|epoch|adapter|endpoint|analytic_id|null|undefined|NaN|TODO|debug|mock|scenario_id|revision_id|basis_ref|v\d+ manifest)\b/gi],
  ["lab name", /\b(?:replay|charging) lab\b/gi],
  ["snake_case name", /\b[a-z]+(?:_[a-z]+)+\b/g],
  // POLISH Addendum 14: the client term is "example data"; a recurrence of "test data" fails the strict gate.
  ["test data wording", /\btest data\b/gi],
];
/** Never exempt. */
export const LABEL_KIND = [["mock deviation label", /\bMOCK DEVIATION\b/g]];

/**
 * The product's own lists (frontend/src/test/productVocabulary.json): the T028 `terms` and `w1.terms`, word-bounded
 * and case-insensitive (Addendum 1 M3: `w1.codes` are left to the code regexes). Allowed glosses are stripped first,
 * from the same file only: the global `glosses` and `w1.glosses`. No tool-local allow-list.
 */
const PRODUCT_VOCAB = JSON.parse(readFileSync(new URL("../frontend/src/test/productVocabulary.json", import.meta.url), "utf-8"));
const esc = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const termRe = (phrase) => new RegExp(`(?<![\\p{L}\\p{N}])${esc(phrase).replace(/ /g, "\\s+")}(?![\\p{L}\\p{N}])`, "giu");
export const GLOSSES = [...PRODUCT_VOCAB.glosses, ...PRODUCT_VOCAB.w1.glosses].map((g) => g.text);
const GLOSS_RES = GLOSSES.map((t) => new RegExp(esc(t), "giu"));
export const TERMS = [
  ...PRODUCT_VOCAB.terms.map((t) => [`product term (T028): ${t.phrase}`, termRe(t.phrase)]),
  ...PRODUCT_VOCAB.w1.terms.map((t) => [`product term (w1): ${t.phrase}`, termRe(t.phrase)]),
];

/** Unique `kind|match` hits of `list` in `text`, each with 50 characters of context either side. */
export function scan(text, list) {
  const hits = [];
  const seen = new Set();
  for (const [name, re] of list) {
    for (const m of (text ?? "").matchAll(re)) {
      const k = `${name}|${m[0]}`;
      if (seen.has(k)) continue;
      seen.add(k);
      const at = m.index ?? 0;
      hits.push({ kind: name, match: m[0], context: text.slice(Math.max(0, at - 50), at + m[0].length + 50).replace(/\s+/g, " ").trim() });
    }
  }
  return hits;
}

/** Product kinds: developer words and Lab names, then the product terms after the file's own glosses. */
function scanProduct(text) {
  let glossFree = text ?? "";
  for (const re of GLOSS_RES) glossFree = glossFree.replace(re, " ");
  return [...scan(text, WORD_KINDS), ...scan(glossFree, TERMS)];
}

/** The kinds each region exempts. */
const REGION_SCAN = {
  "data-technical-details": (t) => [...scan(t, ID_KINDS), ...scan(t, UTC_KIND), ...scanProduct(t)],
  "data-vocabulary-exempt": (t) => scanProduct(t),
  "data-time-zone-note": (t) => scan(t, UTC_KIND),
};

/**
 * Classifies one capture's texts (from `CAPTURE_TEXTS`):
 *   full: all visible <main> text; ids: Technical details removed; utc: Technical details and time-zone notes removed;
 *   words: Technical details and vocabulary-exempt regions removed (a time-zone note exempts only UTC);
 *   regions: [{ attr, value, text }] for each rendered exempt region (one inside Technical details, or inside a region
 *   of its own kind, is covered by that outer region).
 * Returns `vocabulary` (hits that count, MOCK DEVIATION included), `exempt_hits` and `counted`. The `-open` capture
 * counts only ids and MOCK DEVIATION; review mode records MOCK DEVIATION without counting it.
 */
export function classifyCapture({ full, ids, utc, words, regions = [] }, { open = false, reviewLabels = false } = {}) {
  const idHits = scan(ids, ID_KINDS);
  const rest = open ? [] : [...scan(utc, UTC_KIND), ...scanProduct(words)];
  const labels = scan(full, LABEL_KIND);
  const exempt_hits = [];
  for (const r of regions) {
    const fn = REGION_SCAN[r.attr];
    if (!fn) continue;
    for (const h of fn(r.text)) exempt_hits.push({ kind: h.kind, match: h.match, region: `${r.attr}=${r.value ?? ""}`, context: h.context });
  }
  const vocabulary = [...idHits, ...rest, ...labels];
  const counted = idHits.length + rest.length + (reviewLabels ? 0 : labels.length);
  return { vocabulary, exempt_hits, counted };
}

/** In-page: the texts `classifyCapture` takes. Regions are hidden with display:none for one read each, then restored. */
export const CAPTURE_TEXTS = `(()=>{const m=document.querySelector('main')||document.body;
 const read=(sel)=>{const ex=sel?[...m.querySelectorAll(sel)]:[];
   const prev=ex.map(e=>[e.style.getPropertyValue('display'),e.style.getPropertyPriority('display')]);
   for(const e of ex)e.style.setProperty('display','none','important');
   const t=m.innerText;
   ex.forEach((e,i)=>{const [v,p]=prev[i];if(v)e.style.setProperty('display',v,p);else e.style.removeProperty('display');});
   return t;};
 const TD='[data-technical-details]',TZ='[data-time-zone-note]',VX='[data-vocabulary-exempt]';
 const regions=[];
 for(const [attr,sel] of [['data-technical-details',TD],['data-vocabulary-exempt',VX],['data-time-zone-note',TZ]]){
   for(const e of m.querySelectorAll(sel)){
     const outer=e.parentElement&&e.parentElement.closest(attr==='data-technical-details'?TD:TD+','+sel);
     if(outer&&m.contains(outer))continue;
     if(!e.getClientRects().length)continue;
     regions.push({attr,value:e.getAttribute(attr),text:e.innerText});}}
 return {full:read(''),ids:read(TD),utc:read(TD+','+TZ),words:read(TD+','+VX),regions};})()`;
