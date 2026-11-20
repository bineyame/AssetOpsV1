/* IA-1 click-depth check, guardrail G1 (spec §2.5, §2.8; D-IA.10 measured as D-IA.18 and D-IA.21), jsdom.
   Nodes are pages (the route) and drawers ("<route>#drawer=<element id>"). A page's edges are the a[href^="#/"] and [data-ux-drawer]
   openers inside its header tabs, its [data-level] regions and the "Waiting for you" control ([data-ia-inbox]), never inside any
   .ux-drawer; an opener is an edge to the drawer node it names. A drawer node's edges are the links and openers inside that drawer
   element only. The rail, the breadcrumb, the scope menu and search are not edges. Origin: #/portfolio (from IA-1b).
   Surfaces come from IA_G1_SURFACES() ({ op, surface, route, limit, via }); via "queue" walks only the links in portfolio's L2
   .ux-queue, via "inbox" only the [data-ia-inbox] control and #ia-inbox a[data-ia-row]. A surface with route null prints n/a.
   Self-tests (every unit): a fixed synthetic graph with its expected depths (a drawer reached by an opener among them), and the edge
   reader on a fixed DOM fixture (a level region holding link A, an opener to drawer D and the closed D itself, with link B inside D): it must read
   page -> A, page -> D and D -> B, never page -> B.
   Output: one line per surface, "op · surface · depth · path".
   Run: node tools/click_depth_check.cjs   Plants: G1_PLANT=engine (every unit), tile, driver, hidden (from IA-1b), inbox (IA-1c). */
