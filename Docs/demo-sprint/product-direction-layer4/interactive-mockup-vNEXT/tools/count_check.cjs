/* IA-1 counts check (spec §2.8, D-IA.24), jsdom. Per operator, in three states (default, ?state=no-recommendation, and after one act:
   the operator's first waiting decision chosen with its recommendation, where one exists), it computes its own expected values from
   ATTN[op], uxDecState(id).key and HC.decisions[].chooser, never through iaDecIds, iaWaiting or the inbox builders, and asserts:
   the Overview "Decisions" count and its waiting split; each Site page's count, split and sticky pill; Outcomes column 6 per Site;
   from IA-1c the badge and the row sets of "For you" and "In your portfolio".
   Run: node tools/count_check.cjs   Plants: COUNT_PLANT=choose (iaWaiting drops "none"), foryou (IA-1c; "For you" drops the plan). */
const { boot, OPS } = require('./ia_crawl.cjs');
const PLANT = process.env.COUNT_PLANT || '';
const PLANTS = { choose: `iaWaiting = id => uxDecState(id).key === 'choose';`, foryou: `typeof iaForYou === 'function' && (() => { const _f = iaForYou; iaForYou = op => _f(op).filter(x => x !== 'plan' && !(x && x.plan)); })();` };
if (PLANT && !PLANTS[PLANT]) { console.error(`count_check: unknown plant ${PLANT}`); process.exit(2); }
const fails = [], log = [];
const waitingIn = txt => { const m = String(txt || '').match(/(\d+) waiting for a choice/); return m ? +m[1] : 0; };
(async () => {
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
    /* each Site page */
    for (const s of E.sites) { await go(`site/${s.sk}`);
      const c = +(doc.querySelector('#uxsq-h .ux-count')?.textContent.replace(/\D/g, '') ?? -1), sp = waitingIn(doc.querySelector('.ux-queue-panel [data-ux-split]')?.textContent), pill = doc.querySelector('[data-ux-sticky] .status-pill')?.textContent || '';
      if (c !== s.n) bad(`${s.sk}: the count reads ${c}, expected ${s.n}`);
      if (sp !== s.waiting) bad(`${s.sk}: the split reads ${sp} waiting, expected ${s.waiting}`);
      if (waitingIn(pill) !== s.waiting) bad(`${s.sk}: the sticky pill reads "${pill}", expected ${s.waiting} waiting`); }
    /* Outcomes column 6 */
    await go('portfolio/outcomes');
    for (const s of E.sites) { const tr = doc.querySelector(`.ia-outcomes tr[data-site="${s.sk}"]`), v = tr ? +tr.children[5].textContent.replace(/\D/g, '') : -1;
      if (v !== s.waiting) bad(`Outcomes: ${s.sk} "Waiting for a choice" reads ${v}, expected ${s.waiting}`); }
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
  log.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `count_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${fails.slice(0, 12).join('\n  ')}` : `count_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
})();
