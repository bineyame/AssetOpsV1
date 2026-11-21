/* IA-1 counts check (spec §2.8, D-IA.24), jsdom. Per operator, in three states (default, ?state=no-recommendation, and after one act:
   the operator's first waiting decision chosen with its recommendation, where one exists), it computes its own expected values from
   ATTN[op], uxDecState(id).key and HC.decisions[].chooser, never through iaDecIds, iaWaiting or the inbox builders, and asserts:
   the Overview "Decisions" count and its waiting split; each Site page's count, split and sticky pill; Outcomes column 6 per Site;
   from IA-1c the badge and the row sets of "For you" and "In your portfolio".
   D-IA.34: on the Overview and every Site, rows shown + data-ia-more = the heading's count; every waiting decision (this check's own rule) is a shown row
   (IA-1b) or counted on a line carrying the inbox opener (from IA-1c); the line's parts equal the hidden rows' states. D-IA.35 L3: Outcomes column 5 against the
   Site page's board, one source (the most negative non-residual vr from uxSiteDriversShown). Synthetic: iaQueueCap on Mto's ids with cap = 1.
   M4 (r2): a 390 pass in Chromium (needs PW and CHROME from /opt/assetecon/tools/pw/env.sh): the rows ON SCREEN equal the capped rows, every waiting decision is on screen or counted on a visible line, and "And N more" equals what is truly off screen.
   Run: node tools/count_check.cjs   Plants: COUNT_PLANT=choose (iaWaiting drops "none"), capsel (the cap takes the first in reviewed order), capmore (iaCapMore = ''), phone (restores the phone rule that hides Overview queue rows 4-6 at 390, Chromium pass only),
   adverse (iaLargestAdverse picks the smallest adverse driver), foryou (IA-1c; "For you" drops the plan), nolog (IA-1c r1, D-IA.39; the act writes no log entry: the inbox's "Since you last looked" must hold one log:0 row to #/decision/<id> after Choose and none after Undo). */
const { boot, OPS, forced } = require('./ia_crawl.cjs');
const fs = require('fs'), path = require('path');
const PLANT = process.env.COUNT_PLANT || '';
/* IA-2a plan block (spec §5.1.8 row 2, D-IA.44, D-IA.50 R6/R12): per operator, on plan, plan/left-out, plan/review, plan/history, as proposed,
   after Approve, after its Undo, after Send back (reason and trade-off filled), and after Approve of a non-default case (Lakeside 6500 + LOI No,
   Harvest aggregation No, Metro TOU No): the stepper's current step, the band and sticky chips, the inbox plan row, the badge, History's first row
   and the toast against the state this check derives from sessionStorage['l4-mock'] and M.demo_workflow.plan_state (never iaPlanSteps, uxPlanState
   or iaForYou). Plants: planstep (iaPlanStepper reads PSTATE()), planhist (iaPlanHistory ignores the log), planver (History's first log row reads
   PSTATE().version; fails on the non-default case). Dormant unless IA-2a is landed or IA_FORCE_LANDED=IA-2a; the stub loads when no shapePlan. */
const PLAN_PLANTS = {
  planstep: 'iaPlanStepper = function (op) { const { steps, cur } = iaPlanSteps(PSTATE().state); return `<ol class="ux-dsteps ia-plan-steps" aria-label="Where this plan is">${steps.map((s, i) => `<li class="${i < cur ? \'is-done\' : i === cur ? \'is-current\' : \'\'}"${i === cur ? \' aria-current="step"\' : \'\'}>${s}</li>`).join(\'\')}</ol>`; };',
  planhist: '{ const _h = iaPlanHistory; iaPlanHistory = function (op) { const s = sessionStorage.getItem(UX_MOCK_KEY); uxMockSet({ ...uxMock(), log: [] }); try { return _h(op); } finally { if (s == null) sessionStorage.removeItem(UX_MOCK_KEY); else sessionStorage.setItem(UX_MOCK_KEY, s); } }; }',
  planver: '{ const _h = iaPlanHistory; iaPlanHistory = function (op) { return _h(op).replace(/(data-ia-hist="log:0">Version )[\\d,]+/, (m, a) => a + num(PSTATE().version)); }; }' };
