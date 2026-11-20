/* Browser interaction check (UI/UX guide gate G3/G4 support): drawers, table views, phone Section menu, keyboard focus,
   heading order, reduced motion, empty and loading states. Needs /opt/assetecon/tools/pw/env.sh sourced.
   Run: node tools/ux_interaction_check.cjs "$PWD/index.html" <folder for the two state screenshots> */
const { chromium } = require(process.env.PW);
const base = 'file://' + process.argv[2];
const out = []; const ok = (c, what) => out.push(`${c ? 'PASS' : 'FAIL'} ${what}`);
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME });
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
  // phone option cards: every value starts in the same column, right of the labels (catches content wrapping into the label column)
  { const p = await page('decision/kobo-generator', { w: 390, h: 844 });
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
      for (const li of document.querySelectorAll('.ux-queue>li.ux-q')) { const cells = [...li.children].filter(c => c.offsetParent !== null);
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
    ok(await p.evaluate(() => { const d = document.querySelector('.ux-period'); return d.open && /not available yet/.test(d.textContent) && !!d.querySelector('.period-chip'); }), 'period menu: the current period, earlier periods "not available yet"');
    await p.context().close(); }
  // wave 2: the bridge links each step to its decision, with detail on focus; the value chain draws its losses; tiles have a visual
  for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', { op });
    const a = await p.$('.ux-wf-a'); let tip = false, href = null;
    if (a) { await a.focus(); await p.waitForTimeout(200); href = await a.getAttribute('href'); tip = await p.evaluate(() => { const t = document.activeElement.parentElement.querySelector('.ux-tip'); return +getComputedStyle(t).opacity > 0.9 && getComputedStyle(t).visibility === 'visible'; }); }
    const pd = await page('portfolio/demand-and-capacity', { op }); const vc = await pd.evaluate(() => [...document.querySelectorAll('.ux-vc-loss .ux-vc-bar')].filter(b => b.getBoundingClientRect().width > 1).length);
    const tiles = await p.evaluate(() => [...document.querySelectorAll('.ux-cat')].map(t => !!t.querySelector('.ux-bullet, .ux-seg, .ux-meterbar')));
    ok(!!href && /^#\/decision\//.test(href) && tip, `${op} bridge: a step links to ${href} and shows its detail on focus`);
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
    ok(!before.b && after.b === 'east-africa' && after.band && after.bad === before.bad && Math.abs(after.h - before.h) <= 32 && kept === 'east-africa', `brand switch: neutral to East Africa, motif band on, status colour unchanged, layout height within 32 px (a pack's band and heading rule) (${before.h} to ${after.h}), kept on reload`);
    await p.selectOption('#ux-brand', 'neutral'); await p.waitForTimeout(150);
    ok(await p.evaluate(() => !document.documentElement.hasAttribute('data-brand')), 'brand switch: back to neutral');
    await p.context().close(); }
  // wave 2c classes: overview budget; queue alignment, titles, one primary, quiet blanks; the bridge on the gap's scale;
  // modelled weight; prose size; content in its tab; a distinguishable East Africa pack
  for (const op of ['lakeside', 'harvest', 'metro']) { const p = await page('portfolio', { op });
    const r = await p.evaluate(() => {
      const ov = document.querySelector('.ux-overview'), blocks = [...ov.children].filter(e => e.offsetParent !== null && e.getBoundingClientRect().height > 0).length;
      const rows = [...document.querySelectorAll('.ux-overview .ux-queue>li.ux-q')];
      const ragged = rows.filter(li => Math.abs(li.querySelector('.ux-q-title').getBoundingClientRect().left - li.querySelector('.ux-q-top').getBoundingClientRect().left) > 1).length;
      const repeat = rows.filter(li => li.querySelector('.ux-q-title').textContent.trim().toLowerCase().startsWith(li.querySelector('.ux-q-site').textContent.replace('Site: ', '').trim().toLowerCase())).length;
      const prim = document.querySelectorAll('.ux-overview .ux-queue .ux-q-go.primary').length, firstPrim = rows[0]?.querySelector('.ux-q-go.primary') ? 1 : 0;
      const vis = el => { const c = el.cloneNode(true); c.querySelectorAll('.vh, .ux-q-k').forEach(x => x.remove()); return c.textContent.trim(); }, blankDue = rows.filter(li => !li.dataset.due).every(li => vis(li.querySelector('.ux-q-due')) === '');
      const brk = document.querySelectorAll('.ux-hero .ux-wf-break').length, steps = [...document.querySelectorAll('.ux-wf-gapscale .ux-wf-bar')].map(b => b.getBoundingClientRect().width / b.parentElement.getBoundingClientRect().width);
      const groups = document.querySelectorAll('.ux-wf-gapscale .ux-wf-group').length, perRowHeading = [...document.querySelectorAll('.ux-wf-gapscale .ux-wf-h')].length;
      const fs = e => parseFloat(getComputedStyle(e).fontSize), mod = document.querySelector('.ux-kpi.is-modelled .ux-kpi-v'), act = document.querySelector('.ux-kpi:not(.is-modelled) .ux-kpi-v');
      const small = [...document.querySelectorAll('.ux-overview .ux-kpi-s:not(:has(.ux-trend)), .ux-overview .ux-q-why, .ux-overview .panel-head p, .ux-overview .ux-q-title')].filter(e => fs(e) < 14).length;
      return { blocks, h: document.documentElement.scrollHeight, ragged, repeat, prim, firstPrim, blankDue, brk, minStep: Math.min(...steps), groups, perRowHeading, modW: mod && act ? fs(mod) < fs(act) && getComputedStyle(mod).color !== getComputedStyle(act).color : false, small, leaks: !!document.querySelector('[id^="uxv-h-"]') };
    });
    ok(r.blocks <= 6 && r.h <= 2500 && !r.leaks, `${op} overview budget: ${r.blocks} blocks, ${r.h} px at 1440, value leaks not here`);
    ok(r.ragged === 0 && r.repeat === 0 && r.prim === 1 && r.firstPrim === 1 && r.blankDue, `${op} queue: titles aligned (${r.ragged} ragged), no title repeats its Site (${r.repeat}), one primary Decide on the first row, no "No deadline" noise`);
    ok(r.brk === 0 && r.minStep >= 0.007 && r.groups >= 1 && r.perRowHeading === 0, `${op} bridge: on the gap's scale (no axis break), smallest step ${(r.minStep * 100).toFixed(1)}% of the width, ${r.groups} heading groups, no heading repeated per row`);
    ok(r.modW && r.small === 0, `${op} tiles and text: the modelled tile lighter than actuals; ${r.small} prose elements under 14 px`);
    await p.context().close(); }
  { const pd = await page('portfolio/demand-and-capacity'), po = await page('portfolio/outcomes-by-site');
    ok(await pd.evaluate(() => !!document.querySelector('[id^="uxv-h-"]')) && await po.evaluate(() => !!document.querySelector('.ux-insight')), 'content in its tab: value leaks on Demand and capacity, the insight on Outcomes by site');
    await pd.context().close(); await po.context().close(); }
  { const pn = await page('portfolio'), pe = await page('portfolio');
    await pe.selectOption('#ux-brand', 'east-africa'); await pe.waitForTimeout(200);
    const a = await pn.evaluate(() => ({ f: getComputedStyle(document.querySelector('.page-heading h1')).fontFamily, band: parseFloat(getComputedStyle(document.querySelector('.topbar'), '::after').height) || 0, tab: getComputedStyle(document.querySelector('.tabs a.active')).color }));
    const b = await pe.evaluate(() => ({ f: getComputedStyle(document.querySelector('.page-heading h1')).fontFamily, band: parseFloat(getComputedStyle(document.querySelector('.topbar'), '::after').height) || 0, tab: getComputedStyle(document.querySelector('.tabs a.active')).color, rail: getComputedStyle(document.querySelector('.rail'), '::before').backgroundImage !== 'none' }));
    ok(a.f !== b.f && b.band >= 10 && a.tab !== b.tab && b.rail, `East Africa distinguishable: heading typeface, ${b.band} px textile band, active-tab colour, rail pattern`);
    await pe.selectOption('#ux-brand', 'neutral'); await pn.context().close(); await pe.context().close(); }
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
