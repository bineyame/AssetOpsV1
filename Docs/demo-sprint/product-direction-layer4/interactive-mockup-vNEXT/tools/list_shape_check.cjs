/* IA-2b1 list shape check (spec-IA-2b §8 rows 1 to 4; D-IA.62, D-IA.66 to D-IA.70, D-IA.73, D-IA.80), jsdom. Runs only when IA_LANDED has
   IA-2b1 (or IA_FORCE_LANDED=IA-2b1); otherwise prints "IA-2b1 not landed; dormant" and exits 0.
   A synthetic: iaListModel and iaListHref on a 25-item store in 3 groups (the only block that calls the list's code).
   B live: every operator x the four lists (PARTIAL: not yet written; it fails while landed, so the gate cannot pass without it).
   C the scope menu on a list. D the fixture (tools/list_fixture.cjs), rendered by the real route.
   Plants (LIST_PLANT): A cap, keep, scope, search, sort, invalid, group, canon, tier; B tile, rowctl, restore, own, stakesort, notarget;
   C scopemenu; D remainder (tier and group also bite D). A source plant rewrites the product function at its rule; a rule the source
   lacks exits 2, so a plant cannot pass unbitten. */
const { boot, OPS, sleep } = require('./ia_crawl.cjs');
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
  scopemenu: ['iaScopeEntries', ["route && route.shape === 'list'", 'false']] };
const BLOCK = { cap: 'A', keep: 'A', scope: 'A', search: 'A', sort: 'A', invalid: 'A', group: 'AD', canon: 'A', tier: 'AD', scopemenu: 'C', remainder: 'D', tile: 'BD', rowctl: 'B', restore: 'B', own: 'B', stakesort: 'B', notarget: 'B' };
if (PLANT && !BLOCK[PLANT]) { console.error(`list_shape_check: unknown plant ${PLANT}`); process.exit(2); }
function plantSource(w, block) {
  if (!PLANT || !BLOCK[PLANT].includes(block)) return;
  if (SRC[PLANT]) { const [fn, ...rules] = SRC[PLANT]; const ok = w.eval(`(() => { if (typeof ${fn} !== 'function') return 'no function ${fn}'; let s = ${fn}.toString(); for (const [a, b] of ${JSON.stringify(rules)}) { if (!s.includes(a)) return 'plant found no rule: ' + a; s = s.split(a).join(b); } (0, eval)('${fn} = ' + s); return ''; })()`);
    if (ok) { console.log(`list_shape_check (plant ${PLANT}): ${ok}`); process.exit(2); } w.eval('render()'); return; }
  if (PLANT === 'remainder') { w.eval(`(() => { const d = IA_LIST_DEFS.sites, m = d.more; d.more = () => ''; })()`); return; }
  /* the B plants are written with block B */
}
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
  const items = [...Array(25)].map((_, i) => { const g = G[i % 3]; return { id: `i${i}`, site: byV[g][i % byV[g].length], g, f: ['a', 'b', 'c'][i % 3 === 2 ? 2 : i % 2], v: (i * 7) % 5, t: WORDS[i % 5], keep: i === 20 || i === 23 }; });
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
  if (heads.join(' | ') !== 'Mini-grids 18 | Cold rooms 7 | EV depots 5') fails.push(`D sites30: group heads "${heads.join(' | ')}", expected "Mini-grids 18 | Cold rooms 7 | EV depots 5"`);
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
/* ---- Block B: live (PARTIAL, see specs/IA-1-shape-rebuild/handoff-IA-2b1.md) ---- */
async function blockB(fails, log) { fails.push('B: block B (live, every operator x the four lists) is not written yet'); log.push('B · not written'); }
(async () => {
  const t0 = Date.now(), fails = [], log = [];
  const B0 = await boot('lakeside', 'portfolio'); const on = B0.w.eval("IA_LANDED.has('IA-2b1')"); B0.dom.window.close();
  if (!on) { console.log('IA-2b1 not landed; dormant'); process.exit(0); }
  await blockA(fails, log); await blockB(fails, log); await blockC(fails, log); await blockD(fails, log);
  log.forEach(l => console.log('  ' + l));
  console.log(`list_shape_check · ${((Date.now() - t0) / 1000).toFixed(1)} s${PLANT ? ` · plant ${PLANT}` : ''}`);
  if (fails.length) { console.log(`${fails.length} FAIL\n` + fails.slice(0, 14).map(f => '  ' + f).join('\n')); console.log('list_shape_check: FAIL'); process.exit(1); }
  console.log('list_shape_check: PASS'); process.exit(0);
})();
