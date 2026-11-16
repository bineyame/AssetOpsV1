import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const dir = new URL('./', import.meta.url);
/* vNEXT: adds decisions.css, fixtures.js (generated from the Layer 4 manifest) and decisions.js after the v7.0 sources. */
const css = ['mockups.css', 'portfolio.css', 'outcomes.css', 'decisions.css'].map(f => readFileSync(new URL(f, dir), 'utf8')).join('\n');
const js = ['portfolio.js', 'outcomes.js', 'screens.js', 'fixtures.js', 'decisions.js'].map(f => readFileSync(new URL(f, dir), 'utf8')).join('\n');
const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AssetEcon · vNEXT decision mock-up</title><style>${css}</style></head><body><div id="app"></div><div id="overlay"></div><script>${js}</script></body></html>`;
writeFileSync(new URL('index.html', dir), html);
console.log(`Built standalone vNEXT prototype: ${fileURLToPath(new URL('index.html', dir))}`);
