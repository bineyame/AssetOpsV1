/* IA-2a plan shape check (spec §5.1.1 to §5.1.4, §5.1.8 row 1; D-IA.43, D-IA.44, D-IA.47, D-IA.50 R4/R15/R17, D-IA.51, D-IA.52 R7 to R10),
   jsdom. Runs only when IA_LANDED has IA-2a (or IA_FORCE_LANDED=IA-2a); otherwise prints one line and exits 0. Before 3(a) the window has
   no shapePlan, so tools/fixtures/plan_stub.js is loaded (ia_crawl planStub). For each operator (lakeside, harvest, metro), on the four
   routes plan, plan/left-out, plan/review, plan/history, in three states (as proposed with the default case; as proposed with a
   non-default case picked on Items through the switches' change events: Lakeside 6500/No, Harvest No, Metro No; after Approve):
   1 tabs: the tab row reads Items, Left out, Review, History in that order, with the current one (and only it) active;
   2 stepper: one ol.ia-plan-steps in L1 (none elsewhere) with 4 li reading Draft, Proposed, Approved, Closed; aria-current="step" on the
     li at the expected index and is-done on exactly the li before it (every step before the current, the markup of uxDecStatus, spec §5.1.3). The expected index is this check's own table (DRAFT 0, PROPOSED 1,
     REVISED 1, APPROVED 2, CLOSED 3) over the state read from MANIFEST.demo_workflow.plan_state, overridden by
     sessionStorage['l4-mock'].plan[op].state; never from iaPlanSteps, uxPlanState or iaForYou;
   3 L1 identity: L1's innerHTML is identical on the four tabs, in the default case and after the non-default pick. One normalisation:
     the case line's link is href="#sw-h" on Items and Left out (the switches are on the page) and href="#/plan" on Review and History;
     the check rewrites #sw-h to #/plan before comparing, nothing else. UX_QN is reset to 0 before every render;
   4 case line (D-IA.51): .ia-plan-case once in L1 on all four tabs after the non-default pick, absent in the default case;
   5 placement (§5.1.2, R9): each fingerprint is counted on the page and must be exactly 1 on the tab and level the table names, 0
     elsewhere: headings "Left out of the plan, and why" (Left out L2, its details open), "Listed beside the plan, not added" (Left out
     L3), "Actions that return to their creator in this case" (Left out L3, only in the non-default case on the three hosts), "Try another
     case" (the side panel on Items and Left out), "The plan’s review" (Review L2), "Versions and approvals" (History L2), the items
     heading "The plan for …: items and their Actions" (Items L2); aria-label "Where this plan is" and "The plan at a glance" (L1, every
     tab); .approval-releases (L1, every tab), .notice (L1, every tab, non-default case only), .ia-plan-case (item 4);
   6 no section.approval and no .meter, .metertrack, .meterhead in the plan shape; every class token naming a meter, track or bar inside
     it is ux-meterbar;
   7 the side panel (aside.side-panel) on Items and Left out only, once;
   8 the thresholds opener (button[data-ux-drawer="ia-plan-thresholds"], text "Release thresholds") once, in L1, and its drawer
     #ia-plan-thresholds once, inside [data-ia-drawers], data-open="false";
   9 caps (R7): no [data-ux-over] on Items, Left out and Review; History's visible rows (li not hidden) equal the operator's log entries
     (approve-plan or send-back in sessionStorage['l4-mock'].log) + 2, and are at least 3 after one Approve. PLAN_PLANT=cap is caught by
     the History assertion (its 2 rows exceed a cap of 1); Items, Left out and Review hold no list a cap of 1 must hide in every state;
   10 the release line: L1's .approval-releases outerHTML equals the one in a fresh planScreen() rendered into a template in the same
     state, with the page's one text pass (plainWords, the asset codes as plain names) applied to the reference as render() applies it to the page;
   11 R4: currentScreen().ctx.op equals LS.op (and the booted operator) on every render, also after switching the operator in the window;
   12 the sticky (R8): [data-ux-sticky] exactly once per tab; while PROPOSED, its Approve's data-ux-act equals the band's;
   13 the L1 cap (R10): the crew tiles expected from the manifest period (MANIFEST plan_state.period's two ends; each month with a
     stated limit: the first month's from derivedPlan(op).crew_visits_limit, a later month's from portfolio_constraints
     crew_visits_<mon>; none stated means the band's one crew tile) plus spend and value; L1's .ux-kpi count equals it and is at most 4;
     a period of 3 or more months fails "L1 cap of 4 exceeded, spec stop";
   14 R15: on each tab, Approve (the band's [data-ux-act=approve-plan], then the drawer's [data-ux-act-go]) leaves focus on the L1 chip
     [data-plan-state]; the toast's Undo (.ux-toast [data-ux-undo]) leaves it on the band's [data-ux-act=approve-plan]. jsdom has no
     layout, so offsetParent is shimmed on HTMLElement.prototype: null for a detached element, one under [hidden] or one in a sticky bar
     that is not .is-on (display:none in ux.css), else the parent element; without it uxFocusAction falls back to the H1;
   15 R17: iaPlanSteps on DRAFT, PROPOSED, REVISED, APPROVED, CLOSED gives cur 0, 1, 1, 2, 3 and the words Draft, Proposed, Approved,
     Closed; on BOGUS it throws "plan state BOGUS has no step".
   Run: IA_FORCE_LANDED=IA-2a node tools/plan_shape_check.cjs
   Plants: PLAN_PLANT=tabs|place|l1|approval|thr|stepdone|cap|revised|sticky (each must fail; each wraps a builder, so it works on the
   stub and on the real builders): tabs (History dropped from IA_TAB_GROUPS.Plan), place (Items L2 also holds planParts(op).left), l1
   (History's L1 without .approval-releases), approval (approvalPanel back in the Items aside), thr (no [data-ia-drawers]), stepdone (no
   is-done), cap (uxCapLists caps at 1), revised (REVISED maps to step 0), sticky (the sticky's Approve carries another data-ux-act). */
