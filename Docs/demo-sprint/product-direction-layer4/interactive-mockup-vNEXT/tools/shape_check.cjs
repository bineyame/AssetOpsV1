/* IA-1 shape check (spec §2.5, D-IA.16, D-IA.19), jsdom, for each operator:
   1 every live route (and a typed unknown address, which must show not-found) renders from its shape: one frame root, one
     [data-shape], data-level never decreasing, one h1, at most 4 .ux-kpi in L1, at most one button.primary per level region,
     and a primary outside every region only inside [data-ux-sticky] with the L1 primary's act;
   2 the crawl from iaStart(): every content, tab and palette href, to 6 hops, classifies good (tools/ia_crawl.cjs);
   3 the rail: an unlanded item is an unavailable root with "Not available yet" and no href; a landed item links its route;
   4 the document title is "<title> · <operator name>";
   5 the Lab gate: off, no footer, no Lab link, no Lab option in the review select, #/lab is not-found; on, the footer reads
     "Workspace" and "Simulator Lab" with href="#/lab", and #/lab opens the Lab.
   Run: node tools/shape_check.cjs   Plants: SHAPE_PLANT=unlink|stub|rail|palette|primary|lab (each must fail). */
const { boot, classifier, identity, liveRoutes, hrefsOf, OPS, sleep } = require('./ia_crawl.cjs');
const PLANT = process.env.SHAPE_PLANT || '';
const fails = [], log = [];
/* each plant reaches past the mechanism it tests; host route iaStart() */
const PLANTS = {
  unlink: `iaUnlink = function () {};`,
  stub: `{ const _l = iaLive; iaLive = h => /^#?\\/?site\\/kisiwa\\/health$/.test(String(h)) || _l(h); const r = IA_ROUTES.find(x => x.id === iaStart()), _r = r.render;
    r.render = ctx => _r(ctx).replace('<div data-level="L2">', '<div data-level="L2"><a href="#/site/kisiwa/health">Health</a>'); }`,
  rail: `iaItemLanded = () => true;`,
  palette: `iaPaletteFilter = out => out;`,
  primary: `{ const r = IA_ROUTES.find(x => x.id === iaStart()), _r = r.render; r.render = ctx => _r(ctx).replace('<div data-level="L1">', '<div data-level="L1"><button class="button primary" data-ux-act="plant">Plant</button>'); }`,
  lab: `iaDev = () => true;`
};
if (PLANT && !PLANTS[PLANT]) { console.error(`shape_check: unknown plant ${PLANT}`); process.exit(2); }
(async () => {
  for (const op of OPS) {
    const B = await boot(op, 'plan'), { w, doc, go } = B, bad = m => fails.push(`${B.opName} · ${m}`);
    if (PLANT) w.eval(PLANTS[PLANT]);
    const start = w.eval('iaStart()'); await go(start);
    const cls = classifier(w);
    /* 1 and 4: every live route, and the typed unknown address */
    const routes = [...liveRoutes(w, op), { id: 'x-unknown', shape: 'frame', notFound: true }];
    for (const r of routes) {
      await go(r.id); const app = doc.getElementById('app'), fr = app.querySelectorAll('.ia-frame#ia-root');
      const s = w.eval('currentScreen()'); const tag = `#/${r.id}`;
      if (r.notFound && s.id !== 'not-found') { bad(`${tag}: does not show not-found (${s.id})`); continue; }
      if (fr.length !== 1) { bad(`${tag}: ${fr.length} frame roots`); continue; }
      const f = fr[0], sh = f.querySelectorAll(`[data-shape="${r.shape}"]`).length; if (sh !== 1) bad(`${tag}: ${sh} [data-shape="${r.shape}"]`);
      const lv = [...f.querySelectorAll('[data-level]')].map(e => e.dataset.level); if (lv.some((x, i) => i && x < lv[i - 1])) bad(`${tag}: levels decrease (${lv.join(',')})`);
      const h1 = f.querySelectorAll('h1').length + app.querySelectorAll('.reviewbar h1').length; if (h1 !== 1) bad(`${tag}: ${h1} h1`);
      const l1 = [...f.querySelectorAll('[data-level="L1"]')], k = l1.reduce((a, e) => a + e.querySelectorAll('.ux-kpi').length, 0); if (k > 4) bad(`${tag}: ${k} tiles in L1`);
      const regions = [...f.querySelectorAll('[data-level]')]; regions.forEach(rg => { const n = [...rg.querySelectorAll('button.primary')].filter(b => b.closest('[data-level]') === rg).length; if (n > 1) bad(`${tag}: ${n} primary buttons in one ${rg.dataset.level} region`); });
      const l1act = l1.flatMap(e => [...e.querySelectorAll('button.primary')]).map(b => b.dataset.act || b.dataset.uxAct)[0];
      f.querySelectorAll('button.primary').forEach(b => { if (b.closest('[data-level]')) return; const st = b.closest('[data-ux-sticky]'); if (!st || (b.dataset.act || b.dataset.uxAct) !== l1act) bad(`${tag}: a primary button outside every level ("${b.textContent.trim().slice(0, 30)}")`); });
      const want = `${w.eval('currentScreen().title')} · ${B.opName}`; if (doc.title !== want) bad(`${tag}: document title "${doc.title}", not "${want}"`);
      /* 3 the rail */
      const rail = w.eval('IA_RAIL.map(i => ({ label: i.label, route: i.route, landed: IA_LANDED.has(i.unit) }))');
      for (const i of rail) { const un = f.querySelector(`.rail [data-rail-unavailable="${i.label}"]`), a = [...f.querySelectorAll('.rail a')].find(x => x.textContent.trim() === i.label);
        if (i.landed ? !(a && a.getAttribute('href') === `#/${i.route}`) : !(un && !un.closest('a') && !un.querySelector('a') && !un.hasAttribute('href') && /Not available yet/.test(un.textContent) && !a)) bad(`${tag}: rail item "${i.label}" is not ${i.landed ? 'a link to its route' : 'an unavailable root'}`); }
      log.push(`${B.opName} · #/${r.id} · ${r.notFound ? 'not-found' : r.shape} · levels ${lv.join(',') || 'none'}`);
    }
    /* 2 the crawl, from the start, with the palette's targets as start-route edges */
    await go(start); w.eval('uxPalette(true)'); const pal = [...doc.querySelectorAll('#ux-cmd-list [data-go]')].map(li => '#/' + li.dataset.go); w.eval('uxPalette(false)');
    const seen = new Set([identity(start)]), queue = [[start, 0]], met = new Map(); pal.forEach(h => met.set(h, 'palette'));
    while (queue.length) { const [h, d] = queue.shift(); await go(h);
      const hs = [...hrefsOf(doc), ...(h === start ? pal : [])];
      for (const x of hs) { const c = cls(x); if (c !== 'good') { bad(`crawl: #/${h} links ${x} (${c})`); continue; } const id = identity(x); if (!seen.has(id) && d < 6) { seen.add(id); queue.push([x.replace(/^#\//, ''), d + 1]); } } }
    log.push(`${B.opName} · crawl: ${seen.size} route identities, ${pal.length} palette entries`);
    /* 5 the Lab gate */
    await go(start);
    if (doc.querySelector('[data-ia-footer]')) bad('Lab gate: the workspace footer shows with the switch off');
    if (doc.querySelector('#app a[href^="#/lab"]')) bad('Lab gate: a Lab link with the switch off');
    const labIds = w.eval(`SCREENS.filter(s => s.root === 'Simulator Lab').map(s => s.id)`); if ([...doc.querySelectorAll('#screen-select option')].some(o => labIds.includes(o.value))) bad('Lab gate: the review select lists a Lab screen with the switch off');
    await go('lab'); if (w.eval('currentScreen().id') !== 'not-found') bad('Lab gate: #/lab does not resolve to not-found with the switch off');
    w.sessionStorage.setItem('l4-dev', '1'); await go(start);
    const ft = doc.querySelector('[data-ia-footer]'), fa = ft && ft.querySelector('a');
    if (!ft || !/Workspace/.test(ft.querySelector('.eyebrow')?.textContent || '') || !fa || fa.textContent.trim() !== 'Simulator Lab' || fa.getAttribute('href') !== '#/lab') bad('Lab gate: with the switch on the footer does not read "Workspace" › "Simulator Lab" (#/lab)');
    await go('lab'); if (w.eval('currentScreen().id') !== 'lab') bad('Lab gate: #/lab does not open the Lab with the switch on');
    w.sessionStorage.removeItem('l4-dev');
    if (B.errors.length) bad(`script errors: ${B.errors.slice(0, 2).join(' | ')}`);
    B.dom.window.close();
  }
  log.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `shape_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${[...new Set(fails)].slice(0, 12).join('\n  ')}` : `shape_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
})();
