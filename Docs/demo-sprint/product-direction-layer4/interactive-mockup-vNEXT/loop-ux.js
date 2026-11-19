/* ===== loop-ux.js: the UI/UX guide's components (Docs/design-system/uiux-guide.md), wave 1 =====
   Presentation only. Every figure is read through the other modules' functions (opTotals, gapByHeading, planCase, ATTN,
   CARDS, categoryCard, chainStages, ...); nothing is typed here. Levels (guide §2.1): L1 glance (headline, KPI tiles),
   L2 queue and decide (decision queue, plan card), L3 explain (bridge, value chain, category tiles), L4 evidence (drawers,
   "Show as table", the evidence drawer). The full earlier panels stay in the page, inside drawers and table views, so
   nothing is lost and the content checks read them unchanged. */

/* ---------- numbers at a glance (guide §5.1, proposal U3): whole currency at L1 and L2 ---------- */
const usdW = (n, sign = false) => n === null || n === undefined ? usd(n) : usd(Math.round(n), sign);

/* ---------- certainty marker (guide §6, U1): the scope's baseline class is unmarked; others carry one quiet marker ---------- */
function uxMark(cls) {
  const [w, k] = CLS[cls] || [cls, 'na'];
  if (k === 'rec' || k === 'der') return `<span class="vh"> (${w})</span>`;
  return `<span class="ux-mark ux-mark-${k}">${w}</span>`;
}

/* ---------- KPI tile and bullet (guide §4.5, §5) ---------- */
function uxBullet(actual, target, label, invert = false) {
  if (actual == null || target == null || !(target > 0)) return '';
  const max = Math.max(actual, target) * 1.08, a = Math.max(0, actual) / max * 100, t = target / max * 100;
  const bad = invert ? actual > target : actual < target;
  return `<div class="ux-bullet" role="img" aria-label="${escapeHtml(label)}"><span class="ux-bullet-bar ${bad ? 'is-bad' : 'is-good'}" style="width:${a.toFixed(1)}%"></span><span class="ux-bullet-t" style="left:${t.toFixed(1)}%"></span></div>`;
}
function uxMeterBar(used, cap, label) {
  if (!(cap > 0)) return '';
  const p = Math.min(100, used / cap * 100);
  return `<div class="ux-meterbar ${p >= 100 ? 'is-full' : p >= 90 ? 'is-near' : ''}" role="img" aria-label="${escapeHtml(label)}"><span style="width:${p.toFixed(1)}%"></span></div>`;
}
function uxKpi(label, value, lines = [], extra = '') {
  return `<div class="ux-kpi"><div class="ux-kpi-l">${label}</div><div class="ux-kpi-v">${value}</div>${extra}${lines.filter(Boolean).map(l => `<div class="ux-kpi-s">${l}</div>`).join('')}</div>`;
}

/* ---------- status chip (guide §4.6): five states, each with a word; colour follows meaning ---------- */
const UX_TONE = { off: 'bad', at: 'warn', due: 'warn', new: 'info', unobs: 'neutral' };
function uxTone(k, t) { return /breach|below its limit/i.test(t) ? 'bad' : UX_TONE[k] || 'neutral'; }
const UX_GLYPH = { bad: '↘', warn: '▲', info: '✦', neutral: '?', good: '✓' };
function uxChip(k, t) { const tone = uxTone(k, t); return `<span class="ux-chip attn-k is-${tone}"><span aria-hidden="true">${UX_GLYPH[tone]}</span>${t}</span>`; }

/* ---------- decision queue (guide §7.1): the data's order (design §2.8: never a value ranking); who decides on each row ---------- */
function uxQueue(op, rows, cls = '') {
  if (!rows.length) return '<p class="ux-empty" role="status">No decisions waiting.</p>';
  return `<ul class="attn triage ux-queue ${cls}">${rows.map(([k, t, s, txt, d]) => {
    const D = deciderOf(d);
    return `<li class="attn-${k} ux-q"><div class="ux-q-top">${uxChip(k, t)}<b class="ux-q-site">${SK[s].name}</b></div><div class="ux-q-txt">${txt}</div><div class="ux-q-who"><span class="vh">Decides: </span>${who(op, D.p)}</div>${link(`decision/${d}`, `Decide<span class="vh">: ${SK[s].name}, ${escapeHtml(t)}</span>`, 'button ux-q-go')}</li>`;
  }).join('')}</ul>`;
}

