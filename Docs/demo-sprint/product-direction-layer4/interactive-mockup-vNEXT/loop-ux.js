/* ===== loop-ux.js: the UI/UX guide's components (Docs/design-system/uiux-guide.md), wave 1 =====
   Presentation only. Every figure is read through the other modules' functions (opTotals, gapByHeading, planCase, ATTN,
   CARDS, categoryCard, chainStages, ...); nothing is typed here. Levels (guide §2.1): L1 glance (headline, KPI tiles),
   L2 queue and decide (decision queue, plan card), L3 explain (bridge, value chain, category tiles), L4 evidence (drawers,
   "Show as table", the evidence drawer). The full earlier panels stay in the page, inside drawers and table views, so
   nothing is lost and the content checks read them unchanged. */

/* ---------- numbers at a glance (guide §5.1, proposal U3): whole currency at L1 and L2 ---------- */
const usdW = (n, sign = false) => n === null || n === undefined ? usd(n) : usd(Math.round(n), sign);
const wholeText = t => String(t).replace(/\$([\d,]+\.\d{1,2})\b/g, (m, v) => '$' + Math.round(+v.replace(/,/g, '')).toLocaleString('en-US'));
/* review states (guide §7.6): ?state=empty or ?state=loading shows the designed empty and loading states */
const UX_STATE = (() => { try { return new URLSearchParams(location.search).get('state'); } catch (e) { return null; } })();

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
  const r = actual / target, off = invert ? r - 1 : 1 - r, st = off <= 0 ? 'is-good' : off <= 0.05 ? 'is-warn' : 'is-bad';
  return `<div class="ux-bullet" role="img" aria-label="${escapeHtml(label)}"><span class="ux-bullet-bar ${st}" style="width:${a.toFixed(1)}%"></span><span class="ux-bullet-t" style="left:${t.toFixed(1)}%"></span></div>`;
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
const UX_TONE = { off: 'bad', at: 'warn', due: 'warn', new: 'info', unobs: 'neutral', ok: 'good' };
function uxTone(k, t) { return /breach|below its limit/i.test(t) ? 'bad' : UX_TONE[k] || 'neutral'; }
const UX_GLYPH = { bad: '↘', warn: '▲', info: '✦', neutral: '?', good: '✓' };
const uxTileStatus = (k, op) => { if (k !== 'protect') return ''; const pc = protectCard(op); return `<p class="ux-cat-st">${uxChip(pc.broken ? 'off' : 'ok', pc.broken ? 'Limits broken' : 'All held')}</p>`; };
function uxChip(k, t) { const tone = uxTone(k, t); return `<span class="ux-chip attn-k is-${tone}"><span aria-hidden="true">${UX_GLYPH[tone]}</span>${t}</span>`; }

/* ---------- decision queue (guide §7.1): the data's order (design §2.8: never a value ranking); at stake, due and who decides on each row.
   At stake: the recommended option's 12-month result against no action, with its marker; else the right's value at stake; else the
   option's own words ("No saving claimed"); else "Not available yet". Due: the right's deadline; else the date the issue names. ---------- */
const UX_MON = '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)';
const uxRights = d => (d.rights || []).map(k => { try { return rightsOf(k); } catch (e) { return null; } }).filter(Boolean);
function uxRec(d) { const op = SK[d.site].op, inPlan = planItemsV1(op); return d.opts.find(x => OPT[x].disposition === 'RECOMMENDED') || d.opts.find(x => inPlan.includes(x)); }
function uxDue(decId, txt) {
  const d = decById(decId), r = d && uxRights(d).find(r => r.deadline);
  if (r) return fdate(r.deadline);
  const m = String(txt).match(new RegExp(`(?:due|lapses(?: on)?|by|deadline)\\s+(\\d{1,2} ${UX_MON})`));
  return m ? m[1] : '<span class="muted">No deadline</span>';
}