const { boot, identity, OPS } = require('./ia_crawl.cjs');
const PLANT = process.env.G1_PLANT || '';
const fails = [], out = [];
/* the engine: breadth-first depth from an origin over a graph { node: [[label, target], ...] }; returns depth and path */
function bfs(graph, origin) {
  const dist = new Map([[origin, { d: 0, path: [origin] }]]), q = [origin];
  while (q.length) { const n = q.shift(), cur = dist.get(n); for (const [, t] of graph[n] || []) if (!dist.has(t)) { dist.set(t, { d: cur.d + 1, path: [...cur.path, t] }); q.push(t); } }
  return dist;
}
/* the edge reader: the page's content edges, and each drawer's own; kinds mark the queue and inbox edges */
function readEdges(root, page, o = {}) {
  const hidden = o.hidden || PLANT === 'hidden', E = [], node = el => el.matches('[data-ux-drawer]') ? `${page}#drawer=${el.dataset.uxDrawer}` : identity(el.getAttribute('href').replace(/^#\//, ''));
  const kind = el => el.closest('[data-ia-inbox]') || el.matches('[data-ia-inbox]') || el.closest('#ia-inbox') ? 'inbox' : el.closest('[data-level="L2"] .ux-queue') ? 'queue' : 'any';
  const sel = 'a[href^="#/"], [data-ux-drawer]';
  const onPage = [...root.querySelectorAll(`.tabs a[href^="#/"], .ux-tabs a[href^="#/"], [data-level] a[href^="#/"], [data-level] [data-ux-drawer], [data-ia-inbox]`)]
    .filter(el => hidden || !el.closest('.ux-drawer')).filter(el => !el.closest('.rail, .breadcrumbs, .ux-scope-sw, .searchbox'));
  onPage.forEach(el => E.push([page, el.textContent.trim().slice(0, 40), node(el), kind(el)]));
  root.querySelectorAll('.ux-drawer[id]').forEach(d => d.querySelectorAll(sel).forEach(el => { if (el.closest('.ux-drawer') === d) E.push([`${page}#drawer=${d.id}`, el.textContent.trim().slice(0, 40), node(el), kind(el)]); }));
  return E;
}
/* self-test 1: a fixed synthetic graph with its expected depths */
const SELF = {
  'Overview': [['tab', 'Outcomes'], ['tile', 'Plan'], ['queue row', 'Decision A'], ['inbox control', 'Inbox']],
  'Inbox': [['inbox row', 'Decision B'], ['inbox row', 'Plan']],
  'Outcomes': [['row', 'Site']],
  'Site': [['driver opener', 'Site#drawer=driver']],
  'Site#drawer=driver': [['names', 'Decision A']]
};
const EXPECT = { 'Overview': 0, 'Outcomes': 1, 'Plan': 1, 'Decision A': 1, 'Inbox': 1, 'Decision B': 2, 'Site': 2, 'Site#drawer=driver': 3 };
if (PLANT === 'engine') SELF.Overview = SELF.Overview.filter(([l]) => l !== 'tile'); /* one self-test edge removed */
{ const dist = bfs(SELF, 'Overview');
  for (const [n, want] of Object.entries(EXPECT)) { const got = dist.get(n); const d = got ? got.d : '∞';
    out.push(`self-test · ${n} · ${d} · ${got ? got.path.join(' › ') : 'unreached'}`); if (d !== want) fails.push(`self-test: ${n} at depth ${d}, expected ${want}`); } }
/* the app plants (from IA-1b): the Overview's plan tile link removed; the Site board's driver openers lose data-ux-drawer */
const APP = {
  tile: `{ const r = IA_ROUTES.find(x => x.id === 'portfolio'), _r = r.render; r.render = ctx => _r(ctx).replace(/<a[^>]*href="#\\/portfolio\\/act-first\\/plan"[^>]*>([\\s\\S]*?)<\\/a>/, '$1'); }`,
  driver: `{ const r = IA_ROUTES.find(x => x.id === 'site/:site'), _r = r.render; r.render = ctx => _r(ctx).replace(/data-ux-drawer="(uxsdrv-[^"]*)"/g, 'data-ux-plant="$1"'); }`
};
(async () => {
  /* self-test 2: the edge reader on a fixed DOM fixture */
  { const B0 = await boot('lakeside', 'plan'), d = B0.doc, fx = d.createElement('div');
    fx.innerHTML = '<div data-level="L2"><a href="#/fixture-a">A</a><button type="button" data-ux-drawer="fixture-d">Open D</button><div class="ux-drawer" id="fixture-d" data-open="false"><a href="#/fixture-b">B</a></div></div>'; /* D sits inside the region, as a section's drawer does */
    const E = readEdges(fx, 'page').map(([f, , t]) => `${f} -> ${t}`), want = ['page -> fixture-a', 'page -> page#drawer=fixture-d', 'page#drawer=fixture-d -> fixture-b'];
    want.forEach(x => { if (!E.includes(x)) fails.push(`edge reader: missing ${x}`); }); if (E.includes('page -> fixture-b')) fails.push('edge reader: a link inside a closed drawer read as a step from its page (page -> fixture-b)');
    out.push(`edge reader · fixture · ${E.join(', ')}`);
    const landed = B0.w.eval('!!iaLanded("portfolio")'); B0.dom.window.close();
    if (!landed) { if (['tile', 'driver', 'hidden', 'inbox'].includes(PLANT)) { console.error(`click_depth_check: plant ${PLANT} applies from IA-1b`); process.exit(2); }
      out.push('G1: origin lands in IA-1b; 0 live surfaces'); return finish(); } }
  for (const op of OPS) { const B = await boot(op, 'portfolio'); if (APP[PLANT]) B.w.eval(APP[PLANT]);
    const graph = {}, kinds = {}, q = ['portfolio'], seen = new Set(q);
    while (q.length) { const h = q.shift(); await B.go(h);
      for (const [f, l, t, k] of readEdges(B.doc.getElementById('ia-root') || B.doc.body, identity(h))) { (graph[f] = graph[f] || []).push([l, t]); (kinds[f] = kinds[f] || []).push([l, t, k]);
        const page = t.split('#drawer=')[0]; if (!seen.has(page) && seen.size < 400) { seen.add(page); q.push(page); } } }
    const only = k => Object.fromEntries(Object.entries(kinds).map(([n, es]) => [n, n === 'portfolio' || k === 'inbox' ? es.filter(e => e[2] === k) : es]));
    const D = { any: bfs(graph, 'portfolio'), queue: bfs({ portfolio: (kinds.portfolio || []).filter(e => e[2] === 'queue') }, 'portfolio'), inbox: bfs(only('inbox'), 'portfolio') };
    const S = B.w.eval('typeof IA_G1_SURFACES === "function" ? IA_G1_SURFACES() : []').filter(x => x.op === op);
    for (const s of S) { if (!s.route) { out.push(`${B.opName} · ${s.surface} · n/a · ${s.na || 'no surface'}`); continue; }
      const g = D[s.via || 'any'].get(s.route), d = g ? g.d : '∞';
      out.push(`${B.opName} · ${s.surface} · ${d} · ${g ? g.path.join(' › ') : 'unreached'}${s.via && s.via !== 'any' ? ` (via ${s.via})` : ''}`); if (!g || g.d > s.limit) fails.push(`${B.opName} · ${s.surface}: depth ${d} > ${s.limit}`); }
    out.push(`${B.opName} · graph: ${Object.keys(graph).length} nodes with edges, ${seen.size} pages`);
    B.dom.window.close(); }
  finish();
})();
function finish() {
  out.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `click_depth_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${fails.join('\n  ')}` : `click_depth_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
}
