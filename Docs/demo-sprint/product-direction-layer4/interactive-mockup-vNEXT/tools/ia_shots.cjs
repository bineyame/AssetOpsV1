/* IA-1a layout check and screenshots (spec §6 item 6; review r1 M1, M2). Three operators; the plan and the not-found page at
   1440x900, 1280x720, 1200x800, 900x800 and 390x844, light and dark (screenshots), then a width sweep 390..1920 of the same
   two routes (measures only). Every top bar item keeps one line height (<= 40 px) and no top-bar element ends past the window;
   from 1200 up the top bar is on one line; no sideways scroll; at every width the rail shows, no rail child ends past the
   rail and each unavailable item has its status on one line in words, or (icon rail) a dashed outline, a title and an
   accessible name that say it, and has no tab stop.
   IA-1b: the hub routes (the three Portfolio tabs and every Site of the operator) at 1440x900, 1280x720 and 390x844, light and dark,
   with the same measures, and the headline rule (D-IA.29, R35): the hub's L1 headline is at most 2 lines at 1440 and 1280.
   Run under tools/heavy-slot.sh: node tools/ia_shots.cjs <index.html path> <out dir>
   D-IA.35 L5: at 390 every table.ux-stack stacks: each cell has scrollWidth <= clientWidth + 1 and the table is no wider than its container; #/portfolio/outcomes
   must measure at least one such table (a measured set that is empty fails).
   IA-1c: every decision route of the operator, and the "Waiting for you" inbox opened from the top bar on #/portfolio, at 1440x900, 1280x720 and
   390x844, light and dark, with the same measures; the inbox must be open and its panel inside the window. SHOTS_ONLY=decision runs only this set.
   IA-1c r1 (D-IA.37, D-IA.38): from 761 up the top bar is one line at every width and no visible search, scope, period or inbox label is truncated (scrollWidth <= clientWidth + 1); the width sweep
   (761..1920) runs portfolio, plan, x-unknown and, per operator, the decision of the longest Site name, and at 1440 on #/portfolio data-fit is "0" (the full search shows). Every decision run
   measures its Site crumb (shown, inside the width). SHOTS_ONLY=sweep runs only the sweep.
   Plants: SHOTS_PLANT=fit (no collapse; with SHOTS_ONLY=sweep), truncate (the search box clipped; sweep), crumbs (the keep rule deleted; with SHOTS_ONLY=decision), status (hides the status words), SHOTS_PLANT=headline (narrows the headline to force a third line), SHOTS_PLANT=stack (removes the stacking media rule). */
