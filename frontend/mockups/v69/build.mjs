import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const dir = new URL('./', import.meta.url);
const css = readFileSync(new URL('mockups.css', dir), 'utf8') + '\n' + readFileSync(new URL('portfolio.css', dir), 'utf8');
const js = readFileSync(new URL('portfolio.js', dir), 'utf8') + '\n' + readFileSync(new URL('screens.js', dir), 'utf8');
const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AssetOps · v6.9 Architecture Screen Review</title><style>${css}</style></head><body><div id="app"></div><div id="overlay"></div><script>${js}</script></body></html>`;
writeFileSync(new URL('index.html', dir), html);
console.log(`Built standalone screen prototype: ${fileURLToPath(new URL('index.html', dir))}`);
