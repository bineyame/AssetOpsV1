/* IA-2a r1 quantity check (D-IA.54), jsdom: a total and a part of it on one screen add up there, on every live route.
   Every live route x 3 operators x the plan states (as proposed, approved, sent back) x the default case and the non-default case of
   D-IA.50 (Lakeside 6500 + letter No, Harvest aggregation No, Metro TOU No). Per screen the figures are grouped by key: IA-built markup
   declares data-qty="<key>" and data-qty-role="total|part" (its money is the element's text); reviewed markup is declared in this check's
   own QTY table by selector and money pattern. Assert: where a key's total and every part are shown, the parts sum to the total; in Draft
   the release line has no money and the clause alone is at most the total; totals of one key are equal across the routes of a scenario; a
   QTY row whose selector finds nothing on a route it names fails (never dormant). The sweep's pairs are listed in the packet.
   Run: node tools/qty_check.cjs   Plants: QTY_PLANT=clause (the released-at-creation clause omitted), wait (the clause sums the waiting
   items instead). Both must fail on all three operators. D-IA.60: QTY_PLANT=gap (the $25 removed from the Overview gap tile) and items (one valued item row dropped) must fail too (gap: Lakeside only has a Grow part).
   IA-2b1 unit 2 (spec-IA-2b §8, D-IA.71, D-IA.68), live on IA-2a's routes now and on the lists once they land:
   count mode: an element with data-qty-kind="count" holds one integer (none or more than one fails); its key's parts sum to its total and
     its totals are equal across a scenario's routes (the rules above); a key mixing count and money elements fails;
   format mode (D-IA.59): per screen and key, every money string of IA data-qty figures has one number of decimals; a key with a member in
     the reviewed QTY table is printed "format deferred to IA-2e (D-IA.59)" with its count of screens, never passed silently;
   EQUAL: per scenario, the total of the first key equals the total of the second ([['sites:gap:', 'overview-gap']], the operator's own
     gap at scope all, unfiltered); a row whose keys are not both shown fails once IA-2b1 is landed, else prints "IA-2b1 not landed; dormant".
   IA-2b1 plants (DOM, applied after each route renders, on the lists' markup; a plant that finds nothing on the whole run exits 2):
   counts (the Actions "Returned" tile dropped), tilecount (the Actions tile shows the Released count), sitegap (one Sites row's gap part
   dropped), listcents (the Sites rows' gaps written with cents, the tile whole), gapnet (the Sites gap tile sums the shortfalls only). */
const { boot, OPS, liveRoutes } = require('./ia_crawl.cjs');
const PLANT = process.env.QTY_PLANT || '';
const PLANTS = {
  clause: 'iaPlanReleased = () => "";',
  wait: 'iaPlanReleased = function (op) { const ids = planCaseIds(op).filter(id => !releaseOf(op, id).at); return ids.length ? `<p class="ia-plan-released" data-qty="plan-spend" data-qty-role="part">Waiting: ${ids.map(id => `${itemProse(op, id)} (${usd(releaseOf(op, id).spend)})`).join("; ")}.</p>` : ""; };' };
/* DOM plants, applied after each route renders (D-IA.60): gap removes the $25 part from the Overview gap tile; items drops one valued item row */
const DOM_PLANTS = {
  gap: d => { const k = [...d.querySelectorAll('.ux-kpi')].find(e => /^Gap to target/.test(e.textContent.trim())), x = k && k.querySelector('.ux-kpi-s'); if (x) x.textContent = x.textContent.replace(/Grow\s*[−-]\$25\s*·\s*/, ''); },
  items: d => { const r = [...d.querySelectorAll('.ux-itemrow')].find(e => [...e.querySelectorAll('.ux-it-c.ux-num')].slice(1).some(c => /^[+−-]\$/.test(c.textContent.trim()))); if (r) r.remove(); },
  /* IA-2b1 (D-IA.71), on the list markup of spec-IA-2b §3.2 and §4 */
  counts: d => { const t = tileOf(d, 'actions', 'Returned'); if (t) { t.remove(); HITS.n++; } },
  tilecount: d => { const t = tileOf(d, 'actions', 'Actions'), r = tileOf(d, 'actions', 'Released'), v = t && t.querySelector('[data-qty]'), rv = r && r.querySelector('[data-qty]'); if (v && rv) { v.textContent = rv.textContent; HITS.n++; } },
  sitegap: d => { const e = d.querySelector('[data-ia-list="sites"] tbody tr[data-row] [data-qty^="sites:gap:"][data-qty-role="part"]'); if (e) { e.remove(); HITS.n++; } },
  listcents: (d, w) => { d.querySelectorAll('[data-ia-list="sites"] tbody tr[data-row]').forEach(tr => { const e = tr.querySelector('[data-qty^="sites:gap:"][data-qty-role="part"]'); if (!e) return;
    const v = w.eval(`siteM(${JSON.stringify(tr.dataset.row)}).period.variance`); e.textContent = fmtC(v); HITS.n++; }); },
  gapnet: d => { const s = d.querySelector('[data-ia-list="sites"]'), t = s && s.querySelector('[data-qty^="sites:gap:"][data-qty-role="total"]'); if (!t) return;
    const neg = [...s.querySelectorAll('[data-qty^="sites:gap:"][data-qty-role="part"]')].flatMap(e => moneys(e.textContent)).filter(x => x < 0); t.textContent = fmtW(neg.reduce((a, b) => a + b, 0)); HITS.n++; } };