const { boot, planStub, sleep } = require('./ia_crawl.cjs');
const PLANT = process.env.PLAN_PLANT || '';
const wrap = (tabs, from, to) => `{ const _s = shapePlan; shapePlan = (ctx, tab) => { const h = _s(ctx, tab); return ${tabs}.includes(tab) ? h.replace(${from}, ${to}) : h; }; }`;
const PLANTS = {
  tabs: `{ const _g = IA_TAB_GROUPS.Plan; IA_TAB_GROUPS.Plan = ctx => _g(ctx).filter(([l]) => l !== 'History'); }`,
  place: wrap(`['items']`, `'</div><div data-level="L3">'`, `planParts(ctx.op).left + '</div><div data-level="L3">'`),
  l1: wrap(`['history']`, `/<p class="approval-releases">[\\s\\S]*?<\\/p>/`, `''`),
  approval: wrap(`['items']`, `'<aside class="side-panel" data-level="L3">'`, `(p => '<aside class="side-panel" data-level="L3">' + approvalPanel(ctx.op, p.P, p.budget))(planParts(ctx.op))`),
  thr: wrap(`['items', 'left-out', 'review', 'history']`, `/<div data-ia-drawers>[\\s\\S]*$/`, `'</section>'`),
  stepdone: `{ const _f = iaPlanStepper; iaPlanStepper = op => _f(op).replace(/is-done/g, ''); }`,
  cap: `uxCapLists = function (root) { root.querySelectorAll('ul.list').forEach((ul, i) => { if (ul.closest('.ux-drawer')) return; const li = [...ul.children].filter(x => x.tagName === 'LI'); if (li.length <= 1) return;
  if (!ul.id) ul.id = \`uxcap-\${i}\`; li.slice(1).forEach(x => { x.hidden = true; x.dataset.uxOver = ''; }); ul.insertAdjacentHTML('afterend', uxCapNote(li.length, 1, ul.id)); }); };`,
  revised: `{ const _f = iaPlanSteps; iaPlanSteps = st => st === 'REVISED' ? { ..._f('DRAFT') } : _f(st); }`,
  sticky: `{ const _f = uxPlanSticky; uxPlanSticky = (...a) => _f(...a).replace('data-ux-act="approve-plan"', 'data-ux-act="approve-plant"'); }`
};
if (PLANT && !PLANTS[PLANT]) { console.error(`plan_shape_check: unknown plant ${PLANT}`); process.exit(2); }
const fails = [], log = [];
const TABS = [['Items', 'plan', 'items'], ['Left out', 'plan/left-out', 'left-out'], ['Review', 'plan/review', 'review'], ['History', 'plan/history', 'history']];
const STEP = { DRAFT: 0, PROPOSED: 1, REVISED: 1, APPROVED: 2, CLOSED: 3 }, WORDS = ['Draft', 'Proposed', 'Approved', 'Closed'];
/* the non-default pick per operator (the hosts of the returned Actions, D-IA.48) and the way back to the default case */
const PICK = { lakeside: [['sw-budget', '6500'], ['sw-loi', 'no']], harvest: [['sw-agg', 'no']], metro: [['sw-tou', 'no']] };
const UNPICK = { lakeside: [['sw-budget', '5000'], ['sw-loi', 'yes']], harvest: [['sw-agg', 'yes']], metro: [['sw-tou', 'yes']] };
const OFFSET_SHIM = `Object.defineProperty(HTMLElement.prototype, 'offsetParent', { configurable: true, get() { if (!this.isConnected || this.closest('[hidden]')) return null; const s = this.closest('[data-ux-sticky]'); if (s && !s.classList.contains('is-on')) return null; return this.parentElement; } });`;
const norm = s => String(s || '').replace(/\s+/g, ' ').trim();
const mm = ym => { const [y, m] = ym.split('-').map(Number); return y * 12 + m - 1; };

