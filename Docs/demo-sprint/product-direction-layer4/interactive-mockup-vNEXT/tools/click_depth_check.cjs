/* IA-1 click-depth check, guardrail G1 (spec §2.5, D-IA.10 measured as D-IA.18), jsdom.
   Edges are content edges only: header tab links, and links, rows and tiles inside [data-level] regions, plus the "Waiting for
   you" control and its drawer rows. The rail, the breadcrumb, the scope menu and search are not edges. A drawer opened by a
   link is a node (?drawer=). Origin: #/portfolio. Until IA-1b lands there is no origin and no live surface; the engine's
   self-test runs in every unit. Output: one line per surface, "op · surface · depth · path".
   Run: node tools/click_depth_check.cjs   Plants: G1_PLANT=engine (every unit), tile (from IA-1b), inbox (from IA-1c). */
const { boot, identity, OPS } = require('./ia_crawl.cjs');
const PLANT = process.env.G1_PLANT || '';
const fails = [], out = [];
/* the engine: breadth-first depth from an origin over a graph { node: [[label, target], ...] }; returns depth and path */
function bfs(graph, origin) {
  const dist = new Map([[origin, { d: 0, path: [origin] }]]), q = [origin];
  while (q.length) { const n = q.shift(), cur = dist.get(n); for (const [, t] of graph[n] || []) if (!dist.has(t)) { dist.set(t, { d: cur.d + 1, path: [...cur.path, t] }); q.push(t); } }
  return dist;
}
/* the self-test: a fixed synthetic graph with its expected depths */
const SELF = {
  'Overview': [['tab', 'Outcomes'], ['tile', 'Plan'], ['queue row', 'Decision A'], ['inbox control', 'Inbox']],
  'Inbox': [['inbox row', 'Decision B'], ['inbox row', 'Plan']],
  'Outcomes': [['row', 'Site']],
  'Site': [['driver row', 'Driver drawer']],
  'Driver drawer': [['names', 'Decision A']]
};
const EXPECT = { 'Overview': 0, 'Outcomes': 1, 'Plan': 1, 'Decision A': 1, 'Inbox': 1, 'Decision B': 2, 'Site': 2, 'Driver drawer': 3 };
if (PLANT === 'engine') SELF.Overview = SELF.Overview.filter(([l]) => l !== 'tile'); /* one self-test edge removed */
{ const dist = bfs(SELF, 'Overview');
  for (const [n, want] of Object.entries(EXPECT)) { const got = dist.get(n); const d = got ? got.d : '∞';
    out.push(`self-test · ${n} · ${d} · ${got ? got.path.join(' › ') : 'unreached'}`); if (d !== want) fails.push(`self-test: ${n} at depth ${d}, expected ${want}`); } }
/* the content edges of the rendered page (used once the origin is live) */
function contentEdges(doc) {
  const inFrame = [...doc.querySelectorAll('#ia-root [data-level] a[href^="#/"], #ia-root .ux-tabs a[href^="#/"], #ia-root .tabs a[href^="#/"], #ia-root [data-ia-inbox] a[href^="#/"], #ia-root a[data-ia-inbox][href^="#/"]')];
  return inFrame.filter(a => !a.closest('.rail, .breadcrumbs, .ux-scope-sw, .searchbox')).map(a => [a.textContent.trim().slice(0, 40), a.getAttribute('href').replace(/^#\//, '')]);
}
(async () => {
  const B0 = await boot('lakeside', 'plan'), landed = B0.w.eval('!!iaLanded("portfolio")'); B0.dom.window.close();
  if (!landed) {
    if (PLANT === 'tile' || PLANT === 'inbox') { console.error(`click_depth_check: plant ${PLANT} applies from ${PLANT === 'tile' ? 'IA-1b' : 'IA-1c'}`); process.exit(2); }
    out.push('G1: origin lands in IA-1b; 0 live surfaces');
  } else {
    /* the live graph per operator, over content edges to 6 hops; surfaces and their limits are added by the units that land them */
    for (const op of OPS) { const B = await boot(op, 'portfolio'), graph = {}, q = ['portfolio'], seen = new Set(q);
      while (q.length) { const h = q.shift(); await B.go(h); graph[h] = contentEdges(B.doc); for (const [, t] of graph[h]) { const id = identity(t); if (!seen.has(id) && seen.size < 400) { seen.add(id); q.push(t); } } }
      const dist = bfs(graph, 'portfolio'), S = B.w.eval('typeof IA_G1_SURFACES === "function" ? IA_G1_SURFACES() : []');
      for (const s of S.filter(x => x.op === op)) { const g = dist.get(s.route), d = g ? g.d : '∞'; out.push(`${B.opName} · ${s.surface} · ${d} · ${g ? g.path.join(' › ') : 'unreached'}`); if (!g || g.d > s.limit) fails.push(`${B.opName} · ${s.surface}: depth ${d} > ${s.limit}`); }
      B.dom.window.close(); }
  }
  out.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `click_depth_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${fails.join('\n  ')}` : `click_depth_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
})();