function uxStake(decId) {
  const p = uxStakeParts(decId);
  return p.value ? `<span class="ux-q-v">${p.value}</span><small>${p.note}</small>` : p.word ? `<span class="ux-q-word">${p.word}</span>` : '<span class="muted">Not available yet</span>';
}
/* the at-stake figure in parts (value, note, certainty), so the row stays scannable and the certainty sits in the row's detail */
function uxStakeParts(decId) {
  const d = decById(decId); if (!d) return {};
  const rec = uxRec(d), x = rec ? OPT[rec] : null, ev = x ? String(optEffect(x)[0]) : '';
  if (/^[+−-]?\$/.test(ev)) { const P = planCase(SK[d.site].op), inP = P.ids.includes(rec), capAv = x.avoided_capex != null && !/^[+−-]/.test(ev);
    return { value: wholeText(ev), num: Number(ev.replace(/[^\d.−-]/g, '').replace('−', '-')) || 0, note: `${capAv ? 'capital avoided, not a saving' : '12 months'} · ${inP ? 'in the plan' : 'not in the plan'}`, cls: optClass(x), dv: !!DV_OPT[rec], rec }; }
  const st = uxRights(d).find(r => r.stake), amt = st && (String(st.stake).match(/\$[\d,]+(?:\.\d+)?/) || [])[0];
  if (amt) return { value: wholeText(amt), num: Number(amt.replace(/[^\d.]/g, '')) || 0, note: /cover/i.test(st.stake) ? 'cover kept claimable' : /credit/i.test(st.stake) ? 'possible credit' : 'at stake', cls: 'EXPOSURE', rec };
  if (ev && !/^Not (valued|modelled)/i.test(ev)) return { word: ev, num: 0, rec };
  return { num: 0, rec };
}
const UX_ISO_MON = { Jan: '01', Feb: '02', Mar: '03', Apr: '04', May: '05', Jun: '06', Jul: '07', Aug: '08', Sep: '09', Oct: '10', Nov: '11', Dec: '12' };
function uxDueIso(decId, txt) {
  const d = decById(decId), r = d && uxRights(d).find(r => r.deadline); if (r) return String(r.deadline).slice(0, 10);
  const m = String(txt).match(new RegExp(`(?:due|lapses(?: on)?|by|deadline)\\s+(\\d{1,2}) (${UX_MON})`)); return m ? `2026-${UX_ISO_MON[m[2]]}-${m[1].padStart(2, '0')}` : '';
}
/* decision queue (guide §7.1, wave 2): a short title and scannable columns; the explanation and the certainty one click away */
/* the value chain as leaks (guide §5, wave 2): each stage, then what is lost before the next one, drawn on the leaks' own scale */
function uxChain(op, sk) {
  const st = chainStages(op, sk), unitOf = v => /^\$/.test(v) ? '$' : (String(v).match(/(kWh|crate-days|L)\b/) || [, ''])[1], valOf = v => Number((String(v).match(/[\d,.]+/) || ['0'])[0].replace(/,/g, ''));
  const quiet = s => String(s || '').replace(/\s*·\s*(Emulated|Recorded|Measured)\b/g, '').replace(/^(Emulated|Recorded|Measured)$/, '');
  let prev = null; const leaks = [];
  const rows = st.map(x => {
    if (x[0] !== 'leak') { const na = x[3] === 'na' || !/\d/.test(x[1]); prev = na ? null : { v: valOf(x[1]), u: unitOf(x[1]), name: x[0] }; return { stage: x, na }; }
    const parts = String(x[1] || '').split(/\s*·\s*/).filter(Boolean).map(p => { const m = p.match(/^(.*?)(\$[\d,.]+|[\d,.]+\s*(?:kWh|crate-days|L)|\b\d[\d,.]*\b)\s*$/) || p.match(/^(.*?)(\$[\d,.]+|[\d,.]+\s*(?:kWh|crate-days|L))/);
      if (!m || !prev) return { text: p }; const v = valOf(m[2]), pct = prev.v ? v / prev.v * 100 : null; const L = { text: p, label: m[1].replace(/[:\s]+$/, ''), amount: m[2].trim(), pct, of: prev.name.toLowerCase() }; leaks.push(L); return L; });
    return { parts };
  });
  const maxPct = Math.max(1, ...leaks.map(l => l.pct || 0)), top = [...leaks].sort((a, b) => (b.pct || 0) - (a.pct || 0))[0];
  const html = rows.map(r => r.stage ? `<li class="ux-vc-stage ${r.na ? 'is-na' : ''}"><span class="ux-vc-lab">${r.stage[0]}<small>${quiet(r.stage[2])}</small></span><span class="ux-vc-val">${r.stage[1]}</span></li>`
    : (r.parts || []).map(p => p.pct != null ? `<li class="ux-vc-loss"><span class="ux-vc-lab"><span aria-hidden="true">↳</span> ${p.label || 'Lost'}</span><span class="ux-vc-val">${p.amount}<small>${p.pct < 0.05 ? 'none' : `${p.pct.toFixed(1)}% of ${p.of}`}</small></span><span class="ux-vc-track"><span class="ux-vc-bar" style="width:${Math.max(p.pct > 0.05 ? 1.5 : 0, p.pct / maxPct * 100).toFixed(1)}%"></span></span></li>` : `<li class="ux-vc-leak"><span aria-hidden="true">↳</span> ${p.text}</li>`).join('')).join('');
  const title = top && top.pct > 0.05 ? `The biggest leak: ${top.label || 'lost'} ${top.amount}, ${top.pct.toFixed(1)}% of ${top.of}` : `${sk ? SK[sk].name : OPS[op].name}, October: no leak measured`;
  return `<section class="panel ux-chart" aria-labelledby="uxv-h-${sk || op}"><div class="panel-head"><div><h2 id="uxv-h-${sk || op}">Where value leaks</h2><p>${title}</p></div></div><ol class="ux-vc">${html}</ol><p class="ux-axis-note">Loss bars are drawn against the largest loss; each says its share of the stage before it.</p>${uxTableView('Show the stages in detail', chainStrip(op, sk))}</section>`;
}
/* an outcome tile: its position, a target-against-actual visual and its counts (wave 2) */
function uxCatTile(op, k, C) {
  const [name, ico] = LENS[k], finds = ATTN[op].filter(r => findingHeading(r) === k).length, P = planCase(op), o = OPS[op];
  const items = P.ids.filter(id => optHeadings(id).some(h => h[0] === k)).length + (k === 'protect' ? proactiveOf(op).length : 0);
  const pos = k === 'assure' ? (C.assure?.pos || 'The evidence behind every heading') : k === 'protect' ? protectCard(op).pos : (C[k]?.pos || '');
  const counts = [finds ? `${num(finds)} Finding${finds === 1 ? '' : 's'}` : 'No Finding', items ? `${num(items)} plan item${items === 1 ? '' : 's'}` : ''].filter(Boolean).join(' · ');
  let vis = '';
  if (k === 'grow' && o.kind !== 'cost') { const a = sumNodes(op, 'actual', 'revenue'), t = sumNodes(op, 'plan', 'revenue'); vis = uxBullet(a, t, `Revenue ${usdW(a)} against a target of ${usdW(t)}`); }
  if (k === 'optimize') { const a = o.kind === 'cost' ? opTotals(op).actual : sumNodes(op, 'actual', 'cost_to_serve'), t = o.kind === 'cost' ? opTotals(op).plan : sumNodes(op, 'plan', 'cost_to_serve'); vis = uxBullet(a, t, `Cost ${usdW(a)} against a target of ${usdW(t)}`, true); }
  if (k === 'protect') { const pc = protectCard(op); vis = pc.total ? `<div class="ux-seg" role="img" aria-label="${num(pc.broken)} of ${num(pc.total)} limits broken">${Array.from({ length: pc.total }, (_, i) => `<span class="${i < pc.broken ? 'is-bad' : 'is-good'}"></span>`).join('')}</div>` : ''; }
  if (k === 'assure') { const c = o.t.portfolio.coverage.cost_recorded_share; vis = `<div class="ux-meterbar is-neutral" role="img" aria-label="${pct(c, 1)} of October cost backed by records"><span style="width:${(c * 100).toFixed(1)}%"></span></div>`; }
  return `<div class="ux-cat" data-tile="${k}"><div class="ux-cat-h">${icon(ico)}<h3>${name}</h3></div>${uxTileStatus(k, op)}<p class="ux-cat-pos">${wholeText(pos)}</p>${vis}<p class="ux-cat-n">${counts}</p>${uxOpener(`uxd-${op}-${k}`, `View ${k === 'protect' ? 'measures' : k === 'assure' ? 'evidence' : 'drivers'}<span class="vh">: ${name}</span> <span aria-hidden="true">›</span>`, 'ux-cat-go')}</div>`;
}

