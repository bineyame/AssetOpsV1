/* IA-1 after-render check (spec §2.5, D-IA.13, D-IA.17), jsdom. For every live route (and the typed not-found) of every
   operator, the observer is attached through window.__iaInserted, straight after the one insertion, to the frame root it is
   handed; it waits for idle (2 animation frames + 300 ms) and dispatches no event. Any mutation fails, except a class change
   whose only changed token is is-on on [data-ux-sticky] or scrolls on .scroll-region.
   Run: node tools/after_render_check.cjs   Plants: AR_PLANT=text|attr|late|replace (hosts: one route per shape per operator, D-IA.29; each must fail). */
const { boot, liveRoutes, OPS, sleep } = require('./ia_crawl.cjs');
const PLANT = process.env.AR_PLANT || '';
const PLANTS = {
  /* plain words skipped while finishing, then run on the inserted frame; the planted node must change or the plant did not bite */
  text: `{ IA_ROUTES.forEach(r => { const _r = r.render; r.render = ctx => _r(ctx).replace(/(<section data-shape="[a-z]+"[^>]*>)/, '$1<p data-ar-plant>the evaluator</p>'); });
    const _pw = plainWords; plainWords = root => { if (root && root.nodeType === 11) return; _pw(root); };
    const _b = iaBind; iaBind = route => { _b(route); setTimeout(() => { const rt = document.getElementById('ia-root'), n = rt.querySelector('[data-ar-plant]'), before = n && n.textContent; _pw(rt); if (!n || n.textContent === before) throw new Error('plant did not bite'); }, 0); }; }`,
  attr: `{ const _b = iaBind; iaBind = route => { _b(route); setTimeout(() => document.querySelector('#ia-root .canvas div').setAttribute('data-ar-plant', ''), 0); }; }`,
  replace: `{ const _b = iaBind; iaBind = route => { _b(route); setTimeout(() => { const rt = document.getElementById('ia-root'), c = rt.cloneNode(true); c.querySelector('h1').textContent = 'Rewritten after render'; rt.replaceWith(c); }, 0); }; }`,
  late: `{ const _b = iaBind; iaBind = route => { _b(route); setTimeout(() => document.querySelector('#ia-root h1').appendChild(document.createTextNode(' late')), 250); }; }`
};
if (PLANT && !PLANTS[PLANT]) { console.error(`after_render_check: unknown plant ${PLANT}`); process.exit(2); }
const fails = [], log = [];
const toks = v => new Set(String(v || '').split(/\s+/).filter(Boolean));
const allowed = (m, w) => { if (m.type !== 'attributes' || m.attributeName !== 'class') return false; const a = toks(m.oldValue), b = toks(m.target.getAttribute('class')), d = [...a, ...b].filter(t => a.has(t) !== b.has(t));
  return d.length > 0 && ((m.target.matches('[data-ux-sticky]') && d.every(t => t === 'is-on')) || (m.target.matches('.scroll-region') && d.every(t => t === 'scrolls'))); };
(async () => {
  for (const op of OPS) {
    let recs = null, hooked = 0, root0 = null;
    const B = await boot(op, 'plan', { before(w) { w.__iaInserted = root => { hooked++; root0 = root; recs = []; const o = new w.MutationObserver(ms => recs.push(...ms)); o.observe(root, { childList: true, characterData: true, attributes: true, subtree: true, attributeOldValue: true, characterDataOldValue: true }); w.__arObs = o; }; } });
    const { w, doc, go } = B;
    if (PLANT) w.eval(PLANTS[PLANT]);
    const idle = () => new Promise(r => w.requestAnimationFrame(() => w.requestAnimationFrame(() => setTimeout(r, 300))));
    /* D-IA.29: a planted run visits one route per shape per operator (plan, the three Portfolio tabs, the first Site; from IA-1c the
       first decision); an unplanted run visits every live route and the typed not-found */
    const live = liveRoutes(w, op), firstSite = live.find(r => r.id.startsWith('site/')), firstDec = live.find(r => r.id.startsWith('decision/'));
    const hosts = PLANT ? live.filter(r => ['plan', 'portfolio', 'portfolio/outcomes', 'portfolio/demand-and-capacity'].includes(r.id) || r === firstSite || r === firstDec) : [...live, { id: 'x-unknown' }];
    for (const r of hosts) {
      const h0 = hooked; recs = null; B.errors.length = 0; await go(r.id); await idle();
      if (hooked - h0 > 1) fails.push(`${B.opName} · #/${r.id}: rendered ${hooked - h0} times for one navigation`);
      if (hooked > h0 && doc.getElementById('ia-root') !== root0) { fails.push(`${B.opName} · #/${r.id}: the frame root was replaced after insertion`); w.__arObs.disconnect(); continue; }
      if (hooked === h0 || !recs) { fails.push(`${B.opName} · #/${r.id}: the insertion hook was not called`); continue; }
      const ms = recs.splice(0).concat(w.__arObs.takeRecords()).filter(m => !allowed(m, w)); w.__arObs.disconnect();
      const what = m => m.type === 'attributes' ? `${m.attributeName} on ${m.target.tagName.toLowerCase()}` : m.type === 'characterData' ? `text "${String(m.target.nodeValue).slice(0, 30)}"` : `children of ${m.target.nodeName.toLowerCase()}`;
      if (ms.length) fails.push(`${B.opName} · #/${r.id}: ${ms.length} mutation(s) after insertion: ${[...new Set(ms.map(what))].slice(0, 3).join('; ')}`);
      if (B.errors.length) fails.push(`${B.opName} · #/${r.id}: ${B.errors[0]}`);
      log.push(`${B.opName} · #/${r.id} · ${ms.length} mutation(s)`);
    }
    B.dom.window.close();
  }
  log.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `after_render_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${fails.slice(0, 10).join('\n  ')}` : `after_render_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
})();