const planOnly = !!PLAN_PLANTS[PLANT];
const IA2A = forced().includes('IA-2a') || /IA-2a/.test((fs.readFileSync(path.join(__dirname, '..', 'ia-routes.js'), 'utf8').match(/const IA_LANDED = new Set\(\[([^\]]*)\]\)/) || [, ''])[1]);
const planStub = w => { if (w.eval('typeof shapePlan') !== 'function') w.eval(fs.readFileSync(path.join(__dirname, 'fixtures', 'plan_stub.js'), 'utf8')); };
const PLANTS = { choose: `iaWaiting = id => uxDecState(id).key === 'choose';`, capsel: `iaQueueCap = (ids, cap) => ({ shown: ids.slice(0, cap), hidden: ids.slice(cap) });`,
  capmore: `iaCapMore = () => '';`,
  phone: '0',
  /* IA-1c r1 (D-IA.39): the act log loses the entry the act wrote */
  nolog: `{ const _a = uxActDo; uxActDo = key => { _a(key); const m = uxMock(); m.log = m.log.slice(1); uxMockSet(m); render(); }; }`,
  adverse: `iaLargestAdverse = sk => { let best = null; uxSiteDriversShown(sk).forEach(r => { if (!r.s.st.residual && r.vr < 0 && (!best || r.vr > best.vr)) best = r; }); return best; };`,
  foryou: `typeof iaForYou === 'function' && (() => { const _f = iaForYou; iaForYou = op => _f(op).filter(x => x !== 'plan' && !(x && x.plan)); })();` };
if (PLANT && !PLANTS[PLANT] && !PLAN_PLANTS[PLANT]) { console.error(`count_check: unknown plant ${PLANT}`); process.exit(2); }
const fails = [], log = [];
/* the IA-2a plan block (see the header); its own words for the steps and chips, its own state from storage and the manifest */
const PLAN_ROUTES = ['plan', 'plan/left-out', 'plan/review', 'plan/history'], STEP_WORD = { DRAFT: 'Draft', PROPOSED: 'Proposed', REVISED: 'Proposed', APPROVED: 'Approved', CLOSED: 'Closed' },
  CHIP_WORD = { ...STEP_WORD, REVISED: 'Revised' }, NONDEF = { lakeside: 'LS.budget = 6500; LS.loi = false', harvest: 'LS.agg = false', metro: 'LS.tou = false' };
