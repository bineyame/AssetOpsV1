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
   IA-1c fix round (D-IA.41): the sweep adds 390, 600, 601, 760 and checks at every width: past, reach, trunc, midword, rows (data-fit 0-4 one line, 5 two row bands, 5 below 761), order (data-fit never rises with width), full (0 at 1920), asof (period menu holds the figures' time; 1440 and 390 on #/portfolio).
   Plants (D-IA.41, SHOTS_ONLY=sweep): wrap, phonesearch, midword, asof must fail; longname must pass.
   Plants: SHOTS_PLANT=fit (no collapse; with SHOTS_ONLY=sweep), truncate (the search box clipped; sweep), crumbs (the keep rule deleted; with SHOTS_ONLY=decision), status (hides the status words), SHOTS_PLANT=headline (narrows the headline to force a third line), SHOTS_PLANT=stack (removes the stacking media rule).
   IA-2r1 (D-IA.55, D-IA.56): SHOTS_ONLY=tabs runs the tab-switch set (plants tabnoscroll, tabscrollall); tilefill (every .heroes.ux-kpis row fills its width, at every
   measured route and width; plant SHOTS_PLANT=tilefill) is a measure of every run, and the run prints the count of tile rows it measured.
   IA-2a (spec §5.1.8 row 7, D-IA.52 R14, D-IA.49): with IA-2a in IA_LANDED or IA_FORCE_LANDED=IA-2a (then each page adds the unit and loads
   tools/fixtures/plan_stub.js when it has no shapePlan, and renders again), the four plan routes plan, plan/left-out, plan/review, plan/history
   join the measured set at 1440x900, 1280x720 and 390x844, light and dark, with every measure above (fit, truncate, crumbs clauses), and
   approvefold: at 1440x900 and 1280x720, at scroll 0 and while the plan is proposed, the band's own Approve (.ux-planband
   [data-ux-act="approve-plan"], never one inside [data-ux-sticky]) has getBoundingClientRect().bottom <= innerHeight. Shots on plan at 1440
   and 390 light: the Approve dialog open, after Approve, after Send back; the thresholds drawer at 1440 and 390; Lakeside 6500/No on Left out at
   1440. SHOTS_ONLY=plan runs only this set; otherwise it prints "IA-2a not landed; dormant". Plant SHOTS_PLANT=approvefold (a 900 px block
   before the band) must fail.