const { chromium } = require(process.env.PW), fs = require('fs');
const base = 'file://' + process.argv[2], out = process.argv[3]; fs.mkdirSync(out, { recursive: true });
const PLANT = process.env.SHOTS_PLANT || '';
const measure = () => { const tb = document.querySelector('.ia-frame .topbar'), kids = tb ? [...tb.querySelectorAll(':scope > *, :scope > .right > *')].filter(e => e.getBoundingClientRect().height > 0) : [];
  const cs = kids.map(e => { const r = e.getBoundingClientRect(); return (r.top + r.bottom) / 2; }), oneLine = Math.max(...cs) - Math.min(...cs) <= 8;
  const tall = kids.filter(e => e.getBoundingClientRect().height > 40).map(e => e.className || e.tagName), past = tb ? [...tb.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.right > innerWidth + 1; }).map(e => e.className || e.tagName) : [];
  const rail = document.querySelector('.ia-frame .rail'), rr = rail && getComputedStyle(rail).display !== 'none' ? rail.getBoundingClientRect() : null, rp = [], un = [];
  if (rr) { rail.querySelectorAll('*').forEach(e => { const r = e.getBoundingClientRect(); if (r.width > 0 && r.right > rr.right + 1) rp.push(e.className || e.tagName); });
    rail.querySelectorAll('[data-rail-unavailable]').forEach(e => { const st = e.querySelector('[data-rail-status]'), r = st && st.getBoundingClientRect(), shown = !!r && r.width > 0 && r.height > 0 && r.height <= 20, cs = getComputedStyle(e);
      const iconOk = cs.borderTopStyle === 'dashed' && /Not available yet/.test(e.title) && /Not available yet/.test(e.getAttribute('aria-label') || '');
      un.push({ n: e.dataset.railUnavailable, ok: (shown || iconOk) && !e.matches('[tabindex],a,button') && !e.querySelector('[tabindex],a,button') && e.getBoundingClientRect().right <= rr.right + 1 }); }); }
  const hl = document.querySelector('[data-shape="hub"] [data-level="L1"] .ux-headline'), hlLines = hl ? Math.round(hl.getBoundingClientRect().height / parseFloat(getComputedStyle(hl).lineHeight)) : null;
  const st = [...document.querySelectorAll('table.ux-stack')], stackBad = [];
  st.forEach(t => { const box = (t.closest('.table-wrap') || t.parentElement).getBoundingClientRect(); if (t.getBoundingClientRect().width > box.width + 1) stackBad.push('table wider than its container');
    t.querySelectorAll('th, td').forEach(c => { if (c.getClientRects().length && c.scrollWidth > c.clientWidth + 1) stackBad.push(`cell "${c.textContent.trim().slice(0, 24)}" ${c.scrollWidth} > ${c.clientWidth}`); }); });
  const trunc = [...document.querySelectorAll('.ia-frame .topbar .ia-search-t, .ia-frame .topbar .ux-scope-sw>summary, .ia-frame .topbar .ux-period summary, .ia-frame .topbar .ia-inbox-label')].filter(e => e.getBoundingClientRect().width > 2 && e.scrollWidth > e.clientWidth + 1).map(e => `${e.className || e.tagName} ${e.scrollWidth} > ${e.clientWidth}`);
  const ca = document.querySelector('.ia-frame .canvas .breadcrumbs a[href^="#/site/"]'), cr = ca && ca.getBoundingClientRect(), cs2 = ca && getComputedStyle(ca), cb = ca && getComputedStyle(ca.parentElement);
  const crumb = ca ? { shown: ca.getClientRects().length > 0 && cs2.visibility !== 'hidden' && cb.display !== 'none' && cb.visibility !== 'hidden', inside: cr.left >= 0 && cr.right <= innerWidth + 1 } : null;
  return { stackN: st.length, stackBad: [...new Set(stackBad)], hlLines, fit: tb ? tb.dataset.fit || null : null, trunc, crumb, frame: !!document.querySelector('#ia-root.ia-frame'), oneLine, kids: kids.length, tall, past, hscroll: document.documentElement.scrollWidth > innerWidth + 1, rail: !!rr, railPast: rp, un };
};
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const lines = []; let bad = 0;
  const run = async (op, w, h, dark, r, shot, act) => {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: dark ? 'dark' : 'light' }); await ctx.addInitScript(v => { try { sessionStorage.setItem('l4-op', v); } catch (e) {} }, op);
    const p = await ctx.newPage(); await p.goto(`${base}#/${r}`); await p.waitForTimeout(400);
    if (PLANT === 'status') await p.addStyleTag({ content: '.ia-rail-status{display:none!important}' });
    if (PLANT === 'fit') await p.evaluate(() => { iaFitTopbar = () => {}; render(); });
    if (PLANT === 'truncate') await p.addStyleTag({ content: '.ia-frame .topbar .searchbox{max-width:140px;overflow:hidden}.ia-frame .topbar .ia-search-t{overflow:hidden;text-overflow:ellipsis}' });
    if (PLANT === 'crumbs') await p.evaluate(() => { for (const sh of document.styleSheets) for (let i = sh.cssRules.length - 1; i >= 0; i--) if (/data-ia-crumbs/.test(sh.cssRules[i].cssText)) sh.deleteRule(i); });
    if (PLANT === 'headline') await p.addStyleTag({ content: '.ux-headline{max-width:220px!important}' });
    if (PLANT === 'stack') await p.evaluate(() => { for (const sh of document.styleSheets) for (let i = sh.cssRules.length - 1; i >= 0; i--) { const r = sh.cssRules[i]; if (r.type === CSSRule.MEDIA_RULE && /max-width:\s*760px/.test(r.conditionText) && /table\.ux-stack/.test(r.cssText)) sh.deleteRule(i); } });
    if (act === 'inbox') { await p.click('[data-ia-inbox]'); await p.waitForTimeout(350); }
    const m = await p.evaluate(measure), why = [];
    if (act === 'inbox') { const ib = await p.evaluate(() => { const d = document.getElementById('ia-inbox'), r = d && d.querySelector('.ux-drawer-panel').getBoundingClientRect(); return { open: !!d && d.dataset.open === 'true', fits: !!r && r.left >= -1 && r.right <= innerWidth + 1, rows: d ? d.querySelectorAll('a[data-ia-row]').length : 0 }; });
      if (!ib.open) why.push('the inbox did not open'); if (!ib.fits) why.push('the inbox panel runs past the window'); m.inboxRows = ib.rows; }
    if (!m.frame) why.push('no frame'); if (m.hscroll) why.push('sideways scroll'); if (m.tall.length) why.push(`tall top-bar item ${m.tall[0]}`); if (m.past.length) why.push(`top bar runs past the window (${m.past[0]})`);
    if (w >= 761 && !m.oneLine) why.push('top bar not on one line'); if (w >= 761 && m.trunc.length) why.push(`truncated control (${m.trunc[0]})`);
    if (r.startsWith('decision/')) { if (!m.crumb) why.push('no Site crumb link'); else if (!m.crumb.shown) why.push('the Site crumb is not shown'); else if (!m.crumb.inside) why.push('the Site crumb lies outside the viewport width'); }
    if (r === 'portfolio' && w === 1440 && !act && m.fit !== '0') why.push(`data-fit ${m.fit}, not 0: the full search is not shown where it fits`);
    if (m.railPast.length) why.push(`rail overflow (${m.railPast[0]})`); const u = m.un.filter(x => !x.ok); if (u.length) why.push(`unavailable item reads as live or overflows: ${u.map(x => x.n).join(', ')}`);
    if (m.rail && !m.un.length) why.push('no unavailable items measured');
    if (w >= 1280 && m.hlLines !== null && m.hlLines > 2) why.push(`headline on ${m.hlLines} lines`);
    if (w <= 760 && m.stackBad.length) why.push(`stacked table does not fit: ${m.stackBad[0]}`); if (w === 390 && r === 'portfolio/outcomes' && !m.stackN) why.push('no table.ux-stack measured on Outcomes');
    if (!why.length) {} else bad++;
    if (shot) await p.screenshot({ path: `${out}/${op}-${r === 'x-unknown' ? 'not-found' : r.replace(/\//g, '-')}${act ? `-${act}` : ''}-${w}-${dark ? 'dark' : 'light'}.png`, fullPage: false });
    lines.push(`${why.length ? 'BAD' : 'ok '} ${op} #/${r}${act ? ` (${act} open, ${m.inboxRows} rows)` : ''} ${w}x${h} ${dark ? 'dark' : 'light'}: top bar one line ${m.oneLine} (${m.kids} items), rail ${m.rail ? `${m.un.length} unavailable items measured` : 'hidden'}${m.hlLines !== null ? `, headline ${m.hlLines} line(s)` : ''}${why.length ? ' · ' + why.join('; ') : ''}`); await ctx.close(); };
  const SITES = { lakeside: ['kobo', 'kisiwa', 'mto'], harvest: ['mwea', 'thika', 'kirinyaga'], metro: ['embakasi', 'kasarani', 'ruiru'] };
  const ONLY = process.env.SHOTS_ONLY; /* optional: run only the hub routes (IA-1b's set), or only the decisions and the inbox (IA-1c's) */
  /* IA-1c: every decision of each operator, and the inbox open */
  const DECS = await (async () => { const ctx = await b.newContext(), p = await ctx.newPage(); await p.goto(`${base}#/plan`); await p.waitForTimeout(300);
    const x = await p.evaluate(() => Object.fromEntries(Object.keys(OPS).map(op => [op, DEC.filter(d => OPS[op].sites.includes(d.site)).map(d => d.id)]))); const L = await p.evaluate(() => Object.fromEntries(Object.keys(OPS).map(op => [op, DEC.filter(d => OPS[op].sites.includes(d.site)).sort((a, b) => SK[b.site].name.length - SK[a.site].name.length)[0].id]))); await ctx.close(); x.longest = L; return x; })();
  if (ONLY !== 'hub') for (const op of Object.keys(SITES)) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) for (const dark of [false, true]) {
    for (const d of DECS[op]) if (ONLY !== 'sweep') await run(op, w, h, dark, `decision/${d}`, !PLANT);
    if (ONLY !== 'sweep') await run(op, w, h, dark, 'portfolio', !PLANT, 'inbox'); }
  /* D-IA.37: the width sweep, 761 up */
  const SW = [761, 800, 900, 1023, 1024, 1100, 1101, 1199, 1200, 1280, 1366, 1440, 1600, 1920];
  if (ONLY === 'sweep' || !ONLY) for (const op of Object.keys(SITES)) for (const w of SW) for (const r of ['portfolio', 'plan', 'x-unknown', `decision/${DECS.longest[op]}`]) await run(op, w, 800, false, r, false);
  if (ONLY === 'sweep') { await b.close(); console.log(lines.join('\n')); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); }
  if (ONLY === 'decision') { await b.close(); console.log(lines.join('\n')); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); }
  for (const op of Object.keys(SITES)) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) for (const dark of [false, true]) for (const r of ['portfolio', 'portfolio/outcomes', 'portfolio/demand-and-capacity', ...SITES[op].map(k => `site/${k}`)]) if (ONLY !== 'decision') await run(op, w, h, dark, r, !PLANT);
  if (ONLY === 'hub') { await b.close(); console.log(lines.join('\n')); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); }
  for (const op of ['lakeside', 'harvest', 'metro']) for (const [w, h] of [[1440, 900], [1280, 720], [1200, 800], [900, 800], [390, 844]]) for (const dark of [false, true]) for (const r of ['plan', 'x-unknown']) await run(op, w, h, dark, r, true);
  for (const op of ['lakeside', 'harvest', 'metro']) for (const w of [390, 600]) for (const r of ['plan', 'x-unknown']) await run(op, w, 800, false, r, false);
  await b.close(); console.log(lines.join('\n')); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); })();
