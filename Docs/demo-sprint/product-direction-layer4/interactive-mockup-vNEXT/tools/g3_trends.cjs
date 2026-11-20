/* DS1m G3 capture (D-DS1.15, supersedes spec 9.4 and MB7): Portfolio overview (3 operators) and Site (Kobo, Thika, Ruiru)
   x {1440x900, 1280x720, 390x844} x {light, dark} = 36 shots. Asserts what the trend slots say and that it is visible, by width.
   Usage (through tools/heavy-slot.sh, env.sh sourced): node tools/g3_trends.cjs <index.html> <outdir> */
const { chromium } = require(process.env.PW); const fs = require('fs'), path = require('path');
const [idx, out] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
const PAGES = [['lakeside', 'portfolio'], ['harvest', 'portfolio'], ['metro', 'portfolio'], ['lakeside', 'site/kobo'], ['harvest', 'site/thika'], ['metro', 'site/ruiru']];
const VP = [[1440, 900], [1280, 720], [390, 844]];
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const rows = []; let fail = 0;
  for (const [op, route] of PAGES) for (const [w, h] of VP) for (const theme of ['light', 'dark']) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: theme });
    await ctx.addInitScript(([o, t]) => { try { sessionStorage.setItem('l4-op', o); localStorage.setItem('l4-theme', t); } catch (e) {} }, [op, theme]);
    const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.goto('file://' + path.resolve(idx) + '#/' + route); await p.waitForTimeout(700);
    const m = await p.evaluate(([w, h, route]) => { const H = innerHeight, site = route.startsWith('site/'), cost = OPS[sessionStorage.getItem('l4-op')].kind === 'cost';
      const root = document.querySelector(site ? '#app .ux-kpis' : '#app .ux-overview') || document.body, tiles = [...root.querySelectorAll('.ux-kpi')].filter(k => k.querySelector('.ux-trend'));
      const inside = (a, c) => a.left >= c.left - 0.5 && a.right <= c.right + 0.5 && a.top >= c.top - 0.5 && a.bottom <= c.bottom + 0.5;
      const slots = [...root.querySelectorAll('.ux-kpi .ux-trend')].map((t, i) => { const text = t.textContent.trim(), r = t.getBoundingClientRect(), k = t.closest('.ux-kpi'), sub = t.closest('.ux-kpi-s') || t, sr = sub.getBoundingClientRect(), cs = getComputedStyle(sub);
        const mm = text.match(/[−+]?\$[\d,]+/); let fr = null;
        if (mm) { const idx = t.textContent.indexOf(mm[0]); const walker = document.createTreeWalker(t, NodeFilter.SHOW_TEXT); let n, off = 0; while ((n = walker.nextNode())) { if (idx >= off && idx < off + n.length) { const rg = document.createRange(); rg.setStart(n, idx - off); rg.setEnd(n, Math.min(n.length, idx - off + mm[0].length)); const q = rg.getBoundingClientRect(); fr = { left: q.left, right: q.right, top: q.top, bottom: q.bottom, width: q.width }; break; } off += n.length; } }
        const sp = t.querySelector('svg.ux-spark'), spw = sp ? sp.getBoundingClientRect().width : 0;
        const stOk = !!sp === !t.hasAttribute('data-measure');
        const form = stOk && (i === 0 && cost ? t.getAttribute('data-measure') === 'monthly-cost' && !sp && /^Monthly cost (up \$[\d,]+|down \$[\d,]+|unchanged) against Sep$/.test(text) : !t.hasAttribute('data-measure') && !!sp && /^[−+-]?\$[\d,]+ against Sep$/.test(text));
        return { text, form, signed: !!sp, spw, hasFig: !!fr, subShown: cs.display !== 'none' && sr.width > 0 && sr.height > 0,
          visible: t.offsetParent !== null && r.width > 0 && r.height > 0 && getComputedStyle(t).visibility !== 'hidden', inTile: inside(r, k.getBoundingClientRect()), firstViewport: r.top >= 0 && r.bottom <= H,
          subUnclipped: sub.scrollWidth <= sub.clientWidth, figInSub: !!fr && fr.width > 0 && fr.left >= sr.left - 0.5 && fr.right <= sr.right + 0.5 && fr.top >= sr.top - 0.5 && fr.bottom <= sr.bottom + 0.5, endsSep: /against Sep$/.test(text) }; });
      return { theme: document.documentElement.getAttribute('data-theme'), slots,
        clipped: [...document.querySelectorAll('.ux-kpi')].flatMap(k => { const kr = k.getBoundingClientRect(); return [...k.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden' && !inside(r, kr); }).map(e => e.className || e.tagName); }),
        hScroll: document.documentElement.scrollWidth > innerWidth }; }, [w, h, route]);
    const reasons = []; if (errs.length) reasons.push('page errors ' + errs.length); if (m.theme !== theme) reasons.push(`theme ${m.theme}`); if (m.clipped.length) reasons.push('clipped ' + m.clipped.join(',')); if (m.hScroll) reasons.push('sideways scroll');
    if (m.slots.length !== 2 || !m.slots.every(s => s.form)) reasons.push(`form: ${m.slots.length} slots, ${m.slots.filter(s => !s.form).length} not in an 8a form`);
    m.slots.forEach((s, i) => { const f = c => { if (!c) reasons.push(`slot ${i + 1}: ${c === false ? '' : ''}`); };
      const need = (c, what) => { if (!c) reasons.push(`slot ${i + 1} ${what}`); };
      if (w === 1440) { need(s.visible, 'not visible'); need(s.inTile, 'not inside its tile'); need(s.firstViewport, 'not in the first viewport'); if (s.signed) need(s.spw > 0, 'sparkline width 0'); need(s.subUnclipped, 'text clipped'); }
      else if (w === 1280) { need(s.subShown, 'sub-line not displayed'); if (s.signed) need(s.spw > 0, 'sparkline width 0'); need(s.figInSub, 'figure outside the sub-line'); }
      else { need(s.subShown, 'sub-line not displayed'); if (s.signed) need(s.spw === 0, 'sparkline drawn on a phone'); need(s.figInSub, 'figure outside the sub-line'); need(s.endsSep && s.subUnclipped, 'text does not end "against Sep" unclipped'); } });
    const pass = reasons.length === 0; if (!pass) fail++;
    const file = path.join(out, `${route.replace('/', '-')}-${op}-${w}x${h}-${theme}.png`); await p.screenshot({ path: file, fullPage: w < 600 });
    rows.push({ route, op, w, h, theme, pass, reasons, ...m, file }); await ctx.close(); }
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(rows, null, 1));
  for (const r of rows) console.log(`${r.pass ? 'PASS' : 'FAIL'} ${r.route} ${r.op} ${r.w}x${r.h} ${r.theme} ${r.pass ? r.slots.map(s => s.text).join(' | ') : r.reasons.join('; ')}`);
  console.log(`${rows.length - fail} of ${rows.length} pass`); await b.close(); process.exit(fail ? 1 : 0); })();
