/* Copy check (UI/UX guide §7.7; copy review round 4): faults that word replacements can create, read from the rendered
   prose segments of every loop screen and sampled evidence drawer (tools/rendered-text.json, written by render_text.cjs):
   1. a doubled word ("service service", "the the");
   2. a phrase repeated right after itself ("hours without backup supply with no backup supply");
   3. a space before an apostrophe or punctuation ("mini-grid ’s", "word ,");
   4. a doubled sign ("+ +$", "− −").
   Run: node tools/render_text.cjs && node tools/copy_check.cjs     Plant test: COPY_PLANT=1 (one example of each; must fail). */
const fs = require('fs'), path = require('path');
let recs = JSON.parse(fs.readFileSync(path.join(__dirname, 'rendered-text.json'), 'utf8'));
if (process.env.COPY_PLANT) recs = recs.map(r => r.id === 'portfolio' && r.op === 'lakeside' ? { ...r, segments: [...r.segments, 'Fails the evening service service limit', 'Hours without backup supply with no backup supply: 0 h', 'How a mini-grid ’s economics are built', 'Worked sum: $883 + +$19.68', 'Energy matches the occupancy model (0 more buses.6%)'] } : r);
const RULES = [
  ['doubled word', /\b([A-Za-z]{2,})[ ]+\1\b/i],
  ['phrase repeated after itself', /\b([A-Za-z]{4,} [A-Za-z]{4,})\b[^¶]{0,24}?\b\1\b/i], /* ¶ marks a line break or a note under a label */
  ['space before an apostrophe or punctuation', /[A-Za-z)]\s+(?:[’'](?=s\b)|[,;:!?](?=\s|$)|\.(?=\s|$))/],
  ['doubled sign', /(?:^|\s)[+−-]\s*[+−-]\s?\$?\d/],
  ['number broken by words (a rewrite rule split a figure; REVIEW-decision-page L7)', /\b\d+ [a-z]+(?: [a-z]+){0,3}\.\d/],
];
const ALLOW = [/\b(\d+)\s+\1\b/, /\bthat that\b/i];
const hits = [];
for (const r of recs) { if (!r.loop) continue;
  for (const t of r.segments || []) for (const [kind, re] of RULES) { const m = t.match(re); if (m && !ALLOW.some(a => a.test(m[0]))) hits.push({ op: r.op, id: r.id, kind, match: m[0], at: t.slice(0, 160) }); } }
const uniq = [...new Map(hits.map(h => [h.kind + '|' + h.at, h])).values()];
console.log(JSON.stringify({ planted: !!process.env.COPY_PLANT, segments: recs.reduce((a, r) => a + (r.loop ? (r.segments || []).length : 0), 0), hits: uniq.length, by_kind: uniq.reduce((a, h) => (a[h.kind] = (a[h.kind] || 0) + 1, a), {}), first: uniq.slice(0, 40) }, null, 1));
process.exit(uniq.length ? 1 : 0);
