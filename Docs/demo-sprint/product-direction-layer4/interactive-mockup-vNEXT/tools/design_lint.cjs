/* Design lint (UI/UX guide Docs/design-system/uiux-guide.md §10.2, gate G2). Two parts:
   1. Static, over the built index.html and the files written under the guide:
      - every px font size in the bundled CSS is a step of the guide's scale (12, 13, 14, 16, 20, 24, 32), none under 12 px;
      - no colour literal (#hex, rgb(), hsl()) in ux.css, loop-ux.js or theme.css outside the token blocks (:root, dark blocks)
        and outside attribute selectors that re-point an earlier sheet's literal ([style*="#..."]);
      - no inline style colour in the loop-*.js templates.
      Reported, not failing (known residual, wave 2): colour literals in economics.css, mockups.css, portfolio.css and
      outcomes.css, which theme.css re-points at tokens.
   2. Rendered (needs /opt/assetecon/tools/pw/env.sh sourced): for each wave-1 route at 1440 x 900, light and dark, every
      visible text element's computed font size is on the scale and at least 12 px; no page-level horizontal scroll.
   Run: node tools/design_lint.cjs [--static]        Plant test: LINT_PLANT=1 node tools/design_lint.cjs (must fail). */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..'), read = f => fs.readFileSync(path.join(root, f), 'utf8');
