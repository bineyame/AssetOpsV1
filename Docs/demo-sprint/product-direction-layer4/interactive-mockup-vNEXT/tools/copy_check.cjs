/* Copy check (UI/UX guide §7.7; copy review round 4): faults that word replacements can create, read from the rendered
   prose segments of every loop screen and sampled evidence drawer (tools/rendered-text.json, written by render_text.cjs):
   1. a doubled word ("service service", "the the");
   2. a phrase repeated right after itself ("hours without backup supply with no backup supply");
   3. a space before an apostrophe or punctuation ("mini-grid ’s", "word ,");
   4. a doubled sign ("+ +$", "− −").
   Run: node tools/render_text.cjs && node tools/copy_check.cjs     Plant test: COPY_PLANT=1 (one example of each; must fail).
   IA-2a block (spec §5.1.6, D-IA.52 R16; Q4: a new block here, its own jsdom render, independent of rendered-text.json): with IA-2a in
   IA_LANDED or IA_FORCE_LANDED=IA-2a (tools/fixtures/plan_stub.js loads when the window has no shapePlan), per operator and on plan,
   plan/left-out, plan/review, plan/history, as proposed in the default case, after the non-default pick (Lakeside 6500/No, Harvest No,
   Metro No) and after Approve: every text node and aria-label inside [data-shape="plan"] and the tab row that is not a string of the reviewed
   pages in the same state (planScreen() and whatChangedScreen(), plainWords applied as render() does; the reviewed drawer chrome of
   uxDrawer around the §5.1.6 title; of the tab row, the tab labels (its aria-label is the IA-1 tab chrome); the act log's own toasts and by-lines, the inbox row's form) must match the §5.1.6 list below. Otherwise it prints
   "IA-2a not landed; dormant". Plant COPY_PLANT=plan (this block only): a stray sentence in the plan's L1. */