async function planBlock() {
  const t0 = Date.now(), wait = ms => new Promise(r => setTimeout(r, ms)), sq = t => String(t || '').replace(/\s+/g, ' ').trim(); let boots = 0, combos = 0;
  /* one boot per operator and route for the four default states, one per operator for the non-default Approve on the four routes */
  const jobs = [...OPS.flatMap(op => PLAN_ROUTES.map(route => ({ op, route }))), ...OPS.map(op => ({ op, nondef: true }))];
  for (const J of jobs) {
    const B = await boot(J.op, 'plan'), { w, doc, go } = B, op = J.op; boots++;
    planStub(w); if (PLAN_PLANTS[PLANT]) w.eval(PLAN_PLANTS[PLANT]);
    const M0 = w.eval('JSON.parse(JSON.stringify(M.demo_workflow.plan_state))');
    if (J.nondef) w.eval(NONDEF[op]);
    /* the state as this check derives it: plan[op] of the stored mock over the manifest's plan_state */
    const derive = () => { let m = {}; try { m = JSON.parse(w.sessionStorage.getItem('l4-mock') || '{}'); } catch (e) {} const p = (m.plan || {})[op];
      return { state: p ? p.state : M0.state, by: p ? (p.by || '') : (M0.by || ''), version: p && p.version != null ? p.version : M0.version,
        log: (m.log || []).filter(e => e.op === op && (e.key === 'approve-plan' || e.key === 'send-back')) }; };
    const badgeN = () => +(doc.querySelector('[data-ia-inbox] .ia-badge')?.textContent.replace(/\D/g, '') || 0);
    const histFirst = route => { if (route === 'plan/history') return doc.querySelector('[data-ia-hist]');
      const d = doc.createElement('div'); d.innerHTML = w.eval(`iaPlanHistory(${JSON.stringify(op)})`); return d.querySelector('[data-ia-hist]'); };
    const toastT = () => sq(doc.querySelector('.ux-toast span')?.textContent);
    /* one assertion set: tag names the operator, case, route and state; want is what the act sequence must have produced */
    const check = (route, stateTag, want, badge0) => { const E = derive(), bad = m => fails.push(`${B.opName} · ${J.nondef ? 'non-default case · ' : ''}${route} · ${stateTag} · ${m}`); combos++;
      if (E.state !== want.state || E.version !== want.version) bad(`the stored state is ${E.state} v${E.version}, the act should have made ${want.state} v${want.version}`);
      const cur = [...doc.querySelectorAll('.ia-plan-steps [aria-current=step]')];
      if (cur.length !== 1 || sq(cur[0].textContent) !== STEP_WORD[E.state]) bad(`the stepper's current step reads "${cur.map(c => sq(c.textContent)).join('|') || 'none'}", expected "${STEP_WORD[E.state]}"`);
      const chipT = `${E.state === 'DRAFT' && E.by ? `Draft, sent back by ${E.by}` : `${CHIP_WORD[E.state]}${E.by ? ` by ${E.by}` : ''}`} · version ${E.version}`;
      for (const [where, sel] of [['band', '.ux-planband [data-plan-state]'], ['sticky', '[data-ux-sticky] [data-plan-state]']]) { const c = doc.querySelectorAll(sel);
        if (c.length !== 1) bad(`${c.length} ${where} chips`); else if (c[0].getAttribute('data-plan-state') !== E.state || sq(c[0].textContent) !== chipT) bad(`the ${where} chip reads "${sq(c[0].textContent)}" [${c[0].getAttribute('data-plan-state')}], expected "${chipT}" [${E.state}]`); }
      const row = doc.querySelector('#ia-inbox [data-ia-row="plan"]');
      if (E.state === 'PROPOSED') { if (!row) bad('the inbox has no plan row while proposed'); else if (sq(row.querySelector('small')?.textContent) !== `${STEP_WORD[E.state]}: awaiting approval`) bad(`the inbox plan row says "${sq(row.querySelector('small')?.textContent)}"`); }
      else if (row) bad(`the inbox still holds the plan row at ${E.state}`);
      const b = badgeN(), wb = badge0 - (E.state !== 'PROPOSED' ? 1 : 0); if (b !== wb) bad(`the badge reads ${b}, expected ${wb} (${badge0} as proposed${E.state !== 'PROPOSED' ? ', down by one' : ''})`);
      const h = histFirst(route), hT = h ? sq(h.textContent) : '', L = E.log[0];
      const wantH = L ? (L.key === 'approve-plan' ? `Version ${E.version} approved` : `Version ${want.sentFrom} sent back`) : `Version ${M0.version} proposed`;
      if (!h || h.getAttribute('data-ia-hist') !== (L ? 'log:0' : 'proposed') || !hT.startsWith(wantH + ' ')) bad(`History's first row is ${h ? `${h.getAttribute('data-ia-hist')} "${hT}"` : 'missing'}, expected ${L ? 'log:0' : 'proposed'} "${wantH} …"`);
      if (L) { const lr = doc.querySelector('#ia-inbox [data-ia-section="since"] [data-ia-row="log:0"]'); if (!lr || !sq(lr.textContent).startsWith(wantH + ' ')) bad(`the inbox's "Since you last looked" first row reads "${lr ? sq(lr.textContent) : 'nothing'}", expected "${wantH} …"`); }
      if (want.toast !== undefined && toastT() !== want.toast) bad(`the toast reads "${toastT()}", expected "${want.toast}"`);
      const cl = doc.querySelectorAll('.ia-plan-case').length; if (cl !== (J.nondef ? 1 : 0)) bad(`${cl} case lines, expected ${J.nondef ? 1 : 0}`);
      if (B.errors.length) bad(`script error: ${B.errors[0]}`); };
    const click = async sel => { const e = doc.querySelector(sel); if (!e) return false; e.click(); await wait(20); return true; };
    const approve = async (route, tag) => { if (!await click('.ux-planband [data-ux-act="approve-plan"]')) { fails.push(`${B.opName} · ${route} · ${tag}: no Approve in the band`); return false; }
      if (!await click('#uxact [data-ux-act-go]')) { fails.push(`${B.opName} · ${route} · ${tag}: no go button in the dialog`); return false; } return true; };
    const routes = J.nondef ? PLAN_ROUTES : [J.route];
    for (const route of routes) {
      await go(route);
      const badge0 = badgeN(), v1 = J.nondef ? M0.version + 1 : M0.version, P = { state: M0.state, version: M0.version };
      if (!J.nondef) check(route, 'as proposed', P, badge0);
      if (!await approve(route, 'Approve')) continue;
      check(route, J.nondef ? 'after Approve' : 'after Approve', { state: 'APPROVED', version: v1, toast: `Version ${v1} approved. Shown in this demonstration only.` }, badge0);
      if (!await click('.ux-toast [data-ux-undo]')) { fails.push(`${B.opName} · ${route}: no Undo on the toast`); continue; }
      if (J.nondef) { if (derive().state !== M0.state) fails.push(`${B.opName} · non-default case · ${route}: Undo did not restore ${M0.state}`); continue; }
      check(route, 'after Undo', { ...P, toast: 'Undone.' }, badge0);
      if (!await click('.ux-planband [data-ux-act="send-back"]')) { fails.push(`${B.opName} · ${route}: no Send back in the band`); continue; }
      const ta = doc.getElementById('ux-sb-reason'), sel = doc.getElementById('ux-sb-way'), opt = sel && [...sel.options].find(o => o.value);
      if (!ta || !opt) { fails.push(`${B.opName} · ${route}: the Send back dialog lacks its reason or a trade-off`); continue; }
      ta.value = 'The crew cannot do both visits'; sel.value = opt.value; for (const e of [ta, sel]) for (const t of ['input', 'change']) e.dispatchEvent(new w.Event(t, { bubbles: true }));
      if (!await click('#uxact [data-ux-act-go]')) { fails.push(`${B.opName} · ${route}: no go button in the Send back dialog`); continue; }
      check(route, 'after Send back', { state: 'DRAFT', version: M0.version, sentFrom: M0.version, toast: `Version ${M0.version} sent back. Shown in this demonstration only.` }, badge0);
    }
    B.dom.window.close();
  }
  log.push(`IA-2a plan block · ${combos} route × state combinations asserted (${OPS.length} operators × 4 routes × 4 states + 4 routes × 3 non-default Approves) · ${boots} boots · ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  if (combos !== 60) fails.push(`IA-2a plan block: ${combos} combinations asserted, expected 60`);
}
const waitingIn = txt => { const m = String(txt || '').match(/(\d+) waiting for a choice/); return m ? +m[1] : 0; };
(async () => {
  const IDS = id => [...String(id).matchAll(/decision\/([\w-]+)/g)].map(m => m[1]);
  const partsOf = (w, ids) => w.eval(`(() => { const k = ${JSON.stringify(ids)}.map(id => uxDecState(id)), n = f => k.filter(f).length, parts = [[n(x => x.key === 'choose' || x.key === 'none'), 'waiting for a choice'], [n(x => x.key === 'approval' && !x.draft), 'awaiting approval'], [n(x => x.key === 'approval' && x.draft), 'with the plan sent back to draft'], [n(x => x.key === 'released'), 'under way']].filter(([c]) => c); return parts.map(([c, t]) => c + ' ' + t).join(', '); })()`);
  /* D-IA.34: the rows shown in a queue panel, the line, and the invariants */
  const capCheck = (w, doc, panel, headCount, E_ids, E_wait, bad, tag) => {
    const rows = [...doc.querySelectorAll(`${panel} li.ux-q`)], shown = rows.map(li => IDS(li.innerHTML)[0]).filter(Boolean), line = doc.querySelector(`${panel} [data-ia-more]`), more = line ? +line.dataset.iaMore : 0;
    if (shown.length + more !== headCount) bad(`${tag}: ${shown.length} rows shown + ${more} on the line = ${shown.length + more}, the heading counts ${headCount}`);
    const hiddenWait = E_wait.filter(id => !shown.includes(id)), inbox = !!(line && line.querySelector('[data-ux-drawer="ia-inbox"]'));
    if (hiddenWait.length && !(w.eval('IA_LANDED.has("IA-1c")') && inbox)) bad(`${tag}: waiting decision ${hiddenWait[0]} is hidden by the cap${w.eval('IA_LANDED.has("IA-1c")') ? ' and the line has no inbox opener' : ''}`);
    const hidden = E_ids.filter(id => !shown.includes(id)), want = hidden.length ? `And ${hidden.length} more: ${partsOf(w, hidden)}.` : '';
    const got = line ? line.textContent.replace(/\s+/g, ' ').replace(/ Open Waiting for you$/, '').trim() : '';
    if (got !== want) bad(`${tag}: the line reads "${got}", expected "${want}"`);
  };
  for (const op of (planOnly ? [] : OPS)) for (const state of ['default', 'no-recommendation', 'after one act']) {
    const B = await boot(op, 'portfolio', { search: state === 'no-recommendation' ? '?state=no-recommendation' : '' }), { w, doc, go } = B, bad = m => fails.push(`${B.opName} (${state}) · ${m}`);
    if (PLANTS[PLANT]) w.eval(PLANTS[PLANT]);
    /* the expected values, by this check's own code */
    const X = () => w.eval(`(() => { const op = ${JSON.stringify(op)}, rows = ATTN[op], ids = [], seen = new Set();
      rows.forEach(r => { if (!seen.has(r[4])) { seen.add(r[4]); ids.push(r[4]); } });
      const key = id => uxDecState(id).key, wait = id => key(id) === 'choose' || key(id) === 'none';
      const site = sk => { const s = []; rows.forEach(r => { if (r[2] === sk && !s.includes(r[4])) s.push(r[4]); }); return s; };
      return { ids, waiting: ids.filter(wait), first: ids.find(id => wait(id) && uxRec(decById(id))) || null,
        sites: OPS[op].sites.map(sk => ({ sk, n: site(sk).length, waiting: site(sk).filter(wait).length })),
        chooser: Object.fromEntries((HC.decisions || []).map(d => [d.id, d.chooser])) }; })()`);
    let E = X(), E0 = null;
    if (state === 'after one act') { if (!E.first) { log.push(`${B.opName} · after one act: no waiting decision with a recommendation`); B.dom.window.close(); continue; }
      E0 = E; const act = () => w.eval(`uxActDo('choose:${E0.first}:' + uxRec(decById(${JSON.stringify(E0.first)})))`), sets = sec => [...doc.querySelectorAll(`#ia-inbox [data-ia-section="${sec}"] a[data-ia-row]`)].map(a => a.dataset.iaRow.replace(/^decision:/, '')).sort().join(','), logs = () => [...doc.querySelectorAll('#ia-inbox [data-ia-section="since"] a[data-ia-row^="log:"]')];
      const fy0 = sets('for-you'), pt0 = sets('portfolio'), id0 = E0.first; act();
      /* D-IA.39: the act log after Choose, and after Undo (the toast goes with the next navigation, so both are read here) */
      { const l = logs(); if (l.length !== 1 || l[0].dataset.iaRow !== 'log:0' || l[0].getAttribute('href') !== `#/decision/${id0}`) bad(`act log after Choose: ${l.length} rows (${l.map(a => `${a.dataset.iaRow} ${a.getAttribute('href')}`).join('; ') || 'none'}), expected one log:0 to #/decision/${id0}`);
        for (const sec of ['for-you', 'portfolio']) if (sets(sec).split(',').includes(id0)) bad(`after Choose: ${id0} is still in "${sec}"`);
        const ub = doc.querySelector('.ux-toast [data-ux-undo]'); if (!ub) bad('after Choose: no Undo on the toast'); else {
          ub.click(); await new Promise(r => setTimeout(r, 30));
          const left = logs().filter(a => a.getAttribute('href') === `#/decision/${id0}`); if (left.length) bad(`act log after Undo: ${left.length} log row(s) still name ${id0}`);
          if (sets('for-you') !== fy0 || sets('portfolio') !== pt0) bad(`after Undo the sets are not restored: For you ${sets('for-you') || 'nothing'} (was ${fy0 || 'nothing'}), In your portfolio ${sets('portfolio') || 'nothing'} (was ${pt0 || 'nothing'})`);
          act(); } }
      E = X(); }
    /* the Overview */
    await go('portfolio');
    const n = +(doc.querySelector('#uxq-h .ux-count')?.textContent.replace(/\D/g, '') ?? -1), split = waitingIn(doc.querySelector('#uxq-h [data-ux-split]')?.textContent);
    if (n !== E.ids.length) bad(`Overview: "Decisions" reads ${n}, expected ${E.ids.length}`);
    if (split !== E.waiting.length) bad(`Overview: the split reads ${split} waiting, expected ${E.waiting.length}`);
    capCheck(w, doc, '.ux-queue-panel', n, E.ids, E.waiting, bad, 'Overview queue');
    /* each Site page */
    for (const s of E.sites) { await go(`site/${s.sk}`);
      const c = +(doc.querySelector('#uxsq-h .ux-count')?.textContent.replace(/\D/g, '') ?? -1), sp = waitingIn(doc.querySelector('.ux-queue-panel [data-ux-split]')?.textContent), pill = doc.querySelector('[data-ux-sticky] .status-pill')?.textContent || '';
      if (c !== s.n) bad(`${s.sk}: the count reads ${c}, expected ${s.n}`);
      if (sp !== s.waiting) bad(`${s.sk}: the split reads ${sp} waiting, expected ${s.waiting}`);
      capCheck(w, doc, '.ux-queue-panel', c, E.ids.filter(id => w.eval(`ATTN[${JSON.stringify(op)}].some(r => r[2] === ${JSON.stringify(s.sk)} && r[4] === ${JSON.stringify(id)})`)), E.waiting.filter(id => w.eval(`ATTN[${JSON.stringify(op)}].some(r => r[2] === ${JSON.stringify(s.sk)} && r[4] === ${JSON.stringify(id)})`)), bad, `${s.sk} queue`);
      if (waitingIn(pill) !== s.waiting) bad(`${s.sk}: the sticky pill reads "${pill}", expected ${s.waiting} waiting`); }
    /* Outcomes column 6 */
    await go('portfolio/outcomes');
    for (const s of E.sites) { const tr = doc.querySelector(`table.ia-list tbody tr[data-row="${s.sk}"]`), v = tr ? +tr.children[5].textContent.replace(/\D/g, '') : -1;
      if (v !== s.waiting) bad(`Outcomes: ${s.sk} "Waiting for a choice" reads ${v}, expected ${s.waiting}`); }
    /* D-IA.35 L3: column 5 against the board, one source (computed here, not through iaLargestAdverse) */
    for (const s of E.sites) {
      const V = w.eval(`(() => { const sk = ${JSON.stringify(s.sk)}; if (tree(sk).plan == null) return { target: false }; let best = null; uxSiteDriversShown(sk).forEach(r => { if (!r.s.st.residual && r.vr < 0 && (!best || r.vr < best.vr)) best = r; }); return { target: true, lab: best ? plainText(best.s.lab) : null, vr: best ? best.vr : null, fmt: best ? usdW(best.vr, true) : null }; })()`);
      if (!V.target) continue;
      await go(`site/${s.sk}`); const board = [...doc.querySelectorAll('[data-board-v]')].map(e => ({ v: +e.dataset.boardV, t: (e.closest('tr')?.querySelector('.ux-board-go')?.textContent || '').replace(/: what is behind it/, '').trim() }));
      await go('portfolio/outcomes'); const c5 = doc.querySelector(`table.ia-list tbody tr[data-row="${s.sk}"]`)?.children[4].textContent.replace(/\s+/g, ' ').trim() || '';
      if (V.lab === null) { if (board.some(b => b.v < 0)) bad(`${s.sk}: no adverse driver by the check, but the board has a negative data-board-v`); if (!/No driver (widens the gap|raises the cost)/.test(c5)) bad(`Outcomes: ${s.sk} column 5 reads "${c5}", expected the "no driver" cell`); }
      else { if (!board.some(b => b.v === V.vr && b.t.includes(V.lab))) bad(`${s.sk}: the board has no opener "${V.lab}" with data-board-v ${V.vr}`);
        if (!c5.includes(V.lab) || !c5.includes(V.fmt)) bad(`Outcomes: ${s.sk} column 5 reads "${c5}", expected "${V.lab}" and ${V.fmt}`); }
    }
    /* IA-1c: the badge and the inbox row sets */
    if (w.eval('IA_LANDED.has("IA-1c")')) {
      const plan = w.eval(`uxPlanState(${JSON.stringify(op)}).state === 'PROPOSED'`), forYou = [...(plan ? ['plan'] : []), ...E.waiting.filter(id => E.chooser[id] === 'OPERATOR_EXECUTIVE')], port = E.waiting.filter(id => E.chooser[id] !== 'OPERATOR_EXECUTIVE');
      const badge = +(doc.querySelector('[data-ia-inbox] .ia-badge')?.textContent.replace(/\D/g, '') || 0);
      if (badge !== forYou.length) bad(`the badge reads ${badge}, expected ${forYou.length}`);
      const rows = sec => [...doc.querySelectorAll(`#ia-inbox [data-ia-section="${sec}"] a[data-ia-row]`)].map(a => a.dataset.iaRow.replace(/^decision:/, '')).sort().join(',');
      if (rows('for-you') !== [...forYou].sort().join(',')) bad(`"For you" holds ${rows('for-you') || 'nothing'}, expected ${forYou.join(',') || 'nothing'}`);
      if (rows('portfolio') !== [...port].sort().join(',')) bad(`"In your portfolio" holds ${rows('portfolio') || 'nothing'}, expected ${port.join(',') || 'nothing'}`);
    }
    log.push(`${B.opName} · ${state} · ${E.ids.length} decisions, ${E.waiting.length} waiting · ${E.sites.map(s => `${s.sk} ${s.n}/${s.waiting}`).join(', ')}`);
    if (B.errors.length) bad(`script errors: ${B.errors[0]}`);
    B.dom.window.close();
  }
  /* synthetic: iaQueueCap on Mto's ids with cap = 1 */
  if (!planOnly) { const B = await boot('lakeside', 'portfolio'), w = B.w; if (PLANTS[PLANT]) w.eval(PLANTS[PLANT]);
    const S = w.eval(`(() => { const ids = uxMergeRows(ATTN.lakeside.filter(r => r[2] === 'mto')).map(m => m.d), c = iaQueueCap(ids, 1); return { ids, shown: c.shown, hidden: c.hidden, wait: ids.filter(id => ['choose', 'none'].includes(uxDecState(id).key)), more: iaCapMore(c.hidden) }; })()`);
    const want = S.wait[0], d = B.doc.createElement('div'); d.innerHTML = S.more;
    if (S.shown.length !== 1 || S.shown[0] !== want) fails.push(`synthetic: iaQueueCap(Mto, 1) shows ${S.shown.join(',')}, expected the first waiting id ${want}`);
    if (S.hidden.length !== S.ids.length - 1 || S.hidden.includes(want)) fails.push(`synthetic: iaQueueCap(Mto, 1) hides ${S.hidden.join(',')}`);
    /* from IA-1c the line ends with the inbox opener when it hides a waiting decision (D-IA.34) */
    const hidW = S.hidden.some(id => S.wait.includes(id)), opener = w.eval('IA_LANDED.has("IA-1c")') && hidW;
    const wantT = `And ${S.ids.length - 1} more: ${partsOf(w, S.ids.filter(id => id !== want))}.${opener ? ' Open Waiting for you' : ''}`; if (d.textContent.trim() !== wantT) fails.push(`synthetic: iaCapMore reads "${d.textContent.trim()}", expected "${wantT}"`);
    if (opener !== !!d.querySelector('[data-ux-drawer="ia-inbox"]')) fails.push(`synthetic: iaCapMore ${opener ? 'lacks' : 'carries'} the inbox opener`);
    log.push(`synthetic · Mto cap 1 · shown ${S.shown.join(',')} · "${d.textContent.trim()}"`); B.dom.window.close(); }
  if (IA2A) await planBlock(); else console.log('IA-2a not landed; dormant');
  /* M4: the same counts as rendered at 390 (the media rules are in force only in a browser) */
  if (!planOnly && !process.env.PW) { console.error('count_check: PW is not set (source /opt/assetecon/tools/pw/env.sh)'); process.exit(2); }
  if (!planOnly) { const { chromium } = require(process.env.PW), br = await chromium.launch({ executablePath: process.env.CHROME }), base = 'file://' + require('path').resolve(__dirname, '..', 'index.html');
    const PAGE = () => { const op = sessionStorage.getItem('l4-op'), vis = e => e.getClientRects().length > 0 && getComputedStyle(e).display !== 'none' && getComputedStyle(e).visibility !== 'hidden';
      const waiting = ids => ids.filter(id => ['choose', 'none'].includes(uxDecState(id).key)), ids = [], seen = new Set(); ATTN[op].forEach(r => { if (!seen.has(r[4])) { seen.add(r[4]); ids.push(r[4]); } });
      const IDS = li => (li.innerHTML.match(/decision\/([\w-]+)/) || [])[1];
      const read = (sk) => { const all = sk ? [...new Set(ATTN[op].filter(r => r[2] === sk).map(r => r[4]))] : ids, panel = document.querySelector('.ux-queue-panel'), rows = panel ? [...panel.querySelectorAll('li.ux-q')] : [],
        built = rows.map(IDS).filter(Boolean), shown = rows.filter(vis).map(IDS).filter(Boolean), line = panel && panel.querySelector('[data-ia-more]'), lineVis = !!line && vis(line);
        return { total: all.length, wait: waiting(all), built, shown, more: line ? +line.dataset.iaMore : 0, lineVis, inbox: !!(line && line.querySelector('[data-ux-drawer="ia-inbox"]')) }; };
      return { read, sites: OPS[op].sites }; };
    for (const op of OPS) for (const q of ['', '?state=no-recommendation']) {
      const ctx = await br.newContext({ viewport: { width: 390, height: 844 } }); await ctx.addInitScript(v => { try { sessionStorage.setItem('l4-op', v); } catch (e) {} }, op);
      const p = await ctx.newPage(), errs = []; p.on('pageerror', e => errs.push(String(e))); await p.goto(`${base}${q}#/portfolio`); await p.waitForTimeout(500);
      if (PLANT === 'phone') await p.addStyleTag({ content: '@media (max-width:600px){.ux-overview .ux-queue:not(.is-filtered)>li.ux-q:nth-child(n+4){display:none}}' });
      const routes = [['portfolio', null], ...(await p.evaluate(() => OPS[sessionStorage.getItem('l4-op')].sites)).map(sk => [`site/${sk}`, sk])], IAL = await p.evaluate('IA_LANDED.has("IA-1c")'); let nRows = 0;
      for (const [r, sk] of routes) { await p.evaluate(h => { location.hash = h; }, `#/${r}`); await p.waitForTimeout(350);
        const R = await p.evaluate(`(${PAGE.toString()})().read(${JSON.stringify(sk)})`), tag = `${op} ${q || 'default'} 390 ${r}`; nRows += R.shown.length;
        const bad = m => fails.push(`${tag}: ${m}`), off = R.total - R.shown.length;
        if (R.shown.length !== R.built.length) bad(`${R.shown.length} rows on screen, the cap built ${R.built.length} (${R.built.filter(x => !R.shown.includes(x)).join(',')} hidden by CSS)`);
        if (R.more !== off) bad(`"And ${R.more} more" but ${off} of ${R.total} are off screen`);
        if (R.more && !R.lineVis) bad('the "more" line is not on screen');
        const hw = R.wait.filter(id => !R.shown.includes(id)); if (hw.length && !(IAL && R.inbox && R.lineVis)) bad(`waiting decision ${hw[0]} is neither on screen nor counted on a visible line`); }
      log.push(`${op} · ${q || 'default'} · 390 · ${routes.length} routes, ${nRows} rows on screen`); if (!nRows) fails.push(`${op} ${q || 'default'} 390: no queue row measured`);
      if (errs.length) fails.push(`390 ${op}: script error ${errs[0]}`); await ctx.close(); }
    await br.close(); }
  log.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `count_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${fails.slice(0, 12).join('\n  ')}` : `count_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
})();