(async () => {
  const OPS = ['lakeside', 'harvest', 'metro'];
  let first = true;
  for (const op of OPS) {
    const B = await boot(op, 'plan'), { w, doc, go } = B;
    if (first) { first = false; if (!w.eval(`IA_LANDED.has('IA-2a')`)) { console.log('IA-2a not landed; dormant'); B.dom.window.close(); process.exit(0); } }
    const stub = planStub(w);
    w.eval(OFFSET_SHIM);
    if (PLANT) w.eval(PLANTS[PLANT]);
    w.eval('UX_QN = 0; render()'); await sleep(20);
    const bad = m => fails.push(`${B.opName}: ${m}`);
    const PS = JSON.parse(w.eval('JSON.stringify(MANIFEST.demo_workflow.plan_state)'));
    const mock = () => { try { return JSON.parse(w.sessionStorage.getItem('l4-mock') || '{}'); } catch (e) { return {}; } };
    const expState = () => ((mock().plan || {})[op] || {}).state || PS.state;
    const logN = () => (mock().log || []).filter(e => e.op === op && (e.key === 'approve-plan' || e.key === 'send-back')).length;
    const visit = async route => { w.eval('UX_QN = 0'); await go(route); const c = w.eval('currentScreen().ctx.op'), l = w.eval('LS.op'); if (c !== l || l !== op) bad(`#/${route}: ctx.op ${c}, LS.op ${l}, booted ${op} (R4)`); };
    /* 15 R17 */
    const steps = w.eval(`JSON.stringify(['DRAFT', 'PROPOSED', 'REVISED', 'APPROVED', 'CLOSED'].map(s => { try { return iaPlanSteps(s); } catch (e) { return { err: String(e.message) }; } }))`);
    JSON.parse(steps).forEach((r, i) => { const s = ['DRAFT', 'PROPOSED', 'REVISED', 'APPROVED', 'CLOSED'][i]; if (r.err || r.cur !== STEP[s] || JSON.stringify(r.steps) !== JSON.stringify(WORDS)) bad(`iaPlanSteps(${s}) gives ${JSON.stringify(r)}, expected cur ${STEP[s]} and ${WORDS.join(', ')} (R17)`); });
    const bogus = w.eval(`(() => { try { iaPlanSteps('BOGUS'); return 'no throw'; } catch (e) { return String(e.message); } })()`);
    if (bogus !== 'plan state BOGUS has no step') bad(`iaPlanSteps('BOGUS'): ${bogus}, expected the throw "plan state BOGUS has no step" (R17)`);
    /* 13 the expected L1 tile count from the manifest */
    const [pa, pb] = PS.period.split(' to '), months = mm(pb || pa) - mm(pa) + 1;
    const limited = Number(w.eval(`(() => { const [a, b] = ${JSON.stringify([pa, pb])}, ms = [a, b].filter((v, i, l) => v && l.indexOf(v) === i), C = OPS[${JSON.stringify(op)}].t.portfolio_constraints;
      return ms.filter((ym, i) => (i === 0 ? derivedPlan(${JSON.stringify(op)}).crew_visits_limit : C['crew_visits_' + MONTHS[+ym.split('-')[1] - 1].slice(0, 3).toLowerCase()]) !== undefined).length; })()`));
    const tiles = 2 + (limited || 1);
    if (months >= 3) bad(`the plan period ${PS.period} has ${months} months: L1 cap of 4 exceeded, spec stop`);
    /* one page's assertions; returns L1's normalised innerHTML */
    const page = (label, tab, o) => {
      const [tname, route, key] = tab, at = `#/${route} (${label})`, S = doc.querySelector('#ia-root [data-shape="plan"]');
      if (!S) { bad(`${at}: no [data-shape="plan"]`); return ''; }
      const L1s = S.querySelectorAll('[data-level="L1"]'), L1 = L1s[0];
      if (L1s.length !== 1) { bad(`${at}: ${L1s.length} L1 regions`); if (!L1) return ''; }
      /* 1 tabs */
      const nav = doc.querySelector('#ia-root nav.tabs'), ts = nav ? [...nav.querySelectorAll('a')] : [];
      if (ts.map(a => norm(a.textContent)).join('|') !== TABS.map(t => t[0]).join('|')) bad(`${at}: tabs read "${ts.map(a => norm(a.textContent)).join(', ')}", expected Items, Left out, Review, History`);
      else { const act = ts.filter(a => a.classList.contains('active')).map(a => norm(a.textContent)); if (act.join() !== tname) bad(`${at}: active tab ${act.join(', ') || 'none'}, expected ${tname}`); }
      /* 2 stepper */
      const st = S.querySelectorAll('ol.ia-plan-steps'), es = expState(), cur = STEP[es];
      if (st.length !== 1 || !L1.contains(st[0])) bad(`${at}: ${st.length} steppers${st[0] && !L1.contains(st[0]) ? ', outside L1' : ''}`);
      else { const li = [...st[0].children].filter(x => x.tagName === 'LI');
        if (li.map(x => norm(x.textContent)).join('|') !== WORDS.join('|')) bad(`${at}: stepper reads ${li.map(x => norm(x.textContent)).join(', ')}`);
        const c = li.findIndex(x => x.getAttribute('aria-current') === 'step'), cn = li.filter(x => x.getAttribute('aria-current') === 'step').length;
        if (cn !== 1 || c !== cur) bad(`${at}: stepper current ${c} (${cn} marked), expected ${cur} for state ${es}`);
        const done = li.map((x, i) => x.classList.contains('is-done') ? i : -1).filter(i => i >= 0), want = [...Array(cur).keys()];
        if (done.join() !== want.join()) bad(`${at}: is-done on [${done.join(', ')}], expected [${want.join(', ')}] (state ${es})`); }
      /* 4 case line, 5 placement */
      const nd = o.nondefault, onAll = { items: 'L1', 'left-out': 'L1', review: 'L1', history: 'L1' };
      const heads = [...S.querySelectorAll('h2, .ux-h2')];
      const levelOf = e => e.closest('aside.side-panel') ? 'aside' : (e.closest('[data-level]') || { dataset: {} }).dataset.level || 'none';
      const FP = [
        ['heading "Left out of the plan, and why"', heads.filter(h => norm(h.textContent) === 'Left out of the plan, and why'), { 'left-out': 'L2' }],
        ['heading "Listed beside the plan, not added"', heads.filter(h => norm(h.textContent) === 'Listed beside the plan, not added'), { 'left-out': 'L3' }],
        ['heading "Actions that return to their creator in this case"', heads.filter(h => norm(h.textContent) === 'Actions that return to their creator in this case'), nd ? { 'left-out': 'L3' } : {}],
        ['heading "Try another case"', heads.filter(h => norm(h.textContent) === 'Try another case'), { items: 'aside', 'left-out': 'aside' }],
        ['heading "The plan’s review"', heads.filter(h => norm(h.textContent) === 'The plan’s review'), { review: 'L2' }],
        ['heading "Versions and approvals"', heads.filter(h => norm(h.textContent) === 'Versions and approvals'), { history: 'L2' }],
        ['the items heading', heads.filter(h => /^The plan for .+: items and their Actions$/.test(norm(h.textContent))), { items: 'L2' }],
        ['aria-label "Where this plan is"', [...S.querySelectorAll('[aria-label="Where this plan is"]')], onAll],
        ['aria-label "The plan at a glance"', [...S.querySelectorAll('[aria-label="The plan at a glance"]')], onAll],
        ['.approval-releases', [...S.querySelectorAll('.approval-releases')], onAll],
        ['.notice', [...S.querySelectorAll('.notice')], nd ? onAll : {}],
        ['.ia-plan-case', [...S.querySelectorAll('.ia-plan-case')], nd ? onAll : {}]
      ];
      FP.forEach(([n, els, where]) => { const want = where[key];
        if (els.length !== (want ? 1 : 0)) bad(`${at}: ${n} counted ${els.length}, expected ${want ? 1 : 0}`);
        else if (want && levelOf(els[0]) !== want) bad(`${at}: ${n} in ${levelOf(els[0])}, expected ${want}`); });
      const lo = FP[0][1][0]; if (key === 'left-out' && lo && !(lo.closest('details') || {}).open) bad(`${at}: "Left out of the plan, and why" is not open`);
      /* 6 no approval panel, no legacy meter */
      if (S.querySelector('section.approval') || doc.querySelector('#ia-root section.approval')) bad(`${at}: section.approval present`);
      const mt = S.querySelectorAll('.meter, .metertrack, .meterhead').length; if (mt) bad(`${at}: ${mt} legacy .meter/.metertrack/.meterhead`);
      const bars = [...new Set([...S.querySelectorAll('[class]')].flatMap(e => [...e.classList]).filter(c => /meter|track|(^|-)bars?$/.test(c)))].filter(c => c !== 'ux-meterbar');
      if (bars.length) bad(`${at}: bar classes other than ux-meterbar: ${bars.join(', ')}`);
      /* 7 side panel */
      const side = S.querySelectorAll('aside.side-panel').length, wantSide = key === 'items' || key === 'left-out' ? 1 : 0;
      if (side !== wantSide) bad(`${at}: ${side} side panels, expected ${wantSide}`);
      /* 8 thresholds opener and drawer */
      const op8 = [...S.querySelectorAll('button[data-ux-drawer="ia-plan-thresholds"]')];
      if (op8.length !== 1 || !L1.contains(op8[0]) || norm(op8[0].textContent) !== 'Release thresholds') bad(`${at}: thresholds opener ${op8.length}${op8[0] ? ` "${norm(op8[0].textContent)}"${L1.contains(op8[0]) ? '' : ' outside L1'}` : ''}, expected one "Release thresholds" in L1`);
      const dr = doc.querySelectorAll('#ia-plan-thresholds');
      if (dr.length !== 1 || !dr[0].closest('[data-ia-drawers]') || dr[0].dataset.open !== 'false') bad(`${at}: thresholds drawer: ${dr.length} found${dr[0] ? `${dr[0].closest('[data-ia-drawers]') ? '' : ', not in [data-ia-drawers]'}, data-open=${dr[0].dataset.open}` : ''}`);
      /* 9 caps and History's rows */
      if (key !== 'history') { const ov = S.querySelectorAll('[data-ux-over]').length; if (ov) bad(`${at}: ${ov} rows hidden by a cap ([data-ux-over])`); }
      else { const rows = S.querySelectorAll('.ia-plan-history > li:not([hidden])').length, n = logN() + 2;
        if (rows !== n) bad(`${at}: History shows ${rows} rows, expected ${n} (log entries + 2)`);
        if (o.approved && rows < 3) bad(`${at}: History shows ${rows} rows after Approve, expected at least 3`); }
      /* 10 the release line against planScreen() */
      const rel = L1.querySelector('.approval-releases'), ref = w.eval(`(() => { const t = document.createElement('template'); t.innerHTML = planScreen(); plainWords(t.content); const e = t.content.querySelector('.approval-releases'); return e ? e.outerHTML : ''; })()`);
      if (rel && rel.outerHTML !== ref) { let j = 0; while (rel.outerHTML[j] === ref[j]) j++; bad(`${at}: L1's release line differs from planScreen()'s at ${j}:\n    ${rel.outerHTML.slice(Math.max(0, j - 60), j + 100)}\n    ${ref.slice(Math.max(0, j - 60), j + 100)}`); }
      /* 12 sticky */
      const sk = doc.querySelectorAll('[data-ux-sticky]');
      if (sk.length !== 1) bad(`${at}: ${sk.length} [data-ux-sticky], expected 1`);
      else if (es === 'PROPOSED') { const sa = sk[0].querySelector('.primary[data-ux-act]'), ba = L1.querySelector('.ux-planband .primary[data-ux-act]');
        if (!sa || !ba || sa.dataset.uxAct !== ba.dataset.uxAct || ba.dataset.uxAct !== 'approve-plan') bad(`${at}: sticky's Approve act ${sa ? sa.dataset.uxAct : 'none'}, the band's ${ba ? ba.dataset.uxAct : 'none'}`); }
      /* 13 the L1 cap */
      const k = L1.querySelectorAll('.ux-kpi').length;
      if (k !== tiles || k > 4) bad(`${at}: L1 holds ${k} .ux-kpi, expected ${tiles} (spend, ${limited || 'the band\'s one'} crew, value)${k > 4 ? ': L1 cap of 4 exceeded, spec stop' : ''}`);
      return L1.innerHTML.replace(/href="#sw-h"/g, 'href="#/plan"');
    };
    const pick = async P => { for (const [name, val] of P) { const r = doc.querySelector(`input[name="${name}"][value="${val}"]`); if (!r) { bad(`#/plan: no switch ${name}=${val}`); continue; } r.checked = true; r.dispatchEvent(new w.Event('change', { bubbles: true })); await sleep(10); } };
    const allTabs = async (label, o) => { const L = []; for (const t of TABS) { await visit(t[1]); L.push(page(label, t, o)); } return L; };
    const same = (label, L) => { L.forEach((h, i) => { if (i && h !== L[0]) { let j = 0; while (h[j] === L[0][j]) j++; bad(`L1 on ${TABS[i][0]} differs from Items (${label}) at ${j}: "${L[0].slice(j, j + 80)}" vs "${h.slice(j, j + 80)}"`); } }); };
    /* default case */
    const mock0 = w.sessionStorage.getItem('l4-mock');
    same('default case', await allTabs('default case', { nondefault: false }));
    /* the non-default case, picked on Items */
    await visit('plan'); await pick(PICK[op]);
    const ls = w.eval('JSON.stringify({ b: LS.budget, l: LS.loi, a: LS.agg, t: LS.tou })'), J = JSON.parse(ls);
    const picked = op === 'lakeside' ? J.b === 6500 && J.l === false : op === 'harvest' ? J.a === false : J.t === false;
    if (!picked) bad(`the switches' change events did not set the case: ${ls}`);
    same('non-default case', await allTabs('non-default case', { nondefault: true }));
    await visit('plan'); await pick(UNPICK[op]);
    /* 11 R4 across an operator switch in the window */
    const other = OPS[(OPS.indexOf(op) + 1) % 3]; w.eval(`setOp(${JSON.stringify(other)}); render()`); await sleep(20);
    if (w.eval('currentScreen().ctx.op') !== w.eval('LS.op')) bad(`after setOp(${other}): ctx.op ${w.eval('currentScreen().ctx.op')}, LS.op ${w.eval('LS.op')} (R4)`);
    w.eval(`setOp(${JSON.stringify(op)}); render()`); await sleep(20);
    /* 14 Approve and Undo on each tab */
    for (const t of TABS) {
      if (mock0 === null) w.sessionStorage.removeItem('l4-mock'); else w.sessionStorage.setItem('l4-mock', mock0);
      await visit(t[1]);
      const a = doc.querySelector('#ia-root [data-level="L1"] .ux-planband [data-ux-act="approve-plan"]');
      if (!a) { bad(`#/${t[1]}: no Approve in the band`); continue; }
      a.click(); await sleep(10);
      const g = doc.querySelector('#uxact [data-ux-act-go]'); if (!g) { bad(`#/${t[1]}: Approve opened no dialog`); continue; }
      g.click(); await sleep(20);
      const fa = doc.activeElement;
      if (!fa || !fa.matches('[data-plan-state]') || !fa.closest('[data-level="L1"]')) bad(`#/${t[1]}: focus after Approve on ${fa ? fa.outerHTML.slice(0, 90) : 'nothing'}, expected the L1 chip [data-plan-state] (R15)`);
      if (expState() !== 'APPROVED') bad(`#/${t[1]}: state after Approve ${expState()}`);
      w.eval('UX_QN = 0; render()'); await sleep(20);
      page('after Approve', t, { nondefault: false, approved: true });
      const u = doc.querySelector('.ux-toast [data-ux-undo]');
      if (!u) { bad(`#/${t[1]}: no Undo in the toast after Approve`); continue; }
      u.click(); await sleep(20);
      const fu = doc.activeElement;
      if (!fu || !fu.matches('.ux-planband [data-ux-act="approve-plan"]')) bad(`#/${t[1]}: focus after Undo on ${fu ? fu.outerHTML.slice(0, 90) : 'nothing'}, expected the band's [data-ux-act=approve-plan] (R15)`);
      if (expState() !== PS.state) bad(`#/${t[1]}: state after Undo ${expState()}, expected ${PS.state}`);
    }
    log.push(`${B.opName} · ${stub ? 'stub' : 'builders'} · 4 tabs × (default, non-default ${PICK[op].map(x => x.join('=')).join(' ')}, after Approve) · L1 tiles ${tiles} (period ${PS.period})`);
    if (B.errors.length) bad(`script errors: ${B.errors.slice(0, 2).join(' | ')}`);
    B.dom.window.close();
  }
  log.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `plan_shape_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${[...new Set(fails)].slice(0, 12).join('\n  ')}` : `plan_shape_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
})();
