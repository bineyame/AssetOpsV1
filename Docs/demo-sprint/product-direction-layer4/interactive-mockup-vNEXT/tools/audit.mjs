/* Scripted browser audit for the Layer 4 rev 4 mock-up. Usage (from the interactive-mockup-vNEXT folder):
   CHROME=/path/to/chrome PW=/path/to/playwright-core node tools/audit.mjs [--shots]
   Writes tools/audit-results.json, screen-manifest-vnext.json and (with --shots) screenshots/. */
import { createRequire } from 'node:module';
import { writeFileSync, mkdirSync, readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW);
const here = path.dirname(fileURLToPath(import.meta.url)), root = path.resolve(here, '..');
const url = pathToFileURL(path.join(root, 'index.html')).href;
const v70 = pathToFileURL(path.resolve(root, '../../../../frontend/mockups/v70/index.html')).href;
const shots = process.argv.includes('--shots');
const REPLAY = JSON.parse(execFileSync('python3', [path.join(here, 'replay_values.py')]).toString());

const out = { dvScan: { occurrences: 0, unlabelled: [], drawersOpened: 0, byFigure: {} }, idHits: [], idHitsPreserved: [], roleHits: [], routes: [], overflow390: [], vocab: [], drawer: {}, focus: [], contrast: [], switches: {}, operator: {}, filters: [], preservedText: [], errors: [], links: {} };
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
out.placeholders = await page.evaluate(() => ({ fig: TPL.fig, rec: TPL.rec, strings: TPL.strings, unresolved: TPL.unresolved }));
out.dvScan.independentPatterns = REPLAY.patterns.length; out.dvScan.independentFigures = REPLAY.figures; out.dvScan.sameAsTagger = await page.evaluate(f => { const nums = a => a.map(x => parseFloat(x)).sort((x, y) => x - y).join(','); return nums(REPLAY_VALUES) === nums(f); }, REPLAY.figures);
writeFileSync(path.join(root, 'screen-manifest-vnext.json'), JSON.stringify(manifest, null, 1));
const ids = manifest.map(s => s.id), idset = new Set(ids);
const st = id => manifest.find(s => s.id === id).layer4_status;
if (shots) { mkdirSync(path.join(root, 'screenshots/vnext'), { recursive: true }); mkdirSync(path.join(root, 'screenshots/v70'), { recursive: true }); }
const VOCAB = /\b(?:KOB|BAT|KIS|MTO|MWEA|THIKA|KIRI|EMB|KAS|RUI)-[A-Z][A-Z0-9-]*\b|\bfixtures?\b|\bmanifest\b|\boracle\b|\bLOI\b|money_class|overlap.group|driver catalogue|\bdrivers?\b|[<>]=|\b20\d\d-\d\d-\d\d\b|\bO&M\b|\bEXPOSURE\b|\bMODELLED\b|\bRECOMMENDED\b|\bREJECTED\b|NO_ACTION|ECONOMIC_ACTUAL|\.py\b|\.py\b|undefined|NaN|\[object|\bnull\b/;
/* independent replay set: tools/replay_values.py reads the manifest YAML directly (not fixtures.js, not the tagger) */
const DV_SCAN = ([rootSel, pats]) => { const R = document.querySelector(rootSel); if (!R) return { n: 0, bad: [] }; const RE = new RegExp(pats.join('|'), 'g'); let n = 0; const bad = [];
  const w = document.createTreeWalker(R, NodeFilter.SHOW_TEXT); let tn; while ((tn = w.nextNode())) { const pe = tn.parentElement; if (pe.closest('.dv,.vh,select,option,details.tech')) continue; const ms = tn.textContent.match(RE); if (!ms) continue; n += ms.length; ms.forEach(x => { (window.__fig = window.__fig || {})[x] = (window.__fig[x] || 0) + 1; }); const c = pe.closest('tr,li,p,dd,.hero,.path,.total,.evhead'); if (!c || !c.querySelector('.dv')) bad.push({ figure: ms[0], at: (c || pe).textContent.slice(0, 120) }); } return { n, bad }; };
const LOOPLIKE = s => s === 'Added' || s === 'Changed';
/* L2 identifier rule: product record ids never bare; client asset/batch tags only inside parentheses after a plain name.
   Owner rule (17 Nov, seventh message): no role names or executive-question stems; no heading phrased as a question. */
const ID_CHECK = (rootSel) => { const R = document.querySelector(rootSel); if (!R) return []; const REC = /\b(?:F|ACT|WR|INC)-\d{2,}\b/g, TAG = /\b(?:GEN-CR-01|GEN-KS-0\d|INV-MT-0\d|CH-K2|CH-R7|B-1\d{3}|BAT-\d{3}|CN-\d{4}|PM-\d{4})\b/g; const hits = [];
  const w = document.createTreeWalker(R, NodeFilter.SHOW_TEXT); let n; while ((n = w.nextNode())) { if (n.parentElement.closest('details.tech,select,option')) continue; const el = n.parentElement.closest('p,li,td,th,dd,dt,small,b,span,h1,h2,h3,a,div,figcaption'); const txt = el.textContent;
    for (const m of n.textContent.matchAll(REC)) hits.push({ kind: 'record id', id: m[0], at: txt.slice(0, 120) });
    for (const m of n.textContent.matchAll(TAG)) { const idx = txt.indexOf(m[0]); const before = txt.slice(0, idx); const open = before.lastIndexOf('('), close = before.lastIndexOf(')'); const ok = open > close && /[A-Za-z][A-Za-z0-9 ,’'–-]{2,}\s*$/.test(before.slice(0, open)); if (!ok) hits.push({ kind: 'asset or batch tag without a plain name', id: m[0], at: txt.slice(0, 120) }); } }
  return hits; };
const ROLE_CHECK = () => { const R = document.querySelector('.canvas'); const txt = R.textContent; const hits = []; const m1 = txt.match(/\b(?:CEO|COO|CFO|CCO)\b|Which sites and investments|Where should limited crews|Why is performance off plan|Which demand can be sold/); if (m1) hits.push({ kind: 'role or question stem', match: m1[0] });
  R.querySelectorAll('h1,h2,h3,h4,.page-heading p,figcaption,.eyebrow,th,legend').forEach(h => { if (/\?\s*$/.test(h.textContent.trim())) hits.push({ kind: 'heading phrased as a question', match: h.textContent.trim().slice(0, 100) }); }); return hits; };
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
    { const full = manifest.find(x => x.id === id).loop || s === 'Added' || ['portfolio', 'sites', 'globalfinancials'].includes(id);
      if (op === 'lakeside' || full) { const h = await page.evaluate(ID_CHECK, full ? '.canvas' : '.slim-banner'); h.forEach(x => (LOOPLIKE(s) ? out.idHits : out.idHitsPreserved).push({ op, id, ...x }));
        if (LOOPLIKE(s) && full) (await page.evaluate(ROLE_CHECK)).forEach(x => out.roleHits.push({ op, id, ...x }));
        else if (LOOPLIKE(s)) { const ph = await page.evaluate(() => [...document.querySelectorAll('.slim-banner,.tabs a')].map(e => e.textContent).join(' ')); if (/\b(?:CEO|COO|CFO|CCO)\b/.test(ph)) out.roleHits.push({ op, id, kind: 'role in banner or tab' }); }
        if (!LOOPLIKE(s) && op === 'lakeside') { const h2 = await page.evaluate(ID_CHECK, '.canvas'); h2.forEach(x => out.idHitsPreserved.push({ op, id, ...x })); } } }
    { const d = await page.evaluate(DV_SCAN, ['.canvas', REPLAY.patterns]); if (s === 'Preserved') { d.bad.forEach(b => (out.dvScan.preservedCoincidences = out.dvScan.preservedCoincidences || []).push({ op, id, ...b })); } else { out.dvScan.occurrences += d.n; d.bad.forEach(b => out.dvScan.unlabelled.push({ op, id, ...b })); }
      const nb = await page.locator('.ev-num').count(); for (let k = 0; k < Math.min(nb, 60); k++) { await page.locator('.ev-num').nth(k).click(); out.dvScan.drawersOpened++; const dd = await page.evaluate(DV_SCAN, ['.drawer', REPLAY.patterns]); out.dvScan.occurrences += dd.n; dd.bad.forEach(b => out.dvScan.unlabelled.push({ op, id: id + ' (drawer ' + k + ')', ...b })); await page.keyboard.press('Escape'); } }
    if (DRAWER_SAMPLE.has(id)) { const n = await page.locator('.ev-num').count(); for (let k = 0; k < Math.min(n, 6); k++) { await page.locator('.ev-num').nth(k).click(); const dt = (await page.evaluate(() => { const d = document.querySelector('.drawer').cloneNode(true); d.querySelectorAll('details.tech,.srcrows thead').forEach(x => x.remove()); return d.textContent; })); const dh = await page.evaluate(ID_CHECK, '.drawer'); if (/\b(?:CEO|COO|CFO|CCO)\b|Which sites and investments|Where should limited crews|Why is performance off plan|Which demand can be sold/.test(dt)) out.roleHits.push({ op, id: id + ' (drawer ' + k + ')', kind: 'role or question stem in drawer' }); dh.forEach(x => out.idHits.push({ op, id: id + ' (drawer ' + k + ')', ...x })); const m2 = dt.match(VOCAB); if (m2) out.vocab.push({ op, id: id + ' (drawer ' + k + ')', match: m2[0], at: dt.slice(Math.max(0, m2.index - 50), m2.index + 50) }); await page.keyboard.press('Escape'); } }
    out.routes.push({ op, id, status: s, ok: !!r.h1 && errs.length === 0, h1: r.h1, landed: r.hash.slice(2), errors: errs.slice(0, 3), topbarOperatorSelect: r.topbarOp, reviewOperatorSelect: r.reviewOp });
    if (shots && op !== 'lakeside' && ['portfolio', 'portfolio/act-first', 'portfolio/outcomes-by-site', 'portfolio/demand-and-capacity'].includes(id)) await page.screenshot({ path: path.join(root, `screenshots/vnext/${op}-${id.replace(/\//g, '_')}-1440.png`), fullPage: true });
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
/* rev 13: expectations from the evaluator's switch cases (derived-values.json), not typed copies */
const DV = JSON.parse(readFileSync(path.join(root, '..', 'derived-values.json'), 'utf8')), YN = s => s === 'True' ? 'yes' : 'no';
const cases = Object.fromEntries(Object.entries(DV.plans['lakeside-power'].switch_cases).map(([k, c]) => { const [b, l] = k.split('/'); return [`${b}/${YN(l)}`, { ...c, inverter: c.items.includes('MTO-INV-BUYNOW') ? 'BUYNOW' : 'CLAIM', huller: c.items.includes('MTO-HULLER') }]; }));
await page.check('input[name="sw-budget"][value="6500"]'); await page.check('input[name="sw-loi"][value="no"]');
for (const [k, c] of Object.entries(cases)) {
  const [b, l] = k.split('/'); await page.check(`input[name="sw-budget"][value="${b}"]`); await page.check(`input[name="sw-loi"][value="${l}"]`);
  const r = await page.evaluate(() => ({ total: document.querySelector('.total strong')?.innerText, meter: document.querySelector('.meterhead strong')?.innerText, win: document.querySelector('.path.win h3')?.innerText, lose: document.querySelector('.path:not(.win) h3')?.innerText, rows: document.querySelector('.panel table')?.innerText || '', live: document.getElementById('plan-live')?.textContent, note: document.querySelector('.total small')?.textContent, down: document.querySelector('.downside')?.textContent, focus: document.activeElement?.name }));
  out.switches['lakeside ' + k] = { expectSpend: usd(c.spend), expectValue: '+' + usd(c.value), spendOk: r.meter?.startsWith(usd(c.spend)), valueOk: r.total?.startsWith('+' + usd(c.value)), inverterOk: (c.inverter === 'BUYNOW') === /Buy a replacement/.test(r.win || ''), competingShown: !!r.lose, hullerOk: c.huller === /rice huller/.test(r.rows), valuedCostsOk: r.note?.includes(usd(c.spend - c.not_valued_in_money)) && r.note?.includes(usd(M.tenants[0].portfolio.allocation.must_do_spend)) && r.note?.includes(usd(M.tenants[0].portfolio.allocation.protective_spend)), downsideOk: (r.down || '').replace(/^Downside( shown for the default plan)?: /, '').startsWith('+' + usd(DV.plans['lakeside-power'].downside)) && (k === '5000/yes') === r.down.startsWith('Downside: '), announced: !!r.live, focusKept: r.focus === 'sw-loi' };
  if (shots) await page.screenshot({ path: path.join(root, `screenshots/vnext/act-first-lakeside-${k.replace('/', '-')}-1440.png`), fullPage: true });
}
await page.check('input[name="sw-budget"][value="5000"]'); await page.check('input[name="sw-loi"][value="yes"]');
await page.selectOption('#op-switch', 'harvest'); await go(url + '#/portfolio/act-first');
const HD = DV.plans['harvest-cold'], MD = DV.plans['metro-bus'], VS = c => [usd(c.spend), `${c.crew_visits_used} of ${c.crew_visits_limit}`, (c.value < 0 ? '−' : '+') + usd(c.value)];
for (const [v, sp, vis, val] of [['yes', ...VS(HD.switch_cases.True)], ['no', ...VS(HD.switch_cases.False)]]) { await page.check(`input[name="sw-agg"][value="${v}"]`); const r = await page.evaluate(() => [...document.querySelectorAll('.meterhead strong')].map(x => x.innerText)); const tt = await page.evaluate(() => document.querySelector('.total strong').innerText); const dn = await page.evaluate(() => document.querySelector('.downside')?.textContent || ''); out.switches['harvest aggregator ' + v] = { spendOk: r[0].startsWith(sp), visitsOk: r[1].startsWith(vis), valueOk: tt.startsWith(val), downsideOk: v === 'yes' ? dn.startsWith('Downside: +' + usd(HD.downside)) : dn.startsWith('Downside shown for the default plan: +' + usd(HD.downside)), got: r.concat(tt) }; }
await page.check('input[name="sw-agg"][value="yes"]');
await page.selectOption('#op-switch', 'metro'); await go(url + '#/portfolio/act-first');
for (const [v, sp, val] of [['yes', ...VS(MD.switch_cases.True).filter((x, i) => i !== 1)], ['no', ...VS(MD.switch_cases.False).filter((x, i) => i !== 1)]]) { await page.check(`input[name="sw-tou"][value="${v}"]`); const r = await page.evaluate(() => ({ m: document.querySelector('.meterhead strong').innerText, t: document.querySelector('.total strong').innerText, d: document.querySelector('.downside')?.textContent || '' })); out.switches['metro tariff ' + v] = { spendOk: r.m.startsWith(sp), valueOk: r.t.startsWith(val), downsideOk: v === 'yes' ? r.d.startsWith('Downside: +' + usd(MD.downside)) : r.d.startsWith('Downside shown for the default plan: +' + usd(MD.downside)), got: r }; }
await page.check('input[name="sw-tou"][value="yes"]');
/* owner rule also covers drawers and tab/section names: review-notes drawer on every added screen, tab rows on every added/changed screen */
await page.selectOption('#op-switch', 'lakeside');
for (const s of manifest.filter(m => m.layer4_status === 'Added' || ['portfolio', 'sites', 'globalfinancials'].includes(m.id))) { await go(url + '#/' + s.id); await page.click('footer [data-notes]'); const d = await page.evaluate(() => document.querySelector('.drawer').textContent + ' ' + [...document.querySelectorAll('.tabs a')].map(a => a.textContent).join(' ')); const m = d.match(/\b(?:CEO|COO|CFO|CCO)\b|Which sites and investments|Where should limited crews|Why is performance off plan|Which demand can be sold/); if (m) out.roleHits.push({ id: s.id + ' (review notes or tabs)', kind: 'role or question stem', match: m[0] }); await page.keyboard.press('Escape'); }
out.reviewNotesChecked = true;
/* rev 5: Protect measures shown with targets; plan figure labelled per the file */
out.rev5 = {};
for (const op of ['lakeside', 'harvest', 'metro']) { await page.selectOption('#op-switch', op); await go(url + '#/portfolio/outcomes-by-site');
  out.rev5[op] = await page.evaluate(() => ({ protectTable: !!document.querySelector('[aria-label="Protect measures by site"]'), novTable: !!document.querySelector('[aria-label="Protect measures, November to 6 Nov"]'), stakeListed: /listed, never summed/.test(document.querySelector('.canvas').textContent), avoidableObserved: /not avoidable in the replay|feasibly avoidable/i.test(document.querySelector('.canvas').textContent) }));
  await go(url + '#/portfolio'); out.rev5[op].overviewProtectTargets = await page.evaluate(() => /target 0|target \$0/.test(document.querySelector('.lens-b-protect').textContent)); out.rev5[op].valueNote = await page.evaluate(() => [...document.querySelectorAll('.hero small')].map(x => x.textContent).join(' ').slice(0, 400)); }
await page.selectOption('#op-switch', 'lakeside');
/* rev 6 checks: tab order, old route redirect, design-value labels, Ruiru residual wording */
out.rev6 = {};
await page.selectOption('#op-switch', 'lakeside'); await go(url + '#/portfolio');
out.rev6.tabOrder = await page.evaluate(() => [...document.querySelectorAll('.canvas .tabs a')].map(a => a.textContent.trim()));
out.rev6.tabOrderOk = JSON.stringify(out.rev6.tabOrder) === JSON.stringify(['Overview', 'Outcomes by site', 'Demand and capacity', 'Act first', 'What changed', 'Scope & coverage']);
await page.goto(url + '#/portfolio/opportunity'); await page.waitForFunction(() => window.mockupReady); out.rev6.oldRouteRedirect = await page.evaluate(() => location.hash);
const DVT = 'Design estimate: not yet tested on your recorded data';
out.rev6.dvDecisionPages = {};
for (const d of ['kobo-generator', 'mto-demand', 'embakasi-schedule', 'kirinyaga-energy', 'mto-inverter']) { await go(url + '#/decision/' + d); out.rev6.dvDecisionPages[d] = await page.evaluate(() => [...document.querySelectorAll('.dv')].map(x => x.textContent)); }
out.rev6.dvOk = Object.values(out.rev6.dvDecisionPages).every(a => a.length > 0);
out.rev6.dvPlanDrawer = {}; out.rev6.overviewNote = {};
for (const op of ['lakeside', 'harvest', 'metro']) { await page.selectOption('#op-switch', op); await go(url + '#/portfolio'); out.rev6.overviewNote[op] = await page.evaluate(op => (op === 'harvest' ? /includes an assumed recovery share/ : /includes design values not yet run on site data/).test(document.querySelector('.heroes').textContent), op); await page.click('[data-evd$=":m12"]'); out.rev6.dvPlanDrawer[op] = await page.evaluate(([t, op]) => document.querySelector('.drawer').textContent.includes(op === 'harvest' ? 'Assumption: Kirinyaga recovery share 80%, range 60–90%' : t) && (op !== 'harvest' || !/forward replay/i.test(document.querySelector('.drawer').textContent)) && /Modelled 12-month change from the valued options/.test(document.querySelector('.drawer').textContent) && /Downside|default plan/.test(document.querySelector('.drawer').textContent), [DVT, op]); await page.keyboard.press('Escape'); }
await page.selectOption('#op-switch', 'metro');
out.rev6.ruiruNoModelWording = {};
for (const r of ['site/ruiru', 'site/ruiru/economics', 'portfolio/outcomes-by-site']) { await go(url + '#/' + r); out.rev6.ruiruNoModelWording[r] = await page.evaluate(r => { const el = r.startsWith('portfolio') ? [document.getElementById('fs-ruiru'), ...[...document.querySelectorAll('.wfrow')].filter(x => /Ruiru/.test(x.textContent))] : [document.querySelector('.canvas')]; return !el.some(e => e && /not explained by the model/.test(e.textContent)); }, r); }
out.rev6.ruiruOk = Object.values(out.rev6.ruiruNoModelWording).every(Boolean);
await go(url + '#/portfolio/outcomes-by-site'); out.rev7 = { evMeasure: await page.evaluate(() => /Deliverable energy used \(import-limited\)/.test(document.querySelector('.canvas').textContent) && /binding limit/.test(document.querySelector('.canvas').textContent)) };
await go(url + '#/portfolio/demand-and-capacity'); out.rev7.ruiruNameplate = await page.evaluate(() => /nameplate charger-hours/.test(document.querySelector('.canvas').textContent) && /61% of the energy deliverable a night/.test(document.querySelector('.canvas').textContent));
await page.selectOption('#op-switch', 'lakeside');
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
for (const [route, sels] of [['portfolio', ['.ec-rec', '.ec-est', '.ec-der', '.ec-mod', '.ec-stake', '.ec-na', '.hero small', '.note', '.attn-k', '.attn-new .attn-k', '.attn-at .attn-k', '.attn-unobs .attn-k', '.chain .stage span', '.chain .leak', '.ocard h4', '.op-select']], ['portfolio/outcomes-by-site', ['.fac small', '.wfval small', '.wflabel small', '.lens', '.ftab thead th', '.lgrid tbody th small']], ['portfolio/act-first', ['.cellnote', '.switch small', '.meterhead', '.downside', '.dv']], ['decision/mto-inverter', ['.legal', '.steps small', '.deadline']], ['decision/kobo-generator', ['.obl-pass', '.obl-fail', '.obl-cost', '.obl-unknown', '.legal', '.badge.green', '.badge.amber', '.badge.red']], ['findings', ['.slim-banner']]]) {
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
/* Rev 12 (M5): hand-typed figure scan of loop-*.js against the evaluated figures (tools/hand_typed_scan.py); required 0 */
const HT = JSON.parse(execFileSync('python3', [path.join(here, 'hand_typed_scan.py')]).toString()); out.handTyped = HT;
out.summary = { routesChecked: out.routes.length, routesOk: out.routes.filter(r => r.ok).length, screens: manifest.length, byStatus: manifest.reduce((a, s) => (a[s.layer4_status] = (a[s.layer4_status] || 0) + 1, a), {}), consoleErrorRoutes: out.routes.filter(r => r.errors.length).length, badLinkRoutes: Object.keys(out.links).length, overflow390: out.overflow390.length, vocabHits: out.vocab.length, identifierHitsAddedChanged: out.idHits.length, identifierHitsPreservedV70: out.idHitsPreserved.length, roleOrQuestionHits: out.roleHits.length, filterControlsOnPortfolio: out.filters.length, operatorSelectInTopbar: out.routes.filter(r => r.topbarOperatorSelect).length, operatorSelectInReviewBar: out.routes.filter(r => r.reviewOperatorSelect).length, designValueScan: `independent set of ${out.dvScan.independentPatterns} replay figures (same as the tagger's: ${out.dvScan.sameAsTagger}); ${out.dvScan.occurrences} occurrences scanned on all routes and ${out.dvScan.drawersOpened} drawers; unlabelled ${out.dvScan.unlabelled.length}; unrelated matches on preserved v7.0 pages (exempt, not replay figures): ${(out.dvScan.preservedCoincidences || []).length}`, rev6TabOrder: out.rev6.tabOrderOk, rev7EvMeasure: out.rev7.evMeasure, rev7RuiruNameplate: out.rev7.ruiruNameplate, rev6DesignValueLabels: out.rev6.dvOk && Object.values(out.rev6.dvPlanDrawer).every(Boolean) && Object.values(out.rev6.overviewNote).every(Boolean), rev6RuiruWording: out.rev6.ruiruOk, rev6OldRoute: out.rev6.oldRouteRedirect, switchCasesOk: Object.values(out.switches).filter(x => Object.entries(x).filter(([k]) => /Ok$|Shown$|announced|focusKept/.test(k)).every(([, v]) => v)).length + '/' + Object.keys(out.switches).length, drawerOk: Object.values(out.drawer).every(Boolean), focusVisible: out.focus.filter(f => f.visible).length + '/' + out.focus.length, contrastPass: out.contrast.filter(c => c.pass).length + '/' + out.contrast.filter(c => !c.missing).length, preservedIdentical: out.preservedText.filter(p => p.identicalAfterNames).length + '/' + out.preservedText.length, oracleShipped: out.oracleShipped, hand_typed_figures: HT.count, handTypedCode: HT.hits.length, handTypedManifest: HT.manifest_count, manifestStringsScanned: HT.manifest_strings_scanned, handTypedAllowList: HT.allow_total, handTypedAllowUnused: HT.allow_unused.length, placeholdersFig: out.placeholders.fig, placeholdersRec: out.placeholders.rec, placeholderStrings: out.placeholders.strings, unresolvedPlaceholders: out.placeholders.unresolved.length };
writeFileSync(path.join(here, 'audit-results.json'), JSON.stringify(out, null, 1));
console.log(JSON.stringify(out.summary, null, 1));