/* ---------- side drawer (guide §8): stays in the page (closed: hidden from view and focus), opened by a named button ---------- */
function uxDrawer(id, title, body, wide = false) {
  return `<div class="ux-drawer ${wide ? 'is-wide' : ''}" id="${id}" role="dialog" aria-modal="true" aria-labelledby="${id}-h" data-open="false"><div class="ux-drawer-scrim" data-ux-close></div><div class="ux-drawer-panel"><header class="ux-drawer-head"><h2 id="${id}-h">${title}</h2><button type="button" class="ux-x" data-ux-close aria-label="Close ${escapeHtml(String(title).replace(/<[^>]+>/g, ''))}">×</button></header><div class="ux-drawer-body">${body}</div></div></div>`;
}
const uxOpener = (id, text, cls = '') => `<button type="button" class="ux-open ${cls}" data-ux-drawer="${id}" aria-haspopup="dialog" aria-controls="${id}">${text}</button>`;
let UX_LAST = null;
function uxOpen(id, from) {
  const d = document.getElementById(id); if (!d) return;
  UX_LAST = from || document.activeElement; d.dataset.open = 'true'; document.body.classList.add('ux-locked');
  setTimeout(() => d.querySelector('.ux-x')?.focus(), 0);
}
function uxClose(d) {
  d.dataset.open = 'false'; document.body.classList.remove('ux-locked');
  if (UX_LAST && document.contains(UX_LAST)) UX_LAST.focus(); UX_LAST = null;
}
document.addEventListener('click', e => {
  const o = e.target.closest('[data-ux-drawer]'); if (o) { e.preventDefault(); uxOpen(o.dataset.uxDrawer, o); return; }
  const c = e.target.closest('[data-ux-close]'); if (c) { e.preventDefault(); uxClose(c.closest('.ux-drawer')); }
});
document.addEventListener('keydown', e => {
  const d = document.querySelector('.ux-drawer[data-open="true"]'); if (!d) return;
  if (e.key === 'Escape') { e.preventDefault(); uxClose(d); return; }
  if (e.key === 'Tab') { /* keep focus inside the open drawer */
    const f = [...d.querySelectorAll('a[href],button:not([disabled]),input,select,summary,[tabindex="0"]')].filter(x => x.offsetParent !== null);
    if (!f.length) return; const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }
});

/* ---------- collapsible section (guide §2: L3 detail closed by default, its summary says what is inside) ---------- */
const secD = (title, body, sub = '', open = false) => `<details class="panel ux-disc"${open ? ' open' : ''}><summary><span class="ux-disc-t"><span class="ux-h2">${title}</span>${sub ? `<span class="ux-disc-sub">${sub}</span>` : ''}</span><span class="ux-disc-cue" aria-hidden="true"></span></summary><div class="ux-disc-body">${body}</div></details>`;
const uxTableView = (label, body) => `<details class="ux-tableview"><summary>${label}</summary><div class="ux-tableview-body">${body}</div></details>`;

/* ---------- tabs with a phone menu (guide §3.5, proposal U4): more than 4 tabs become a "Section" menu under 600 px ---------- */
function uxTabs(items, active, sub = false) {
  const nav = tabRow(items, active, sub);
  if (items.length <= 4) return nav;
  const cur = (items.find(([, id]) => id === active) || items[0])[0];
  return `<div class="ux-tabs">${nav}<details class="ux-tabmenu"><summary><span class="ux-tabmenu-k">Section:</span> ${cur}</summary><nav aria-label="${sub ? 'Section views' : 'Sections'}">${items.map(([l, id]) => link(id, l, id === active ? 'active' : '')).join('')}</nav></details></div>`;
}

