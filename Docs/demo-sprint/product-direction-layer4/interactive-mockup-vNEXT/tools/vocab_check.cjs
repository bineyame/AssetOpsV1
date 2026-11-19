/* Banned user-facing vocabulary (owner, 19 Nov: "not using technical workds that should not be user facing").
   Scans tools/rendered-text.json (written by tools/render_text.cjs: every screen's visible text, accessible names and
   sampled evidence drawers, with the blue review bar removed as review tooling) for internal words: record and option
   codes, data keys, class codes, design and workflow codes, system and build terms, and words the design retired
   ("against plan" means target, OD-6). Fails (exit 1) on any hit on a screen built for this design (loop screens:
   Portfolio tabs, plan, sites, decisions, Financials) and on the shared chrome (rail, top bar, tabs, breadcrumbs,
   banners, footer) of every screen. The body of the kept v7.0 earlier views (pages not rebuilt for this design) is
   reported separately as a known residual and does not fail.
   Run: node tools/render_text.cjs && node tools/vocab_check.cjs        Plant test: VOCAB_PLANT=1 (see README). */
const fs = require('fs'), path = require('path');
const BANNED = [
  ['option or record code', /\b(?:KOB|BAT|KIS|MTO|MWEA|THIKA|KIRI|EMB|KAS|RUI)-[A-Z][A-Z0-9-]*\b|\b(?:F|ACT|WR|INC)-\d+\b/],
  ['data key (snake_case)', /\b[a-z]+_[a-z0-9_]+\b/],
  ['outcome category code', /\b(?:GROW_REVENUE|OPTIMIZE_COST(?:_AND_EFFICIENCY)?|PROTECT_ASSET(?:_AND_CAPITAL)?|ASSURE_PERFORMANCE(?:_AND_RETURNS)?|GROW|OPTIMIZE|PROTECT|ASSURE)\b/],
  ['class or state code', /\b[A-Z]{3,}_[A-Z_]+\b|\b(?:EXPOSURE|MODELLED|RECOMMENDED|REJECTED|RECORDED|DERIVED|MEASURED|ESTIMATED|INSUFFICIENT|CANDIDATE|SYSTEM)\b/],
  ['design or workflow code', /\b(?:L[1-7]|B[1-3]|CH[1-5]|G-?F?\d|OD-\d+|D1[0-9]|Q-[A-Z]\d|W[1-9]|S[1-6]-\d+)\b/],
  ['system or build term', /\b(?:registry|observer|evaluator|manifest|fixtures?|oracle|canonical|schema|payload|endpoint|API|JSON|YAML|tenant|slice|spec|specification|backend|frontend|idempoten\w*|enum|undefined|NaN|null)\b|\[object|\.py\b|\.js\b|[<>]=/i],
  ['design jargon', /\b(?:levers?|evidence class(?:es)?|factor structure|leaf factors?|structure evaluator|evaluated through|replay(?:ed|s)?|composes|disposition|admissib\w+|guardrails?|horizon)\b|Σ/i],
  ['design jargon (review, wave 1)', /\b(?:counterfactual|bound check|obligations check|switches|what if|explained by factors|Emulated)\b/i],
  ['design jargon (review, round 2)', /\b(?:switch(?:es)?|obligations?|rights)\b/i],
  ['design jargon (review, round 3)', /\b(?:factors?|protect measures?|candidate running|necessary running|item state|item released|rate-card|ledger to invoice)\b/i],
  ['asset or record code', /\b(?:GEN|INV|BAT|CH|CN|PM)-[A-Z0-9]{1,4}(?:-\d+)?\b/],
  ['retired word: plan used for a target (OD-6)', /\b(?:against|off|to|versus|vs\.?|from|than) (?:the )?plan\b(?! (?:for|item|items|approval|beside))|\bActual against plan\b/i],
];
function scan(recs) {
  const hits = [], preserved = {};
  for (const r of recs) {
    const texts = r.loop ? [['screen', r.text, true], ...r.drawers.map((d, i) => [`drawer ${i + 1}`, d, true])]
      : [['chrome', r.chrome || '', true], ['earlier-view body', r.text, false]];
    for (const [where, t, fails] of texts) for (const [kind, re] of BANNED) {
      const g = new RegExp(re.source, re.flags.includes('g') ? re.flags : re.flags + 'g'); let m;
      while ((m = g.exec(t))) { const h = { op: r.op, id: r.id, where, kind, match: m[0], at: t.slice(Math.max(0, m.index - 60), m.index + m[0].length + 40) };
        if (!fails) preserved[r.id] = (preserved[r.id] || 0) + 1; else hits.push(h); }
    }
  }
  return { hits, preserved };
}
let recs = JSON.parse(fs.readFileSync(path.join(__dirname, 'rendered-text.json'), 'utf8'));
if (process.env.VOCAB_PLANT) { recs = recs.map(r => r.id === 'portfolio' && r.op === 'lakeside' ? { ...r, text: r.text + ' Actual against plan from the factor registry (KOB-STOPSOC)' } : r); }
const { hits, preserved } = scan(recs);
const byKind = hits.reduce((a, h) => (a[h.kind] = (a[h.kind] || 0) + 1, a), {});
const out = { screens_scanned: recs.length, hits: hits.length, by_kind: byKind, earlier_view_body_hits_not_failing: Object.values(preserved).reduce((a, b) => a + b, 0), earlier_view_routes: Object.keys(preserved).length, first: hits.slice(0, +(process.env.VOCAB_SHOW || 25)) };
fs.writeFileSync(path.join(__dirname, 'vocab-results.json'), JSON.stringify({ ...out, all: hits }, null, 1));
console.log(JSON.stringify(out, null, 1));
process.exit(hits.length ? 1 : 0);
