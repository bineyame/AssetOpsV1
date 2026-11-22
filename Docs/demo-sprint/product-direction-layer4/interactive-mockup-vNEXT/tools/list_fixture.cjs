/* IA-2b1 list fixture (spec-IA-2b §8 block D, D-IA.67, D-IA.68): synthetic stores for the scale case, injected into a booted window
   through the list def's items(op) seam (IA_LIST_DEFS[key].items, which is not cached), then rendered by the real route. Tools only:
   index.html never loads this file and no product route reaches it. The window is the only thing changed.
   sites30: 30 Sites in three groups (18 Mini-grids, 7 Cold rooms, 5 EV depots), one without a target. Every gap ends in .40 so the
     shown rows' whole-dollar gaps plus the remainder miss the whole-dollar rounding of the exact total: the cents fallback (§3.4).
     Rows have the iaOutcomeRows shape with D-IA.76's text fields: { key, name, group, hasTarget, gap, result, gapText, driver, waiting }.
     Their keys (fx01 to fx30) are not Sites of any operator, so their row links are unlinked text: block D asserts counts, not targets.
   decisions25: 25 decisions of the booted operator, cloned from its own decisions (each clone keeps the source's Site, options and rights,
     so the reviewed uxDecState gives it the source's state) and registered in the window's DEC so that decById and the row link resolve.
     6 are waiting for a choice, placed so that 3 of them sit below the 10th row in store order (the keep-first rule, D-IA.34).
   Use: const F = require('./list_fixture.cjs'); F.install(w, 'sites30' | 'decisions25'[, n]) returns the injected items (n slices the
   store, for the tier cases); IA_LIST_FIXTURE=sites30|decisions25 names one for ia_shots. */
const GROUPS = [['mini', 18], ['cold', 7], ['ev', 5]];
function sites30(w) {
  const usdW = w.eval('usdW'), out = []; let i = 0;
  for (const [g, n] of GROUPS) for (let j = 0; j < n; j++) {
    i++; const key = `fx${String(i).padStart(2, '0')}`, gap = i === 30 ? null : (i % 4 === 0 ? 1 : -1) * (40 + ((i * 37) % 23) * 11) - 0.4 * (i % 4 === 0 ? -1 : 1), has = i !== 30;
    out.push({ key, name: `Fixture Site ${i}`, group: g, hasTarget: has, gap: has ? Math.round(gap * 100) / 100 : 0,
      result: has ? `$${1000 + i * 10} against a target of $${1000 + i * 10 - Math.round(gap)}` : '', gapText: has ? usdW(gap, true) : '',
      driver: has ? `Fixture driver ${i} ${usdW(gap, true)} Optimize cost and efficiency` : 'No driver widens the gap', waiting: i % 5 === 0 ? 1 : 0 });
  }
  return out;
}
const WAIT_AT = [1, 4, 8, 12, 17, 23]; /* 0-based store positions of the 6 waiting clones */
function decisions25(w) {
  const op = w.eval('LS.op'), ids = w.eval(`[...new Set(ATTN[${JSON.stringify(op)}].map(r => r[4]))]`), st = id => w.eval(`uxDecState(${JSON.stringify(id)}).key`);
  const W = ids.filter(id => ['choose', 'none'].includes(st(id))), N = ids.filter(id => !['choose', 'none'].includes(st(id)));
  if (!W.length || !N.length) throw new Error(`list_fixture decisions25: ${op} needs a waiting and a non-waiting decision to clone (use lakeside)`);
  const out = []; let wi = 0, ni = 0;
  for (let i = 0; i < 25; i++) { const src = WAIT_AT.includes(i) ? W[wi++ % W.length] : N[ni++ % N.length], id = `fx-${i + 1}-${src}`;
    w.eval(`(() => { if (!decById(${JSON.stringify(id)})) { const s = decById(${JSON.stringify(src)}); DEC.push({ ...s, id: ${JSON.stringify(id)}, q: s.q + ' (fixture ${i + 1})' }); } })()`);
    out.push(id); }
  return out;
}
const BUILD = { sites30: ['sites', sites30], decisions25: ['decisions', decisions25] };
function install(w, name, n) {
  const b = BUILD[name]; if (!b) throw new Error(`list_fixture: unknown fixture ${name}`);
  if (w.eval(`typeof IA_LIST_DEFS === 'object' && !!IA_LIST_DEFS[${JSON.stringify(b[0])}]`) !== true) throw new Error(`list_fixture: the window has no IA_LIST_DEFS.${b[0]} (the list is not built)`);
  const items = b[1](w).slice(0, n == null ? undefined : n);
  w.__iaFixture = items; w.eval(`IA_LIST_DEFS[${JSON.stringify(b[0])}].items = () => window.__iaFixture.slice()`);
  return items;
}
module.exports = { install, sites30, decisions25, WAIT_AT, GROUPS, LIST_OF: { sites30: 'sites', decisions25: 'decisions' } };
