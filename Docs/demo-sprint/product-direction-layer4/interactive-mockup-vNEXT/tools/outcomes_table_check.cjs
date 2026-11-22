/* IA-1 Outcomes table check (spec §3.2, D-IA.27), jsdom; retargeted in IA-2b1 (spec-IA-2b §5 and §8, D-IA.64, D-IA.76, D-IA.80): the Outcomes
   L2 is the Sites list's component without its tools (iaListBody('sites', ctx, { tools: false, tiles: false })). Every demo operator has
   three Sites of one group, so the cap, grouping, scope and no-target rules are identity on the data; this check feeds the component
   synthetic rows (the iaOutcomeRows shape, through IA_LIST_DEFS.sites.items, with window-only SK entries so a group scope resolves) and
   iaOutcomeHeadline:
   A 12 Sites in one group, shuffled: 10 shown, "Show all 12", sorted by gap ascending with ties in the given order;
   B 12 Sites in two groups of 7 and 5 (D-IA.80, one cap per list): 10 shown, heads "Cold rooms 7 | EV depots 5", "Show all 12";
   C B at scope group:<the 7>: 7 rows;
   D a Site without a target among Sites above and below target: last, "Not available yet" in columns 3 to 5, outside the headline's m.
   C also asserts the headline over the scoped rows; E no row with a target: "No Site in this scope has a target in <month>" (D-IA.35 L4).
   R (D-IA.76) every row holds exactly one interactive element, its a.ia-row-go: no button and no second link.
   L (live, once IA-2b1 is landed or IA_FORCE_LANDED=IA-2b1) every operator: the Outcomes rows equal the Sites list's rows at the same
   scope (all and each Site); else "IA-2b1 not landed; dormant".
   Run: node tools/outcomes_table_check.cjs   Plants: OUT_PLANT=cap|group|scope|sort|notarget (each disables its rule in the component or
   the Sites def), headline (live: shapeHubOutcomes passes all rows to the headline; Lakeside ?scope=site:mto). */
const { boot, OPS } = require('./ia_crawl.cjs');
const PLANT = process.env.OUT_PLANT || '';
/* each plant rewrites the product's own source at its rule: [function or def member, [from, to]...]; a replacement that finds nothing
   throws, so a plant cannot pass unbitten */
