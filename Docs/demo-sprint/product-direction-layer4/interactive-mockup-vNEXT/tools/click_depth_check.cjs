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
   Run: node tools/click_depth_check.cjs   Plants: G1_PLANT=engine, details (every unit), tile, driver, hidden, closed, siteclosed (from IA-1b), inbox (IA-1c).
   D-IA.32: a closed details is a node <owner>#details=<k> (k its id, else its index among the owner's details); its summary is the owner's edge to it. */
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
  const hidden = o.hidden || PLANT === 'hidden', nodet = PLANT === 'details', E = [], node = el => el.matches('[data-ux-drawer]') ? `${page}#drawer=${el.dataset.uxDrawer}` : identity(el.getAttribute('href').replace(/^#\//, ''));
  const kind = el => el.closest('[data-ia-inbox]') || el.matches('[data-ia-inbox]') || el.closest('#ia-inbox') ? 'inbox' : el.closest('[data-level="L2"] .ux-queue') ? 'queue' : 'any';
  const sel = 'a[href^="#/"], [data-ux-drawer]';
  /* D-IA.32: a closed details is a node, "<owner>#details=<k>"; its summary is the owner's edge to it; what is inside it is its edge, never the owner's */
  const ownerEl = el => el.closest('.ux-drawer[id]'), ownerName = el => { const d = ownerEl(el); return d ? `${page}#drawer=${d.id}` : page; };
  const nearestClosed = el => { let d = el.parentElement && el.parentElement.closest('details:not([open])'); while (d) { const sm = el.closest('summary'); if (!(sm && sm.parentElement === d)) return d; d = d.parentElement && d.parentElement.closest('details:not([open])'); } return null; };
  const detNode = d => { const od = ownerEl(d), scope = od || root, all = [...scope.querySelectorAll('details')].filter(x => ownerEl(x) === od); return `${ownerName(d)}#details=${d.id || all.indexOf(d)}`; };
  const from = el => { const c = nearestClosed(el); return !nodet && c ? detNode(c) : ownerName(el); };
  const onPage = [...root.querySelectorAll(`.tabs a[href^="#/"], .ux-tabs a[href^="#/"], [data-level] a[href^="#/"], [data-level] [data-ux-drawer], [data-ia-inbox]`)]
    .filter(el => hidden || !el.closest('.ux-drawer')).filter(el => !el.closest('.rail, .breadcrumbs, .ux-scope-sw, .searchbox'));
  onPage.forEach(el => E.push([hidden ? page : from(el), el.textContent.trim().slice(0, 40), node(el), kind(el)]));
  root.querySelectorAll('.ux-drawer[id]').forEach(d => d.querySelectorAll(sel).forEach(el => { if (el.closest('.ux-drawer') === d) E.push([hidden ? `${page}#drawer=${d.id}` : from(el), el.textContent.trim().slice(0, 40), node(el), kind(el)]); }));
  if (!nodet) root.querySelectorAll('details:not([open])').forEach(d => { const sm = [...d.children].find(c => c.tagName === 'SUMMARY'); if (!sm || d.closest('.rail, .breadcrumbs, .ux-scope-sw, .searchbox') || !(ownerEl(d) || d.closest('[data-level]') || d.closest('.tabs, .ux-tabs'))) return;
    const par = d.parentElement && d.parentElement.closest('details:not([open])'), pn = par ? detNode(par) : ownerName(d); if (hidden && !par) return; E.push([pn, sm.textContent.trim().slice(0, 40), detNode(d), 'any']); });
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
  closed: `{ const r = IA_ROUTES.find(x => x.id === 'portfolio'), _r = r.render; r.render = ctx => _r(ctx).replace(/<a[^>]*href="#\\/portfolio\\/act-first\\/plan"[^>]*>[\\s\\S]*?<\\/a>/, m => '<details><summary>More</summary>' + m + '</details>'); }`,
  siteclosed: `shapeHubSite = eval('(' + shapeHubSite.toString().replace('3, true)', '3, false)') + ')');`,
  /* IA-1c: one waiting decision dropped from the inbox rows (its via-inbox surface becomes unreached) */
  inbox: `{ const _f = iaInboxDrawer; iaInboxDrawer = op => _f(op).replace(/<li><a href="#\\/decision\\/[^"]*" data-ia-row="decision:[^"]*">[\\s\\S]*?<\\/a><\\/li>/, ''); }`,
  driver: `{ const r = IA_ROUTES.find(x => x.id === 'site/:site'), _r = r.render; r.render = ctx => _r(ctx).replace(/data-ux-drawer="(uxsdrv-[^"]*)"/g, 'data-ux-plant="$1"'); }`
};
(async () => {
  /* self-test 2: the edge reader on a fixed DOM fixture */
  { const B0 = await boot('lakeside', 'plan'), d = B0.doc, fx = d.createElement('div');
    fx.innerHTML = '<div data-level="L2"><a href="#/fixture-a">A</a><button type="button" data-ux-drawer="fixture-d">Open D</button><div class="ux-drawer" id="fixture-d" data-open="false"><a href="#/fixture-b">B</a></div><details><summary>S</summary><a href="#/fixture-c">C</a><button type="button" data-ux-drawer="fixture-e">E</button></details><details open><summary>O</summary><a href="#/fixture-f">F</a></details></div><div class="ux-drawer" id="fixture-e" data-open="false"></div>'; /* D sits inside the region, as a section's drawer does; E outside both details */
    const E = readEdges(fx, 'page').map(([f, , t]) => `${f} -> ${t}`), want = ['page -> fixture-a', 'page -> page#drawer=fixture-d', 'page#drawer=fixture-d -> fixture-b', 'page -> page#details=0', 'page#details=0 -> fixture-c', 'page#details=0 -> page#drawer=fixture-e', 'page -> fixture-f'];
    want.forEach(x => { if (!E.includes(x)) fails.push(`edge reader: missing ${x}`); }); if (E.includes('page -> fixture-b')) fails.push('edge reader: a link inside a closed drawer read as a step from its page (page -> fixture-b)'); ['page -> fixture-c', 'page -> page#drawer=fixture-e'].forEach(x => { if (E.includes(x)) fails.push(`edge reader: a link inside a closed disclosure read as a step from its page (${x})`); });
    out.push(`edge reader · fixture · ${E.join(', ')}`);
    const landed = B0.w.eval('!!iaLanded("portfolio")'); B0.dom.window.close();
    if (!landed) { if (['tile', 'driver', 'hidden', 'closed', 'siteclosed', 'inbox'].includes(PLANT)) { console.error(`click_depth_check: plant ${PLANT} applies from IA-1b`); process.exit(2); }
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
