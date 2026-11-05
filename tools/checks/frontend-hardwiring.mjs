// Frontend hard-wiring ratchet (CH-5b1, build sheet CH-5b R7; design §13 AG-31; CH5b1-R Q7).
//
// Counts, per product source file under frontend/src (tests, test helpers, F/blocks/vocabulary* and
// F/views/registry.ts excluded), the §13 hard-wiring patterns:
//   cmp   site_type / siteType === or !== against a string literal or a *SITE_TYPE constant (not typeof)
//   lit   a quoted Site-type value (MINIGRID, COLDCHAIN, EV_CHARGING)
//   code  a Site code (KOBO-001, COLD-LAB-001, EV-LAB-001 shapes)
//   oid   an outcome-id literal (MG-n, CC-n, EV-n)
//   api   a quoted /api string in a .tsx component
//   href  href= / to= bound directly to a server field (x.href, x.url, x.link, x.links.y)
// and compares them with tools/checks/fixtures/frontend-hardwiring-baseline.json. A ratchet, not a wall: any cell
// above its baseline fails, a file outside the baseline counts from 0 (a rename is a new file), and no file under
// F/blocks/ may have a baseline row. The baseline changes only by `--shrink` (refused while any cell has risen; it
// never raises a cell or adds a file) or by a hand-moved row for a rename with equal counts, in a reviewed diff.
// CH-10a turns this into the full guard.
//
// Run: node tools/checks/frontend-hardwiring.mjs [--shrink | --print]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const SCAN_ROOT = 'frontend/src';
export const BASELINE_PATH = 'tools/checks/fixtures/frontend-hardwiring-baseline.json';

export const PATTERNS = {
  cmp: /(?<!typeof\s+[\w.?!]*)\b(?:site_type|siteType)\s*[!=]==\s*(?:["'`]|[A-Z_]*SITE_TYPE\b)/g,
  lit: /["'`](?:MINIGRID|COLDCHAIN|EV_CHARGING)["'`]/g,
  code: /\b(?:KOBO|COLD-LAB|EV-LAB)-\d{3}\b/g,
  oid: /\b(?:MG|CC|EV)-\d\b/g,
  api: /["'`]\/api[/"'`]/g,
  href: /\b(?:href|to)=\{\s*[\w?.!]+\.(?:href|url|link|links\??\.\w+)\s*\}/g,
};
const TSX_ONLY = new Set(['api']);

export function isProductSource(rel) {
  if (!/\.(ts|tsx)$/.test(rel)) return false;
  if (/(^|\/)__tests__\//.test(rel) || /\.test\.[jt]sx?$/.test(rel) || /(^|\/)test\//.test(rel)) return false;
  if (/^blocks\/vocabulary/.test(rel) || rel === 'views/registry.ts') return false;
  return true;
}

export function countText(rel, text) {
  const out = {};
  for (const [name, re] of Object.entries(PATTERNS)) {
    if (TSX_ONLY.has(name) && !rel.endsWith('.tsx')) continue;
    const n = (text.match(re) || []).length;
    if (n) out[name] = n;
  }
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

/** {relPath: {pattern: count}} with zero cells and zero files left out. */
export function scan(root = path.join(repoRoot, SCAN_ROOT)) {
  const counts = {};
  for (const rel of walk(root, root, []).sort()) {
    if (!isProductSource(rel)) continue;
    const c = countText(rel, fs.readFileSync(path.join(root, rel), 'utf8'));
    if (Object.keys(c).length) counts[rel] = c;
  }
  return counts;
}

/** rises: cells above baseline (a file outside the baseline counts from 0); shrinks: cells below it. */
export function compare(baselineFiles, current) {
  const rises = [];
  const shrinks = [];
  const problems = [];
  for (const rel of Object.keys(baselineFiles)) {
    if (rel.startsWith('blocks/')) problems.push(`${rel}: F/blocks/ files must have 0 and no baseline row`);
  }
  const files = new Set([...Object.keys(baselineFiles), ...Object.keys(current)]);
  for (const rel of [...files].sort()) {
    const base = baselineFiles[rel] || {};
    const now = current[rel] || {};
    for (const p of Object.keys(PATTERNS)) {
      const b = base[p] || 0;
      const n = now[p] || 0;
      if (n > b) rises.push({ file: rel, pattern: p, base: b, now: n });
      else if (n < b) shrinks.push({ file: rel, pattern: p, base: b, now: n });
    }
  }
  return { rises, shrinks, problems };
}

/** The shrunk baseline files: min(old, now) per cell, zero cells and files dropped. Throws on any rise. */
export function shrink(baselineFiles, current) {
  const { rises, problems } = compare(baselineFiles, current);
  if (rises.length || problems.length) {
    throw new Error(`--shrink refused: ${rises.length} cell(s) rose, ${problems.length} problem(s); fix them first`);
  }
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

export function readBaseline(file = path.join(repoRoot, BASELINE_PATH)) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function writeBaseline(doc, file = path.join(repoRoot, BASELINE_PATH)) {
  fs.writeFileSync(file, JSON.stringify(doc, null, 1) + '\n');
}

export function totals(files) {
  const t = {};
  for (const cells of Object.values(files)) for (const [p, n] of Object.entries(cells)) t[p] = (t[p] || 0) + n;
  return t;
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
      writeBaseline({ ...doc, files, totals: totals(files) });
      console.log(`baseline shrunk: totals ${JSON.stringify(totals(files))}`);
      process.exit(0);
    } catch (err) {
      console.log(err.message);
      process.exit(1);
    }
  }
  const { rises, shrinks, problems } = compare(doc.files, current);
  for (const p of problems) console.log(`FAIL ${p}`);
  for (const r of rises) console.log(`FAIL ${SCAN_ROOT}/${r.file}: ${r.pattern} ${r.base} -> ${r.now} (the ratchet only shrinks)`);
  for (const s of shrinks) console.log(`note ${SCAN_ROOT}/${s.file}: ${s.pattern} ${s.base} -> ${s.now} (run --shrink)`);
  if (rises.length || problems.length) {
    console.log(`Frontend hard-wiring ratchet failed: ${rises.length} rise(s), ${problems.length} problem(s).`);
    process.exit(1);
  }
  console.log(`Frontend hard-wiring ratchet passed: totals ${JSON.stringify(totals(current))}` +
    (shrinks.length ? `; ${shrinks.length} cell(s) can shrink` : ''));
}
