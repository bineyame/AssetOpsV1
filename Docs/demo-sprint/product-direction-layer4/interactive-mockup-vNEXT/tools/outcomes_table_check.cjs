/* IA-1 Outcomes table check (spec §3.2, D-IA.27), jsdom. Every demo operator has three Sites of one group, so the cap, grouping,
   scope and no-target rules are identity on the data; this check feeds iaOutcomeTable (and iaOutcomeHeadline) synthetic rows:
   A 12 Sites in one group, shuffled: 10 shown, "Show all 12", sorted by gap ascending with ties in the given order;
   B 12 Sites in two groups of 7 and 5: two groups, each headed by its word and count, no cap;
   C B at scope group:<the 7>: 7 rows;
   D a Site without a target among Sites above and below target: last, "Not available yet" in columns 3 to 5, outside the headline's m.
   C also asserts the headline over the scoped rows; E no row with a target: "No Site in this scope has a target in <month>" (D-IA.35 L4).
   Run: node tools/outcomes_table_check.cjs   Plants: OUT_PLANT=cap|group|scope|sort|notarget (each disables its rule in the builder or in iaOutcomeScope), headline (live: shapeHubOutcomes
   passes all rows to the headline; Lakeside ?scope=site:mto). */
const { boot } = require('./ia_crawl.cjs');
const PLANT = process.env.OUT_PLANT || '';
/* each plant rewrites the builder's own source at its rule; a replacement that finds nothing throws, so a plant cannot pass unbitten */
const FN = { scope: 'iaOutcomeScope' }, RULE = {
  cap: [['i >= 10 ?', 'i >= Infinity ?'], ['uxCapNote(sorted.length, 10, id)', "''"]],
  group: [['sorted.length > 10 && groups.length > 1', 'false']],
  scope: [["scope.kind === 'site' ? r.key === scope.id : scope.kind === 'group' ? r.group === scope.id : true", 'true']],
  sort: [['a.hasTarget ? a.gap - b.gap : 0', '0']],
  notarget: [['(a.hasTarget !== b.hasTarget ? (a.hasTarget ? -1 : 1) : a.hasTarget ? a.gap - b.gap : 0)', '((a.gap || 0) - (b.gap || 0))'], ['r.hasTarget ? r.resultHtml : NA', 'r.resultHtml']]
};
if (PLANT && !RULE[PLANT] && PLANT !== 'headline') { console.error(`outcomes_table_check: unknown plant ${PLANT}`); process.exit(2); }
const fails = [], log = [];
(async () => {
  const B = await boot('lakeside', 'portfolio'), { w, doc } = B;
  if (PLANT && PLANT !== 'headline') w.eval(`(() => { const fn = ${JSON.stringify(FN[PLANT] || 'iaOutcomeTable')}; let src = eval(fn).toString(); for (const [a, b] of ${JSON.stringify(RULE[PLANT])}) { if (!src.includes(a)) throw new Error('plant found no rule: ' + a); src = src.split(a).join(b); }
    (0, eval)(fn + ' = eval(' + JSON.stringify('(' + src + ')') + ')'); })()`);
  if (PLANT === 'headline') w.eval(`(() => { let src = shapeHubOutcomes.toString(); const a = 'iaOutcomeHeadline(rows,'; if (!src.includes(a)) throw new Error('plant found no rule'); src = src.replace(a, 'iaOutcomeHeadline(iaOutcomeRows(op),'); shapeHubOutcomes = eval('(' + src + ')'); })()`);
  const row = (i, g, gap, hasTarget = true) => ({ key: `s${i}`, name: `Site ${i}`, group: g, hasTarget, resultHtml: `R${i}`, gapHtml: `G${i}`, gap, driverHtml: `D${i}`, waiting: i % 3 });
  const table = (rows, scope) => { const d = doc.createElement('div'); d.innerHTML = w.eval(`iaOutcomeTable(${JSON.stringify(rows)}, { scope: ${JSON.stringify(scope || { kind: 'all' })} })`); return d; };
  const shown = d => [...d.querySelectorAll('tbody tr[data-site]')].filter(t => !t.hidden).map(t => t.dataset.site), all = d => [...d.querySelectorAll('tbody tr[data-site]')].map(t => t.dataset.site);
  /* A: 12 in one group, shuffled gaps with a tie (s2 and s7 both -50; s2 first in the given order) */
  const gapsA = [-10, 40, -50, -200, 5, -75, 0, -50, 12, -300, 60, -1], A = gapsA.map((g, i) => row(i, 'mini', g)), dA = table(A);
  const wantA = A.map((r, i) => [r, i]).sort((x, y) => x[0].gap - y[0].gap || x[1] - y[1]).map(([r]) => r.key);
  if (shown(dA).length !== 10) fails.push(`A: ${shown(dA).length} rows shown, expected 10`);
  if (!/Show all 12/.test(dA.textContent)) fails.push('A: no "Show all 12"');
  if (all(dA).join(',') !== wantA.join(',')) fails.push(`A: order ${all(dA).join(',')}, expected ${wantA.join(',')}`);
  log.push(`A · ${shown(dA).length} shown of ${all(dA).length} · ${/Show all 12/.test(dA.textContent) ? '"Show all 12"' : 'no cap note'} · order ${all(dA).slice(0, 4).join(',')}…`);
  /* B: 12 in two groups (7 cold, 5 ev) */
  const B12 = [...Array(12)].map((_, i) => row(i, i < 7 ? 'cold' : 'ev', i * 10 - 60)), dB = table(B12), heads = [...dB.querySelectorAll('.ia-out-group th')].map(t => t.textContent.replace(/\s+/g, ' ').trim());
  if (heads.join(' | ') !== 'Cold rooms 7 | EV depots 5') fails.push(`B: group heads "${heads.join(' | ')}", expected "Cold rooms 7 | EV depots 5"`);
  if (shown(dB).length !== 12 || /Show all/.test(dB.textContent)) fails.push(`B: ${shown(dB).length} rows shown${/Show all/.test(dB.textContent) ? ' and a cap note' : ''}, expected 12 and no cap`);
  log.push(`B · groups ${heads.join(' | ') || 'none'} · ${shown(dB).length} shown`);
  /* C: B at group:cold */
  const dC = table(B12, { kind: 'group', id: 'cold' });
  if (all(dC).length !== 7 || all(dC).some(k => +k.slice(1) >= 7)) fails.push(`C: ${all(dC).length} rows at group:cold, expected the 7 cold Sites`);
  log.push(`C · ${all(dC).length} rows at group:cold`);
  /* D: a Site without a target among Sites above and below target */
  const D = [row(0, 'mini', 30), row(1, 'mini', 0, false), row(2, 'mini', -20), row(3, 'mini', 15)], dD = table(D), last = [...dD.querySelectorAll('tbody tr[data-site]')].pop();
  if (last?.dataset.site !== 's1') fails.push(`D: the Site without a target is not last (${all(dD).join(',')})`);
  if (!last || [2, 3, 4].some(c => !/Not available yet/.test(last.children[c].textContent))) fails.push('D: columns 3 to 5 of the Site without a target do not read "Not available yet"');
  const hl = w.eval(`iaOutcomeHeadline(${JSON.stringify(D)}, false, 'October')`); if (hl !== '1 of 3 Sites are below target in October') fails.push(`D: headline "${hl}", expected "1 of 3 Sites are below target in October"`);
  log.push(`D · order ${all(dD).join(',')} · headline "${hl}"`);
  /* C: the headline over the scoped rows, as the hub renders it (the two share iaOutcomeScope) */
  const hC = w.eval(`iaOutcomeHeadline(iaOutcomeScope(${JSON.stringify(B12)}, { kind: 'group', id: 'cold' }), false, 'October')`);
  if (!/^\d+ of 7 Sites are below target in October$/.test(hC)) fails.push(`C: headline over the scoped rows "${hC}", expected "{n} of 7 Sites are below target in October"`);
  /* E: no row with a target */
  const hE = w.eval(`iaOutcomeHeadline(${JSON.stringify([row(0, 'mini', 0, false)])}, false, 'October')`);
  if (hE !== 'No Site in this scope has a target in October') fails.push(`E: headline "${hE}", expected "No Site in this scope has a target in October"`);
  /* live: Lakeside scoped to one Site; the headline counts the rendered rows */
  await B.go('portfolio/outcomes?scope=site:mto');
  const live = doc.querySelectorAll('.ia-outcomes tr[data-site]').length, hlLive = (doc.querySelector('[data-level="L1"] .ux-headline')?.textContent || '').trim(), mm = hlLive.match(/of (\d+) Sites/);
  if (live !== 1) fails.push(`live: Lakeside scope=site:mto renders ${live} rows, expected 1`);
  if (!mm || +mm[1] > live) fails.push(`live: the headline "${hlLive}" counts Sites outside the ${live} rendered row(s)`);
  log.push(`C/E · "${hC}" · "${hE}" · live scope=site:mto ${live} row, headline "${hlLive}"`);
  if (B.errors.length) fails.push(`script errors: ${B.errors[0]}`);
  B.dom.window.close();
  log.forEach(l => console.log('  ' + l));
  console.log(fails.length ? `outcomes_table_check${PLANT ? ` (plant ${PLANT})` : ''}: FAIL\n  ${fails.join('\n  ')}` : `outcomes_table_check${PLANT ? ` (plant ${PLANT})` : ''}: PASS`);
  process.exit(fails.length ? 1 : 0);
})();
