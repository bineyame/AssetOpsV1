// UQ-FI-1 type codemod (D-UQFI.2, architect-sequence-client-scope-2026-11-11.md revision 6, 6.3).
//
// Committed and idempotent: any branch that merges after UQ-FI reruns it, then passes the style
// ratchet (tools/checks/style-ratchet.mjs). Over frontend/src/**/*.css except ui/tokens.css and
// ui/fonts.css it moves every font-size onto the 8-step scale (or keeps a role token), turns the
// monospace literals into var(--font-mono), and drops fallbacks inside var(). A value it cannot map
// is printed and fails the run: map it by the nearest-step rule (ties go up) and add it below.
//
// With --spacing it also snaps padding, margin and gap px values in the demo-path CSS files
// (DEMO_PATH_CSS) to the nearest --space-* step, ties down; 0, 1px, 2px, >64px, negative and calc() values stay.
//
// Run: node tools/uqfi-type-codemod.mjs [--spacing] [--check]
//   --check  rewrites nothing; exits 1 if any file would change (used after a merge).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(repoRoot, 'frontend/src');
export const EXCLUDED = new Set(['ui/tokens.css', 'ui/fonts.css']);

// The CSS files the P1-P8 demo-path frames load (rev 6 table 6.1), page-specific only.
// ui/primitives.css is shared by every page and keeps its spacing for 17 Nov.
export const DEMO_PATH_CSS = [
  'estate/estatePortfolio.css', 'estate/estate.css', 'sites/outcomes.css', 'blocks/blocks.css',
  'sites/w1ux02-site.css', 'sites/w2-cold-site.css', 'sites/w2-ev-site.css', 'sites/w4-mini-performance.css',
  'sites/w4-mini-decisions.css', 'sites/w1ux02-finding.css', 'sites/w1ux02-findings-index.css',
  'sites/w1f4-verification.css', 'work/globalWork.css', 'sites/periodStrip.css',
];

const STEP_BY_PX = new Map([
  [13, 200], [14, 300], [15, 400], [16, 400], [17, 500], [18, 500], [19, 500],
  [20, 600], [21, 600], [22, 600], [23, 700], [24, 700], [25, 700], [26, 700], [27, 700], [30, 800],
]);
const STEP_BY_LITERAL = new Map([
  ['0.75rem', 100], ['0.8125rem', 200], ['0.875rem', 300], ['1rem', 400],
  // Added by the builder (nearest step on the 14px body, ties up): 0.85em = 11.9px.
  ['0.85em', 100],
]);
const KEEP = new Set(['inherit', '1em', '100%']);

function roleTokens() {
  const text = fs.readFileSync(path.join(SRC, 'ui/tokens.css'), 'utf8');
  return new Set([...text.matchAll(/(--(?:text|font-size)-[\w-]+)\s*:/g)].map((m) => m[1]));
}

/** The scale variable for one font-size value, or null when it cannot be mapped. */
export function mapFontSize(raw, tokens = roleTokens()) {
  const v = raw.trim();
  if (KEEP.has(v)) return v;
  const varMatch = /^var\(\s*(--[\w-]+)\s*(?:,\s*(.+))?\)$/.exec(v);
  if (varMatch) {
    const [, name, fallback] = varMatch;
    if (name === '--font-size-sm') return 'var(--font-size-100)';
    if (/^--(?:text|font-size)-/.test(name) && tokens.has(name)) return `var(${name})`;
    return fallback ? mapFontSize(fallback, tokens) : null; // an undefined token: map its fallback
  }
  if (STEP_BY_LITERAL.has(v)) return `var(--font-size-${STEP_BY_LITERAL.get(v)})`;
  const px = /^(\d+(?:\.\d+)?)px$/.exec(v);
  if (px) {
    const n = Number(px[1]);
    if (n <= 12) return 'var(--font-size-100)';
    if (STEP_BY_PX.has(n)) return `var(--font-size-${STEP_BY_PX.get(n)})`;
  }
  return null;
}

const MONO = /(?:ui-monospace,\s*)?(?:SFMono-Regular,\s*)?(?:Menlo,\s*)?Consolas,\s*(?:"Courier New",\s*)?monospace|var\(--font-mono,[^)]*\)/g;

export function mapFontFamily(raw) {
  return raw.replace(MONO, 'var(--font-mono)').replace(/var\(--font-sans,[^)]*\)/g, 'var(--font-sans)');
}