/* one row per decision (review 2b): the issues behind it become its chips and its "Why"; counts are decisions, not issues */
function uxMergeRows(rows) {
  const by = new Map();
  rows.forEach(([k, t, s, txt, d], i) => { if (!by.has(d)) by.set(d, { d, s, i, issues: [] }); by.get(d).issues.push([k, t, txt]); });
  return [...by.values()];
}
const uxDecCount = rows => new Set(rows.map(r => r[4])).size;
const UX_RANK = { bad: 0, warn: 1, info: 2, neutral: 3, good: 4 };
const uxUrgency = iso => { if (!iso) return 'none'; const d = daysUntil(iso); return d <= 7 ? 'week' : iso.slice(0, 7) === String(AS_OF).slice(0, 7) || d <= 31 ? 'month' : 'later'; };
const UX_URG = { week: 'Due this week', month: 'Due this month', later: 'Due later', none: 'No deadline' };
let UX_QN = 0;
function uxQueue(op, rows, cls = '') {
  if (UX_STATE === 'loading') return `<div class="ux-skel" role="status"><span class="vh">Loading decisions…</span>${'<span class="ux-skel-row" aria-hidden="true"></span>'.repeat(3)}</div>`;
  if (UX_STATE === 'empty' || !rows.length) return '<p class="ux-empty" role="status">No decisions waiting. New issues appear here when the next day of records is in.</p>';
  const M = uxMergeRows(rows);
  const items = M.map((m, i) => {
    const { d, s } = m, D = deciderOf(d), dec = decById(d), id = `uxq-${++UX_QN}`, P = uxStakeParts(d), due = m.issues.map(([, , txt]) => uxDueIso(d, txt)).filter(Boolean).sort()[0] || '';
    const tones = m.issues.map(([k, t]) => uxTone(k, t)), worst = [...tones].sort((a, b) => UX_RANK[a] - UX_RANK[b])[0];
    const stake = P.value ? `<span class="ux-q-v">${P.value}</span><small>${P.note}</small>` : P.word ? `<span class="ux-q-word">${P.word}</span>` : '<span class="muted">Not available yet</span>';
    const ck = P.cls && (CLS[P.cls] || [])[1], cert = P.value && P.cls ? `<span class="ux-q-cert">How sure: ${ck === 'rec' || ck === 'der' ? 'recorded' : `${uxMark(P.cls)}`}${P.dv ? ` · ${dvTag()} design estimate, not yet tested on your recorded data` : ''}</span>` : '';
    const why = m.issues.map(([k, t, txt]) => `<span class="ux-q-issue-line"><b>${t}:</b> ${txt}</span>`).join('');
    return `<li class="attn-${m.issues[0][0]} ux-q" data-order="${i}" data-site="${s}" data-kind="${worst}" data-kinds="${[...new Set(tones)].join(' ')}" data-due="${due}" data-urg="${uxUrgency(due)}" data-stake="${P.num || 0}" data-issues="${m.issues.length}"><div class="ux-q-issue"><div class="ux-q-top">${m.issues.map(([k, t]) => uxChip(k, t)).join('')}<b class="ux-q-title">${dec ? dec.q : m.issues[0][1]}</b></div><button type="button" class="ux-q-more" aria-expanded="false" aria-controls="${id}">Why${m.issues.length > 1 ? ` (${num(m.issues.length)} issues)` : ''}<span class="vh">: ${escapeHtml(dec ? dec.q : '')}</span></button><div class="ux-q-why is-collapsed" id="${id}">${why}${cert ? `<span class="ux-q-issue-line">${cert}</span>` : ''}</div></div><div class="ux-q-site"><span class="ux-q-k">Site: </span>${SK[s].name}</div><div class="ux-q-stake"><span class="ux-q-k">At stake: </span>${stake}</div><div class="ux-q-due"><span class="ux-q-k">Due: </span>${due ? fdate(due) : '<span class="muted">No deadline</span>'}</div><div class="ux-q-who"><span class="ux-q-k">Decides: </span>${who(op, D.p)}</div>${link(`decision/${d}`, `Decide<span class="vh">: ${escapeHtml(dec ? dec.q : '')}, ${SK[s].name}</span>`, 'button ux-q-go')}</li>`;
  });
  const sites = [...new Set(M.map(m => m.s))], kinds = [...new Set(M.flatMap(m => m.issues.map(([k, t]) => uxTone(k, t))))];
  const KW = { bad: 'Off target or breached', warn: 'At a limit or deadline', info: 'New or opportunity', neutral: 'Not explained yet', good: 'On target' };
  const dl = `uxsl-${UX_QN}`;
  const tools = M.length > 1 ? `<div class="ux-qtools" role="group" aria-label="Filter, sort and group the decisions">
   ${sites.length > 1 ? `<label>Site <input type="search" data-qf="site" list="${dl}" placeholder="All sites" autocomplete="off" aria-label="Filter by Site: type a Site name"><datalist id="${dl}">${sites.map(s => `<option value="${SK[s].name}"></option>`).join('')}</datalist></label>` : ''}
   ${kinds.length > 1 ? `<label>Status <select data-qf="kind"><option value="">All</option>${kinds.map(k => `<option value="${k}">${KW[k]}</option>`).join('')}</select></label>` : ''}
   <label>Sort <select data-qs><option value="order">Priority</option><option value="due">Due date</option><option value="stake">At stake</option></select></label>
   <label>Group <select data-qg><option value="">None</option><option value="urg">By urgency</option>${sites.length > 1 ? '<option value="site">By site</option>' : ''}</select></label>
   <label class="ux-dense"><input type="checkbox" data-qd> Compact</label>
   <span class="ux-qcount" role="status" aria-live="polite">${num(M.length)} of ${num(M.length)}</span></div>` : '';
  return `<div class="ux-queue-wrap">${tools}<div class="ux-qh" aria-hidden="true"><span>Decision</span><span>Site</span><span>At stake</span><span>Due</span><span>Who decides</span><span></span></div><ul class="attn triage ux-queue ${cls}">${items.join('')}</ul></div>`;
}
function uxApplyQueue(wrap) {
  const ul = wrap.querySelector('.ux-queue'), get = s => wrap.querySelector(s)?.value || '';
  const q = get('[data-qf="site"]').trim().toLowerCase(), fKind = get('[data-qf="kind"]'), sort = get('[data-qs]') || 'order', group = get('[data-qg]');
  wrap.classList.toggle('is-dense', !!wrap.querySelector('[data-qd]')?.checked);
  ul.querySelectorAll('.ux-grp').forEach(g => g.remove());
  const li = [...ul.querySelectorAll('li.ux-q')];
  li.forEach(x => { x.hidden = !!((q && !SK[x.dataset.site].name.toLowerCase().includes(q)) || (fKind && !x.dataset.kinds.split(' ').includes(fKind))); });
  const key = x => sort === 'due' ? (x.dataset.due || '9999') : sort === 'stake' ? -Math.abs(+x.dataset.stake || 0) : +x.dataset.order;
  const gk = x => group === 'site' ? SK[x.dataset.site].name : group === 'urg' ? ['week', 'month', 'later', 'none'].indexOf(x.dataset.urg) : '';
  const gl = x => group === 'site' ? SK[x.dataset.site].name : UX_URG[x.dataset.urg];
  li.sort((a, b) => (group ? (gk(a) < gk(b) ? -1 : gk(a) > gk(b) ? 1 : 0) : 0) || (key(a) < key(b) ? -1 : key(a) > key(b) ? 1 : +a.dataset.order - +b.dataset.order));
  let last = null;
  li.forEach(x => { if (group && !x.hidden && gk(x) !== last) { last = gk(x); const n = li.filter(y => !y.hidden && gk(y) === last).length; ul.insertAdjacentHTML('beforeend', `<li class="ux-grp"><h3>${gl(x)} <span class="ux-count">${num(n)}</span></h3></li>`); } ul.appendChild(x); });
  const shown = li.filter(x => !x.hidden).length; wrap.querySelector('.ux-qcount').textContent = `${num(shown)} of ${num(li.length)}`;
  ul.classList.toggle('is-filtered', !!(q || fKind || group || sort !== 'order'));
}

