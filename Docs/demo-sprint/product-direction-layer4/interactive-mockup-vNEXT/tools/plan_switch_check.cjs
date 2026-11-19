/* jsdom check of the plan page (no browser needed): for each switch case, the budget meter, the plan's 12-month value,
   and the Actions are compared with the evaluator's switch cases (../derived-values.json) and the stated demo workflow
   (fixtures.js MANIFEST.demo_workflow). Checks: spend and value match the case; every stated Action of a version-1 item
   appears, released or waiting as stated, or under "return to their creator" when the case drops its item; Act first
   shows the triage before the plan summary; the summary and the approval panel show version, state and thresholds.
   Items (demo_workflow items[]): every item card names its owner and its stated state (Chosen or Released); each
   decision page names the item's chooser; the proactive item is a declared card with its factor, dependency, date and
   crew month, and adds no item to the evaluated case; each month with a stated crew limit has its own meter
   (crew_visits_<mon>), counting the case's visits in the first month and each proactive visit in its month; the capital
   item waits with its after-approval Action and no created Action; "Approving releases" counts every waiting item's
   planned spend once, capital included.
   Headings (rev 16.10, OD-21/OD-23): each Overview card lists exactly its heading's money effects; Grow + Optimize equal the
   evaluated contribution gap per Site; the Assure card shows no money; every screen shows the snapshot "as of" date; the
   huller's Grow and Optimize effects on its decision page and plan item; outstanding sits under Optimize as cash; the bridge opens from Assure.
   Rev 16.11 (register calls 17-19): every factor row's heading equals the data's registry row (home_categories), rows with no
   row listed under Assure; no dollar figure on the Protect card (values at stake excepted) or in any Protect option table;
   Kasarani's avoided penalties are an Optimize line; the per-portfolio snapshot time with its hour and the pending notice;
   the portfolio cash line equals the data (received at cold rooms, collected on mini-grids) and is not zero.
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
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTH = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const fdate = iso => { const [, m, d] = iso.slice(0, 10).split('-').map(Number); return `${d} ${MON[m - 1]}`; };
const hhmm = iso => /T\d{2}:\d{2}/.test(iso || '') ? iso.slice(11, 16) : null;
const squash = s => (s || '').replace(/\s+/g, ' ');
const wfOf = op => MAN.demo_workflow.tenants.find(t => t.tenant === T[op]);
const consOf = op => MAN.tenants.find(t => t.tenant === T[op]).portfolio_constraints;
const proOf = op => (wfOf(op).items || []).filter(i => i.kind === 'PROACTIVE');
const itemSpend = (op, it) => it.kind === 'PROACTIVE' ? (it.planned_spend || 0) : (DV.options[it.item].operator_one_off || 0);
// expected meters: budget, then one per period month with a stated crew limit (first month: the evaluator's limit and the case's visits)
function expectedCrew(op, c) {
  const [a, b] = MAN.demo_workflow.plan_state.period.split(' to '), months = [...new Set([a, b])];
  return months.map((ym, i) => { const m = +ym.split('-')[1], lim = i === 0 ? c.crew_visits_limit : consOf(op)[`crew_visits_${MON[m - 1].toLowerCase()}`];
    const used = (i === 0 ? c.crew_visits_used : 0) + proOf(op).filter(it => (it.crew_month || a) === ym).reduce((s, it) => s + (it.crew_visits || 0), 0);
    return { month: MONTH[m - 1], used, lim }; }).filter(x => x.lim !== undefined);
}
function metersCheck(op, panel, c, label) {
  const ms = [...(panel?.querySelectorAll('.meter') || [])].map(m => squash(m.textContent)), ex = expectedCrew(op, c);
  ok(ms.length === 1 + ex.length, `${label}: ${1 + ex.length} meters (budget and ${ex.length} crew month${ex.length === 1 ? '' : 's'}), found ${ms.length}`);
  ex.forEach((x, i) => ok(ms[1 + i] && ms[1 + i].includes(`${x.used} of ${x.lim}`) && (ex.length === 1 || ms[1 + i].includes(x.month)), `${label}: ${x.month} crew meter ${x.used} of ${x.lim} (${ms[1 + i]})`));
}
function itemsCheck(op, d, c, label) {
  const wf = wfOf(op);
  for (const it of wf.items || []) {
    const card = d.querySelector(`.plan-item[data-item="${it.item}"]`), inCase = it.kind === 'PROACTIVE' || c.items.includes(it.item);
    if (!inCase) { ok(!card, `${label}: ${it.item} left out, no card`); continue; }
    const own = squash(card?.querySelector('.item-owner')?.textContent), word = { CHOSEN: 'Chosen', RELEASED: 'Released' }[it.item_state];
    ok(card && own.includes(it.owner) && own.includes(it.chosen_by) && word && own.includes(word) && !/\b(CHOSEN|RELEASED)\b/.test(squash(card.textContent)), `${label}: ${it.item} card owner ${it.owner}, state ${word}`);
    if (it.kind === 'PROACTIVE') {
      const tx = squash(card?.textContent);
      ok(!!card && card.classList.contains('proactive') && tx.includes(it.label) && tx.toLowerCase().includes(it.factor) && /no value claimed/i.test(tx), `${label}: proactive ${it.item} declared with its factor and no value claimed`);
      ok(tx.includes(it.depends_reason) && tx.includes(fdate(it.service_date)) && tx.includes(`in ${MONTH[+it.crew_month.split('-')[1] - 1]}`) && tx.includes('$' + it.planned_spend), `${label}: proactive ${it.item} dependency, date ${fdate(it.service_date)}, crew month and spend`);
    }
    if (it.capital) {
      const tx = squash(card?.textContent), ex = wf.people.find(p => p.role === 'OPERATOR_EXECUTIVE').name;
      ok(/waits as capital/i.test(tx) && (it.actions_after_approval || []).every(a => tx.includes(a)) && tx.includes(`${it.owner} creates its Action only after ${ex}`) && !!card && !card.querySelector('.action-list'), `${label}: capital ${it.item} waits, Action by ${it.owner} after ${ex}'s approval`);
    }
  }
  ok(d.querySelectorAll('.plan-item').length === c.items.length + proOf(op).length, `${label}: ${c.items.length} case items plus ${proOf(op).length} declared`);
}
function approvalCheck(op, d, label) {
  const wf = wfOf(op), v1 = [...DV.plans[T[op]].default.items, ...proOf(op).map(i => i.item)];
  const waiting = (wf.items || []).filter(i => v1.includes(i.item) && i.item_state === 'CHOSEN'), spend = waiting.reduce((s, i) => s + itemSpend(op, i), 0);
  const capital = waiting.filter(i => i.capital), capSpend = capital.reduce((s, i) => s + itemSpend(op, i), 0);
  const tx = squash(d.querySelector('.approval .approval-releases')?.textContent);
  ok(tx.includes(`${waiting.length} item${waiting.length === 1 ? '' : 's'}, ${usd(spend)} of one-off spend`), `${label}: approval releases ${waiting.length} items, ${usd(spend)} (${tx.slice(0, 90)})`);
  ok(!capital.length || tx.includes(`including ${usd(capSpend)} of capital`), `${label}: approval counts ${usd(capSpend)} of capital`);
}
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
    actionsCheck('lakeside', d, c.items, `lakeside ${k}`);
    itemsCheck('lakeside', d, c, `lakeside ${k}`); metersCheck('lakeside', d.querySelector('.approval'), c, `lakeside ${k} approval`); approvalCheck('lakeside', d, `lakeside ${k}`);
  }
  w.close(); }
for (const [op, sw] of [['harvest', 'sw-agg'], ['metro', 'sw-tou']]) {
  const dom = boot(op, 'portfolio/act-first/plan'), w = dom.window, d = w.document;
  for (const [v, key] of [['yes', 'True'], ['no', 'False']]) {
    pick(w, sw, v); const c = DV.plans[T[op]].switch_cases[key];
    const meter = d.querySelector('.approval .meterhead strong')?.textContent;
    ok(meter && meter.startsWith(usd(c.spend)), `${op} ${v}: budget meter ${meter} starts ${usd(c.spend)}`);
    actionsCheck(op, d, c.items, `${op} ${v}`);
    itemsCheck(op, d, c, `${op} ${v}`); metersCheck(op, d.querySelector('.approval'), c, `${op} ${v} approval`); approvalCheck(op, d, `${op} ${v}`);
  }
  w.close(); }
// Decision pages: who chooses is the item's stated chooser (items[].chosen_by), reached from each item card's decision link
for (const op of ['lakeside', 'harvest', 'metro']) {
  const dom = boot(op, 'portfolio/act-first/plan'), d = dom.window.document;
  const links = (wfOf(op).items || []).map(it => [it, d.querySelector(`.plan-item[data-item="${it.item}"] .plan-item-link`)?.getAttribute('href')]).filter(([, h]) => h);
  dom.window.close();
  for (const [it, href] of links) {
    const dd = boot(op, href.replace(/^#\//, '')), wd = dd.window.document.querySelector('.who-decides .wd-steps li:nth-child(2)');
    ok(wd && squash(wd.textContent).includes(it.chosen_by), `${op} ${href}: who chooses is ${it.chosen_by}`);
    dd.window.close();
  }
  ok(links.length === (wfOf(op).items || []).filter(i => i.kind !== 'PROACTIVE').length, `${op}: every chosen item links to its decision`);
}
// Act first: triage first, plan summary beside it
for (const op of ['lakeside', 'harvest', 'metro']) {
  const dom = boot(op, 'portfolio/act-first'), w = dom.window, d = w.document, S = MAN.demo_workflow.plan_state, wf = MAN.demo_workflow.tenants.find(t => t.tenant === T[op]);
  const lay = d.querySelector('.layout-main-side'), main = lay?.children[0], side = lay?.children[1];
  ok(main?.querySelector('.triage li') && side?.classList.contains('side-panel'), `${op} act first: triage in the main column, plan in the side panel`);
  const st = side?.textContent.replace(/\s+/g, ' ') || '';
  ok(st.includes(`Version ${S.version}`) && st.includes('Proposed by the system') && st.includes('awaiting the operator executive') && st.includes(wf.people.find(p => p.role === 'OPERATOR_EXECUTIVE').name), `${op} act first: version, state and executive`);
  ok(st.replace(/ /g, '').includes(`Spendthreshold${usd(wf.spend_threshold)}`) && /visit threshold ?0/.test(st) === (wf.crew_visit_threshold === 0) && side.querySelector('a[href="#/portfolio/act-first/plan"]'), `${op} act first: thresholds and Open the plan`);
  metersCheck(op, side, DV.plans[T[op]].default, `${op} act first`);
  w.close(); }
// ---- Rev 16.9 (design §2.0, Figure 1b, OD-21; §2.8, OD-23): the four headings over the structure ----
// Independent of the mock-up's HOME table (design rev 16.10): a bridge row is Grow when it is growth in what is sold (metered
// and billed kWh, occupied crate-days; worked-portfolios §1.0 Home categories), else Optimize (litres at their price, energy,
// demand charge, and the service-to-charge part: unmapped meters, adjustments). Collection is Optimize, as cash outside the gap. Checks: each card lists exactly its heading's effects; Grow + Optimize = the evaluated contribution
// gap per Site; the Assure card shows no money; every screen shows the snapshot's "as of" date; the huller's effects sit
// under both money headings on its decision page and plan item.
const GROW_DRIVERS = ['DEMAND_VOLUME', 'OCCUPANCY_REVENUE'];
const SITES = { lakeside: ['kobo', 'kisiwa', 'mto'], harvest: ['mwea', 'thika', 'kirinyaga'], metro: ['embakasi', 'kasarani', 'ruiru'] };
const r2c = x => Math.round(x * 100) / 100;
const bridgeOf = (op, i) => MAN.tenants.find(t => t.tenant === T[op]).sites[i];
function dvGap(op, i) { const s = bridgeOf(op, i), dv = DV.sites[`${T[op]}/${s.site}`]; const a = dv.actual.nodes.contribution, p = dv.plan.nodes?.contribution;
  return p != null ? r2c(a - p) : r2c(a + dv.plan.stated_total); }
for (const op of ['lakeside', 'harvest', 'metro']) {
  const dom = boot(op, 'portfolio'), d = dom.window.document;
  const card = k => d.querySelector(`.ocard[data-heading="${k}"]`);
  ok(['grow', 'optimize', 'protect', 'assure'].every(card), `${op}: four heading cards`);
  SITES[op].forEach((sk, i) => {
    const br = bridgeOf(op, i).period.bridge || [], gap = dvGap(op, i);
    const exp = { grow: r2c(br.filter(b => GROW_DRIVERS.includes(b.driver)).reduce((a, b) => a + b.amount, 0)), optimize: r2c(br.filter(b => !GROW_DRIVERS.includes(b.driver)).reduce((a, b) => a + b.amount, 0)) };
    if (!br.length) exp.optimize = gap; // no bridge: the explicit residual on the cost leaf (Ruiru) is the whole gap
    for (const k of ['grow', 'optimize']) {
      const lis = [...(card(k)?.querySelectorAll(`li[data-site="${sk}"][data-effect]`) || [])], got = r2c(lis.reduce((a, l) => a + +l.dataset.effect, 0));
      const n = br.length ? br.filter(b => GROW_DRIVERS.includes(b.driver) === (k === 'grow') && Math.abs(b.amount) > 0.004).length : (k === 'optimize' && Math.abs(gap) > 0.004 ? 1 : 0);
      ok(lis.length === n && Math.abs(got - exp[k]) < 0.005, `${op} ${sk}: ${k} card lists ${n} effect(s) summing ${exp[k]} (got ${lis.length}, ${got})`);
    }
    const others = ['protect', 'assure'].some(k => card(k)?.querySelector(`li[data-site="${sk}"][data-effect]`));
    ok(!others, `${op} ${sk}: no money effect under Protect or Assure`);
    const row = d.querySelector(`.contrib-bridge tr[data-site="${sk}"]`);
    ok(row && Math.abs(+row.dataset.grow + +row.dataset.optimize - gap) < 0.005 && Math.abs(+row.dataset.gap - gap) < 0.005 && Math.abs(+row.dataset.grow - exp.grow) < 0.005,
      `${op} ${sk}: Grow ${exp.grow} + Optimize ${exp.optimize} = contribution gap ${gap} (row ${row?.dataset.grow} + ${row?.dataset.optimize} = ${row?.dataset.gap})`);
  });
  // Assure has no money of its own: outside the bridge it presents (whose figures are the Grow and Optimize ones), no money at all
  const ac = card('assure')?.cloneNode(true); ac?.querySelectorAll('.cb-disc').forEach(x => x.remove());
  const at = squash(ac?.textContent);
  ok(at && !/\$|\d+(?:\.\d+)? (?:a month|dollars)/.test(at), `${op}: the Assure card shows no money of its own`);
  ok(card('assure')?.querySelector('.cb-disc.contrib-bridge') && d.querySelectorAll('.contrib-bridge').length === 1, `${op}: contribution's bridge opens from Assure, not as a layer of its own`);
  if (op !== 'metro') SITES[op].forEach((sk, i) => { const ou = DV.sites[`${T[op]}/${bridgeOf(op, i).site}`].actual.nodes.outstanding;
    const li = card('optimize')?.querySelector(`li[data-cash="${sk}"]`);
    ok(li && squash(li.textContent).includes(`${usd(ou)} outstanding`) && !squash(card('grow')?.textContent).includes('outstanding') && !li.hasAttribute('data-effect'), `${op} ${sk}: ${ou} outstanding sits under Optimize as cash, outside the gap`); });
  const chip = squash(d.querySelector('.period-chip')?.textContent), snap = MAN.snapshot.portfolios.find(p => p.tenant === T[op]);
  ok(chip.includes(`Figures as of ${hhmm(snap.as_of)}, ${fdate(snap.as_of)}`), `${op}: snapshot "as of" shown with its hour (${chip})`);
  ok(!d.querySelector('.snap-pending') === !(snap.recalculation_pending === true), `${op}: recalculation-pending notice only where the data says so`);
  // rev 16.11 (register call 19): the per-portfolio pending notice names what arrived, when, and the Sites it affects, in plain words
  if (snap.recalculation_pending) { const nt = squash(d.querySelector('.snap-pending')?.textContent), pd = snap.pending;
    const names = pd.sites.map(n => n.split('·').pop().trim());
    ok(nt.startsWith('Recalculation pending.') && nt.includes(`At ${hhmm(pd.received)} on ${fdate(pd.received)}`) && nt.includes(pd.what) && names.every(n => nt.includes(n)) && (!pd.portfolio_also || nt.includes('the portfolio')) && nt.includes(`${hhmm(snap.as_of)} figures`) && !/[a-z]+_[a-z_]+|\b\d{4}-\d{2}-\d{2}/.test(nt),
      `${op}: pending notice in plain words: what arrived at ${hhmm(pd.received)}, ${names.join(', ')}${pd.portfolio_also ? ' and the portfolio' : ''} (${nt})`); }
  // cash: the portfolio's cash line equals the data's sum (received at cold rooms, collected on mini-grids) and is not zero
  if (op !== 'metro') { const ck = op === 'harvest' ? 'received' : 'collected', exp = r2c(SITES[op].reduce((a, sk, i) => a + (DV.sites[`${T[op]}/${bridgeOf(op, i).site}`].actual.nodes[ck] || 0), 0));
    const pl = card('optimize')?.querySelector('li[data-cash="portfolio"]'), pt = squash(pl?.textContent);
    ok(exp > 0 && pt.includes(`${usd(exp)} ${ck}`) && Math.abs(+pl.dataset.cashValue - exp) < 0.005, `${op}: portfolio cash ${exp} ${ck}, not zero (${pt})`); }
  // no money under Protect: no dollar figure on the Protect card outside the values at stake (class At stake, listed never summed)
  { const pc = card('protect')?.cloneNode(true); pc?.querySelectorAll('li').forEach(li => { if (li.querySelector('.ec-stake')) li.remove(); });
    const pt = squash(pc?.textContent); ok(pt && !/\$\s?\d/.test(pt), `${op}: no dollar figure on the Protect card outside the values at stake${/\$\s?\d/.test(pt) ? ' (found: ' + pt.match(/.{60}\$\s?\d.{20}/)?.[0] + ')' : ''}`); }
  dom.window.close(); }
// rev 16.11 (design §2.0, register call 17): every factor row's heading is the data's registry row (home_categories.nodes),
// never inherited. A bridge row's key is checked against the data's bridge (driver -> bridge_drivers); every other key must be an
// evaluated node of that Site. Rows with no registry row show no heading and are listed under Assure. One row is stated by the
// dispatch rather than the registry: Ruiru's unattributed bill-total residual, Optimize (worked-portfolios §1.0, EV depot, O1).
const HC = MAN.home_categories, VK = { lakeside: 'MINI_GRID', harvest: 'COLD_CHAIN', metro: 'EV_DEPOT_CAPTIVE' }, STATED = { resid: 'optimize' };
for (const op of ['lakeside', 'harvest', 'metro']) { const gapsSeen = [];
  SITES[op].forEach((sk, i) => { const dom = boot(op, `site/${sk}`), d = dom.window.document, rows = [...d.querySelectorAll('tr[data-node]')], site = bridgeOf(op, i), nodes = DV.sites[`${T[op]}/${site.site}`].actual.nodes;
    ok(rows.length > 5, `${op} ${sk}: factor rows found (${rows.length})`);
    for (const r of rows) { const id = r.dataset.node, key = r.dataset.key, got = r.dataset.heading, home = r.dataset.home;
      const bm = id.match(/^f(\d+)$/), drv = bm ? site.period.bridge[+bm[1]]?.driver : null;
      if (bm) ok(key === HC.bridge_drivers[drv], `${op} ${sk} ${id}: bridge row ${drv} keyed ${HC.bridge_drivers[drv]} (got ${key})`);
      let exp;
      if (STATED[id]) exp = STATED[id];
      else if (home === 'potential') { ok((HC.potential[VK[op]] || []).some(p => p.name === key), `${op} ${sk} ${id}: potential ${key} is in the data's potential list`); exp = 'grow'; }
      else { const row = key ? HC.nodes[VK[op]][key] : null; exp = row && ['grow', 'optimize', 'protect', 'assure'].includes(row[0]) ? row[0] : '';
        if (key && !bm) ok(key in nodes, `${op} ${sk} ${id}: key ${key} is an evaluated node of the Site`);
        if (!row) gapsSeen.push(r.querySelector('b')?.textContent); }
      ok(got === exp, `${op} ${sk} ${id}: heading ${exp || '(none)'} from the registry row ${key || '(none)'} (got ${got || '(none)'})`); }
    dom.window.close(); });
  const dom = boot(op, 'portfolio'), at = squash(dom.window.document.querySelector('.ocard[data-heading="assure"]')?.textContent);
  ok(gapsSeen.every(g => at.includes(g)) && (gapsSeen.length > 0) === at.includes('Not yet under a heading'), `${op}: rows with no registry row listed under Assure (${gapsSeen.join('; ') || 'none'})`);
  dom.window.close(); }
// a money line takes its own factor's heading (§2.0): Kasarani's cover is a Protect decision, and its avoided penalties are Optimize
{ const dv = DV.options['KAS-OEM-STOPGAP'], dom = boot('metro', 'portfolio/act-first/plan'), el = dom.window.document.querySelector('.plan-item[data-item="KAS-OEM-STOPGAP"]');
  const o = squash(el?.querySelector('[data-heading="optimize"]')?.textContent), p = squash(el?.querySelector('[data-heading="protect"]')?.textContent);
  ok(o.startsWith('Optimize cost and efficiency +') && o.includes(usd(dv.monthly_or_horizon_change)) && p && !/\$/.test(p), `Kasarani cover: Optimize +${dv.monthly_or_horizon_change} and a Protect line with no money (${o} | ${p})`);
  dom.window.close(); }
// no dollar figure in any Protect option table (decision pages: "Protect measures under each option")
for (const dc of MAN.home_categories.decisions) { const op = Object.keys(T).find(k => MAN.tenants.find(t => t.tenant === T[k]).sites.some(s => s.site === dc.site));
  const dom = boot(op, `decision/${dc.id}`), regs = [...dom.window.document.querySelectorAll('[aria-label="Protect measures under each option"]')];
  regs.forEach((rg, j) => { const t = squash(rg.textContent); ok(!/\$\s?\d/.test(t), `${dc.id}: Protect option table ${j + 1} shows no dollar figure${/\$\s?\d/.test(t) ? ' (' + t.match(/.{50}\$\s?\d.{10}/)?.[0] + ')' : ''}`); });
  dom.window.close(); }
{ const hu = MAN.tenants[0].sites.find(s => s.site === 'Mto').decision.options.find(o => o.id === 'MTO-HULLER').economics, cost = hu.fuel_monthly + hu.collection_cost_monthly;
  for (const [hash, sel] of [['decision/mto-demand', '.opts tbody tr:first-child'], ['portfolio/act-first/plan', '.plan-item[data-item="MTO-HULLER"]']]) {
    const dom = boot('lakeside', hash), el = dom.window.document.querySelector(sel), g = squash(el?.querySelector('[data-heading="grow"]')?.textContent), o = squash(el?.querySelector('[data-heading="optimize"]')?.textContent);
    ok(g.includes(usd(hu.revenue_monthly)) && g.startsWith('Grow revenue +') && o.includes(usd(cost)) && o.startsWith('Optimize cost and efficiency −'), `${hash}: huller Grow +${hu.revenue_monthly} and Optimize −${cost} (${g} | ${o})`);
    dom.window.close(); } }
console.log(`plan_switch_check: ${log.length} passed, ${fails.length} failed, script errors ${errors.length}`);
if (fails.length) console.log(fails.join('\n')); if (errors.length) console.log(errors.slice(0, 5).join('\n'));
if (fails.length || errors.length) process.exitCode = 1;
