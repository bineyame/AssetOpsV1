#!/usr/bin/env node
// W1-F5b all-26 audit index. Reads every evidence.json that `tools/w1-fidelity-evidence.mjs` wrote under
// <root> (one folder per walkthrough part), and writes <root>/index.html and <root>/audit.json: each of the 26
// W1 screens with its app-vs-mock pairs at 1440 and 390, the panel-count and title match, horizontal overflow,
// and each panel's app/mock height ratio. Optional <root>/overages.json maps "screen|case|width|panel title" (or
// "screen|*|*|panel title") to the honest reason a panel stays above ~1.3x the mock.
//
// Usage: node tools/w1-fidelity-audit-index.mjs <root>
import fs from 'node:fs';
import path from 'node:path';

const SCREENS = [
  ['sites', 'Sites'], ['mini', 'Site overview'], ['foundation', 'Foundation · Site model'],
  ['readiness', 'Foundation · Readiness'], ['sld', 'Foundation · Single line diagram'], ['evidence', 'Evidence'],
  ['evidence-analysis', 'Evidence · Analysis'], ['dispatch', 'Performance · Dispatch'], ['analysis', 'Performance · Analysis'],
  ['finding', 'Finding'], ['finding-evidence', 'Finding · Evidence'], ['finding-history', 'Finding · History'],
  ['sitefindings', 'Site findings'], ['financials', 'Financials'], ['assumptions', 'Financials · Assumptions'],
  ['recommendation', 'Finding · Recommendation'], ['changes', 'Foundation · Change & effect'], ['action-overview', 'Action'],
  ['action-execution', 'Action · Execution'], ['action-history', 'Action · History'], ['action-plan', 'Action · Plan'],
  ['action-evidence', 'Action · Evidence'], ['verification', 'Action · Verification'], ['sitework', 'Work · Actions'],
  ['health', 'Health'], ['asset', 'Health · Battery'],
];
const LIMIT = 1.3;

const root = path.resolve(process.argv[2] ?? '.');
const files = [];
(function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name === 'evidence.json') files.push(full);
  }
})(root);
const overages = fs.existsSync(path.join(root, 'overages.json'))
  ? JSON.parse(fs.readFileSync(path.join(root, 'overages.json'), 'utf8'))
  : {};

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const rel = (file) => path.relative(root, file).split(path.sep).join('/');

const rows = [];
for (const file of files) {
  const ev = JSON.parse(fs.readFileSync(file, 'utf8'));
  const dir = path.dirname(file);
  for (const p of ev.pairs ?? []) {
    const width = String(p.viewport ?? '').split('x')[0];
    const appTitles = p.app?.titles ?? [];
    const mockTitles = p.mock?.titles ?? [];
    const panels = (p.app?.panels ?? []).map((a, i) => {
      const m = (p.mock?.panels ?? [])[i];
      const ratio = m && m.h > 0 ? a.h / m.h : null;
      const key = `${p.screen}|${p.case ?? ''}|${width}|${a.title}`;
      const wild = `${p.screen}|*|*|${a.title}`;
      return { title: a.title, app: a.h, mock: m?.h ?? null, ratio, reason: overages[key] ?? overages[wild] ?? null };
    });
    rows.push({
      screen: p.screen, case: p.case || 'default', width, part: rel(dir), revision: ev.revision,
      appUrl: p.app_url, mockHash: p.mock_hash,
      appImage: p.app_image ? rel(path.join(dir, p.app_image)) : null,
      mockImage: p.mock_image ? rel(path.join(dir, p.mock_image)) : null,
      appCount: appTitles.length, mockCount: mockTitles.length,
      countMatch: appTitles.length === mockTitles.length,
      appTitles, mockTitles,
      overflow: p.app?.overflowX ?? null,
      panels,
      maxRatio: panels.reduce((mx, x) => (x.ratio !== null && x.ratio > mx ? x.ratio : mx), 0),
    });
  }
}

const byScreen = new Map(SCREENS.map(([id]) => [id, []]));
for (const r of rows) (byScreen.get(r.screen) ?? byScreen.set(r.screen, []).get(r.screen)).push(r);
for (const list of byScreen.values()) list.sort((a, b) => a.case.localeCompare(b.case) || Number(b.width) - Number(a.width));

function verdict(list) {
  if (list.length === 0) return { word: 'Not captured', tone: 'red' };
  const widths = new Set(list.map((r) => r.width));
  if (!widths.has('1440') || !widths.has('390')) return { word: 'One width only', tone: 'red' };
  if (list.some((r) => !r.countMatch)) return { word: 'Panel count differs', tone: 'red' };
  if (list.some((r) => r.overflow !== 0)) return { word: 'Sideways overflow', tone: 'red' };
  const over = list.flatMap((r) => r.panels.filter((x) => x.ratio !== null && x.ratio > LIMIT));
  if (over.some((x) => !x.reason)) return { word: 'Taller than mock, no reason stated', tone: 'amber' };
  if (over.length > 0) return { word: 'Matches; some panels taller, reasons stated', tone: 'amber' };
  return { word: 'Matches', tone: 'green' };
}

const summary = SCREENS.map(([id, name], i) => ({ n: i + 1, id, name, ...verdict(byScreen.get(id)), pairs: byScreen.get(id).length }));
fs.writeFileSync(path.join(root, 'audit.json'), JSON.stringify({ generated: new Date().toISOString(), limit: LIMIT, summary, rows }, null, 1));