/* the bridge as a stepped waterfall, the page's hero chart (guide §5, review 2b): target, each factor's step from the running
   total, October. The axis starts at a round value below the lowest point and the break is drawn and said; each step links
   to the decision on its driver, with its detail on hover and keyboard focus. */
function uxBridge(op) {
  const o = OPS[op], T = opTotals(op), G = gapByHeading(op), cost = o.kind === 'cost';
  const sum = G.rows.reduce((a, r) => a + r.total, 0), dir = Math.abs(T.actual - T.plan - sum) < Math.abs(T.actual - T.plan + sum) ? 1 : -1;
  let rows = [...G.rows].sort((a, b) => (a.lens === b.lens ? 0 : a.lens === 'grow' ? -1 : 1) || Math.abs(b.total) - Math.abs(a.total));
  if (rows.length > 8) { const keep = rows.slice(0, 7), rest = rows.slice(7); rows = [...keep, { word: 'Other factors', lens: 'other', total: r2(rest.reduce((a, r) => a + r.total, 0)) }]; }
  let run = T.plan; const pts = [T.plan, T.actual];
  const steps = rows.map(r => { const a = run, b = run + dir * r.total; run = b; pts.push(a, b); return { ...r, a, b }; });
  const mn = Math.min(...pts), mx = Math.max(...pts), span = Math.max(1, mx - mn), mag = Math.pow(10, Math.floor(Math.log10(span)));
  const lo = Math.max(0, Math.floor((mn - span * 0.5) / mag) * mag), hi = mx + span * 0.04, X = v => ((v - lo) / (hi - lo) * 100);
  const bar = (a, b, c) => `<span class="ux-wf-bar ${c}" style="left:${X(Math.min(a, b)).toFixed(2)}%;width:${Math.max(0.6, X(Math.max(a, b)) - X(Math.min(a, b))).toFixed(2)}%"></span>`;
  const head = cost ? 'Cost' : 'Contribution', shown = st => cost ? dir * st.total : st.total, gapAbs = Math.abs(T.actual - T.plan) || 1;
  const tone = r => { const worse = cost ? dir * r.total > 0 : dir * r.total < 0; return worse ? 'is-bad' : 'is-good'; };
  const brk = lo > 0 ? '<span class="ux-wf-break" aria-hidden="true"></span>' : '';
  const names = OPS[op].sites.map(k => SK[k].name);
  const decFor = st => { const f = (HC.findings || []).find(f => names.includes(String(f.site).replace(/^Room [A-C] · /, '')) && (st.hkeys || []).includes(f.factor)); return f ? f.decision : null; };
  const nw = t => `<span class="ux-nw">${t}</span>`;
  const total = (lab, v, c) => `<li class="ux-wf-row is-end"><span class="ux-wf-lab">${lab}</span><span class="ux-wf-val">${usdW(v)}</span><span class="ux-wf-track">${brk}${bar(lo, v, c)}</span></li>`;
  const list = steps.map((st, i) => { const lab = `${st.lens === 'other' ? '' : `<span class="ux-wf-h">${st.lens === 'grow' ? 'Grow' : 'Optimize'}</span>`}${GAP_SHORT[st.word] || st.word}`, val = usdW(shown(st), true), b = bar(st.a, st.b, tone(st) + (st.residual ? ' is-resid' : '')) + `<span class="ux-wf-conn" style="left:${X(st.b).toFixed(2)}%" aria-hidden="true"></span>`, dk = decFor(st), dec = dk && decById(dk);
    const share = Math.round(Math.abs(st.total) / gapAbs * 100), tip = `${GAP_SHORT[st.word] || st.word}: ${nw(val)}, ${nw(`${share}%`)} of the ${cost ? 'difference' : 'gap'}${dec ? `. Open: ${dec.q}` : '. No decision is open on it'}`;
    return dec ? `<li class="ux-wf-row is-step is-link"><a class="ux-wf-a" href="#/decision/${dk}" aria-describedby="uxwt-${op}-${i}"><span class="ux-wf-lab">${lab}</span><span class="ux-wf-val">${val}</span><span class="ux-wf-track">${b}</span></a><span class="ux-tip" role="tooltip" id="uxwt-${op}-${i}">${tip} ›</span></li>`
      : `<li class="ux-wf-row is-step" tabindex="0" aria-describedby="uxwt-${op}-${i}"><span class="ux-wf-lab">${lab}</span><span class="ux-wf-val">${val}</span><span class="ux-wf-track">${b}</span><span class="ux-tip" role="tooltip" id="uxwt-${op}-${i}">${tip}</span></li>`; }).join('');
  const big = Object.entries({ grow: G.grow, optimize: G.optimize }).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0];
  const title = cost ? `Cost and efficiency explain ${usdW(Math.abs(G.optimize))} of the ${usdW(gapAbs)} over target`
    : `${big[0] === 'optimize' ? 'Cost and efficiency explain' : 'Revenue explains'} ${usdW(Math.abs(big[1]))} of the ${usdW(gapAbs)} gap`;
  return `<section class="panel ux-chart ux-hero" aria-labelledby="uxb-h"><div class="panel-head"><div><h2 id="uxb-h">Where the gap comes from</h2><p>${title}. Open a step to see its decision.</p></div></div><ol class="ux-wf" aria-label="${head} from target to October, step by step">${total(`${head} target`, T.plan, 'is-total')}${list}${total(`${head}, October`, T.actual, 'is-total is-actual')}</ol>${lo > 0 ? `<p class="ux-axis-note"><span class="ux-wf-break is-key" aria-hidden="true"></span> The axis starts at ${usdW(lo)}, not zero, so the steps can be read; the totals are drawn from the same start.</p>` : ''}${uxTableView('Show as table, by Site', gapSplit(op))}</section>`;
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