/** Rewrites one stylesheet. Returns {text, sizes, families, unmapped}. */
export function rewriteType(text, tokens = roleTokens()) {
  let sizes = 0;
  let families = 0;
  const unmapped = [];
  let out = text.replace(/(font-size\s*:\s*)([^;}]+?)(\s*!important)?(\s*)(?=[;}])/g, (m, head, value, imp = '', ws) => {
    const mapped = mapFontSize(value, tokens);
    if (!mapped) { unmapped.push(value.trim()); return m; }
    if (mapped !== value.trim()) sizes += 1;
    return `${head}${mapped}${imp}${ws}`;
  });
  out = out.replace(/(font-family\s*:\s*)([^;}]+?)(?=\s*[;}])/g, (m, head, value) => {
    const mapped = mapFontFamily(value);
    if (mapped !== value) families += 1;
    return head + mapped;
  });
  // The `font:` shorthand: its size and its family, the same rules.
  out = out.replace(/(\bfont\s*:\s*)(?!inherit)(\S+)(\s*\/\s*[\d.]+\s+)([^;}]+?)(?=\s*[;}])/g, (m, head, size, lh, family) => {
    const mapped = mapFontSize(size, tokens);
    if (!mapped) { unmapped.push(size); return m; }
    const fam = mapFontFamily(family);
    if (mapped !== size) sizes += 1;
    if (fam !== family) families += 1;
    return `${head}${mapped}${lh}${fam}`;
  });
  return { text: out, sizes, families, unmapped };
}

const SPACE_STEPS = [4, 8, 12, 16, 20, 24, 32, 40, 48, 64];
const SPACE_NAME = { 4: 1, 8: 2, 12: 3, 16: 4, 20: 5, 24: 6, 32: 8, 40: 10, 48: 12, 64: 16 };

/** Nearest --space-* step for a px value, ties down; 0-2px hairlines and values above 64px stay. */
export function snapSpace(n) {
  if (n <= 2 || n > 64) return null;
  let best = SPACE_STEPS[0];
  for (const s of SPACE_STEPS) if (Math.abs(s - n) < Math.abs(best - n)) best = s;
  return `var(--space-${SPACE_NAME[best]})`;
}

/** Snaps padding / margin / gap px values (declarations only, not media queries). */
export function rewriteSpacing(text) {
  let changed = 0;
  const out = text.replace(
    /((?:^|[;{\s])(?:padding|margin|gap|row-gap|column-gap)(?:-(?:top|right|bottom|left|inline|block)(?:-(?:start|end))?)?\s*:\s*)([^;}]+?)(?=\s*[;}])/g,
    (m, head, value) => {
      if (/calc\(/.test(value)) return m;
      const v = value.replace(/(^|[\s(,])(\d+(?:\.\d+)?)px\b/g, (mm, pre, num) => {
        const snapped = snapSpace(Number(num));
        if (!snapped) return mm;
        changed += 1;
        return pre + snapped;
      });
      return head + v;
    },
  );
  return { text: out, changed };
}

function walk(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full, acc);
    else if (e.name.endsWith('.css')) acc.push(path.relative(SRC, full).split(path.sep).join('/'));
  }
  return acc;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const check = args.includes('--check');
  const spacing = args.includes('--spacing');
  const tokens = roleTokens();
  let failed = false;
  let wouldChange = 0;
  const rows = [];
  for (const rel of walk(SRC).sort()) {
    if (EXCLUDED.has(rel)) continue;
    const file = path.join(SRC, rel);
    const before = fs.readFileSync(file, 'utf8');
    const t = rewriteType(before, tokens);
    for (const u of t.unmapped) { console.log(`UNMAPPED ${rel}: font-size ${u}`); failed = true; }
    let text = t.text;
    let space = 0;
    if (spacing && DEMO_PATH_CSS.includes(rel)) ({ text, changed: space } = rewriteSpacing(text));
    if (text !== before) {
      wouldChange += 1;
      rows.push(`${rel}: font-size ${t.sizes}, font-family ${t.families}${spacing ? `, spacing ${space}` : ''}`);
      if (!check) fs.writeFileSync(file, text);
    }
  }
  for (const r of rows) console.log(r);
  if (failed) { console.log('codemod failed: unmapped values above'); process.exit(1); }
  if (check && wouldChange) { console.log(`codemod --check: ${wouldChange} file(s) would change`); process.exit(1); }
  console.log(`codemod ${check ? 'check' : 'done'}: ${wouldChange} file(s) ${check ? 'would change' : 'changed'}`);
}