const fmt = (r) => (r === null ? '–' : `${r.toFixed(2)}x`);
const css = `
:root{--bg:#f6f8fb;--panel:#fff;--ink:#1d2939;--muted:#5d6b82;--line:#dfe5ee;--green:#1d7f4e;--amber:#9a6200;--red:#b42318;--accent:#245ac0}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#11161e;--panel:#18202b;--ink:#e6ebf2;--muted:#9aa7b8;--line:#2a3442;--green:#4cc38a;--amber:#e3a64a;--red:#f07167;--accent:#7aa7ff}}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,sans-serif}
main{max-width:1500px;margin:0 auto;padding:24px 16px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:0}p.lead{color:var(--muted);margin:0 0 16px;max-width:900px}
table{border-collapse:collapse;width:100%;background:var(--panel)}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{font-size:12px;color:var(--muted);font-weight:600}
.tone-green{color:var(--green);font-weight:600}.tone-amber{color:var(--amber);font-weight:600}.tone-red{color:var(--red);font-weight:600}
section.screen{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:16px;margin:18px 0}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0 18px}.pair figure{margin:0}.pair img{width:100%;border:1px solid var(--line);border-radius:4px}
.pair figcaption{font-size:12px;color:var(--muted)}.pair.narrow{grid-template-columns:repeat(2,minmax(0,390px))}
.case{border-top:1px solid var(--line);padding-top:10px;margin-top:10px}.meta{font-size:12px;color:var(--muted);word-break:break-all}
a{color:var(--accent)}.wrap{overflow-x:auto}
@media (max-width:760px){.pair,.pair.narrow{grid-template-columns:1fr}}`;

let html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>W1 Screen Audit</title><style>${css}</style></head><body><main>
<h1>W1 screen audit: app beside mock-up</h1>
<p class="lead">All 26 W1 site screens, each captured in the app and in the v69 mock-up at desktop (1440 px) and phone (390 px) width, in every state the slices captured. For each capture: whether the app shows the same number of panels with the same titles as the mock-up, whether the page scrolls sideways, and how tall each app panel is compared with the mock-up's (above ${LIMIT}x is flagged; a stated reason follows where the extra height is real content). Mock-up sample values differ from real data by design: judge layout, order and honest gaps.</p>
<div class="wrap"><table><thead><tr><th>#</th><th>Screen</th><th>Result</th><th>Captures</th><th>Tallest panel vs mock</th></tr></thead><tbody>`;
for (const s of summary) {
  const list = byScreen.get(s.id);
  const mx = list.reduce((m, r) => Math.max(m, r.maxRatio), 0);
  html += `<tr><td>${s.n}</td><td><a href="#${s.id}">${esc(s.name)}</a> <span class="meta">${s.id}</span></td><td class="tone-${s.tone}">${esc(s.word)}</td><td>${s.pairs}</td><td>${list.length ? fmt(mx) : '–'}</td></tr>`;
}
html += `</tbody></table></div>`;

for (const s of summary) {
  const list = byScreen.get(s.id);
  html += `<section class="screen" id="${s.id}"><h2>${s.n}. ${esc(s.name)} <span class="meta">${s.id}</span> · <span class="tone-${s.tone}">${esc(s.word)}</span></h2>`;
  if (list.length === 0) html += `<p class="tone-red">No capture found for this screen.</p>`;
  for (const r of list) {
    html += `<div class="case"><strong>${esc(r.case)} · ${r.width} px</strong> · panels app ${r.appCount} / mock ${r.mockCount} <span class="tone-${r.countMatch ? 'green' : 'red'}">${r.countMatch ? 'same' : 'different'}</span> · sideways overflow <span class="tone-${r.overflow === 0 ? 'green' : 'red'}">${r.overflow ?? 'not measured'}</span>
<div class="meta">${esc(r.appUrl)} · mock ${esc(r.mockHash)} · ${esc(r.part)} · rev ${esc(r.revision)}</div>
<div class="wrap"><table><thead><tr><th>Panel</th><th>App height</th><th>Mock height</th><th>Ratio</th><th>Reason if taller</th></tr></thead><tbody>`;
    for (const x of r.panels) {
      const tone = x.ratio === null ? '' : x.ratio > LIMIT ? (x.reason ? 'amber' : 'red') : 'green';
      html += `<tr><td>${esc(x.title)}</td><td>${x.app}</td><td>${x.mock ?? '–'}</td><td class="tone-${tone}">${fmt(x.ratio)}</td><td>${esc(x.reason ?? '')}</td></tr>`;
    }
    html += `</tbody></table></div>`;
    if (!r.countMatch) html += `<p class="meta">App titles: ${esc(r.appTitles.join(' | '))}<br>Mock titles: ${esc(r.mockTitles.join(' | '))}</p>`;
    html += `<div class="pair${r.width === '390' ? ' narrow' : ''}"><figure><a href="${esc(r.appImage)}"><img loading="lazy" src="${esc(r.appImage)}" alt="App, ${esc(s.name)}, ${esc(r.case)}, ${r.width} px"></a><figcaption>App</figcaption></figure><figure><a href="${esc(r.mockImage)}"><img loading="lazy" src="${esc(r.mockImage)}" alt="Mock-up, ${esc(s.name)}, ${r.width} px"></a><figcaption>Mock-up</figcaption></figure></div></div>`;
  }
  html += `</section>`;
}
html += `</main></body></html>`;
fs.writeFileSync(path.join(root, 'index.html'), html);
const bad = summary.filter((s) => s.tone === 'red');
console.log(`audit: ${rows.length} pairs, ${summary.filter((s) => s.tone === 'green').length} match, ${summary.filter((s) => s.tone === 'amber').length} taller, ${bad.length} failing${bad.length ? ': ' + bad.map((s) => `${s.id} (${s.word})`).join(', ') : ''}`);