/* ---------- the value chain as bars on one baseline (guide §5): a stage with no source is an outlined empty bar ---------- */

/* ---------- the four headings as tiles, each opening its full card in a drawer (guide §9, proposal U5) ---------- */
function uxCats(op) {
  const C = CARDS[op](), ks = Object.keys(LENS);
  const about = 'The four headings sit over one structure: each factor under one heading, so no figure is counted twice and the headings are never added together. Grow and Optimize effects explain the contribution gap; cash collected sits under Optimize, outside that gap; Protect shows measures against target with values at stake listed beside, never money; Assure shows the evidence, with the bridge, and adds no money.';
  return `<section class="ux-cats-wrap" aria-labelledby="uxc-h"><div class="ux-row-head"><h2 id="uxc-h">By outcome</h2><p class="ux-prov-extra" hidden data-prov="${escapeHtml(about)}"></p></div><div class="ux-cats ocards">${ks.map(k => uxCatTile(op, k, C)).join('')}</div>${ks.map(k => uxDrawer(`uxd-${op}-${k}`, LENS[k][0], categoryCard(op, k, C), true)).join('')}</section>`;
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
    [`Target ${usdW(T.plan)} · ${Math.round(T.actual / T.plan * 100)}% of target`, uxTrendNA(), `${fig(`port:${op}:cov`, pct(Pp.coverage.cost_recorded_share, 1))} of cost backed by records`], uxBullet(T.actual, T.plan, `${cost ? 'Cost' : 'Contribution'} ${usdW(T.actual)} against a target of ${usdW(T.plan)}`, cost));
  const k2 = uxKpi('Gap to target', fig(`port:${op}:variance`, usdW(T.variance, true)),
    cost ? [`Optimize ${usdW(G.optimize, true)}`, uxTrendNA(), resid ? `${usdW(G.residual, true)} not attributed yet: a target stated only as a bill total` : 'All of it explained']
      : [`Grow ${usdW(G.grow, true)} · Optimize ${usdW(G.optimize, true)}`, uxTrendNA(), resid ? `${usdW(G.residual, true)} not explained yet` : 'All of it explained']);
  const k3 = uxKpi(`Plan spend · ${periodWords()}`, `${fig(`port:${op}:spend`, usdW(P.spend))} <small>of ${usdW(budget)}</small> ${uxMark('QUOTE')}`,
    [`${num(P.visits)} of ${num(derivedPlan(op).crew_visits_limit)} ${o.crewWord}`, `${STATE_WORD[PSTATE().state]}: awaiting the operator executive’s approval`], uxMeterBar(P.spend, budget, `${usdW(P.spend)} of ${usdW(budget)} budget`));
  const k4 = uxKpi('Options’ value, 12 months', `<span>${fig(`port:${op}:m12`, val === 0 ? '$0' : usdW(val, true))}${op === 'harvest' ? '' : dvTag()}</span> ${uxMark('MODELLED')}`,
    [op === 'harvest' ? 'Includes an assumed recovery share (80%) at Kirinyaga' : 'Valued options only; not realised until records show it']);
  const n = uxDecCount(ATTN[op]);
  return `<div class="ux-overview"><p class="headline ux-headline">${hl}</p>
 <div class="heroes ux-kpis">${k1}${k2}${k3}${k4}</div>
 <div class="ux-main-aside"><section class="panel ux-queue-panel" aria-labelledby="uxq-h"><div class="panel-head"><div><h2 id="uxq-h">Needs a decision <span class="ux-count">${num(n)}</span></h2><p>One row per decision, with who decides. AssetOps values the options; your team chooses.</p></div>${link('portfolio/act-first', 'Act first ›', 'ux-link')}</div>${uxQueue(op, ATTN[op].filter(r => uxMergeRows(ATTN[op]).slice(0, 6).some(m => m.d === r[4])))}${n > 6 ? `<p class="ux-more">${link('portfolio/act-first', `View all ${num(n)} in Act first`)}</p>` : n > 3 ? `<p class="ux-more ux-more-phone">${link('portfolio/act-first', `View all ${num(n)} in Act first`)}</p>` : ''}</section>
 </div>
 ${uxBridge(op)}
 <div class="ux-two">${uxChain(op)}<div class="ux-aside ux-aside-stack">${uxPlanCard(op)}${uxInsight(op)}</div></div>
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
 ${D.item ? `<div class="ux-dgo ux-chosen"><span class="status-pill is-approved">Chosen</span><span>${optLabel(D.item)}, by ${who(op, D.p)}${itemOf(op, D.item) ? ` · ${(ITEM_STATE_WORD[itemOf(op, D.item).item_state] || '').toLowerCase()} in the plan` : ''}</span><a class="ux-link" href="#wd-h-${id}">See its Actions</a><a class="ux-link" href="#uxopts-${id}">Compare all options</a></div>`
  : `<div class="ux-dgo">${rec ? uxOpener(`uxc-${id}`, 'Choose this option', 'button primary') : ''}<a class="ux-link" href="#uxopts-${id}">Compare all options</a></div>${rec ? uxDrawer(`uxc-${id}`, `Choose: ${optLabel(rec)}`, choose) : ''}`}</section>`;
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
  return `<div class="heroes ux-kpis">${uxKpi(cost ? 'Cost per required departure met' : 'Contribution', fig(`node:${sk}:root`, cost ? fmtU(t.actual, t.unit) : usdW(t.actual)), [`Target ${cost ? fmtU(t.plan, t.unit) : usdW(t.plan)}`, uxTrendNA()], cost ? '' : uxBullet(t.actual, t.plan, `Contribution ${usdW(t.actual)} against a target of ${usdW(t.plan)}`))}
 ${uxKpi('Gap to target', usdW(s.period.variance, true), [cost ? 'on cost' : 'October', uxTrendNA()])}
 ${(() => { const v = decs.map(d => [d, uxRec(d)]).filter(([, r]) => r && /^[+−-]?\$/.test(String(optEffect(OPT[r])[0])));
   return uxKpi('Open decisions: value if chosen', v.length ? `${wholeText(optEffect(OPT[v[0][1]])[0])} ${uxMark(optClass(OPT[v[0][1]]))}` : '<span class="ux-kpi-na">Not valued</span>', v.length ? [`${optLabel(v[0][1])}, 12 months against no action`, v.length > 1 ? `+ ${num(v.length - 1)} more valued decision${v.length > 2 ? 's' : ''}` : `${num(decs.length)} decision${decs.length === 1 ? '' : 's'} open`] : [`${num(decs.length)} decision${decs.length === 1 ? '' : 's'} open`]); })()}
 ${(() => { const st = decs.flatMap(uxRights).find(r => r.stake), amt = st && (String(st.stake).match(/\$[\d,]+/) || [])[0];
   return uxKpi('At stake, not money', amt ? `${amt} <small>${/cover/i.test(st.stake) ? 'of cover' : 'at stake'}</small>` : '<span class="ux-kpi-na">None open</span>', [st ? `${st.asset} ${String(st.type).toLowerCase()}: protected, never added to money` : 'No warranty or contract at stake at this site']); })()}</div>`;
}