*/
const { chromium } = require(process.env.PW), fs = require('fs');
const base = 'file://' + process.argv[2], out = process.argv[3]; fs.mkdirSync(out, { recursive: true });
const PLANT = process.env.SHOTS_PLANT || '', LAST = {}; let relN = 0, SW_ORDER = false, IA2A_ON = false, tilesN = 0;
const path = require('path'), IA2A_FORCED = String(process.env.IA_FORCE_LANDED || '').split(',').map(x => x.trim()).includes('IA-2a');
const PLAN_STUB = fs.readFileSync(path.join(__dirname, 'fixtures', 'plan_stub.js'), 'utf8');
const measure = () => { const tb = document.querySelector('.ia-frame .topbar'), kids = tb ? [...tb.querySelectorAll(':scope > *, :scope > .right > *')].filter(e => e.getBoundingClientRect().height > 0) : [];
  const cs = kids.map(e => { const r = e.getBoundingClientRect(); return (r.top + r.bottom) / 2; }), oneLine = Math.max(...cs) - Math.min(...cs) <= 8;
  const fit5 = !!tb && tb.dataset.fit === '5', tall = kids.filter(e => !(fit5 && e.matches('.ux-scope-sw')) && e.getBoundingClientRect().height > 40).map(e => e.className || e.tagName), past = tb ? [...tb.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && !e.closest('details:not([open]) > :not(summary)') && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName) : [];
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
  /* D-IA.41: reach (each control a real box, inside the window, hit at its centre), rows (centre bands), midword (the scope summary never breaks inside a word) */
  const CTL = { scope: '.ux-scope-sw>summary', search: '.searchbox', period: '.ux-period>summary', inbox: '.ia-inbox', theme: '.theme-toggle' }, reach = [];
  for (const [n, sel] of Object.entries(CTL)) { const e = tb && tb.querySelector(sel), r = e && e.getBoundingClientRect(); if (!r) { reach.push(`${n} not present`); continue; }
    const hit = document.elementFromPoint(Math.min(Math.max(r.left + r.width / 2, 0), innerWidth - 1), Math.min(Math.max(r.top + r.height / 2, 0), innerHeight - 1));
    if (r.width < 16 || r.left < -1 || r.right > innerWidth + 1 || r.top < -1 || r.bottom > innerHeight + 1 || !hit || !(e === hit || e.contains(hit))) reach.push(`${n} not reachable`); }
  const bands = []; cs.slice().sort((a, b) => a - b).forEach(c => { if (!bands.length || c - bands[bands.length - 1] > 8) bands.push(c); });
  const sw = tb && tb.querySelector('.ux-scope-sw>summary'), swc = sw && getComputedStyle(sw), mw = swc ? (swc.overflowWrap !== 'normal' || swc.wordBreak !== 'normal' || swc.textOverflow === 'ellipsis' ? `${swc.overflowWrap}/${swc.wordBreak}/${swc.textOverflow}` : '') : 'no scope switch';
  /* D-IA.56: every .heroes.ux-kpis row in the IA frame fills its width: the last tile's right edge is within 2 px of the row's content right edge */
  const tiles = [...document.querySelectorAll('.ia-frame .heroes.ux-kpis')].filter(e => e.getClientRects().length && e.children.length).map(e => { const r = e.getBoundingClientRect(), pr = parseFloat(getComputedStyle(e).paddingRight) || 0, last = e.lastElementChild.getBoundingClientRect(); return { n: e.children.length, gap: Math.round(r.right - pr - last.right) }; });
  return { tiles, reach, bandN: bands.length, mw, stackN: st.length, stackBad: [...new Set(stackBad)], hlLines, fit: tb ? tb.dataset.fit || null : null, trunc, crumb, frame: !!document.querySelector('#ia-root.ia-frame'), oneLine, kids: kids.length, tall, past, hscroll: document.documentElement.scrollWidth > innerWidth + 1, rail: !!rr, railPast: rp, un };
};
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const lines = []; let bad = 0;
  const run = async (op, w, h, dark, r, shot, act) => {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: dark ? 'dark' : 'light' }); await ctx.addInitScript(v => { try { sessionStorage.setItem('l4-op', v); } catch (e) {} }, op);
    const p = await ctx.newPage(); await p.goto(`${base}#/${r}`); await p.waitForTimeout(400);
    if (IA2A_FORCED) await p.evaluate(src => { IA_LANDED.add('IA-2a'); if (typeof shapePlan !== 'function') (0, eval)(src); render(); }, PLAN_STUB);
    if (act === 'case') { await p.evaluate(() => { for (const [n, v] of [['sw-budget', '6500'], ['sw-loi', 'no']]) { const i = document.querySelector(`input[name="${n}"][value="${v}"]`); i.checked = true; i.dispatchEvent(new Event('change', { bubbles: true })); } location.hash = '#/plan/left-out'; }); await p.waitForTimeout(300); }
    if (PLANT === 'approvefold') await p.evaluate(() => { const b = document.querySelector('[data-shape="plan"] .ux-planband'); if (b) b.insertAdjacentHTML('beforebegin', '<div data-plant="approvefold" style="height:900px"></div>'); });
    if (PLANT === 'tilefill') await p.evaluate(() => { const del = l => { for (let i = l.length - 1; i >= 0; i--) { const r = l[i]; if (r.cssRules && r.type !== CSSRule.STYLE_RULE) del(r.cssRules); else if (/heroes\.ux-kpis[^{]*last-child/.test(r.selectorText || '') && /ia-frame/.test(r.selectorText)) (r.parentRule || r.parentStyleSheet).deleteRule(i); } }; for (const sh of document.styleSheets) del(sh.cssRules); });
    if (PLANT === 'releasedtype') await p.addStyleTag({ content: '.ia-plan-released{font-size:1rem!important;color:#c00!important}' }); /* D-IA.60 L6: the rule removed */
    if (PLANT === 'status') await p.addStyleTag({ content: '.ia-rail-status{display:none!important}' });
    if (PLANT === 'fit') await p.evaluate(() => { iaFitTopbar = () => {}; render(); });
    if (PLANT === 'truncate') await p.addStyleTag({ content: '.ia-frame .topbar .searchbox{max-width:140px;overflow:hidden}.ia-frame .topbar .ia-search-t{overflow:hidden;text-overflow:ellipsis}' });
    const PAD = '.ia-frame .topbar .ux-scope-sw>summary{padding-right:240px}';
    if (PLANT === 'wrap') { await p.evaluate(() => { const del = l => { for (let i = l.length - 1; i >= 0; i--) { const r = l[i]; if (r.cssRules && r.type !== CSSRule.STYLE_RULE) del(r.cssRules); else if (/data-fit="5"/.test(r.selectorText || '')) (r.parentRule || r.parentStyleSheet).deleteRule(i); } }; for (const sh of document.styleSheets) del(sh.cssRules); }); await p.addStyleTag({ content: PAD }); await p.evaluate(() => iaFitTopbar()); }
    if (PLANT === 'longname') await p.evaluate(() => { const s = document.querySelector('.ia-frame .topbar .ux-scope-sw>summary'); s.textContent = 'Lakeside Power · Kisiwa Generator and Fuel Depot, Northern Shore Extension ▾'; iaFitTopbar(); }); /* control: a long name made of words (the 240px padding stand-in cannot fit at 390 by any form) */
    if (PLANT === 'phonesearch') await p.addStyleTag({ content: '@media (max-width:600px){.ia-frame .topbar .searchbox{display:none!important}}' });
    if (PLANT === 'midword') { await p.addStyleTag({ content: PAD + '.ia-frame .topbar .ux-scope-sw>summary{overflow-wrap:anywhere!important}' }); await p.evaluate(() => iaFitTopbar()); }
    if (PLANT === 'asof') await p.evaluate(() => { iaPeriodHtml = op => uxPeriodMenuHtml(op, iaPeriodChip(op)); render(); });
    if (PLANT === 'crumbs') await p.evaluate(() => { for (const sh of document.styleSheets) for (let i = sh.cssRules.length - 1; i >= 0; i--) if (/data-ia-crumbs/.test(sh.cssRules[i].cssText)) sh.deleteRule(i); });
    if (PLANT === 'headline') await p.addStyleTag({ content: '.ux-headline{max-width:220px!important}' });
    if (PLANT === 'stack') await p.evaluate(() => { for (const sh of document.styleSheets) for (let i = sh.cssRules.length - 1; i >= 0; i--) { const r = sh.cssRules[i]; if (r.type === CSSRule.MEDIA_RULE && /max-width:\s*760px/.test(r.conditionText) && /table\.ux-stack/.test(r.cssText)) sh.deleteRule(i); } });
    if (act === 'inbox') { await p.click('[data-ia-inbox]'); await p.waitForTimeout(350); }
    const fold = r.startsWith('plan') && !act && (w === 1440 || w === 1280) ? await p.evaluate(() => { const a = [...document.querySelectorAll('[data-shape="plan"] .ux-planband [data-ux-act="approve-plan"]')].find(e => !e.closest('[data-ux-sticky]'));
      return a ? { b: Math.round(a.getBoundingClientRect().bottom), h: innerHeight, y: scrollY } : null; }) : null;
    if (['dialog', 'approved', 'sentback'].includes(act)) { await p.click('[data-shape="plan"] .ux-planband [data-ux-act="' + (act === 'sentback' ? 'send-back' : 'approve-plan') + '"]'); await p.waitForTimeout(300);
      if (act === 'sentback') await p.evaluate(() => { const t = document.getElementById('ux-sb-reason'), s = document.getElementById('ux-sb-way'); t.value = 'The crew cannot do both visits'; s.value = [...s.options].find(o => o.value).value; for (const e of [t, s]) for (const k of ['input', 'change']) e.dispatchEvent(new Event(k, { bubbles: true })); });
      if (act !== 'dialog') { await p.click('#uxact [data-ux-act-go]'); await p.waitForTimeout(400); } }
    if (act === 'thresholds') { await p.click('[data-shape="plan"] button[data-ux-drawer="ia-plan-thresholds"]'); await p.waitForTimeout(350); }
    const m = await p.evaluate(measure), why = [];
    if (act === 'inbox') { const ib = await p.evaluate(() => { const d = document.getElementById('ia-inbox'), r = d && d.querySelector('.ux-drawer-panel').getBoundingClientRect(); return { open: !!d && d.dataset.open === 'true', fits: !!r && r.left >= -1 && r.right <= innerWidth + 1, rows: d ? d.querySelectorAll('a[data-ia-row]').length : 0 }; });
      if (!ib.open) why.push('the inbox did not open'); if (!ib.fits) why.push('the inbox panel runs past the window'); m.inboxRows = ib.rows; }
    if (r.startsWith('plan') && !act && (w === 1440 || w === 1280) && IA2A_ON) { if (!fold) why.push('no band Approve measured (approvefold)'); else if (fold.b > fold.h || fold.y) why.push(`the band's Approve ends at ${fold.b} past the first viewport ${fold.h} (approvefold)`); else m.fold = fold.b; }
    if (act === 'thresholds' && !(await p.evaluate(() => (document.getElementById('ia-plan-thresholds') || {}).dataset?.open === 'true'))) why.push('the thresholds drawer did not open');
    if (act === 'approved' && !(await p.evaluate(() => /approved/i.test((document.querySelector('.ux-toast') || {}).textContent || '')))) why.push('no approval toast');
    if (r === 'plan' && !act && IA2A_ON) { const t = await p.evaluate(() => { const a = document.querySelector('.ia-plan-released'), b = document.querySelector('.approval-releases'); if (!a || !b) return null; const x = getComputedStyle(a), y = getComputedStyle(b); return { same: x.fontSize === y.fontSize && x.color === y.color && x.fontWeight === y.fontWeight, a: `${x.fontSize} ${x.fontWeight} ${x.color}`, b: `${y.fontSize} ${y.fontWeight} ${y.color}` }; });
      if (t) { relN++; if (!t.same) why.push(`the already-released clause reads ${t.a}, the release line ${t.b} (releasedtype)`); } }
    if (!m.frame) why.push('no frame'); if (m.hscroll) why.push('sideways scroll'); if (m.tall.length) why.push(`tall top-bar item ${m.tall[0]}`); if (m.past.length) why.push(`top bar runs past the window (${m.past[0]})`);
    if (m.reach.length && !act) why.push(`${m.reach[0]} (reach)`); if (m.trunc.length) why.push(`truncated control (${m.trunc[0]})`); if (m.mw) why.push(`the scope label breaks inside a word or ends in an ellipsis (${m.mw}) (midword)`);
    if (w < 761 && m.fit !== '5') why.push(`data-fit ${m.fit}, not 5 below 761 (rows)`);
    if (m.fit !== null && m.fit !== '5' && !m.oneLine) why.push(`data-fit ${m.fit} but the top bar is not on one line (rows)`); if (m.fit === '5' && m.bandN !== 2) why.push(`data-fit 5 but the items fall in ${m.bandN} row band(s), not 2 (rows)`);
    if (SW_ORDER && PLANT !== 'longname') { const k = `${op} ${r}`, f = +m.fit; if (LAST[k] !== undefined && f > LAST[k]) why.push(`data-fit rose from ${LAST[k]} to ${f} as the width rose to ${w} (order)`); LAST[k] = f; }
    if (SW_ORDER && PLANT !== 'longname' && w === 1920 && m.fit !== '0') why.push(`data-fit ${m.fit}, not 0 at 1920 (full)`);
    if (SW_ORDER && (w === 1440 || w === 390) && r === 'portfolio') { const a = await p.evaluate(async () => { const s = document.querySelector('.ia-frame .topbar .ux-period>summary'); s.click(); await new Promise(x => setTimeout(x, 100)); const it = document.querySelector('.ia-frame .topbar .ux-period [aria-current="true"]'); return { t: it ? it.textContent : '', want: snapText() }; }); if (!a.t.includes(a.want)) why.push(`the period menu's current item lacks "${a.want}" (asof)`); }
    if (r.startsWith('decision/')) { if (!m.crumb) why.push('no Site crumb link'); else if (!m.crumb.shown) why.push('the Site crumb is not shown'); else if (!m.crumb.inside) why.push('the Site crumb lies outside the viewport width'); }
    if (r === 'portfolio' && w === 1440 && !act && PLANT !== 'longname' && m.fit !== '0') why.push(`data-fit ${m.fit}, not 0: the full search is not shown where it fits`);
    if (m.railPast.length) why.push(`rail overflow (${m.railPast[0]})`); const u = m.un.filter(x => !x.ok); if (u.length) why.push(`unavailable item reads as live or overflows: ${u.map(x => x.n).join(', ')}`);
    if (m.rail && !m.un.length) why.push('no unavailable items measured');
    if (w >= 1280 && m.hlLines !== null && m.hlLines > 2) why.push(`headline on ${m.hlLines} lines`);
    if (w <= 760 && m.stackBad.length) why.push(`stacked table does not fit: ${m.stackBad[0]}`); if (w === 390 && r === 'portfolio/outcomes' && !m.stackN) why.push('no table.ux-stack measured on Outcomes');
    for (const t of m.tiles) { tilesN++; if (Math.abs(t.gap) > 2) why.push(`a ${t.n}-tile row stops ${t.gap} px short of its row's right edge (tilefill)`); }
    if (!why.length) {} else bad++;
    if (shot) await p.screenshot({ path: `${out}/${op}-${r === 'x-unknown' ? 'not-found' : r.replace(/\//g, '-')}${act ? `-${act}` : ''}-${w}-${dark ? 'dark' : 'light'}.png`, fullPage: false });
    lines.push(`${why.length ? 'BAD' : 'ok '} ${op} #/${r}${act ? ` (${act}${act === 'inbox' ? ` open, ${m.inboxRows} rows` : ''})` : ''}${m.fold ? ` band Approve bottom ${m.fold}` : ''} ${w}x${h} ${dark ? 'dark' : 'light'}: top bar one line ${m.oneLine} (${m.kids} items), rail ${m.rail ? `${m.un.length} unavailable items measured` : 'hidden'}${m.hlLines !== null ? `, headline ${m.hlLines} line(s)` : ''}${why.length ? ' · ' + why.join('; ') : ''}`); await ctx.close(); };
  const SITES = { lakeside: ['kobo', 'kisiwa', 'mto'], harvest: ['mwea', 'thika', 'kirinyaga'], metro: ['embakasi', 'kasarani', 'ruiru'] };
  const ONLY = process.env.SHOTS_ONLY; /* optional: run only the hub routes (IA-1b's set), or only the decisions and the inbox (IA-1c's) */
  /* IA-1c: every decision of each operator, and the inbox open */
  const DECS = await (async () => { const ctx = await b.newContext(), p = await ctx.newPage(); await p.goto(`${base}#/plan`); await p.waitForTimeout(300);
    const x = await p.evaluate(() => Object.fromEntries(Object.keys(OPS).map(op => [op, DEC.filter(d => OPS[op].sites.includes(d.site)).map(d => d.id)]))); const L = await p.evaluate(() => Object.fromEntries(Object.keys(OPS).map(op => [op, DEC.filter(d => OPS[op].sites.includes(d.site)).sort((a, b) => SK[b.site].name.length - SK[a.site].name.length)[0].id]))); await ctx.close(); x.longest = L; return x; })();
  /* IA-2a: the four plan routes (landed, or forced) */
  { const ctx = await b.newContext(), p = await ctx.newPage(); await p.goto(`${base}#/plan`); await p.waitForTimeout(300); IA2A_ON = IA2A_FORCED || await p.evaluate(() => IA_LANDED.has('IA-2a')); await ctx.close(); }
  if (!IA2A_ON) { lines.push('IA-2a not landed; dormant'); if (ONLY === 'plan') { await b.close(); console.log(lines.join('\n') + `\ntile rows measured: ${tilesN}`); process.exit(0); } }
  else if (!ONLY || ONLY === 'plan') { for (const op of Object.keys(SITES)) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) for (const dark of [false, true]) for (const r of ['plan', 'plan/left-out', 'plan/review', 'plan/history']) await run(op, w, h, dark, r, !PLANT);
    if (!PLANT) { for (const op of Object.keys(SITES)) for (const [w, h] of [[1440, 900], [390, 844]]) { for (const a of ['dialog', 'approved', 'sentback', 'thresholds']) await run(op, w, h, false, 'plan', true, a); }
      await run('lakeside', 1440, 900, false, 'plan', true, 'case'); }
    if (!relN) { lines.push('BAD no already-released clause measured (releasedtype)'); bad++; } lines.push(`releasedtype: ${relN} clauses measured`);
    if (ONLY === 'plan') { await b.close(); console.log(lines.join('\n') + `\ntile rows measured: ${tilesN}`); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); } }

  /* D-IA.55: a tab switch shows its tab. Every group with more than one landed tab (Portfolio; Plan; Site on one Site of each type) x the operator x
     390x844, 1280x720, 1440x900: from the first tab click each other tab in turn, then the last back to the first, then Back once. After two frames:
     the content's first box has at least 48 px inside the viewport; the active tab is wholly in view; after a click focus is on the active tab (or the
     phone menu's summary); on the plan routes at 1440 and 1280 scrollY is 0. Plants tabnoscroll (no listener), tabscrollall (no fold test). */
  if (IA2A_ON && (!ONLY || ONLY === 'tabs')) {
    const CFGS = ['proposed', 'approved', 'sent back'].flatMap(st => [false, true].map(nd => [st, nd])); /* D-IA.58: every plan state x the default and the non-default case (D-IA.50) */
    const GROUPS = op => [['Portfolio', 'portfolio'], ['Plan', 'plan'], ['Site', `site/${SITES[op][0]}`]];  /* a group with one landed tab draws no tabs and has no switch: reported, not measured */ let tabN = 0, tabBad = 0;
    for (const op of Object.keys(SITES)) for (const [w, h] of [[390, 844], [1280, 720], [1440, 900]]) for (const [g, start] of GROUPS(op)) for (const [state, cs] of (g === 'Plan' ? CFGS : [['proposed', false]])) {
      const ctx = await b.newContext({ viewport: { width: w, height: h } }); await ctx.addInitScript(v => { try { sessionStorage.setItem('l4-op', v); } catch (e) {} }, op);
      const p = await ctx.newPage(); await p.goto(`${base}#/${start}`); await p.waitForTimeout(400);
      if (IA2A_FORCED) await p.evaluate(src => { IA_LANDED.add('IA-2a'); if (typeof shapePlan !== 'function') (0, eval)(src); render(); }, PLAN_STUB);
      if (cs) await p.evaluate(() => { for (const [n, v] of (({ lakeside: [['sw-budget', '6500'], ['sw-loi', 'no']], harvest: [['sw-agg', 'no']], metro: [['sw-tou', 'no']] })[sessionStorage.getItem('l4-op')] || [])) { const i = document.querySelector(`input[name="${n}"][value="${v}"]`); if (i) { i.checked = true; i.dispatchEvent(new Event('change', { bubbles: true })); } } });
      if (state !== 'proposed') { await p.click('[data-shape="plan"] .ux-planband [data-ux-act="' + (state === 'sent back' ? 'send-back' : 'approve-plan') + '"]'); await p.waitForTimeout(300);
        if (state === 'sent back') await p.evaluate(() => { const t = document.getElementById('ux-sb-reason'), s = document.getElementById('ux-sb-way'); t.value = 'The crew cannot do both visits'; s.value = [...s.options].find(o => o.value).value; for (const e of [t, s]) for (const k of ['input', 'change']) e.dispatchEvent(new Event(k, { bubbles: true })); });
        await p.click('#uxact [data-ux-act-go]'); await p.waitForTimeout(400); }
      if (PLANT === 'tabstrip') await p.evaluate(() => { iaTabSwitch = () => requestAnimationFrame(() => { const s = document.querySelector('[data-ia-tabs]'), L2 = document.querySelector('[data-level="L2"]') || document.querySelector('[data-level]'), box = L2 && [L2, ...L2.querySelectorAll('*')].find(e => e.getClientRects().length); if (s && box && box.getBoundingClientRect().top + scrollY > innerHeight - 48) window.scrollTo({ top: s.firstElementChild.getBoundingClientRect().top + scrollY, behavior: 'instant' }); const t = [...document.querySelector('[data-ia-tabs]').querySelectorAll('a.active, .ux-tabmenu summary')].find(e => e.getClientRects().length); if (t) t.focus({ preventScroll: true }); }); }); /* the D-IA.55 rule: strip to the top */
      if (PLANT === 'tabnoscroll') await p.evaluate(() => { iaTabSwitch = () => requestAnimationFrame(() => { const t = [...document.querySelector('[data-ia-tabs]').querySelectorAll('a.active, .ux-tabmenu summary')].find(e => e.getClientRects().length); if (t) t.focus({ preventScroll: true }); }); }); /* no scroll listener, focus kept */
      if (PLANT === 'tabscrollall') await p.evaluate(() => { iaTabSwitch = () => requestAnimationFrame(() => { const s = document.querySelector('[data-ia-tabs]'); if (s) window.scrollTo({ top: s.firstElementChild.getBoundingClientRect().top + scrollY, behavior: 'instant' }); const t = [...document.querySelector('[data-ia-tabs]').querySelectorAll('a.active, .ux-tabmenu summary')].find(e => e.getClientRects().length); if (t) t.focus({ preventScroll: true }); }); });
      const hrefs = await p.evaluate(() => [...document.querySelectorAll('[data-ia-tabs] nav.tabs a[href^="#/"]')].map(a => a.getAttribute('href'))), seq = [...hrefs.slice(1), hrefs[0]];
      if (hrefs.length < 2) { if (g === 'Site') lines.push(`ok  ${op} ${g} ${w}x${h}: one landed tab, no tab switch (not measured)`); else { lines.push(`BAD ${op} ${g} ${w}x${h}: fewer than 2 tabs measured`); bad++; tabBad++; } await ctx.close(); continue; }
      const check = async (label, click) => { await p.waitForTimeout(150);
        const m = await p.evaluate(() => { const strip = document.querySelector('[data-ia-tabs]'), L2 = document.querySelector('[data-level="L2"]') || document.querySelector('[data-level]'), box = L2 && [L2, ...L2.querySelectorAll('*')].find(e => e.getClientRects().length), act = strip && [...strip.querySelectorAll('a.active, .ux-tabmenu summary')].find(e => e.getClientRects().length), r = act && act.getBoundingClientRect(), f = document.activeElement;
          const bar = document.querySelector('[data-ux-sticky]'), br = bar && bar.classList.contains('is-on') ? bar.getBoundingClientRect() : null, barTop = br && br.top > innerHeight / 2 ? br.top : innerHeight, barBottom = br && br.top <= innerHeight / 2 ? br.bottom : 0, bt = box ? box.getBoundingClientRect().top : null;
          return { under: bt !== null && scrollY > 0 && bt < barBottom - 1 ? Math.round(barBottom - bt) : 0, inside: box ? barTop - bt : null, tabIn: !!r && r.top >= -1 && r.bottom <= innerHeight + 1, focus: !!act && f === act, y: scrollY }; });
        const why = []; tabN++;
        if (m.inside === null || m.inside < 48) why.push(`the tab's content starts ${m.inside === null ? 'nowhere' : `${Math.round(m.inside)} px inside`} the viewport, under 48`);
        if (m.under) why.push(`the tab's content starts ${m.under} px under the sticky bar`);
        if (!m.tabIn && !m.y) why.push('the active tab is not wholly in view'); if (click && !m.focus) why.push('focus is not on the active tab');
        if (g === 'Plan' && (w === 1440 || w === 1280) && !cs && state === 'proposed' && m.y) why.push(`scrollY ${Math.round(m.y)}, not 0 (tabscrollall)`);
        if (why.length) { bad++; tabBad++; lines.push(`BAD ${op} ${g}${g === 'Plan' ? ` ${state}${cs ? ' non-default' : ''}` : ''} ${w}x${h} ${label}: ${why.join('; ')}`); } };
      for (const hr of seq) { await p.evaluate(h2 => { const a = [...document.querySelectorAll('[data-ia-tabs] nav.tabs a')].find(x => x.getAttribute('href') === h2), vis = a && a.getClientRects().length ? a : null;
          if (vis) vis.click(); else { const d = document.querySelector('[data-ia-tabs] .ux-tabmenu'); if (d) d.open = true; const l = d && [...d.querySelectorAll('nav a')].find(x => x.getAttribute('href') === h2); if (l) l.click(); else location.hash = h2; } }, hr);
        await check(`click ${hr}`, true); }
      await p.goBack(); await check('Back', false);
      await ctx.close(); }
    lines.push(`${tabBad ? 'BAD' : 'ok '} tab switches: ${tabN} switches measured (3 operators x 3 widths x the groups; Plan x 3 states x 2 cases), ${tabBad} bad`);
    if (!tabN) { lines.push('BAD no tab switch measured'); bad++; }
    if (ONLY === 'tabs') { await b.close(); console.log(lines.join('\n') + `\ntile rows measured: ${tilesN}`); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); } }
  if (ONLY !== 'hub') for (const op of Object.keys(SITES)) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) for (const dark of [false, true]) {
    for (const d of DECS[op]) if (ONLY !== 'sweep') await run(op, w, h, dark, `decision/${d}`, !PLANT);
    if (ONLY !== 'sweep') await run(op, w, h, dark, 'portfolio', !PLANT, 'inbox'); }
  /* D-IA.37: the width sweep, 761 up */
  const SW0 = [390, 600, 601, 760, 761, 800, 900, 1023, 1024, 1100, 1101, 1199, 1200, 1280, 1366, 1440, 1600, 1920];
  const SW = process.env.SHOTS_W ? process.env.SHOTS_W.split(',').map(Number) : SW0; /* SHOTS_W=390,761 narrows the sweep (debug) */
  SW_ORDER = ONLY === 'sweep' || !ONLY;
  if (ONLY === 'sweep' || !ONLY) for (const op of Object.keys(SITES)) for (const w of SW) for (const r of ['portfolio', 'plan', 'x-unknown', `decision/${DECS.longest[op]}`]) await run(op, w, 800, false, r, false);
  SW_ORDER = false;
  if (ONLY === 'sweep') { await b.close(); console.log(lines.join('\n') + `\ntile rows measured: ${tilesN}`); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); }
  if (ONLY === 'decision') { await b.close(); console.log(lines.join('\n') + `\ntile rows measured: ${tilesN}`); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); }
  for (const op of Object.keys(SITES)) for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) for (const dark of [false, true]) for (const r of ['portfolio', 'portfolio/outcomes', 'portfolio/demand-and-capacity', ...SITES[op].map(k => `site/${k}`)]) if (ONLY !== 'decision') await run(op, w, h, dark, r, !PLANT);
  if (ONLY === 'hub') { await b.close(); console.log(lines.join('\n') + `\ntile rows measured: ${tilesN}`); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); }
  for (const op of ['lakeside', 'harvest', 'metro']) for (const [w, h] of [[1440, 900], [1280, 720], [1200, 800], [900, 800], [390, 844]]) for (const dark of [false, true]) for (const r of ['plan', 'x-unknown']) await run(op, w, h, dark, r, true);
  for (const op of ['lakeside', 'harvest', 'metro']) for (const w of [390, 600]) for (const r of ['plan', 'x-unknown']) await run(op, w, 800, false, r, false);
  await b.close(); console.log(lines.join('\n') + `\ntile rows measured: ${tilesN}`); console.log(`shots: ${lines.length} measured, ${bad} bad`); process.exit(bad ? 1 : 0); })();