const RULE = {
  cap: [['iaListModel', ['rank.slice(0, IA_LIST_CAP)', 'rank']]],
  group: [['iaListModel', ['n > IA_LIST_CAP && gs.length > 1', 'false']]],
  scope: [['iaListModel', ['items.filter(it => iaInScope(def.site(it), scope))', 'items.slice()']], ['iaOutcomeScope', ["scope.kind === 'site' ? r.key === scope.id : scope.kind === 'group' ? r.group === scope.id : true", 'true']]],
  sort: [['IA_LIST_DEFS.sites.sorts[0].cmp', ['a.hasTarget ? a.gap - b.gap : 0', '0']]],
  notarget: [['IA_LIST_DEFS.sites.sorts[0].cmp', ['(a.hasTarget !== b.hasTarget ? (a.hasTarget ? -1 : 1) : a.hasTarget ? a.gap - b.gap : 0)', '((a.gap || 0) - (b.gap || 0))']],
    ['IA_LIST_DEFS.sites.row', ['r.hasTarget ? r.result : IA_NA', 'r.result']]]
};
if (PLANT && !RULE[PLANT] && PLANT !== 'headline') { console.error(`outcomes_table_check: unknown plant ${PLANT}`); process.exit(2); }
const fails = [], log = [];
(async () => {
  const B = await boot('lakeside', 'portfolio'), { w, doc } = B;
  if (PLANT && PLANT !== 'headline') for (const [fn, ...rules] of RULE[PLANT]) w.eval(`(() => { let src = (0, eval)(${JSON.stringify(fn)}).toString(); for (const [a, b] of ${JSON.stringify(rules)}) { if (!src.includes(a)) throw new Error('plant found no rule: ' + a); src = src.split(a).join(b); }
    (0, eval)(${JSON.stringify(fn)} + ' = eval(' + JSON.stringify('(' + src + ')') + ')'); })()`);
  const TYPE = { mini: 'Mini-grid', cold: 'Cold room', ev: 'EV depot' };
  const row = (i, g, gap, hasTarget = true) => ({ key: `s${i}`, name: `Site ${i}`, group: g, hasTarget, result: hasTarget ? `R${i}` : '', gapText: hasTarget ? `G${i}` : '', gap, driver: `D${i}`, waiting: i % 3 });
  /* the component on synthetic rows: SK entries for their keys (window only), the rows through the def's items seam */
  const table = (rows, scope, query) => { w.__outRows = rows; w.eval(`(() => { const T = ${JSON.stringify(TYPE)}; window.__outRows.forEach(r => { SK[r.key] = { name: r.name, type: T[r.group], op: 'lakeside' }; }); IA_LIST_DEFS.sites.items = () => window.__outRows.slice(); })()`);
    const d = doc.createElement('div'); d.innerHTML = w.eval(`iaListBody('sites', { op: 'lakeside', scope: ${JSON.stringify(scope || { kind: 'all' })}, query: ${JSON.stringify(query || {})}, params: {}, path: 'portfolio/outcomes' }, { tools: false, tiles: false })`); return d; };
  const keysOf = d => [...d.querySelectorAll('tbody tr[data-row]')].map(t => t.dataset.row), shown = keysOf;
  const all = (rows, scope) => keysOf(table(rows, scope, { show: 'all' }));
  const oneTarget = (d, tag) => d.querySelectorAll('tbody tr[data-row]').forEach(tr => { const ia = [...tr.querySelectorAll('a[href], button, input, select, textarea, summary, [tabindex]:not([tabindex="-1"])')];
    if (ia.length !== 1 || !ia[0].matches('a.ia-row-go')) fails.push(`R ${tag}: row ${tr.dataset.row} has ${ia.length} interactive element(s) (${ia.map(e => e.tagName.toLowerCase()).join(', ')}), expected one a.ia-row-go`); });
  /* A: 12 in one group, shuffled gaps with a tie (s2 and s7 both -50; s2 first in the given order) */
  const gapsA = [-10, 40, -50, -200, 5, -75, 0, -50, 12, -300, 60, -1], A = gapsA.map((g, i) => row(i, 'mini', g)), dA = table(A); oneTarget(dA, 'A');
  const wantA = A.map((r, i) => [r, i]).sort((x, y) => x[0].gap - y[0].gap || x[1] - y[1]).map(([r]) => r.key);
  if (shown(dA).length !== 10) fails.push(`A: ${shown(dA).length} rows shown, expected 10`);
  if (!/Show all 12/.test(dA.textContent)) fails.push('A: no "Show all 12"');
  const allA = all(A); if (allA.join(',') !== wantA.join(',') || shown(dA).join(',') !== wantA.slice(0, 10).join(',')) fails.push(`A: order ${allA.join(',')} (shown ${shown(dA).join(',')}), expected ${wantA.join(',')}`);
  log.push(`A · ${shown(dA).length} shown of ${allA.length} · ${/Show all 12/.test(dA.textContent) ? '"Show all 12"' : 'no cap note'} · order ${allA.slice(0, 4).join(',')}…`);
  /* B: 12 in two groups (7 cold, 5 ev) */
  const B12 = [...Array(12)].map((_, i) => row(i, i < 7 ? 'cold' : 'ev', i * 10 - 60)), dB = table(B12), heads = [...dB.querySelectorAll('.ia-list-group th')].map(t => t.textContent.replace(/\s+/g, ' ').trim()); oneTarget(dB, 'B');
  if (heads.join(' | ') !== 'Cold rooms 7 | EV depots 5') fails.push(`B: group heads "${heads.join(' | ')}", expected "Cold rooms 7 | EV depots 5"`);
  const moreB = [...dB.querySelectorAll('a')].filter(a => /^Show all \d+$/.test(a.textContent.trim())).map(a => a.textContent.trim());
  if (shown(dB).length !== 10 || moreB.join() !== 'Show all 12') fails.push(`B: ${shown(dB).length} rows shown and "${moreB.join(', ') || 'no Show all'}", expected 10 and one "Show all 12" (D-IA.80: one cap per list)`);
  log.push(`B · groups ${heads.join(' | ') || 'none'} · ${shown(dB).length} shown · ${moreB.join(', ') || 'no Show all'}`);
  /* C: B at group:cold */
  const dC = table(B12, { kind: 'group', id: 'cold' }), allC = all(B12, { kind: 'group', id: 'cold' });
  if (allC.length !== 7 || allC.some(k => +k.slice(1) >= 7)) fails.push(`C: ${allC.length} rows at group:cold, expected the 7 cold Sites`);
  log.push(`C · ${allC.length} rows at group:cold`);
  /* D: a Site without a target among Sites above and below target */
  const D = [row(0, 'mini', 30), row(1, 'mini', 0, false), row(2, 'mini', -20), row(3, 'mini', 15)], dD = table(D), last = [...dD.querySelectorAll('tbody tr[data-row]')].pop(); oneTarget(dD, 'D');
  if (last?.dataset.row !== 's1') fails.push(`D: the Site without a target is not last (${keysOf(dD).join(',')})`);
  if (!last || [2, 3, 4].some(c => !/Not available yet/.test(last.children[c].textContent))) fails.push('D: columns 3 to 5 of the Site without a target do not read "Not available yet"');
  const hl = w.eval(`iaOutcomeHeadline(${JSON.stringify(D)}, false, 'October')`); if (hl !== '1 of 3 Sites are below target in October') fails.push(`D: headline "${hl}", expected "1 of 3 Sites are below target in October"`);
  log.push(`D · order ${keysOf(dD).join(',')} · headline "${hl}"`);
  /* C: the headline over the scoped rows, as the hub renders it (the two share iaOutcomeScope) */
  const hC = w.eval(`iaOutcomeHeadline(iaOutcomeScope(${JSON.stringify(B12)}, { kind: 'group', id: 'cold' }), false, 'October')`);
  if (!/^\d+ of 7 Sites are below target in October$/.test(hC)) fails.push(`C: headline over the scoped rows "${hC}", expected "{n} of 7 Sites are below target in October"`);
  /* E: no row with a target */
  const hE = w.eval(`iaOutcomeHeadline(${JSON.stringify([row(0, 'mini', 0, false)])}, false, 'October')`);
  if (hE !== 'No Site in this scope has a target in October') fails.push(`E: headline "${hE}", expected "No Site in this scope has a target in October"`);
  /* live: Lakeside scoped to one Site; the headline counts the rendered rows (a fresh boot: the synthetic rows stay in the first window) */
  B.dom.window.close();
  const L = await boot('lakeside', 'portfolio'); if (PLANT === 'headline') L.w.eval(`(() => { let src = shapeHubOutcomes.toString(); const a = 'iaOutcomeHeadline(rows,'; if (!src.includes(a)) throw new Error('plant found no rule'); src = src.replace(a, 'iaOutcomeHeadline(iaOutcomeRows(op),'); shapeHubOutcomes = eval('(' + src + ')'); })()`);
  await L.go('portfolio/outcomes?scope=site:mto');
  const LR = d => [...d.querySelectorAll('table.ia-list tbody tr[data-row]')];
  const live = LR(L.doc).length, hlLive = (L.doc.querySelector('[data-level="L1"] .ux-headline')?.textContent || '').trim(), mm = hlLive.match(/of (\d+) Sites/);
  if (live !== 1) fails.push(`live: Lakeside scope=site:mto renders ${live} rows, expected 1`);
  if (!mm || +mm[1] > live) fails.push(`live: the headline "${hlLive}" counts Sites outside the ${live} rendered row(s)`);
  log.push(`C/E · "${hC}" · "${hE}" · live scope=site:mto ${live} row, headline "${hlLive}"`);
  if (L.errors.length) fails.push(`script errors: ${L.errors[0]}`);
  L.dom.window.close();
  /* L: the Outcomes rows are the Sites list's rows at the same scope (D-IA.64), once the list is landed */
  const landed = (process.env.IA_FORCE_LANDED || '').split(',').includes('IA-2b1');
  for (const op of OPS) { const V = await boot(op, 'portfolio'); if (!landed && !V.w.eval("IA_LANDED.has('IA-2b1')")) { V.dom.window.close(); if (op === OPS[0]) log.push('L · IA-2b1 not landed; dormant'); break; }
    const scopes = ['', ...V.w.eval(`OPS[${JSON.stringify(op)}].sites`).map(k => `site:${k}`)], got = [];
    for (const sc of scopes) { const q = sc ? `?scope=${sc}` : '';
      await V.go(`portfolio/outcomes${q}`); const o = LR(V.doc).map(r => r.outerHTML); oneTarget(V.doc.querySelector('[data-level="L2"]') || V.doc, `${op} outcomes${q}`);
      await V.go(`sites${q}`); const l = LR(V.doc).map(r => r.outerHTML);
      if (o.join('') !== l.join('') || !o.length) fails.push(`L ${op}${q}: the Outcomes rows (${o.length}) are not the Sites list's rows (${l.length})`); got.push(`${sc || 'all'} ${o.length}`); }
    log.push(`L · ${op} · Outcomes rows = Sites rows at ${got.join(', ')}`);
    if (V.errors.length) fails.push(`${op}: script errors: ${V.errors[0]}`); V.dom.window.close(); }
  log.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `outcomes_table_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${fails.join('\n  ')}` : `outcomes_table_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
})();