/* ---------- Decision options: the limits in one word per kind; the detail opens in the option's drawer (review finding 2) ---------- */
function uxOblSummary(html) {
  const n = k => (String(html).match(new RegExp(`obl-${k}\\b`, 'g')) || []).length, out = [];
  if (n('fail')) out.push('<span class="ux-lim is-bad">Fails</span>');
  if (n('pass')) out.push('<span class="ux-lim is-good">Passes</span>');
  if (n('cost')) out.push('<span class="ux-lim">Costed</span>');
  if (n('unknown')) out.push('<span class="ux-lim is-na">Cannot be checked yet</span>');
  return out.join(' ') || '<span class="muted">None</span>';
}

/* ---------- The plan: an L1 band with the approval actions, and one line per item (review finding 6) ---------- */
function uxPlanBand(op, P, budget) {
  const o = OPS[op], S = PSTATE(), val = op === 'lakeside' ? P.value : op === 'harvest' ? harvestValue() : derivedPlan('metro').value, ms = crewByMonth(op, P);
  return `<section class="ux-planband" aria-label="The plan at a glance"><div class="heroes ux-kpis">
 ${uxKpi('Plan spend', `${usdW(P.spend)} <small>of ${usdW(budget)}</small> ${uxMark('QUOTE')}`, [], uxMeterBar(P.spend, budget, `${usdW(P.spend)} of ${usdW(budget)} budget`))}
 ${uxKpi(cap(o.crewWord), ms.length ? `${num(ms[0].used)} <small>of ${num(ms[0].limit)} in ${ms[0].month}</small>` : '—', ms.slice(1).map(m => `${num(m.used)} of ${num(m.limit)} in ${m.month}`))}
 ${uxKpi('Options’ value, 12 months', `${val ? usdW(val, true) : '$0'} ${uxMark('MODELLED')}`, ['Not realised until records show it'])}
 </div><div class="ux-planact"><span class="status-pill is-${S.state === 'PROPOSED' ? 'proposed' : S.state === 'APPROVED' ? 'approved' : 'waiting'}">${STATE_WORD[S.state]} · v${num(S.version)}</span><button type="button" class="button primary" aria-describedby="ux-nowire">Approve version ${num(S.version)}</button><button type="button" class="button" aria-describedby="ux-nowire">Send back with a trade-off</button><span id="ux-nowire" class="ux-note">Approving is not wired in this mock-up. It is recorded under the executive’s name and the time.</span></div></section>`;
}
const uxItemHead = () => '<div class="ux-itemh" aria-hidden="true"><span>Item</span><span>Owner</span><span>Due</span><span>One-off</span><span>12-month result</span><span>State</span></div>';
function uxItemRow(op, id, f) {
  const it = itemOf(op, id), acts = actionsOf(op, id), due = acts.map(a => a.due).filter(Boolean).sort()[0] || it?.service_date || null;
  const st = it ? ITEM_STATE_WORD[it.item_state] || '' : '';
  return `<details class="ux-item" data-row="${id}"><summary class="ux-itemrow"><span class="ux-it-main"><small>${f.site}${f.why ? ` · ${f.why}` : ''}</small><b>${f.label}</b></span><span class="ux-it-c" data-k="Owner">${it ? who(op, it.owner) : '<span class="muted">Not available yet</span>'}</span><span class="ux-it-c" data-k="Due">${due ? fdate(due) : '<span class="muted">No date</span>'}</span><span class="ux-it-c ux-num" data-k="One-off">${wholeText(f.cost)}</span><span class="ux-it-c ux-num" data-k="12-month result">${/of cover/.test(f.result) ? wholeText(f.result).replace(/^Protects /, '') : `${wholeText(f.result)} ${f.cls && !/^Not /.test(f.result) ? uxMark(f.cls) : ''}`}</span><span class="ux-it-c" data-k="State">${st ? `<span class="ux-state">${st}</span>` : ''}</span><span class="ux-disc-cue" aria-hidden="true"></span></summary><div class="ux-item-body">`;
}