/* ---------- the bridge as a horizontal waterfall (guide §5): target, each factor's effect, actual ---------- */
const GAP_SHORT = { 'kWh sold (demand volume)': 'kWh sold', 'Fuel the generator model does not explain': 'Fuel not explained', 'Meters not yet mapped to a customer': 'Unmapped meters' };
function uxBridge(op) {
  const o = OPS[op], T = opTotals(op), G = gapByHeading(op), cost = o.kind === 'cost';
  const sum = G.rows.reduce((a, r) => a + r.total, 0), dir = Math.abs(T.actual - T.plan - sum) < Math.abs(T.actual - T.plan + sum) ? 1 : -1;
  let rows = [...G.rows].sort((a, b) => (a.lens === b.lens ? 0 : a.lens === 'grow' ? -1 : 1) || Math.abs(b.total) - Math.abs(a.total));
  if (rows.length > 8) { const keep = rows.slice(0, 7), rest = rows.slice(7); rows = [...keep, { word: 'Other factors', lens: 'other', total: r2(rest.reduce((a, r) => a + r.total, 0)) }]; }
  let run = T.plan; const pts = [T.plan, T.actual];
  const steps = rows.map(r => { const a = run, b = run + dir * r.total; run = b; pts.push(a, b); return { ...r, a, b }; });
  const mn = Math.min(...pts), mx = Math.max(...pts), mag = Math.pow(10, Math.floor(Math.log10(Math.max(1, mx)))) / 2;
  const lo = Math.max(0, Math.floor((mn - (mx - mn) * 0.6) / mag) * mag), hi = mx + (mx - lo) * 0.03, X = v => ((v - lo) / (hi - lo) * 100).toFixed(2); /* axis starts at a round value below the lowest point; said in the caption */
  const bar = (a, b, c) => `<span class="ux-wf-bar ${c}" style="left:${X(Math.min(a, b))}%;width:${Math.max(0.6, X(Math.max(a, b)) - X(Math.min(a, b))).toFixed(2)}%"></span>`;
  const head = cost ? 'Cost' : 'Contribution';
  const line = (lab, val, b, cls = '') => `<li class="ux-wf-row ${cls}"><span class="ux-wf-lab">${lab}</span><span class="ux-wf-val">${val}</span><span class="ux-wf-track">${b}</span></li>`;
  const tone = r => { const worse = cost ? dir * r.total > 0 : dir * r.total < 0; return worse ? 'is-bad' : 'is-good'; };
  const big = Object.entries({ grow: G.grow, optimize: G.optimize }).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0];
  const title = cost ? `Cost and efficiency explain ${usdW(Math.abs(G.optimize))} of the ${usdW(Math.abs(T.actual - T.plan))} over target`
    : `${big[0] === 'optimize' ? 'Cost and efficiency explain' : 'Revenue explains'} ${usdW(Math.abs(big[1]))} of the ${usdW(Math.abs(T.actual - T.plan))} gap`;
  const list = [line(`${head} target`, usdW(T.plan), bar(lo, T.plan, 'is-total'), 'is-end'),
    ...steps.map(s => line(`${s.lens === 'other' ? '' : `<span class="ux-wf-h">${s.lens === 'grow' ? 'Grow' : 'Optimize'}</span>`}${GAP_SHORT[s.word] || s.word}`, usdW(cost ? dir * s.total : s.total, true), bar(s.a, s.b, tone(s) + (s.residual ? ' is-resid' : '')))),
    line(`${head}, October`, usdW(T.actual), bar(lo, T.actual, 'is-total is-actual'), 'is-end')].join('');
  return `<section class="panel ux-chart" aria-labelledby="uxb-h"><div class="panel-head"><div><h2 id="uxb-h">Where the gap comes from</h2><p>${title}</p></div></div><ol class="ux-wf" aria-label="${head} from target to October, factor by factor">${list}</ol>${lo > 0 ? `<p class="ux-axis-note">Bars start at ${usdW(lo)}, not at zero, so the factors’ effects can be compared.</p>` : ''}${uxTableView('Show as table, by Site', gapSplit(op))}</section>`;
}

/* ---------- the value chain as bars on one baseline (guide §5): a stage with no source is an outlined empty bar ---------- */
function uxChain(op, sk) {
  const st = chainStages(op, sk), unitOf = v => /^\$/.test(v) ? '$' : (String(v).match(/(kWh|crate-days|L)\b/) || [, ''])[1], valOf = v => Number((String(v).match(/[\d,.]+/) || ['0'])[0].replace(/,/g, ''));
  const max = {}; st.forEach(x => { if (x[0] !== 'leak' && x[3] !== 'na' && /\d/.test(x[1])) { const u = unitOf(x[1]); max[u] = Math.max(max[u] || 0, valOf(x[1])); } });
  const quiet = s => String(s || '').replace(/\s*·\s*(Emulated|Recorded|Measured)\b/g, '').replace(/^(Emulated|Recorded|Measured)$/, '');
  const rows = st.map(x => {
    if (x[0] === 'leak') return x[1] ? `<li class="ux-vc-leak"><span aria-hidden="true">↳</span> ${x[1]}</li>` : '';
    const na = x[3] === 'na' || !/\d/.test(x[1]), u = unitOf(x[1]), w = na ? 100 : (max[u] ? valOf(x[1]) / max[u] * 100 : 0);
    return `<li class="ux-vc-stage ${na ? 'is-na' : ''}"><span class="ux-vc-lab">${x[0]}<small>${quiet(x[2])}</small></span><span class="ux-vc-val">${x[1]}</span><span class="ux-vc-track"><span class="ux-vc-bar" style="width:${w.toFixed(1)}%"></span></span></li>`;
  }).join('');
  return `<section class="panel ux-chart" aria-labelledby="uxv-h-${sk || op}"><div class="panel-head"><div><h2 id="uxv-h-${sk || op}">Where value leaks</h2><p>${sk ? SK[sk].name : OPS[op].name}, October: each stage against the one before it</p></div></div><ol class="ux-vc">${rows}</ol>${uxTableView('Show the stages in detail', chainStrip(op, sk))}</section>`;
}

