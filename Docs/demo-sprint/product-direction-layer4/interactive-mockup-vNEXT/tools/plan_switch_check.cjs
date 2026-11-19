/* jsdom check of the plan page (no browser needed): for each switch case, the budget meter, the plan's 12-month value,
   and the Actions are compared with the evaluator's switch cases (../derived-values.json) and the stated demo workflow
   (fixtures.js MANIFEST.demo_workflow). Checks: spend and value match the case; every stated Action of a version-1 item
   appears, released or waiting as stated, or under "return to their creator" when the case drops its item; Act first
   shows the triage before the plan summary; the summary and the approval panel show version, state and thresholds.
   Run: node tools/plan_switch_check.cjs   (from the interactive-mockup-vNEXT folder; exit 1 on any failure) */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const candidates = [process.env.JSDOM_PATH, path.resolve(root, '../../../../frontend/node_modules/jsdom'), '/opt/assetecon/AssetOpsV1/frontend/node_modules/jsdom'].filter(Boolean);
let JSDOM, VirtualConsole; for (const c of candidates) { try { ({ JSDOM, VirtualConsole } = require(c)); break; } catch (e) {} }
if (!JSDOM) { console.error('plan_switch_check: jsdom not found (set JSDOM_PATH)'); process.exit(2); }
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const DV = JSON.parse(fs.readFileSync(path.join(root, '..', 'derived-values.json'), 'utf8'));
const MAN = JSON.parse(fs.readFileSync(path.join(root, 'fixtures.js'), 'utf8').match(/const MANIFEST = (.*);\nconst MANIFEST_SHA/s)[1]);
const usd = n => '$' + Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: Number.isInteger(n) ? 0 : 2, maximumFractionDigits: 2 });
const fails = [], errors = [], log = [];
function boot(op, hash) {
  const vc = new VirtualConsole(); vc.on('jsdomError', e => errors.push(String(e.message || e).slice(0, 200))); vc.on('error', e => errors.push(String(e).slice(0, 200)));
  return new JSDOM(html, { virtualConsole: vc, runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://127.0.0.1:8790/#/' + hash,
    beforeParse(w) { try { w.sessionStorage.setItem('l4-op', op); } catch (e) {} w.matchMedia = w.matchMedia || (() => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} })); w.scrollTo = () => {}; } });
}
const ok = (cond, what) => { (cond ? log : fails).push(what); };
const pick = (w, name, val) => { const el = w.document.querySelector(`input[name="${name}"][value="${val}"]`); el.checked = true; el.dispatchEvent(new w.Event('change', { bubbles: true })); };
const T = { lakeside: 'lakeside-power', harvest: 'harvest-cold', metro: 'metro-bus' };
function actionsCheck(op, d, caseItems, label) {
  const wf = MAN.demo_workflow.tenants.find(t => t.tenant === T[op]), v1 = DV.plans[T[op]].default.items;
  const text = [...d.querySelectorAll('.action-list li')].map(li => li.textContent.replace(/\s+/g, ' '));
  for (const a of wf.actions) {
    const li = text.find(t => t.includes(a.action));
    if (!v1.includes(a.item)) { ok(!li, `${label}: ${a.item} not in version 1, not listed`); continue; }
    if (!caseItems.includes(a.item)) { ok(li && li.includes('Returns to its creator'), `${label}: ${a.action.slice(0, 30)} returns to its creator`); continue; }
    ok(li && li.includes(a.release === 'AT_CREATION' ? 'Released' : 'Waiting for approval'), `${label}: ${a.action.slice(0, 30)} ${a.release}`);
  }
}
// Lakeside: the four switch cases
{ const dom = boot('lakeside', 'portfolio/act-first/plan'), w = dom.window, d = w.document;
  for (const [k, c] of Object.entries(DV.plans['lakeside-power'].switch_cases)) {
    const [b, l] = k.split('/'); pick(w, 'sw-budget', b); pick(w, 'sw-loi', l === 'True' ? 'yes' : 'no');
    const meter = d.querySelector('.approval .meterhead strong')?.textContent, total = d.querySelector('.total strong')?.textContent;
    ok(meter && meter.startsWith(usd(c.spend)), `lakeside ${k}: budget meter ${meter} starts ${usd(c.spend)}`);
    ok(total && total.startsWith((c.value < 0 ? '−' : '+') + usd(c.value)), `lakeside ${k}: value ${total}`);
    ok(d.querySelectorAll('.plan-item').length === c.items.length, `lakeside ${k}: ${c.items.length} items`);
    actionsCheck('lakeside', d, c.items, `lakeside ${k}`);
  }
  w.close(); }
for (const [op, sw] of [['harvest', 'sw-agg'], ['metro', 'sw-tou']]) {
  const dom = boot(op, 'portfolio/act-first/plan'), w = dom.window, d = w.document;
  for (const [v, key] of [['yes', 'True'], ['no', 'False']]) {
    pick(w, sw, v); const c = DV.plans[T[op]].switch_cases[key];
    const meter = d.querySelector('.approval .meterhead strong')?.textContent;
    ok(meter && meter.startsWith(usd(c.spend)), `${op} ${v}: budget meter ${meter} starts ${usd(c.spend)}`);
    actionsCheck(op, d, c.items, `${op} ${v}`);
  }
  w.close(); }
// Act first: triage first, plan summary beside it
for (const op of ['lakeside', 'harvest', 'metro']) {
  const dom = boot(op, 'portfolio/act-first'), w = dom.window, d = w.document, S = MAN.demo_workflow.plan_state, wf = MAN.demo_workflow.tenants.find(t => t.tenant === T[op]);
  const lay = d.querySelector('.layout-main-side'), main = lay?.children[0], side = lay?.children[1];
  ok(main?.querySelector('.triage li') && side?.classList.contains('side-panel'), `${op} act first: triage in the main column, plan in the side panel`);
  const st = side?.textContent.replace(/\s+/g, ' ') || '';
  ok(st.includes(`Version ${S.version}`) && st.includes('Proposed by the system') && st.includes('awaiting the operator executive') && st.includes(wf.people.find(p => p.role === 'OPERATOR_EXECUTIVE').name), `${op} act first: version, state and executive`);
  ok(st.replace(/ /g, '').includes(`Spendthreshold${usd(wf.spend_threshold)}`) && /visit threshold ?0/.test(st) === (wf.crew_visit_threshold === 0) && side.querySelector('a[href="#/portfolio/act-first/plan"]'), `${op} act first: thresholds and Open the plan`);
  ok(side.querySelectorAll('.meter').length === 2, `${op} act first: budget and crew meters`);
  w.close(); }
console.log(`plan_switch_check: ${log.length} passed, ${fails.length} failed, script errors ${errors.length}`);
if (fails.length) console.log(fails.join('\n')); if (errors.length) console.log(errors.slice(0, 5).join('\n'));
if (fails.length || errors.length) process.exitCode = 1;