/* ===== wave 2, Portfolio polish: queue controls, the row's "Why", the provenance popover, the command search, the scope
   switcher and the period menu (guide §7.1, §8). Presentation only; every list is built from the data the screen shows. ===== */
const uxTrendNA = () => '<span class="ux-trend"><span class="ux-spark-na" aria-hidden="true"></span>Trend not available yet</span>';

/* queue: expand a row's explanation */
document.addEventListener('click', e => {
  const b = e.target.closest('.ux-q-more'); if (!b) return;
  const t = document.getElementById(b.getAttribute('aria-controls')), open = b.getAttribute('aria-expanded') !== 'true';
  b.setAttribute('aria-expanded', String(open)); t?.classList.toggle('is-collapsed', !open);
});
/* queue: filter, sort and group, in the page (a real product keeps the choice in the URL and filters on the server past 50 Sites) */
['change', 'input'].forEach(ev => document.addEventListener(ev, e => { const w = e.target.closest('.ux-qtools'); if (w) uxApplyQueue(w.closest('.ux-queue-wrap')); }));

/* provenance popover and other popovers: Esc closes and returns focus */
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  const d = document.querySelector('details.ux-pop[open]'); if (d) { d.open = false; d.querySelector('summary')?.focus(); }
});
document.addEventListener('click', e => { document.querySelectorAll('details.ux-pop[open]').forEach(d => { if (!d.contains(e.target)) d.open = false; }); });

/* command search (guide §8): Ctrl+K, ⌘K or "/" anywhere, or the top bar's search button */
function uxCommands() {
  const op = LS.op, o = OPS[op], out = [];
  PTABS.forEach(([l, id]) => out.push([l, 'Portfolio', id]));
  out.push(['The plan', 'Portfolio', 'portfolio/act-first/plan']);
  o.sites.forEach(sk => out.push([SK[sk].name, 'Site', `site/${sk}`]));
  DEC.filter(d => SK[d.site].op === op).forEach(d => out.push([d.q, `Decision · ${SK[d.site].name}`, `decision/${d.id}`]));
  [['Financials', 'globalfinancials'], ['Findings', 'findings'], ['Actions', 'actions'], ['Evidence', 'globalevidence']].forEach(([l, id]) => out.push([l, 'Go to', id]));
  return out;
}
function uxPalette(open = true) {
  let d = document.getElementById('ux-cmd');
  if (!d) { document.body.insertAdjacentHTML('beforeend', `<div class="ux-cmd" id="ux-cmd" role="dialog" aria-modal="true" aria-label="Search screens, sites and decisions" data-open="false"><div class="ux-cmd-scrim" data-ux-cmd-close></div><div class="ux-cmd-box"><input type="text" class="ux-cmd-in" role="combobox" aria-expanded="true" aria-controls="ux-cmd-list" aria-autocomplete="list" placeholder="Search screens, sites and decisions" aria-label="Search screens, sites and decisions"><ul class="ux-cmd-list" id="ux-cmd-list" role="listbox"></ul><p class="ux-cmd-hint">↑ ↓ to move · Enter to open · Esc to close</p></div></div>`); d = document.getElementById('ux-cmd'); }
  if (!open) { d.dataset.open = 'false'; UX_LAST?.focus?.(); return; }
  UX_LAST = document.activeElement; d.dataset.open = 'true'; const inp = d.querySelector('.ux-cmd-in'); inp.value = ''; uxPaletteFill(''); setTimeout(() => inp.focus(), 0);
}
function uxPaletteFill(q) {
  const list = document.getElementById('ux-cmd-list'), w = q.toLowerCase().split(/\s+/).filter(Boolean);
  const hits = uxCommands().filter(([l, k]) => w.every(x => (l + ' ' + k).toLowerCase().includes(x))).slice(0, 12);
  list.innerHTML = hits.length ? hits.map(([l, k, id], i) => `<li role="option" id="ux-cmd-${i}" data-go="${id}" aria-selected="${i === 0}"><span>${l}</span><small>${k}</small></li>`).join('') : '<li class="ux-cmd-none" role="option" aria-disabled="true">Nothing matches</li>';
  document.querySelector('.ux-cmd-in').setAttribute('aria-activedescendant', hits.length ? 'ux-cmd-0' : '');
}
function uxPaletteGo(li) { if (!li || !li.dataset.go) return; uxPalette(false); location.hash = '#/' + li.dataset.go; }
document.addEventListener('keydown', e => {
  const d = document.getElementById('ux-cmd'), open = d && d.dataset.open === 'true';
  if (!open && ((e.key === 'k' && (e.ctrlKey || e.metaKey)) || (e.key === '/' && !/input|textarea|select/i.test(document.activeElement?.tagName || '')))) { e.preventDefault(); uxPalette(true); return; }
  if (!open) return;
  if (e.key === 'Escape') { e.preventDefault(); uxPalette(false); return; }
  const opts = [...d.querySelectorAll('[role="option"][data-go]')], cur = opts.findIndex(x => x.getAttribute('aria-selected') === 'true');
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); const n = Math.max(0, Math.min(opts.length - 1, cur + (e.key === 'ArrowDown' ? 1 : -1))); opts.forEach((x, i) => x.setAttribute('aria-selected', String(i === n))); d.querySelector('.ux-cmd-in').setAttribute('aria-activedescendant', opts[n]?.id || ''); opts[n]?.scrollIntoView({ block: 'nearest' }); }
  if (e.key === 'Enter') { e.preventDefault(); uxPaletteGo(opts[cur]); }
  if (e.key === 'Tab') e.preventDefault();
});
document.addEventListener('input', e => { if (e.target.classList.contains('ux-cmd-in')) uxPaletteFill(e.target.value); });
document.addEventListener('click', e => {
  if (e.target.closest('[data-ux-cmd-close]')) { uxPalette(false); return; }
  const li = e.target.closest('#ux-cmd-list [data-go]'); if (li) { uxPaletteGo(li); return; }
  const sb = e.target.closest('.topbar [data-index]'); if (sb && !location.search.includes('index=1')) { e.preventDefault(); e.stopImmediatePropagation(); uxPalette(true); }
}, true);

