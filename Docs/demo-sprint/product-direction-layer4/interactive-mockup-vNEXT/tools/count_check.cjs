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
   adverse (iaLargestAdverse picks the smallest adverse driver), foryou (IA-1c; "For you" drops the plan). */
const { boot, OPS } = require('./ia_crawl.cjs');
const PLANT = process.env.COUNT_PLANT || '';
const PLANTS = { choose: `iaWaiting = id => uxDecState(id).key === 'choose';`, capsel: `iaQueueCap = (ids, cap) => ({ shown: ids.slice(0, cap), hidden: ids.slice(cap) });`,
  capmore: `iaCapMore = () => '';`,
  phone: '0',
  adverse: `iaLargestAdverse = sk => { let best = null; uxSiteDriversShown(sk).forEach(r => { if (!r.s.st.residual && r.vr < 0 && (!best || r.vr > best.vr)) best = r; }); return best; };`,
  foryou: `typeof iaForYou === 'function' && (() => { const _f = iaForYou; iaForYou = op => _f(op).filter(x => x !== 'plan' && !(x && x.plan)); })();` };
if (PLANT && !PLANTS[PLANT]) { console.error(`count_check: unknown plant ${PLANT}`); process.exit(2); }
const fails = [], log = [];
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
  for (const op of OPS) for (const state of ['default', 'no-recommendation', 'after one act']) {
    const B = await boot(op, 'portfolio', { search: state === 'no-recommendation' ? '?state=no-recommendation' : '' }), { w, doc, go } = B, bad = m => fails.push(`${B.opName} (${state}) · ${m}`);
    if (PLANT) w.eval(PLANTS[PLANT]);
    /* the expected values, by this check's own code */
    const X = () => w.eval(`(() => { const op = ${JSON.stringify(op)}, rows = ATTN[op], ids = [], seen = new Set();
      rows.forEach(r => { if (!seen.has(r[4])) { seen.add(r[4]); ids.push(r[4]); } });
      const key = id => uxDecState(id).key, wait = id => key(id) === 'choose' || key(id) === 'none';
      const site = sk => { const s = []; rows.forEach(r => { if (r[2] === sk && !s.includes(r[4])) s.push(r[4]); }); return s; };
      return { ids, waiting: ids.filter(wait), first: ids.find(id => wait(id) && uxRec(decById(id))) || null,
        sites: OPS[op].sites.map(sk => ({ sk, n: site(sk).length, waiting: site(sk).filter(wait).length })),
        chooser: Object.fromEntries((HC.decisions || []).map(d => [d.id, d.chooser])) }; })()`);
    let E = X();
    if (state === 'after one act') { if (!E.first) { log.push(`${B.opName} · after one act: no waiting decision with a recommendation`); B.dom.window.close(); continue; }
      w.eval(`uxMockSet({ chosen: { ${JSON.stringify(E.first)}: uxRec(decById(${JSON.stringify(E.first)})) } })`); E = X(); }
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
    for (const s of E.sites) { const tr = doc.querySelector(`.ia-outcomes tr[data-site="${s.sk}"]`), v = tr ? +tr.children[5].textContent.replace(/\D/g, '') : -1;
      if (v !== s.waiting) bad(`Outcomes: ${s.sk} "Waiting for a choice" reads ${v}, expected ${s.waiting}`); }
    /* D-IA.35 L3: column 5 against the board, one source (computed here, not through iaLargestAdverse) */
    for (const s of E.sites) {
      const V = w.eval(`(() => { const sk = ${JSON.stringify(s.sk)}; if (tree(sk).plan == null) return { target: false }; let best = null; uxSiteDriversShown(sk).forEach(r => { if (!r.s.st.residual && r.vr < 0 && (!best || r.vr < best.vr)) best = r; }); return { target: true, lab: best ? plainText(best.s.lab) : null, vr: best ? best.vr : null, fmt: best ? usdW(best.vr, true) : null }; })()`);
      if (!V.target) continue;
      await go(`site/${s.sk}`); const board = [...doc.querySelectorAll('[data-board-v]')].map(e => ({ v: +e.dataset.boardV, t: (e.closest('tr')?.querySelector('.ux-board-go')?.textContent || '').replace(/: what is behind it/, '').trim() }));
      await go('portfolio/outcomes'); const c5 = doc.querySelector(`.ia-outcomes tr[data-site="${s.sk}"]`)?.children[4].textContent.replace(/\s+/g, ' ').trim() || '';
      if (V.lab === null) { if (board.some(b => b.v < 0)) bad(`${s.sk}: no adverse driver by the check, but the board has a negative data-board-v`); if (!/No driver (widens the gap|raises the cost)/.test(c5)) bad(`Outcomes: ${s.sk} column 5 reads "${c5}", expected the "no driver" cell`); }
      else { if (!board.some(b => b.v === V.vr && b.t.includes(V.lab))) bad(`${s.sk}: the board has no opener "${V.lab}" with data-board-v ${V.vr}`);
        if (!c5.includes(V.lab) || !c5.includes(V.fmt)) bad(`Outcomes: ${s.sk} column 5 reads "${c5}", expected "${V.lab}" and ${V.fmt}`); }
    }
    /* IA-1c: the badge and the inbox row sets */
    if (w.eval('IA_LANDED.has("IA-1c")')) {
      const plan = w.eval(`uxPlanState(${JSON.stringify(op)}).state === 'PROPOSED'`), forYou = [...(plan ? ['plan'] : []), ...E.waiting.filter(id => E.chooser[id] === 'OPERATOR_EXECUTIVE')], port = E.waiting.filter(id => E.chooser[id] !== 'OPERATOR_EXECUTIVE');
      const badge = +(doc.querySelector('[data-ia-inbox] .ia-badge')?.textContent.replace(/\D/g, '') || 0);
      if (badge !== forYou.length) bad(`the badge reads ${badge}, expected ${forYou.length}`);
      const rows = sec => [...doc.querySelectorAll(`#ia-inbox [data-ia-section="${sec}"] a[data-ia-row]`)].map(a => a.dataset.iaRow).sort().join(',');
      if (rows('for-you') !== [...forYou].sort().join(',')) bad(`"For you" holds ${rows('for-you') || 'nothing'}, expected ${forYou.join(',') || 'nothing'}`);
      if (rows('portfolio') !== [...port].sort().join(',')) bad(`"In your portfolio" holds ${rows('portfolio') || 'nothing'}, expected ${port.join(',') || 'nothing'}`);
    }
    log.push(`${B.opName} · ${state} · ${E.ids.length} decisions, ${E.waiting.length} waiting · ${E.sites.map(s => `${s.sk} ${s.n}/${s.waiting}`).join(', ')}`);
    if (B.errors.length) bad(`script errors: ${B.errors[0]}`);
    B.dom.window.close();
  }
  /* synthetic: iaQueueCap on Mto's ids with cap = 1 */
  { const B = await boot('lakeside', 'portfolio'), w = B.w; if (PLANT) w.eval(PLANTS[PLANT]);
    const S = w.eval(`(() => { const ids = uxMergeRows(ATTN.lakeside.filter(r => r[2] === 'mto')).map(m => m.d), c = iaQueueCap(ids, 1); return { ids, shown: c.shown, hidden: c.hidden, wait: ids.filter(id => ['choose', 'none'].includes(uxDecState(id).key)), more: iaCapMore(c.hidden) }; })()`);
    const want = S.wait[0], d = B.doc.createElement('div'); d.innerHTML = S.more;
    if (S.shown.length !== 1 || S.shown[0] !== want) fails.push(`synthetic: iaQueueCap(Mto, 1) shows ${S.shown.join(',')}, expected the first waiting id ${want}`);
    if (S.hidden.length !== S.ids.length - 1 || S.hidden.includes(want)) fails.push(`synthetic: iaQueueCap(Mto, 1) hides ${S.hidden.join(',')}`);
    const wantT = `And ${S.ids.length - 1} more: ${partsOf(w, S.ids.filter(id => id !== want))}.`; if (d.textContent.trim() !== wantT) fails.push(`synthetic: iaCapMore reads "${d.textContent.trim()}", expected "${wantT}"`);
    log.push(`synthetic · Mto cap 1 · shown ${S.shown.join(',')} · "${d.textContent.trim()}"`); B.dom.window.close(); }
  /* M4: the same counts as rendered at 390 (the media rules are in force only in a browser) */
  if (!process.env.PW) { console.error('count_check: PW is not set (source /opt/assetecon/tools/pw/env.sh)'); process.exit(2); }
  { const { chromium } = require(process.env.PW), br = await chromium.launch({ executablePath: process.env.CHROME }), base = 'file://' + require('path').resolve(__dirname, '..', 'index.html');
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