/* ---------- the four headings as tiles, each opening its full card in a drawer (guide §9, proposal U5) ---------- */
function uxCatTile(op, k, C) {
  const [name, ico] = LENS[k], finds = ATTN[op].filter(r => findingHeading(r) === k).length, P = planCase(op);
  const items = P.ids.filter(id => optHeadings(id).some(h => h[0] === k)).length + (k === 'protect' ? proactiveOf(op).length : 0);
  const pos = k === 'assure' ? (C.assure?.pos || 'The evidence behind every heading') : k === 'protect' ? protectCard(op).pos : (C[k]?.pos || '');
  const whole = t => String(t).replace(/\$([\d,]+\.\d{2})\b/g, (m, v) => '$' + Math.round(+v.replace(/,/g, '')).toLocaleString('en-US')); /* U3 at the tile */
  const counts = [finds ? `${num(finds)} Finding${finds === 1 ? '' : 's'}` : 'No Finding', items ? `${num(items)} plan item${items === 1 ? '' : 's'}` : ''].filter(Boolean).join(' · ');
  return `<div class="ux-cat" data-tile="${k}"><div class="ux-cat-h">${icon(ico)}<h3>${name}</h3></div><p class="ux-cat-pos">${whole(pos)}</p><p class="ux-cat-n">${counts}</p>${uxOpener(`uxd-${op}-${k}`, `View ${k === 'protect' ? 'measures' : k === 'assure' ? 'evidence' : 'factors'}<span class="vh">: ${name}</span> <span aria-hidden="true">›</span>`, 'ux-cat-go')}</div>`;
}
function uxCats(op) {
  const C = CARDS[op](), ks = Object.keys(LENS);
  const about = 'The four headings sit over one structure: each factor under one heading, so no figure is counted twice and the headings are never added together. Grow and Optimize effects explain the contribution gap; cash collected sits under Optimize, outside that gap; Protect shows measures against target with values at stake listed beside, never money; Assure shows the evidence, with the bridge, and adds no money.';
  return `<section class="ux-cats-wrap" aria-labelledby="uxc-h"><div class="ux-row-head"><h2 id="uxc-h">By outcome</h2><details class="ux-about"><summary>About these figures</summary><p>${about}</p></details></div><div class="ux-cats ocards">${ks.map(k => uxCatTile(op, k, C)).join('')}</div>${ks.map(k => uxDrawer(`uxd-${op}-${k}`, LENS[k][0], categoryCard(op, k, C), true)).join('')}</section>`;
}

/* ---------- the plan card and the insight (L2 aside) ---------- */
function uxPlanCard(op) {
  const P = planCase(op), o = OPS[op], M2 = o.t.portfolio_constraints, budget = op === 'lakeside' ? LS.budget : M2.budget_usd_nov_dec, S = PSTATE();
  const moves = P.rows.slice(0, 3).map(r => `<li>${link(`decision/${DEC_SEE_ALSO[r.id] || decOf(r.id).id}`, optLabel(r.id))} <small>${SK[OPT[r.id]._site].name}</small></li>`).join('');
  return `<section class="panel ux-plan" aria-labelledby="uxp-h"><div class="ux-plan-head"><h2 id="uxp-h">The plan, ${periodWords()}</h2><span class="status-pill is-${S.state === 'PROPOSED' ? 'proposed' : S.state === 'APPROVED' ? 'approved' : 'waiting'}">${STATE_WORD[S.state]} · v${num(S.version)}</span></div>
 <p class="ux-plan-who">Approver: ${who(op, execOf(op))}</p>
 ${meter('Budget used', P.spend, budget, usdW)}${crewMeters(op, P)}
 <h3 class="ux-h3">First three moves</h3><ol class="ux-moves">${moves}</ol>
 <div class="ux-plan-go">${btn('portfolio/act-first/plan', 'Review the plan', true)}${link('portfolio/act-first', 'Act first', 'ux-link')}</div></section>`;
}
function uxInsight(op) {
  return CONTRAST[op].map(([h, p, d, l]) => `<section class="panel ux-insight" aria-labelledby="uxi-h"><div class="ux-eyebrow">Sites that look alike need different levers</div><h2 id="uxi-h">${h}</h2><p>${p}</p>${link(`decision/${d}`, `Open ${l} →`)}</section>`).join('');
}

