/* Browser interaction check (UI/UX guide gate G3/G4 support): drawers, table views, phone Section menu, keyboard focus,
   heading order, reduced motion, empty and loading states. Needs /opt/assetecon/tools/pw/env.sh sourced.
   Run: node tools/ux_interaction_check.cjs "$PWD/index.html" <folder for the two state screenshots>
   IA-1b fix round: D-IA.31 drawer walks (every press stays inside; sweep; unlinked last), D-IA.35 L1/L2 (EV board on its live route; text-accepting retargets
   expire with IA-1c). Plants (each must fail): container, x5, palette, block7, tall, viewall, trap (D-IA.31), evrev. expiry (D-IA.35) is retired with IA-1c:
   its decision links are live, so the three evaluations pass on the real links and TEXT_OK is false whatever the plant. */
const { chromium } = require(process.env.PW);
const base = 'file://' + (process.argv[2] || require('path').resolve(__dirname, '..', 'index.html')); /* ia_gates passes no argument: this tree's page */
const out = []; const ok = (c, what) => out.push(`${c ? 'PASS' : 'FAIL'} ${what}`);
/* review r4 H1 and r5 G1: the plan's item list, measured (cells never overlap or overflow; the row never overflows its own box) */
const PLAN_LAYOUT = () => { const bad = [], inter = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1;
      const head = document.querySelector('.ux-itemh'), card = !head || getComputedStyle(head).display === 'none'; let rows = 0;
      const check = (el, name) => { const cs = [...el.children].filter(c => !c.classList.contains('ux-disc-cue') && getComputedStyle(c).display !== 'none'), rc = cs.map(c => c.getBoundingClientRect());
        cs.forEach((c, i) => { if (c.scrollWidth > c.clientWidth + 1) bad.push(`${name}: cell ${i} text is wider than its cell`); for (let j = i + 1; j < cs.length; j++) if (inter(rc[i], rc[j])) bad.push(`${name}: cells ${i} and ${j} overlap`); }); return rc; };
      if (head && !card) check(head, 'header');
      document.querySelectorAll('summary.ux-itemrow').forEach(s => { rows++; const rc = check(s, s.parentElement.dataset.row); if (!card && rc[0].width < 160) bad.push(`${s.parentElement.dataset.row}: item cell ${Math.round(rc[0].width)} px`);
        /* r5 G1: the row never overflows its own box, and its last cell ends inside its card */
        if (s.scrollWidth > s.clientWidth + 1) bad.push(`${s.parentElement.dataset.row}: row ${s.scrollWidth} px wide in a ${s.clientWidth} px box`);
        const box = (s.closest('.panel, .ux-items') || s).getBoundingClientRect(), last = rc.filter(r => r.width > 0).pop(); if (last && last.right > box.right + 1) bad.push(`${s.parentElement.dataset.row}: last cell ends at ${Math.round(last.right)}, past its card at ${Math.round(box.right)}`); });
      return { rows, card, bad: [...new Set(bad)].slice(0, 3) }; };
let TEXT_OK = null; /* D-IA.35 L2: the text form of an unbuilt decision link counts only until IA-1c lands; expiry forces landed */
/* IA-2a (spec §5.1.8 row 6, D-IA.48, D-IA.49): IA_FORCE_LANDED=<unit>[,…] adds the units to IA_LANDED on every page after load and renders
   again (prep, after every goto and reload). With IA-2a landed or forced, the plan block reads the plan shape: at least 2 answer-titled
   sections on plan (was 4: Left out, Listed beside and the review moved to their tabs), plan/left-out with at least 2 answer-titled sections,
   each answered; the M1 "every page agrees after Approve" routes gain plan/left-out, plan/review and plan/history; on each tab, after scrolling
   to the end, the sticky bar carries Approve or, on a tab too short to scroll the band away, the band's Approve stays in view. Otherwise
   it prints "IA-2a not landed; dormant". Plants UXI_PLANT=planans (Left out's answers emptied), planwait (History's sub says "awaiting
   approval" after Approve); each must fail. */
const FORCED = String(process.env.IA_FORCE_LANDED || '').split(',').map(x => x.trim()).filter(Boolean);
const prep = async p => { await p.evaluate(([u, plant]) => { u.forEach(x => IA_LANDED.add(x));
  if (plant === 'planans' && typeof shapePlan === 'function') { const _s = shapePlan; shapePlan = (ctx, tab) => { const h = _s(ctx, tab); if (tab !== 'left-out') return h; const t = document.createElement('template'); t.innerHTML = h; t.content.querySelectorAll('.ux-ans').forEach(e => { e.textContent = ''; }); return t.innerHTML; }; }
  if (plant === 'planwait' && typeof iaPlanHistory === 'function') { const _h = iaPlanHistory; iaPlanHistory = op => _h(op).replace(/(Version [\d,]+, )approved/, '$1awaiting approval'); }
  if (u.length || plant === 'planans' || plant === 'planwait') render(); }, [FORCED, process.env.UXI_PLANT || '']); };
/* IA-2b1 (spec-IA-2b §5, mid-build Q6): #/portfolio/act-first is an alias of the Decisions list once IA-2b1 lands; the reviewed screen stays
   registered, and the blocks that measure it read it with the alias removed in that window only (as plan_switch_check does) */
