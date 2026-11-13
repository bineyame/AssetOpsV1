// Style ratchet (UQ-FI-1, D-UQFI.3; architect-sequence-client-scope-2026-11-11.md revision 6, 6.3).
//
// Same contract and shape as frontend-hardwiring.mjs. Counts, per source file under frontend/src
// (*.css and *.tsx; tests, ui/tokens.css and ui/fonts.css excluded):
//   rawFontSize    a font-size (or `font:` shorthand size) that is not var(--text-*), var(--font-size-*),
//                  inherit, 1em or 100%; plus every inline `fontSize` in TSX
//   rawFontFamily  a font-family (or `font:` shorthand family) that is not var(--font-*) or inherit;
//                  plus every inline `fontFamily` in TSX
//   rawHex         a hex colour literal
// and compares them with tools/checks/fixtures/style-ratchet-baseline.json. Any cell above its baseline
// fails; a file outside the baseline counts from 0. The baseline changes only by `--shrink` (refused while
// any cell has risen; it never raises a cell or adds a file).
//
// The wall (not a ratchet; the whole tree, tokens.css included): any font-size that resolves below 12px
// fails, through var() chains, rem (16px root) and px; a relative em/% size under 1em/100% fails too.
//
// After a merge that adds CSS: `node tools/uqfi-type-codemod.mjs`, then this guard.
// Run: node tools/checks/style-ratchet.mjs [--shrink | --print]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const SCAN_ROOT = 'frontend/src';
export const BASELINE_PATH = 'tools/checks/fixtures/style-ratchet-baseline.json';
export const CELLS = ['rawFontSize', 'rawFontFamily', 'rawHex'];
const TOKEN_FILES = new Set(['ui/tokens.css', 'ui/fonts.css']);
const FLOOR_PX = 12;

export function isStyleSource(rel) {
  if (!/\.(css|tsx)$/.test(rel)) return false;
  if (/(^|\/)__tests__\//.test(rel) || /\.test\.tsx$/.test(rel) || /(^|\/)test\//.test(rel)) return false;
  return !TOKEN_FILES.has(rel);
}

const ALLOWED_SIZE = /^(?:var\(\s*--(?:text|font-size)-[\w-]+\s*\)|inherit|1em|100%)$/;
const ALLOWED_FAMILY = /^(?:var\(\s*--font-[\w-]+\s*\)|inherit)$/;
const SIZE_DECL = /\bfont-size\s*:\s*([^;}]+?)\s*(?:!important\s*)?(?=[;}])/g;
const FAMILY_DECL = /\bfont-family\s*:\s*([^;}]+?)\s*(?=[;}])/g;
const FONT_SHORTHAND = /(?<![\w-])font\s*:\s*(?!inherit\b)(?:(?:italic|oblique|normal|bold|bolder|lighter|small-caps|\d{3})\s+)*(\S+?)(?:\s*\/\s*[\d.]+)?\s+([^;}]+?)\s*(?=[;}])/g;
const HEX = /(?<![\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![\w-])/g;

export function countText(rel, text) {
  const out = {};
  const add = (k, n = 1) => { if (n) out[k] = (out[k] || 0) + n; };
  if (rel.endsWith('.css')) {
    for (const m of text.matchAll(SIZE_DECL)) if (!ALLOWED_SIZE.test(m[1].trim())) add('rawFontSize');
    for (const m of text.matchAll(FAMILY_DECL)) if (!ALLOWED_FAMILY.test(m[1].trim())) add('rawFontFamily');
    for (const m of text.matchAll(FONT_SHORTHAND)) {
      if (!ALLOWED_SIZE.test(m[1].trim())) add('rawFontSize');
      if (!ALLOWED_FAMILY.test(m[2].trim())) add('rawFontFamily');
    }
  } else {
    add('rawFontSize', (text.match(/\bfontSize\s*[:=]/g) || []).length + (text.match(/\bfont-size\s*=/g) || []).length);
    add('rawFontFamily', (text.match(/\bfontFamily\s*[:=]/g) || []).length);
  }
  add('rawHex', (text.match(HEX) || []).length);
  return out;
}

function walk(dir, base, acc) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, base, acc);
    else acc.push(path.relative(base, full).split(path.sep).join('/'));
  }
  return acc;
}

export function scan(root = path.join(repoRoot, SCAN_ROOT)) {
  const counts = {};
  for (const rel of walk(root, root, []).sort()) {
    if (!isStyleSource(rel)) continue;
    const c = countText(rel, fs.readFileSync(path.join(root, rel), 'utf8'));
    if (Object.keys(c).length) counts[rel] = c;
  }
  return counts;
}

/** Every custom property definition in a stylesheet: name -> [values] (media overrides included). */
export function customProperties(text) {
  const map = new Map();
  for (const m of text.matchAll(/(--[\w-]+)\s*:\s*([^;}]+?)\s*(?=[;}])/g)) {
    if (!map.has(m[1])) map.set(m[1], []);
    map.get(m[1]).push(m[2]);
  }
  return map;
}

