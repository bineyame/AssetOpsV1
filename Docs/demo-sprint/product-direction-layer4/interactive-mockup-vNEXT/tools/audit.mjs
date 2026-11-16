/* Scripted browser audit for the vNEXT mock-up. Usage (from the vNEXT folder):
   CHROME=/path/to/chrome PW=/path/to/playwright-core node tools/audit.mjs [--shots]
   Writes tools/audit-results.json, screen-manifest-vnext.json and (with --shots) screenshots/. */
import { createRequire } from 'node:module';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW);
const here = path.dirname(fileURLToPath(import.meta.url)), root = path.resolve(here, '..');
const url = pathToFileURL(path.join(root, 'index.html')).href;
const v70 = pathToFileURL(path.resolve(root, '../../../../frontend/mockups/v70/index.html')).href;
const shots = process.argv.includes('--shots');
const out = { routes: [], links: {}, overflow390: [], vocab: [], drawer: {}, focus: [], contrast: [], role: {}, budget: {}, errors: [] };
const browser = await chromium.launch({ executablePath: process.env.CHROME, args: ['--no-sandbox', '--disable-gpu'] });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await ctx.newPage();
let errs = [];
page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
page.on('pageerror', e => errs.push(String(e)));
await page.goto(url); await page.waitForFunction(() => window.mockupReady);
const manifest = await page.evaluate(() => window.mockupManifest);
writeFileSync(path.join(root, 'screen-manifest-vnext.json'), JSON.stringify(manifest, null, 1));
const ids = manifest.map(s => s.id), idset = new Set(ids);
const added = manifest.filter(s => s.vnext_status === 'Added').map(s => s.id), changed = manifest.filter(s => s.vnext_status === 'Changed').map(s => s.id);
if (shots) { mkdirSync(path.join(root, 'screenshots/vnext'), { recursive: true }); mkdirSync(path.join(root, 'screenshots/v70'), { recursive: true }); }
const CODE = /[<>]=|\bLOI\b|INV-MT|GEN-KS|BAT-0|CH-K2|\bP1\b|EV-L\d|MG-?L?\d|~\d|_[a-z]+_|\b(?:KOB|BAT|KIS|MTO|MWEA|THIKA|KIRI|EMB|KAS|RUI)-[A-Z0-9-]+\b|\bFinding\b|\bthread\b|CONTRIBUTIONS|overlap.group|ECONOMIC_ACTUAL|MODELLED\b|RECOMMENDED\b|REJECTED\b|NO_ACTION|undefined|NaN|\[object/;
for (const id of ids) {
  errs = [];
  await page.goto(url + '#/' + id); await page.waitForFunction(() => window.mockupReady);
  const r = await page.evaluate(() => ({ title: document.querySelector('h1')?.textContent, hrefs: [...document.querySelectorAll('a[href^="#/"]')].map(a => a.getAttribute('href').slice(2)), text: document.querySelector('.canvas')?.innerText || '' }));
  const bad = [...new Set(r.hrefs.filter(h => !idset.has(h)))];
  out.links[id] = bad;
  const st = manifest.find(s => s.id === id).vnext_status;
  if (st === 'Added') { const m = r.text.match(CODE); if (m) out.vocab.push({ id, match: m[0], at: r.text.slice(Math.max(0, m.index - 40), m.index + 40) }); }
  out.routes.push({ id, status: st, ok: !!r.title && errs.length === 0, h1: r.title, errors: errs.slice(0, 3), badLinks: bad });
  if (shots && (st === 'Added' || st === 'Changed')) await page.screenshot({ path: path.join(root, `screenshots/vnext/${id}-1440.png`), fullPage: true });
}
/* 390 px overflow for every route */
await page.setViewportSize({ width: 390, height: 844 });
for (const id of ids) {
  await page.goto(url + '#/' + id); await page.waitForFunction(() => window.mockupReady);
  const w = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, culprits: [...document.querySelectorAll('body *')].filter(e => { const b = e.getBoundingClientRect(); return b.right > document.documentElement.clientWidth + 1 && !e.closest('.table-wrap,.tabs,svg,pre,.d-scroll') && getComputedStyle(e).position !== 'fixed'; }).slice(0, 3).map(e => e.tagName + '.' + [...e.classList].join('.')) }));
  const st = manifest.find(s => s.id === id).vnext_status;
  if (w.sw > w.cw) out.overflow390.push({ id, status: st, scrollWidth: w.sw, culprits: w.culprits });
  if (shots && ['decide-lakeside', 'decide-harvest', 'decide-metro', 'choice-kobo-generator', 'choice-mto-inverter', 'choice-embakasi-schedule'].includes(id)) await page.screenshot({ path: path.join(root, `screenshots/vnext/${id}-390.png`), fullPage: true });
}
await page.setViewportSize({ width: 1440, height: 1000 });
/* role emphasis never changes numbers */
await page.goto(url + '#/decide-lakeside'); await page.waitForFunction(() => window.mockupReady);
const nums = async () => (await page.evaluate(() => (document.querySelector('.canvas').innerText.match(/[−+]?\$[\d,]+(?:\.\d\d)?/g) || []).sort().join('|')));
const base = await nums(); const roleRes = {};
for (const r of ['COO', 'CFO', 'CCO', 'CEO']) { await page.click(`[data-role="${r}"]`); roleRes[r] = { sameNumbers: (await nums()) === base, question: await page.textContent('.d-question p'), firstPanel: await page.evaluate(() => document.querySelector('.d-panels > .panel h2')?.textContent), focusRestored: await page.evaluate(r => document.activeElement?.dataset?.role === r, r) }; }
out.role = roleRes;
/* drawer: open from a money figure, focus inside, trap, Escape returns focus */
const trig = page.locator('.d-insight .d-money').first(); await trig.focus(); await page.keyboard.press('Enter');
await page.waitForSelector('.drawer');
const inDrawer = await page.evaluate(() => !!document.activeElement.closest('.drawer'));
let trapped = true; for (let i = 0; i < 25; i++) { await page.keyboard.press('Tab'); if (!(await page.evaluate(() => !!document.activeElement.closest('.drawer')))) trapped = false; }
for (let i = 0; i < 5; i++) { await page.keyboard.press('Shift+Tab'); if (!(await page.evaluate(() => !!document.activeElement.closest('.drawer')))) trapped = false; }
const drawerText = await page.textContent('.drawer');
if (shots) await page.screenshot({ path: path.join(root, 'screenshots/vnext/evidence-drawer-1440.png') });
await page.keyboard.press('Escape');
const closed = await page.evaluate(() => !document.querySelector('.drawer')), back = await page.evaluate(() => document.activeElement?.classList.contains('d-money'));
out.drawer = { openedWithKeyboard: true, focusInside: inDrawer, focusTrapped: trapped, escapeCloses: closed, focusReturned: back, hasProvenance: /Emulated source|Simulated demo data/.test(drawerText), hasFixtureRef: /tenants\[/.test(drawerText) };
/* focus visible on representative controls */
for (const sel of ['.rail a', '.d-roles .chip', '.d-money', '#op-switch', '.d-table summary', '.tabs a']) {
  const el = page.locator(sel).first(); await el.focus(); await page.keyboard.press('Shift+Tab'); await page.keyboard.press('Tab');
  const o = await page.evaluate(() => { const e = document.activeElement, s = getComputedStyle(e); return { tag: e.tagName, outline: s.outlineStyle + ' ' + s.outlineWidth }; });
  out.focus.push({ sel, ...o, visible: !/none|0px/.test(o.outline) });
}
/* contrast spot checks */
out.contrast = await page.evaluate(() => {
  const lum = c => { const m = c.match(/\d+(\.\d+)?/g).map(Number).slice(0, 3).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * m[0] + .7152 * m[1] + .0722 * m[2]; };
  const bg = e => { while (e) { const c = getComputedStyle(e).backgroundColor; if (c && !/rgba\(0, 0, 0, 0\)|transparent/.test(c)) return c; e = e.parentElement; } return 'rgb(255,255,255)'; };
  return ['.d-note', '.d-cellnote', '.d-rank small', '.badge.green', '.badge.amber', '.badge.red', '.badge.blue', '.d-legal', '.eyebrow', '.d-focustag', '.d-rolenote', '.tabs a', '.d-wfval small', '.d-question p'].map(sel => { const e = document.querySelector(sel); if (!e) return { sel, missing: true }; const a = lum(getComputedStyle(e).color), b = lum(bg(e)); const r = (Math.max(a, b) + .05) / (Math.min(a, b) + .05); return { sel, ratio: Math.round(r * 100) / 100, size: getComputedStyle(e).fontSize, pass: r >= 4.5 }; });
});
/* budget sensitivity */
await page.goto(url + '#/plan-lakeside'); await page.waitForFunction(() => window.mockupReady);
const t1 = await page.textContent('.canvas'); await page.check('[data-budget="high"]');
const t2 = await page.textContent('.canvas');
if (shots) await page.screenshot({ path: path.join(root, 'screenshots/vnext/plan-lakeside-6500-1440.png'), fullPage: true });
out.budget = { base_has_claim: t1.includes('Claim the inverter under warranty and wait'), base_spend: /\$3,880[^$]*of \$5,000/.test(t1), high_has_buynow_recommended: /Buy a replacement now, then claim the failed unit/.test(t2), high_spend: /\$6,430 of \$6,500/.test(t2), high_total: t2.includes('+$3,546') };
await page.check('[data-budget="base"]');
/* pilot form */
await page.goto(url + '#/pilot-lakeside'); await page.waitForFunction(() => window.mockupReady);
await page.click('[data-pilot-form] button[type=submit]'); out.pilotToast = await page.textContent('.toast');
/* v70 before captures */
if (shots) { for (const id of changed) { await page.goto(v70 + '#/' + id); await page.waitForTimeout(300); await page.screenshot({ path: path.join(root, `screenshots/v70/${id}-1440.png`), fullPage: true }); } }
await browser.close();
out.summary = { routes: out.routes.length, routesOk: out.routes.filter(r => r.ok).length, added: added.length, changed: changed.length, badLinkRoutes: Object.entries(out.links).filter(([, v]) => v.length).length, overflowAdded: out.overflow390.filter(o => o.status === 'Added').length, overflowOther: out.overflow390.filter(o => o.status !== 'Added').length, vocabHits: out.vocab.length };
writeFileSync(path.join(here, 'audit-results.json'), JSON.stringify(out, null, 1));
console.log(JSON.stringify(out.summary));
