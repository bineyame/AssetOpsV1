/* IA-1 byte identity (spec §6 item 2, D-IA.20, D-IA.22): each legacy function before its split (a base index.html) and after it
   (this tree's index.html), byte for byte, with UX_QN reset to 0 before each call, in the default state and under
   ?state=no-recommendation: planScreen() for each operator and switch case (planParts), uxOverview(op) for each operator
   (uxOverviewParts), siteOverview(sk) for each Site of each operator (siteOverviewP, uxSiteParts); from IA-1c decisionScreen(id).
   The one named fix (D-IA.22: the Site sticky's "Decide" targets the queue's own primary) is reported apart: a Site case whose only
   difference is inside its leading .ux-dsticky bar is "sticky only"; any other difference fails.
   IA-2a (D-IA.46, D-IA.50): planScreen() also in the three plan states of PLAN_STATES (as proposed, approved, sent back to draft;
   approved runs every case, a non-default case as the next version with that case's items), whatChangedScreen() in the three states, and
   the four splits as jobs: each base function against this script's own join of the new parts (planParts, approvalParts,
   uxPlanBandParts, whatChangedParts). PI_PLANT=planparts|approval|band|whatchanged changes one byte of that split's output in the new
   window; each must report DIFFERS. The script fails if both windows come from the same file.
   Run: node tools/parts_identity.cjs <base index.html> [<new index.html>] */
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const { JSDOM, VirtualConsole } = require(['/opt/assetecon/AssetOpsV1/frontend/node_modules/jsdom', path.resolve(__dirname, '../../../../../frontend/node_modules/jsdom')].find(p => { try { require.resolve(p); return true; } catch (e) { return false; } }));
const baseFile = process.argv[2], newFile = process.argv[3] || path.join(__dirname, '..', 'index.html');
if (!baseFile) { console.error('usage: node tools/parts_identity.cjs <base index.html> [<new index.html>]'); process.exit(2); }
if (fs.realpathSync(baseFile) === fs.realpathSync(newFile)) { console.log(`parts_identity: both windows from ${newFile}: a window compared with itself\nFAIL`); process.exit(1); }
const PLANT = process.env.PI_PLANT || '';
/* the plan states (D-IA.50), one literal; by, version, ids and giveWay are filled from the base window per operator and case and the
   same object is written to both windows */
const PLAN_STATES = { proposed: null, approved: { state: 'APPROVED', at: 'now' }, 'sent back': { state: 'DRAFT', at: 'now', reason: 'Too much spend' } };
const fill = (W, op, name) => { const t = PLAN_STATES[name]; if (!t) return null;
  const ex = W.eval(`(execOf(${JSON.stringify(op)})||{}).name||''`), ids = W.eval(`planCaseIds(${JSON.stringify(op)})`);
  return { plan: { [op]: t.state === 'APPROVED' ? { ...t, by: ex, version: W.eval(`DEFAULT_CASE(${JSON.stringify(op)})?PSTATE().version:PSTATE().version+1`), ids: [...ids] }
    : { ...t, by: ex, giveWay: W.eval(`optLabel(${JSON.stringify(ids[0])})`) } } }; };
const BUDGET = "(LS.op==='lakeside'?LS.budget:OPS[LS.op].t.portfolio_constraints.budget_usd_nov_dec)";
/* this script's own joins of the new parts (the reviewed templates, written out here) */
const JOIN = {
  approval: "(a=>`<section class=\"panel approval\" aria-labelledby=\"ap-h\"><h2 id=\"ap-h\">Approval</h2>${a.status}\n ${a.kv}\n ${a.meters}\n ${a.releases}\n ${a.notice}\n ${a.note}\n ${a.thresholds}</section>`)",
  band: "(B=>`<section class=\"ux-planband\" aria-label=\"The plan at a glance\"><div class=\"heroes ux-kpis\">\n ${B.spend}\n ${B.crew}\n ${B.value}\n </div>${B.act}</section>`)",
  whatchanged: "(w=>[w.kpis,w.actions,w.review,w.chosen,w.rightsM,w.rights].join('\\n '))"
};
const SPLITS = [
  ['planParts', 'planScreen()', `(p=>\`\${p.sticky}\${p.band}<div class="layout-main-side"><div>\${p.l2}\n \${p.diff}\n \${p.paths}\n <div class="grid2">\${p.crew}\${p.listed}</div>\n \${uxSecAx('Left out of the plan, and why',p.leftBody,p.leftAns)}\n \${p.cases}\n \${p.returned}\n </div><aside class="side-panel">\${${JOIN.approval}(p.ap)}\${p.switches}</aside></div>\`)(planParts(LS.op))`, 'planparts'],
  ['approvalParts', `approvalPanel(LS.op,planCase(LS.op),${BUDGET})`, `${JOIN.approval}(approvalParts(LS.op,planCase(LS.op),${BUDGET}))`, 'approval'],
  ['uxPlanBandParts', `uxPlanBand(LS.op,planCase(LS.op),${BUDGET})`, `${JOIN.band}(uxPlanBandParts(LS.op,planCase(LS.op),${BUDGET}))`, 'band']];
