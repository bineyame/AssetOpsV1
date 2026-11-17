import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const dir = new URL('./', import.meta.url);
/* Layer 4 rev 4: the re-based v7.0 sources (tools/rebase_v70.py), then fixtures.js (generated from the demo scenario
   file, private oracle removed) and the loop-*.js modules. One standalone index.html; opens with file:// or a static server. */
const css = ['mockups.css', 'portfolio.css', 'outcomes.css', 'economics.css'].map(f => readFileSync(new URL(f, dir), 'utf8')).join('\n');
const js = ['portfolio.js', 'outcomes.js', 'screens.js', 'fixtures.js', 'loop-core.js', 'loop-decisions.js', 'loop-protect.js', 'loop-portfolio.js', 'loop-site.js', 'loop-init.js'].map(f => readFileSync(new URL(f, dir), 'utf8')).join('\n');
if (/"oracle"\s*:/.test(js)) throw new Error('private oracle found in bundle');
const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AssetEcon · Layer 4 mock-up</title><style>${css}</style></head><body><div id="app"></div><div id="overlay"></div><script>${js}</script></body></html>`;
writeFileSync(new URL('index.html', dir), html);
console.log(`Built standalone Layer 4 mock-up: ${fileURLToPath(new URL('index.html', dir))}`);
