/* IA-1a layout check and screenshots (spec §6 item 6; review r1 M1, M2). Three operators; the plan and the not-found page at
   1440x900, 1280x720, 1200x800, 900x800 and 390x844, light and dark (screenshots), then a width sweep 390..1920 of the same
   two routes (measures only). Every top bar item keeps one line height (<= 40 px) and no top-bar element ends past the window;
   from 1200 up the top bar is on one line; no sideways scroll; at every width the rail shows, no rail child ends past the
   rail and each unavailable item has its status on one line in words, or (icon rail) a dashed outline, a title and an
   accessible name that say it, and has no tab stop.
   IA-1b: the hub routes (the three Portfolio tabs and every Site of the operator) at 1440x900, 1280x720 and 390x844, light and dark,
   with the same measures, and the headline rule (D-IA.29, R35): the hub's L1 headline is at most 2 lines at 1440 and 1280.
   Run under tools/heavy-slot.sh: node tools/ia_shots.cjs <index.html path> <out dir>
   Plants: SHOTS_PLANT=status (hides the status words), SHOTS_PLANT=headline (narrows the headline to force a third line). */
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
  return { hlLines, frame: !!document.querySelector('#ia-root.ia-frame'), oneLine, kids: kids.length, tall, past, hscroll: document.documentElement.scrollWidth > innerWidth + 1, rail: !!rr, railPast: rp, un };
};
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const lines = []; let bad = 0;
  const run = async (op, w, h, dark, r, shot) => {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: dark ? 'dark' : 'light' }); await ctx.addInitScript(v => { try { sessionStorage.setItem('l4-op', v); } catch (e) {} }, op);
    const p = await ctx.newPage(); await p.goto(`${base}#/${r}`); await p.waitForTimeout(400);
    if (PLANT === 'status') await p.addStyleTag({ content: '.ia-rail-status{display:none!important}' });
    if (PLANT === 'headline') await p.addStyleTag({ content: '.ux-headline{max-width:220px!important}' });
    const m = await p.evaluate(measure), why = [];
    if (!m.frame) why.push('no frame'); if (m.hscroll) why.push('sideways scroll'); if (m.tall.length) why.push(`tall top-bar item ${m.tall[0]}`); if (m.past.length) why.push(`top bar runs past the window (${m.past[0]})`);
    if (w >= 1200 && !m.oneLine) why.push('top bar not on one line'); if (m.railPast.length) why.push(`rail overflow (${m.railPast[0]})`); const u = m.un.filter(x => !x.ok); if (u.length) why.push(`unavailable item reads as live or overflows: ${u.map(x => x.n).join(', ')}`);
    if (m.rail && !m.un.length) why.push('no unavailable items measured');
    if (w >= 1280 && m.hlLines !== null && m.hlLines > 2) why.push(`headline on ${m.hlLines} lines`);
    if (!why.length) {} else bad++;
    if (shot) await p.screenshot({ path: `${out}/${op}-${r === 'x-unknown' ? 'not-found' : r.replace(/\//g, '-')}-${w}-${dark ? 'dark' : 'light'}.png`, fullPage: false });
    lines.push(`${why.length ? 'BAD' : 'ok '} ${op} #/${r} ${w}x${h} ${dark ? 'dark' : 'light'}: top bar one line ${m.oneLine} (${m.kids} items), rail ${m.rail ? `${m.un.length} unavailable items measured` : 'hidden'}${m.hlLines !== null ? `, headline ${m.hlLines} line(s)` : ''}${why.length ? ' · ' + why.join('; ') : ''}`); await ctx.close(); };
  const SITES = { lakeside: ['kobo', 'kisiwa', 'mto'], harvest: ['mwea', 'thika', 'kirinyaga'], metro: ['embakasi', 'kasarani', 'ruiru'] };
  const ONLY = process.env.SHOTS_ONLY; /* optional: run only the hub routes (IA-1b's set) */
  for (const op of Object.keys(SITES)) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) for (const dark of [false, true]) for (const r of ['portfolio', 'portfolio/outcomes', 'portfolio/demand-and-capacity', ...SITES[op].map(k => `site/${k}`)]) await run(op, w, h, dark, r, !PLANT);
  if (ONLY === 'hub') { await b.close(); console.log(lines.join('\n')); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); }
  for (const op of ['lakeside', 'harvest', 'metro']) for (const [w, h] of [[1440, 900], [1280, 720], [1200, 800], [900, 800], [390, 844]]) for (const dark of [false, true]) for (const r of ['plan', 'x-unknown']) await run(op, w, h, dark, r, true);
  for (const op of ['lakeside', 'harvest', 'metro']) for (const w of [390, 600, 761, 1023, 1024, 1100, 1101, 1279, 1400, 1600, 1920]) for (const r of ['plan', 'x-unknown']) await run(op, w, 800, false, r, false);
  await b.close(); console.log(lines.join('\n')); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); })();
