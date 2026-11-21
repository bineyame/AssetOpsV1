/* IA-2a r1 quantity check (D-IA.54), jsdom: a total and a part of it on one screen add up there, on every live route.
   Every live route x 3 operators x the plan states (as proposed, approved, sent back) x the default case and the non-default case of
   D-IA.50 (Lakeside 6500 + letter No, Harvest aggregation No, Metro TOU No). Per screen the figures are grouped by key: IA-built markup
   declares data-qty="<key>" and data-qty-role="total|part" (its money is the element's text); reviewed markup is declared in this check's
   own QTY table by selector and money pattern. Assert: where a key's total and every part are shown, the parts sum to the total; in Draft
   the release line has no money and the clause alone is at most the total; totals of one key are equal across the routes of a scenario; a
   QTY row whose selector finds nothing on a route it names fails (never dormant). The sweep's pairs are listed in the packet.
   Run: node tools/qty_check.cjs   Plants: QTY_PLANT=clause (the released-at-creation clause omitted), wait (the clause sums the waiting
   items instead). Both must fail on all three operators. */
const { boot, OPS, liveRoutes } = require('./ia_crawl.cjs');
const PLANT = process.env.QTY_PLANT || '';
const PLANTS = {
  clause: 'iaPlanReleased = () => "";',
  wait: 'iaPlanReleased = function (op) { const ids = planCaseIds(op).filter(id => !releaseOf(op, id).at); return ids.length ? `<p class="ia-plan-released" data-qty="plan-spend" data-qty-role="part">Waiting: ${ids.map(id => `${itemProse(op, id)} (${usd(releaseOf(op, id).spend)})`).join("; ")}.</p>` : ""; };' };
if (PLANT && !PLANTS[PLANT]) { console.error(`qty_check: unknown plant ${PLANT}`); process.exit(2); }
const MONEY = /[−-]?\$[\d,]+(?:\.\d+)?/g;
const num = s => { const m = String(s).replace(/,/g, ''); return (/^[−-]/.test(m) ? -1 : 1) * parseFloat(m.replace(/^[−-]?\$/, '')); };
const moneys = t => (String(t).match(MONEY) || []).map(num);
const PLAN_ROUTES = ['plan', 'plan/left-out', 'plan/review', 'plan/history'];
/* reviewed markup, by selector (D-IA.54 row 1). pick(text) returns the money of the role */
const QTY = [
  { key: 'plan-spend', role: 'total', routes: PLAN_ROUTES, sel: '.ux-planband .ux-kpi-v', pick: t => moneys(t).slice(0, 1) },
  { key: 'plan-spend', role: 'part', routes: PLAN_ROUTES, sel: '.approval-releases', pick: t => { const m = t.match(/([−-]?\$[\d,]+(?:\.\d+)?) of one-off spend/); return m ? [num(m[1])] : []; } },
  { key: 'plan-spend', role: 'total', routes: ['portfolio'], sel: '.ux-kpi', text: /^Plan spend/, within: '.ux-kpi-v', pick: t => moneys(t).slice(0, 1) }];
const PICK = { lakeside: [['sw-budget', '6500'], ['sw-loi', 'no']], harvest: [['sw-agg', 'no']], metro: [['sw-tou', 'no']] };
const fails = []; let screens = 0, figs = 0;
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const t0 = Date.now();
  for (const op of OPS) for (const nd of [false, true]) for (const st of ['proposed', 'approved', 'sent back']) {
    const B = await boot(op, 'plan'), { w, doc } = B, tag = `${B.opName} · ${nd ? 'non-default case' : 'default case'} · ${st}`;
    if (PLANT) { w.eval(PLANTS[PLANT]); w.eval('render()'); await sleep(20); }
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
      await B.go(r.id); screens++;
      const at = `${tag} · ${r.id}`, root = doc.querySelector('#app') || doc.body, by = {};
      const add = (key, role, vals) => { (by[key] = by[key] || { total: [], part: [], shown: 0 })[role].push(...vals); figs += vals.length; };
      root.querySelectorAll('[data-qty]').forEach(e => add(e.dataset.qty, e.dataset.qtyRole === 'total' ? 'total' : 'part', moneys(e.textContent)));
      for (const q of QTY) { if (!q.routes.includes(r.id)) continue;
        const hit = [...root.querySelectorAll(q.sel)].find(e => !q.text || q.text.test(e.textContent.trim()));
        if (!hit) { fails.push(`${at}: QTY row ${q.key}/${q.role} selector "${q.sel}" finds nothing`); continue; }
        add(q.key, q.role, q.pick((q.within ? hit.querySelector(q.within) || { textContent: '' } : hit).textContent)); }
      for (const [key, g] of Object.entries(by)) {
        if (g.total.length > 1 && g.total.some(x => x !== g.total[0])) fails.push(`${at}: two totals of ${key} differ: ${g.total.join(', ')}`);
        if (!g.total.length) continue;
        const T = g.total[0]; (totalsOf[key] = totalsOf[key] || []).push([r.id, T]);
        const lineMoney = root.querySelector('.approval-releases') ? moneys(root.querySelector('.approval-releases').textContent).length > 0 : true, sum = Math.round(g.part.reduce((a, b) => a + b, 0) * 100) / 100;
        if (!g.part.length) continue;
        if (key === 'plan-spend' && !lineMoney) { if (sum > T) fails.push(`${at}: Draft: the clause $${sum} exceeds the total $${T}`); }
        else if (sum !== T) fails.push(`${at}: the parts of ${key} sum to $${sum} but its total is $${T} (parts ${g.part.map(x => '$' + x).join(' + ')})`); }
      if (B.errors.length) fails.push(`${at}: script error ${B.errors[0]}`);
    }
    for (const [key, L] of Object.entries(totalsOf)) L.forEach(([id, x]) => { if (x !== L[0][1]) fails.push(`${tag}: total of ${key} is $${x} on ${id}, $${L[0][1]} on ${L[0][0]}`); });
    w.close();
  }
  console.log(`qty_check · ${screens} screens (3 operators x 2 cases x 3 states x every live route) · ${figs} figures grouped · ${((Date.now() - t0) / 1000).toFixed(1)} s${PLANT ? ` · plant ${PLANT}` : ''}`);
  if (fails.length) { console.log(`failing operators: ${[...new Set(fails.map(f => f.split(' · ')[0]))].join(', ')}`);
    console.log(`${fails.length} FAIL\n` + fails.slice(0, 12).map(f => '  ' + f).join('\n')); console.log('qty_check: FAIL'); process.exit(1); }
  console.log('qty_check: PASS'); process.exit(0);
})();
