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
const RELEASE_STATES = ['Waiting', 'Released', 'Returned', 'Withdrawn'];
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
      const tx = squash(card?.textContent), P = t => (d.defaultView.plainText ? d.defaultView.plainText(t) : t); /* the screen's display words: asset codes as plain names */
      ok(!!card && card.classList.contains('proactive') && tx.includes(P(it.label)) && tx.toLowerCase().includes(P(it.factor).toLowerCase()) && /no value claimed/i.test(tx), `${label}: proactive ${it.item} declared with its factor and no value claimed`);
      ok(tx.includes(P(it.depends_reason)) && tx.includes(fdate(it.service_date)) && tx.includes(`in ${MONTH[+it.crew_month.split('-')[1] - 1]}`) && tx.includes('$' + it.planned_spend), `${label}: proactive ${it.item} dependency, date ${fdate(it.service_date)}, crew month and spend`);
    }
    if (it.capital) {
      const tx = squash(card?.textContent), ex = wf.people.find(p => p.role === 'OPERATOR_EXECUTIVE').name;
      ok(/waits as capital/i.test(tx) && (it.actions_after_approval || []).every(a => tx.includes(a)) && tx.includes(`${it.owner} creates its Action only after ${ex}`) && !!card && !card.querySelector('.action-list'), `${label}: capital ${it.item} waits, Action by ${it.owner} after ${ex}'s approval`);
    }
  }
  ok(d.querySelectorAll('.plan-item').length === c.items.length + proOf(op).length, `${label}: ${c.items.length} case items plus ${proOf(op).length} declared`);
}
function approvalCheck(op, d, label) {
  /* review r4 M4: the approval covers the case on screen (a different case is approved as the next version), so its items are the ones shown */
  const wf = wfOf(op), v1 = [...d.querySelectorAll('.plan-item')].map(e => e.dataset.item);
  /* an option the case adds has no item record yet: it waits when it is above either threshold (the release rule) */
  const have = new Set((wf.items || []).map(i => i.item)), extra = v1.filter(id => !have.has(id)).map(id => { const x = DV.options[id] || {}; return { item: id, kind: 'OPTION', item_state: (x.operator_one_off || 0) > wf.spend_threshold || (x.crew_visits || 0) > wf.crew_visit_threshold ? 'CHOSEN' : 'RELEASED' }; });
  const waiting = [...(wf.items || []), ...extra].filter(i => v1.includes(i.item) && i.item_state === 'CHOSEN'), spend = waiting.reduce((s, i) => s + itemSpend(op, i), 0);
  const capital = waiting.filter(i => i.capital), capSpend = capital.reduce((s, i) => s + itemSpend(op, i), 0);
  const tx = squash(d.querySelector('.approval .approval-releases')?.textContent);
  ok(tx.includes(`${waiting.length} item${waiting.length === 1 ? '' : 's'}, ${usd(spend)} of one-off spend`), `${label}: approval releases ${waiting.length} items, ${usd(spend)} (${tx.slice(0, 90)})`);
  ok(!capital.length || tx.includes(`including ${usd(capSpend)} of capital`), `${label}: approval counts ${usd(capSpend)} of capital`);
}
function actionsCheck(op, d, caseItems, label) {
  const wf = MAN.demo_workflow.tenants.find(t => t.tenant === T[op]), v1 = DV.plans[T[op]].default.items;
  const text = [...d.querySelectorAll('.action-list li')].map(li => li.textContent.replace(/\s+/g, ' '));
  for (const a of wf.actions) {
    const shown = d.defaultView.plainText ? d.defaultView.plainText(a.action) : a.action, li = text.find(t => t.includes(shown)); /* the screen shows asset codes as plain names */
    if (!v1.includes(a.item)) { ok(!li, `${label}: ${a.item} not in version 1, not listed`); continue; }
    if (!caseItems.includes(a.item)) { ok(li && li.includes('Returned') && li.includes('To its creator'), `${label}: ${a.action.slice(0, 30)} Returned to its creator`); continue; }
    ok(li && li.includes(a.release === 'AT_CREATION' ? 'Released' : 'Waiting'), `${label}: ${a.action.slice(0, 30)} ${a.release}`);
  }
  // rev 16.12 (design §2.5, Figure 6d): an Action's release shows only Waiting, Released, Returned or Withdrawn; deferral is an event
  for (const p of d.querySelectorAll('.action-list .state .status-pill')) ok(RELEASE_STATES.includes(squash(p.textContent).trim()), `${label}: release state "${squash(p.textContent).trim()}" is one of Figure 6d's four`);
  { const n = d.querySelectorAll('.action-list .state .status-pill').length; ok(n > 0, `${label}: ${n} release states shown`); }
}
// Lakeside: the four switch cases
{ const dom = boot('lakeside', 'portfolio/act-first/plan'), w = dom.window, d = w.document;
  for (const [k, c] of Object.entries(DV.plans['lakeside-power'].switch_cases)) {
    const [b, l] = k.split('/'); pick(w, 'sw-budget', b); pick(w, 'sw-loi', l === 'True' ? 'yes' : 'no');
    const meter = d.querySelector('.approval .meterhead strong')?.textContent, total = d.querySelector('.total strong')?.textContent;
    ok(meter && meter.startsWith(usd(c.spend)), `lakeside ${k}: budget meter ${meter} starts ${usd(c.spend)}`);
    ok(total && [usd(c.value), usd(Math.round(c.value))].some(v => total.startsWith((c.value < 0 ? '−' : '+') + v)), `lakeside ${k}: value ${total}`); /* UI/UX guide U3: whole dollars at the plan total */
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
      /* the heading's effects, by Site: on its card, or (opened from the gap, one grammar) in its drivers' drawers */
      const lis = [...(card(k)?.querySelectorAll(`li[data-site="${sk}"][data-effect]`) || []), ...d.querySelectorAll(`.ux-drawer[id^="uxdrv-${op}-${k}-"] li[data-site="${sk}"][data-effect]`)], got = r2c(lis.reduce((a, l) => a + +l.dataset.effect, 0));
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
const HC = MAN.home_categories, VK = { lakeside: 'MINI_GRID', harvest: 'COLD_CHAIN', metro: 'EV_DEPOT_CAPTIVE' }, STATED = { resid: (HC.residuals?.EV_DEPOT_CAPTIVE?.stated_total_unattributed || [])[0] };
for (const op of ['lakeside', 'harvest', 'metro']) { const gapsSeen = [];
  SITES[op].forEach((sk, i) => { const dom = boot(op, `site/${sk}`), d = dom.window.document, rows = [...d.querySelectorAll('tr[data-node]')], site = bridgeOf(op, i), nodes = DV.sites[`${T[op]}/${site.site}`].actual.nodes;
    ok(rows.length > 5, `${op} ${sk}: factor rows found (${rows.length})`);
    for (const r of rows) { const id = r.dataset.node, key = r.dataset.key, got = r.dataset.heading, home = r.dataset.home;
      const bm = id.match(/^f(\d+)$/), drv = bm ? site.period.bridge[+bm[1]]?.driver : null;
      if (bm) ok(key === HC.bridge_drivers[drv], `${op} ${sk} ${id}: bridge row ${drv} keyed ${HC.bridge_drivers[drv]} (got ${key})`);
      let exp;
      if (STATED[id]) exp = STATED[id];
      else if (home === 'potential') { ok((HC.potential[VK[op]] || []).some(p => p.name === key), `${op} ${sk} ${id}: potential ${key} is in the data's potential list`); exp = 'grow'; }
      else if (key && key.includes('+')) { const parts = key.split('+'), rows = parts.map(k => HC.nodes[VK[op]][k]);
        ok(parts.every(k => k in nodes) && rows.every(r => r && r[0] === rows[0][0] && r[1] === rows[0][1]) && (r.dataset.actual === '' || Math.abs(+r.dataset.actual - parts.reduce((a, k) => a + nodes[k], 0)) < 0.01), `${op} ${sk} ${id}: summed node ${key}: evaluated parts with one registry row, figure ${r.dataset.actual} is their sum`);
        exp = rows.every(r => r && r[0] === rows[0][0]) ? rows[0][0] : ''; }
      else { const row = key ? HC.nodes[VK[op]][key] : null; exp = row && ['grow', 'optimize', 'protect', 'assure'].includes(row[0]) ? row[0] : '';
        if (key && !bm) ok(key in nodes, `${op} ${sk} ${id}: key ${key} is an evaluated node of the Site`);
        // the key is the right one: the row's October figure is that evaluated node's value (or its November-to-date value, for a row shown since 1 Nov)
        if (key && r.dataset.via === 'node' && r.dataset.actual !== '') { const a = +r.dataset.actual, nv = DV.sites[`${T[op]}/${site.site}`].november_to_date?.nodes?.[key];
          ok(Math.abs(a - nodes[key]) < 0.01 || (nv !== undefined && Math.abs(a - nv) < 0.01), `${op} ${sk} ${id}: figure ${a} is the evaluated ${key} (${nodes[key]}${nv !== undefined ? ', November ' + nv : ''})`); }
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
  const dom = boot(op, `decision/${dc.id}`), regs = [...dom.window.document.querySelectorAll('[aria-label="Service and asset limits under each option"]')];
  regs.forEach((rg, j) => { const t = squash(rg.textContent); ok(!/\$\s?\d/.test(t), `${dc.id}: Protect option table ${j + 1} shows no dollar figure${/\$\s?\d/.test(t) ? ' (' + t.match(/.{50}\$\s?\d.{10}/)?.[0] + ')' : ''}`); });
  dom.window.close(); }
{ const hu = MAN.tenants[0].sites.find(s => s.site === 'Mto').decision.options.find(o => o.id === 'MTO-HULLER').economics, cost = hu.fuel_monthly + hu.collection_cost_monthly;
  for (const [hash, sel] of [['decision/mto-demand', '.opts tbody tr:first-child'], ['portfolio/act-first/plan', '.plan-item[data-item="MTO-HULLER"]']]) {
    const dom = boot('lakeside', hash), el = dom.window.document.querySelector(sel), g = squash(el?.querySelector('[data-heading="grow"]')?.textContent), o = squash(el?.querySelector('[data-heading="optimize"]')?.textContent);
    ok(g.includes(usd(hu.revenue_monthly)) && g.startsWith('Grow revenue +') && o.includes(usd(cost)) && o.startsWith('Optimize cost and efficiency −'), `${hash}: huller Grow +${hu.revenue_monthly} and Optimize −${cost} (${g} | ${o})`);
    dom.window.close(); } }
// ---- Rev 16.12 (review H fix round, the Architect's list) ----
const usd2s = n => { const v = r2c(n || 0), a = Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); return (v < -0.0001 ? '−' : v > 0.0001 ? '+' : '') + '$' + a; };
const opOfSite = site => Object.keys(T).find(k => MAN.tenants.find(t => t.tenant === T[k]).sites.some(s => s.site === site));
const ROLE_WORDS = { OPERATOR_EXECUTIVE: 'Operator executive', FINANCE_AND_COMMERCIAL_LEAD: 'Finance and commercial lead', SITE_MANAGER: 'Site manager', FIELD_TECHNICIAN: 'Field technician', ANALYST: 'Analyst' };
// (1) Organisation settings (spec §8): the data's people in the five roles, a grant record, thresholds at portfolio and Site level
// with their defaults, the period's budget and each month's crew-visit limit; no Admin, no Viewer, no B. Yohannes
for (const op of ['lakeside', 'harvest', 'metro']) {
  const dom = boot(op, 'settings-tenant'), d = dom.window.document, wf = wfOf(op), C = consOf(op), mt = MAN.tenants.find(t => t.tenant === T[op]);
  const pn = [...d.querySelectorAll('.panel')].find(x => squash(x.querySelector('h2')?.textContent) === 'Users and roles'), tx = squash(pn?.textContent), all = squash(d.querySelector('#app .canvas')?.textContent);
  const tabs = [...(pn?.querySelectorAll('table') || [])], rowsOf = i => [...(tabs[i]?.querySelectorAll('tbody tr') || [])].map(r => [...r.querySelectorAll('td')].map(c => squash(c.textContent).trim()).join(' | '));
  ok(pn && !/\bAdmin\b|\bViewer\b|B\. Yohannes/.test(all), `${op} settings: no Admin, no Viewer, no B. Yohannes${/\bAdmin\b|\bViewer\b|B\. Yohannes/.test(all) ? ' (found: ' + all.match(/.{30}(?:\bAdmin\b|\bViewer\b|B\. Yohannes).{20}/)?.[0] + ')' : ''}`);
  const site = p => p.site ? p.site.split(' · ').pop() : '';
  ok(rowsOf(0).length === wf.people.length && wf.people.every((p, i) => rowsOf(0)[i].includes(p.name) && rowsOf(0)[i].includes(ROLE_WORDS[p.role]) && rowsOf(0)[i].includes(site(p)) && rowsOf(0)[i].includes('Illustrative')), `${op} settings: ${wf.people.length} people, each with the data's role and Site, labelled Illustrative`);
  ok(new Set(wf.people.map(p => p.role)).size === 5 && Object.values(ROLE_WORDS).every(w => rowsOf(0).some(r => r.includes(w))), `${op} settings: the five roles shown`);
  ok(rowsOf(1).length === wf.people.length && wf.people.every(p => rowsOf(1).some(r => r.startsWith(p.name) && r.includes('Granted'))), `${op} settings: a grant record row per person (${rowsOf(1).length})`);
  const thr = rowsOf(2), sites = mt.sites.map(s => s.site.split(' · ').pop());
  ok(thr[0]?.includes(usd(wf.spend_threshold)) && thr[0]?.includes(String(wf.crew_visit_threshold)) && sites.every(s => thr.some(r => r.startsWith(`Site: ${s}`) && r.includes('No Site setting'))) && thr.some(r => r.startsWith('Default when unset') && r.includes('Not set: nothing is released without approval') && /\b0\b/.test(r)),
    `${op} settings: spend ${wf.spend_threshold} and visit threshold ${wf.crew_visit_threshold} at portfolio level, each Site, and the defaults (${thr.join(' | ').slice(0, 160)})`);
  const lim = rowsOf(3), keys = Object.keys(C).filter(k => /_visits_[a-z]{3}$/.test(k));
  ok(lim[0]?.includes(usd(C.budget_usd_nov_dec)) && keys.every(k => lim.some(r => r.startsWith(MONTH[MON.findIndex(m => m.toLowerCase() === k.slice(-3))]) && r.endsWith(String(C[k])))), `${op} settings: budget ${C.budget_usd_nov_dec} and the month limits ${keys.map(k => k + '=' + C[k]).join(', ')}`);
  dom.window.close(); }
// (2) the overview's one split of the gap, by heading (spec §10): each line is the sum of the bridge rows on its factors (bridge
// driver -> registry key -> heading, from the data), subtotals per heading, Grow + Optimize = the evaluated gap, residual only on
// an unobserved leaf; no revenue-and-cost split and no "not explained" residual beside it
for (const op of ['lakeside', 'harvest', 'metro']) {
  const dom = boot(op, 'portfolio'), d = dom.window.document, cost = op === 'metro', keyTot = {}, keySite = {}, headTot = { grow: 0, optimize: 0 };
  SITES[op].forEach((sk, i) => (bridgeOf(op, i).period.bridge || []).forEach(b => { if (Math.abs(b.amount) < 0.005) return; const k = HC.bridge_drivers[b.driver], h = HC.nodes[VK[op]][k][0];
    keyTot[k] = r2c((keyTot[k] || 0) + b.amount); (keySite[k] = keySite[k] || {})[sk] = r2c((keySite[k]?.[sk] || 0) + b.amount); headTot[h] = r2c(headTot[h] + b.amount); }));
  const gap = r2c(SITES[op].reduce((a, sk, i) => a + dvGap(op, i), 0)), rows = [...d.querySelectorAll('table.gapsplit tr[data-split-key]')], seen = [];
  ok(d.querySelectorAll('table.gapsplit').length === 1 && rows.length > 0, `${op} overview: one split of the gap (${rows.length} lines)`);
  for (const r of rows) { const ks = r.dataset.splitKey.split(',').filter(Boolean), h = r.dataset.splitHeading;
    if (ks.length === 1 && HC.residuals?.[VK[op]]?.[ks[0]]) { const res = HC.residuals[VK[op]][ks[0]]; const exp = r2c(SITES[op].reduce((a, sk, i) => a + ((bridgeOf(op, i).period.bridge || []).length ? 0 : dvGap(op, i)), 0));
      ok(h === res[0] && Math.abs(+r.dataset.splitTotal - exp) < 0.005, `${op} overview: residual line ${ks[0]} under ${res[0]} is the unobserved Sites' gap ${exp} (got ${h} ${r.dataset.splitTotal})`); seen.push(...ks); continue; }
    const exp = r2c(ks.reduce((a, k) => a + (keyTot[k] || 0), 0));
    ok(ks.every(k => HC.nodes[VK[op]][k]?.[0] === h) && Math.abs(+r.dataset.splitTotal - exp) < 0.005 && SITES[op].every(sk => { const c = r.querySelector(`td[data-site="${sk}"]`), v = r2c(ks.reduce((a, k) => a + (keySite[k]?.[sk] || 0), 0)); return c && (c.dataset.v === '' ? Math.abs(v) < 0.005 : Math.abs(+c.dataset.v - v) < 0.005); }),
      `${op} overview: ${h} line ${ks.join('+')} = ${exp} from the bridge rows, per Site (got ${r.dataset.splitTotal})`); seen.push(...ks); }
  ok(Object.keys(keyTot).every(k => seen.filter(x => x === k).length === 1), `${op} overview: every bridge factor on exactly one line (${Object.keys(keyTot).join(', ')})`);
  const sub = k => +d.querySelector(`table.gapsplit tr.subtotal[data-split-heading="${k}"]`)?.dataset.splitSubtotal, root = d.querySelector('table.gapsplit tr.root');
  const resExp = cost ? r2c(gap - headTot.optimize) : 0;
  ok((cost || Math.abs(sub('grow') - headTot.grow) < 0.005) && Math.abs(sub('optimize') - r2c(headTot.optimize + resExp)) < 0.005 && Math.abs(+root?.dataset.splitGap - gap) < 0.005 && Math.abs(+root?.dataset.splitResidual - resExp) < 0.005 && Math.abs((cost ? 0 : sub('grow')) + sub('optimize') - gap) < 0.005,
    `${op} overview: Grow ${headTot.grow} + Optimize ${r2c(headTot.optimize + resExp)} = gap ${gap}, residual ${resExp} (got ${sub('grow')} + ${sub('optimize')} = ${root?.dataset.splitGap}, residual ${root?.dataset.splitResidual})`);
  /* UI/UX guide U3: glance figures show whole currency, so the split is compared at the precision shown (cents or whole dollars) */
  const usd0s = n => { const v = Math.round(n || 0); return (v < 0 ? '−' : v > 0 ? '+' : '') + '$' + Math.abs(v).toLocaleString('en-US'); };
  const top = squash(d.querySelector('.headline')?.textContent) + ' ' + squash(d.querySelector('.heroes')?.textContent);
  ok(!/Revenue factors|cost factors move|attributed to factors ·|not explained by the model/.test(top) && (cost || [usd2s, usd0s].some(f => top.includes(`Grow ${f(headTot.grow)}`) && top.includes(`Optimize ${f(headTot.optimize)}`))), `${op} overview: headline and figures split by heading only (${top.slice(0, 200)})`);
  if (op === 'lakeside') { const ux = rows.find(r => r.dataset.splitKey === 'unexplained_l'), ub = keySite.unexplained_l || {};
    ok(ux && squash(ux.textContent).includes('Fuel the generator model does not explain') && ux.dataset.splitHeading === 'optimize' && Object.keys(ub).length === 2 && Object.entries(ub).every(([sk, v]) => squash(ux.querySelector(`td[data-site="${sk}"]`)?.textContent) === usd2s(v)),
      `lakeside overview: fuel the generator model does not explain, under Optimize, ${Object.entries(ub).map(([s, v]) => s + ' ' + v).join(', ')}`); }
  dom.window.close(); }
// (4) who chooses (design §2.4 step 2, OD-16 ruling): the role the data names (home_categories.decisions[].chooser), the Site's manager
// for a Site role; the item, where there is one, chosen by that person; its Actions shown with their creators
// (5) each valued option's money lines under the headings of the money factors the data names (home_categories.option_money_factors)
// (11) the decision page's release state is one of Figure 6d's four
const optSeen = new Set();
for (const dc of HC.decisions) { const op = opOfSite(dc.site), wf = wfOf(op), dom = boot(op, `decision/${dc.id}`), d = dom.window.document;
  const p = wf.people.find(x => x.role === dc.chooser && (dc.chooser !== 'SITE_MANAGER' || x.site === dc.site)), wd = squash(d.querySelector('.who-decides .wd-steps li:nth-child(2)')?.textContent);
  const it = (wf.items || []).find(i => i.kind !== 'PROACTIVE' && DV.options[i.item]?.decision === dc.plan), acts = it ? wf.actions.filter(a => a.item === it.item) : [], st3 = squash(d.querySelector('.who-decides .wd-steps li:nth-child(3)')?.textContent);
  ok(p && wd.includes(p.name) && wd.includes(ROLE_WORDS[p.role]) && (!it || it.chosen_by === p.name) && acts.every(a => st3.includes(dom.window.plainText ? dom.window.plainText(a.action) : a.action) && st3.includes(`Created by ${ROLE_WORDS[wf.people.find(x => x.name === a.created_by).role]}`) && st3.includes(a.created_by)),
    `${dc.id}: chosen by ${p?.name} (${dc.chooser})${it ? `, item ${it.item} chosen by ${it.chosen_by}` : ''}${acts.length ? `, Actions created by ${[...new Set(acts.map(a => a.created_by))].join(', ')}` : ''} (${wd.slice(0, 80)})`);
  for (const rp of d.querySelectorAll('.who-decides [data-release], .action-list .state .status-pill')) ok(RELEASE_STATES.includes(squash(rp.textContent).trim()), `${dc.id}: release state "${squash(rp.textContent).trim()}" is one of Figure 6d's four`);
  for (const [id, F] of Object.entries(HC.option_money_factors)) { const tr = d.querySelector(`tr[data-opt="${id}"]`); if (!tr) continue; optSeen.add(id);
    const hs = [...new Set(F.map(f => HC.nodes[VK[op]][f]?.[0]))].sort(), got = [...tr.querySelectorAll('[data-heading]')].map(l => l.dataset.heading).filter(h => h === 'grow' || h === 'optimize').sort(), dv = DV.options[id];
    const one = hs.length === 1 ? squash(tr.querySelector(`[data-heading="${hs[0]}"]`)?.textContent) : '';
    ok(JSON.stringify(got) === JSON.stringify(hs) && (hs.length !== 1 || !dv?.monthly_or_horizon_change || one.includes(usd(dv.monthly_or_horizon_change))), `${dc.id} ${id}: money lines under ${hs.join(' and ')} from its factors ${F.join(', ')} (got ${got.join(', ') || 'none'}${one ? ': ' + one : ''})`); } }
ok(Object.keys(HC.option_money_factors).every(id => optSeen.has(id)), `every option with money factors is on its decision page (missing: ${Object.keys(HC.option_money_factors).filter(id => !optSeen.has(id)).join(', ') || 'none'})`);
// (7) the Mto claim: its one-off is what the operator bears, the supplier's share is named, the extra fuel is an Optimize line,
// and the option's value is the 12-month result, never a one-off cost
{ const dv = DV.options['MTO-INV-CLAIM'], cov = Object.values(dv.cost_lines).filter(l => l.covered_by && l.operator_share === 0).reduce((a, l) => a + l.amount, 0);
  for (const [hash, sel] of [['portfolio/act-first/plan', '.plan-item[data-item="MTO-INV-CLAIM"]'], ['decision/mto-inverter', 'tr[data-opt="MTO-INV-CLAIM"]']]) {
    const dom = boot('lakeside', hash), el = dom.window.document.querySelector(sel), tx = squash(el?.textContent);
    const oneOff = hash.startsWith('decision') ? squash(el?.querySelector('td:nth-child(4)')?.textContent) : squash([...(el?.querySelectorAll('.plan-item-figs > div') || [])].find(x => /^One-off cost/.test(squash(x.querySelector('dt')?.textContent)))?.querySelector('dd')?.textContent);
    const o = squash(el?.querySelector('[data-heading="optimize"]')?.textContent);
    ok(oneOff.startsWith(usd(dv.net_one_off)) && oneOff.includes(`supplier bears ${usd(cov)}`) && !oneOff.includes(usd(-dv.value)) && tx.includes('−' + usd(dv.value)) && o.startsWith('Optimize cost and efficiency −') && o.includes(usd(dv.monthly_or_horizon_change)),
      `${hash}: Mto claim one-off ${dv.net_one_off}, supplier bears ${cov}, extra fuel ${dv.monthly_or_horizon_change} under Optimize, value ${dv.value} not a one-off (${oneOff} | ${o})`);
    dom.window.close(); } }
// (8) and (11) What changed: each chosen option's state derives from its item and Actions; release states are Figure 6d's four
for (const op of ['lakeside', 'harvest', 'metro']) { const dom = boot(op, 'portfolio/what-changed'), d = dom.window.document, wf = wfOf(op);
  const rows = [...d.querySelectorAll('[aria-label="Chosen options"] tbody tr')];
  for (const r of rows) { const dc = HC.decisions.find(x => r.querySelector('a')?.getAttribute('href') === `#/decision/${x.id}`), it = dc ? (wf.items || []).find(i => i.kind !== 'PROACTIVE' && DV.options[i.item]?.decision === dc.plan) : null, acts = it ? wf.actions.filter(a => a.item === it.item) : [];
    const exp = !it ? 'BESIDE' : it.capital && !acts.length ? 'CAPITAL' : acts.length && acts.every(a => a.release === 'AT_CREATION') ? 'RELEASED' : 'WAITING', got = r.querySelector('[data-commit-state]')?.dataset.commitState;
    ok(dc && got === exp && (exp !== 'WAITING' || /Waiting for approval/.test(squash(r.textContent))) && (exp !== 'CAPITAL' || /capital approval/.test(squash(r.textContent)) && /No Action yet/.test(squash(r.textContent))), `${op} what changed: ${dc?.id} ${exp} (got ${got})`); }
  ok(rows.length > 0, `${op} what changed: ${rows.length} chosen options`);
  const pills = [...d.querySelectorAll('.action-list .state .status-pill')];
  ok(pills.length > 0 && pills.every(p => RELEASE_STATES.includes(squash(p.textContent).trim())), `${op} what changed: ${pills.length} release states, each one of Figure 6d's four (${[...new Set(pills.map(p => squash(p.textContent).trim()))].join(', ')})`);
  dom.window.close(); }
// (12) final wiring (design rev 16.12 §2.0, OD-25): each attention row is keyed to its Finding row, so a linked Finding takes its own heading
// (Embakasi "At its limit" Protect, "New tariff" Optimize; Ruiru "Near its limit" Protect); no row without a Finding id (FIND_GAPS empty)
{ const dom = boot('metro', 'portfolio'), d = dom.window.document, cards = [...d.querySelectorAll('article.ocard[data-heading]')];
  const under = (title, site) => cards.filter(c => [...c.querySelectorAll('li')].some(li => squash(li.querySelector('b')?.textContent) === title && squash(li.textContent).includes(`· ${site}:`))).map(c => c.dataset.heading);
  for (const [title, site, fid] of [['At its limit', 'Embakasi', 'embakasi-import-limit'], ['New tariff', 'Embakasi', 'embakasi-night-rate'], ['Near its limit', 'Ruiru', 'ruiru-import-limit']]) {
    const exp = HC.findings.find(f => f.id === fid).heading, got = under(title, site);
    ok(got.length === 1 && got[0] === exp, `metro overview: linked Finding ${fid} "${title}" at ${site} under its own heading ${exp} (got ${got.join(', ') || 'none'})`); }
  dom.window.close(); }
for (const op of ['lakeside', 'harvest', 'metro']) { const dom = boot(op, 'portfolio'); ok(Array.isArray(dom.window.FIND_GAPS) && dom.window.FIND_GAPS.length === 0, `${op} overview: FIND_GAPS empty (${(dom.window.FIND_GAPS || ['no list']).join(', ')})`); dom.window.close(); }
// the money residual column on "Outcomes by site" only where the data has a residuals row (Metro Bus: Ruiru's bill total); never Lakeside or Harvest
for (const op of ['lakeside', 'harvest', 'metro']) { const dom = boot(op, 'portfolio/outcomes-by-site'), d = dom.window.document, tb = d.querySelector('[aria-label="Portfolio composition"] table') || d.querySelector('table'), hd = [...tb.querySelectorAll('thead th')].map(x => squash(x.textContent)), has = !!HC.residuals?.[VK[op]];
  const ru = [...tb.querySelectorAll('tbody tr')].find(r => /Ruiru/.test(r.cells[0].textContent)), rv = DV.sites[`${T[op]}/Ruiru`];
  ok(hd.some(h => /^Of which/.test(h)) === has && (!has || (hd[hd.length - 1] === 'Of which not attributed yet' && ru && ru.cells.length === hd.length && /\$[\d,.]+/.test(ru.cells[ru.cells.length - 1].textContent))) && (has || [...tb.querySelectorAll('tr')].every(r => r.cells.length === 4)), `${op} outcomes by site: residual column ${has ? 'present, "Of which not attributed yet", with Ruiru’s figure' : 'absent'} (${hd.join(' | ')})`);
  dom.window.close(); }
// MTO-BILLING: an Optimize money line for the restored charges, "listed, not added"
{ const dom = boot('lakeside', 'decision/mto-billing'), tr = dom.window.document.querySelector('tr[data-opt="MTO-BILLING"]'), li = tr?.querySelector('[data-heading="optimize"]'), tx = squash(li?.textContent);
  ok(li && /listed, not added/.test(tx) && /\$\d/.test(tx), `mto-billing: MTO-BILLING Optimize money line "listed, not added" (${tx})`); dom.window.close(); }
// no former user's initials or name on any screen; the avatar is the portfolio's illustrative operator executive
for (const op of ['lakeside', 'harvest', 'metro']) { const man = (() => { const f = boot(op, 'portfolio'), m = f.window.mockupManifest || []; f.window.close(); return m; })(), exec = wfOf(op).people.find(x => x.role === 'OPERATOR_EXECUTIVE').name; let n = 0, bad = [], wrong = 0;
  for (const sc of man) { if (op !== 'lakeside' && !sc.id.startsWith('portfolio') && sc.id !== 'sites' && sc.id !== 'globalfinancials') continue;
    const dom = boot(op, sc.id), d = dom.window.document; n++; const av = squash(d.querySelector('.topbar .avatar')?.textContent), tx = d.body.textContent;
    if (/\bBY\b|Yohannes/.test(tx) || av === 'BY') bad.push(sc.id); if (d.querySelector('.topbar') && !(sc.id.startsWith('portfolio') ? av === exec[0] : ['A', 'E', 'D'].includes(av))) wrong++; dom.window.close(); }
  ok(n >= 5 && !bad.length && !wrong, `${op}: ${n} screens, no "BY" or "Yohannes", avatar is an executive's initial (portfolio screens: ${exec[0]}, ${exec}) (bad: ${bad.slice(0, 5).join(', ') || 'none'}; wrong avatar ${wrong})`); }
console.log(`plan_switch_check: ${log.length} passed, ${fails.length} failed, script errors ${errors.length}`);
if (fails.length) console.log(fails.join('\n')); if (errors.length) console.log(errors.slice(0, 5).join('\n'));
if (fails.length || errors.length) process.exitCode = 1;
