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
    const caveats = (root.innerText.match(/not yet tested on your recorded data/gi) || []).length;
    return { height: document.documentElement.scrollHeight, width: document.documentElement.scrollWidth, sections,
      fontSizes: Object.keys(sizes).length, sizes, textElements: texts, under12, chips, caveats };
  }, { names, vh: +h });
  console.log(JSON.stringify({ src, viewport: `${w}x${h}${dark === 'dark' ? ' dark' : ''}`, errors: errors.length, ...r,
    horizontalOverflow: r.width > +w }));
  await b.close();
})();
