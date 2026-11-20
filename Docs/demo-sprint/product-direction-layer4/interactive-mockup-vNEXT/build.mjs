import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const dir = new URL('./', import.meta.url);
/* Layer 4 rev 4: the re-based v7.0 sources (tools/rebase_v70.py), then fixtures.js (generated from the demo scenario
   file, private oracle removed) and the loop-*.js modules. One standalone index.html; opens with file:// or a static server. */
/* UI/UX guide (Docs/design-system/uiux-guide.md §4.2): one type scale. Every px font size in the sheets is mapped to the
   nearest step of 12/13/14/16/20/24/32 px at build time, never below 12 px, so the re-based v7.0 sheets stay byte-identical to
   their source while the page renders one scale. ux.css (loaded last) holds the guide's components. */
const STEP = px => px < 12.5 ? 12 : px < 13.5 ? 13 : px < 15 ? 14 : px < 18 ? 16 : px < 22 ? 20 : px <= 28 ? 24 : 32;
const toScale = t => t.replace(/font-size:\s*([\d.]+)px/g, (m, n) => `font-size:${STEP(+n)}px`).replace(/(font:\s*(?:\d{3}\s+)?)([\d.]+)px/g, (m, a, n) => `${a}${STEP(+n)}px`);
const css = toScale(['mockups.css', 'portfolio.css', 'outcomes.css', 'economics.css', 'theme.css', 'ux.css', 'ia.css', 'brand.css'].map(f => readFileSync(new URL(f, dir), 'utf8')).join('\n'));
const js = ['portfolio.js', 'outcomes.js', 'screens.js', 'fixtures.js', 'loop-core.js', 'loop-decisions.js', 'loop-protect.js', 'loop-portfolio.js', 'loop-site.js', 'loop-ux.js', 'ia-routes.js', 'ia-shapes.js', 'loop-init.js'].map(f => readFileSync(new URL(f, dir), 'utf8')).join('\n');
if (/"oracle"\s*:/.test(js)) throw new Error('private oracle found in bundle');
const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AssetEcon · Layer 4 mock-up</title><style>${css}</style></head><body><div id="app"></div><div id="overlay"></div><script>${js}</script></body></html>`;
writeFileSync(new URL('index.html', dir), html);
console.log(`Built standalone Layer 4 mock-up: ${fileURLToPath(new URL('index.html', dir))}`);
