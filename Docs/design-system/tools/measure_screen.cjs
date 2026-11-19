// Design-quality metrics for one screen in a real browser (UI/UX guide §10.3, gate G3).
// usage: node measure_screen.cjs <file-or-url> [width] [height] [dark] ["Section title|Another"]
// Needs /opt/assetecon/tools/pw/env.sh sourced (PW, CHROME) and LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH.
// Prints one JSON line. Review tooling (.reviewbar / [data-review]) is excluded from content counts.
const { chromium } = require(process.env.PW);
(async () => {
  const [src, w = '1440', h = '900', dark, names = 'Needs a decision|Factors needing attention'] = process.argv.slice(2);
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  const p = await b.newPage({ viewport: { width: +w, height: +h }, colorScheme: dark === 'dark' ? 'dark' : 'light' });
  const errors = []; p.on('pageerror', e => errors.push(e.message));
  await p.goto(src); await p.waitForTimeout(800);
  const r = await p.evaluate(({ names, vh }) => {
    const root = document.querySelector('main') || document.body;
    const vis = e => e.offsetParent !== null && !e.closest('.reviewbar,[data-review]');
    const top = e => Math.round(e.getBoundingClientRect().top + scrollY);
    const sections = {};
    for (const n of names.split('|')) {
      const el = [...root.querySelectorAll('h1,h2,h3,summary')].find(e => e.textContent.trim().startsWith(n));
      sections[n] = el ? { y: top(el), aboveFold: top(el) < vh } : null;
    }
    const sizes = {}; let under12 = 0, texts = 0;
    for (const e of root.querySelectorAll('*')) {
      if (!vis(e) || ![...e.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) continue;
      const fs = parseFloat(getComputedStyle(e).fontSize); sizes[fs] = (sizes[fs] || 0) + 1; texts++; if (fs < 12) under12++;
    }
    const chipLike = e => { const c = getComputedStyle(e); return c.backgroundColor !== 'rgba(0, 0, 0, 0)' || parseFloat(c.borderTopWidth) > 0; };
    const chips = [...root.querySelectorAll('.badge,.ec,.chip,.ux-mark,.ux-chip,.dv')].filter(e => vis(e) && chipLike(e)).length; /* styled as a chip: a fill or a border */
    /* WCAG 1.4.3 text contrast against the first opaque background behind it (4.5:1; 3:1 for text of 24 px, or 18.66 px bold) */
    const rgb = c => (c.match(/[\d.]+/g) || []).map(Number), lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const bgOf = e => { for (let x = e; x; x = x.parentElement) { const c = rgb(getComputedStyle(x).backgroundColor); if (c.length >= 3 && (c[3] === undefined || c[3] > 0.5)) return c; } return [255, 255, 255]; };
    const low = [];
    for (const e of root.querySelectorAll('*')) {
      if (!vis(e) || e.closest('.vh,.sr-only') || ![...e.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) continue;
      const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
      const L1 = lum(rgb(cs.color)), L2 = lum(bgOf(e)), ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05), fs = parseFloat(cs.fontSize), big = fs >= 24 || (fs >= 18.66 && +cs.fontWeight >= 700);
      if (ratio < (big ? 3 : 4.5)) low.push(`${ratio.toFixed(2)}: ${e.textContent.trim().slice(0, 40)}`);
    }
    const caveats = (root.innerText.match(/not yet tested on your recorded data/gi) || []).length;
    return { height: document.documentElement.scrollHeight, width: document.documentElement.scrollWidth, sections,
      fontSizes: Object.keys(sizes).length, sizes, textElements: texts, under12, chips, caveats, lowContrast: low.length, lowContrastSamples: low.slice(0, 6) };
  }, { names, vh: +h });
  console.log(JSON.stringify({ src, viewport: `${w}x${h}${dark === 'dark' ? ' dark' : ''}`, errors: errors.length, ...r,
    horizontalOverflow: r.width > +w }));
  await b.close();
})();