const fs = require('fs'), path = require('path');
let recs = JSON.parse(fs.readFileSync(path.join(__dirname, 'rendered-text.json'), 'utf8'));
if (process.env.COPY_PLANT && process.env.COPY_PLANT !== 'plan') recs = recs.map(r => r.id === 'portfolio' && r.op === 'lakeside' ? { ...r, segments: [...r.segments, 'Fails the evening service service limit', 'Hours without backup supply with no backup supply: 0 h', 'How a mini-grid ’s economics are built', 'Worked sum: $883 + +$19.68', 'Energy matches the occupancy model (0 more buses.6%)', 'Repair or claim · its record connector fault', 'Maintenance lead · /'] } : r);
const RULES = [
  ['doubled word', /\b([A-Za-z]{2,})[ ]+\1\b/i],
  ['phrase repeated after itself', /\b([A-Za-z]{4,} [A-Za-z]{4,})\b[^¶]{0,24}?\b\1\b/i], /* ¶ marks a line break or a note under a label */
  ['space before an apostrophe or punctuation', /[A-Za-z)]\s+(?:[’'](?=s\b)|[,;:!?](?=\s|$)|\.(?=\s|$))/],
  ['placeholder left by removed text (r2 M5)', /\bits record\b|·\s*\/|(^|\s)[·\/]\s*$/],
  ['doubled sign', /(?:^|\s)[+−-]\s*[+−-]\s?\$?\d/],
  ['number broken by words (a rewrite rule split a figure; REVIEW-decision-page L7)', /\b\d+ [a-z]+(?: [a-z]+){0,3}\.\d/],
];
const ALLOW = [/\b(\d+)\s+\1\b/, /\bthat that\b/i];
const hits = [];
for (const r of recs) { if (!r.loop) continue;
  for (const t of r.segments || []) for (const [kind, re] of RULES) { const m = t.match(re); if (m && !ALLOW.some(a => a.test(m[0]))) hits.push({ op: r.op, id: r.id, kind, match: m[0], at: t.slice(0, 160) }); } }
const uniq = [...new Map(hits.map(h => [h.kind + '|' + h.at, h])).values()];
console.log(JSON.stringify({ planted: !!process.env.COPY_PLANT && process.env.COPY_PLANT !== 'plan', segments: recs.reduce((a, r) => a + (r.loop ? (r.segments || []).length : 0), 0), hits: uniq.length, by_kind: uniq.reduce((a, h) => (a[h.kind] = (a[h.kind] || 0) + 1, a), {}), first: uniq.slice(0, 40) }, null, 1));
/* the IA-2a block: the §5.1.6 list, this check's own words */
const NUM = '\\d[\\d,]*', MONTH = '(January|February|March|April|May|June|July|August|September|October|November|December)';
const PLAN_COPY = [
  ['tab', /^(Items|Left out|Review|History)$/],
  ['step', /^(Draft|Proposed|Approved|Closed)$/],
  ['stepper name', /^Where this plan is$/],
  ['crew tile label', new RegExp(`^[A-Z][a-z]+(?: [a-z]+)* used(?:, ${MONTH})?$`)],
  ['crew tile value', new RegExp(`^${NUM}$|^of ${NUM}$`)],
  ['crew meter name', new RegExp(`^${NUM} of ${NUM} [a-z]+(?: [a-z]+)*(?: in ${MONTH})?$`)],
  ['opener and drawer title', /^Release thresholds$/],
  ['case line', /^Showing the case you chose: .+\.$|^Change the case$/],
  ['History', new RegExp(`^Versions and approvals$|^Version ${NUM}, (draft|proposed|approved|closed|revised)$|^Version ${NUM} proposed$|^Opened within the executive’s limits$|^The system · \\d{1,2} [A-Z][a-z]{2}$|^Changes made here are shown in this demonstration only\\.$`)]
];
async function planCopy() {
  const { boot, OPS, planStub, sleep } = require('./ia_crawl.cjs');
  const PICK = { lakeside: [['sw-budget', '6500'], ['sw-loi', 'no']], harvest: [['sw-agg', 'no']], metro: [['sw-tou', 'no']] };
  const ROUTES = ['plan', 'plan/left-out', 'plan/review', 'plan/history'], sq = t => String(t || '').replace(/\s+/g, ' ').trim();
  const strings = root => { const out = []; const tw = root.ownerDocument.createTreeWalker(root, 4); let n; while ((n = tw.nextNode())) { if (n.parentElement && n.parentElement.closest('script,style')) continue; const t = sq(n.nodeValue); if (t && /[A-Za-z0-9]/.test(t)) out.push(t); }
    root.querySelectorAll('[aria-label]').forEach(e => out.push(sq(e.getAttribute('aria-label')))); if (root.getAttribute && root.getAttribute('aria-label')) out.push(sq(root.getAttribute('aria-label'))); return out; };
  const stray = [], seen = { n: 0 }, listed = {}; let first = true;
  for (const op of OPS) {
    const B = await boot(op, 'plan'), { w, doc, go } = B;
    if (first) { first = false; if (!w.eval("IA_LANDED.has('IA-2a')")) { console.log('copy_check IA-2a block: IA-2a not landed; dormant'); B.dom.window.close(); return 0; } }
    planStub(w); if (process.env.COPY_PLANT === 'plan') w.eval(`{ const _s = shapePlan; shapePlan = (ctx, tab) => _s(ctx, tab).replace('<div data-level="L1">', '<div data-level="L1"><p>Approve this quickly before the window closes.</p>'); }`);
    w.eval('render()'); await sleep(20);
    /* the reviewed strings in the window's current state */
    const ref = () => { const t = doc.createElement('template'); t.innerHTML = w.eval(`planScreen() + whatChangedScreen() + uxDrawer('ia-ref', 'Release thresholds', '') + (uxMock().log || []).map(e => '<p>' + e.toast + '</p><p>' + e.by + ' · ' + (hhmm(e.at) || '') + '</p>').join('')`); w.eval('plainWords')(t.content); const d = doc.createElement('div'); d.appendChild(t.content); return new Set(strings(d)); };
    const pass = async state => { for (const r of ROUTES) { await go(r); const R = ref(), S = doc.querySelector('#ia-root [data-shape="plan"]'), T = doc.querySelector('#ia-root nav.tabs');
      if (!S) { stray.push(`${B.opName} · #/${r} · ${state}: no [data-shape="plan"]`); continue; }
      for (const t of [...strings(S), ...(T ? [...T.querySelectorAll('a')].map(x => sq(x.textContent)) : [])]) { seen.n++; if (R.has(t)) continue; const hit = PLAN_COPY.find(([, re]) => re.test(t)); if (hit) { listed[hit[0]] = (listed[hit[0]] || 0) + 1; continue; } stray.push(`${B.opName} · #/${r} · ${state}: "${t.slice(0, 120)}"`); } } };
    await pass('as proposed');
    await go('plan'); for (const [name, val] of PICK[op]) { const i = doc.querySelector(`input[name="${name}"][value="${val}"]`); if (!i) { stray.push(`${B.opName}: no switch ${name}=${val}`); continue; } i.checked = true; i.dispatchEvent(new w.Event('change', { bubbles: true })); await sleep(10); }
    await pass('non-default case');
    await go('plan'); const a = doc.querySelector('.ux-planband [data-ux-act="approve-plan"]'); if (a) { a.click(); await sleep(10); const g = doc.querySelector('#uxact [data-ux-act-go]'); if (g) { g.click(); await sleep(20); } }
    if (!w.eval(`uxPlanState(${JSON.stringify(op)}).state === 'APPROVED'`)) stray.push(`${B.opName}: Approve did not take`);
    await pass('after Approve');
    if (B.errors.length) stray.push(`${B.opName}: script error ${B.errors[0]}`);
    B.dom.window.close();
  }
  const u = [...new Set(stray)];
  console.log(`copy_check IA-2a block: ${seen.n} strings on the four plan routes × 3 operators × 3 states, ${u.length} not in the reviewed pages or the §5.1.6 list (new strings matched per entry: ${PLAN_COPY.map(([k]) => `${k} ${listed[k] || 0}`).join(', ')})${u.length ? ' FAIL\n  ' + u.slice(0, 15).join('\n  ') : ''}`);
  return u.length ? 1 : 0;
}
(async () => { const planBad = await planCopy(); process.exit(uniq.length || planBad ? 1 : 0); })();
