/* Browser interaction check (UI/UX guide gate G3/G4 support): drawers, table views, phone Section menu, keyboard focus,
   heading order, reduced motion, empty and loading states. Needs /opt/assetecon/tools/pw/env.sh sourced.
   Run: node tools/ux_interaction_check.cjs "$PWD/index.html" <folder for the two state screenshots> */
const { chromium } = require(process.env.PW);
const base = 'file://' + process.argv[2];
const out = []; const ok = (c, what) => out.push(`${c ? 'PASS' : 'FAIL'} ${what}`);
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  const page = async (hash, o = {}) => { const ctx = await b.newContext({ viewport: { width: o.w || 1440, height: o.h || 900 }, colorScheme: o.dark ? 'dark' : 'light', reducedMotion: o.rm ? 'reduce' : 'no-preference' }); const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); await p.goto(base + (o.q || '') + '#/' + hash); await p.waitForTimeout(500); p._errs = errs; return p; };
  // 1 drawers on the Overview: open, focus, trap, Esc, return focus
  { const p = await page('portfolio');
    for (const k of ['grow', 'optimize', 'protect', 'assure']) {
      const sel = `[data-ux-drawer="uxd-lakeside-${k}"]`; await p.click(sel); await p.waitForTimeout(250);
      const st = await p.evaluate(k => ({ open: document.getElementById(`uxd-lakeside-${k}`).dataset.open, focus: document.activeElement.classList.contains('ux-x'), card: !!document.querySelector(`#uxd-lakeside-${k} .ocard[data-heading="${k}"]`) }), k);
      for (let i = 0; i < 40; i++) await p.keyboard.press('Tab');
      const inside = await p.evaluate(k => !!document.activeElement.closest(`#uxd-lakeside-${k}`), k);
      await p.keyboard.press('Escape'); await p.waitForTimeout(250);
      const back = await p.evaluate(sel => document.activeElement === document.querySelector(sel) && document.querySelector('.ux-drawer[data-open="true"]') === null, sel);
      ok(st.open === 'true' && st.focus && st.card && inside && back, `overview drawer ${k}: opens with its card, focus on Close, Tab stays inside, Esc closes and returns focus`);
    }
    // 2 table views
    for (const t of ['Show as table, by Site', 'Show the stages in detail']) {
      const s = p.locator('summary', { hasText: t }).first(); await s.click(); await p.waitForTimeout(150);
      const shown = await p.evaluate(t => { const d = [...document.querySelectorAll('details.ux-tableview')].find(x => x.querySelector('summary').textContent.includes(t)); return d.open && d.querySelector('.ux-tableview-body').getBoundingClientRect().height > 50; }, t);
      ok(shown, `overview "${t}" opens its table view`);
    }
    // 4 keyboard focus visible
    await p.goto(base + '#/portfolio'); await p.waitForTimeout(400); await p.keyboard.press('Tab');
    let seen = 0, visible = 0; for (let i = 0; i < 25; i++) { await p.keyboard.press('Tab'); const f = await p.evaluate(() => { const e = document.activeElement, c = getComputedStyle(e); return { ok: e !== document.body, vis: c.outlineStyle !== 'none' && parseFloat(c.outlineWidth) >= 2 || c.boxShadow !== 'none' }; }); if (f.ok) { seen++; if (f.vis) visible++; } }
    ok(seen >= 20 && visible === seen, `overview keyboard: ${visible} of ${seen} focused elements show a visible focus indicator`);
    ok(!p._errs.length, 'overview: no page errors'); await p.context().close(); }
  // decision page: the option Details drawers, chosen state
  { const p = await page('decision/kobo-generator');
    const ids = await p.evaluate(() => [...document.querySelectorAll('[data-ux-drawer^="uxo-"]')].map(e => e.dataset.uxDrawer));
    let good = 0; for (const id of ids) { await p.click(`[data-ux-drawer="${id}"]`); await p.waitForTimeout(200); const s = await p.evaluate(id => { const d = document.getElementById(id); return d.dataset.open === 'true' && !!d.querySelector('.ux-obl') && !!d.querySelector('[data-heading],.muted'); }, id); await p.keyboard.press('Escape'); await p.waitForTimeout(150); if (s) good++; }
    ok(ids.length === 4 && good === ids.length, `decision: ${good} of ${ids.length} option Details drawers open with limits and effects`);
    const chosen = await p.evaluate(() => !!document.querySelector('.ux-chosen') && !document.querySelector('[data-ux-drawer^="uxc-"]'));
    ok(chosen, 'decision: chosen item shows its chosen state, no Choose button');
    await p.context().close(); }
  // 3 phone Section menu
  { const p = await page('portfolio', { w: 390, h: 844 });
    const vis = await p.evaluate(() => { const m = document.querySelector('.ux-tabmenu summary'), t = document.querySelector('.ux-tabs>.tabs'); return m.offsetParent !== null && getComputedStyle(t).display === 'none'; });
    await p.click('.ux-tabmenu summary'); await p.waitForTimeout(150); await p.click('.ux-tabmenu nav a[href="#/portfolio/act-first"]'); await p.waitForTimeout(400);
    const at = await p.evaluate(() => location.hash);
    const top3 = await p.evaluate(() => { const li = [...document.querySelectorAll('.ux-queue>li')]; return li.length; });
    ok(vis && at === '#/portfolio/act-first', 'phone: Section menu replaces the tab row and navigates');
    await p.goto(base + '#/portfolio'); await p.waitForTimeout(400);
    const shown = await p.evaluate(() => [...document.querySelectorAll('.ux-overview .ux-queue>li')].filter(e => e.offsetParent !== null).length + ' / ' + (document.querySelector('.ux-more-phone')?.offsetParent ? 'link' : 'no link'));
    ok(shown === '3 / link', `phone overview: top 3 queue items and "View all" (${shown})`);
    const opt = await (async () => { await p.goto(base + '#/decision/kobo-generator'); await p.waitForTimeout(400); return p.evaluate(() => { const tr = document.querySelector('table.ux-opts tbody tr'); return getComputedStyle(tr).display === 'block' && document.documentElement.scrollWidth <= innerWidth; }); })();
    ok(opt, 'phone decision: options as stacked cards, no sideways page scroll');
    await p.context().close(); }
  // 5 heading order on the five screens
  for (const r of ['portfolio', 'portfolio/act-first', 'portfolio/act-first/plan', 'decision/kobo-generator', 'site/kobo']) {
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
    await p.screenshot({ path: process.argv[3] + `/state-${st}-1440.png` }); await p.context().close(); }
  await b.close(); console.log(out.join('\n')); process.exit(out.some(l => l.startsWith('FAIL')) ? 1 : 0);
})();