/* ---------- Portfolio Overview (guide §9) ---------- */
function uxOverview(op) {
  const o = OPS[op], T = opTotals(op), G = gapByHeading(op), cost = o.kind === 'cost', P = planCase(op), Pp = o.t.portfolio, M2 = o.t.portfolio_constraints;
  const budget = op === 'lakeside' ? LS.budget : M2.budget_usd_nov_dec, val = op === 'lakeside' ? P.value : op === 'harvest' ? harvestValue() : derivedPlan('metro').value;
  const gap = T.actual - T.plan, big = Object.entries({ grow: G.grow, optimize: G.optimize }).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0];
  const hl = cost ? `Charging and depot cost is ${usdW(Math.abs(gap))} ${gap > 0 ? 'over' : 'under'} target in October; all ${num(Pp.departures_met)} required departures were met, at ${usd2(Pp.cost_per_departure_actual)} each.`
    : `Contribution is ${usdW(Math.abs(gap))} ${gap < 0 ? 'below' : 'above'} target in October; ${big[0] === 'optimize' ? 'cost and efficiency explain' : 'revenue explains'} ${usdW(Math.abs(big[1]))} of it.`;
  const resid = Math.abs(G.residual) > 0.005;
  const k1 = uxKpi(cost ? 'Charging and depot cost' : 'Contribution', fig(`port:${op}:actual`, usdW(T.actual)),
    [`Target ${usdW(T.plan)} · ${Math.round(T.actual / T.plan * 100)}% of target`, `${fig(`port:${op}:cov`, pct(Pp.coverage.cost_recorded_share, 1))} of cost on records`], uxBullet(T.actual, T.plan, `${cost ? 'Cost' : 'Contribution'} ${usdW(T.actual)} against a target of ${usdW(T.plan)}`, cost));
  const k2 = uxKpi('Gap to target', fig(`port:${op}:variance`, usdW(T.variance, true)),
    cost ? [`Optimize ${usdW(G.optimize, true)}`, resid ? `${usdW(G.residual, true)} not attributed yet: a target stated only as a bill total` : 'All of it explained by factors']
      : [`Grow ${usdW(G.grow, true)} · Optimize ${usdW(G.optimize, true)}`, resid ? `${usdW(G.residual, true)} not explained yet` : 'All of it explained by factors']);
  const k3 = uxKpi(`Plan spend · ${periodWords()}`, `${fig(`port:${op}:spend`, usdW(P.spend))} <small>of ${usdW(budget)}</small> ${uxMark('QUOTE')}`,
    [`${num(P.visits)} of ${num(derivedPlan(op).crew_visits_limit)} ${o.crewWord}`, `${STATE_WORD[PSTATE().state]}: awaiting the operator executive’s approval`], uxMeterBar(P.spend, budget, `${usdW(P.spend)} of ${usdW(budget)} budget`));
  const k4 = uxKpi('Options’ value, 12 months', `<span>${fig(`port:${op}:m12`, val === 0 ? '$0' : usdW(val, true))}${op === 'harvest' ? '' : dvTag()}</span> ${uxMark('MODELLED')}`,
    [op === 'harvest' ? 'Includes an assumed recovery share (80%) at Kirinyaga' : 'Valued options only; not realised until records show it']);
  const n = ATTN[op].length;
  return `<div class="ux-overview"><p class="headline ux-headline">${hl}</p>
 <div class="heroes ux-kpis">${k1}${k2}${k3}${k4}</div>
 <div class="ux-main-aside"><section class="panel ux-queue-panel" aria-labelledby="uxq-h"><div class="panel-head"><div><h2 id="uxq-h">Needs a decision <span class="ux-count">${num(n)}</span></h2><p>Each issue with its site and who decides. The system values the options; a person chooses.</p></div>${link('portfolio/act-first', 'Act first ›', 'ux-link')}</div>${uxQueue(op, ATTN[op].slice(0, 6))}${n > 6 ? `<p class="ux-more">${link('portfolio/act-first', `View all ${num(n)} in Act first`)}</p>` : ''}</section>
 <div class="ux-aside">${uxPlanCard(op)}${uxInsight(op)}</div></div>
 <div class="ux-two">${uxBridge(op)}${uxChain(op)}</div>
 ${uxCats(op)}</div>`;
}