/* the top bar: a scope switcher (the whole portfolio or one Site) and the period as a menu; injected after render */
function uxChrome(s) {
  const bar = document.querySelector('.topbar'); if (!bar || bar.querySelector('.ux-scope-sw')) return;
  const op = LS.op, cur = s && (s.site || (s.crumbs && null)), name = bar.querySelector('.portfolio-name');
  const here = location.hash.replace(/^#\//, ''), site = (here.match(/^site\/([a-z]+)/) || [])[1];
  name?.insertAdjacentHTML('afterend', `<details class="ux-pop ux-scope-sw"><summary aria-label="Choose the portfolio or a site">${site ? SK[site]?.name || 'All sites' : 'All sites'} <span aria-hidden="true">▾</span></summary><div class="ux-pop-menu" role="menu"><input type="search" class="ux-sw-q" placeholder="Type a Site name" aria-label="Filter Sites" autocomplete="off"><a role="menuitem" href="#/portfolio"${!site ? ' aria-current="page"' : ''}>All sites · ${OPS[op].name}</a>${OPS[op].sites.map(k => `<a role="menuitem" href="#/site/${k}"${site === k ? ' aria-current="page"' : ''}>${SK[k].name}</a>`).join('')}</div></details>`);
  const chip = bar.querySelector('.period-chip');
  if (chip && !chip.closest('.ux-period')) { const w = document.createElement('details'); w.className = 'ux-pop ux-period'; const sm = document.createElement('summary'); sm.setAttribute('aria-label', 'Period: October 2026. Choose a period'); chip.replaceWith(w); sm.appendChild(chip); w.appendChild(sm);
    w.insertAdjacentHTML('beforeend', '<div class="ux-pop-menu" role="menu"><span role="menuitem" aria-current="true">October 2026 <small>current period</small></span><span role="menuitem" aria-disabled="true">September 2026 <small>not available yet</small></span><span role="menuitem" aria-disabled="true">A custom range <small>not available yet</small></span></div>'); }
}

/* ===== brand packs (guide §4.7): a configurable identity over the same tokens and components. Resolution order: the
   review-bar choice (mock tooling), then the tenant's setting (UX_BRAND_BY_TENANT, empty in the demo data), then neutral. ===== */
const UX_BRANDS = { neutral: 'Neutral', 'east-africa': 'East Africa' }; /* add 'west-africa', 'southern-africa' … as packs in brand.css */
const UX_BRAND_BY_TENANT = {};
function uxBrand() { let b = null; try { b = localStorage.getItem('l4-brand'); } catch (e) {} return UX_BRANDS[b] ? b : (UX_BRAND_BY_TENANT[OPS?.[LS?.op]?.t?.tenant] || 'neutral'); }
function uxApplyBrand() { const b = uxBrand(); if (b === 'neutral') document.documentElement.removeAttribute('data-brand'); else document.documentElement.setAttribute('data-brand', b); }
function uxBrandSwitch() {
  const rb = document.querySelector('.reviewbar .right'); if (!rb || rb.querySelector('.ux-brand-sw')) return;
  const b = uxBrand();
  rb.insertAdjacentHTML('afterbegin', `<label class="ux-brand-sw">Brand <select id="ux-brand" aria-label="Brand pack (review tool)">${Object.entries(UX_BRANDS).map(([k, l]) => `<option value="${k}"${k === b ? ' selected' : ''}>${l}</option>`).join('')}</select></label>`);
}
document.addEventListener('change', e => { if (e.target.id !== 'ux-brand') return; try { localStorage.setItem('l4-brand', e.target.value); } catch (x) {} uxApplyBrand(); });

document.addEventListener('input', e => { if (!e.target.classList.contains('ux-sw-q')) return; const q = e.target.value.trim().toLowerCase(); e.target.parentElement.querySelectorAll('a[role="menuitem"]').forEach(a => { a.hidden = !!q && !a.textContent.toLowerCase().includes(q); }); });

/* the top bar's search names what it searches, on every screen */
function uxSearchLabel() { const sb = document.querySelector('.topbar [data-index]'); if (!sb) return; [...sb.childNodes].filter(n => n.nodeType === 3 && n.nodeValue.trim()).forEach(n => { n.nodeValue = 'Search sites, decisions, screens'; }); sb.setAttribute('aria-label', 'Search sites, decisions and screens (Ctrl K)'); }
