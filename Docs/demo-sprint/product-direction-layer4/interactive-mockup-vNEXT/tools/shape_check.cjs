/* IA-1 shape check (spec §2.5, §2.8; D-IA.16, D-IA.19, D-IA.23, D-IA.25, D-IA.28, D-IA.29), jsdom, for each operator:
   1 every live route (and a typed unknown address, which must show not-found) renders from its shape: one frame root, one
     [data-shape], data-level never decreasing, one h1, at most 4 .ux-kpi in L1; the primary rule (D-IA.23): a primary is any
     a.primary or button.primary outside every .ux-drawer, its act is data-act, else data-ux-act, else drawer:<data-ux-drawer>, else
     href:<href> (none fails); at most one per [data-level] region; the page primary is the first inside a region; a primary outside
     every region sits in [data-ux-sticky] with the page primary's act. Unplanted, item 1 runs in three states: default,
     ?state=no-recommendation, and after one act (the operator's first waiting decision chosen with its recommendation);
   2 the crawl from iaStart(): every content, tab and palette href, to 6 hops, classifies good (tools/ia_crawl.cjs);
   3 the rail: an unlanded item is an unavailable root with "Not available yet" and no href; a landed item links its route;
   4 the document title is "<title> · <operator name>";
   5 the Lab gate (also the empty-hash landing and ?book with the switch off): off, no footer, no Lab link, no Lab option in the
     review select, #/lab is not-found; on, the footer reads "Workspace" and "Simulator Lab" with href="#/lab", and #/lab opens the Lab;
   6 (IA-1b) no self-link: no a[href^="#/"] inside a [data-level] region whose iaCanon href has the current path and query;
   7 (IA-1b) reserved paths, static: no IA_ALIASES key matches an IA_ROUTES pattern, an IA_RAIL route or a tab route of the
     operator's Sites;
   8 (IA-1b) the operator's own addresses: a typed site/<another operator's Site> and decision/<another operator's decision> show
     not-found;
   9 (IA-1b) the landing: the empty hash renders iaStart().
   Hosts (D-IA.29): a planted run visits only its plant's host: the hosted plants run items 1, 3, 4 and 6 on the host and the crawl to
   depth 0; the Lab plants item 5; notfound the typed probe; aliaskey item 7; crossop item 8; landing item 9.
   10 (IA-1b, D-IA.35 L4) a scope never empties by address: another vertical's group:<g> and another operator's site:<k> render all the operator's Sites on Outcomes.
   Run: node tools/shape_check.cjs   Plants: SHAPE_PLANT=foreignscope|unlink|stub|rail|palette|primary|lab|tabstop|notfound|noact|lablegacy|
   selflink|aliaskey|crossop|linkprimary|landing|decprimary|stickyact (each must fail). */