const HITS = { n: 0 }, LIST_PLANTS = ['counts', 'tilecount', 'sitegap', 'listcents', 'gapnet'];
const tileOf = (d, key, label) => { const s = d.querySelector(`[data-ia-list="${key}"]`); return s ? [...s.querySelectorAll('[data-level="L1"] .ux-kpi')].find(e => e.querySelector('.ux-kpi-l')?.textContent.trim() === label) : null; };
const fmtW = v => `${v < 0 ? '−' : v > 0 ? '+' : ''}$${Math.round(Math.abs(v)).toLocaleString('en-US')}`, fmtC = v => `${v < 0 ? '−' : v > 0 ? '+' : ''}$${Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
/* D-IA.68: totals that must be equal within a scenario */
const EQUAL = [['sites:gap:', 'overview-gap']];
if (PLANT && !PLANTS[PLANT] && !DOM_PLANTS[PLANT]) { console.error(`qty_check: unknown plant ${PLANT}`); process.exit(2); }
const MONEY = /[−-]?\$[\d,]+(?:\.\d+)?/g;
const num = s => { const m = String(s).replace(/,/g, ''); return (/^[−-]/.test(m) ? -1 : 1) * parseFloat(m.replace(/^[−-]?\$/, '')); };
const moneys = t => (String(t).match(MONEY) || []).map(num);
const decs = t => (String(t).match(MONEY) || []).map(m => (m.match(/\.(\d+)$/) || ['', ''])[1].length);
const ints = t => String(t).replace(MONEY, ' $ ').match(/\d[\d,]*(?:\.\d+)?/g) || [];
const PLAN_ROUTES = ['plan', 'plan/left-out', 'plan/review', 'plan/history'];
/* reviewed markup, by selector (D-IA.54 row 1). pick(text) returns the money of the role */
const QTY = [
  { key: 'plan-spend', role: 'total', routes: PLAN_ROUTES, sel: '.ux-planband .ux-kpi-v', pick: t => moneys(t).slice(0, 1) },
  { key: 'plan-spend', role: 'part', routes: PLAN_ROUTES, sel: '.approval-releases', pick: t => { const m = t.match(/([−-]?\$[\d,]+(?:\.\d+)?) of one-off spend/); return m ? [num(m[1])] : []; } },
  /* D-IA.60 L5: the Overview gap ($852 = $827 + $25) and the Items sum ("$1,520 in all" = the valued item rows' one-off costs), each its own key (D-IA.54) */
  { key: 'overview-gap', role: 'total', routes: ['portfolio'], sel: '.ux-kpi', text: /^Gap to target/, within: '.ux-kpi-v', pick: t => moneys(t).slice(0, 1) },
  { key: 'overview-gap', role: 'part', routes: ['portfolio'], sel: '.ux-kpi', text: /^Gap to target/, within: '.ux-kpi-s', pick: t => moneys(t) },
  { key: 'plan-items', role: 'total', routes: ['plan'], sel: '*', text: /in all/, pick: t => { const m = t.match(/([−-]?\$[\d,]+(?:\.\d+)?) in all/); return m ? [num(m[1])] : []; } },
  { key: 'plan-items', role: 'part', routes: ['plan'], sel: '.ux-itemrow', all: true, pickRow: row => { const c = [...row.querySelectorAll('.ux-it-c.ux-num')].map(e => e.textContent.trim()); return c.slice(1).some(x => /^[+−-]\$/.test(x)) ? moneys(c[0]).slice(0, 1) : []; } },
  { key: 'plan-spend', role: 'total', routes: ['portfolio'], sel: '.ux-kpi', text: /^Plan spend/, within: '.ux-kpi-v', pick: t => moneys(t).slice(0, 1) }];
const PICK = { lakeside: [['sw-budget', '6500'], ['sw-loi', 'no']], harvest: [['sw-agg', 'no']], metro: [['sw-tou', 'no']] };
const fails = []; let screens = 0, figs = 0;
const MODE = { count: new Set(), format: new Set(), deferred: {}, equal: [] }, QTY_KEYS = new Set(QTY.map(q => q.key));
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const t0 = Date.now();
  for (const op of OPS) for (const nd of [false, true]) for (const st of ['proposed', 'approved', 'sent back']) {
    const B = await boot(op, 'plan'), { w, doc } = B, tag = `${B.opName} · ${nd ? 'non-default case' : 'default case'} · ${st}`;
    if (PLANT && PLANTS[PLANT]) { w.eval(PLANTS[PLANT]); w.eval('render()'); await sleep(20); }
    const click = async sel => { const e = doc.querySelector(sel); if (!e) return false; e.click(); await sleep(20); return true; };
    if (nd) for (const [name, val] of PICK[op]) { const r = doc.querySelector(`input[name="${name}"][value="${val}"]`); if (!r) { fails.push(`${tag}: no switch ${name}=${val}`); continue; } r.checked = true; r.dispatchEvent(new w.Event('change', { bubbles: true })); await sleep(10); }
    if (st === 'approved' && !(await click('.ux-planband [data-ux-act="approve-plan"]') && await click('#uxact [data-ux-act-go]'))) { fails.push(`${tag}: Approve did not run`); continue; }
    if (st === 'sent back') {
      if (!await click('.ux-planband [data-ux-act="send-back"]')) { fails.push(`${tag}: no Send back`); continue; }
      const ta = doc.getElementById('ux-sb-reason'), sel = doc.getElementById('ux-sb-way'), opt = sel && [...sel.options].find(o => o.value);
      if (!ta || !opt) { fails.push(`${tag}: the Send back dialog lacks its reason or a trade-off`); continue; }
      ta.value = 'The crew cannot do both visits'; sel.value = opt.value; for (const e of [ta, sel]) for (const t of ['input', 'change']) e.dispatchEvent(new w.Event(t, { bubbles: true }));
      if (!await click('#uxact [data-ux-act-go]')) { fails.push(`${tag}: Send back did not run`); continue; } }
    const totalsOf = {};
    for (const r of liveRoutes(w, op)) {
      await B.go(r.id); screens++; if (DOM_PLANTS[PLANT]) DOM_PLANTS[PLANT](doc, w);
      const at = `${tag} · ${r.id}`, root = doc.querySelector('#app') || doc.body, by = {};
      const add = (key, role, vals, kind = 'money', reviewed = true) => { const g = (by[key] = by[key] || { total: [], part: [], shown: 0, kinds: new Set(), dec: new Set(), qty: false }); g[role].push(...vals); g.kinds.add(kind); if (reviewed) g.qty = true; figs += vals.length; };
      root.querySelectorAll('[data-qty]').forEach(e => { const role = e.dataset.qtyRole === 'total' ? 'total' : 'part', k = e.dataset.qty;
        if (e.dataset.qtyKind === 'count') { const n = ints(e.textContent); if (n.length !== 1 || /\./.test(n[0])) fails.push(`${at}: the count ${k}/${role} "${e.textContent.trim().slice(0, 60)}" holds ${n.length} numbers${n.length === 1 ? ' (not a whole number)' : ''}, expected one integer`);
          add(k, role, n.length === 1 ? [+n[0].replace(/,/g, '')] : [], 'count', false); MODE.count.add(k); return; }
        add(k, role, moneys(e.textContent), 'money', false); decs(e.textContent).forEach(x => by[k].dec.add(x)); });
      for (const q of QTY) { if (!q.routes.includes(r.id)) continue;
        if (q.all) { const rows = [...root.querySelectorAll(q.sel)]; if (!rows.length) { fails.push(`${at}: QTY row ${q.key}/${q.role} selector "${q.sel}" finds nothing`); continue; } add(q.key, q.role, rows.flatMap(q.pickRow)); continue; }
        const hit = [...root.querySelectorAll(q.sel)].find(e => !q.text || q.text.test(e.textContent.trim()));
        if (!hit) { fails.push(`${at}: QTY row ${q.key}/${q.role} selector "${q.sel}" finds nothing`); continue; }
        add(q.key, q.role, q.pick((q.within ? hit.querySelector(q.within) || { textContent: '' } : hit).textContent)); }
      for (const [key, g] of Object.entries(by)) {
        if (g.kinds.size > 1) fails.push(`${at}: the key ${key} mixes count and money figures`);
        /* format mode (D-IA.59): one number of decimals per screen and key over IA data-qty money; a key with a reviewed QTY member is deferred */
        if (!g.kinds.has('count') && g.dec.size) { if (g.qty || QTY_KEYS.has(key)) MODE.deferred[key] = (MODE.deferred[key] || 0) + 1;
          else { MODE.format.add(key); if (g.dec.size > 1) fails.push(`${at}: the figures of ${key} are written with ${[...g.dec].sort().join(' and ')} decimals (one form per key on a screen, D-IA.59)`); } }
        if (g.total.length > 1 && g.total.some(x => x !== g.total[0])) fails.push(`${at}: two totals of ${key} differ: ${g.total.join(', ')}`);
        if (!g.total.length) continue;
        const T = g.total[0]; (totalsOf[key] = totalsOf[key] || []).push([r.id, T]);
        const lineMoney = root.querySelector('.approval-releases') ? moneys(root.querySelector('.approval-releases').textContent).length > 0 : true, sum = Math.round(g.part.reduce((a, b) => a + b, 0) * 100) / 100;
        if (!g.part.length) continue;
        if (key === 'plan-spend' && !lineMoney) { if (sum > T) fails.push(`${at}: Draft: the clause $${sum} exceeds the total $${T}`); }
        else if (sum !== T) fails.push(`${at}: the parts of ${key} sum to $${sum} but its total is $${T} (parts ${g.part.map(x => '$' + x).join(' + ')})`); }
      if (B.errors.length) fails.push(`${at}: script error ${B.errors[0]}`);
    }
    /* EQUAL (D-IA.68): within the scenario, the first key's total equals the second's */
    for (const [a, b] of EQUAL) { const A = (totalsOf[a] || [])[0], Bt = (totalsOf[b] || [])[0];
      if (A && Bt) { MODE.equal.push(`${tag}: ${a} ${A[1]} = ${b} ${Bt[1]}`); if (A[1] !== Bt[1]) fails.push(`${tag}: EQUAL ${a} is $${A[1]} on ${A[0]}, ${b} is $${Bt[1]} on ${Bt[0]}`); }
      else if (w.eval("IA_LANDED.has('IA-2b1')")) fails.push(`${tag}: EQUAL ${a} = ${b} not measured (${[A ? '' : a + ' not shown', Bt ? '' : b + ' not shown'].filter(Boolean).join(', ')})`);
      else MODE.equal.push('IA-2b1 not landed; dormant'); }
    for (const [key, L] of Object.entries(totalsOf)) L.forEach(([id, x]) => { if (x !== L[0][1]) fails.push(`${tag}: total of ${key} is $${x} on ${id}, $${L[0][1]} on ${L[0][0]}`); });
    w.close();
  }
  if (LIST_PLANTS.includes(PLANT) && !HITS.n) { console.log(`qty_check (plant ${PLANT}): the plant found nothing to change on any screen`); process.exit(2); }
  const dk = Object.entries(MODE.deferred), eqd = MODE.equal.filter(x => /dormant/.test(x)).length, eqm = MODE.equal.filter(x => !/dormant/.test(x));
  console.log(`count mode: ${MODE.count.size} key(s)${MODE.count.size ? ' · ' + [...MODE.count].slice(0, 24).join(', ') : ''}`);
  console.log(`format mode: ${MODE.format.size} key(s)${MODE.format.size ? ' · ' + [...MODE.format].slice(0, 24).join(', ') : ''}`);
  console.log(`format deferred to IA-2e (D-IA.59): ${dk.length} key(s)${dk.length ? ' · ' + dk.map(([k, n]) => `${k} on ${n} screens`).join(', ') : ''}`);
  console.log(eqd ? `EQUAL sites:gap: = overview-gap: IA-2b1 not landed; dormant (${eqd} scenarios)` : `EQUAL: ${eqm.length} scenario(s) measured · ${eqm.filter(x => / default case · proposed/.test(x)).join(' | ')}`);
  console.log(`qty_check · ${screens} screens (3 operators x 2 cases x 3 states x every live route) · ${figs} figures grouped · ${((Date.now() - t0) / 1000).toFixed(1)} s${PLANT ? ` · plant ${PLANT}` : ''}`);
  if (fails.length) { console.log(`failing operators: ${[...new Set(fails.map(f => f.split(' · ')[0]))].join(', ')}`);
    console.log(`${fails.length} FAIL\n` + fails.slice(0, 12).map(f => '  ' + f).join('\n')); console.log('qty_check: FAIL'); process.exit(1); }
  console.log('qty_check: PASS'); process.exit(0);
})();