const flip = x => { const i = x.length >> 1; return x.slice(0, i) + (x[i] === 'x' ? 'y' : 'x') + x.slice(i + 1); };
const CASES = { lakeside: [[5000, true], [5000, false], [6500, true], [6500, false]].map(([b, l]) => ({ budget: b, loi: l })), harvest: [{ agg: true }, { agg: false }], metro: [{ tou: true }, { tou: false }] };
const boot = (file, op, search) => new JSDOM(fs.readFileSync(file, 'utf8'), { virtualConsole: new VirtualConsole(), runScripts: 'dangerously', pretendToBeVisual: true, url: `http://x/${search}#/not-a-route`,
  beforeParse(w) { w.sessionStorage.setItem('l4-op', op); w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; } }).window;
const h = x => crypto.createHash('sha256').update(x).digest('hex').slice(0, 16);
const noSticky = x => x.replace(/^<div class="ux-dsticky"[\s\S]*?<\/div>(?=<p class="headline)/, '');
const stickyOf = x => (x.match(/^<div class="ux-dsticky"[\s\S]*?<\/div>(?=<p class="headline)/) || [''])[0];
const count = { same: 0, sticky: 0, bad: 0 }, by = {}, diffs = [];
for (const search of ['', '?state=no-recommendation']) for (const op of Object.keys(CASES)) {
  const A = boot(baseFile, op, search), B = boot(newFile, op, search), st = search ? 'no-recommendation' : 'default';
  const call = (W, expr, m) => W.eval(`setOp(${JSON.stringify(op)});${m ? `sessionStorage.setItem('l4-mock',${JSON.stringify(JSON.stringify(m))})` : `sessionStorage.removeItem('l4-mock')`};UX_QN=0;${expr}`);
  const has = (W, f) => W.eval(`typeof ${f} === 'function'`);
  const st0 = n => (c => { A.eval(`setOp(${JSON.stringify(op)});Object.assign(LS,${JSON.stringify(c)})`); return fill(A, op, n); });
  const inState = (n, c) => ({ m: st0(n)(c), set: `Object.assign(LS,${JSON.stringify(c)});` });
  const jobs = [...CASES[op].map(c => ['planScreen', JSON.stringify(c), `Object.assign(LS,${JSON.stringify(c)});planScreen()`]),
    ...Object.keys(PLAN_STATES).filter(n => PLAN_STATES[n]).flatMap(n => CASES[op].map(c => { const s = inState(n, c); return ['planScreen', `${JSON.stringify(c)} · ${n}`, `${s.set}planScreen()`, null, s.m]; })),
    ...Object.keys(PLAN_STATES).flatMap(n => CASES[op].flatMap(c => { const s = inState(n, c); return SPLITS.map(([fn, a, b, pl]) => [fn, `${JSON.stringify(c)} · ${n}`, `${s.set}${a}`, `${s.set}${b}`, s.m, pl]); })),
    ...Object.keys(PLAN_STATES).flatMap(n => { const s = inState(n, CASES[op][0]); return [['whatChangedScreen', n, `${s.set}whatChangedScreen()`, null, s.m], ['whatChangedParts', n, `${s.set}whatChangedScreen()`, `${s.set}${JOIN.whatchanged}(whatChangedParts(LS.op))`, s.m, 'whatchanged']]; }),
    ['uxOverview', op, `uxOverview(${JSON.stringify(op)})`],
    ...A.eval(`OPS[${JSON.stringify(op)}].sites`).map(sk => ['siteOverview', sk, `siteOverview(${JSON.stringify(sk)})`]),
    ...(has(A, 'decisionScreen') && has(B, 'uxDecisionSlots') ? A.eval(`DEC.filter(d => OPS[${JSON.stringify(op)}].sites.includes(d.site)).map(d => d.id)`).map(id => ['decisionScreen', id, `decisionScreen(${JSON.stringify(id)})`]) : [])];
  for (const [fn, arg, expr, exprB, m, pl] of jobs) { const a = call(A, expr, m); let b = call(B, exprB || expr, m); if (pl && pl === PLANT) b = flip(b); let v;
    if (a === b) { v = 'byte-identical'; count.same++; }
    else if (fn === 'siteOverview' && noSticky(a) === noSticky(b)) { v = 'sticky only'; count.sticky++; diffs.push(`${st} · ${op} · ${arg}\n    before: ${stickyOf(a)}\n    after:  ${stickyOf(b)}`); }
    else { v = 'DIFFERS'; count.bad++; let i = 0; while (a[i] === b[i]) i++; diffs.push(`${st} · ${fn} · ${arg} DIFFERS at ${i}: before "${a.slice(Math.max(0, i - 60), i + 80)}" after "${b.slice(Math.max(0, i - 60), i + 80)}"`); }
    by[fn] = (by[fn] || 0) + 1;
    console.log(`${st} · ${fn} · ${arg} · ${a.length} bytes · before ${h(a)} · after ${h(b)} · ${v}`); }
  A.close(); B.close(); }
if (diffs.length) console.log('differences:\n  ' + diffs.join('\n  '));
console.log(`parts_identity: ${count.same + count.sticky + count.bad} cases (${Object.entries(by).map(([k, v]) => `${k} ${v}`).join(', ')}): ${count.same} byte-identical, ${count.sticky} sticky only, ${count.bad} differ`);
process.exit(count.bad ? 1 : 0);
