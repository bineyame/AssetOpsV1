/* Scripted browser audit for the Layer 4 rev 4 mock-up. Usage (from the interactive-mockup-vNEXT folder):
   CHROME=/path/to/chrome PW=/path/to/playwright-core node tools/audit.mjs [--shots]
   Writes tools/audit-results.json, screen-manifest-vnext.json and (with --shots) screenshots/. */
import { createRequire } from 'node:module';
import { writeFileSync, mkdirSync, readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW);
const here = path.dirname(fileURLToPath(import.meta.url)), root = path.resolve(here, '..');
const url = pathToFileURL(path.join(root, 'index.html')).href;
const v70 = pathToFileURL(path.resolve(root, '../../../../frontend/mockups/v70/index.html')).href;
const shots = process.argv.includes('--shots');
const out = { routes: [], overflow390: [], vocab: [], drawer: {}, focus: [], contrast: [], switches: {}, operator: {}, filters: [], preservedText: [], errors: [], links: {} };
const browser = await chromium.launch({ executablePath: process.env.CHROME, args: ['--no-sandbox', '--disable-gpu'] });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await ctx.newPage();
let errs = [];
page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
page.on('pageerror', e => errs.push(String(e)));
const go = async (u) => { await page.goto(u); await page.waitForFunction(() => window.mockupReady); };
await go(url);
const manifest = await page.evaluate(() => window.mockupManifest);
out.oracleShipped = await page.evaluate(() => 'oracle' in MANIFEST);
writeFileSync(path.join(root, 'screen-manifest-vnext.json'), JSON.stringify(manifest, null, 1));
const ids = manifest.map(s => s.id), idset = new Set(ids);
const st = id => manifest.find(s => s.id === id).layer4_status;
if (shots) { mkdirSync(path.join(root, 'screenshots/vnext'), { recursive: true }); mkdirSync(path.join(root, 'screenshots/v70'), { recursive: true }); }
const VOCAB = /\b(?:KOB|BAT|KIS|MTO|MWEA|THIKA|KIRI|EMB|KAS|RUI)-[A-Z0-9-]+\b|\bINV-MT|\bGEN-KS|\bCH-K2\b|\bCH-R7\b|\bfixtures?\b|\bmanifest\b|\boracle\b|\bLOI\b|money_class|overlap.group|driver catalogue|\bdrivers?\b|[<>]=|\b20\d\d-\d\d-\d\d\b|\bO&M\b|\bEXPOSURE\b|\bMODELLED\b|\bRECOMMENDED\b|\bREJECTED\b|NO_ACTION|ECONOMIC_ACTUAL|undefined|NaN|\[object|\bnull\b/;
const LOOPLIKE = s => s === 'Added' || s === 'Changed';
const DRAWER_SAMPLE = new Set(['portfolio', 'portfolio/outcomes-by-site', 'portfolio/act-first', 'decision/kobo-generator', 'decision/thika-backup', 'decision/embakasi-schedule', 'site/kasarani', 'globalfinancials']);
for (const op of ['lakeside', 'harvest', 'metro']) {
  await go(url); await page.selectOption('#op-switch', op);
  for (const id of ids) {
    if (op !== 'lakeside' && !(id.startsWith('portfolio') || id === 'sites' || id === 'globalfinancials')) continue;
    errs = [];
    await go(url + '#/' + id);
    const r = await page.evaluate(() => ({ h1: document.querySelector('h1')?.textContent, hash: location.hash, hrefs: [...document.querySelectorAll('a[href^="#/"]')].map(a => a.getAttribute('href').slice(2)), text: document.querySelector('.canvas')?.textContent || '', banner: [...document.querySelectorAll('.slim-banner')].map(b => b.textContent).join(' '), chips: document.querySelectorAll('.canvas .chip,[data-lens-filter],[data-site-filter-l4]').length, topbarOp: !!document.querySelector('.topbar #op-switch'), reviewOp: !!document.querySelector('.reviewbar #op-switch') }));
    const bad = [...new Set(r.hrefs.filter(h => !idset.has(h)))];
    if (bad.length) out.links[op + ':' + id] = bad;
    const s = st(id);
    if (LOOPLIKE(s)) { const scanned = manifest.find(x => x.id === id).loop || s === 'Added' || ['portfolio', 'sites', 'globalfinancials'].includes(id) ? r.text : r.banner; const m = scanned.match(VOCAB); if (m) out.vocab.push({ op, id, match: m[0], at: scanned.slice(Math.max(0, m.index - 50), m.index + 50) }); }
    if (id.startsWith('portfolio') && r.chips) out.filters.push({ op, id, chips: r.chips });
    if (DRAWER_SAMPLE.has(id)) { const n = await page.locator('.ev-num').count(); for (let k = 0; k < Math.min(n, 6); k++) { await page.locator('.ev-num').nth(k).click(); const dt = (await page.evaluate(() => { const d = document.querySelector('.drawer').cloneNode(true); d.querySelectorAll('details.tech,.srcrows thead').forEach(x => x.remove()); return d.textContent; })); const m2 = dt.match(VOCAB); if (m2) out.vocab.push({ op, id: id + ' (drawer ' + k + ')', match: m2[0], at: dt.slice(Math.max(0, m2.index - 50), m2.index + 50) }); await page.keyboard.press('Escape'); } }
    out.routes.push({ op, id, status: s, ok: !!r.h1 && errs.length === 0, h1: r.h1, landed: r.hash.slice(2), errors: errs.slice(0, 3), topbarOperatorSelect: r.topbarOp, reviewOperatorSelect: r.reviewOp });
    if (shots && op !== 'lakeside' && ['portfolio', 'portfolio/act-first', 'portfolio/outcomes-by-site', 'portfolio/opportunity'].includes(id)) await page.screenshot({ path: path.join(root, `screenshots/vnext/${op}-${id.replace(/\//g, '_')}-1440.png`), fullPage: true });
    if (shots && op === 'lakeside' && LOOPLIKE(s) && (id.startsWith('portfolio') || id.startsWith('decision/') || /^site\/(kobo|thika|ruiru|kisiwa|kasarani)(\/economics)?$/.test(id) || ['sites', 'globalfinancials', 'mini', 'findings', 'ev-health'].includes(id))) await page.screenshot({ path: path.join(root, `screenshots/vnext/${id.replace(/\//g, '_')}-1440.png`), fullPage: true });
  }
}
/* 390 px overflow, every route (Lakeside, plus portfolio routes for each operator) */
await page.setViewportSize({ width: 390, height: 844 });
for (const op of ['lakeside', 'harvest', 'metro']) {
  await go(url); await page.selectOption('#op-switch', op);
  for (const id of ids) {
    if (op !== 'lakeside' && !id.startsWith('portfolio')) continue;
    await go(url + '#/' + id);
    const w = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, culprits: [...document.querySelectorAll('body *')].filter(e => { const b = e.getBoundingClientRect(); return b.right > document.documentElement.clientWidth + 1 && !e.closest('.table-wrap,.tabs,pre,.scroll-region,.reviewbar') && getComputedStyle(e).position !== 'fixed'; }).slice(0, 3).map(e => e.tagName + '.' + [...e.classList].join('.')) }));
    if (w.sw > w.cw) out.overflow390.push({ op, id, status: st(id), scrollWidth: w.sw, culprits: w.culprits });
    if (shots && op === 'lakeside' && ['portfolio', 'portfolio/act-first', 'portfolio/outcomes-by-site', 'decision/kobo-generator', 'site/kobo'].includes(id)) await page.screenshot({ path: path.join(root, `screenshots/vnext/${id.replace(/\//g, '_')}-390.png`), fullPage: true });
    if (shots && op === 'metro' && id === 'portfolio') await page.screenshot({ path: path.join(root, `screenshots/vnext/metro-portfolio-390.png`), fullPage: true });
  }
}
await page.setViewportSize({ width: 1440, height: 1000 });
/* switches re-compute the plan */
const M = JSON.parse(readFileSync(path.join(root, 'fixtures.js'), 'utf8').match(/const MANIFEST = (.*);\nconst MANIFEST_SHA/s)[1]);
const usd = n => '$' + Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: Number.isInteger(n) ? 0 : 2 });
await go(url); await page.selectOption('#op-switch', 'lakeside'); await go(url + '#/portfolio/act-first');
const cases = M.tenants[0].portfolio.allocation.switches.find(x => x.cases).cases;
await page.check('input[name="sw-budget"][value="6500"]'); await page.check('input[name="sw-loi"][value="no"]');
for (const [k, c] of Object.entries(cases)) {
  const [b, l] = k.split('/'); await page.check(`input[name="sw-budget"][value="${b}"]`); await page.check(`input[name="sw-loi"][value="${l}"]`);
  const r = await page.evaluate(() => ({ total: document.querySelector('.total strong')?.innerText, meter: document.querySelector('.meterhead strong')?.innerText, win: document.querySelector('.path.win h3')?.innerText, lose: document.querySelector('.path:not(.win) h3')?.innerText, rows: document.querySelector('.panel table')?.innerText || '', live: document.getElementById('plan-live')?.textContent, focus: document.activeElement?.name }));
  out.switches['lakeside ' + k] = { expectSpend: usd(c.spend), expectValue: '+' + usd(c.value), spendOk: r.meter?.startsWith(usd(c.spend)), valueOk: r.total?.startsWith('+' + usd(c.value)), inverterOk: (c.inverter === 'BUYNOW') === /Buy a replacement/.test(r.win || ''), competingShown: !!r.lose, hullerOk: c.huller === /rice huller/.test(r.rows), announced: !!r.live, focusKept: r.focus === 'sw-loi' };
  if (shots) await page.screenshot({ path: path.join(root, `screenshots/vnext/act-first-lakeside-${k.replace('/', '-')}-1440.png`), fullPage: true });
}
await page.check('input[name="sw-budget"][value="5000"]'); await page.check('input[name="sw-loi"][value="yes"]');
await page.selectOption('#op-switch', 'harvest'); await go(url + '#/portfolio/act-first');
for (const [v, sp, vis] of [['yes', '$720', '2 of 2'], ['no', '$450', '1 of 2']]) { await page.check(`input[name="sw-agg"][value="${v}"]`); const r = await page.evaluate(() => [...document.querySelectorAll('.meterhead strong')].map(x => x.innerText)); out.switches['harvest aggregator ' + v] = { spendOk: r[0].startsWith(sp), visitsOk: r[1].startsWith(vis), got: r }; }
await page.check('input[name="sw-agg"][value="yes"]');
await page.selectOption('#op-switch', 'metro'); await go(url + '#/portfolio/act-first');
for (const [v, sp, val] of [['yes', '$1,590', '+$95,484'], ['no', '$90', '$0']]) { await page.check(`input[name="sw-tou"][value="${v}"]`); const r = await page.evaluate(() => ({ m: document.querySelector('.meterhead strong').innerText, t: document.querySelector('.total strong').innerText })); out.switches['metro tariff ' + v] = { spendOk: r.m.startsWith(sp), valueOk: r.t.startsWith(val), got: r }; }
await page.check('input[name="sw-tou"][value="yes"]');
/* operator switch: review bar only; headline follows the tenant */
await page.selectOption('#op-switch', 'lakeside'); await go(url + '#/portfolio');
for (const op of ['harvest', 'metro', 'lakeside']) { await page.selectOption('#op-switch', op); await page.waitForTimeout(100); out.operator[op] = await page.evaluate(() => ({ topbar: document.querySelector('.portfolio-name')?.innerText, headline: document.querySelector('.headline p')?.innerText.slice(0, 90), inTopbar: !!document.querySelector('.topbar select#op-switch') })); }
/* drawer: keyboard open, focus inside and trapped, Escape closes and returns focus */
await go(url + '#/portfolio');
const trig = page.locator('.heroes .ev-num').first(); await trig.focus(); await page.keyboard.press('Enter'); await page.waitForSelector('.drawer');
const inDrawer = await page.evaluate(() => !!document.activeElement.closest('.drawer'));
let trapped = true; for (let i = 0; i < 25; i++) { await page.keyboard.press('Tab'); if (!(await page.evaluate(() => !!document.activeElement.closest('.drawer')))) trapped = false; }
for (let i = 0; i < 5; i++) { await page.keyboard.press('Shift+Tab'); if (!(await page.evaluate(() => !!document.activeElement.closest('.drawer')))) trapped = false; }
const dtext = await page.innerText('.drawer');
if (shots) await page.screenshot({ path: path.join(root, 'screenshots/vnext/evidence-drawer-1440.png') });
await page.keyboard.press('Escape');
out.drawer = { openedWithKeyboard: true, focusInside: inDrawer, focusTrapped: trapped, escapeCloses: await page.evaluate(() => !document.querySelector('.drawer')), focusReturned: await page.evaluate(() => document.activeElement?.classList.contains('ev-num')), hasDefinition: /What this is/.test(dtext), hasFormula: /How it is worked out/.test(dtext), hasSourceRows: /Source records/.test(dtext), hasClocks: /Period and clocks/.test(dtext), hasCoverage: /Coverage/.test(dtext), hasProvenance: /Source-emulated demo record|Simulated demo data/.test(dtext) };
/* tabs are links: keyboard reachable */
out.tabsKeyboard = await page.evaluate(() => [...document.querySelectorAll('.canvas .tabs a')].every(a => a.tabIndex >= 0));
/* focus visible */
for (const sel of ['.rail a', '.tabs a', '.ev-num', '#op-switch', 'button.wfrow', 'input[name="sw-budget"]', 'details.astable summary']) {
  const target = sel === 'button.wfrow' || sel === 'details.astable summary' ? 'portfolio/outcomes-by-site' : sel.startsWith('input') ? 'portfolio/act-first' : 'portfolio';
  await go(url + '#/' + target); const el = page.locator(sel).first(); await el.focus(); await page.keyboard.press('Shift+Tab'); await page.keyboard.press('Tab');
  const o = await page.evaluate(() => { const e = document.activeElement, s = getComputedStyle(e); return { tag: e.tagName, outline: s.outlineStyle + ' ' + s.outlineWidth, shadow: s.boxShadow }; });
  out.focus.push({ sel, ...o, visible: !/none|0px/.test(o.outline) || o.shadow !== 'none' });
}
/* contrast spot checks */
for (const [route, sels] of [['portfolio', ['.ec-rec', '.ec-est', '.ec-der', '.ec-mod', '.ec-stake', '.ec-na', '.hero small', '.note', '.attn-k', '.attn-new .attn-k', '.attn-at .attn-k', '.attn-unobs .attn-k', '.chain .stage span', '.chain .leak', '.ocard h4', '.op-select']], ['portfolio/outcomes-by-site', ['.fac small', '.wfval small', '.wflabel small', '.lens', '.ftab thead th', '.lgrid tbody th small']], ['portfolio/act-first', ['.cellnote', '.switch small', '.meterhead']], ['decision/mto-inverter', ['.legal', '.steps small', '.deadline']], ['decision/kobo-generator', ['.obl-pass', '.obl-fail', '.obl-cost', '.obl-unknown', '.legal', '.badge.green', '.badge.amber', '.badge.red']], ['findings', ['.slim-banner']]]) {
  await go(url + '#/' + route);
  out.contrast.push(...await page.evaluate((sels) => {
    const lum = c => { const m = c.match(/[\d.]+/g).map(Number).slice(0, 3).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * m[0] + .7152 * m[1] + .0722 * m[2]; };
    const bg = e => { while (e) { const c = getComputedStyle(e).backgroundColor; if (c && !/rgba\(0, 0, 0, 0\)|transparent/.test(c)) return c; e = e.parentElement; } return 'rgb(255,255,255)'; };
    return sels.map(sel => { const e = document.querySelector(sel); if (!e) return { sel, missing: true }; const a = lum(getComputedStyle(e).color), b = lum(bg(e)); const r = (Math.max(a, b) + .05) / (Math.min(a, b) + .05); return { sel, ratio: Math.round(r * 100) / 100, size: getComputedStyle(e).fontSize, pass: r >= 4.5 }; });
  }, sels).then(a => a.map(x => ({ route, ...x }))));
}
/* preserved v7.0 screens: canvas text equals v7.0 after the display-name map */
const NAMES = [[/GreenHarvest Cold Room/g, 'Thika cold room'], [/GreenHarvest/g, 'Thika'], [/Depot Charging Hub/g, 'Ruiru depot'], [/Depot charging hub/g, 'Ruiru depot'], [/(?<!Westfield )\bDepot\b(?! auxiliary| attendant)/g, 'Ruiru'], [/MG-DEMO-01/g, 'KOBO-001'], [/CR-DEMO-01/g, 'COLD-THIKA'], [/EV-DEMO-01/g, 'EV-RUI']];
const v70page = await ctx.newPage();
for (const s of manifest.filter(m => m.layer4_status === 'Preserved')) {
  await v70page.goto(v70 + '#/' + s.id); await v70page.waitForFunction(() => window.mockupReady);
  const a = (await v70page.evaluate(() => document.querySelector('.canvas')?.innerText || '')); const mapped = NAMES.reduce((t, [p, r]) => t.replace(p, r), a);
  await go(url + '#/' + s.id); const b = await page.evaluate(() => document.querySelector('.canvas')?.innerText || '');
  out.preservedText.push({ id: s.id, identicalAfterNames: mapped === b, namesChanged: mapped !== a });
}
/* v7.0 before captures */
if (shots) { for (const id of ['portfolio', 'sites', 'globalfinancials', 'financials', 'mini']) { await v70page.goto(v70 + '#/' + id); await v70page.waitForTimeout(300); await v70page.screenshot({ path: path.join(root, `screenshots/v70/${id}-1440.png`), fullPage: true }); } }
await browser.close();
const lk = out.routes.filter(r => r.op === 'lakeside');
out.summary = { routesChecked: out.routes.length, routesOk: out.routes.filter(r => r.ok).length, screens: manifest.length, byStatus: manifest.reduce((a, s) => (a[s.layer4_status] = (a[s.layer4_status] || 0) + 1, a), {}), consoleErrorRoutes: out.routes.filter(r => r.errors.length).length, badLinkRoutes: Object.keys(out.links).length, overflow390: out.overflow390.length, vocabHits: out.vocab.length, filterControlsOnPortfolio: out.filters.length, operatorSelectInTopbar: out.routes.filter(r => r.topbarOperatorSelect).length, operatorSelectInReviewBar: out.routes.filter(r => r.reviewOperatorSelect).length, switchCasesOk: Object.values(out.switches).filter(x => Object.entries(x).filter(([k]) => /Ok$|Shown$|announced|focusKept/.test(k)).every(([, v]) => v)).length + '/' + Object.keys(out.switches).length, drawerOk: Object.values(out.drawer).every(Boolean), focusVisible: out.focus.filter(f => f.visible).length + '/' + out.focus.length, contrastPass: out.contrast.filter(c => c.pass).length + '/' + out.contrast.filter(c => !c.missing).length, preservedIdentical: out.preservedText.filter(p => p.identicalAfterNames).length + '/' + out.preservedText.length, oracleShipped: out.oracleShipped };
writeFileSync(path.join(here, 'audit-results.json'), JSON.stringify(out, null, 1));
console.log(JSON.stringify(out.summary, null, 1));