/* ---------- Decision page header (guide §2.3, §7.2): the recommendation in one line and the primary action ---------- */
function uxDecisionHead(id) {
  const d = decById(id), op = SK[d.site].op, D = deciderOf(id), inPlan = planItemsV1(op);
  const rec = d.opts.find(x => OPT[x].disposition === 'RECOMMENDED') || d.opts.find(x => inPlan.includes(x));
  const x = rec ? OPT[rec] : null, [ev] = x ? optEffect(x) : ['—'], [cv] = x ? optCost(x) : ['—'];
  const choose = `<p class="prose">Choosing records the choice under the chooser’s name. The steps below say which Actions it creates and whether it is released at once or waits for the plan’s approval.</p><div class="ux-choose-steps" data-ux-clone=".who-decides .wd-steps"></div><p class="note">Choosing is not wired in this mock-up.</p>`;
  return `<section class="panel ux-dhead" aria-labelledby="uxdh-h"><div class="ux-eyebrow">${rec ? 'Recommended' : 'No option recommended'}</div><h2 id="uxdh-h">${rec ? optLabel(rec) : 'Each option valued against no action'}</h2>
 ${rec ? `<dl class="ux-dfacts"><div><dt>Result against no action</dt><dd>${fig(`opt:${rec}:effect`, ev)} ${uxMark(optClass(x))}${DV_OPT[rec] ? dvTag(DV_OPT[rec]) : ''}</dd></div><div><dt>One-off cost · who pays</dt><dd>${cv} <small>${whoPays(x)}</small></dd></div><div><dt>Who chooses</dt><dd>${who(op, D.p)}</dd></div></dl>` : ''}
 <div class="ux-dgo">${rec ? uxOpener(`uxc-${id}`, 'Choose this option', 'button primary') : ''}<a class="ux-link" href="#uxopts-${id}">Compare all options</a></div>${rec ? uxDrawer(`uxc-${id}`, `Choose: ${optLabel(rec)}`, choose) : ''}</section>`;
}
document.addEventListener('click', e => { /* the choose drawer shows the page's own "who decides" steps */
  const o = e.target.closest('[data-ux-drawer^="uxc-"]'); if (!o) return;
  const t = document.getElementById(o.dataset.uxDrawer)?.querySelector('[data-ux-clone]'), src = document.querySelector(t?.dataset.uxClone);
  if (t && src && !t.childElementCount) t.innerHTML = src.outerHTML;
}, true);

/* ---------- Site overview tiles (guide §2.3 Site row) ---------- */
function uxSiteTiles(sk) {
  const s = siteM(sk), op = SK[sk].op, o = OPS[op], t = tree(sk), decs = DEC.filter(d => d.site === sk), att = ATTN[op].filter(r => r[2] === sk);
  if (t.plan == null) return '';
  const cost = o.kind === 'cost';
  return `<div class="heroes ux-kpis">${uxKpi(cost ? 'Cost per required departure met' : 'Contribution', fig(`node:${sk}:root`, cost ? fmtU(t.actual, t.unit) : usdW(t.actual)), [`Target ${cost ? fmtU(t.plan, t.unit) : usdW(t.plan)}`], cost ? '' : uxBullet(t.actual, t.plan, `Contribution ${usdW(t.actual)} against a target of ${usdW(t.plan)}`))}
 ${uxKpi('Gap to target', usdW(s.period.variance, true), [cost ? 'on cost' : 'October'])}
 ${uxKpi('Needs a decision', `${num(att.length)}`, [att.length ? att.map(r => r[1]).join(' · ') : 'Nothing waiting'])}
 ${uxKpi('Decisions open', `${num(decs.length)}`, [decs.length ? `${decs.map(d => d.q).slice(0, 2).join(' · ')}` : 'None'])}</div>`;
}