const { boot, classifier, identity, liveRoutes, hrefsOf, OPS } = require('./ia_crawl.cjs');
const PLANT = process.env.SHAPE_PLANT || '';
const fails = [], log = [];
const atLevel = (n, html) => `const r = IA_ROUTES.find(x => x.id === ${n}), _r = r.render; r.render = ctx => _r(ctx).replace('<div data-level="${html[0]}">', '<div data-level="${html[0]}">${html[1]}');`;
const PLANTS = {
  unlink: `iaUnlink = function () {};`,
  stub: `{ const _l = iaLive; iaLive = h => /^#?\\/?site\\/kisiwa\\/health$/.test(String(h)) || _l(h); ${atLevel('iaStart()', ['L2', '<a href="#/site/kisiwa/health">Health</a>'])} }`,
  rail: `iaItemLanded = () => true;`,
  palette: `iaPaletteFilter = out => out;`,
  primary: `{ ${atLevel('iaStart()', ['L1', '<button class="button primary" data-ux-act="plant-a">A</button><button class="button primary" data-ux-act="plant-b">B</button>'])} }`,
  lab: `iaDev = () => true;`,
  tabstop: `{ const _r = iaRailHtml; iaRailHtml = r => _r(r).replace(/class="ia-rail-unavailable"/g, 'tabindex="0" class="ia-rail-unavailable"'); }`,
  notfound: `{ const _u = iaUnlink; iaUnlink = root => { if (root.querySelector('[data-shape="frame"]')) return; _u(root); }; }`,
  noact: `{ const r = IA_ROUTES.find(x => x.id === 'plan'), _r = r.render; r.render = ctx => _r(ctx).replace(/ data-(ux-)?act="[^"]*"/g, ''); }`,
  lablegacy: `{ const _r = rail; rail = s => _r(s).replace('</aside>', '<a href="#/lab">Simulator Lab</a></aside>'); }`,
  selflink: `{ ${atLevel('iaStart()', ['L2', '<a href="#/portfolio">Portfolio</a>'])} }`,
  aliaskey: `IA_ALIASES['portfolio/outcomes'] = 'portfolio';`,
  crossop: `iaSiteOk = k => !!SK[k]; iaDecOk = id => DEC.some(d => d.id === id);`,
  linkprimary: `{ ${atLevel('iaStart()', ['L2', '<a class="button primary" href="#/portfolio/outcomes">A</a><a class="button primary" href="#/plan">B</a>'])} }`,
  landing: `iaLanding = () => null;`,
  /* IA-1c (D-IA.23; host: the operator's first decision waiting with a recommendation; Harvest has none and skips them): a second
     "Choose this" opener in its L1; the sticky's opener pointed at another option's dialog */
  decprimary: `{ const r = IA_ROUTES.find(x => x.id === 'decision/:dec'), _r = r.render; r.render = ctx => { const d = decById(ctx.params.dec), o = d.opts.find(x => x !== uxRec(d) && !isNoAction(x)) || 'plant'; return _r(ctx).replace('<div data-level="L1">', '<div data-level="L1">' + uxOpener('uxc-' + d.id + '-' + o, 'Choose this', 'button primary')); }; }`,
  stickyact: `{ const r = IA_ROUTES.find(x => x.id === 'decision/:dec'), _r = r.render; r.render = ctx => { const h = _r(ctx), d = decById(ctx.params.dec), rec = uxRec(d), o = d.opts.find(x => x !== rec && !isNoAction(x)) || 'plant', i = h.indexOf('data-ux-sticky'), j = h.indexOf('</div>', i); return h.slice(0, i) + h.slice(i, j).replace('data-ux-drawer="uxc-' + d.id + '-' + rec + '"', 'data-ux-drawer="uxc-' + d.id + '-' + o + '"') + h.slice(j); }; }`,
  foreignscope: `iaCtx = eval('(' + iaCtx.toString().replace("kind === 'group' ? sites.some(k => iaVertical(k) === id)", "kind === 'group' ? true") + ')');`
};
const HOSTED = ['unlink', 'stub', 'rail', 'palette', 'primary', 'tabstop', 'noact', 'selflink', 'linkprimary', 'decprimary', 'stickyact'], DEC_HOSTED = ['decprimary', 'stickyact'];
const ITEM = { lab: 5, lablegacy: 5, notfound: 'probe', aliaskey: 7, crossop: 8, landing: 9, foreignscope: 10 };
if (PLANT && !PLANTS[PLANT]) { console.error(`shape_check: unknown plant ${PLANT}`); process.exit(2); }
const all = !PLANT, runs = n => all || ITEM[PLANT] === n;
const actOf = e => e.dataset.act || e.dataset.uxAct || (e.dataset.uxDrawer ? `drawer:${e.dataset.uxDrawer}` : '') || (e.getAttribute('href') ? `href:${e.getAttribute('href')}` : '');
/* items 1, 3, 4 and 6 on the page shown */
function onPage(B, r, bad, cls, state) {
  const { w, doc } = B, app = doc.getElementById('app'), fr = app.querySelectorAll('.ia-frame#ia-root'), s = w.eval('currentScreen()'), tag = `#/${r.id}${state ? ` (${state})` : ''}`;
  if (r.notFound && s.id !== 'not-found') { bad(`${tag}: does not show not-found (${s.id})`); return; }
  if (fr.length !== 1) { bad(`${tag}: ${fr.length} frame roots`); return; }
  const f = fr[0], sh = f.querySelectorAll(`[data-shape="${r.shape}"]`).length; if (sh !== 1) bad(`${tag}: ${sh} [data-shape="${r.shape}"]`);
  const lv = [...f.querySelectorAll('[data-level]')].map(e => e.dataset.level); if (lv.some((x, i) => i && x < lv[i - 1])) bad(`${tag}: levels decrease (${lv.join(',')})`);
  const h1 = f.querySelectorAll('h1').length + app.querySelectorAll('.reviewbar h1').length; if (h1 !== 1) bad(`${tag}: ${h1} h1`);
  const l1 = [...f.querySelectorAll('[data-level="L1"]')], k = l1.reduce((a, e) => a + e.querySelectorAll('.ux-kpi').length, 0); if (k > 4) bad(`${tag}: ${k} tiles in L1`);
  /* the primary rule (D-IA.23) */
  const prim = [...f.querySelectorAll('a.primary, button.primary')].filter(e => !e.closest('.ux-drawer')), say = e => `"${e.textContent.trim().slice(0, 30)}"`;
  prim.forEach(e => { if (!actOf(e)) bad(`${tag}: a primary that names no act (${say(e)})`); });
  [...f.querySelectorAll('[data-level]')].forEach(rg => { const n = prim.filter(e => e.closest('[data-level]') === rg).length; if (n > 1) bad(`${tag}: ${n} primaries in one ${rg.dataset.level} region`); });
  const page = prim.find(e => e.closest('[data-level]')), pageAct = page ? actOf(page) : undefined;
  prim.filter(e => !e.closest('[data-level]')).forEach(e => { if (!e.closest('[data-ux-sticky]') || pageAct === undefined || actOf(e) !== pageAct) bad(`${tag}: a primary outside every level that is not the sticky repeat of the page primary (${say(e)})`); });
  if (state) return { lv };
  const want = `${w.eval('currentScreen().title')} · ${B.opName}`; if (doc.title !== want) bad(`${tag}: document title "${doc.title}", not "${want}"`);
  /* 3 the rail */
  const rail = w.eval('IA_RAIL.map(i => ({ label: i.label, route: i.route, landed: IA_LANDED.has(i.unit) }))');
  for (const i of rail) { const un = f.querySelector(`.rail [data-rail-unavailable="${i.label}"]`), a = [...f.querySelectorAll('.rail a')].find(x => x.textContent.trim() === i.label);
    if (i.landed ? !(a && a.getAttribute('href') === `#/${i.route}`) : !(un && !un.closest('a') && !un.querySelector('a') && !un.hasAttribute('href') && /Not available yet/.test(un.textContent) && !a && !un.matches('[tabindex],button,a') && !un.querySelector('[tabindex],button,a'))) bad(`${tag}: rail item "${i.label}" is not ${i.landed ? 'a link to its route' : 'an unavailable root'}`); }
  /* 6 no self-link inside a level region */
  if (!r.notFound) { const here = w.location.hash.replace(/^#\//, '');
    f.querySelectorAll('[data-level] a[href^="#/"]').forEach(a => { const c = w.eval(`iaCanon(${JSON.stringify(a.getAttribute('href'))})`).replace(/^#\//, ''); if (c === here) bad(`${tag}: a self-link in ${a.closest('[data-level]').dataset.level} ("${a.textContent.trim().slice(0, 30)}")`); }); }
  if (r.notFound) for (const x of hrefsOf(doc)) { const c = cls(x); if (c !== 'good') bad(`${tag}: not-found links ${x} (${c})`); }
  return { lv };
}
(async () => {
  for (const op of OPS) {
    const B = await boot(op, 'plan'), { w, doc, go } = B, bad = m => fails.push(`${B.opName} · ${m}`);
    if (PLANT) w.eval(PLANTS[PLANT]);
    const start = w.eval('iaStart()'); await go(start);
    const cls = classifier(w, op);
    const decHost = w.eval(`(() => { const id = [...new Set(ATTN[${JSON.stringify(op)}].map(r => r[4]))].find(id => uxDecState(id).key === 'choose' && uxRec(decById(id))); return id ? 'decision/' + id : null; })()`);
    const host = PLANT === 'noact' ? 'plan' : DEC_HOSTED.includes(PLANT) ? decHost : start;
    if (DEC_HOSTED.includes(PLANT) && !host) { log.push(`${B.opName} · plant ${PLANT}: no decision waiting with a recommendation, skipped`); B.dom.window.close(); continue; }
    /* 1, 3, 4, 6: every live route (unplanted), the host (a hosted plant), the typed unknown address (unplanted and notfound) */
    const live = liveRoutes(w, op), probe = { id: 'x-unknown', shape: 'frame', notFound: true };
    const routes = all ? [...live, probe] : HOSTED.includes(PLANT) ? live.filter(r => r.id === host) : PLANT === 'notfound' ? [probe] : [];
    for (const r of routes) { await go(r.id); const o = onPage(B, r, bad, cls); if (o) log.push(`${B.opName} · #/${r.id} · ${r.notFound ? 'not-found' : r.shape} · levels ${o.lv.join(',') || 'none'}`); }
    /* item 1 in the two other states (unplanted only) */
    if (all) {
      const N = await boot(op, 'plan', { search: '?state=no-recommendation' }); for (const r of live) { await N.go(r.id); onPage(N, r, bad, cls, 'no-recommendation'); } N.dom.window.close();
      const first = w.eval(`(() => { const ids = [...new Set(ATTN[${JSON.stringify(op)}].map(r => r[4]))]; return ids.find(id => ['choose', 'none'].includes(uxDecState(id).key) && uxRec(decById(id))) || null; })()`);
      if (first) { w.eval(`uxMockSet({ ...uxMock(), chosen: { ...(uxMock().chosen || {}), ${JSON.stringify(first)}: uxRec(decById(${JSON.stringify(first)})) } })`);
        for (const r of live) { await go(r.id); onPage(B, r, bad, cls, `after choosing ${first}`); } w.eval('uxMockSet({})'); }
      log.push(`${B.opName} · item 1 in three states (default, no-recommendation, ${first ? `after choosing ${first}` : 'no waiting decision with a recommendation'})`);
    }
    /* 2 the crawl, from the start, with the palette's targets as start-route edges; a hosted plant crawls the host to depth 0 */
    if (all || HOSTED.includes(PLANT)) {
      await go(host); w.eval('uxPalette(true)'); const pal = [...doc.querySelectorAll('#ux-cmd-list [data-go]')].map(li => '#/' + li.dataset.go); w.eval('uxPalette(false)');
      const seen = new Set([identity(host)]), queue = [[host, 0]], maxD = all ? 6 : 0;
      while (queue.length) { const [h, d] = queue.shift(); await go(h);
        const hs = [...hrefsOf(doc), ...(h === host ? pal : [])];
        for (const x of hs) { const c = cls(x); if (c !== 'good') { bad(`crawl: #/${h} links ${x} (${c})`); continue; } const id = identity(x); if (!seen.has(id) && d < maxD) { seen.add(id); queue.push([x.replace(/^#\//, ''), d + 1]); } } }
      log.push(`${B.opName} · crawl from #/${host} to depth ${maxD}: ${seen.size} route identities, ${pal.length} palette entries`);
    }
    /* 5 the Lab gate */
    if (runs(5)) {
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
      await go(''); if (doc.querySelector('#app a[href^="#/lab"]')) bad('Lab gate: a Lab link on the empty-hash landing with the switch off');
      const BK = await boot(op, '', { search: '?book' }); if (PLANT) BK.w.eval(PLANTS[PLANT]); await BK.go('');
      if (BK.doc.querySelector('#book-lab')) bad('Lab gate: ?book lists the Lab with the switch off'); if (BK.doc.querySelector('#app a[href^="#/lab"]')) bad('Lab gate: a Lab link in ?book with the switch off'); BK.dom.window.close();
    }
    /* 7 reserved paths (static; its own matching) */
    if (runs(7)) {
      const S = w.eval(`(() => { const sites = OPS[${JSON.stringify(op)}].sites, decs = DEC.filter(d => sites.includes(d.site)).map(d => d.id);
        const ex = p => { let ids = [p]; if (p.includes(':site')) ids = ids.flatMap(x => sites.map(s => x.replace(':site', s))); if (p.includes(':dec')) ids = ids.flatMap(x => decs.map(d => x.replace(':dec', d))); return ids; };
        const reserved = new Set([...IA_ROUTES.flatMap(r => ex(r.id)), ...IA_RAIL.map(i => i.route), ...sites.flatMap(s => Object.values(IA_TAB_GROUPS).flatMap(g => g({ site: s }).map(([, id]) => id)))]);
        return { keys: Object.keys(IA_ALIASES).map(k => [k, ex(k)]), reserved: [...reserved] }; })()`);
      const R = new Set(S.reserved); S.keys.forEach(([k, xs]) => { const hit = xs.find(x => R.has(x)); if (hit) bad(`reserved paths: the alias key "${k}" matches the route "${hit}"`); });
      log.push(`${B.opName} · reserved paths: ${S.keys.length} alias keys against ${R.size} reserved paths`);
    }
    /* 8 another operator's Site and decision show not-found */
    if (runs(8)) {
      const X = w.eval(`(() => { const mine = OPS[${JSON.stringify(op)}].sites, s = Object.keys(SK).filter(k => !mine.includes(k)); return [...s.map(k => 'site/' + k), ...DEC.filter(d => !mine.includes(d.site)).map(d => 'decision/' + d.id)]; })()`);
      for (const h of X) { await go(h); const id = w.eval('currentScreen().id'); if (id !== 'not-found' || !doc.querySelector('#ia-root [data-shape="frame"]')) bad(`own addresses: #/${h} shows ${id}, not not-found`); }
      log.push(`${B.opName} · own addresses: ${X.length} addresses of other operators typed`);
    }
    /* 9 the landing */
    if (runs(9)) { await go(''); const id = w.eval('currentScreen().id'); if (id !== start || !doc.getElementById('ia-root')) bad(`landing: the empty hash renders ${id}${doc.getElementById('ia-root') ? '' : ' (the legacy screen, outside the frame)'}, not ${start} in the frame`); }
    /* 10 a scope never empties by address */
    if (runs(10)) {
      const X = w.eval(`(() => { const mine = OPS[${JSON.stringify(op)}].sites, have = new Set(mine.map(iaVertical)), g = ['mini', 'cold', 'ev'].find(x => !have.has(x)), s = Object.keys(SK).find(k => !mine.includes(k)); return { n: mine.length, scopes: ['group:' + g, 'site:' + s] }; })()`);
      for (const sc of X.scopes) { await go(`portfolio/outcomes?scope=${sc}`); const n = doc.querySelectorAll('.ia-outcomes tr[data-site]').length; if (n !== X.n) bad(`foreign scope: #/portfolio/outcomes?scope=${sc} renders ${n} rows, expected ${X.n}`); }
      log.push(`${B.opName} · foreign scopes: ${X.scopes.join(', ')} render all ${X.n} Sites`);
    }
    if (B.errors.length) bad(`script errors: ${B.errors.slice(0, 2).join(' | ')}`);
    B.dom.window.close();
  }
  log.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `shape_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${[...new Set(fails)].slice(0, 12).join('\n  ')}` : `shape_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
})();