const SCALE = [12, 13, 14, 16, 20, 24, 32], PLANT = !!process.env.LINT_PLANT, fails = [], notes = [];
const ROUTES = ['portfolio', 'portfolio/act-first', 'portfolio/act-first/plan', 'decision/kobo-generator', 'site/kobo'];
let html = read('index.html');
if (PLANT) html = html.replace('</style>', '.ux-headline{font-size:11px!important}</style>');
const css = (html.match(/<style>([\s\S]*?)<\/style>/) || ['', ''])[1];
for (const m of css.matchAll(/font(?:-size)?:\s*(?:\d{3}\s+)?([\d.]+)px/g)) if (!SCALE.includes(+m[1])) fails.push(`bundled CSS: font size ${m[1]}px is not on the scale`);
const stripTokens = t => t.replace(/:root(?:\[[^\]]+\]|:not\(\[[^\]]+\]\))*\s*\{[^}]*\}/g, '').replace(/\[style\*="[^"]*"\]/g, ''); /* token blocks, including brand packs ([data-brand]) */
const COLOR = /#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(/g;
const owned = { 'ux.css': read('ux.css') + (PLANT ? '\n.lint-plant{color:#123456}' : ''), 'loop-ux.js': read('loop-ux.js'), 'theme.css': read('theme.css'), 'brand.css': read('brand.css') };
for (const [f, t] of Object.entries(owned)) { const n = (stripTokens(t).match(COLOR) || []).length; if (n) fails.push(`${f}: ${n} colour literal(s) outside the token blocks`); }
for (const f of fs.readdirSync(root).filter(f => /^loop-.*\.js$/.test(f))) { const n = (read(f).match(/style="[^"]*(?:#[0-9a-fA-F]{3,8}|rgba?\(|color:)[^"]*"/g) || []).length; if (n) fails.push(`${f}: ${n} inline style colour(s)`); }
/* a figure's period or meaning is read from the data (optEffect's second part), never typed in the page code (REVIEW-decision-page H1) */
{ const t = owned['loop-ux.js'] + (PLANT ? "\nconst p = 'over 12 months against doing nothing';" : ''), m = t.match(/over 12 months|12 months against/g); if (m) fails.push(`loop-ux.js: ${m.length} figure period(s) typed by hand ("${m[0]}"); read it from optEffect`); }
/* the comparator of a figure is its basis (D-RECON.6, review r2 H1): no typed "against no action / doing nothing" in page code
   outside the basis table (loop-decisions.js BASIS_*) and comments */
for (const f of fs.readdirSync(root).filter(f => /^loop-.*\.js$/.test(f))) { const src = read(f).replace(/\/\*[\s\S]*?\*\//g, '').split('\n').filter(l => !/^\s*const BASIS_|^\s*\/\//.test(l)).join('\n') + (PLANT && f === 'loop-site.js' ? "\nconst x = 'Each option valued against no action';" : '');
  const m = src.match(/(?:against|compared? with|than) (?:no action|doing nothing)/gi); /* r3 L8: any typed comparator */ if (m) fails.push(`${f}: ${m.length} comparator(s) typed by hand ("${m[0]}"); read it from the basis`); }
/* no dead declaration: the same property for the same selector list under the same condition, declared twice, leaves the earlier one dead (REVIEW-decision-page L1) */
function deadDecls(css) {
  const t = css.replace(/\/\*[\s\S]*?\*\//g, ''), seen = new Map(), dead = [];
  const block = (ctx, txt) => { for (const m of txt.matchAll(/([^{}]+)\{([^{}]*)\}/g)) { const sel = m[1].trim().split(',').map(s => s.trim().replace(/\s+/g, ' ')).sort().join(','); for (const d of m[2].split(';')) { const k = d.split(':')[0].trim(); if (!k || !d.includes(':')) continue; const key = `${ctx}|${sel}|${k}`, imp = /!important/.test(d); if (seen.has(key) && !(seen.get(key) && !imp)) dead.push(key); seen.set(key, imp); } } };
  let top = ''; for (let j = 0; j < t.length; j++) { if (t[j] === '@') { const o = t.indexOf('{', j), at = t.slice(j, o).trim(); let d = 1, k = o + 1; while (d && k < t.length) { if (t[k] === '{') d++; else if (t[k] === '}') d--; k++; } if (/^@(media|container|supports)/.test(at)) block(at.replace(/\s+/g, ' '), t.slice(o + 1, k - 1)); else top += t.slice(j, k); j = k - 1; continue; } top += t[j]; }
  block('', top); return dead;
}
for (const f of ['ux.css', 'brand.css', 'theme.css']) { const dd = deadDecls(owned[f] + (PLANT && f === 'ux.css' ? '\n.lint-plant{gap:4px}\n.lint-plant{gap:8px}' : '')); if (dd.length) fails.push(`${f}: ${dd.length} dead declaration(s), overridden later in the file (${dd.slice(0, 3).join('; ')})`); }
for (const f of ['economics.css', 'mockups.css', 'portfolio.css', 'outcomes.css']) notes.push(`${f}: ${(read(f).match(COLOR) || []).length} colour literals, re-pointed by theme.css (residual, not failing)`);
async function rendered() {
  const { chromium } = require(process.env.PW);
  const tmp = path.join(root, 'tools', '.lint-index.html'); fs.writeFileSync(tmp, html);
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  for (const dark of [false, true]) for (const r of ROUTES) {
    const p = await b.newPage({ viewport: { width: 1440, height: 900 }, colorScheme: dark ? 'dark' : 'light' });
    await p.goto('file://' + tmp + '#/' + r); await p.waitForTimeout(500);
    const res = await p.evaluate(scale => {
      const bad = {}; let n = 0;
      for (const e of document.querySelectorAll('#app *')) {
        if (e.closest('.reviewbar') || e.offsetParent === null) continue;
        if (![...e.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) continue;
        const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || (e.closest('.vh,.sr-only'))) continue;
        const r = e.getBoundingClientRect(); if (r.width <= 1 && r.height <= 1) continue;
        const fs = Math.round(parseFloat(cs.fontSize) * 10) / 10; n++;
        if (fs < 12 || !scale.includes(fs)) bad[fs] = (bad[fs] || 0) + 1;
      }
      return { n, bad, overflow: document.documentElement.scrollWidth > innerWidth };
    }, SCALE);
    const k = `${r}${dark ? ' dark' : ''}`;
    if (Object.keys(res.bad).length) fails.push(`${k}: text off the scale or under 12 px ${JSON.stringify(res.bad)} (of ${res.n})`);
    if (res.overflow) fails.push(`${k}: page scrolls horizontally`);
    await p.close();
  }
  await b.close(); fs.unlinkSync(tmp);
}
(async () => {
  if (!process.argv.includes('--static') && process.env.PW) await rendered(); else notes.push('rendered part not run (no --static omitted, or PW not set)');
  console.log(JSON.stringify({ planted: PLANT, fails, notes }, null, 1));
  process.exit(fails.length ? 1 : 0);
})();
