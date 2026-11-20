/* Browser interaction check (UI/UX guide gate G3/G4 support): drawers, table views, phone Section menu, keyboard focus,
   heading order, reduced motion, empty and loading states. Needs /opt/assetecon/tools/pw/env.sh sourced.
   Run: node tools/ux_interaction_check.cjs "$PWD/index.html" <folder for the two state screenshots> */
const { chromium } = require(process.env.PW);
const base = 'file://' + process.argv[2];
const out = []; const ok = (c, what) => out.push(`${c ? 'PASS' : 'FAIL'} ${what}`);
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  const openAll = p => p.evaluate(() => document.querySelectorAll('.canvas details').forEach(d => { d.open = true; }));
  const page = async (hash, o = {}) => { const ctx = await b.newContext({ viewport: { width: o.w || 1440, height: o.h || 900 }, colorScheme: o.dark ? 'dark' : 'light', reducedMotion: o.rm ? 'reduce' : 'no-preference' }); if (o.op) await ctx.addInitScript(v => { try { sessionStorage.setItem('l4-op', v); } catch (e) {} }, o.op); const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); await p.goto(base + (o.q || '') + '#/' + hash); await p.waitForTimeout(500); p._errs = errs; return p; };
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
    const vis = await p.evaluate(() => { const m = document.querySelector('.ux-tabmenu summary'), t = document.querySelector('.ux-tabs>.tabs'); return m.offsetParent !== null && getComputedStyle(t).display === 'none'; });
    await p.click('.ux-tabmenu summary'); await p.waitForTimeout(150); await p.click('.ux-tabmenu nav a[href="#/portfolio/act-first"]'); await p.waitForTimeout(400);
    const at = await p.evaluate(() => location.hash);
    const top3 = await p.evaluate(() => { const li = [...document.querySelectorAll('.ux-queue>li')]; return li.length; });
    ok(vis && at === '#/portfolio/act-first', 'phone: Section menu replaces the tab row and navigates');
    await p.goto(base + '#/portfolio'); await p.waitForTimeout(400);
    const shown = await p.evaluate(() => [...document.querySelectorAll('.ux-overview .ux-queue>li')].filter(e => e.offsetParent !== null).length + ' / ' + ([...document.querySelectorAll('.ux-overview .ux-more')].some(e => e.offsetParent) ? 'link' : 'no link'));
    ok(shown === '3 / link', `phone overview: top 3 queue items and "View all" (${shown})`);
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
  for (const [op, r] of [['lakeside', 'decision/kobo-generator'], ['lakeside', 'decision/kisiwa-genset'], ['lakeside', 'decision/mto-inverter'], ['harvest', 'decision/mwea-occupancy'], ['lakeside', 'portfolio'], ['lakeside', 'site/kobo'], ['lakeside', 'portfolio/act-first/plan']]) {
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
    const pv = await p.evaluate(() => { const d = document.querySelector('.ux-prov'); return d.open && /Design estimate/.test(d.textContent) && d.querySelector('.ux-pop-menu').offsetParent !== null; });
    await p.keyboard.press('Escape'); await p.waitForTimeout(100);
    const pc = await p.evaluate(() => !document.querySelector('.ux-prov').open && document.activeElement === document.querySelector('.ux-prov>summary'));
    ok(pv && pc, 'provenance: About these figures opens with the † meaning; Esc closes it and returns focus');
    await p.keyboard.press('Control+k'); await p.waitForTimeout(150);
    const op1 = await p.evaluate(() => document.getElementById('ux-cmd')?.dataset.open === 'true' && document.activeElement.classList.contains('ux-cmd-in'));
    await p.keyboard.type('kobo gen'); await p.waitForTimeout(100);
    const first = await p.evaluate(() => document.querySelector('#ux-cmd-list [aria-selected="true"]')?.textContent);
    await p.keyboard.press('Enter'); await p.waitForTimeout(400);
    const at = await p.evaluate(() => location.hash);
    ok(op1 && /Kobo generator stop setting/.test(first || '') && at === '#/decision/kobo-generator', `command search: Ctrl+K opens, "kobo gen" finds "${first}", Enter opens ${at}`);
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
      const r = await p.evaluate(id => { const d = document.getElementById(id); const t = d ? d.textContent : ''; return { open: d && d.dataset.open === 'true', hash: location.hash, drv: /^uxdrv-/.test(id), done: /What is being done/.test(t) && (d.querySelector('a[href^="#/decision/"]') ? /Open decision →/.test(t) : /No decision yet/.test(t)) }; }, m.d);
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
        const dr = document.getElementById(s.id), got = new Set([...dr.querySelectorAll('a[href^="#/decision/"]')].map(a => a.getAttribute('href').replace('#/decision/', '')));
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
  for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', { op });
    const r = await p.evaluate(() => {
      const ov = document.querySelector('.ux-overview'), blocks = [...ov.children].filter(e => e.offsetParent !== null && e.getBoundingClientRect().height > 0).length;
      const rows = [...document.querySelectorAll('.ux-overview .ux-queue>li.ux-q')];
      const ragged = rows.filter(li => Math.abs(li.querySelector('.ux-q-title').getBoundingClientRect().left - li.querySelector('.ux-q-top').getBoundingClientRect().left) > 1).length;
      const repeat = rows.filter(li => li.querySelector('.ux-q-title').textContent.trim().toLowerCase().startsWith(li.querySelector('.ux-q-site').textContent.replace('Site: ', '').trim().toLowerCase())).length;
      const prim = document.querySelectorAll('.ux-overview .ux-queue .ux-q-go.primary').length, fc = rows.find(li => li.dataset.state === 'choose'), firstPrim = fc ? (fc.querySelector('.ux-q-go.primary') ? 1 : 0) : 1;
      const vis = el => { const c = el.cloneNode(true); c.querySelectorAll('.vh, .ux-q-k').forEach(x => x.remove()); return c.textContent.trim(); }, blankDue = rows.filter(li => !li.dataset.due).every(li => vis(li.querySelector('.ux-q-due')) === '');
      const brk = document.querySelectorAll('.ux-hero .ux-wf-break').length, steps = [...document.querySelectorAll('.ux-wf-gapscale .ux-wf-bar')].map(b => b.getBoundingClientRect().width / b.parentElement.getBoundingClientRect().width);
      const groups = document.querySelectorAll('.ux-wf-gapscale .ux-wf-group').length, perRowHeading = [...document.querySelectorAll('.ux-wf-gapscale .ux-wf-h')].length;
      const fs = e => parseFloat(getComputedStyle(e).fontSize), mod = document.querySelector('.ux-kpi.is-modelled .ux-kpi-v'), act = document.querySelector('.ux-kpi:not(.is-modelled) .ux-kpi-v');
      const small = [...document.querySelectorAll('.ux-overview .ux-kpi-s:not(:has(.ux-trend)), .ux-overview .ux-q-why, .ux-overview .panel-head p, .ux-overview .ux-q-title')].filter(e => fs(e) < 14).length;
      return { blocks, h: document.documentElement.scrollHeight, ragged, repeat, prim, firstPrim, blankDue, brk, minStep: Math.min(...steps), groups, perRowHeading, modW: mod && act ? fs(mod) < fs(act) && getComputedStyle(mod).color !== getComputedStyle(act).color : false, small, leaks: !!document.querySelector('[id^="uxv-h-"]') };
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
          const dv = rec && DV_OPT[rec] && !String(DV_OPT[rec]).startsWith(DVTEXT) ? (document.querySelector('.ux-drec-n') || {}).textContent.includes(DV_OPT[rec]) : true;
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
          document.querySelectorAll('.canvas [data-count]').forEach(e => { const n = document.querySelectorAll(e.dataset.countOf || '#none').length; if (+e.dataset.count !== n) out.bad.push(`X5 ${r}: count ${e.dataset.count} but ${n} in ${e.dataset.countOf}`); });
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
  { const sites = { lakeside: ['kobo', 'kisiwa', 'mto'], harvest: ['mwea', 'thika', 'kirinyaga'], metro: ['embakasi', 'kasarani', 'ruiru'] }, shapes = new Set();
    for (const [op, sks] of Object.entries(sites)) for (const sk of sks) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) {
      const p = await page(`site/${sk}`, { op, w, h });
      const r = await p.evaluate(() => { const secs = [...document.querySelectorAll('.ux-dsecs > .ux-ans-sec')];
        return { labels: secs.map(s => s.querySelector('.ux-h2').textContent.trim()).filter(l => l !== 'Operations measures').join('|'), ans: secs.every(s => (s.querySelector('.ux-ans')?.textContent.trim() || '').length > 4),
          h1: document.querySelectorAll('h1').length, spark: [...document.querySelectorAll('.ux-kpi .ux-spark')].some(x => x.getBoundingClientRect().width > 0), words: [...document.querySelectorAll('.ux-kpi .ux-trend')].filter(x => x.getBoundingClientRect().height > 0).map(x => x.textContent.trim()),
          ovf: document.documentElement.scrollWidth > innerWidth, marks: [...document.querySelectorAll('.ux-board-go')].map(b => b.dataset.uxDrawer) }; });
      shapes.add(r.labels);
      let nav = 0, drw = 0; const h0 = await p.evaluate(() => location.hash);
      if (w === 1440) for (const id of r.marks.slice(0, 4)) { await p.evaluate(id => { document.querySelector(`[data-ux-drawer="${id}"]`).click(); }, id); await p.waitForTimeout(150);
        const st = await p.evaluate(id => ({ open: document.getElementById(id)?.dataset.open === 'true', hash: location.hash, done: /What is being done/.test(document.getElementById(id)?.textContent || '') }), id);
        if (st.open && st.done) drw++; if (st.hash !== h0) nav++; await p.keyboard.press('Escape'); await p.waitForTimeout(100); }
      await p.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await p.waitForTimeout(150); const stickyOn = await p.evaluate(() => !!document.querySelector('.ux-dsticky.is-on .status-pill')); await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(100);
      const phoneOk = w >= 600 || (!r.spark && r.words.length >= 1 && r.words.every(x => /against|not available yet/i.test(x))); /* G3: at least one trend, in words */
      const svc = await p.evaluate(() => { const s = [...document.querySelectorAll('.ux-ans-sec')].find(x => /Service and assets/.test(x.querySelector('.ux-h2').textContent)); if (!s) return false; const a = s.querySelector('.ux-ans').textContent, n = (s.innerHTML.match(/Above its target/g) || []).length; const m = a.match(/^(\d+) of/); return m ? +m[1] === n : n === 0; });
      ok(svc && r.ans && r.h1 === 1 && !r.ovf && phoneOk && !nav && stickyOn && (w !== 1440 || drw === Math.min(4, r.marks.length)), `${op} site/${sk} at ${w}: answer-titled sections, sticky context after scroll, one h1, no sideways scroll${w < 600 ? ', KPI trend in words without a sparkline' : ''}${w === 1440 ? `, ${drw} driver rows open their drawers in place` : ''}`);
      await p.context().close(); }
    ok(shapes.size === 1, `Site pages: one section structure for every Site type (${[...shapes].join(' / ')})`); }
  /* the plan page: answer-titled sections, the approver's sticky bar, and Approve / Send back with the one feedback pattern */
  for (const op of ['lakeside', 'harvest', 'metro']) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) {
    const p = await page('portfolio/act-first/plan', { op, w, h });
    const r = await p.evaluate(() => { const secs = [...document.querySelectorAll('.ux-ans-sec')]; return { n: secs.length, ans: secs.every(s => (s.querySelector('.ux-ans')?.textContent.trim() || '').length > 4), ovf: document.documentElement.scrollWidth > innerWidth, chip: document.querySelector('.ux-planband [data-plan-state]')?.dataset.planState, diff: /Changes since version/.test(document.body.textContent), crew: !!document.querySelector('[data-k="Crew"]') }; });
    await p.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await p.waitForTimeout(150);
    const st = await p.evaluate(() => ({ on: !!document.querySelector('.ux-dsticky.is-on [data-plan-state]'), act: !!document.querySelector('.ux-dsticky.is-on [data-ux-act="approve-plan"]') }));
    let flow = true, desc = '';
    if (w === 1440) { await p.evaluate(() => window.scrollTo(0, 0)); await p.click('.ux-planband [data-ux-act="approve-plan"]'); await p.waitForTimeout(250);
      const dlg = await p.evaluate(() => document.getElementById('uxact')?.dataset.open === 'true' && /What happens/.test(document.getElementById('uxact').textContent) && /Recorded under/.test(document.getElementById('uxact').textContent));
      await p.click('#uxact [data-ux-act-go]'); await p.waitForTimeout(400);
      const a = await p.evaluate(() => ({ chip: document.querySelector('.ux-planband [data-plan-state]')?.dataset.planState, undo: !!document.querySelector('.toast [data-ux-undo]') }));
      await p.click('.toast [data-ux-undo]'); await p.waitForTimeout(400); const b = await p.evaluate(() => document.querySelector('.ux-planband [data-plan-state]')?.dataset.planState);
      await p.click('.ux-planband [data-ux-act="send-back"]'); await p.waitForTimeout(250); await p.click('#uxact [data-ux-act-go]'); await p.waitForTimeout(400);
      const sb = await p.evaluate(() => ({ chip: document.querySelector('.ux-planband [data-plan-state]')?.dataset.planState, reason: /Sent back in this demonstration: “/.test(document.querySelector('.ux-planband').textContent) }));
      await p.click('.toast [data-ux-undo]'); await p.waitForTimeout(300);
      flow = dlg && a.chip === 'APPROVED' && a.undo && b === 'PROPOSED' && sb.chip === 'REVISED' && sb.reason; desc = `; Approve: confirm, toast with Undo, ${a.chip}, Undo ${b}; Send back with a reason: ${sb.chip}`; }
    ok(r.n >= 4 && r.ans && !r.ovf && r.chip === 'PROPOSED' && r.diff && (w < 600 || r.crew) && st.on && st.act && flow, `${op} plan at ${w}: ${r.n} answer-titled sections, changes since the version, crew per item, sticky approver bar${desc}`);
    await p.context().close(); }
  /* r2 M3: the captive fleet's revenue row says "Not applicable", in its own words */
  { const p = await page('ev', { op: 'metro' }); const t = await p.evaluate(() => document.querySelector('.canvas').textContent);
    ok(/Not applicable/.test(t) && /Revenue not applicable: charging is a cost centre/.test(t) && !/Grow revenue\s*Not measured yet/.test(t), 'EV board: the revenue row reads "Not applicable" with its reason'); await p.context().close(); }
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
    const y = await p.evaluate(() => { const li = document.querySelector('.ux-queue>li'); return li ? Math.round(li.getBoundingClientRect().bottom + scrollY) : null; }), ovf = await p.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    ok(y !== null && y <= 720 && !ovf, `${op} ${r} at 1280 x 720: first queue row ends at ${y} px (fold 720), no sideways scroll`); await p.context().close(); }
  // the header holds one row; a recalculation notice has its own row under it
  for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', { op });
    const r = await p.evaluate(() => ({ h: Math.round(document.querySelector('.topbar').getBoundingClientRect().height), inBar: !!document.querySelector('.topbar .snap-pending'), row: !!document.querySelector('.canvas>.ux-pending .snap-pending'), ovf: document.documentElement.scrollWidth > innerWidth }));
    ok(r.h <= 64 && !r.inBar && !r.ovf, `${op} header at 1440: one row (${r.h} px), notice ${r.row ? 'on its own row' : 'none'}, no overflow`); await p.context().close(); }
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
