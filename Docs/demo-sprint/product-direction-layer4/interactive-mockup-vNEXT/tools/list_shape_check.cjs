/* IA-2b1 list shape check (spec-IA-2b §8 rows 1 to 4; D-IA.62, D-IA.66 to D-IA.70, D-IA.73, D-IA.80), jsdom. Runs only when IA_LANDED has
   IA-2b1 (or IA_FORCE_LANDED=IA-2b1); otherwise prints "IA-2b1 not landed; dormant" and exits 0.
   A synthetic: iaListModel and iaListHref on a 25-item store in 3 groups (the only block that calls the list's code).
   B live: every operator x the four lists x the views of spec §8 row 2, against its own rows and literal tables (D-IA.73).
   C the scope menu on a list. D the fixture (tools/list_fixture.cjs), rendered by the real route.
   Plants (LIST_PLANT): A cap, keep, scope, search, sort, invalid, group, canon, tier; B tile, rowctl, restore, own, stakesort, notarget;
   C scopemenu, foldquery, palettealias; D remainder (tier and group also bite D). A source plant rewrites the product function at its rule; a rule the source
   lacks exits 2, so a plant cannot pass unbitten. */
const { boot, OPS, sleep, classifier } = require('./ia_crawl.cjs');
const F = require('./list_fixture.cjs');
const PLANT = process.env.LIST_PLANT || '';
const money = s => { const m = String(s).replace(/,/g, '').match(/([−-])?\$(\d+(?:\.\d+)?)/); return m ? (m[1] ? -1 : 1) * parseFloat(m[2]) : NaN; };
/* the rules the source plants rewrite: [function, [from, to]...]; the strings are the component's (unit 3) */
const SRC = {
  cap: ['iaListModel', ['rank.slice(0, IA_LIST_CAP)', 'rank']],
  keep: ['iaListModel', ['def.keep ? [...rows.filter(def.keep), ...rows.filter(it => !def.keep(it))] : rows', 'rows']],
  scope: ['iaListModel', ['items.filter(it => iaInScope(def.site(it), scope))', 'items.slice()']],
  search: ['iaListModel', ['words.every(x => t.includes(x))', 'words.some(x => t.includes(x))']],
  sort: ['iaListModel', ['sort.cmp(a, b) || i - j', 'sort.cmp(a, b) || j - i']],
  invalid: ['iaListModel', ['f.options().some(([o]) => String(o) === String(v))', 'true']],
  group: ['iaListModel', ['n > IA_LIST_CAP && gs.length > 1', 'false']],
  canon: ['iaListHref', ['v.sort !== def.sorts[0].key', '!!v.sort']],
  tier: ['iaListTier', ['ns <= IA_LIST_CAP ? 1 : 2', '2']],
  tile: ['iaListTiles', ['const n = m.n;', 'const n = m.shown.length;']],
  palettealias: ['iaPaletteFilter', [' && !iaIsListAlias(id)', '']],
  foldquery: ['shapeHubOutcomes', ['{ ...ctx, query: {} }', 'ctx']],
  scopemenu: ['iaScopeEntries', ["route && route.shape === 'list'", 'false']] };
