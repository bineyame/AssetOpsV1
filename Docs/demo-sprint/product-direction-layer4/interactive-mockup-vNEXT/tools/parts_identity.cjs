/* IA-1 byte identity (spec §6 item 2, D-IA.20, D-IA.22): each legacy function before its split (a base index.html) and after it
   (this tree's index.html), byte for byte, with UX_QN reset to 0 before each call, in the default state and under
   ?state=no-recommendation: planScreen() for each operator and switch case (planParts), uxOverview(op) for each operator
   (uxOverviewParts), siteOverview(sk) for each Site of each operator (siteOverviewP, uxSiteParts); from IA-1c decisionScreen(id).
   The one named fix (D-IA.22: the Site sticky's "Decide" targets the queue's own primary) is reported apart: a Site case whose only
   difference is inside its leading .ux-dsticky bar is "sticky only"; any other difference fails.
   Run: node tools/parts_identity.cjs <base index.html> [<new index.html>] */
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const { JSDOM, VirtualConsole } = require(['/opt/assetecon/AssetOpsV1/frontend/node_modules/jsdom', path.resolve(__dirname, '../../../../../frontend/node_modules/jsdom')].find(p => { try { require.resolve(p); return true; } catch (e) { return false; } }));
const baseFile = process.argv[2], newFile = process.argv[3] || path.join(__dirname, '..', 'index.html');
if (!baseFile) { console.error('usage: node tools/parts_identity.cjs <base index.html> [<new index.html>]'); process.exit(2); }
const CASES = { lakeside: [[5000, true], [5000, false], [6500, true], [6500, false]].map(([b, l]) => ({ budget: b, loi: l })), harvest: [{ agg: true }, { agg: false }], metro: [{ tou: true }, { tou: false }] };
const boot = (file, op, search) => new JSDOM(fs.readFileSync(file, 'utf8'), { virtualConsole: new VirtualConsole(), runScripts: 'dangerously', pretendToBeVisual: true, url: `http://x/${search}#/not-a-route`,
  beforeParse(w) { w.sessionStorage.setItem('l4-op', op); w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; } }).window;
const h = x => crypto.createHash('sha256').update(x).digest('hex').slice(0, 16);
const noSticky = x => x.replace(/^<div class="ux-dsticky"[\s\S]*?<\/div>(?=<p class="headline)/, '');
const stickyOf = x => (x.match(/^<div class="ux-dsticky"[\s\S]*?<\/div>(?=<p class="headline)/) || [''])[0];
const count = { same: 0, sticky: 0, bad: 0 }, by = {}, diffs = [];
for (const search of ['', '?state=no-recommendation']) for (const op of Object.keys(CASES)) {
  const A = boot(baseFile, op, search), B = boot(newFile, op, search), st = search ? 'no-recommendation' : 'default';
  const call = (W, expr) => W.eval(`setOp(${JSON.stringify(op)});UX_QN=0;${expr}`);
  const has = (W, f) => W.eval(`typeof ${f} === 'function'`);
  const jobs = [...CASES[op].map(c => ['planScreen', JSON.stringify(c), `Object.assign(LS,${JSON.stringify(c)});planScreen()`]), ['uxOverview', op, `uxOverview(${JSON.stringify(op)})`],
    ...A.eval(`OPS[${JSON.stringify(op)}].sites`).map(sk => ['siteOverview', sk, `siteOverview(${JSON.stringify(sk)})`]),
    ...(has(A, 'decisionScreen') && has(B, 'uxDecisionSlots') ? A.eval(`DEC.filter(d => OPS[${JSON.stringify(op)}].sites.includes(d.site)).map(d => d.id)`).map(id => ['decisionScreen', id, `decisionScreen(${JSON.stringify(id)})`]) : [])];
  for (const [fn, arg, expr] of jobs) { const a = call(A, expr), b = call(B, expr); let v;
    if (a === b) { v = 'byte-identical'; count.same++; }
    else if (fn === 'siteOverview' && noSticky(a) === noSticky(b)) { v = 'sticky only'; count.sticky++; diffs.push(`${st} · ${op} · ${arg}\n    before: ${stickyOf(a)}\n    after:  ${stickyOf(b)}`); }
    else { v = 'DIFFERS'; count.bad++; let i = 0; while (a[i] === b[i]) i++; diffs.push(`${st} · ${fn} · ${arg} DIFFERS at ${i}: before "${a.slice(Math.max(0, i - 60), i + 80)}" after "${b.slice(Math.max(0, i - 60), i + 80)}"`); }
    by[fn] = (by[fn] || 0) + 1;
    console.log(`${st} · ${fn} · ${arg} · ${a.length} bytes · before ${h(a)} · after ${h(b)} · ${v}`); }
  A.close(); B.close(); }
if (diffs.length) console.log('differences:\n  ' + diffs.join('\n  '));
console.log(`parts_identity: ${count.same + count.sticky + count.bad} cases (${Object.entries(by).map(([k, v]) => `${k} ${v}`).join(', ')}): ${count.same} byte-identical, ${count.sticky} sticky only, ${count.bad} differ`);
process.exit(count.bad ? 1 : 0);