const actFirst = async (p, hash) => { if (hash !== 'portfolio/act-first') return; await p.evaluate(() => { if (typeof IA_ALIASES === 'object' && 'portfolio/act-first' in IA_ALIASES && IA_LANDED.has('IA-2b1')) { delete IA_ALIASES['portfolio/act-first']; history.replaceState(null, '', '#/portfolio/act-first'); render(); } }); await p.waitForTimeout(100); };
const PLANT = process.env.UXI_PLANT || ''; /* UXI_PLANT=anchor: (D-IA.36) iaInPage returns false, the in-page link lands on not-found; UXI_PLANT=container: the item list's container query removed; the layout gate must fail at 1440 and 1280 */
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  /* D-IA.31: after every one of 30 Tab and 30 Shift+Tab presses the focus is inside the open drawer; returns the first leak or null */
  const walk = async (p, sel) => { for (const dir of ['Tab', 'Shift+Tab']) for (let i = 0; i < 30; i++) { await p.keyboard.press(dir); await p.waitForTimeout(12);
    const at = await p.evaluate(s => document.activeElement.closest(s) ? null : `${document.activeElement.tagName.toLowerCase()}.${String(document.activeElement.className).split(' ')[0]}`, sel); if (at) return `${dir} press ${i + 1} left the drawer for ${at}`; } return null; };
  const unlinkedLast = async p => { await p.click('[data-ux-drawer="uxd-lakeside-assure"]'); await p.waitForTimeout(250);
    await p.evaluate(() => { const d = document.getElementById('uxd-lakeside-assure'), x = d.querySelector('.ux-x'); d.querySelectorAll('a[href]').forEach(a => { if (x.compareDocumentPosition(a) & Node.DOCUMENT_POSITION_FOLLOWING) { const sp = document.createElement('span'); sp.className = 'ia-unlinked'; sp.dataset.iaTo = a.getAttribute('href').replace(/^#\//, ''); sp.innerHTML = a.innerHTML; a.replaceWith(sp); } });
      const body = d.querySelector('.ux-drawer-body') || d; body.insertAdjacentHTML('beforeend', '<details data-plant-d><summary>More</summary><a href="#/plan">x</a></details>'); });
    const leak = await walk(p, '#uxd-lakeside-assure');
    await p.evaluate(() => document.querySelector('#uxd-lakeside-assure .ux-x').focus()); await p.keyboard.press('Shift+Tab'); await p.waitForTimeout(12);
    const onSummary = await p.evaluate(() => document.activeElement === document.querySelector('#uxd-lakeside-assure details[data-plant-d] > summary'));
    return { leak, onSummary }; };
  const openAll = p => p.evaluate(() => document.querySelectorAll('.canvas details').forEach(d => { d.open = true; }));
  const page = async (hash, o = {}) => { const ctx = await b.newContext({ viewport: { width: o.w || 1440, height: o.h || 900 }, colorScheme: o.dark ? 'dark' : 'light', reducedMotion: o.rm ? 'reduce' : 'no-preference' }); if (o.op) await ctx.addInitScript(v => { try { sessionStorage.setItem('l4-op', v); } catch (e) {} }, o.op);
    /* review Site M3: sideways overflow is any visible element in the canvas past the viewport outside its own scrolling frame;
       the page never scrolls sideways (.workspace clips), so the page's scrollWidth alone cannot fail */
    await ctx.addInitScript(() => { window.__ovf = () => { const out = []; for (const e of document.querySelectorAll('#app .canvas *')) { const a = e.getBoundingClientRect(); if (a.width <= 1 || a.height <= 1 || (a.right <= innerWidth + 1 && a.left >= -1)) continue; if (e.closest('.ux-drawer:not([data-open="true"]), [hidden], .vh')) continue;
      let sc = false; for (let x = e.parentElement; x && !sc && !x.matches('.canvas'); x = x.parentElement) { const ov = getComputedStyle(x).overflowX; sc = ov === 'auto' || ov === 'scroll'; } if (!sc) out.push(`${e.tagName.toLowerCase()}.${String(e.className).split(' ')[0]} ${Math.round(a.left)}..${Math.round(a.right)}`); } return out.length ? out.slice(0, 3).join('; ') : false; }; }); const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); await p.goto(base + (o.q || '') + '#/' + hash); await p.waitForTimeout(500); await prep(p); await p.waitForTimeout(100); await actFirst(p, hash); p._errs = errs; if (TEXT_OK === null) TEXT_OK = PLANT === 'expiry' ? false : !(await p.evaluate(() => IA_LANDED.has('IA-1c'))); await p.evaluate(v => { window.__tx = v; }, TEXT_OK); return p; };
  if (PLANT === 'container') { for (const op of ['lakeside', 'harvest', 'metro']) for (const [w, h] of [[1440, 900], [1280, 720]]) { const p = await page('plan', { op, w, h });
      await p.evaluate(() => { for (const sh of document.styleSheets) for (let i = sh.cssRules.length - 1; i >= 0; i--) { const r = sh.cssRules[i]; if (r.constructor.name === 'CSSContainerRule' && r.containerName === 'uxitems') sh.deleteRule(i); } }); await p.waitForTimeout(150);
      const lay = await p.evaluate(PLAN_LAYOUT); ok(lay.rows > 0 && !lay.bad.length, `plant container: ${op} plan at ${w}: ${lay.rows} rows${lay.bad.length ? `, ${lay.bad.join('; ')}` : ''}`); await p.context().close(); }
    await b.close(); console.log(out.join('\n')); process.exit(out.some(l => l.startsWith('FAIL')) ? 1 : 0); }
  /* IA-1b (D-IA.16): on an IA route the palette lists only live entries, so "kobo gen" finds nothing until decisions land (IA-1c);
     "kisiwa" finds the Site and Enter opens it. Retargeted from "kobo gen opens the decision"; UXI_PLANT=palette (filter off) must fail.
     IA-1c: decisions are live, so "kobo gen" finds the decision; the filter is then proven by "findings" (Findings is IA-2b's), which must
     find nothing live. */
  async function paletteTest(p) {
    await p.keyboard.press('Control+k'); await p.waitForTimeout(150);
    const op1 = await p.evaluate(() => document.getElementById('ux-cmd')?.dataset.open === 'true' && document.activeElement.classList.contains('ux-cmd-in'));
    await p.keyboard.type('kobo gen'); await p.waitForTimeout(100);
    const kg = await p.evaluate(() => document.querySelector('#ux-cmd-list [aria-selected="true"]')?.textContent || ''), decLive = await p.evaluate(() => IA_LANDED.has('IA-1c')), listLive = await p.evaluate(() => IA_LANDED.has('IA-2b1'));
    await p.fill('.ux-cmd-in', 'findings'); await p.waitForTimeout(100);
    const fd = await p.evaluate(() => document.querySelector('#ux-cmd-list [aria-selected="true"]')?.textContent || '');
    await p.fill('.ux-cmd-in', 'kisiwa'); await p.waitForTimeout(100);
    const first = await p.evaluate(() => document.querySelector('#ux-cmd-list [aria-selected="true"]')?.textContent || '');
    await p.keyboard.press('Enter'); await p.waitForTimeout(400);
    const at = await p.evaluate(() => location.hash);
    ok(op1 && (decLive ? /Kobo generator/.test(kg) : !/Kobo generator/.test(kg)) && (listLive ? /^Findings/.test(fd) : !fd) && /Kisiwa/.test(first) && at === '#/site/kisiwa', `command search: Ctrl+K opens, "kobo gen" finds ${kg ? `"${kg}"` : 'nothing live'}, "findings" finds ${fd ? `"${fd}"` : 'nothing live'}, "kisiwa" finds "${first}", Enter opens ${at}`);
    if (at !== '#/portfolio') { await p.goto(base + '#/portfolio'); await p.waitForTimeout(400); }
  }
  const evBoard = async () => { const p = await page('portfolio/demand-and-capacity', { op: 'metro' }); /* D-IA.35 L1: the live route, not the legacy builder */
    if (PLANT === 'evrev') await p.evaluate(() => { document.querySelectorAll('#app li.ux-vc-stage.is-na').forEach(li => { const w = document.createTreeWalker(li, NodeFilter.SHOW_TEXT); let n; while ((n = w.nextNode())) if (/Not applicable/.test(n.nodeValue)) n.nodeValue = n.nodeValue.replace('Not applicable', 'Not measured yet'); }); });
    const r = await p.evaluate(() => ({ rows: [...document.querySelectorAll('#app li.ux-vc-stage')].filter(l => /Revenue/.test(l.textContent) && /charging is a cost centre/.test(l.textContent) && /Not applicable/.test(l.textContent)).length, bad: /Grow revenue\s*Not measured yet/.test(document.body.textContent) }));
    ok(r.rows === 1 && !r.bad, `EV board: Metro #/portfolio/demand-and-capacity has ${r.rows} Revenue row reading "charging is a cost centre" and "Not applicable"${r.bad ? ', and "Grow revenue Not measured yet" appears' : ''}`); await p.context().close(); };
  if (PLANT === 'evrev') { await evBoard(); await b.close(); console.log(out.join('\n')); process.exit(out.some(l => l.startsWith('FAIL')) ? 1 : 3); }
  if (PLANT === 'trap') { /* D-IA.31: the pre-fix filter; "drawer trap unlinked last" and the Lakeside "overview drawer assure" walk must both fail */
    const p = await page('portfolio'); await p.evaluate(() => { uxTabbable = x => x.offsetParent !== null; });
    const u = await unlinkedLast(p); ok(!u.leak && u.onSummary, `plant trap: drawer trap unlinked last: ${u.leak || (u.onSummary ? 'holds' : 'Shift+Tab from Close does not land on the last summary')}`);
    const q = await page('portfolio'); await q.evaluate(() => { uxTabbable = x => x.offsetParent !== null; }); await q.click('[data-ux-drawer="uxd-lakeside-assure"]'); await q.waitForTimeout(250);
    await q.evaluate(() => { const d = document.getElementById('uxd-lakeside-assure'), x = d.querySelector('.ux-x'); d.querySelectorAll('a[href]').forEach(a => { if (x.compareDocumentPosition(a) & Node.DOCUMENT_POSITION_FOLLOWING) { const sp = document.createElement('span'); sp.className = 'ia-unlinked'; sp.innerHTML = a.innerHTML; a.replaceWith(sp); } }); });
    const w = await walk(q, '#uxd-lakeside-assure'); ok(!w, `plant trap: overview drawer assure walk: ${w || 'holds'}`);
    await b.close(); console.log(out.join('\n')); const passed = out.filter(l => l.startsWith('PASS')).length; if (passed) { console.log(`plant trap NOT CAUGHT: ${passed} of 2 passed`); process.exit(3); } process.exit(1); }
  if (PLANT === 'x5') { const p = await page('site/mto'); const bad = await p.evaluate(() => { document.querySelectorAll('.ux-queue-panel .ux-qcount').forEach(q => q.remove()); const out = [];
      document.querySelectorAll('.canvas [data-count]').forEach(e => { const n = document.querySelectorAll(e.dataset.countOf || '#none').length, capped = /ux-queue/.test(e.dataset.countOf || '') && [...document.querySelectorAll('.ux-queue-panel .ux-qcount')].some(q => +q.dataset.total === +e.dataset.count); if (+e.dataset.count !== n && !capped) out.push(`count ${e.dataset.count} but ${n} in ${e.dataset.countOf}`); }); return out; });
    ok(!bad.length, `plant x5: site/mto without its "3 of 4" line: ${bad.join('; ') || 'counts hold'}`); await b.close(); console.log(out.join('\n')); process.exit(out.some(l => l.startsWith('FAIL')) ? 1 : 0); }
  if (PLANT === 'palette') { const p = await page('portfolio'); await p.evaluate(() => { iaPaletteFilter = out => out; }); await paletteTest(p); await b.close(); console.log(out.join('\n')); process.exit(out.some(l => l.startsWith('FAIL')) ? 1 : 0); }
  /* IA-1b plants (spec §6 item 4, P16): block7 adds two blocks to the Overview's L3 (seven), tall one block that takes the hub past
     2,500 px, viewall puts the "View all" line back on the phone queue; each must fail its retargeted assertion */
  if (['block7', 'tall', 'viewall'].includes(PLANT)) {
    for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', PLANT === 'viewall' ? { op, w: 390, h: 844 } : { op });
      const r = await p.evaluate(pl => { const l3 = document.querySelector('[data-shape="hub"] > [data-level="L3"]');
        if (pl === 'block7') l3.insertAdjacentHTML('beforeend', '<div style="height:20px">plant</div><div style="height:20px">plant</div>');
        if (pl === 'tall') { const hub = document.querySelector('[data-shape="hub"]'); l3.insertAdjacentHTML('beforeend', `<div style="height:${Math.max(200, 2501 - Math.round(hub.getBoundingClientRect().height))}px">plant</div>`); }
        if (pl === 'viewall') document.querySelector('[data-shape="hub"] .ux-queue-panel').insertAdjacentHTML('beforeend', '<p class="ux-more">View all</p>');
        const hub = document.querySelector('[data-shape="hub"]'), blocks = [...hub.querySelectorAll(':scope > [data-level] > *')].filter(e => !e.closest('.ux-drawer, [data-ia-drawers]') && getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().height > 0).length;
        const built = document.querySelectorAll('.ux-overview .ux-queue>li').length, shown = [...document.querySelectorAll('.ux-overview .ux-queue>li')].filter(e => e.offsetParent !== null).length + (built ? '' : '') + ' of ' + built + ' / ' + ([...document.querySelectorAll('.ux-overview .ux-more')].some(e => e.offsetParent) ? 'link' : 'no link');
        return { blocks, h: Math.round(hub.getBoundingClientRect().height), shown }; }, PLANT);
      if (PLANT === 'viewall') ok(/^(\d+) of \1 \/ no link$/.test(r.shown), `plant viewall: ${op} phone overview: every capped row on screen, no "View all" (${r.shown})`);
      else ok(r.blocks <= 6 && r.h <= 2500, `plant ${PLANT}: ${op} overview budget: ${r.blocks} blocks, ${r.h} px at 1440`);
      await p.context().close(); }
    await b.close(); console.log(out.join('\n')); process.exit(out.some(l => l.startsWith('FAIL')) ? 1 : 0); }
  /* IA-1c r1 (D-IA.36): an in-page link scrolls on the page it is on; Metro's no-recommendation decision, 1440 and 390 */
  const anchorTest = async () => { for (const w of [1440, 390]) { const p = await page('decision/ruiru-connector', { op: 'metro', q: '?state=no-recommendation', w, h: w === 390 ? 844 : 900 });
      if (PLANT === 'anchor') await p.evaluate(() => { iaInPage = () => false; });
      if (PLANT === 'stickyh') await p.evaluate(() => { (0, eval)('iaInPage = ' + iaInPage.toString().replace('${hh}px', '0px')); }); /* D-IA.42: --ia-sticky-h forced to 0px; the section heading then lies under the sticky bar */
      const before = await p.evaluate(() => location.hash.split('?')[0]);
      await p.locator('#app a', { hasText: 'See the options' }).first().click(); await p.waitForTimeout(700);
      const r = await p.evaluate(() => { const h = document.querySelector('#app h1'), sec = document.getElementById('uxcards-ruiru-connector'), h2 = sec && sec.querySelector('h2'), sb = document.querySelector('.ux-dsticky.is-on'), sbBottom = sb && sb.getBoundingClientRect().top < innerHeight / 2 ? sb.getBoundingClientRect().bottom : 0, t = h2 ? h2.getBoundingClientRect().top : -1;
        return { path: location.hash.split('?')[0], h1: h ? h.textContent.trim() : '', nf: /Page not found/.test(document.getElementById('ia-root').innerText), focus: document.activeElement && document.activeElement.id, top: t, sbBottom, inView: t >= 0 && t < innerHeight, below: t >= sbBottom - 1 }; });
      ok(r.path === before && r.path === '#/decision/ruiru-connector' && !r.nf && r.h1 !== 'Page not found' && r.focus === 'uxcards-ruiru-connector' && r.below && r.inView, `in-page link at ${w}: "See the options" stays on #/decision/ruiru-connector (${r.path}), H1 "${r.h1.slice(0, 40)}", focus on ${r.focus || 'nothing'}, options heading at ${Math.round(r.top)} px (sticky bar bottom ${Math.round(r.sbBottom)}), not-found ${r.nf}`);
      await p.context().close(); } };
  if (PLANT === 'anchor' || PLANT === 'stickyh') { await anchorTest(); await b.close(); console.log(out.join('\n')); process.exit(out.some(l => l.startsWith('FAIL')) ? 1 : 0); }
  await anchorTest(); if (process.env.UXI_ONLY === 'anchor') { await b.close(); console.log(out.join('\n')); process.exit(out.some(l => l.startsWith('FAIL')) ? 1 : 0); }
  // 1 drawers on the Overview: open, focus, trap (every press, D-IA.31), Esc, return focus; all three operators
  for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', { op });
    for (const k of ['grow', 'optimize', 'protect', 'assure']) {
      const sel = `[data-ux-drawer="uxd-${op}-${k}"]`; await p.click(sel); await p.waitForTimeout(250);
      const st = await p.evaluate(([op, k]) => ({ open: document.getElementById(`uxd-${op}-${k}`).dataset.open, focus: document.activeElement.classList.contains('ux-x'), card: !!document.querySelector(`#uxd-${op}-${k} .ocard[data-heading="${k}"]`) }), [op, k]);
      const leak = await walk(p, `#uxd-${op}-${k}`);
      await p.keyboard.press('Escape'); await p.waitForTimeout(250);
      const back = await p.evaluate(sel => document.activeElement === document.querySelector(sel) && document.querySelector('.ux-drawer[data-open="true"]') === null, sel);
      ok(st.open === 'true' && st.focus && st.card && !leak && back, `${op} overview drawer ${k}: opens with its card, focus on Close, every Tab and Shift+Tab stays inside${leak ? ` (${leak})` : ''}, Esc closes and returns focus`);
    }
    await p.context().close(); }
  // D-IA.31 sweep: every visible drawer opener of the hub, one per drawer id, the same walk, then Escape returns focus to the opener
  for (const op of ['lakeside', 'harvest', 'metro']) { const first = await (async () => { const q = await page('portfolio', { op }); const k = await q.evaluate(op => OPS[op].sites[0], op); await q.context().close(); return k; })();
    let total = 0;
    for (const r of ['portfolio', 'portfolio/outcomes', 'portfolio/demand-and-capacity', `site/${first}`]) { const p = await page(r, { op });
      const ids = await p.evaluate(() => { const seen = new Set(), out = []; document.querySelectorAll('#app [data-ux-drawer]').forEach(e => { const id = e.dataset.uxDrawer; if (seen.has(id) || !e.getClientRects().length || e.closest('details:not([open]) > :not(summary)')) return; seen.add(id); e.setAttribute('data-gx-sweep', out.length); out.push(id); }); return out; });
      let leak = null;
      for (let i = 0; i < ids.length && !leak; i++) { const sel = `[data-gx-sweep="${i}"]`; await p.click(sel); await p.waitForTimeout(250);
        const w = await walk(p, `#${ids[i]}`); if (w) { leak = `${ids[i]}: ${w}`; break; }
        await p.keyboard.press('Escape'); await p.waitForTimeout(200);
        const back = await p.evaluate(sel => document.activeElement === document.querySelector(sel), sel); if (!back) leak = `${ids[i]}: Escape did not return focus to its opener`; }
      total += ids.length; ok(!leak, `drawer trap sweep: ${op} #/${r}: ${ids.length} drawer${ids.length === 1 ? '' : 's'}${leak ? `; first leak ${leak}` : ' hold'}`); await p.context().close(); }
    ok(total > 0, `drawer trap sweep: ${op}: ${total} drawers measured across the four routes (a sweep that finds none proves nothing)`); }
  // D-IA.31 the class: the last link unlinked and a closed disclosure last; the walk stays inside, and Shift+Tab from Close lands on that summary
  { const p = await page('portfolio'); const u = await unlinkedLast(p); ok(!u.leak && u.onSummary, `drawer trap unlinked last: ${u.leak || (u.onSummary ? 'the walk holds and Shift+Tab from Close lands on the last summary' : 'Shift+Tab from Close does not land on the last summary')}`); await p.context().close(); }
  { const p = await page('portfolio');
    // 2 table views
    for (const t of ['Show as table, by Site']) {
      const s = p.locator('summary', { hasText: t }).first(); await s.click(); await p.waitForTimeout(150);
      const shown = await p.evaluate(t => { const d = [...document.querySelectorAll('details.ux-tableview')].find(x => x.querySelector('summary').textContent.includes(t)); return d.open && d.querySelector('.ux-tableview-body').getBoundingClientRect().height > 50; }, t);
      ok(shown, `overview "${t}" opens its table view`);
    }    { const pd = await page('portfolio/demand-and-capacity'); await pd.locator('summary', { hasText: 'Show the stages in detail' }).first().click(); await pd.waitForTimeout(150);
      ok(await pd.evaluate(() => { const d = [...document.querySelectorAll('details.ux-tableview')].find(x => x.querySelector('summary').textContent.includes('Show the stages in detail')); return d.open && d.querySelector('.ux-tableview-body').getBoundingClientRect().height > 50; }), 'Demand and capacity: "Show the stages in detail" opens its table view'); await pd.context().close(); }

    // 4 keyboard focus visible
    await p.goto(base + '#/portfolio'); await p.waitForTimeout(400); await p.keyboard.press('Tab');
    let seen = 0, visible = 0; for (let i = 0; i < 25; i++) { await p.keyboard.press('Tab'); const f = await p.evaluate(() => { const e = document.activeElement, c = getComputedStyle(e); return { ok: e !== document.body, vis: c.outlineStyle !== 'none' && parseFloat(c.outlineWidth) >= 2 || c.boxShadow !== 'none' }; }); if (f.ok) { seen++; if (f.vis) visible++; } }
    ok(seen >= 20 && visible === seen, `overview keyboard: ${visible} of ${seen} focused elements show a visible focus indicator`);
    ok(!p._errs.length, 'overview: no page errors'); await p.context().close(); }
  // decision page: the option Details drawers, chosen state
  { const p = await page('decision/kobo-generator'); await openAll(p); await p.waitForTimeout(100);
    const ids = await p.evaluate(() => [...document.querySelectorAll('[data-ux-drawer^="uxo-"]')].map(e => e.dataset.uxDrawer));
    let good = 0; for (const id of ids) { await p.click(`[data-ux-drawer="${id}"]`); await p.waitForTimeout(200); const s = await p.evaluate(id => { const d = document.getElementById(id); return d.dataset.open === 'true' && !!d.querySelector('.ux-obl') && !!d.querySelector('[data-heading],.muted'); }, id); await p.keyboard.press('Escape'); await p.waitForTimeout(150); if (s) good++; }
    ok(ids.length === 4 && good === ids.length, `decision: ${good} of ${ids.length} option Details drawers open with limits and effects`);
    const chosen = await p.evaluate(() => /Released/.test(document.querySelector('.ux-dmeta .status-pill').textContent) && !document.querySelector('[data-ux-drawer^="uxc-"]'));
    ok(chosen, 'decision: a released item shows its state in the header, and no Choose button');
    await p.context().close(); }
  // 3 phone Section menu
  { const p = await page('portfolio', { w: 390, h: 844 });
    /* IA-1b: the Portfolio has three tabs, so uxTabs draws the row itself (the Section menu is for more than four); the row fits and navigates */
    const vis = await p.evaluate(() => { const t = document.querySelector('#ia-root .tabs'); return !!t && !document.querySelector('#ia-root .ux-tabmenu') && t.offsetParent !== null && t.scrollWidth <= t.clientWidth + 1; });
    await p.click('#ia-root .tabs a[href="#/portfolio/outcomes"]'); await p.waitForTimeout(400);
    const at = await p.evaluate(() => location.hash);
    ok(vis && at === '#/portfolio/outcomes', 'phone: the three Portfolio tabs fit on one row and navigate');
    await p.goto(base + '#/portfolio'); await p.waitForTimeout(400);
    const shown = await p.evaluate(() => { const li = [...document.querySelectorAll('.ux-overview .ux-queue>li')]; return li.filter(e => e.offsetParent !== null).length + ' of ' + li.length + ' / ' + ([...document.querySelectorAll('.ux-overview .ux-more')].some(e => e.offsetParent) ? 'link' : 'no link'); });
    ok(/^(\d+) of \1 \/ no link$/.test(shown), `phone overview: every capped row on screen (D-IA.34, M4), no "View all" until IA-2b (${shown})`);
    const opt = await (async () => { await p.goto(base + '#/decision/kobo-generator'); await p.waitForTimeout(400); await openAll(p); await p.waitForTimeout(100); return p.evaluate(() => { const tr = document.querySelector('table.ux-opts tbody tr'); return getComputedStyle(tr).display === 'block' && document.documentElement.scrollWidth <= innerWidth; }); })();
    ok(opt, 'phone decision: options as stacked cards, no sideways page scroll');
    await p.context().close(); }
  // phone option cards: every value starts in the same column, right of the labels (catches content wrapping into the label column)
  { const p = await page('decision/kobo-generator', { w: 390, h: 844 }); await openAll(p); await p.waitForTimeout(100);
    const r = await p.evaluate(() => { const bad = []; let cards = 0;
      for (const tr of document.querySelectorAll('table.ux-opts tbody tr')) { cards++; const xs = [];
        for (const td of tr.querySelectorAll('td')) { const cell = td.querySelector(':scope>.ux-cell'), tl = td.getBoundingClientRect().left;
          if (!cell || td.children.length !== 1) { bad.push('cell not wrapped'); continue; }
          const x = cell.getBoundingClientRect().left; xs.push(x);
          if (x < tl + 90) bad.push(`value inside the label column (${Math.round(x - tl)} px)`);
          for (const e of cell.querySelectorAll('*')) { if (e.closest('.ux-drawer')) continue; const r = e.getBoundingClientRect(); if (r.width && r.left < x - 1) bad.push('child left of its value column'); } }
        if (xs.length && Math.max(...xs) - Math.min(...xs) > 1) bad.push('value columns differ within a card'); }
      return { cards, bad: [...new Set(bad)] }; });
    ok(r.cards === 4 && !r.bad.length, `phone decision cards: label and value columns consistent in ${r.cards} cards (${r.bad.join('; ') || 'no fault'})`);
    await p.context().close(); }
  // phone: no chip or pill extends past its card (copy review round 4)
  for (const [op, r] of [['lakeside', 'decision/kobo-generator'], ['lakeside', 'decision/kisiwa-genset'], ['lakeside', 'decision/mto-inverter'], ['harvest', 'decision/mwea-occupancy'], ['lakeside', 'portfolio'], ['lakeside', 'site/kobo'], ['lakeside', 'plan']]) {
    const p = await page(r, { w: 390, h: 844, op });
    const bad = await p.evaluate(() => { const out = [];
      for (const e of document.querySelectorAll('#app .canvas .badge, #app .canvas .status-pill, #app .canvas .ux-chip, #app .canvas .ux-mark, #app .canvas .ec')) {
        if (e.offsetParent === null || e.closest('.ux-drawer')) continue; let sc = false; for (let x = e.parentElement; x && !sc; x = x.parentElement) { const ov = getComputedStyle(x).overflowX; sc = (ov === 'auto' || ov === 'scroll') && x.scrollWidth > x.clientWidth; } if (sc) continue; /* inside a table that scrolls in its own frame: reachable, not clipped */ const card = e.closest('table.ux-opts tr, li, .ux-kpi, .panel, .ux-cat'); if (!card) continue;
        const a = e.getBoundingClientRect(), c = card.getBoundingClientRect(); if (a.width && (a.right > c.right + 1 || a.right > innerWidth)) out.push(`${e.textContent.trim().slice(0, 30)} (${Math.round(a.right)} > ${Math.round(c.right)})`); }
      return out; });
    ok(!bad.length, `${op} ${r} at 390: chips and pills inside their cards (${bad.slice(0, 3).join('; ') || 'none past'})`); await p.context().close(); }
  // wave 2: the queue's Why, filters, sort and group (Metro: 3 Sites)
  { const p = await page('portfolio', { op: 'metro' });
    await p.click('.ux-queue>li.ux-q .ux-q-more'); await p.waitForTimeout(100);
    const why = await p.evaluate(() => { const b = document.querySelector('.ux-queue>li.ux-q .ux-q-more'), t = document.getElementById(b.getAttribute('aria-controls')); return b.getAttribute('aria-expanded') === 'true' && t.offsetParent !== null && t.textContent.length > 20; });
    ok(why, 'queue: Why expands the explanation (aria-expanded)');
    await p.fill('.ux-overview [data-qf="site"]', 'Emb'); await p.waitForTimeout(100);
    const f = await p.evaluate(() => { const li = [...document.querySelectorAll('.ux-overview .ux-queue>li.ux-q')].filter(x => !x.hidden); return { n: li.length, all: li.every(x => x.dataset.site === 'embakasi'), count: document.querySelector('.ux-overview .ux-qcount').textContent }; });
    ok(f.n > 0 && f.all && /^\d+ of \d+$/.test(f.count), `queue filter by Site: ${f.n} Embakasi rows only (${f.count})`);
    await p.fill('.ux-overview [data-qf="site"]', ''); await p.selectOption('.ux-overview [data-qs]', 'due'); await p.waitForTimeout(100);
    const due = await p.evaluate(() => [...document.querySelectorAll('.ux-overview .ux-queue>li.ux-q')].map(x => x.dataset.due || '9999'));
    ok(due.every((d, i) => i === 0 || due[i - 1] <= d), `queue sort by due date: ${due.join(', ')}`);
    await p.selectOption('.ux-overview [data-qg]', 'site'); await p.waitForTimeout(100);
    const g = await p.evaluate(() => ({ heads: [...document.querySelectorAll('.ux-overview .ux-queue>li.ux-grp h3')].map(h => h.textContent.trim()), sites: new Set([...document.querySelectorAll('.ux-overview .ux-queue>li.ux-q')].map(x => x.dataset.site)).size }));
    ok(g.heads.length === g.sites && g.sites > 1, `queue group by Site: ${g.heads.join(' | ')}`);
    await p.context().close(); }
  // wave 2b: one row per decision (counts are decisions); urgency grouping; compact mode; the scope switcher filters as you type
  for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', { op });
    const r = await p.evaluate(() => { const li = [...document.querySelectorAll('.ux-overview .ux-queue>li.ux-q')], titles = li.map(x => x.querySelector('.ux-q-title').textContent), cnt = +document.querySelector('#uxq-h .ux-count').textContent; return { dup: titles.length - new Set(titles).size, n: li.length, cnt, multi: li.filter(x => x.querySelectorAll('.ux-chip').length > 1).length }; });
    ok(r.dup === 0 && r.n <= r.cnt && r.cnt === new Set(await p.evaluate(() => ATTN[LS.op].map(x => x[4]))).size, `${op} queue: one row per decision (${r.n} rows, count ${r.cnt}, ${r.multi} with more than one issue, no duplicate titles)`);
    await p.context().close(); }
  { const p = await page('portfolio', { op: 'metro' });
    await p.selectOption('.ux-overview [data-qg]', 'urg'); await p.waitForTimeout(100);
    const g = await p.evaluate(() => [...document.querySelectorAll('.ux-overview .ux-queue>li.ux-grp h3')].map(h => h.textContent.trim()));
    ok(g.length >= 1 && g.every(t => /^(Due this week|Due this month|Due later|No deadline)/.test(t)), `queue group by urgency: ${g.join(' | ')}`);
    await p.check('.ux-overview [data-qd]'); await p.waitForTimeout(100);
    ok(await p.evaluate(() => document.querySelector('.ux-overview .ux-queue-wrap').classList.contains('is-dense')), 'queue compact mode on');
    await p.click('.ux-scope-sw>summary'); await p.fill('.ux-sw-q', 'emb'); await p.waitForTimeout(100);
    const sw = await p.evaluate(() => [...document.querySelectorAll('.ux-scope-sw a[role="menuitem"]')].filter(a => !a.hidden).map(a => a.textContent));
    ok(sw.length === 1 && /Embakasi/.test(sw[0]), `scope switcher type-ahead: "emb" leaves ${sw.join(', ')}`);
    await p.context().close(); }
  // no queue cell overlaps its neighbour (review 2b M1), at 1280 and 1440, on the three Portfolios, Act first and the Kobo site
  for (const [op, r] of [['lakeside', 'portfolio'], ['harvest', 'portfolio'], ['metro', 'portfolio'], ['lakeside', 'portfolio/act-first'], ['lakeside', 'site/kobo']]) for (const w of [1280, 1440]) {
    const p = await page(r, { op, w, h: 900 });
    const bad = await p.evaluate(() => { const out = [];
      for (const li of document.querySelectorAll('.ux-queue>li.ux-q')) { const cells = [...li.children].filter(c => c.offsetParent !== null && c.getBoundingClientRect().width > 2); /* a 1 px screen-reader-only cell is not a visible cell */
        for (const c of cells) { if (c.scrollWidth > c.clientWidth + 1) out.push(`${c.className} overflows (${c.scrollWidth} > ${c.clientWidth})`);
          for (const e of c.querySelectorAll('*')) { const a = e.getBoundingClientRect(), b = c.getBoundingClientRect(); if (a.width && a.right > b.right + 1) { out.push(`${c.className}: "${e.textContent.trim().slice(0, 24)}" past its cell`); break; } } }
        for (let i = 1; i < cells.length; i++) { const a = cells[i - 1].getBoundingClientRect(), b = cells[i].getBoundingClientRect(); if (Math.abs(a.top - b.top) < 4 && a.right > b.left + 1) out.push(`${cells[i - 1].className} overlaps ${cells[i].className}`); } }
      return [...new Set(out)]; });
    ok(!bad.length, `${op} ${r} at ${w}: no queue cell overlaps its neighbour (${bad.slice(0, 2).join('; ') || 'none'})`); await p.context().close(); }
  // wave 2: the provenance popover, the command search, the scope switcher, the period menu
  { const p = await page('portfolio');
    await p.click('.ux-prov>summary'); await p.waitForTimeout(100);
    const pv = await p.evaluate(() => { const d = document.querySelector('.ux-prov'); return d.open && /Simulated figures come from a simulation of a declared season/.test(d.textContent) && d.querySelector('.ux-pop-menu').offsetParent !== null; });
    await p.keyboard.press('Escape'); await p.waitForTimeout(100);
    const pc = await p.evaluate(() => !document.querySelector('.ux-prov').open && document.activeElement === document.querySelector('.ux-prov>summary'));
    ok(pv && pc, 'provenance: About these figures opens with the Simulated meaning; Esc closes it and returns focus');
    await paletteTest(p);
    await p.click('.topbar [data-index]'); await p.waitForTimeout(150);
    const op2 = await p.evaluate(() => document.getElementById('ux-cmd').dataset.open === 'true');
    await p.keyboard.press('Escape'); await p.waitForTimeout(100);
    const cl = await p.evaluate(() => document.getElementById('ux-cmd').dataset.open === 'false');
    ok(op2 && cl, 'command search: the top bar search opens it; Esc closes it');
    await p.goto(base + '#/portfolio'); await p.waitForTimeout(400);
    await p.click('.ux-scope-sw>summary'); await p.click('.ux-scope-sw a[href="#/site/kobo"]'); await p.waitForTimeout(400);
    ok(await p.evaluate(() => location.hash === '#/site/kobo' && /Kobo/.test(document.querySelector('.ux-scope-sw>summary').textContent)), 'scope switcher: opens a Site and names it');
    await p.click('.ux-period>summary'); await p.waitForTimeout(100);
    ok(await p.evaluate(() => { const d = document.querySelector('.ux-period'), hasHist = !!(typeof DERIVED !== 'undefined' && DERIVED.history); return d.open && !!d.querySelector('.period-chip') && (hasHist ? /September 2026/.test(d.textContent) && !/September 2026\s*not available yet/.test(d.textContent) : /not available yet/.test(d.textContent)); }), 'period menu: the current period; earlier periods listed when history is loaded, otherwise "not available yet"');
    await p.context().close(); }
  // wave 2: the bridge links each step to its decision, with detail on focus; the value chain draws its losses; tiles have a visual
  for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', { op });
    const a = await p.$('.ux-wf-a'); let tip = false;
    if (a) { await a.focus(); await p.waitForTimeout(200); tip = await p.evaluate(() => { const t = document.activeElement.parentElement.querySelector('.ux-tip'); return +getComputedStyle(t).opacity > 0.9 && getComputedStyle(t).visibility === 'visible'; }); }
    /* one drill-down grammar (guide §8; owner, 20 Nov): every chart step, chart heading and outcome tile opens a drawer in place and
       never changes the route; a driver drawer says what is being done ("Open decision →" or "No decision yet"); the Grow and
       Optimize tiles open the same drawer as their chart group; no direct decision link sits on the chart or the tiles */
    const marks = await p.evaluate(() => [...document.querySelectorAll('.ux-hero .ux-wf-a, .ux-hero .ux-wf-gbtn, .ux-cats .ux-cat-go')].map((e, i) => { e.setAttribute('data-gx', i); return { i, d: e.dataset.uxDrawer || null }; }));
    const bad = []; const h0 = await p.evaluate(() => location.hash);
    for (const m of marks) { if (!m.d) { bad.push(`mark ${m.i} opens no drawer`); continue; }
      await p.click(`[data-gx="${m.i}"]`); await p.waitForTimeout(220);
      const r = await p.evaluate(id => { const tx = window.__tx, d = document.getElementById(id); const t = d ? d.textContent : ''; return { open: d && d.dataset.open === 'true', hash: location.hash, drv: /^uxdrv-/.test(id), done: /What is being done/.test(t) && (d.querySelector('a[href^="#/decision/"]') ? /Open decision →/.test(t)     : tx && d.querySelector('.ia-unlinked[data-ia-to^="decision/"]') ? /Open decision/.test(t) : /No decision yet/.test(t)) }; /* IA-1b: until IA-1c lands decisions, iaUnlink names them as text (D-IA.35 L2: only then) */ }, m.d);
      if (!r.open) bad.push(`${m.d} did not open`); if (r.hash !== h0) bad.push(`${m.d} navigated to ${r.hash}`); if (r.drv && !r.done) bad.push(`${m.d} does not say what is being done`);
      await p.keyboard.press('Escape'); await p.waitForTimeout(150); }
    const same = await p.evaluate(() => ['grow', 'optimize'].every(k => { const g = document.querySelector(`.ux-hero .ux-wf-gbtn[data-ux-drawer$="-${k}"]`), t = document.querySelector(`.ux-cat[data-tile="${k}"] .ux-cat-go`); return !g || (t && t.dataset.uxDrawer === g.dataset.uxDrawer); }));
    const direct = await p.evaluate(() => [...document.querySelectorAll('.ux-hero a[href], .ux-cats a[href]')].filter(a => !a.closest('.ux-drawer')).length);
    ok(marks.length >= 4 && !bad.length && same && !direct, `${op} drill-down: ${marks.length} chart steps, headings and tiles each open a drawer in place, none navigates; Grow and Optimize tiles share their chart group's drawer; ${direct} direct links on the chart or tiles (${bad.slice(0, 3).join('; ') || 'all hold'})`);
    const pd = await page('portfolio/demand-and-capacity', { op }); const vc = await pd.evaluate(() => [...document.querySelectorAll('.ux-vc-loss .ux-vc-bar')].filter(b => b.getBoundingClientRect().width > 1).length);
    const tiles = await p.evaluate(() => [...document.querySelectorAll('.ux-cat')].map(t => !!t.querySelector('.ux-bullet, .ux-seg, .ux-meterbar')));
    ok(tip, `${op} bridge: a step shows its detail on focus`);
    /* review H1: every decision that moves a driver is named in its drawer: its Finding sits on the driver, an option's money factors
       include it, or (a service-failure cost line) a Protect Finding at its Site; "No decision yet" only when none does */
    const h1 = await p.evaluate(op => { const M = uxGapModel(op), omf = HC.option_money_factors || {}, svcN = (OPS[op].t.portfolio.service_cost_lines || []).map(l => l.node), bad = [];
      M.groups.forEach(g => g.steps.forEach(s => { const hk = s.st.hkeys || [], sites = Object.keys(s.st.by), nm = sites.map(k => SK[k].name), siteOf = f => String(f.site).replace(/^Room [A-C] · /, '');
        const want = new Set([...DEC.filter(d => sites.includes(d.site) && d.opts.some(x => (omf[x] || []).some(f => hk.includes(f)))).map(d => d.id),
          ...(HC.findings || []).filter(f => nm.includes(siteOf(f)) && (hk.includes(f.factor) || (hk.some(h => svcN.includes(h)) && f.heading === 'protect'))).map(f => f.decision)].filter(Boolean));
        const dr = document.getElementById(s.id), got = new Set([...[...dr.querySelectorAll('a[href^="#/decision/"]')].map(a => a.getAttribute('href').replace('#/decision/', '')), ...(window.__tx ? [...dr.querySelectorAll('.ia-unlinked[data-ia-to^="decision/"]')].map(e => e.dataset.iaTo.replace('decision/', '')) : [])]); /* IA-1b: named as text until IA-1c (D-IA.35 L2) */
        const same = want.size === got.size && [...want].every(x => got.has(x)); if (!same || (!want.size && !/No decision yet/.test(dr.textContent))) bad.push(`${s.lab}: wants ${[...want].join('+') || 'none'}, shows ${[...got].join('+') || 'none'}`); }));
      return bad; }, op);
    ok(!h1.length, `${op} drivers: each drawer names every decision that moves its driver (${h1.join('; ') || 'all hold'})`);
    /* review H2: one share basis; a heading's share is the sum of its steps' shares, the same on the tile, the drawer and the chart */
    const h2 = await p.evaluate(() => { const bad = [], rows = [...document.querySelectorAll('.ux-hero .ux-wf>li')]; let k = null; const sum = {};
      rows.forEach(li => { if (li.classList.contains('ux-wf-group')) { k = li.querySelector('[data-ux-drawer]').dataset.uxDrawer.split('-').pop(); sum[k] = 0; } else { const v = li.querySelector('.ux-wf-val'); if (v && v.dataset.share) sum[k] += +v.dataset.share; } });
      Object.entries(sum).forEach(([k, s]) => { const tile = document.querySelector(`.ux-cat[data-tile="${k}"] [data-heading-share]`), dr = document.querySelector(`[id$="-${k}"].ux-drawer [data-heading-share]`);
        const tv = tile ? +tile.dataset.headingShare : null, dv = dr ? +dr.dataset.headingShare : null; if ((tv !== null && tv !== s) || (dv !== null && dv !== s)) bad.push(`${k}: steps ${s}%, tile ${tv}%, drawer ${dv}%`); });
      return bad; });
    ok(!h2.length, `${op} shares: each heading's share equals the sum of its steps' on the tile, the drawer and the chart (${h2.join('; ') || 'all hold'})`);
    const noLeak = await pd.evaluate(() => /no leak measured/.test(document.querySelector('[id^="uxv-h-"]')?.parentElement?.textContent || '')); await pd.context().close();
    ok(vc >= 1 || noLeak, `${op} value chain: ${vc} loss bars drawn${noLeak ? ' (no leak measured, said in the title)' : ''}`);
    ok(tiles.filter(Boolean).length >= 3, `${op} outcome tiles: ${tiles.filter(Boolean).length} of 4 with a target-against-actual visual`);
    await p.context().close(); }
  // brand packs: the review-bar switch applies a pack; status colours and layout stay; text contrast holds in both packs
  { const p = await page('portfolio');
    const before = await p.evaluate(() => ({ b: document.documentElement.getAttribute('data-brand'), bad: getComputedStyle(document.querySelector('.ux-chip.is-bad')).color, h: document.documentElement.scrollHeight }));
    await p.selectOption('#ux-brand', 'east-africa'); await p.waitForTimeout(200);
    const after = await p.evaluate(() => ({ b: document.documentElement.getAttribute('data-brand'), bad: getComputedStyle(document.querySelector('.ux-chip.is-bad')).color, h: document.documentElement.scrollHeight, band: getComputedStyle(document.querySelector('.topbar'), '::after').backgroundImage !== 'none' }));
    await p.reload(); await p.waitForTimeout(400);
    const kept = await p.evaluate(() => document.documentElement.getAttribute('data-brand'));
    ok(before.b === 'east-africa' && after.b === 'east-africa' && after.band && after.bad === before.bad && kept === 'east-africa', `brand: the demo operators start in East Africa (U10); the switch keeps it, motif band on, status colour unchanged, kept on reload`);
    await p.selectOption('#ux-brand', 'neutral'); await p.waitForTimeout(150);
    const neutral = await p.evaluate(() => ({ none: !document.documentElement.hasAttribute('data-brand'), h: document.documentElement.scrollHeight }));
    ok(neutral.none, 'brand switch: to Neutral, the product default');
    ok(Math.abs(after.h - neutral.h) <= 32, `brand packs: page height East Africa against Neutral within the 32 px budget (${after.h} against ${neutral.h})`);
    await p.context().close(); }
  // wave 2c classes: overview budget; queue alignment, titles, one primary, quiet blanks; the bridge on the gap's scale;
  // modelled weight; prose size; content in its tab; a distinguishable East Africa pack
  /* IA-1b (D-IA.25): a block is a visible direct child of a [data-level] region of the hub, outside .ux-drawer and [data-ia-drawers];
     at most 6, and the hub section at most 2,500 px tall at 1440 */
  for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', { op });
    const r = await p.evaluate(() => {
      const hub = document.querySelector('[data-shape="hub"]'), blocks = hub ? [...hub.querySelectorAll(':scope > [data-level] > *')].filter(e => !e.closest('.ux-drawer, [data-ia-drawers]') && getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().height > 0).length : 99;
      const rows = [...document.querySelectorAll('.ux-overview .ux-queue>li.ux-q')];
      const ragged = rows.filter(li => Math.abs(li.querySelector('.ux-q-title').getBoundingClientRect().left - li.querySelector('.ux-q-top').getBoundingClientRect().left) > 1).length;
      const repeat = rows.filter(li => li.querySelector('.ux-q-title').textContent.trim().toLowerCase().startsWith(li.querySelector('.ux-q-site').textContent.replace('Site: ', '').trim().toLowerCase())).length;
      const prim = document.querySelectorAll('.ux-overview .ux-queue .ux-q-go.primary').length, fc = rows.find(li => li.dataset.state === 'choose'), firstPrim = fc ? (fc.querySelector('.ux-q-go.primary') || (window.__tx && !fc.querySelector('a.ux-q-go') && fc.querySelector('.ia-unlinked[data-ia-to^="decision/"]')) ? 1 : 0) : 1; /* IA-1b (D-IA.25): no primary while decisions are unlanded */
      const vis = el => { const c = el.cloneNode(true); c.querySelectorAll('.vh, .ux-q-k').forEach(x => x.remove()); return c.textContent.trim(); }, blankDue = rows.filter(li => !li.dataset.due).every(li => vis(li.querySelector('.ux-q-due')) === '');
      const brk = document.querySelectorAll('.ux-hero .ux-wf-break').length, steps = [...document.querySelectorAll('.ux-wf-gapscale .ux-wf-bar')].map(b => b.getBoundingClientRect().width / b.parentElement.getBoundingClientRect().width);
      const groups = document.querySelectorAll('.ux-wf-gapscale .ux-wf-group').length, perRowHeading = [...document.querySelectorAll('.ux-wf-gapscale .ux-wf-h')].length;
      const fs = e => parseFloat(getComputedStyle(e).fontSize), mod = document.querySelector('.ux-kpi.is-modelled .ux-kpi-v'), act = document.querySelector('.ux-kpi:not(.is-modelled) .ux-kpi-v');
      const small = [...document.querySelectorAll('.ux-overview .ux-kpi-s:not(:has(.ux-trend)), .ux-overview .ux-q-why, .ux-overview .panel-head p, .ux-overview .ux-q-title')].filter(e => fs(e) < 14).length;
      return { blocks, h: hub ? Math.round(hub.getBoundingClientRect().height) : 99999, ragged, repeat, prim, firstPrim, blankDue, brk, minStep: Math.min(...steps), groups, perRowHeading, modW: mod && act ? fs(mod) < fs(act) && getComputedStyle(mod).color !== getComputedStyle(act).color : false, small, leaks: !!document.querySelector('[id^="uxv-h-"]') };
    });
    ok(r.blocks <= 6 && r.h <= 2500 && !r.leaks, `${op} overview budget: ${r.blocks} blocks, ${r.h} px at 1440, value leaks not here`);
    ok(r.ragged === 0 && r.repeat === 0 && r.prim <= 1 && r.firstPrim === 1 && r.blankDue, `${op} queue: titles aligned (${r.ragged} ragged), no title repeats its Site (${r.repeat}), at most one primary: the first decision waiting for a choice, no "No deadline" noise`);
    ok(r.brk === 0 && r.minStep >= 0.007 && r.groups >= 1 && r.perRowHeading === 0, `${op} bridge: on the gap's scale (no axis break), smallest step ${(r.minStep * 100).toFixed(1)}% of the width, ${r.groups} heading groups, no heading repeated per row`);
    ok(r.modW && r.small === 0, `${op} tiles and text: the modelled tile lighter than actuals; ${r.small} prose elements under 14 px`);
    await p.context().close(); }
  { const pd = await page('portfolio/demand-and-capacity'), po = await page('portfolio/outcomes-by-site');
    ok(await pd.evaluate(() => !!document.querySelector('[id^="uxv-h-"]')) && await po.evaluate(() => !!document.querySelector('.ux-insight')), 'content in its tab: value leaks on Demand and capacity, the insight on Outcomes by site');
    await pd.context().close(); await po.context().close(); }
  { const pn = await page('portfolio'), pe = await page('portfolio');
    await pn.selectOption('#ux-brand', 'neutral'); await pn.waitForTimeout(200); await pe.selectOption('#ux-brand', 'east-africa'); await pe.waitForTimeout(200);
    const a = await pn.evaluate(() => ({ f: getComputedStyle(document.querySelector('.page-heading h1')).fontFamily, band: parseFloat(getComputedStyle(document.querySelector('.topbar'), '::after').height) || 0, tab: getComputedStyle(document.querySelector('.tabs a.active')).color }));
    const b = await pe.evaluate(() => ({ f: getComputedStyle(document.querySelector('.page-heading h1')).fontFamily, band: parseFloat(getComputedStyle(document.querySelector('.topbar'), '::after').height) || 0, tab: getComputedStyle(document.querySelector('.tabs a.active')).color, rail: getComputedStyle(document.querySelector('.rail'), '::before').backgroundImage !== 'none' }));
    ok(a.f !== b.f && b.band >= 10 && a.tab !== b.tab && b.rail, `East Africa distinguishable: heading typeface, ${b.band} px textile band, active-tab colour, rail pattern`);
    await pe.selectOption('#ux-brand', 'neutral'); await pn.context().close(); await pe.context().close(); }
  // wave 2c fix round: every bridge bar inside its track; displayed figures reconcile; empty due cells silent on phone
  for (const op of ['lakeside', 'harvest', 'metro']) for (const w of [1440, 390]) {
    const p = await page('portfolio', { op, w, h: 900 });
    const r = await p.evaluate(() => {
      const out = [];
      for (const b of document.querySelectorAll('.ux-wf-gapscale .ux-wf-bar')) { const t = b.closest('.ux-wf-track').getBoundingClientRect(), a = b.getBoundingClientRect(); if (a.left < t.left - 1 || a.right > t.right + 1) out.push(`bar ${Math.round(a.left - t.left)}..${Math.round(a.right - t.right)} px outside`); }
      const num = t => { const m = String(t).replace(/,/g, '').match(/([+−-]?)\$(\d+)/); return m ? (m[1] === '−' || m[1] === '-' ? -1 : 1) * +m[2] : 0; };
      const ol = document.querySelector('.ux-wf-gapscale'), gap = +ol.dataset.gap; let subSum = 0; const sharesW = [];
      for (const g of ol.querySelectorAll('.ux-wf-group')) { const sub = num(g.querySelector('.ux-wf-gv').textContent); subSum += sub; let n = g.nextElementSibling, s = 0;
        while (n && !n.classList.contains('ux-wf-group')) { const v = n.querySelector('.ux-wf-val'); s += num(v.firstChild.textContent); if (v.dataset.share) sharesW.push(+v.dataset.share); n = n.nextElementSibling; }
        if (s !== sub) out.push(`rows ${s} against subtotal ${sub}`); }
      if (subSum !== gap) out.push(`subtotals ${subSum} against gap ${gap}`);
      if (sharesW.reduce((a, b) => a + b, 0) !== 100) out.push(`shares sum ${sharesW.reduce((a, b) => a + b, 0)}%`);
      const emptyDue = innerWidth < 600 ? [...document.querySelectorAll('.ux-q-due.is-empty')].filter(e => e.getBoundingClientRect().height > 2).length : 0;
      if (emptyDue) out.push(`${emptyDue} empty due lines visible`);
      return out; });
    ok(!r.length, `${op} at ${w}: bridge bars inside their track, rows sum to subtotals and the gap, shares 100%, no empty due line (${r.slice(0, 3).join('; ') || 'all hold'})`);
    await p.context().close(); }
  // on-request recalculation (owner Q7): the control is keyboard reachable and turns the notice to an honest, neutral request line
  { const p = await page('portfolio', { op: 'harvest' });
    const has = await p.evaluate(() => !!document.querySelector('.ux-pending [data-ux-recalc]') && /Recalculation pending/.test(document.querySelector('.ux-pending .snap-pending').textContent));
    let reached = false; for (let i = 0; i < 40 && !reached; i++) { await p.keyboard.press('Tab'); reached = await p.evaluate(() => document.activeElement?.hasAttribute('data-ux-recalc')); }
    if (reached) { await p.keyboard.press('Enter'); await p.waitForTimeout(150); }
    const after = await p.evaluate(() => { const t = document.querySelector('.ux-pending .snap-pending'); return { txt: t.textContent, status: t.getAttribute('role'), btn: !!document.querySelector('[data-ux-recalc]') }; });
    const hasRecalc = await p.evaluate(() => !!(typeof DERIVED !== 'undefined' && DERIVED.recalc)); /* r2 L1: the whole assertion branches on the data */
    ok(has && reached && (hasRecalc ? /^Recalculated at \d{2}:\d{2}, 6 Nov by Operator executive/.test(after.txt.trim()) : /^Recalculation requested at \d{2}:\d{2}, 6 Nov by Operator executive/.test(after.txt.trim()) && /This demo holds no recalculated values, so the figures still show 06:00\./.test(after.txt) && !/^Recalculated|Figures updated/.test(after.txt.trim())) && !/green/.test(await p.evaluate(() => document.querySelector('.ux-pending .snap-pending .badge').className)) && /as of 06:00/.test(await p.evaluate(() => document.querySelector('.topbar').textContent)) && after.status === 'status' && !after.btn, `Recalculate now: reachable by keyboard, the notice reads "${after.txt.trim().slice(0, 70)}…"`);
    await p.context().close(); }
  // the Decision page (owner, 20 Nov; REVIEW-decision-page r1): the question is the title, one primary, state-aware queue buttons,
  // the status line follows the real path, one Recommended, each figure with its own basis, the confirmation states the design's rules
  const STATE_BTN = { choose: 'Decide', approval: 'Awaiting approval', released: 'Review', none: 'Review' };
  for (const op of ['lakeside', 'harvest', 'metro']) {
    const p = await page('portfolio/act-first', { op });
    const rows = await p.evaluate(() => [...document.querySelectorAll('.ux-queue>li.ux-q')].map(li => ({ st: li.dataset.state, btn: li.querySelector('.ux-q-go').childNodes[0].textContent.trim(), href: li.querySelector('.ux-q-go').getAttribute('href') })));
    ok(rows.length && rows.every(r => STATE_BTN[r.st] === r.btn), `${op} queue buttons follow the state: ${rows.map(r => `${r.st}=${r.btn}`).join(', ')}`);
    /* a queue with no decision waiting for a choice has no primary button (the primary check cannot pass trivially) */
    const prim = await p.evaluate(() => ({ n: document.querySelectorAll('.ux-queue .ux-q-go.primary').length, choose: document.querySelectorAll('.ux-queue>li.ux-q[data-state="choose"]').length }));
    ok(prim.choose ? prim.n === 1 : prim.n === 0, `${op} queue: ${prim.n} primary button for ${prim.choose} decision(s) waiting for a choice`);
    const decs = await p.evaluate(op => DEC.filter(d => SK[d.site].op === op).map(d => d.id), op); await p.context().close();
    for (const id of decs) for (const [w, h] of [[1280, 720], [1440, 900], [390, 844]]) {
      const q = await page(`decision/${id}`, { op, w, h });
      const r = await q.evaluate(id => {
        const vis = e => e && e.offsetParent !== null && !e.closest('.ux-drawer') && !e.closest('details:not([open])');
        const h1 = document.querySelector('.page-heading h1'), prims = [...document.querySelectorAll('.canvas .button.primary')].filter(vis).length;
        const rec = document.querySelector('.ux-drec'), recBottom = rec ? Math.round(rec.getBoundingClientRect().bottom + scrollY) : 9999;
        const lis = [...document.querySelectorAll('.ux-dsteps li')].map(li => ({ t: li.textContent.trim(), c: li.className })), grid = !!document.querySelector('.who-decides') && vis(document.querySelector('.who-decides'));
        const cards = document.querySelectorAll('.ux-ocard').length, base = document.querySelectorAll('.ux-ocard.is-base').length;
        /* the path the design gives this decision (decision-loop §6) */
        const d = decById(id), op = SK[d.site].op, st = uxDecState(id), it = deciderOf(id).item, oid = it || uxRec(d), path = oid ? uxReleaseFor(op, oid).path : 'wait', atOnce = st.key === 'released' && releaseOf(op, it).at;
        const want = [st.key === 'none' ? 'No option recommended' : 'Recommended', 'Chosen', ...(atOnce || path === 'at' ? ['Released at once'] : path === 'none' ? ['Actions go ahead'] : ['Awaiting approval', 'Actions released'])];
        const curAt = lis.findIndex(l => /is-current/.test(l.c)), wantCur = st.key === 'released' ? want.length - 1 : st.key === 'approval' ? 2 : 0;
        const stepsOk = lis.map(l => l.t).join('|') === want.join('|') && lis.filter(l => /is-current/.test(l.c)).length === 1 && curAt === wantCur && !(atOnce && lis.some(l => /Awaiting approval/.test(l.t)));
        /* one Recommended: on the cards, and in the table under Why */
        const chips = sel => [...document.querySelectorAll(sel)].filter(e => e.textContent.trim() === 'Recommended').length;
        const oneRec = chips('.ux-ocard header .badge') <= 1 && chips('table.ux-opts td[data-label="Status"] .badge') <= 1;
        const wantBase = decBasis(d) === 'RESTORE_REFERENCE' ? 0 : 1;
        const asks = ['choose', 'none'].includes(st.key), secs = [...document.querySelectorAll('.ux-dsecs > .ux-ans-sec')];
        const secOk = secs.length >= 4 && secs.every(x => (x.querySelector(':scope > summary .ux-ans')?.textContent.trim() || '').length > 8) && !document.querySelector('.ux-dsecs details details.ux-disc');
        const capOk = [...document.querySelectorAll('.canvas ul.list')].filter(u => !u.closest('.ux-drawer')).every(u => [...u.children].filter(li => !li.hidden).length <= 7);
        return { secOk, capOk, nsec: secs.length, wantBase, q: h1 && (asks ? /^What should we do about .+\?$/ : /^[^?]+$/).test(h1.textContent.trim()) && !document.querySelector('.ux-dq') && !document.querySelector('.page-heading h1 + p, .page-heading .title-row + p'), prims, recBottom, stepsOk, steps: lis.map(l => l.t).join(' > '), grid, cards, base, oneRec, mock: /MOCK DEVIATION/.test(document.querySelector('.canvas').textContent), rb: /MOCK DEVIATION D2 · decision page redesign/.test(document.querySelector('.reviewbar').textContent), h: innerHeight };
      }, id);
      ok(r.q && r.secOk && r.capOk && r.prims <= 1 && r.stepsOk && !r.grid && r.cards >= 2 && r.base === r.wantBase && r.oneRec && !r.mock && r.rb && (r.h > 720 || r.recBottom <= 720 || w < 600),
        `${op} ${id} at ${w}: the title is a question only while a choice waits, ${r.nsec} answer-titled sections (one level, lists capped at 7), ${r.prims} primary, status line "${r.steps}" follows the path, process grid not on the page, ${r.cards} option cards with one baseline, one Recommended, review mark in the review bar only${w === 1280 ? `, recommendation ends at ${r.recBottom} px (fold 720)` : ''}`);
      /* context that stays (long-page standard): after scrolling, the sticky bar shows the title, the state and the primary action
         (top at desktop, bottom on phone) and never covers the focused element (WCAG 2.4.11) */
      /* r3 M4: the sticky bar never covers the focused element: walk the whole tab order forwards and backwards with the sections
         open, let each scroll settle, and test 2-D overlap against the bar (review tooling excluded), at 390, 1280 x 720 and 1440 */
      { await q.evaluate(() => { document.querySelectorAll('.ux-dsecs > details').forEach(x => { x.open = true; }); window.scrollTo(0, document.documentElement.scrollHeight); }); await q.waitForTimeout(150);
        const sb = await q.evaluate(() => { const b = document.querySelector('.ux-dsticky'), rc = document.querySelector('.ux-drec').getBoundingClientRect(); if (rc.bottom >= 0) return { short: true }; if (!b || !b.classList.contains('is-on')) return { on: false }; const r = b.getBoundingClientRect();
          return { on: true, top: Math.round(r.top), bottom: Math.round(r.bottom), h: innerHeight, pill: !!b.querySelector('.status-pill'), prim: !!b.querySelector('.button.primary') }; });
        const covered = []; await q.evaluate(() => { window.scrollTo(0, 0); document.activeElement?.blur(); });
        for (const key of [...Array(90).fill('Tab'), ...Array(40).fill('Shift+Tab')]) { await q.keyboard.press(key); await q.waitForTimeout(12);
          const c = await q.evaluate(() => { const b = document.querySelector('.ux-dsticky.is-on'), e = document.activeElement; if (!b || !e || e === document.body || b.contains(e) || e.closest('.reviewbar, .ux-drawer')) return null;
            const r = b.getBoundingClientRect(), f = e.getBoundingClientRect(); if (!f.width || !f.height) return null; const ox = Math.min(r.right, f.right) - Math.max(r.left, f.left), oy = Math.min(r.bottom, f.bottom) - Math.max(r.top, f.top);
            /* a control must not be overlapped at all; a scrolling region taller than half the screen must keep most of its visible part clear (WCAG 2.4.11) */
            const vis = Math.max(0, Math.min(f.bottom, innerHeight) - Math.max(f.top, 0)) * Math.max(0, Math.min(f.right, innerWidth) - Math.max(f.left, 0)), hit = Math.max(0, ox) * Math.max(0, oy);
            const big = f.height > innerHeight / 2; return ox > 0 && oy > 0 && (!big || hit > vis * 0.5) ? (e.textContent || e.getAttribute('aria-label') || e.tagName).trim().slice(0, 40) : null; });
          if (c) covered.push(c); }
        const want = await q.evaluate(id => uxDecState(id).key === 'choose', id);
        ok((sb.short || sb.on && sb.pill && (!want || sb.prim) && (w < 600 ? sb.bottom === sb.h : sb.top <= 1)) && !covered.length, `${op} ${id} at ${w}: ${sb.short ? 'the page fits, so no sticky bar shows' : `the sticky bar keeps the title, state${want ? ' and primary action' : ''} (${w < 600 ? 'bottom' : 'top'})`}; a full focus walk finds ${covered.length ? `it covering "${covered[0]}" (${covered.length} times)` : 'no focused element under it'}`); }
      if (w === 1440) {
        /* each figure carries its own basis: the recommendation's and every card's qualifier equal the options table's (review r1 H1, L8) */
        await openAll(q); await q.waitForTimeout(80);
        const m = await q.evaluate(id => {
          const d = decById(id), rec = uxRec(d), tq = o => { const c = document.querySelector(`table.ux-opts tr[data-opt="${o}"] td:nth-of-type(1) .cellnote`); return c ? c.textContent.trim() : null; }, bad = [];
          const rq = document.querySelector('.ux-drec-q');
          if (rec && (!rq || rq.textContent.trim() !== tq(rec))) bad.push(`recommendation "${rq && rq.textContent.trim()}" vs table "${tq(rec)}"`);
          for (const c of document.querySelectorAll('.ux-ocard:not(.is-base)')) { const o = c.dataset.optCard, cq = c.querySelector('.ux-ocard-q'); if (!cq || cq.textContent.trim() !== tq(o)) bad.push(`${optLabel(o)}: "${cq && cq.textContent.trim()}" vs "${tq(o)}"`); }
          const dv = rec && DV_OPT[rec] && !STUDY(DV_OPT[rec]).days ? (document.querySelector('.ux-drec-n') || {}).textContent.includes(DV_OPT[rec]) : true;
          /* r2 H1: no sentence on the page names a comparator the decision does not use */
          if (decBasis(d) !== 'NO_ACTION' && /against (?:no action|doing nothing)/i.test(document.querySelector('.canvas').textContent)) bad.push(`a typed "against no action" on a ${decBasis(d)} decision`);
          return { bad, dv, n: document.querySelectorAll('.ux-ocard:not(.is-base)').length };
        }, id);
        /* r3 M1-M3: closed answers agree with their rows; do nothing is "the reference" only on a doing-nothing basis; the drawer's release
           rule equals the dialog's */
        const k = await q.evaluate(id => { const d = decById(id), bad = [], ans = l => { const s = [...document.querySelectorAll('.ux-ans-sec')].find(x => x.querySelector('.ux-h2').textContent.trim() === l); return s ? s.querySelector('.ux-ans').textContent : null; };
          const cards = [...document.querySelectorAll('.ux-ocard')], base = cards.find(c => c.classList.contains('is-base')), rec = cards.find(c => c.classList.contains('is-rec')), other = cards.filter(c => c !== base && c !== rec);
          const limOf = c => (c.querySelector('dl > div:nth-child(3) dd')?.textContent || ''), la = ans('Limits and cover') || '';
          const nFail = other.filter(c => /Fails/.test(limOf(c))).length, mF = la.match(/(\d+) (?:other )?options? breaks?/), nUnk = other.filter(c => /Cannot be checked/.test(limOf(c))).length, mU = la.match(/(\d+) cannot be checked/);
          if (la === null) bad.push('no Limits and cover section');
          if (!/No limit applies to these options/.test(la)) { if ((mF ? +mF[1] : 0) !== nFail) bad.push(`Limits says ${mF ? mF[1] : 0} break, the cards show ${nFail}`); if ((mU ? +mU[1] : 0) !== nUnk) bad.push(`Limits says ${mU ? mU[1] : 0} unchecked, the cards show ${nUnk}`);
            if (/doing nothing breaks/.test(la) !== !!(base && /Fails/.test(limOf(base)))) bad.push('Limits and the baseline card disagree');
            if (rec && /keeps every limit/.test(la) && /Fails|Cannot be checked/.test(limOf(rec))) bad.push('the recommendation is said to keep every limit'); }
          const oa = ans('All options in detail') || '', mR = oa.match(/(\d+) rejected or deferred/), nR = cards.filter(c => c !== base && /Rejected|Deferred/.test(c.querySelector('header').textContent)).length;
          if ((mR ? +mR[1] : 0) !== nR) bad.push(`All options says ${mR ? mR[1] : 0} rejected or deferred, the cards show ${nR}`);
          if (decBasis(d) !== 'NO_ACTION' && [...document.querySelectorAll('table.ux-opts tr[data-opt]')].some(tr => isNoAction(tr.dataset.opt) && /The reference/.test(tr.textContent))) bad.push('do nothing called the reference');
          const rel = document.querySelector(`#uxhow-${id} [data-release-text]`), dlg = document.querySelector(`[id^="uxc-${id}-"] .ux-confirm`); if (rel && dlg) { const dd = [...dlg.querySelectorAll('div')].find(x => /^Approval/.test(x.querySelector('dt')?.textContent || ''))?.querySelector('dd')?.textContent.trim(); if (dd && dd !== rel.textContent.trim()) bad.push(`drawer release "${rel.textContent.trim().slice(0, 50)}" differs from the dialog`); }
          return bad; }, id);
        ok(!k.length, `${op} ${id}: closed answers agree with their rows; the reference matches the basis; How this works states the dialog's release rule (${k.join('; ') || 'all hold'})`);
        ok(!m.bad.length && m.dv, `${op} ${id}: the recommendation and ${m.n} card(s) state each figure's own basis, as the options table does${m.dv ? '' : '; the specific estimate note is lost'} (${m.bad.join('; ') || 'all match'})`);
      }
      await q.context().close(); }
  }
  /* the confirmation states the design's rules for every option that can be chosen (decision-loop §6-§8; review r1 H2, M1, M3) */
  { const p = await page('portfolio');
    const R = await p.evaluate(() => {
      const out = [], money = ['COMMERCIAL_CORRECTION'], claim = ['SUPPLIER_REMEDY', 'RIGHTS_REVIEW'];
      for (const d of DEC) { const op = SK[d.site].op; if (uxDecState(d.id).key !== 'choose') continue;
        for (const o of d.opts.filter(o => !isNoAction(o) && uxDisp(o) !== 'REJECTED')) {
          const host = document.createElement('div'); host.innerHTML = uxChooseDialog(d.id, o); const t = host.textContent.replace(/\s+/g, ' ');
          const x = DOPT(o) || {}, spend = x.operator_one_off || 0, crew = x.crew_visits || 0, chooser = ((HC.decisions || []).find(r => r.id === d.id) || {}).chooser;
          const fin = personByRole(op, 'FINANCE_AND_COMMERCIAL_LEAD').name, sm = personByRole(op, 'SITE_MANAGER', SK[d.site].name).name, ex = execOf(op).name, acts = actionsOf(op, o).length;
          const errs = [];
          if (/valued at|No saving claimed over|in the demo data/i.test(t)) errs.push('generic wording');
          if (chooser === 'OPERATOR_EXECUTIVE') { if (!/listed beside the plan/.test(t) || /becomes a plan item|Released when|Released at once/.test(t)) errs.push('expansion not beside the plan, or released'); if (!acts && !/After .*approval/.test(t)) errs.push('expansion Actions not after approval'); if (!acts && new RegExp(`${ex}\\s*creates`).test(t)) errs.push('the executive creates an Action'); }
          else if (!spend && !crew && !['CAPEX', 'DEMAND_CONNECTION'].includes(OPT[o].kind)) { if (!/not a plan item/.test(t) || /becomes a plan item/.test(t)) errs.push('a no-spend option called a plan item'); }
          if (!acts && (claim.includes(OPT[o].kind) || money.includes(OPT[o].kind) || chooser === 'FINANCE_AND_COMMERCIAL_LEAD') && !new RegExp(`${fin}\\s*creates`).test(t)) errs.push(`the finance lead (${fin}) is not named as creator`);
          if (!acts && !claim.includes(OPT[o].kind) && !money.includes(OPT[o].kind) && chooser === 'SITE_MANAGER' && !new RegExp(`${sm}\\s*creates`).test(t)) errs.push(`the Site manager (${sm}) is not named as creator`);
          if (!t.includes(BASIS_LABEL[optBasis(o)]) || !t.includes(uxQual(o))) errs.push('result without its basis');
          out.push(`${o}${errs.length ? ': ' + errs.join(', ') : ''}`); } }
      return out; });
    ok(R.length >= 5 && R.every(s => !s.includes(':')), `confirmation rules for ${R.length} choosable options: plan item only when it spends budget or a crew visit, an expansion beside the plan and after approval, the §8 creator named (${R.filter(s => s.includes(':')).join('; ') || 'all hold'})`);
    await p.context().close(); }
  { const p = await page('decision/mto-billing'); await p.click('.ux-drec [data-ux-drawer^="uxc-"]'); await p.waitForTimeout(250);
    const d = await p.evaluate(() => { const dr = document.querySelector('.ux-drawer[data-open="true"]'); return dr ? { t: dr.textContent, f: document.activeElement.classList.contains('ux-x') } : null; });
    ok(d && /What happens/.test(d.t) && /Actions/.test(d.t) && /Approval/.test(d.t) && /(Released when|Waits for|No approval needed)/.test(d.t) && /Recorded under/.test(d.t) && /Finance and commercial lead/.test(d.t) && d.f, 'Choose this: the confirmation says what happens, the Actions, the approval rule and whose name it is recorded under');
    /* one feedback pattern (UX audit C6): confirm, then a toast with Undo, then a visible state change; Undo restores it */
    await p.click('.ux-drawer[data-open="true"] [data-ux-act-go]'); await p.waitForTimeout(400);
    const c = await p.evaluate(() => ({ open: !!document.querySelector('.ux-drawer[data-open="true"]'), toast: (document.querySelector('.toast') || {}).textContent || '', undo: !!document.querySelector('.toast [data-ux-undo]'), pill: document.querySelector('.ux-dmeta .status-pill')?.textContent || '' }));
    await p.click('.toast [data-ux-undo]'); await p.waitForTimeout(400); const back = await p.evaluate(() => document.querySelector('.ux-dmeta .status-pill')?.textContent || '');
    ok(!c.open && c.undo && /chosen/i.test(c.toast) && /Chosen in this demonstration/.test(c.pill) && /Waiting for a choice/.test(back), `Confirm the choice: toast with Undo, the state changes ("${c.pill}"), Undo restores it ("${back}")`);
    await p.context().close(); }
  /* the fourth state, from its review fixture and the review-bar control (review r1 L2) */
  { const p = await page('decision/kisiwa-om', { op: 'lakeside' });
    const ctl = await p.evaluate(() => { const a = document.querySelector('.reviewbar [data-ux-norec]'); return a ? a.getAttribute('href') : null; });
    let r = null;
    if (ctl) { await p.click('.reviewbar [data-ux-norec]'); await p.waitForTimeout(400);
      r = await p.evaluate(() => ({ pill: document.querySelector('.ux-dmeta .status-pill').textContent.trim(), cur: (document.querySelector('.ux-dsteps li.is-current') || {}).textContent, recChip: [...document.querySelectorAll('.canvas .badge')].some(b => b.textContent.trim() === 'Recommended'), prim: document.querySelectorAll('.canvas .ux-drec .button.primary').length, why: (document.querySelector('.ux-drec .ux-note') || {}).textContent || '', rb: /preview: no option recommended/.test(document.querySelector('.reviewbar').textContent), canvas: /preview|fixture/i.test(document.querySelector('.ux-drec').textContent) })); }
    ok(!!ctl && r && r.pill === 'No option recommended' && r.cur === 'No option recommended' && !r.recChip && r.prim === 0 && /^No option is recommended: of \d+ options?, .+\. .+ can still choose/.test(r.why) && r.rb && !r.canvas,
      `fourth state: the review-bar control opens it; pill and current step say "No option recommended", no Recommended chip, no primary, the reason counts the options ("${r ? r.why.slice(0, 90) : 'control missing'}")`);
    await p.context().close(); }
  // RECON-1 (D-RECON.3): every shared figure carries data-figure, data-scope and data-v; X1 identical across routes, X2 tied where a
  // line and its heading differ, X3 adds up, X4 the demo cases, X5 counts equal their lists, X6 loss colour only against target, X7 words
  { const all = [], bad = [];
    for (const op of ['lakeside', 'harvest', 'metro']) {
      const sites = await (async () => { const p = await page('portfolio', { op }); const s = await p.evaluate(op => OPS[op].sites, op); await p.context().close(); return s; })();
      for (const r of ['portfolio', 'portfolio/outcomes-by-site', 'globalfinancials', 'sites', 'findings', 'actions', ...sites.flatMap(sk => [`site/${sk}`, `site/${sk}/economics`])]) {
        const p = await page(r, { op });
        const res = await p.evaluate(({ r, op }) => {
          const label = (M.home_categories.reconciliation || {}).crossing_label || '', out = { figs: [], bad: [] };
          document.querySelectorAll('.canvas [data-figure]').forEach(e => out.figs.push({ r, f: e.dataset.figure, s: e.dataset.scope, v: +e.dataset.v, t: e.textContent }));
          const by = (f, s) => out.figs.filter(x => x.f === f && x.s === s);
          for (const s of [...new Set(out.figs.map(x => x.s))]) for (const [L, H] of [['revenue_change', 'grow'], ['optimize', 'cost_change']]) {
            const l = by(L, s)[0], h = by(H, s)[0]; if (l && h && Math.abs(l.v - h.v) > 0.005) { const x = by('metered_not_billed', s)[0];
              if (!x || Math.abs(x.v - (L === 'revenue_change' ? l.v - h.v : l.v - h.v)) > 0.01 || !x.t.toLowerCase().includes(label.toLowerCase())) out.bad.push(`X2 ${r} ${s}: ${L} ${l.v} and ${H} ${h.v} differ, with no labelled ${label} line equal to the difference`); } }
          document.querySelectorAll('.canvas [data-count]').forEach(e => { const n = document.querySelectorAll(e.dataset.countOf || '#none').length, capped = /ux-queue/.test(e.dataset.countOf || '') && [...document.querySelectorAll('.ux-queue-panel .ux-qcount')].some(q => +q.dataset.total === +e.dataset.count); /* IA-1b (D-IA.22): the Site queue shows its top 3 and says "3 of 4" */ if (+e.dataset.count !== n && !capped) out.bad.push(`X5 ${r}: count ${e.dataset.count} but ${n} in ${e.dataset.countOf}`); });
          document.querySelectorAll('.canvas .is-bad[data-actual][data-target]').forEach(e => { if (+e.dataset.actual >= +e.dataset.target) out.bad.push(`X6 ${r}: a bar marked as a loss is at or above its target`); });
          if (/(?<!grow )revenue explains/i.test(document.querySelector('.canvas').textContent)) out.bad.push(`X7 ${r}: "revenue explains" labels a Grow figure`); /* r2 M4: any case */
          const qc = document.querySelector('.ux-queue-panel .ux-qcount'), badge = document.querySelector('.ux-queue-panel .ux-count');
          if (qc && badge && +qc.dataset.total !== +badge.textContent.replace(/\D/g, '')) out.bad.push(`X5 ${r}: the queue says "${qc.textContent}" under a count of ${badge.textContent}`); /* r2 M6 */
          return out; }, { r, op });
        all.push(...res.figs.map(f => ({ ...f, op }))); bad.push(...res.bad); await p.context().close(); }
    }
    const key = f => `${f.f}|${f.s}`, seen = {};
    all.forEach(f => { (seen[key(f)] = seen[key(f)] || []).push(f); });
    Object.entries(seen).forEach(([k, fs]) => { const vs = [...new Set(fs.map(f => f.v))]; if (vs.length > 1) bad.push(`X1 ${k} differs: ${fs.map(f => `${f.r} ${f.v}`).join(', ')}`); });
    const val = (f, s) => (seen[`${f}|${s}`] || [])[0]?.v;
    for (const s of [...new Set(all.map(f => f.s))]) { const g = val('grow', s) ?? 0, o = val('optimize', s), gap = val('gap', s); if (o != null && gap != null && Math.abs(g + o - gap) > 0.02) bad.push(`X3 ${s}: grow ${g} + optimize ${o} is not the gap ${gap}`); }
    const has = (op, r, f, s) => all.some(x => x.op === op && x.r === r && x.f === f && x.s === s && Math.abs(x.v) > 0.005);
    if (!has('lakeside', 'portfolio', 'metered_not_billed', 'lakeside') || !has('lakeside', 'globalfinancials', 'metered_not_billed', 'lakeside') || !has('lakeside', 'site/mto/economics', 'metered_not_billed', 'mto')) bad.push('X4 Lakeside does not show the tie on the Portfolio, Financials and Mto economics');
    if (all.some(x => x.op === 'harvest' && x.f === 'metered_not_billed' && Math.abs(x.v) > 0.005)) bad.push('X4 Harvest shows a crossing line');
    if (all.some(x => x.op === 'metro' && ['revenue_change', 'grow'].includes(x.f))) bad.push('X4 Metro shows a revenue or Grow figure');
    ok(all.length > 30 && !bad.length, `RECON-1 X1-X7: ${all.length} tagged figures on ${new Set(all.map(f => f.op + f.r)).size} routes agree, tie, add up and count (${bad.slice(0, 4).join('; ') || 'all hold'})`); }
  { const p = await page('globalfinancials', { op: 'harvest' }); const t = await p.evaluate(() => [...document.querySelectorAll('.canvas table')].map(x => x.textContent).find(x => /Statement line/.test(x)) || '');
    ok(/none this month/.test(t), 'X4 Harvest Financials: the crossing cell reads "none this month"'); await p.context().close(); }
  /* the Site page (owner, 20 Nov): the same structure on every Site; answer-titled sections; a driver row opens its drawer in
     place and never navigates; counts from one source; the sticky bar; on a phone the KPI trend is words, not a sparkline */
  { const sites = { lakeside: ['kobo', 'kisiwa', 'mto'], harvest: ['mwea', 'thika', 'kirinyaga'], metro: ['embakasi', 'kasarani', 'ruiru'] }, shapes = new Set(), opsAns = new Set();
    for (const [op, sks] of Object.entries(sites)) for (const sk of sks) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) {
      const p = await page(`site/${sk}`, { op, w, h });
      const r = await p.evaluate(() => { const secs = [...document.querySelectorAll('.ux-dsecs > .ux-ans-sec')];
        return { labels: secs.map(s => s.querySelector('.ux-h2').textContent.trim()).filter(l => l !== 'Operations measures').join('|'), ans: secs.every(s => (s.querySelector('.ux-ans')?.textContent.trim() || '').length > 4),
          h1: document.querySelectorAll('h1').length, spark: [...document.querySelectorAll('.ux-kpi .ux-spark')].some(x => x.getBoundingClientRect().width > 0), words: [...document.querySelectorAll('.ux-kpi .ux-trend')].filter(x => x.getBoundingClientRect().height > 0).map(x => x.textContent.trim()),
          ovf: (window.__ovf() || document.documentElement.scrollWidth > innerWidth), marks: [...document.querySelectorAll('.ux-board-go')].map(b => b.dataset.uxDrawer) }; });
      shapes.add(r.labels);
      let nav = 0, drw = 0; const h0 = await p.evaluate(() => location.hash);
      if (w === 1440) for (const id of r.marks.slice(0, 4)) { const found = await p.evaluate(id => { const b = document.querySelector(`[data-ux-drawer="${id}"]`); if (b) b.click(); return !!b; }, id); if (!found) { nav++; continue; } /* r1 L4: a row gone after navigating is a failure, not a crash */ await p.waitForTimeout(150);
        const st = await p.evaluate(id => ({ open: document.getElementById(id)?.dataset.open === 'true', hash: location.hash, done: /What is being done/.test(document.getElementById(id)?.textContent || '') }), id);
        if (st.open && st.done) drw++; if (st.hash !== h0) nav++; await p.keyboard.press('Escape'); await p.waitForTimeout(100); }
      await p.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await p.waitForTimeout(150); const stickyOn = await p.evaluate(() => !!document.querySelector('.ux-dsticky.is-on .status-pill')); await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(100);
      const phoneOk = w >= 600 || (!r.spark && r.words.length >= 1 && r.words.every(x => /against|not available yet/i.test(x))); /* G3: at least one trend, in words */
      /* review Site r1 classes: H1 a trend is the tile's measure; M1 state words; M2 the board adds to the gap */
      const tru = await p.evaluate(sk => { const bad = [], tx = e => (e?.textContent || '').replace(/\s+/g, ' ').trim(), mon = s => { const m = String(s).match(/([+−-])?\$([\d,]+)/); return m ? (m[1] && m[1] !== '+' ? -1 : 1) * +m[2].replace(/,/g, '') : null; };
        const k1 = document.querySelector('.ux-kpis .ux-kpi'); if (/per required departure/.test(tx(k1)) && [...k1.querySelectorAll('.ux-trend')].some(x => /^[+−-]\$/.test(tx(x)) || /^Cost /.test(tx(x)))) bad.push('H1 a per-departure tile carries a signed cost trend');
        const ids = [...new Set(ATTN[SK[sk].op].filter(r => r[2] === sk).map(r => r[4]))], wait = ids.some(id => ['choose', 'none'].includes(uxDecState(id).key)), c = tx(document.querySelector('.canvas'));
        if (!wait && /value if chosen|decisions? open\b|Needs a decision|\d+ open\b/.test(c)) bad.push('M1 "open" or "if chosen" with nothing to choose');
        const cells = [...document.querySelectorAll('[data-board-v]')]; if (cells.length) { const shown = cells.reduce((a, e) => a + mon(e.textContent), 0), gk = [...document.querySelectorAll('.ux-kpis .ux-kpi')].find(k => /^Gap to target/.test(tx(k))), g = mon(tx(gk).replace(/^Gap to target/, '')); if (g !== null && shown !== g) bad.push(`M2 board ${shown} against gap ${g}`); }
        const ops = [...document.querySelectorAll('.ux-ans-sec')].find(x => /Operations measures/.test(tx(x.querySelector('.ux-h2')))); return { bad, ops: ops ? tx(ops.querySelector('.ux-ans')) : null }; }, sk);
      if (tru.ops) opsAns.add(tru.ops); if (tru.ops && !/\d|no operations measure/i.test(tru.ops)) tru.bad.push('M4 Operations answer has no figure');
      ok(!tru.bad.length, `${op} site/${sk} at ${w}: the tile's trend is its own measure, state words match the decisions' states, the board adds to the gap${tru.ops ? ', the Operations answer is its rows' : ''} (${tru.bad.join('; ') || 'all hold'})`);
      const svc = await p.evaluate(() => { const s = [...document.querySelectorAll('.ux-ans-sec')].find(x => /Service and assets/.test(x.querySelector('.ux-h2').textContent)); if (!s) return false; const a = s.querySelector('.ux-ans').textContent, n = (s.innerHTML.match(/Above its target/g) || []).length; const m = a.match(/^(\d+) of/); return m ? +m[1] === n : n === 0; });
      ok(svc && r.ans && r.h1 === 1 && !r.ovf && phoneOk && !nav && stickyOn && (w !== 1440 || drw === Math.min(4, r.marks.length)), `${op} site/${sk} at ${w}${r.ovf ? ` OVERFLOW ${r.ovf}` : ""}: answer-titled sections, sticky context after scroll, one h1, no sideways scroll${w < 600 ? ', KPI trend in words without a sparkline' : ''}${w === 1440 ? `, ${drw} driver rows open their drawers in place` : ''}`);
      await p.context().close(); }
    ok(shapes.size === 1, `Site pages: one section structure for every Site type (${[...shapes].join(' / ')})`);
    ok(opsAns.size > 2, `Site pages: the Operations answers differ with their measures (${opsAns.size} distinct)`); }
  /* the plan page: answer-titled sections, the approver's sticky bar, and Approve / Send back with the one feedback pattern.
     Review r4: H1 the item list never overlaps (cells do not intersect, none is wider than its box, the item cell holds 160 px or the row is a card);
     M1 after Approve nothing on any page still says waiting; M2 Send back returns to Draft; M3 a reason and a trade-off are required and not prefilled;
     M4 the dialog follows the case on screen; M7 focus is never on the page body after an action or an Undo; L2 dialog copy; L3 the vertical's word;
     L4 no phrase said twice in a row; L5 the phone bar does not truncate its pill; L7 a focus walk under the plan's sticky bar */
  const WAIT = /awaiting approval|awaiting [^.]{0,40}approval|waiting for (?:the plan’s )?approval|Chosen · awaiting|Chosen · the plan was sent back/i;
  let IA2 = null; const TABS2 = ['plan/left-out', 'plan/review', 'plan/history'];
  for (const op of ['lakeside', 'harvest', 'metro']) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) {
    const p = await page('plan', { op, w, h }); if (IA2 === null) { IA2 = await p.evaluate(() => IA_LANDED.has('IA-2a')); if (!IA2) out.push('IA-2a not landed; dormant'); }
    /* IA-2a: Left out's answers, and each tab's Approve after scrolling to the end */
    let tabsDesc = '', tabsOk = true;
    if (IA2) { const q = await page('plan/left-out', { op, w, h }), lo = await q.evaluate(() => { const secs = [...document.querySelectorAll('[data-shape="plan"] .ux-ans-sec')]; return { n: secs.length, ans: secs.every(s => (s.querySelector('.ux-ans')?.textContent.trim() || '').length > 4) }; }); await q.context().close();
      const reach = [];
      for (const t of TABS2) { const q2 = await page(t, { op, w, h }); await q2.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await q2.waitForTimeout(150);
        reach.push(await q2.evaluate(t => { const st = !!document.querySelector('.ux-dsticky.is-on [data-ux-act="approve-plan"]'), a = [...document.querySelectorAll('[data-shape="plan"] .ux-planband [data-ux-act="approve-plan"]')].find(e => !e.closest('[data-ux-sticky]')), r = a && a.getBoundingClientRect();
          return { t, how: st ? 'sticky' : r && r.top >= 0 && r.bottom <= innerHeight ? 'band in view' : null }; }, t)); await q2.context().close(); }
      tabsOk = lo.n >= 2 && lo.ans && reach.every(x => x.how);
      tabsDesc = `; Left out ${lo.n} answer-titled sections${lo.ans ? ', each answered' : ', NOT all answered'}; Approve at the end of ${reach.map(x => `${x.t.slice(5)} ${x.how || 'NOT REACHABLE'}`).join(', ')}`; }
    const r = await p.evaluate(() => { const secs = [...document.querySelectorAll('.ux-ans-sec')]; return { n: secs.length, ans: secs.every(s => (s.querySelector('.ux-ans')?.textContent.trim() || '').length > 4), ovf: (window.__ovf() || document.documentElement.scrollWidth > innerWidth), chip: document.querySelector('.ux-planband [data-plan-state]')?.dataset.planState, diff: /Changes since version/.test(document.body.textContent), crew: !!document.querySelector('[data-k="Visits"]') }; });
    /* H1: layout of the item list, measured, with its own proof that the set is not empty */
    const lay = await p.evaluate(PLAN_LAYOUT);
    /* L4 a phrase said twice in a row; L3 the vertical's word */
    const words = await p.evaluate(() => { const rep = []; document.querySelectorAll('summary.ux-itemrow').forEach(s => { const segs = s.innerText.split(/[\n,:;]| · /).map(x => x.replace(/\s+/g, ' ').trim()).filter(x => x.length >= 24); const seen = new Set(); for (const x of segs) { if (seen.has(x)) rep.push(x.slice(0, 40)); seen.add(x); } });
      const t = [...document.querySelectorAll('.ux-h2, th, .ux-itemh span, .ux-kpi-l, [data-k]')].map(e => e.textContent).join(' | '); /* the page's own labels, not the data's prose */ return { rep, crew: /\bcrews?\b/i.test(t), tech: /technician/i.test(t), op: OPS[LS.op].vertical, n: document.querySelectorAll('.ux-h2, th').length }; });
    const wordOk = words.n > 3 && !words.rep.length && (words.op === 'mini' ? !words.tech : !words.crew);
    await p.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await p.waitForTimeout(150);
    const st = await p.evaluate(() => { const b = document.querySelector('.ux-dsticky.is-on'); return { on: !!document.querySelector('.ux-dsticky.is-on [data-plan-state]'), act: !!document.querySelector('.ux-dsticky.is-on [data-ux-act="approve-plan"]'), trunc: b ? [...b.querySelectorAll('.status-pill, .ux-dsticky-t')].filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent.trim().slice(0, 24)) : [] }; });
    /* L7: the focus walk under the plan's sticky bar, forwards and backwards */
    const covered = []; await p.evaluate(() => { window.scrollTo(0, 0); document.activeElement?.blur(); });
    for (const key of [...Array(70).fill('Tab'), ...Array(30).fill('Shift+Tab')]) { await p.keyboard.press(key); await p.waitForTimeout(12);
      const c = await p.evaluate(() => { const b = document.querySelector('.ux-dsticky.is-on'), e = document.activeElement; if (!b || !e || e === document.body || b.contains(e) || e.closest('.reviewbar, .ux-drawer')) return null; const r = b.getBoundingClientRect(), f = e.getBoundingClientRect(); if (!f.width || !f.height) return null;
        const ox = Math.min(r.right, f.right) - Math.max(r.left, f.left), oy = Math.min(r.bottom, f.bottom) - Math.max(r.top, f.top), vis = Math.max(0, Math.min(f.bottom, innerHeight) - Math.max(f.top, 0)) * Math.max(0, Math.min(f.right, innerWidth) - Math.max(f.left, 0)), big = f.height > innerHeight / 2;
        return ox > 0 && oy > 0 && (!big || Math.max(0, ox) * Math.max(0, oy) > vis * 0.5) ? (e.textContent || e.tagName).trim().slice(0, 40) : null; }); if (c) covered.push(c); }
    await p.evaluate(() => window.scrollTo(0, 0));
    /* L1: at a phone width the toast sits above the bar and not over it or the state it reports */
    let toastOk = true; if (w === 390) { await p.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await p.waitForTimeout(150); await p.click('.ux-dsticky.is-on [data-ux-act="approve-plan"]'); await p.waitForTimeout(250); await p.click('#uxact [data-ux-act-go]'); await p.waitForTimeout(400); await p.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await p.waitForTimeout(200);
      toastOk = await p.evaluate(() => { const t = document.querySelector('.ux-toast')?.getBoundingClientRect(), b = document.querySelector('.ux-dsticky.is-on')?.getBoundingClientRect(); return !!t && !!b && t.bottom <= b.top + 1; }); await p.evaluate(() => sessionStorage.removeItem('l4-mock')); await p.reload(); await p.waitForTimeout(300); await prep(p); }
    let flow = true, desc = '';
    if (w === 1440) { const fails = [], ST = () => p.evaluate(() => ({ chip: document.querySelector('.ux-planband [data-plan-state]')?.dataset.planState, undo: !!document.querySelector('.toast [data-ux-undo]'), focus: document.activeElement.tagName, act: document.activeElement.dataset?.uxAct || '' }));
      await p.click('.ux-planband [data-ux-act="approve-plan"]'); await p.waitForTimeout(250);
      /* M4 L2: the dialog says what the screen says, and no stray space before a comma */
      const dlg = await p.evaluate(() => { const d = document.getElementById('uxact'), t = (d?.textContent || '').replace(/\s+/g, ' '), band = (document.querySelector('.ux-planband .ux-kpi-v')?.textContent.match(/\$[\d,]+/) || [''])[0], later = waitingSummary(LS.op, planCaseIds(LS.op)).later.length;
        return { ok: d?.dataset.open === 'true' && /What happens/.test(t) && /Recorded under/.test(t), spend: d?.querySelector('[data-ux-plan-spend]')?.textContent, band, comma: /\s,/.test(t), later: later ? /After approval/.test(t) : true, items: d?.querySelector('[data-ux-plan-items]')?.textContent, shown: document.querySelectorAll('summary.ux-itemrow').length }; });
      if (!dlg.ok) fails.push('the Approve dialog lacks What happens / Recorded under'); if (dlg.spend !== dlg.band) fails.push(`dialog spend ${dlg.spend} against the band ${dlg.band}`); if (dlg.comma) fails.push('a space before a comma in the dialog'); if (!dlg.later) fails.push('the dialog omits the Actions created after approval'); if (+dlg.items !== dlg.shown) fails.push(`dialog items ${dlg.items} against ${dlg.shown} rows`);
      await p.click('#uxact [data-ux-act-go]'); await p.waitForTimeout(400);
      const a = await ST(), left = await p.evaluate(src => ({ waiting: document.querySelectorAll('[data-release="WAITING"]').length, chosen: [...document.querySelectorAll('.ux-state')].filter(e => /Chosen/.test(e.textContent)).length, say: new RegExp(src, 'i').test(document.querySelector('.canvas').textContent) }), WAIT.source);
      if (a.chip !== 'APPROVED' || !a.undo) fails.push(`Approve gives ${a.chip}, toast ${a.undo}`); if (a.focus === 'BODY') fails.push('focus on the page body after Approve (M7)');
      if (left.waiting || left.chosen || left.say) fails.push(`after Approve the plan page still says waiting: ${left.waiting} waiting pills, ${left.chosen} Chosen, "awaiting" text ${left.say} (M1)`);
      await p.click('.toast [data-ux-undo]'); await p.waitForTimeout(400); const b = await ST(); if (b.chip !== 'PROPOSED') fails.push(`Undo gives ${b.chip}`); if (b.focus === 'BODY') fails.push('focus on the page body after Undo (M7)');
      /* M1: every page agrees with the approval */
      await p.click('.ux-planband [data-ux-act="approve-plan"]'); await p.waitForTimeout(250); await p.click('#uxact [data-ux-act-go]'); await p.waitForTimeout(400);
      const dec = { lakeside: 'kisiwa-genset', harvest: 'kirinyaga-energy', metro: 'embakasi-schedule' }[op], routes = ['portfolio', 'portfolio/act-first', 'decisions', 'actions', 'portfolio/what-changed', `decision/${dec}`, 'plan'];
      if (IA2) routes.splice(routes.length - 1, 0, ...TABS2); /* plan stays last: the Send back and case flows below run on it */
      for (const rt of routes) { await p.goto(base + '#/' + rt); await p.waitForTimeout(300); await prep(p); await p.waitForTimeout(100); await actFirst(p, rt);
        const s = await p.evaluate(src => { const k = document.querySelector('.canvas').cloneNode(true); k.querySelectorAll('.ux-dsteps').forEach(x => x.remove()); /* the stage list names its steps */ const t = k.textContent.replace(/\s+/g, ' '), m = t.match(new RegExp('.{0,40}(?:' + src + ').{0,20}', 'i')); return { say: m ? m[0] : '', waiting: document.querySelectorAll('[data-release="WAITING"]').length }; }, WAIT.source);
        if (s.say || s.waiting) fails.push(`${rt} after Approve: "${s.say}" ${s.waiting} waiting pills`);
        if (rt === 'portfolio' && await p.evaluate(() => !!document.querySelector('.ux-toast'))) fails.push('the toast of the plan survives navigation to another page (L1)'); }
      await p.evaluate(() => sessionStorage.removeItem('l4-mock')); await p.reload(); await p.waitForTimeout(400); await prep(p); await p.waitForTimeout(100);
      /* M2 M3: Send back returns to Draft, and needs a reason and a trade-off that the executive wrote */
      await p.click('.ux-planband [data-ux-act="send-back"]'); await p.waitForTimeout(250);
      const sd = () => p.evaluate(() => ({ dis: document.querySelector('#uxact [data-ux-act-go]').disabled, reason: document.getElementById('ux-sb-reason').value, way: document.getElementById('ux-sb-way').value }));
      const s0 = await sd(); if (!s0.dis || s0.reason || s0.way) fails.push(`Send back opens prefilled or enabled (${JSON.stringify(s0)})`);
      await p.fill('#ux-sb-reason', 'Too much spend before the deadline items'); const s1 = await sd(); if (!s1.dis) fails.push('Send back is enabled with a reason and no trade-off');
      await p.selectOption('#ux-sb-way', { index: 1 }); const s2 = await sd(); if (s2.dis) fails.push('Send back stays disabled with a reason and a trade-off');
      await p.fill('#ux-sb-reason', '   '); const s3 = await sd(); if (!s3.dis) fails.push('Send back accepts a blank reason');
      await p.fill('#ux-sb-reason', 'Too much spend before the deadline items'); await p.click('#uxact [data-ux-act-go]'); await p.waitForTimeout(400);
      const sb = await p.evaluate(() => ({ chip: document.querySelector('.ux-planband [data-plan-state]')?.dataset.planState, txt: document.querySelector('.ux-planband').textContent, focus: document.activeElement.tagName, sub: document.querySelector('.page-heading')?.textContent || '' }));
      if (sb.chip !== 'DRAFT' || /Revised/.test(sb.txt + sb.sub)) fails.push(`Send back gives ${sb.chip}, not Draft`); if (!/Too much spend/.test(sb.txt) || !/gives way/.test(sb.txt)) fails.push('the reason and the trade-off are not shown'); if (sb.focus === 'BODY') fails.push('focus on the page body after Send back (M7)');
      await p.click('.toast [data-ux-undo]'); await p.waitForTimeout(300); const c2 = await ST(); if (c2.chip !== 'PROPOSED' || c2.focus === 'BODY') fails.push(`Undo after Send back: ${c2.chip}, focus ${c2.focus}`);
      /* M4: a case that differs from the proposal is approved as the next version, with its own items and spend */
      await p.evaluate(() => { const op = LS.op; if (op === 'lakeside') LS.loi = false; else if (op === 'harvest') LS.agg = false; else LS.tou = false; render(); }); await p.waitForTimeout(300);
      await p.click('.ux-planband [data-ux-act="approve-plan"]'); await p.waitForTimeout(250);
      const nd = await p.evaluate(() => { const d = document.getElementById('uxact'), t = (d?.textContent || '').replace(/\s+/g, ' '), band = (document.querySelector('.ux-planband .ux-kpi-v')?.textContent.match(/\$[\d,]+/) || [''])[0]; return { def: DEFAULT_CASE(LS.op), v2: /makes version 2/.test(t), spend: d?.querySelector('[data-ux-plan-spend]')?.textContent, band, items: d?.querySelector('[data-ux-plan-items]')?.textContent, shown: document.querySelectorAll('summary.ux-itemrow').length }; });
      if (nd.def || !nd.v2 || nd.spend !== nd.band || +nd.items !== nd.shown) fails.push(`a case that differs: default ${nd.def}, makes version 2 ${nd.v2}, spend ${nd.spend} against ${nd.band}, items ${nd.items} against ${nd.shown} rows`);
      flow = !fails.length; desc = `; Approve/Send back/case flows${fails.length ? ` FAIL: ${fails.join(' | ')}` : ': dialog matches the case, every page follows Approve, Send back returns to Draft with a required reason and trade-off, focus stays on the page'}`; }
    const layOk = lay.rows > 0 && !lay.bad.length;
    ok(r.n >= (IA2 ? 2 : 4) && tabsOk && r.ans && !r.ovf && r.chip === 'PROPOSED' && r.diff && (w < 600 || r.crew) && st.on && st.act && flow && toastOk && layOk && wordOk && !st.trunc.length && !covered.length,
      `${op} plan at ${w}: ${r.n} answer-titled sections, changes since the version, visits per item, sticky approver bar${w < 600 ? ` (pill ${st.trunc.length ? 'TRUNCATED ' + st.trunc[0] : 'whole'})` : ''}; ${lay.rows} item rows as ${lay.card ? 'cards' : 'a table'}${layOk ? ', no cell overlaps or overflows (H1)' : ` OVERLAP ${lay.rows ? lay.bad.join('; ') : 'no rows found'}`}${wordOk ? '' : ` WORDS ${words.rep.join('; ')} ${words.op === 'mini' ? (words.tech ? 'technician' : '') : (words.crew ? 'crew' : '')}`}${toastOk ? '' : ' TOAST over the bar'}; a full focus walk finds ${covered.length ? `the bar covering "${covered[0]}" (${covered.length} times)` : 'no focused element under it'}${desc}${tabsDesc}`);
    await p.context().close(); }
  /* review r4 M5: a choice made in the demonstration says the one release rule, the same words as its dialog and How this works */
  { const p = await page('decision/mto-billing', { op: 'lakeside' });
    await p.click('.ux-drec [data-ux-drawer^="uxc-mto-billing-"]'); await p.waitForTimeout(250); await p.click('.ux-drawer[data-open="true"] [data-ux-act-go^="choose:"]'); await p.waitForTimeout(400);
    const r = await p.evaluate(() => { const line = document.querySelector('.ux-dgo span')?.textContent.replace(/\s+/g, ' ') || '', oid = uxMock().chosen?.['mto-billing'], h = document.createElement('div'); h.innerHTML = oid ? uxReleaseFor('lakeside', oid).text : ''; const rule = h.textContent.replace(/\s+/g, ' ').trim(); return { line, rule, oid, focus: document.activeElement.tagName }; });
    ok(!!r.oid && r.rule.length > 10 && r.line.includes(r.rule) && !/Released at once/.test(r.line) && r.focus !== 'BODY', `mto-billing after Choose: the card says the one release rule ("${r.rule.slice(0, 50)}…"), not a second one; focus is not on the page body (${r.focus})`);
    await p.click('.toast [data-ux-undo]'); await p.waitForTimeout(300); ok(await p.evaluate(() => document.activeElement.tagName !== 'BODY'), 'mto-billing after Undo: focus returns to the Choose button'); await p.context().close(); }
  /* review r4 M6 (Site r1 M1 class): the queue heads on the Portfolio and Act first say their count by state, from the one state source */
  { let differs = 0;
    for (const op of ['lakeside', 'harvest', 'metro']) for (const rt of ['portfolio', 'portfolio/act-first']) { const p = await page(rt, { op });
      const r = await p.evaluate(() => { const ids = [...new Set(ATTN[LS.op].map(x => x[4]))], k = ids.map(id => uxDecState(id).key), want = k.filter(x => x === 'choose' || x === 'none').length, h = document.querySelector('.ux-queue-panel h2, .layout-main-side h2'), head = h ? (() => { const k = h.cloneNode(true); k.querySelectorAll('[data-ux-split]').forEach(x => x.remove()); return k.textContent.replace(/\s+/g, ' ').trim(); })() : '', split = document.querySelector('[data-ux-split]')?.textContent || '', cnt = +(h?.querySelector('.ux-count')?.textContent || -1);
        const claims = /Needs a decision|waiting/i.test(head); const m = split.match(/(\d+) waiting for a choice/); return { ids: ids.length, want, head, claims, cnt, said: m ? +m[1] : 0, split: split.slice(0, 80) }; });
      if (r.ids !== r.want) differs++;
      ok((!r.claims || r.cnt === r.want) && r.said === r.want && r.cnt === r.ids, `${op} ${rt}: "${r.head}" counts ${r.cnt} of ${r.ids} decisions; ${r.want} wait for a choice and the line says ${r.said} (${r.split})`); await p.context().close(); }
    ok(differs >= 3, `queue heads: ${differs} of 6 pages hold decisions that are not waiting for a choice, so the check above is not empty`); }
  /* review r4 L6: at 1280 x 720 a tile's trend is shortened, never hidden */
  { let tiles = 0, hidden = [];
    for (const [op, sk] of [['lakeside', 'kobo'], ['lakeside', 'kisiwa'], ['lakeside', 'mto'], ['harvest', 'mwea'], ['harvest', 'thika'], ['harvest', 'kirinyaga'], ['metro', 'embakasi'], ['metro', 'kasarani'], ['metro', 'ruiru']]) { const p = await page(`site/${sk}`, { op, w: 1280, h: 720 });
      const r = await p.evaluate(() => { const t = [...document.querySelectorAll('.ux-kpis .ux-kpi')].filter(k => k.querySelector('.ux-trend')); return { n: t.length, hid: t.filter(k => { const e = k.querySelector('.ux-kpi-s.has-trend'); return !e || e.offsetHeight === 0; }).length, clip: t.flatMap(k => [...k.querySelectorAll('.ux-kpi-s.has-trend, .ux-kpi-s.has-trend *')]).filter(e => e.offsetHeight > 0 && e.scrollWidth > e.clientWidth + 1).map(e => e.textContent.trim().slice(0, 40)), /* r5 L-a: shortened, never clipped */ sub: (() => { const e = document.querySelector('.page-heading>div>p:not(.ux-scope)'); return e ? e.offsetHeight === 0 : false; })() }; });
      tiles += r.n; if (r.hid || r.sub || r.clip.length) hidden.push(`${sk}${r.hid ? ` ${r.hid} trend(s)` : ''}${r.sub ? ' subtitle' : ''}${r.clip.length ? ` clipped "${r.clip[0]}"` : ''}`); await p.context().close(); }
    ok(tiles >= 9 && !hidden.length, `Site pages at 1280 x 720: ${tiles} tile trends and the subtitle all show, none clipped${hidden.length ? ` (HIDDEN OR CLIPPED: ${hidden.join('; ')})` : ''}`); }
  /* r2 M3: the captive fleet's revenue row says "Not applicable", in its own words */
  await evBoard();
  // empty states that name their data path fail when the data holds a value there (placeholder audit, gap 4)
  for (const [op, r] of [['metro', 'portfolio'], ['metro', 'portfolio/demand-and-capacity'], ['metro', 'portfolio/scope'], ['metro', 'site/embakasi'], ['metro', 'site/kasarani'], ['metro', 'site/ruiru'], ['lakeside', 'portfolio/scope'], ['lakeside', 'portfolio/demand-and-capacity'], ['harvest', 'portfolio/scope'], ['lakeside', 'mini'], ['lakeside', 'cold'], ['lakeside', 'ev']]) {
    const p = await page(r, { op });
    const bad = await p.evaluate(() => [...document.querySelectorAll('[data-na-path]')].flatMap(e => e.dataset.naPath.split(' ').filter(Boolean)).filter(path => uxPathValue(path) != null));
    const boards = r.length <= 4 ? await p.evaluate(() => !/(no billing or payment records|no target declared for this site|no cooling energy meter|no bus roster connected|no settlement records|odometer readings|gross tariff estimate)/i.test(document.querySelector('.canvas').textContent)) : true;
    ok(!bad.length && boards, `${op} ${r}: no empty state where the data holds a value (${bad.join(', ') || 'none'})${r.length <= 4 ? ', earlier-view board reads the data' : ''}`);
    await p.context().close(); }
  // short laptop: the first queue row is above the fold at 1280 x 720 (guide §3.5)
  for (const [op, r] of [['lakeside', 'portfolio'], ['harvest', 'portfolio'], ['metro', 'portfolio'], ['lakeside', 'site/kobo'], ['lakeside', 'portfolio/act-first']]) {
    const p = await page(r, { w: 1280, h: 720, op });
    const y = await p.evaluate(() => { const li = document.querySelector('.ux-queue>li'); return li ? Math.round(li.getBoundingClientRect().bottom + scrollY) : null; }), ovf = await p.evaluate(() => (window.__ovf() || document.documentElement.scrollWidth > innerWidth));
    ok(y !== null && y <= 720 && !ovf, `${op} ${r} at 1280 x 720: first queue row ends at ${y} px (fold 720), no sideways scroll`); await p.context().close(); }
  // the header holds one row; a recalculation notice has its own row under it
  for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', { op });
    const r = await p.evaluate(() => ({ h: Math.round(document.querySelector('.topbar').getBoundingClientRect().height), inBar: !!document.querySelector('.topbar .snap-pending'), row: !!document.querySelector('.canvas>.ux-pending .snap-pending'), ovf: (window.__ovf() || document.documentElement.scrollWidth > innerWidth) }));
    ok(r.h <= 64 && !r.inBar && !r.ovf, `${op} header at 1440: one row (${r.h} px), notice ${r.row ? 'on its own row' : 'none'}, no overflow`); await p.context().close(); }
  // 5 heading order on the five screens
  for (const r of ['portfolio', 'portfolio/act-first', 'plan', 'decision/kobo-generator', 'site/kobo']) {
    const p = await page(r);
    const hs = await p.evaluate(() => [...document.querySelectorAll('#app h1,#app h2,#app h3,#app h4')].filter(e => !e.closest('.reviewbar,.ux-drawer')).map(e => +e.tagName[1]));
    let skip = 0; for (let i = 1; i < hs.length; i++) if (hs[i] > hs[i - 1] + 1) skip++;
    ok(hs.filter(h => h === 1).length === 1 && hs[0] === 1 && skip === 0, `${r}: one h1 first, ${hs.length} headings, ${skip} skipped levels`);
    await p.context().close(); }
  // 6 reduced motion
  { const p = await page('portfolio', { rm: true });
    const d = await p.evaluate(() => getComputedStyle(document.querySelector('.ux-drawer-panel')).transitionDuration);
    ok(/^0s/.test(d), `reduced motion: drawer transition ${d}`); await p.context().close(); }
  // 7 empty and loading states
  for (const st of ['empty', 'loading']) {
    const p = await page('portfolio', { q: `?state=${st}` });
    const r = await p.evaluate(st => { const e = document.querySelector('.ux-queue-panel [role="status"]'); return e ? e.textContent.trim().slice(0, 60) || (st === 'loading' && e.querySelectorAll('.ux-skel-row').length + ' skeleton rows') : null; }, st);
    ok(!!r, `state=${st}: the queue shows its ${st} state (${r})`);
    if (process.argv[3]) await p.screenshot({ path: process.argv[3] + `/state-${st}-1440.png` }); /* no out dir (ia_gates): no shot */ await p.context().close(); }
  // 8 trends (DS1m, R20; D-DS1.15): the 3 Portfolio overviews and all 9 Site pages. 8a form, 8b source and headline, 8c stated change
  const sweep = []; for (const op of ['lakeside', 'harvest', 'metro']) { sweep.push({ op, sk: null }); }
  const sitesOf = await (async () => { const p = await page('portfolio'); const m = await p.evaluate(() => Object.fromEntries(Object.keys(OPS).map(o => [o, OPS[o].sites]))); await p.context().close(); return m; })();
  for (const op of Object.keys(sitesOf)) for (const sk of sitesOf[op]) sweep.push({ op, sk });
  for (const { op, sk } of sweep) { const p = await page(sk ? 'site/' + sk : 'portfolio', { op }); const lab = `${op} ${sk ? 'Site ' + sk : 'overview'}`;
    const r = await p.evaluate(([op, sk]) => { const cost = OPS[op].kind === 'cost', k1 = cost ? 'cost' : 'contribution', root = sk ? '#app .ux-kpis' : '#app .ux-overview';
      const slots = [...document.querySelectorAll(`${root} .ux-kpi .ux-trend`)].map(e => ({ text: e.textContent.trim(), measure: e.getAttribute('data-measure'), sparks: e.querySelectorAll('svg.ux-spark').length }));
      const s1 = sk ? uxHistory(op, k1, sk) : uxHistory(op, k1), s2 = sk ? uxHistory(op, 'gap', sk) : uxHistory(op, 'gap');
      let head1 = null, head2 = null;
      if (sk) { const ov = X => X.status === 'evaluated' ? X.nodes[cost ? 'cost_to_serve' : 'contribution'] : X.stated_total, d = DERIVED.sites[`${OPS[op].t.tenant}/${siteM(sk).site}`]; head1 = ov(d.actual); head2 = siteM(sk).period.variance; }
      else { const T = opTotals(op); head1 = T.actual; head2 = T.variance; }
      const last = s => s ? s[s.length - 1].v : null, chg = s => s ? s[s.length - 1].v - s[s.length - 2].v : null, sep = s => s ? s[s.length - 2].m : null;
      const exp1 = !s1 ? null : cost ? (c => `Monthly cost ${c > 0 ? 'up ' + usdW(c) : c < 0 ? 'down ' + usdW(-c) : 'unchanged'} against ${sep(s1)}`)(Math.round(chg(s1))) : `${usdW(chg(s1), true)} against ${sep(s1)}`;
      const exp2 = !s2 ? null : `${usdW(chg(s2), true)} against ${sep(s2)}`;
      return { cost, slots, a: [last(s1), head1], v: [last(s2), head2], exp: [exp1, exp2] }; }, [op, sk]);
    const sl = r.slots, form = (t, i) => !!t && (i === 0 && r.cost ? t.measure === 'monthly-cost' && t.sparks === 0 && /^Monthly cost (up \$[\d,]+|down \$[\d,]+|unchanged) against \w+$/.test(t.text) : t.measure === null && t.sparks === 1 && /^[−+-]?\$[\d,]+ against \w+$/.test(t.text));
    ok(sl.length === 2 && sl.every(form) && !p._errs.length, `${lab} 8a form: ${sl.length} trend slots (${sl.map(t => `${t.measure || 'signed'}${t.sparks ? ' svg' : ''}: ${t.text}`).join(' | ')}); expected tile 1 ${r.cost ? 'measure-named' : 'signed'}, tile 2 signed`);
    const eq = ([x, y]) => x !== null && Math.abs(x - y) < 0.005;
    ok(eq(r.a) && eq(r.v), `${lab} 8b source and headline: last points ${r.a[0]} = ${r.a[1]} and ${r.v[0]} = ${r.v[1]}`);
    ok(r.exp[0] !== null && r.exp[1] !== null && sl.length === 2 && sl[0].text === r.exp[0] && sl[1].text === r.exp[1], `${lab} 8c stated change: "${sl.map(t => t.text).join('" and "')}" against series "${r.exp.join('" and "')}"`);
    await p.context().close(); }
  await b.close(); console.log(out.join('\n')); process.exit(out.some(l => l.startsWith('FAIL')) ? 1 : 0);
})();