const BLOCK = { cap: 'A', keep: 'AD', scope: 'A', search: 'A', sort: 'A', invalid: 'A', group: 'AD', canon: 'A', tier: 'AD', scopemenu: 'C', foldquery: 'C', palettealias: 'C', remainder: 'D', tile: 'BD', rowctl: 'B', restore: 'B', own: 'B', stakesort: 'B', notarget: 'B' };
if (PLANT && !BLOCK[PLANT]) { console.error(`list_shape_check: unknown plant ${PLANT}`); process.exit(2); }
function plantSource(w, block) {
  if (!PLANT || !BLOCK[PLANT].includes(block)) return;
  if (SRC[PLANT]) { const [fn, ...rules] = SRC[PLANT]; const ok = w.eval(`(() => { if (typeof ${fn} !== 'function') return 'no function ${fn}'; let s = ${fn}.toString(); for (const [a, b] of ${JSON.stringify(rules)}) { if (!s.includes(a)) return 'plant found no rule: ' + a; s = s.split(a).join(b); } (0, eval)('${fn} = ' + s); return ''; })()`);
    if (ok) { console.log(`list_shape_check (plant ${PLANT}): ${ok}`); process.exit(2); } w.eval('render()'); return; }
  if (PLANT === 'remainder') { w.eval(`(() => { const d = IA_LIST_DEFS.sites, m = d.more; d.more = () => ''; })()`); return; }
  /* B's window plants (D-IA.73): each changes the product in the booted window only; a seam the window lacks exits 2 */
  const no = why => { console.log(`list_shape_check (plant ${PLANT}): ${why}`); process.exit(2); };
  if (PLANT === 'rowctl') { const o = w.shapeList; if (typeof o !== 'function') no('no function shapeList');
    w.shapeList = (ctx, key) => { const h = o(ctx, key); return key !== 'decisions' ? h : String(h).replace(/(<tr data-row="[^"]*"[^>]*>[\s\S]*?)(<\/tr>)/g, (m, a, b) => { PLANT_HITS.n++; return `${a}<td data-label="Choose"><button type="button" class="button">Choose</button></td>${b}`; }); }; }
  if (PLANT === 'restore') { const o = w.iaListModel; if (typeof o !== 'function' || w.eval('typeof IA_LIST_KEEP') === 'undefined') no('no iaListModel or IA_LIST_KEEP');
    /* the address's sort and facets ignored unless the render follows the list's own listener (a fresh boot or a typed address) */
    w.iaListModel = (d, it, q, s) => o(d, it, w.eval('IA_LIST_KEEP') ? q : Object.fromEntries(Object.entries(q || {}).filter(([k]) => k === 'q' || k === 'show')), s); }
  if (PLANT === 'own') { const d = w.eval("typeof IA_LIST_DEFS === 'object' ? IA_LIST_DEFS.findings : null"); if (!d || typeof d.items !== 'function') no('no IA_LIST_DEFS.findings.items'); const o = d.items; d.items = op => o(op).slice(0, -1); }
  if (PLANT === 'stakesort') { const ok = w.eval("typeof IA_LIST_DEFS === 'object' && Array.isArray(IA_LIST_DEFS.decisions?.sorts) ? (IA_LIST_DEFS.decisions.sorts.push({ key: 'stake', word: 'At stake', cmp: (a, b) => 0 }), true) : false"); if (!ok) no('no IA_LIST_DEFS.decisions.sorts array'); }
  if (PLANT === 'notarget') { const why = w.eval(`(() => { const op = LS.op, names = OPS[op].sites.map(k => SK[k].name), f = (HC.findings || []).find(f => f.decision && decById(f.decision) && names.includes(String(f.site).replace(/^Room [A-C] · /, '')));
    if (!f) return 'no Finding of ' + op + ' with a decision'; f.decision = 'removed-' + f.decision; return ''; })()`); if (why) no(why); } /* the Finding's link to its decision removed (the decision stays: other stores still point to it) */
  w.eval('render()');
}
const PLANT_HITS = { n: 0 };
/* ---- Block A: synthetic (the only block that calls the model, D-IA.73) ---- */
async function blockA(fails, log) {
  const B = await boot('lakeside', 'portfolio'), { w } = B;
  if (!w.eval("typeof iaListModel === 'function' && typeof iaListHref === 'function'")) { fails.push('A: the window has no iaListModel or iaListHref (the component is not built)'); B.dom.window.close(); return; }
  plantSource(w, 'A');
  /* the store: 25 items over real Sites of the three verticals (own classifier over SK types, never iaVertical) */
  const SKT = w.eval('Object.fromEntries(Object.entries(SK).map(([k, v]) => [k, v.type]))'), vert = k => SKT[k] === 'Mini-grid' ? 'mini' : /^Cold room/.test(SKT[k]) ? 'cold' : 'ev';
  const byV = { mini: [], cold: [], ev: [] }; Object.keys(SKT).forEach(k => byV[vert(k)].push(k));
  if (Object.values(byV).some(a => !a.length)) { fails.push('A: SK lacks a Site of one vertical'); B.dom.window.close(); return; }
  const G = ['mini', 'cold', 'ev'], WORDS = ['alpha beta', 'beta gamma', 'gamma alpha', 'delta', 'alpha <b>beta</b> delta'];
  const items = [...Array(25)].map((_, i) => { const g = G[i % 3]; return { id: `i${i}`, site: byV[g][i % byV[g].length], g, f: ['a', 'b', 'c'][i % 3 === 2 ? 2 : i % 2], v: (i * 7) % 5, t: WORDS[i % 5], keep: i === 21 || i === 24 }; /* v 2 and 3: outside the sort's top 10 (v 0 and 1), so only keep-first shows them (IA-2b1 unit 3: i20/i23 sat inside it and the keep plant passed A) */ });
  /* the def: sorts by v (ties in store order) and by id descending; one facet f; keep on the keep flag; grouped by g */
  w.eval(`IA_LIST_DEFS.__a = { key: '__a', site: it => it.site, text: it => it.t, keep: it => it.keep, group: it => it.g,
    facets: [{ key: 'f', label: 'F', all: 'All f', options: () => [['a', 'A'], ['b', 'B'], ['c', 'C']], of: it => it.f }],
    sorts: [{ key: 'v', word: 'V', cmp: (a, b) => a.v - b.v }, { key: 'idd', word: 'Id', cmp: (a, b) => (b.id > a.id) - (b.id < a.id) }] }`);
  const M = (q, scope, its = items) => w.eval(`(() => { const m = iaListModel(IA_LIST_DEFS.__a, ${JSON.stringify(its)}, ${JSON.stringify(q || {})}, ${JSON.stringify(scope || { kind: 'all' })});
    const id = x => x.id; return { rows: m.rows.map(id), shown: m.shown.map(id), hidden: m.hidden.map(id), n: m.n, ns: m.ns, tier: m.tier, groups: m.groups }; })()`);
  const ids = a => a.map(x => x.id), stable = (a, cmp) => a.map((x, i) => [x, i]).sort(([x, i], [y, j]) => cmp(x, y) || i - j).map(([x]) => x);
  const byv = a => stable(a, (x, y) => x.v - y.v), eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  /* scope: all, group and Site */
  const mAll = M({}, { kind: 'all' }), mG = M({}, { kind: 'group', id: 'cold' }), sk = items[4].site, mS = M({}, { kind: 'site', id: sk });
  if (mAll.ns !== 25) fails.push(`A scope all: ns ${mAll.ns}, expected 25`);
  const wantG = items.filter(x => vert(x.site) === 'cold'), wantS = items.filter(x => x.site === sk);
  if (mG.ns !== wantG.length || !eq(mG.rows.slice().sort(), ids(wantG).sort())) fails.push(`A scope group:cold: ${mG.ns} items, expected ${wantG.length}`);
  if (mS.ns !== wantS.length || !eq(mS.rows.slice().sort(), ids(wantS).sort())) fails.push(`A scope site:${sk}: ${mS.ns} items, expected ${wantS.length}`);
  /* the tier at 2, 3, 10, 11 and 25 items (D-IA.67) */
  const tiers = [2, 3, 10, 11, 25].map(k => [k, M({}, null, items.slice(0, k)).tier]), wantT = { 2: 0, 3: 1, 10: 1, 11: 2, 25: 2 };
  tiers.forEach(([k, t]) => { if (t !== wantT[k]) fails.push(`A tier at ${k} items: ${t}, expected ${wantT[k]}`); });
  /* a facet, and an invalid facet value ignored */
  const mF = M({ f: 'b' }), wantF = byv(items.filter(x => x.f === 'b'));
  if (!eq(mF.rows, ids(wantF)) || mF.n !== wantF.length) fails.push(`A facet f=b: ${mF.n} rows, expected ${wantF.length}`);
  const mI = M({ f: 'zzz' }); if (mI.n !== 25) fails.push(`A invalid facet value f=zzz: ${mI.n} rows, expected 25 (ignored)`);
  /* search: words ANDed, case and tags ignored */
  const mQ = M({ q: 'ALPHA  beta' }), wantQ = byv(items.filter(x => /alpha/.test(x.t.replace(/<[^>]+>/g, '')) && /beta/.test(x.t.replace(/<[^>]+>/g, ''))));
  if (!eq(mQ.rows, ids(wantQ))) fails.push(`A search "ALPHA  beta": rows ${mQ.rows.join(',')}, expected ${ids(wantQ).join(',')}`);
  /* sort: stable, ties in store order; a named sort; an unknown sort is the first */
  if (!eq(mAll.rows, ids(byv(items)))) fails.push(`A sort v: ${mAll.rows.slice(0, 8).join(',')}…, expected ${ids(byv(items)).slice(0, 8).join(',')}… (stable, ties in store order)`);
  const mD = M({ sort: 'idd' }); if (!eq(mD.rows, ids(items).slice().sort().reverse())) fails.push('A sort idd: not by id descending');
  if (!eq(M({ sort: 'nope' }).rows, mAll.rows)) fails.push('A sort nope: not the first sort');
  /* cap 10 with keep-first, displayed in sort order; show=all uncapped */
  const sorted = byv(items), rank = [...sorted.filter(x => x.keep), ...sorted.filter(x => !x.keep)], top = new Set(ids(rank.slice(0, 10)));
  const wantShown = ids(sorted.filter(x => top.has(x.id))), wantHidden = ids(sorted.filter(x => !top.has(x.id)));
  const mNG = w.eval(`(() => { const d = { ...IA_LIST_DEFS.__a }; delete d.group; const m = iaListModel(d, ${JSON.stringify(items)}, {}, { kind: 'all' }); return { shown: m.shown.map(x => x.id), hidden: m.hidden.map(x => x.id), n: m.n, groups: m.groups }; })()`);
  if (mNG.shown.length !== 10 || mNG.hidden.length !== 15 || mNG.n !== 25) fails.push(`A cap: ${mNG.shown.length} shown, ${mNG.hidden.length} hidden, n ${mNG.n}; expected 10, 15, 25`);
  if (!eq(mNG.shown, wantShown)) fails.push(`A keep-first: shown ${mNG.shown.join(',')}, expected ${wantShown.join(',')} (the keep items ranked first, displayed in sort order)`);
  if (!eq(mNG.hidden, wantHidden)) fails.push(`A cap: hidden ${mNG.hidden.join(',')}, expected ${wantHidden.join(',')}`);
  const mAllShow = M({ show: 'all' }); if (mAllShow.shown.length !== 25 || mAllShow.hidden.length) fails.push(`A show=all: ${mAllShow.shown.length} shown, ${mAllShow.hidden.length} hidden; expected 25, 0`);
  if (mNG.groups) fails.push('A groups without def.group');
  /* groups: only above 10 rows in more than one group; one cap; n_g sums to n; shown drawn in group blocks */
  const gs = mAll.groups || [], order = [...new Set(sorted.map(x => x.g))], wantNg = order.map(g => ({ g, n_g: items.filter(x => x.g === g).length }));
  if (!eq(gs, wantNg)) fails.push(`A groups: ${JSON.stringify(gs)}, expected ${JSON.stringify(wantNg)}`);
  if (gs.reduce((a, x) => a + x.n_g, 0) !== mAll.n) fails.push('A groups: n_g does not sum to n');
  const blocks = order.flatMap(g => wantShown.filter(id => items.find(x => x.id === id).g === g));
  if (!eq(mAll.shown, blocks)) fails.push(`A groups: shown ${mAll.shown.join(',')}, expected group blocks ${blocks.join(',')}`);
  if (mAll.shown.length !== 10) fails.push(`A groups: ${mAll.shown.length} shown, expected one cap of 10`);
  if (M({}, null, items.slice(0, 10)).groups) fails.push('A groups at 10 rows (expected none)');
  if (M({}, null, items.filter(x => x.g === 'mini').concat(items.filter(x => x.g === 'mini'))).groups) fails.push('A groups with one group (expected none)');
  /* iaListHref: fixed order (scope, facets, sort, q, show), defaults omitted, a facet change or a search drops show */
  const H = (query, scope, change) => w.eval(`iaListHref('__a', { op: LS.op, scope: ${JSON.stringify(scope || { kind: 'all', id: null })}, query: ${JSON.stringify(query)} }, ${JSON.stringify(change || {})})`);
  const cases = [
    [{}, null, {}, '__a'], [{ sort: 'v' }, null, {}, '__a'], [{ show: 'all', q: 'x y', sort: 'idd', f: 'b' }, { kind: 'group', id: 'cold' }, {}, '__a?scope=group%3Acold&f=b&sort=idd&q=x%20y&show=all'],
    [{ show: 'all' }, null, { f: 'a' }, '__a?f=a'], [{ show: 'all' }, null, { q: 'z' }, '__a?q=z'], [{ show: 'all' }, null, { sort: 'idd' }, '__a?sort=idd&show=all'],
    [{ f: 'zzz' }, null, {}, '__a'], [{ f: 'a', q: 'k' }, null, { f: '' }, '__a?q=k']];
  for (const [q, s, c, want] of cases) { const got = H(q, s, c); if (decodeURIComponent(got) !== decodeURIComponent(want)) fails.push(`A canon ${JSON.stringify(q)} ${JSON.stringify(c)}: ${got}, expected ${want}`); }
  log.push(`A · ns ${mAll.ns}/${mG.ns}/${mS.ns} (all, group, Site) · tiers ${tiers.map(([k, t]) => `${k}:${t}`).join(' ')} · facet ${mF.n} · search ${mQ.n} · cap ${mNG.shown.length}+${mNG.hidden.length} · groups ${gs.map(x => x.n_g).join('+')} · canon ${cases.length}`);
  if (B.errors.length) fails.push(`A: script error ${B.errors[0]}`);
  B.dom.window.close();
}
/* ---- Block C: the scope menu on a list (spec §3.3): entries keep the facets, sort and q and drop show; a Site entry scopes the list ---- */
async function blockC(fails, log) {
  let n = 0;
  for (const op of OPS) {
    const B = await boot(op, 'decisions?state=waiting&sort=due&q=the&show=all'), { w, doc } = B; plantSource(w, 'C');
    const sites = w.eval(`OPS[${JSON.stringify(op)}].sites`), rest = 'state=waiting&sort=due&q=the';
    const got = [...doc.querySelectorAll('.ux-scope-sw .ux-pop-menu a[href]')].map(a => [a.textContent.trim(), a.getAttribute('href')]);
    const want = [['All sites', `#/decisions?${rest}`], ...sites.map(k => [w.eval(`SK[${JSON.stringify(k)}].name`), `#/decisions?scope=site:${k}&${rest}`])];
    for (const [name, href] of want) { n++; const g = got.find(([t]) => t === name); if (!g) { fails.push(`C ${B.opName}: no scope entry "${name}"`); continue; }
      if (decodeURIComponent(g[1]) !== href) fails.push(`C ${B.opName}: the scope entry "${name}" is ${g[1]}, expected ${href}`); }
    const grp = got.filter(([t]) => !want.some(([x]) => x === t));
    for (const [t, h] of grp) { n++; if (!/^#\/decisions\?scope=group:[a-z]+&state=waiting&sort=due&q=the$/.test(decodeURIComponent(h))) fails.push(`C ${B.opName}: the group entry "${t}" is ${h}, expected the list scoped to its group with the view kept`); }
    if (B.errors.length) fails.push(`C ${B.opName}: script error ${B.errors[0]}`);
    B.dom.window.close();
  }
  /* IA-2b1 review L2: the Outcomes fold's list is built from the scope alone; a typed ?sort= or ?target= changes neither its rows nor their order */
  /* IA-2b1 review L1: the command palette names each place once; a list alias (Act first, the old Findings pages) adds no second entry */
  let pn = 0;
  for (const op of OPS) { const B = await boot(op, 'portfolio'), { w } = B; plantSource(w, 'C');
    const cmds = w.eval('uxCommands()').map(([l, k, id]) => [l, k, id]), seen = {};
    for (const [l, k, id] of cmds) { pn++; if (k === 'Portfolio' || k === 'Go to') (seen[id] = seen[id] || []).push(`${l} (${k})`); }
    for (const [id, names] of Object.entries(seen)) if (names.length > 1) fails.push(`C ${op}: the palette has ${names.length} entries for #/${id}: ${names.join(' · ')}`);
    B.dom.window.close(); }
  log.push(`C · ${pn} palette entries over 3 operators, each place named by one Portfolio or Go to entry`);
  let fq = 0;
  for (const op of OPS) {
    const keys = async q => { const B = await boot(op, 'portfolio/outcomes' + q), { w, doc } = B; plantSource(w, 'C'); const r = [...doc.querySelectorAll('tr[data-row]')].map(x => x.getAttribute('data-row')); B.dom.window.close(); return r; };
    const base = await keys(''); if (base.length < 2) fails.push(`C ${op}: the Outcomes fold has ${base.length} rows, too few to prove the order`);
    for (const q of ['?sort=name', '?sort=gap', '?target=on', '?target=below', '?q=zzqx']) { fq++; const got = await keys(q); if (got.join() !== base.join()) fails.push(`C ${op}: #/portfolio/outcomes${q} changes the fold's rows (${got.join(' ') || 'none'}; without it ${base.join(' ')})`); }
  }
  log.push(`C · ${fq} typed queries on the Outcomes fold over 3 operators leave its rows and order as they are`);
  log.push(`C · ${n} scope entries on Decisions?state=waiting&sort=due&q=the&show=all over 3 operators`);
}
/* ---- Block D: the scale case on the fixture (tools/list_fixture.cjs), injected through items(op) and rendered by the real route ---- */
async function blockD(fails, log) {
  const at = async (B, hash, name, k) => { F.install(B.w, name, k); B.w.location.hash = '#/' + hash; await sleep(30); B.w.eval('render()'); await sleep(20); return B.doc.querySelector('section[data-shape="list"]'); };
  const B = await boot('lakeside', 'portfolio'), { w, doc } = B; plantSource(w, 'D');
  const tools = s => { const f = s && s.querySelector('[data-ia-list-tools]'); return f ? [...f.querySelectorAll('select[name], input[name]')].map(e => e.name).join(',') + (f.querySelector('button[type="submit"]') ? ',submit' : '') : ''; };
  /* the tier at 2, 3, 10, 11 and 30 items */
  const T = [];
  for (const k of [2, 3, 10, 11, 30]) { const s = await at(B, 'sites', 'sites30', k), got = tools(s), want = k < 3 ? '' : k <= 10 ? 'sort' : 'target,sort,q,submit';
    T.push(`${k}:${got || 'none'}`); if (got !== want) fails.push(`D tier at ${k} Sites: controls "${got}", expected "${want}"`); }
  /* sites30 default: group heads, one Show all 30, remainder + shown = tile, cents on every figure of the key */
  const s = await at(B, 'sites', 'sites30');
  const heads = [...s.querySelectorAll('tr.ia-list-group th')].map(t => t.textContent.replace(/\s+/g, ' ').trim()), hn = heads.map(h => +(h.match(/(\d+)$/) || [])[1]);
  const tileV = k => { const t = [...s.querySelectorAll('[data-level="L1"] .ux-kpi')].find(e => e.querySelector('.ux-kpi-l')?.textContent.trim() === k); return t ? t.querySelector('.ux-kpi-v').textContent.trim() : null; };
  /* groups in order of first appearance in the sort (spec §3.1 step 7), computed here from the fixture's own gaps (has a target first, gap ascending) */
  const fx = B.w.__iaFixture.map((x, i) => [x, i]).sort(([a, i], [b, j]) => (a.hasTarget !== b.hasTarget ? (a.hasTarget ? -1 : 1) : a.hasTarget ? a.gap - b.gap : 0) || i - j).map(([x]) => x);
  const N = { mini: 18, cold: 7, ev: 5 }, wantHeads = [...new Set(fx.map(x => x.group))].map(g => `${GROUPW[g]} ${N[g]}`).join(' | ');
  if (heads.join(' | ') !== wantHeads) fails.push(`D sites30: group heads "${heads.join(' | ')}", expected "${wantHeads}" (first appearance in the gap sort)`);
  if (hn.reduce((a, b) => a + b, 0) !== +tileV('Sites')) fails.push(`D sites30: the group heads sum to ${hn.reduce((a, b) => a + b, 0)}, tile 1 is ${tileV('Sites')}`);
  const more = [...s.querySelectorAll('a')].filter(a => /^Show all \d+$/.test(a.textContent.trim()));
  if (more.length !== 1 || more[0].textContent.trim() !== 'Show all 30') fails.push(`D sites30: ${more.length} "Show all" link(s) (${more.map(a => a.textContent.trim()).join(', ')}), expected one "Show all 30"`);
  const rowsN = s.querySelectorAll('tbody tr[data-row]').length; if (rowsN !== 10) fails.push(`D sites30: ${rowsN} rows shown, expected 10`);
  const gapEls = [...s.querySelectorAll('[data-qty^="sites:gap:"]')], tot = gapEls.filter(e => e.dataset.qtyRole === 'total'), parts = gapEls.filter(e => e.dataset.qtyRole === 'part');
  const rem = [...s.querySelectorAll('p.ux-more')].find(p => /^Not shown: \d+ Sites, gap to target /.test(p.textContent.trim()));
  if (!rem) fails.push('D sites30: no "Not shown: {h} Sites, gap to target {gap}." line beside "Show all 30"');
  else { const h = +rem.textContent.match(/Not shown: (\d+) Sites/)[1]; if (h !== 20) fails.push(`D sites30: the remainder line counts ${h} Sites, expected 20`); }
  const cents = e => /\.\d\d(?!\d)/.test(e.textContent);
  if (tot.length !== 1) fails.push(`D sites30: ${tot.length} gap totals, expected the one tile`);
  else { const sum = Math.round(parts.reduce((a, e) => a + money(e.textContent), 0) * 100) / 100, T0 = money(tot[0].textContent);
    if (sum !== T0) fails.push(`D sites30: the shown gaps and the remainder sum to ${sum}, the tile is ${T0}`);
    if (parts.length !== 10 + (rem ? 1 : 0)) fails.push(`D sites30: ${parts.length} gap parts, expected the 10 rows${rem ? ' and the remainder' : ''}`); }
  const whole = gapEls.filter(e => !cents(e)); if (whole.length) fails.push(`D sites30: ${whole.length} figure(s) of sites:gap: without cents (the cents fallback is per key on the screen), e.g. "${whole[0].textContent.trim()}"`);
  /* show=all: 30 rows, the Site without a target last, the tile's line */
  const sa = await at(B, 'sites?show=all', 'sites30'), all = [...sa.querySelectorAll('tbody tr[data-row]')].map(r => r.dataset.row);
  if (all.length !== 30) fails.push(`D sites30 show=all: ${all.length} rows, expected 30`);
  const evRows = [...sa.querySelectorAll('tbody[data-group="ev"] tr[data-row]')].map(r => r.dataset.row);
  if (evRows[evRows.length - 1] !== 'fx30') fails.push(`D sites30 show=all: the Site without a target (fx30) is not last in its group (${evRows.join(',')})`);
  if (!/1 Sites without a target are not in this figure/.test(sa.querySelector('[data-level="L1"]')?.textContent || '')) fails.push('D sites30: the gap tile lacks "1 Sites without a target are not in this figure"');
  if ([...sa.querySelectorAll('a')].some(a => /^Show all/.test(a.textContent.trim()))) fails.push('D sites30 show=all: a "Show all" link is still drawn');
  /* two set filters at tier 2: no chip for a drawn control, "Clear filters" to the scope-only address */
  const s2 = await at(B, 'sites?target=below&q=fixture', 'sites30'), cl = [...s2.querySelectorAll('.ia-list-chips a')].find(a => a.textContent.trim() === 'Clear filters');
  if (!cl || cl.getAttribute('href') !== '#/sites') fails.push(`D sites30 target=below&q=fixture: "Clear filters" ${cl ? `is ${cl.getAttribute('href')}` : 'is missing'}, expected #/sites`);
  if (s2.querySelectorAll('.ia-list-chips .ia-chip').length) fails.push('D sites30 at tier 2: a chip names a state its control already shows');
  if (s2.querySelector('[data-ia-list-tools] select[name="target"]')?.value !== 'below' || s2.querySelector('[data-ia-list-tools] input[name="q"]')?.value !== 'fixture') fails.push('D sites30: the controls do not show the address');
  /* tier 1 (10 decisions) with two facets set: a chip each, then "Clear filters" */
  const s3 = await at(B, 'decisions?state=waiting&due=none', 'decisions25', 10), chips = [...s3.querySelectorAll('.ia-list-chips .ia-chip')].map(c => c.textContent.replace(/\s+/g, ' ').trim());
  if (chips.join(' | ') !== 'Waiting for a choice · All states | No deadline · Any due date' && chips.join(' | ') !== 'Waiting for a choice · All states | No deadline · Any due date'.replace('No deadline', w.eval('UX_URG.none') || 'No deadline')) fails.push(`D decisions25 (10) state=waiting&due=none: chips "${chips.join(' | ')}", expected "Waiting for a choice · All states | {due none word} · Any due date"`);
  if (![...s3.querySelectorAll('.ia-list-chips a')].some(a => a.textContent.trim() === 'Clear filters' && a.getAttribute('href') === '#/decisions')) fails.push('D decisions25: no "Clear filters" to #/decisions at 2 set filters');
  /* decisions25: the 6 waiting are never hidden by the cap */
  const s4 = await at(B, 'decisions', 'decisions25'), wait = F.WAIT_AT.map(i => B.w.__iaFixture[i]), shownD = [...s4.querySelectorAll('tbody tr[data-row]')].map(r => r.dataset.row);
  const lost = wait.filter(id => !shownD.includes(id)); if (lost.length) fails.push(`D decisions25: waiting decision(s) hidden by the cap: ${lost.join(', ')}`);
  /* the empty state keeps its tools */
  const s5 = await at(B, 'sites?q=zzqx', 'sites30'), em = s5.querySelector('.ux-empty[role="status"]');
  if (!em || !/^Nothing matches these filters\./.test(em.textContent.trim()) || !em.querySelector('a[href="#/sites"]')) fails.push('D sites30 q=zzqx: no "Nothing matches these filters. Clear filters" empty state');
  if (tools(s5) !== 'target,sort,q,submit') fails.push(`D sites30 q=zzqx: the empty state's controls are "${tools(s5)}", expected the tier's`);
  log.push(`D · tiers ${T.join(' ')} · heads ${heads.join(' | ')} · ${rowsN} shown · remainder ${rem ? 'drawn' : 'missing'} · ${gapEls.length} gap figures with cents ${gapEls.length - whole.length} · show=all ${all.length} · waiting kept ${wait.length - lost.length}/${wait.length}`);
  if (B.errors.length) fails.push(`D: script error ${B.errors[0]}`);
  B.dom.window.close();
}
/* ---- Block B: live (spec §8 row 2, D-IA.69, D-IA.70, D-IA.73). Every operator x the four lists x the default view, each facet value (by
   address), each sort, q = the first row's first word, each scope entry and show=all; Actions also after Approve, after Send back and in
   Lakeside 6500/No. B's rows come from the stores (ATTN, DEC, HC.findings, WF(op).actions, OPS[op].sites) and reviewed one-source
   classifiers (uxDecState, uxDueIso, uxUrgency, releaseShown, planCaseIds, planApprovedIds, planItemsV1, uxPlanState, tree, siteM) with
   its own code; it never calls the list's code. Its word tables are literals, asserted against the product's first (D-IA.73 c). ---- */
const LENSW = { grow: 'Grow revenue', optimize: 'Optimize cost and efficiency', protect: 'Protect asset and capital', assure: 'Assure performance and returns' };
const URGW = { week: 'Due this week', month: 'Due this month', later: 'Due later', none: 'No deadline' };
const RELW = { WAITING: 'Waiting', RELEASED: 'Released', RETURNED: 'Returned', WITHDRAWN: 'Withdrawn' };
const DECW = { waiting: 'Waiting for a choice', approval: 'Awaiting approval', draft: 'With the plan sent back to draft', underway: 'Under way' };
const GROUPW = { mini: 'Mini-grids', cold: 'Cold rooms', ev: 'EV depots' };
/* per list: the title (tile 1's label and the route's H1), the sort literals (D-IA.69), the facets [key, words, way out], def.none */
const LIT = cost => ({
  decisions: { title: 'Decisions', sorts: [['priority', 'Priority'], ['due', 'Due date']], facets: [['state', DECW, 'All states'], ['due', URGW, 'Any due date']], none: 'No decisions in this scope.' },
  findings: { title: 'Findings', sorts: [['priority', 'Priority'], ['site', 'Site']], facets: [['heading', LENSW, 'All headings']], none: 'No Findings in this scope.' },
  actions: { title: 'Actions', sorts: [['due', 'Due date'], ['item', 'Plan item']], facets: [['state', { released: RELW.RELEASED, waiting: RELW.WAITING, returned: RELW.RETURNED }, 'All states'], ['version', null, 'All versions']], none: 'No Actions in this scope.' },
  sites: { title: 'Sites', sorts: [['gap', 'Gap to target'], ['name', 'Name']], facets: [['target', cost ? { below: 'Over target', on: 'On or under target' } : { below: 'Below target', on: 'On or above target' }, cost ? 'Over and under target' : 'Above and below target']], none: 'No Sites in this scope.' } });
const LISTS = ['decisions', 'findings', 'actions', 'sites'];
const INTERACTIVE = 'a[href], button, input, select, textarea, summary, [tabindex]:not([tabindex="-1"]), [contenteditable="true"]';
const norm = s => String(s || '').replace(/\s+/g, ' ').trim();
/* B's own store reads: one JSON per list, from the stores and the reviewed classifiers only */
function ownStore(w, op, key) {
  const o = JSON.stringify(op);
  if (key === 'decisions') return w.eval(`(() => { const op = ${o}; return [...new Set(ATTN[op].map(r => r[4]))].map(id => { const d = decById(id), s = uxDecState(id), due = ATTN[op].filter(r => r[4] === id).map(r => uxDueIso(id, r[3])).filter(Boolean).sort()[0] || '';
    return { key: id, site: d ? d.site : null, target: d ? 'decision/' + id : null, sk: s.key, draft: !!s.draft, due, urg: uxUrgency(due) }; }); })()`)
    .map(x => ({ ...x, f: { state: ['choose', 'none'].includes(x.sk) ? 'waiting' : x.sk === 'approval' ? (x.draft ? 'draft' : 'approval') : x.sk === 'released' ? 'underway' : `unknown ${x.sk}`, due: x.urg }, keep: ['choose', 'none'].includes(x.sk) }));
  if (key === 'findings') return w.eval(`(() => { const op = ${o}, names = OPS[op].sites.map(k => [SK[k].name, k]), nm = f => String(f.site).replace(/^Room [A-C] · /, '');
    return (HC.findings || []).map(f => ({ key: f.id, sname: nm(f), site: (names.find(([n]) => n === nm(f)) || [])[1] || null, target: f.decision && decById(f.decision) ? 'decision/' + f.decision : null, heading: f.heading })).filter(x => x.site); })()`)
    .map(x => ({ ...x, f: { heading: x.heading } }));
  if (key === 'actions') return w.eval(`(() => { const op = ${o}, A = WF(op).actions || [], inCase = new Set(planCaseIds(op)), S = uxPlanState(op), ver = S.state === 'APPROVED' ? planApprovedIds(op) : planItemsV1(op), v1 = planItemsV1(op),
    decs = DEC.filter(d => OPS[op].sites.includes(d.site)), cnt = {};
    return { version: String(S.version), rows: A.map(a => { cnt[a.item] = (cnt[a.item] || 0) + 1; const d = decs.find(d => (d.opts || []).includes(a.item));
      return { key: a.item + '-' + cnt[a.item], item: a.item, site: OPT[a.item]?._site || (itemOf(op, a.item)?.site || '').split(' · ').pop().toLowerCase(), target: d ? 'decision/' + d.id : 'plan',
        state: !inCase.has(a.item) ? 'returned' : releaseShown(op, a.item).at ? 'released' : 'waiting', inVer: ver.includes(a.item), due: a.due || '', ix: v1.indexOf(a.item) }; }) }; })()`);
  return w.eval(`(() => { const op = ${o}; return OPS[op].sites.map(sk => { const t = tree(sk), s = siteM(sk); return { key: sk, site: sk, name: SK[sk].name, target: 'site/' + sk, has: t.plan != null, gap: s.period.variance }; }); })()`)
    .map(x => ({ ...x, f: { target: x.has ? (x.gap < 0 ? 'below' : 'on') : null } }));
}
/* B's own model of a view (spec §3.1 read independently): scope, tier, facets, search, sort, cap with keep-first, group blocks */
function ownView(key, L, items, q, scope, texts, vert) {
  const inS = items.filter(it => scope.kind === 'site' ? it.site === scope.id : scope.kind === 'group' ? vert(it.site) === scope.id : true), ns = inS.length;
  const tier = ns < 3 ? 0 : ns <= 10 ? 1 : 2, opts = facetOpts(L, items);
  let rows = inS.filter(it => L.facets.every(([f]) => !q[f] || !(q[f] in opts[f]) || it.f[f] === q[f]));
  const words = String(q.q || '').toLowerCase().split(/\s+/).filter(Boolean);
  rows = rows.filter(it => words.every(x => (texts[it.key] || '').includes(x)));
  const sk = L.sorts.some(([k]) => k === q.sort) ? q.sort : L.sorts[0][0], cmp = CMP[key][sk], st = rows.map((x, i) => [x, i]).sort(([a, i], [b, j]) => cmp(a, b) || i - j).map(([x]) => x);
  const n = st.length, all = q.show === 'all', rank = key === 'decisions' ? [...st.filter(x => x.keep), ...st.filter(x => !x.keep)] : st, top = new Set((all ? rank : rank.slice(0, 10)).map(x => x.key));
  let shown = st.filter(x => top.has(x.key));
  const gs = key === 'sites' ? [...new Set(st.map(x => vert(x.site)))] : [];
  if (gs.length > 1 && n > 10) shown = gs.flatMap(g => shown.filter(x => vert(x.site) === g));
  const present = f => new Set(inS.map(it => it.f[f]).filter(v => v != null && v in opts[f])).size;
  const drawn = tier === 2 ? L.facets.map(([f]) => f).filter(f => present(f) >= 2) : [];
  return { ns, n, tier, shown: shown.map(x => x.key), hidden: n - shown.length, drawn, sort: sk, opts };
}
const facetOpts = (L, items) => Object.fromEntries(L.facets.map(([f, words]) => [f, f === 'version' ? { [items.version]: `Version ${items.version}` } : f === 'heading' ? Object.fromEntries(Object.entries(words).filter(([k]) => items.some(it => it.f.heading === k))) : words]));
const byDue = (a, b) => (!a.due) - (!b.due) || (a.due < b.due ? -1 : a.due > b.due ? 1 : 0);
const CMP = { decisions: { priority: () => 0, due: byDue }, findings: { priority: () => 0, site: (a, b) => a.sname.localeCompare(b.sname) },
  actions: { due: byDue, item: (a, b) => (a.ix < 0) - (b.ix < 0) || a.ix - b.ix }, sites: { gap: (a, b) => (a.has !== b.has ? (a.has ? -1 : 1) : a.has ? a.gap - b.gap : 0), name: (a, b) => a.name.localeCompare(b.name) } };
/* the address of a view, written with B's own code in the canonical order (scope, facets, sort, q, show) */
function addr(key, L, q, scopeParam) {
  const p = [];
  if (scopeParam) p.push(`scope=${scopeParam}`);
  L.facets.forEach(([f]) => { if (q[f]) p.push(`${f}=${encodeURIComponent(q[f])}`); });
  if (q.sort && q.sort !== L.sorts[0][0]) p.push(`sort=${q.sort}`);
  if (q.q) p.push(`q=${encodeURIComponent(q.q)}`);
  if (q.show) p.push('show=all');
  return key + (p.length ? '?' + p.join('&') : '');
}
const ctlNames = s => { const f = s && s.querySelector('[data-ia-list-tools]'); return f ? [...f.querySelectorAll('select[name], input[name]')].map(e => e.name).join(',') + (f.querySelector('button[type="submit"]') ? ',submit' : '') : ''; };
const l2Of = doc => { const s = doc.querySelector('section[data-shape="list"]'), l = s && s.querySelector('[data-level="L2"]'); return l ? l.innerHTML : null; };
/* one view: every assertion of spec §8 row 2 that reads the screen */
function checkView(ctx, key, q, scope, scopeParam, tag) {
  const { B, op, L, items, texts, vert, fails, cls, stat } = ctx, doc = B.doc, at = `B ${B.opName} · ${tag} · #/${addr(key, L, q, scopeParam)}`;
  const secs = doc.querySelectorAll('[data-shape="list"]'); stat.views++;
  if (secs.length !== 1) { fails.push(`${at}: ${secs.length} [data-shape="list"], expected one`); return; }
  const s = secs[0], V = ownView(key, L, items, q, scope, texts, vert);
  /* tile 1 = the shown rows + the hidden rows = the "Show all" n = B's own count */
  const tile = [...s.querySelectorAll('[data-level="L1"] .ux-kpi')].find(e => norm(e.querySelector('.ux-kpi-l')?.textContent) === L.title), tv = tile ? +norm(tile.querySelector('.ux-kpi-v')?.textContent).replace(/,/g, '') : NaN;
  const rows = [...s.querySelectorAll('tbody tr[data-row]')], keys = rows.map(r => r.dataset.row), more = [...s.querySelectorAll('a')].filter(a => /^Show all [\d,]+$/.test(norm(a.textContent)));
  const moreN = more.length ? +norm(more[0].textContent).replace(/\D/g, '') : null, hidden = moreN == null ? 0 : moreN - rows.length;
  if (tv !== rows.length + hidden || tv !== V.n || (moreN != null && moreN !== tv)) fails.push(`${at}: tile 1 "${L.title}" is ${tile ? tv : 'missing'}; ${rows.length} rows shown + ${hidden} hidden${moreN != null ? ` ("Show all ${moreN}")` : ''}; B counts ${V.n}`);
  if (more.length > 1 || (V.hidden > 0) !== (more.length === 1)) fails.push(`${at}: ${more.length} "Show all" link(s), B hides ${V.hidden} row(s)`);
  /* the row set and order equal B's own computation */
  if (keys.join(',') !== V.shown.join(',')) fails.push(`${at}: rows ${keys.join(',') || 'none'}, B computes ${V.shown.join(',') || 'none'}`);
  /* the tier's controls and no others (D-IA.67); each control's value equals the address */
  const want = V.tier === 0 ? '' : V.tier === 1 ? 'sort' : [...V.drawn, 'sort', 'q', 'submit'].join(','), got = ctlNames(s);
  if (got !== want) fails.push(`${at}: controls "${got}", expected "${want}" (tier ${V.tier}, ${V.ns} in scope)`);
  const form = s.querySelector('[data-ia-list-tools]');
  if (form) { const sel = form.querySelector('select[name="sort"]');
    if (sel) { const ov = [...sel.options].map(o => o.value).join(','), lv = L.sorts.map(([k]) => k).join(','), ow = [...sel.options].map(o => norm(o.textContent)).join(','), lw = L.sorts.map(([, x]) => x).join(',');
      if (ov !== lv || ow !== lw) fails.push(`${at}: the sort list is "${ov}" ("${ow}"), expected the literal "${lv}" ("${lw}") (D-IA.69)`);
      if (sel.value !== V.sort) fails.push(`${at}: Sort shows "${sel.value}", the address's sort is "${V.sort}"`); }
    for (const f of V.drawn) { const e = form.querySelector(`select[name="${f}"]`), wv = q[f] && q[f] in V.opts[f] ? q[f] : '';
      if (e && e.value !== wv) fails.push(`${at}: ${f} shows "${e.value}", the address has "${wv}"`);
      if (e) [...e.options].filter(o => o.value).forEach(o => { if (V.opts[f][o.value] !== norm(o.textContent)) fails.push(`${at}: ${f} option ${o.value} reads "${norm(o.textContent)}", B's table "${V.opts[f][o.value]}"`); }); }
    const qi = form.querySelector('input[name="q"]'); if (qi && qi.value !== (q.q || '')) fails.push(`${at}: Search shows "${qi.value}", the address has "${q.q || ''}"`); }
  /* a chip for each set state that no control shows (D-IA.70), in the order scope, facets, q; Clear filters at 2 or more */
  const chips = [...s.querySelectorAll('.ia-list-chips .ia-chip')].map(c => norm(c.textContent)), wc = [];
  if (scope.kind !== 'all') wc.push(`${scope.kind === 'group' ? GROUPW[scope.id] : ctx.siteName[scope.id]} · All sites`);
  const set = L.facets.filter(([f]) => q[f] && q[f] in V.opts[f]);
  set.forEach(([f, , out]) => { if (!V.drawn.includes(f)) wc.push(`${V.opts[f][q[f]]} · ${out}`); });
  if (q.q && V.tier < 2) wc.push(`Matching “${q.q}” · Clear search`);
  if (chips.join(' | ') !== wc.join(' | ')) fails.push(`${at}: chips "${chips.join(' | ')}", expected "${wc.join(' | ')}"`);
  const clear = [...s.querySelectorAll('.ia-list-chips a')].some(a => norm(a.textContent) === 'Clear filters');
  if (clear !== (set.length + (q.q ? 1 : 0) >= 2)) fails.push(`${at}: "Clear filters" ${clear ? 'drawn' : 'missing'} at ${set.length + (q.q ? 1 : 0)} set filter(s)`);
  /* every row has exactly one interactive element, and it is a live link (D-IA.9, D-IA.70 b, D-IA.76) */
  rows.forEach(r => { const ia = [...r.querySelectorAll(INTERACTIVE)], it = items.rows ? items.rows.find(x => x.key === r.dataset.row) : items.find(x => x.key === r.dataset.row);
    if (ia.length !== 1 || !ia[0].matches('a.ia-row-go[href]')) { fails.push(`${at}: row ${r.dataset.row} has ${ia.length} interactive element(s) (${ia.map(e => e.tagName.toLowerCase()).join(', ')}), expected one a.ia-row-go`); return; }
    const h = ia[0].getAttribute('href'), c = cls(h); if (c !== 'good') fails.push(`${at}: row ${r.dataset.row} opens ${h} (${c})`);
    if (it && it.target && h !== '#/' + it.target) fails.push(`${at}: row ${r.dataset.row} opens ${h}, B's target is #/${it.target}`); });
  /* the empty states */
  const em = s.querySelector('.ux-empty[role="status"]');
  if (V.ns === 0 && norm(em?.textContent) !== L.none) fails.push(`${at}: the empty state is "${norm(em?.textContent)}", expected "${L.none}"`);
  if (V.ns > 0 && V.n === 0 && !/^Nothing matches these filters\. Clear filters$/.test(norm(em?.textContent))) fails.push(`${at}: no "Nothing matches these filters." state`);
  /* the live cents fallback (spec §3.4): counted, expected 0 */
  if (key === 'sites' && [...s.querySelectorAll('[data-qty^="sites:gap:"]')].some(e => /\.\d\d(?!\d)/.test(e.textContent))) stat.cents++;
}
async function blockB(fails, log) {
  const stat = { views: 0, cents: 0, restore: 0, scen: 0 }, counts = [];
  /* the product's word tables equal B's literals (D-IA.73 c) */
  {
    const B = await boot('lakeside', 'portfolio'), { w } = B; plantSource(w, 'B');
    const T = w.eval(`({ lens: Object.fromEntries(Object.entries(LENS).map(([k, v]) => [k, v[0]])), urg: UX_URG, rel: RELEASE_WORD, dec: typeof IA_DEC_STATE_WORD === 'object' ? IA_DEC_STATE_WORD : null, grp: IA_GROUP_WORD })`);
    for (const [n, a, b] of [['LENS headings', T.lens, LENSW], ['UX_URG', T.urg, URGW], ['RELEASE_WORD', T.rel, RELW], ['IA_DEC_STATE_WORD', T.dec, DECW], ['IA_GROUP_WORD', T.grp, GROUPW]])
      if (JSON.stringify(a) !== JSON.stringify(b)) fails.push(`B word table ${n}: the product has ${JSON.stringify(a)}, B's literal ${JSON.stringify(b)} (re-rule on purpose)`);
    B.dom.window.close();
  }
  for (const op of OPS) {
    const scen = [['default', null]].concat([['approved', 'approve'], ['sent back', 'sendback']], op === 'lakeside' ? [['6500/No', 'nd']] : []);
    for (const [sn, how] of scen) {
      const B = await boot(op, how ? 'plan' : 'portfolio'), { w, doc } = B; plantSource(w, 'B'); stat.scen++;
      if (how && !(await scenario(B, op, how, fails))) { B.dom.window.close(); continue; }
      if (w.eval(`OPS[${JSON.stringify(op)}].sites.some(k => !SK[k])`)) fails.push(`B ${B.opName}: a Site key without SK`);
      const SKT = w.eval('Object.fromEntries(Object.entries(SK).map(([k, v]) => [k, v.type]))'), vert = k => SKT[k] === 'Mini-grid' ? 'mini' : /^Cold room/.test(SKT[k]) ? 'cold' : 'ev';
      const ctx = { B, op, fails, stat, vert, cls: classifier(w, op), siteName: w.eval(`Object.fromEntries(OPS[${JSON.stringify(op)}].sites.map(k => [k, SK[k].name]))`) };
      /* the decision state words appear in the reviewed uxStateCount (D-IA.73 c) */
      { const sc = w.eval(`uxStateCount([...new Set(ATTN[${JSON.stringify(op)}].map(r => r[4]))])`).toLowerCase(), present = new Set(ownStore(w, op, 'decisions').map(x => x.f.state)); /* uxStateCount names the states present */
        [...present].forEach(k => { if (!DECW[k] || !sc.includes(DECW[k].toLowerCase())) fails.push(`B ${B.opName} · ${sn}: the state word "${DECW[k] || k}" is not in uxStateCount's output "${sc}"`); }); }
      for (const key of how ? ['actions'] : LISTS) {
        const L = LIT(w.eval(`OPS[${JSON.stringify(op)}].kind`) === 'cost')[key], raw = ownStore(w, op, key), items = key === 'actions' ? Object.assign(raw.rows.map(x => ({ ...x, f: { state: x.state, version: x.inVer ? raw.version : null } })), { version: raw.version }) : raw;
        /* every store item has a live target (D-IA.70 b) */
        items.forEach(it => { if (!it.target) fails.push(`B ${B.opName} · ${sn}: ${key} item ${it.key} has no target`); else if (ctx.cls('#/' + it.target) !== 'good') fails.push(`B ${B.opName} · ${sn}: ${key} item ${it.key}'s target #/${it.target} is ${ctx.cls('#/' + it.target)}`); });
        /* the rendered text of each row, read at show=all (def.text is the row's rendered text) */
        await B.go(`${key}?show=all`); const texts = Object.fromEntries([...doc.querySelectorAll('section[data-shape="list"] tbody tr[data-row]')].map(r => [r.dataset.row, [...r.children].map(c => c.textContent).join(' ').replace(/\s+/g, ' ').toLowerCase()]));
        const C = { ...ctx, L, items, texts }, views = [[{}, { kind: 'all' }, null, 'default'], [{ show: 'all' }, { kind: 'all' }, null, 'show=all']];
        const opts = facetOpts(L, items); L.facets.forEach(([f]) => Object.keys(opts[f]).forEach(v => views.push([{ [f]: v }, { kind: 'all' }, null, `${f}=${v}`])));
        L.sorts.slice(1).forEach(([k]) => views.push([{ sort: k }, { kind: 'all' }, null, `sort=${k}`]));
        await B.go(key); const first = doc.querySelector('section[data-shape="list"] tbody tr[data-row] .ia-row-go'), fw = first ? norm(first.textContent).split(' ')[0].toLowerCase() : '';
        if (fw) views.push([{ q: fw }, { kind: 'all' }, null, 'q']);
        [...doc.querySelectorAll('.ux-scope-sw .ux-pop-menu a[href]')].map(a => decodeURIComponent(a.getAttribute('href'))).forEach(h => { const m = h.match(/[?&]scope=(site|group):([^&]+)/);
          if (m) views.push([{}, { kind: m[1], id: m[2] }, `${m[1]}:${m[2]}`, `scope ${m[1]}:${m[2]}`]); });
        for (const [q, scope, sp, tag] of views) { await B.go(addr(key, L, q, sp)); checkView(C, key, q, scope, sp, `${sn} · ${key} · ${tag}`); }
        if (!how) counts.push(`${B.opName} ${key} ${ownView(key, L, items, {}, { kind: 'all' }, texts, vert).n}`);
        /* D-IA.73 (a): the in-page path (the Sort select changed from the default view) and a fresh boot of the same address give a byte-identical L2 */
        if (!how) for (const [k] of L.sorts.slice(1)) {
          await B.go(key); const sel = doc.querySelector('section[data-shape="list"] [data-ia-list-tools] select[name="sort"]');
          if (!sel) continue; sel.value = k; sel.dispatchEvent(new w.Event('change', { bubbles: true })); await sleep(60);
          const h = w.location.hash.slice(2), inPage = l2Of(doc); stat.restore++;
          if (h !== addr(key, L, { sort: k }, null)) fails.push(`B ${B.opName} · ${key}: the Sort change wrote #/${h}, expected #/${addr(key, L, { sort: k }, null)}`);
          const F2 = await boot(op, h); plantSource(F2.w, 'B'); const fresh = l2Of(F2.doc); F2.dom.window.close();
          if (fresh !== inPage) { const i = [...Array(Math.min((fresh || '').length, (inPage || '').length) + 1).keys()].find(j => (fresh || '')[j] !== (inPage || '')[j]); fails.push(`B ${B.opName} · #/${h}: a fresh boot's L2 differs from the in-page path's at char ${i} (D-IA.73 a): "${(fresh || '').slice(i, i + 60)}" vs "${(inPage || '').slice(i, i + 60)}"`); }
        }
      }
      if (B.errors.length) fails.push(`B ${B.opName} · ${sn}: script error ${B.errors[0]}`);
      B.dom.window.close();
    }
  }
  if (PLANT === 'rowctl' && !PLANT_HITS.n) { console.log('list_shape_check (plant rowctl): the plant found no decision row'); process.exit(2); }
  log.push(`B · ${stat.views} views over ${stat.scen} scenario boots · ${stat.restore} fresh-boot comparisons · lists ${counts.join(', ')} · live cents fallbacks ${stat.cents} (expected 0)`);
}
/* the plan scenarios of D-IA.50 for the Actions list (qty_check's flow) */
async function scenario(B, op, how, fails) {
  const { w, doc } = B, click = async sel => { const e = doc.querySelector(sel); if (!e) return false; e.click(); await sleep(20); return true; }, tag = `B ${B.opName} · ${how}`;
  if (how === 'nd') { for (const [name, val] of [['sw-budget', '6500'], ['sw-loi', 'no']]) { const r = doc.querySelector(`input[name="${name}"][value="${val}"]`); if (!r) { fails.push(`${tag}: no switch ${name}=${val}`); return false; } r.checked = true; r.dispatchEvent(new w.Event('change', { bubbles: true })); await sleep(10); } return true; }
  if (how === 'approve') { if (await click('.ux-planband [data-ux-act="approve-plan"]') && await click('#uxact [data-ux-act-go]')) return true; fails.push(`${tag}: Approve did not run`); return false; }
  if (!await click('.ux-planband [data-ux-act="send-back"]')) { fails.push(`${tag}: no Send back`); return false; }
  const ta = doc.getElementById('ux-sb-reason'), sel = doc.getElementById('ux-sb-way'), opt = sel && [...sel.options].find(o => o.value);
  if (!ta || !opt) { fails.push(`${tag}: the Send back dialog lacks its reason or a trade-off`); return false; }
  ta.value = 'The crew cannot do both visits'; sel.value = opt.value; for (const e of [ta, sel]) for (const t of ['input', 'change']) e.dispatchEvent(new w.Event(t, { bubbles: true }));
  if (await click('#uxact [data-ux-act-go]')) return true; fails.push(`${tag}: Send back did not run`); return false;
}
(async () => {
  const t0 = Date.now(), fails = [], log = [];
  const B0 = await boot('lakeside', 'portfolio'); const on = B0.w.eval("IA_LANDED.has('IA-2b1')"); B0.dom.window.close();
  if (!on) { console.log('IA-2b1 not landed; dormant'); process.exit(0); }
  for (const [n, f] of [['A', blockA], ['B', blockB], ['C', blockC], ['D', blockD]]) { try { await f(fails, log); } catch (e) { fails.push(`${n}: the block threw ${String(e && e.message || e).slice(0, 200)}`); } }
  log.forEach(l => console.log('  ' + l));
  console.log(`list_shape_check · ${((Date.now() - t0) / 1000).toFixed(1)} s${PLANT ? ` · plant ${PLANT}` : ''}`);
  if (fails.length) { console.log(`${fails.length} FAIL\n` + fails.slice(0, process.env.LIST_VERBOSE ? 1e6 : 14).map(f => '  ' + f).join('\n')); console.log('list_shape_check: FAIL'); process.exit(1); }
  console.log('list_shape_check: PASS'); process.exit(0);
})();