/** The px sizes a font-size value can resolve to (16px root, 14px body for em/%), or a reason it cannot. */
export function resolvePx(value, props, seen = new Set()) {
  const v = value.trim();
  if (v === 'inherit' || v === '1em' || v === '100%') return [];
  const varMatch = /^var\(\s*(--[\w-]+)\s*(?:,\s*(.+))?\)$/.exec(v);
  if (varMatch) {
    const [, name, fallback] = varMatch;
    if (seen.has(name)) return [];
    const defs = props.get(name);
    if (!defs) return fallback ? resolvePx(fallback, props, seen) : [`undefined ${name}`];
    return defs.flatMap((d) => resolvePx(d, props, new Set([...seen, name])));
  }
  let m;
  if ((m = /^([\d.]+)px$/.exec(v))) return [Number(m[1])];
  if ((m = /^([\d.]+)rem$/.exec(v))) return [Number(m[1]) * 16];
  if ((m = /^([\d.]+)em$/.exec(v))) return [Number(m[1]) < 1 ? `relative ${v}` : FLOOR_PX];
  if ((m = /^([\d.]+)%$/.exec(v))) return [Number(m[1]) < 100 ? `relative ${v}` : FLOOR_PX];
  return [`unresolved ${v}`];
}

/** The 12px wall over the whole tree: [{file, value, why}]. */
export function wall(root = path.join(repoRoot, SCAN_ROOT)) {
  const files = walk(root, root, []).filter((r) => r.endsWith('.css') && !/__tests__/.test(r)).sort();
  const props = new Map();
  for (const rel of files) {
    for (const [k, vals] of customProperties(fs.readFileSync(path.join(root, rel), 'utf8'))) {
      props.set(k, [...(props.get(k) || []), ...vals]);
    }
  }
  return wallFor(files.map((rel) => [rel, fs.readFileSync(path.join(root, rel), 'utf8')]), props);
}

export function wallFor(entries, props) {
  const bad = [];
  const check = (file, value) => {
    for (const r of resolvePx(value, props)) {
      if (typeof r === 'string') bad.push({ file, value: value.trim(), why: r });
      else if (r < FLOOR_PX) bad.push({ file, value: value.trim(), why: `${r}px < ${FLOOR_PX}px` });
    }
  };
  for (const [rel, text] of entries) {
    for (const m of text.matchAll(SIZE_DECL)) check(rel, m[1]);
    for (const m of text.matchAll(FONT_SHORTHAND)) check(rel, m[1]);
    for (const m of text.matchAll(/(--(?:text|font-size)-[\w-]+)\s*:\s*([^;}]+?)\s*(?=[;}])/g)) {
      if (/^--text-(?:primary|secondary|muted|on|inverse|link|danger|warning|success|accent|strong|subtle)/.test(m[1])) continue;
      if (/^#|rgb|hsl/.test(m[2].trim())) continue; // a colour token, not a size
      check(rel, m[2]);
    }
  }
  return bad;
}

export function compare(baselineFiles, current) {
  const rises = [];
  const shrinks = [];
  const files = new Set([...Object.keys(baselineFiles), ...Object.keys(current)]);
  for (const rel of [...files].sort()) {
    const base = baselineFiles[rel] || {};
    const now = current[rel] || {};
    for (const p of CELLS) {
      const b = base[p] || 0;
      const n = now[p] || 0;
      if (n > b) rises.push({ file: rel, cell: p, base: b, now: n });
      else if (n < b) shrinks.push({ file: rel, cell: p, base: b, now: n });
    }
  }
  return { rises, shrinks };
}

export function shrink(baselineFiles, current) {
  const { rises } = compare(baselineFiles, current);
  if (rises.length) throw new Error(`--shrink refused: ${rises.length} cell(s) rose; fix them first`);
  const out = {};
  for (const rel of Object.keys(baselineFiles).sort()) {
    const cells = {};
    for (const [p, b] of Object.entries(baselineFiles[rel])) {
      const n = Math.min(b, (current[rel] || {})[p] || 0);
      if (n) cells[p] = n;
    }
    if (Object.keys(cells).length) out[rel] = cells;
  }
  return out;
}

export function totals(files) {
  const t = {};
  for (const cells of Object.values(files)) for (const [p, n] of Object.entries(cells)) t[p] = (t[p] || 0) + n;
  return t;
}

export function readBaseline(file = path.join(repoRoot, BASELINE_PATH)) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const current = scan();
  if (args.includes('--print')) {
    console.log(JSON.stringify({ files: current, totals: totals(current) }, null, 1));
    process.exit(0);
  }
  const doc = readBaseline();
  if (args.includes('--shrink')) {
    try {
      const files = shrink(doc.files, current);
      fs.writeFileSync(path.join(repoRoot, BASELINE_PATH), JSON.stringify({ ...doc, files, totals: totals(files) }, null, 1) + '\n');
      console.log(`baseline shrunk: totals ${JSON.stringify(totals(files))}`);
      process.exit(0);
    } catch (err) {
      console.log(err.message);
      process.exit(1);
    }
  }
  const { rises, shrinks } = compare(doc.files, current);
  const walled = wall();
  for (const w of walled) console.log(`FAIL ${SCAN_ROOT}/${w.file}: font-size ${w.value} (${w.why}; the floor is ${FLOOR_PX}px)`);
  for (const r of rises) console.log(`FAIL ${SCAN_ROOT}/${r.file}: ${r.cell} ${r.base} -> ${r.now} (the ratchet only shrinks; run tools/uqfi-type-codemod.mjs for font sizes)`);
  for (const s of shrinks) console.log(`note ${SCAN_ROOT}/${s.file}: ${s.cell} ${s.base} -> ${s.now} (run --shrink)`);
  if (rises.length || walled.length) {
    console.log(`Style ratchet failed: ${rises.length} rise(s), ${walled.length} size(s) under ${FLOOR_PX}px.`);
    process.exit(1);
  }
  console.log(`Style ratchet passed: totals ${JSON.stringify(totals(current))}` + (shrinks.length ? `; ${shrinks.length} cell(s) can shrink` : ''));
}
