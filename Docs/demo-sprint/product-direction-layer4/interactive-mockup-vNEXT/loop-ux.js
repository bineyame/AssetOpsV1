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
function uxKpi(label, value, lines = [], extra = '', cls = '') {
  return `<div class="ux-kpi ${cls}"><div class="ux-kpi-l">${label}</div><div class="ux-kpi-v">${value}</div>${extra}${lines.filter(Boolean).map(l => `<div class="ux-kpi-s${/ux-trend/.test(l) ? ' has-trend' : ''}">${l}</div>`).join('')}</div>`;
}

/* ---------- status chip (guide §4.6): five states, each with a word; colour follows meaning ---------- */
const UX_TONE = { off: 'bad', at: 'warn', due: 'warn', new: 'info', unobs: 'neutral', ok: 'good' };
function uxTone(k, t) { return /breach|below its limit/i.test(t) ? 'bad' : UX_TONE[k] || 'neutral'; }
const UX_GLYPH = { bad: '↘', warn: '▲', info: '✦', neutral: '?', good: '✓' };
const uxTileStatus = (k, op) => { if (k !== 'protect') return ''; const pc = protectCard(op); return `<p class="ux-cat-st">${uxChip(pc.broken ? 'off' : 'ok', pc.broken ? 'Limits broken' : 'All held')}</p>`; };
function uxChip(k, t) { const tone = uxTone(k, t); return `<span class="ux-chip attn-k is-${tone}"><span aria-hidden="true">${UX_GLYPH[tone]}</span>${t}</span>`; }

/* ---------- decision queue (guide §7.1): the data's order (design §2.8: never a value ranking); at stake, due and who decides on each row.
   At stake: the recommended option's result against no action, with its own basis and marker; else the right's value at stake; else the
   option's own words ("No saving claimed"); else "Not available yet". Due: the right's deadline; else the date the issue names. ---------- */
const UX_MON = '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)';
const uxRights = d => (d.rights || []).map(k => { try { return rightsOf(k); } catch (e) { return null; } }).filter(Boolean);
function uxRec(d) { const op = SK[d.site].op, inPlan = planItemsV1(op); return d.opts.find(x => uxDisp(x) === 'RECOMMENDED') || d.opts.find(x => inPlan.includes(x)); }
function uxDue(decId, txt) {
  const d = decById(decId), r = d && uxRights(d).find(r => r.deadline);
  if (r) return fdate(r.deadline);
  const m = String(txt).match(new RegExp(`(?:due|lapses(?: on)?|by|deadline)\\s+(\\d{1,2} ${UX_MON})`));
  return m ? m[1] : '<span class="muted">No deadline</span>';
}

function uxStake(decId) {
  const p = uxStakeParts(decId);
  return p.value ? `<span class="ux-q-v">${p.value}</span><small>${p.note}</small>` : p.word ? `<span class="ux-q-word">${p.word}</span>${p.wnote ? `<small>${p.wnote}</small>` : ''}` : '<span class="muted">Not available yet</span>';
}
/* the at-stake figure in parts (value, note, certainty), so the row stays scannable and the certainty sits in the row's detail */
function uxStakeParts(decId) {
  const d = decById(decId); if (!d) return {};
  const rec = uxRec(d), x = rec ? OPT[rec] : null, ev = x ? String(optEffect(x)[0]) : '';
  /* a figure that is not valued says so, with the opportunity in its own unit (D-RECON.5) */
  if (rec && optBasis(rec) === 'NOT_VALUED' && uxDisp(rec) !== 'REJECTED') { const dd = DOPT(rec) || {}, miss = (dd.protect || {}).departures_missed;
    return { word: `Not valued: ${uxCapital(SK[d.site].op, rec) || 'listed beside the plan'}`, wnote: dd.params?.added_buses ? `${num(dd.params.added_buses)} more buses offered; ${miss ? `${num(miss)} departures missed` : 'all departures met'}` : '', num: 0, rec }; }
  if (/^[+−-]?\$/.test(ev)) { const P = planCase(SK[d.site].op), inP = P.ids.includes(rec);
    return { value: wholeText(ev), num: Number(ev.replace(/[^\d.−-]/g, '').replace('−', '-')) || 0, note: `${[uxQualShort(rec), BASIS_WORDS[optBasis(rec)]].filter(Boolean).join(', ')} · ${inP ? 'in the plan' : 'not in the plan'}`, cls: optClass(x), dv: !!DV_OPT[rec], rec }; }
  const st = uxRights(d).find(r => r.stake), amt = st && (String(st.stake).match(/\$\d(?:[\d,]*\d)?(?:\.\d+)?/) || [])[0];
  if (amt) return { value: wholeText(amt), num: Number(amt.replace(/[^\d.]/g, '')) || 0, note: /cover/i.test(st.stake) ? 'cover kept claimable' : /credit/i.test(st.stake) ? 'possible credit' : 'at stake', cls: 'EXPOSURE', rec };
  if (ev && !/^Not (valued|modelled)/i.test(ev)) return { word: ev, num: 0, rec };
  if (x && /^Not valued/.test(ev)) return { word: `Not valued: ${optEffect(x)[1]}`, num: 0, rec }; /* not valued is a fact, not missing data (r2 M1) */
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
  /* a leak is a loss only against a target (UX audit C2.4; X6): the stage after it is below its target; otherwise it is a step, drawn neutral */
  const adverseAt = i => { const nx = st[i + 1], tm = nx && String(nx[2] || '').match(/target (\$?[\d,.]+)/); return tm ? { a: valOf(nx[1]), t: valOf(tm[1]), bad: valOf(nx[1]) < valOf(tm[1]) } : null; };
  const rows = st.map((x, i) => {
    if (x[0] !== 'leak') { const na = x[3] === 'na' || !/\d/.test(x[1]); prev = na ? null : { v: valOf(x[1]), u: unitOf(x[1]), name: x[0] }; return { stage: x, na }; }
    const parts = String(x[1] || '').split(/\s*·\s*/).filter(Boolean).map(p => { const m = p.match(/^(.*?)(\$[\d,.]+|[\d,.]+\s*(?:kWh|crate-days|L)|\b\d[\d,.]*\b)\s*$/) || p.match(/^(.*?)(\$[\d,.]+|[\d,.]+\s*(?:kWh|crate-days|L))/);
      if (!m || !prev) return { text: p }; const v = valOf(m[2]), pct = prev.v ? v / prev.v * 100 : null; const L = { text: p, label: m[1].replace(/[:\s]+$/, ''), amount: m[2].trim(), pct, of: prev.name.toLowerCase(), adv: adverseAt(i) }; leaks.push(L); return L; });
    return { parts };
  });
  const maxPct = Math.max(1, ...leaks.map(l => l.pct || 0)), byPct = (a, b) => (b.pct || 0) - (a.pct || 0), topBad = leaks.filter(l => l.adv && l.adv.bad).sort(byPct)[0], top = topBad || [...leaks].sort(byPct)[0];
  const html = rows.map(r => r.stage ? `<li class="ux-vc-stage ${r.na ? 'is-na' : ''}"><span class="ux-vc-lab">${r.stage[0]}<small>${quiet(r.stage[2])}</small></span><span class="ux-vc-val">${r.stage[1]}</span></li>`
    : (r.parts || []).map(p => p.pct != null ? `<li class="ux-vc-loss${p.adv && p.adv.bad ? ' is-adverse' : ''}"><span class="ux-vc-lab"><span aria-hidden="true">↳</span> ${p.label || 'Lost'}</span><span class="ux-vc-val">${p.amount}<small>${p.pct < 0.05 ? 'none' : `${p.pct.toFixed(1)}% of ${p.of}`}</small></span><span class="ux-vc-track"><span class="ux-vc-bar${p.adv && p.adv.bad ? ' is-bad' : ''}"${p.adv ? ` data-actual="${p.adv.a}" data-target="${p.adv.t}"` : ''} style="width:${Math.max(p.pct > 0.05 ? 1.5 : 0, p.pct / maxPct * 100).toFixed(1)}%"></span></span></li>` : `<li class="ux-vc-leak"><span aria-hidden="true">↳</span> ${p.text}</li>`).join('')).join('');
  const title = topBad && topBad.pct > 0.05 ? `The biggest leak against target: ${topBad.label || 'lost'} ${topBad.amount}, ${topBad.pct.toFixed(1)}% of ${topBad.of}` : top && top.pct > 0.05 ? `No leak against target; the largest step: ${top.label || 'lost'} ${top.amount}, ${top.pct.toFixed(1)}% of ${top.of}` : `${sk ? SK[sk].name : OPS[op].name}, October: no leak measured`;
  return `<section class="panel ux-chart" aria-labelledby="uxv-h-${sk || op}"><div class="panel-head"><div><h2 id="uxv-h-${sk || op}">Where value leaks</h2><p>${title}</p></div></div><ol class="ux-vc">${html}</ol><p class="ux-axis-note">Loss bars are drawn against the largest loss; each says its share of the stage before it.</p>${uxTableView('Show the stages in detail', chainStrip(op, sk))}</section>`;
}
/* an outcome tile: its position, a target-against-actual visual and its counts (wave 2) */
function uxCatTile(op, k, C) {
  const [name, ico] = LENS[k], finds = ATTN[op].filter(r => findingHeading(r) === k).length, P = planCase(op), o = OPS[op];
  const items = P.ids.filter(id => optHeadings(id).some(h => h[0] === k)).length + (k === 'protect' ? proactiveOf(op).length : 0);
  const pos = k === 'assure' ? (C.assure?.pos || 'The evidence behind every heading') : k === 'protect' ? protectCard(op).pos : (C[k]?.pos || '');
  const counts = [finds ? `${num(finds)} Finding${finds === 1 ? '' : 's'}` : 'No Finding', items ? `${num(items)} plan item${items === 1 ? '' : 's'}` : ''].filter(Boolean).join(' · ');
  let vis = '';
  /* Grow and Optimize do not restate the gap chart's money (owner, 20 Nov; OD-21 keeps the four headings): each gives its share of
     the gap and opens the same drawer as its chart group. Protect and Assure keep their own measures. */
  const g = (k === 'grow' || k === 'optimize') ? uxGapModel(op).groups.find(x => x.k === k) : null;
  if (g) { const M = uxGapModel(op);
    return `<div class="ux-cat" data-tile="${k}"><div class="ux-cat-h">${icon(ico)}<h3>${name}</h3></div><p class="ux-cat-st">${g.sub < 0 ? uxChip('off', 'Off target') : uxChip('ok', 'On target')}</p><p class="ux-cat-pos"><b${figA(k, op, M.G[k])}>${usdW(g.sub, true)}</b> ${g.share != null ? `· <span data-heading-share="${g.share}">${g.share}%</span> of what ${uxWidenWord(M)}${g.offset ? `; ${usdW(g.offset, true)} offsets` : ''}${g.resid ? `; ${usdW(g.resid, true)} not attributed yet` : ''}` : '· an offset to the gap'}</p>${g.share != null ? `<div class="ux-meterbar" role="img" aria-label="${g.share}% of what ${uxWidenWord(M)}"><span style="width:${g.share}%"></span></div>` : ''}<p class="ux-cat-n">${num(g.steps.length)} driver${g.steps.length === 1 ? '' : 's'} · ${counts}</p>${uxOpener(`uxd-${op}-${k}`, `View drivers<span class="vh">: ${name}</span> <span aria-hidden="true">›</span>`, 'ux-cat-go')}</div>`; }
  if (k === 'grow' && o.kind !== 'cost') { const a = sumNodes(op, 'actual', 'revenue'), t = sumNodes(op, 'plan', 'revenue'); vis = uxBullet(a, t, `Revenue ${usdW(a)} against a target of ${usdW(t)}`); }
  if (k === 'optimize') { const a = o.kind === 'cost' ? opTotals(op).actual : sumNodes(op, 'actual', 'cost_to_serve'), t = o.kind === 'cost' ? opTotals(op).plan : sumNodes(op, 'plan', 'cost_to_serve'); vis = uxBullet(a, t, `Cost ${usdW(a)} against a target of ${usdW(t)}`, true); }
  if (k === 'protect') { const pc = protectCard(op); vis = pc.total ? `<div class="ux-seg" role="img" aria-label="${num(pc.broken)} of ${num(pc.total)} limits broken">${Array.from({ length: pc.total }, (_, i) => `<span class="${i < pc.broken ? 'is-bad' : 'is-good'}"></span>`).join('')}</div>` : ''; }
  if (k === 'assure') { const c = o.t.portfolio.coverage.cost_recorded_share; vis = `<div class="ux-meterbar is-neutral" role="img" aria-label="${pct(c, 1)} of October cost backed by records"><span style="width:${(c * 100).toFixed(1)}%"></span></div>`; }
  return `<div class="ux-cat" data-tile="${k}"><div class="ux-cat-h">${icon(ico)}<h3>${name}</h3></div>${uxTileStatus(k, op)}<p class="ux-cat-pos">${wholeText(pos)}</p>${vis}<p class="ux-cat-n">${counts}</p>${uxOpener(`uxd-${op}-${k}`, `View ${k === 'protect' ? 'measures' : k === 'assure' ? 'evidence' : 'drivers'}<span class="vh">: ${name}</span> <span aria-hidden="true">›</span>`, 'ux-cat-go')}</div>`;
}

/* a title never repeats a column: "Kobo generator stop setting" in the Kobo row reads "Generator stop setting" */
const uxTitle = (t, site) => { const r = String(t).replace(new RegExp(`^${site}(?:’s|'s)?\\s+`), ''); return r === t ? t : r.charAt(0).toUpperCase() + r.slice(1); };
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
function uxQueue(op, rows, cls = '', total = 0) { /* total: every open decision in scope, when the list shows only the first rows (review r2 M6) */
  if (UX_STATE === 'loading') return `<div class="ux-skel" role="status"><span class="vh">Loading decisions…</span>${'<span class="ux-skel-row" aria-hidden="true"></span>'.repeat(3)}</div>`;
  if (UX_STATE === 'empty' || !rows.length) return '<p class="ux-empty" role="status">No decisions waiting. New issues appear here when the next day of records is in.</p>';
  const M = uxMergeRows(rows), firstChoose = (M.find(m => uxDecState(m.d).key === 'choose') || {}).d; /* the button follows the state; one primary: the first decision waiting for a choice */
  const items = M.map((m, i) => {
    const { d, s } = m, D = deciderOf(d), dec = decById(d), DS = uxDecState(d), id = `uxq-${++UX_QN}`, P = uxStakeParts(d), due = m.issues.map(([, , txt]) => uxDueIso(d, txt)).filter(Boolean).sort()[0] || '';
    const tones = m.issues.map(([k, t]) => uxTone(k, t)), worst = [...tones].sort((a, b) => UX_RANK[a] - UX_RANK[b])[0];
    const stake = uxStake(d); /* one stake renderer (review r2 M1) */
    const ck = P.cls && (CLS[P.cls] || [])[1], cert = P.value && P.cls ? `<span class="ux-q-cert">How sure: ${ck === 'rec' || ck === 'der' ? 'recorded' : `${uxMark(P.cls)}`}${P.dv ? ` · ${dvTag()} design estimate, not yet tested on your recorded data` : ''}</span>` : '';
    const why = m.issues.map(([k, t, txt]) => `<span class="ux-q-issue-line"><b>${t}:</b> ${txt}</span>`).join('');
    return `<li class="attn-${m.issues[0][0]} ux-q" data-state="${DS.key}" data-order="${i}" data-site="${s}" data-kind="${worst}" data-kinds="${[...new Set(tones)].join(' ')}" data-due="${due}" data-urg="${uxUrgency(due)}" data-stake="${P.num || 0}" data-issues="${m.issues.length}"><div class="ux-q-issue"><div class="ux-q-top">${m.issues.map(([k, t]) => uxChip(k, t)).join('')}</div><b class="ux-q-title">${uxTitle(dec ? dec.q : m.issues[0][1], SK[s].name)}</b><button type="button" class="ux-q-more" aria-expanded="false" aria-controls="${id}">Why${m.issues.length > 1 ? ` (${num(m.issues.length)} issues)` : ''}<span class="vh">: ${escapeHtml(dec ? dec.q : '')}</span></button><div class="ux-q-why is-collapsed" id="${id}">${why}${cert ? `<span class="ux-q-issue-line">${cert}</span>` : ''}</div></div><div class="ux-q-site"><span class="ux-q-k">Site: </span>${SK[s].name}</div><div class="ux-q-stake"><span class="ux-q-k">At stake: </span>${stake}</div><div class="ux-q-due${due ? '' : ' is-empty'}"><span class="ux-q-k">Due: </span>${due ? fdate(due) : '<span class="vh">No deadline</span>'}</div><div class="ux-q-who"><span class="ux-q-k">Decides: </span>${who(op, D.p)}</div>${link(`decision/${d}`, `${DS.btn}<span class="vh">: ${escapeHtml(dec ? dec.q : '')}, ${SK[s].name}</span>`, `button ux-q-go${DS.key === 'choose' && d === firstChoose ? ' primary' : ''}`)}</li>`;
  });
  const sites = [...new Set(M.map(m => m.s))], kinds = [...new Set(M.flatMap(m => m.issues.map(([k, t]) => uxTone(k, t))))];
  const KW = { bad: 'Off target or breached', warn: 'At a limit or deadline', info: 'New or opportunity', neutral: 'Not explained yet', good: 'On target' };
  const dl = `uxsl-${UX_QN}`;
  const tools = M.length > 2 ? `<div class="ux-qtools" role="group" aria-label="Filter, sort and group the decisions">
   ${sites.length > 1 ? `<label>Site <input type="search" data-qf="site" list="${dl}" placeholder="All sites" autocomplete="off" aria-label="Filter by Site: type a Site name"><datalist id="${dl}">${sites.map(s => `<option value="${SK[s].name}"></option>`).join('')}</datalist></label>` : ''}
   ${kinds.length > 1 ? `<label>Status <select data-qf="kind"><option value="">All</option>${kinds.map(k => `<option value="${k}">${KW[k]}</option>`).join('')}</select></label>` : ''}
   <label>Sort <select data-qs><option value="order">Priority</option><option value="due">Due date</option><option value="stake">At stake</option></select></label>
   <label>Group <select data-qg><option value="">None</option><option value="urg">By urgency</option>${sites.length > 1 ? '<option value="site">By site</option>' : ''}</select></label>
   <label class="ux-dense"><input type="checkbox" data-qd> Compact</label>
   <span class="ux-qcount" role="status" aria-live="polite" data-total="${total || M.length}">${num(M.length)} of ${num(total || M.length)}</span></div>` : '';
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
  const shown = li.filter(x => !x.hidden).length; const qc = wrap.querySelector('.ux-qcount'); qc.textContent = `${num(shown)} of ${num(+qc.dataset.total || li.length)}`;
  ul.classList.toggle('is-filtered', !!(q || fKind || group || sort !== 'order'));
}

/* the bridge as a stepped waterfall, the page's hero chart (guide §5, review 2b): target, each factor's step from the running
   total, October. The axis starts at a round value below the lowest point and the break is drawn and said; each step links
   to the decision on its driver, with its detail on hover and keyboard focus. */

/* rounding that reconciles (guide §5.1, wave 2c ruling): round the parts so they sum to the rounded total (largest remainder) */
function uxRoundTo(values, total) {
  const fl = values.map(v => Math.floor(v)), short = Math.round(total) - fl.reduce((a, b) => a + b, 0);
  const order = values.map((v, i) => [v - Math.floor(v), i]).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  const out = [...fl]; for (let k = 0; k < Math.abs(short) && k < order.length; k++) out[order[k][1]] += Math.sign(short);
  return out;
}
/* the gap, modelled once (wave 2c rulings): heading groups in order, each step's displayed value (one sign rule: the effect on the
   headline result), shares of what widens the gap, positions on the gap scale, and the Findings and decisions on each driver.
   The chart, the heading tiles and every driver or heading drawer read this one model, so they cannot disagree. */
function uxGapModel(op) {
  const o = OPS[op], T = opTotals(op), G = gapByHeading(op), cost = o.kind === 'cost';
  const sum = G.rows.reduce((a, r) => a + r.total, 0), dir = Math.abs(T.actual - T.plan - sum) < Math.abs(T.actual - T.plan + sum) ? 1 : -1;
  const disp = st => cost ? -dir * st.total : st.total, gapShown = T.variance;
  const names = o.sites.map(k => SK[k].name), siteOf = f => String(f.site).replace(/^Room [A-C] · /, '');
  const groups = ['grow', 'optimize'].map(k => ({ k, rows: G.rows.filter(r => r.lens === k).sort((a, b) => Math.abs(b.total) - Math.abs(a.total)) })).filter(g => g.rows.length);
  const all = groups.flatMap(g => g.rows);
  let run = 0, lo = 0, hi = 100; const pos = new Map();
  all.forEach(st => { const a = run, b = run + disp(st) / (gapShown || 1) * 100; run = b; pos.set(st, [a, b]); lo = Math.min(lo, a, b); hi = Math.max(hi, a, b); });
  const gapR = Math.round(gapShown), subs = uxRoundTo(groups.map(g => g.rows.reduce((a, r) => a + disp(r), 0)), gapR);
  const widens = v => Math.sign(v) === Math.sign(gapShown);
  const wl = all.filter(st => widens(disp(st))), wTot = wl.reduce((a, r) => a + Math.abs(disp(r)), 0) || 1;
  const sharesR = uxRoundTo(wl.map(r => Math.abs(disp(r)) / wTot * 100), 100), share = new Map(wl.map((r, i) => [r, sharesR[i]]));
  /* one share basis for steps and headings (review H2): a heading's share is the sum of its widening steps' shares; its offsets are said */
  groups.forEach((g, gi) => { g.sub = subs[gi]; const ws = g.rows.filter(r => share.has(r)); g.share = ws.length ? ws.reduce((a, r) => a + share.get(r), 0) : null;
    g.offset = r2(g.rows.filter(r => !share.has(r) && !r.residual).reduce((a, r) => a + disp(r), 0)); g.resid = r2(g.rows.filter(r => !share.has(r) && r.residual).reduce((a, r) => a + disp(r), 0));
    const vals = uxRoundTo(g.rows.map(r => disp(r)), subs[gi]);
    g.steps = g.rows.map((st, i) => {
      /* what is being done on a driver (review H1): a decision whose Finding sits on the driver, or one of whose options moves it
         (option_money_factors); a service-failure cost line is the money side of its Site's Protect measures, so their Findings link */
      const stSites = Object.keys(st.by), stNames = stSites.map(k => SK[k].name), hk = st.hkeys || [], omf = HC.option_money_factors || {};
      const svc = hk.some(h => (o.t.portfolio.service_cost_lines || []).some(l => l.node === h));
      const moved = DEC.filter(d => stSites.includes(d.site) && d.opts.some(x => (omf[x] || []).some(f => hk.includes(f)))).map(d => d.id);
      const finds = (HC.findings || []).filter(f => names.includes(siteOf(f)) && (hk.includes(f.factor) || (stNames.includes(siteOf(f)) && (moved.includes(f.decision) && f.heading === 'protect' || svc && f.heading === 'protect'))));
      const decs = [...new Set([...finds.map(f => f.decision), ...moved].filter(d => d && decById(d)))];
      const nodes = Object.keys(st.by).flatMap(sk => effectsOf(sk).filter(n => n.lens === st.lens && (n.residual ? n.label : (GAP_WORD[n.hkey] || n.label)) === st.word).map(n => ({ sk, n, v: cost ? -dir * n.eff : n.eff })));
      const nr = uxRoundTo(nodes.map(x => x.v), vals[i]); nodes.forEach((x, j) => { x.vr = nr[j]; }); /* evidence rounds to the step's shown value (review M2) */
      return { st, i, id: `uxdrv-${op}-${g.k}-${i}`, lab: GAP_SHORT[st.word] || st.word, v: vals[i], share: share.has(st) ? share.get(st) : null, pos: pos.get(st), finds, decs, nodes };
    }); });
  return { op, o, T, G, cost, groups, lo, hi, gapR, gapAbs: Math.abs(T.actual - T.plan) || 1 };
}
const uxWidenWord = M => M.cost ? 'raises the cost' : 'widens the gap';
/* one drawer shape for a driver (guide §8 drill-down): the amount and its share, what is behind it, what is being done, the evidence */
function uxDecLine(dk) { const d = decById(dk), st = uxDecState(dk); return `<li><span>${d.q}</span> <span class="status-pill is-${st.key === 'released' ? 'approved' : st.key === 'approval' ? 'waiting' : 'proposed'}">${st.label}</span> ${link(`decision/${dk}`, 'Open decision →')}</li>`; }
function uxDriverBody(M, s) {
  const issue = f => { const r = ATTN[M.op].find(r => r[5] === f.id); return r ? r[3] : 'No issue text recorded'; };
  const dirOf = v => Math.sign(v) === Math.sign(M.T.variance) ? 'widens' : 'offsets';
  return `<p class="ux-drv-amt"><b>${usdW(s.v, true)}</b> ${s.share != null ? `${s.share}% of what ${uxWidenWord(M)}` : s.st.residual ? 'not attributed yet' : `offsets ${usdW(Math.abs(s.v))} of it`}, October against target</p>
   <h3 class="ux-drv-h">What is behind it</h3>${s.finds.length ? `<ul class="list">${s.finds.map(f => `<li><b>${f.site}</b>: ${issue(f)}</li>`).join('')}</ul>` : '<p class="muted">No Finding names this driver yet.</p>'}
   <h3 class="ux-drv-h">What is being done</h3>${s.decs.length ? `<ul class="list ux-drv-decs">${s.decs.map(uxDecLine).join('')}</ul>` : '<p>No decision yet.</p>'}
   <h3 class="ux-drv-h">Evidence</h3>${s.nodes.length ? `<ul class="list ux-drv-ev">${s.nodes.map(({ sk, n, vr }) => `<li data-site="${sk}" data-effect="${r2(n.eff)}">${SK[sk].name}: ${fig(n.evd || `node:${sk}:${n.id}`, usdW(vr, true))}${s.nodes.length > 1 && vr ? `, ${dirOf(vr)}` : ''} ${ec(n.cls)}</li>`).join('')}${s.nodes.length > 1 ? `<li class="ux-drv-sum"><b>Total ${usdW(s.v, true)}</b></li>` : ''}</ul>` : '<p class="muted">Not available yet.</p>'}`;
}
/* the heading drawer's head (Grow, Optimize): the same shape, one level up; the heading's full card follows it */
function uxHeadingTop(M, k) {
  const g = M.groups.find(x => x.k === k); if (!g) return '';
  return `<section class="ux-drv-top" aria-label="${LENS[k][0]}: its share of the gap"><p class="ux-drv-amt"><b${figA(k, M.op, M.G[k])}>${usdW(g.sub, true)}</b> ${g.share != null ? `<span data-heading-share="${g.share}">${g.share}%</span> of what ${uxWidenWord(M)}${g.offset ? `; ${usdW(g.offset, true)} offsets` : ''}${g.resid ? `; ${usdW(g.resid, true)} not attributed yet` : ''}` : `offsets ${usdW(Math.abs(g.sub))} of it`}, October against target</p>
   ${reconTie(M.op, k)}<h3 class="ux-drv-h">Its drivers, and what is being done</h3><ul class="list ux-drv-decs">${g.steps.map(s => `<li><span>${s.lab}: <b>${usdW(s.v, true)}</b></span> ${s.decs.length ? s.decs.map(dk => link(`decision/${dk}`, 'Open decision →')).join(' ') : '<span class="muted">No decision yet</span>'}</li>`).join('')}</ul></section>`;
}
/* the bridge (guide §5, wave 2c): the totals on an honest zero axis in one bullet; below it, the gap itself as the scale, each
   driver a step across it under its heading. One drill-down grammar (guide §8): a step opens its driver drawer and a heading opens
   its heading drawer, in place; leaving the page is the drawer's explicit "Open decision →". */
function uxBridge(op) {
  const M = uxGapModel(op), { T, cost, lo, hi, gapR, gapAbs, G } = M, head = cost ? 'Cost' : 'Contribution';
  const S = p => (p - lo) / (hi - lo) * 100, nw = t => `<span class="ux-nw">${t}</span>`;
  const tone = s => { const worse = s.v < 0; return worse ? 'is-bad' : 'is-good'; };
  const body = M.groups.map(g => {
    const rows = g.steps.map(s => {
      const [a, b] = s.pos, L = S(Math.min(a, b)), W = Math.abs(S(b) - S(a)), val = usdW(s.v, true), sh = s.share != null ? `${s.share}%` : s.st.residual ? 'not attributed yet' : 'offsets', tid = `${s.id}-tip`;
      const bar = `<span class="ux-wf-bar ${tone(s)}${s.st.residual ? ' is-resid' : ''}" style="left:${L.toFixed(2)}%;width:${Math.max(0.8, Math.min(W, 100 - L)).toFixed(2)}%"></span>`;
      const tip = `${s.lab}: ${nw(val)}, ${s.share != null ? `${nw(sh)} of what ${uxWidenWord(M)}` : s.st.residual ? 'not attributed yet' : `offsets ${nw(usdW(Math.abs(s.v)))} of it`}. ${s.decs.length ? `${s.decs.length === 1 ? 'A decision is' : `${num(s.decs.length)} decisions are`} open on it` : 'No decision is open on it'}`;
      const inner = `<span class="ux-wf-lab">${s.lab}</span><span class="ux-wf-val" data-v="${s.v}" data-share="${s.share ?? ''}">${val}<small>${sh}</small></span><span class="ux-wf-track">${bar}</span>`;
      return `<li class="ux-wf-row is-step is-link"><button type="button" class="ux-wf-a" data-ux-drawer="${s.id}" aria-haspopup="dialog" aria-controls="${s.id}" aria-describedby="${tid}">${inner}</button><span class="ux-tip" role="tooltip" id="${tid}">${tip}</span></li>`;
    }).join('');
    return `<li class="ux-wf-group" data-v="${g.sub}">${uxOpener(`uxd-${op}-${g.k}`, `<span class="ux-wf-gl">${LENS[g.k][0]}</span><span class="ux-wf-gv"${figA(g.k, op, M.G[g.k])}>${usdW(g.sub, true)}</span>`, 'ux-wf-gbtn')}</li>${rows}`;
  }).join('');
  const drawers = M.groups.flatMap(g => g.steps.map(s => uxDrawer(s.id, s.lab, uxDriverBody(M, s)))).join('');
  const big = Object.entries({ grow: G.grow, optimize: G.optimize }).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0];
  const title = cost ? `Cost and efficiency explain ${usdW(Math.abs(G.optimize))} of the ${usdW(gapAbs)} over target`
    : `${big[0] === 'optimize' ? 'Cost and efficiency explain' : 'Grow revenue explains'} ${usdW(Math.abs(big[1]))} of the ${usdW(gapAbs)} gap`;
  const totals = `<div class="ux-wf-totals">${uxBullet(T.actual, T.plan, `${head} ${usdW(T.actual)} against a target of ${usdW(T.plan)}`, cost)}<div class="ux-wf-tl"><span>${head}, October <b>${usdW(T.actual)}</b></span><span>Target <b>${usdW(T.plan)}</b></span></div></div>`;
  return `<section class="panel ux-chart ux-hero" aria-labelledby="uxb-h"><div class="panel-head"><div><h2 id="uxb-h">Where the gap comes from</h2><p>${title}. Open a step or a heading for what is behind it and the decision on it.</p></div></div>${totals}
 <div class="ux-wf-scale" aria-hidden="true"><span class="ux-wf-mark" style="left:${S(0).toFixed(2)}%">Target ${usdW(T.plan)}</span><span class="ux-wf-mark is-end" style="left:${S(100).toFixed(2)}%">October ${usdW(T.actual)}</span></div><p class="ux-wf-cap">The ${usdW(gapAbs)} ${cost ? 'difference' : 'gap'}, driver by driver. Shares are of what ${uxWidenWord(M)}; a step that works the other way is an offset.</p>
 <ol class="ux-wf ux-wf-gapscale" data-gap="${gapR}" aria-label="${head}: the gap from target to October, driver by driver">${body}</ol>${uxTableView('Show as table, by Site', gapSplit(op))}${drawers}</section>`;
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
  return `<section class="ux-cats-wrap" aria-labelledby="uxc-h"><div class="ux-row-head"><h2 id="uxc-h">By outcome</h2><span class="ux-note">Each heading opens its drivers, Findings and plan items</span><p class="ux-prov-extra" hidden data-prov="${escapeHtml(about)}"></p></div><div class="ux-cats ocards">${ks.map(k => uxCatTile(op, k, C)).join('')}</div>${ks.map(k => uxDrawer(`uxd-${op}-${k}`, LENS[k][0], `${uxHeadingTop(uxGapModel(op), k)}${categoryCard(op, k, C, { fromGap: ['grow', 'optimize'].includes(k) })}`, true)).join('')}</section>`;
}

/* ---------- the plan card and the insight (L2 aside) ---------- */
function uxInsight(op) {
  return CONTRAST[op].map(([h, p, d, l]) => `<section class="panel ux-insight" aria-labelledby="uxi-h"><div class="ux-eyebrow">Sites that look alike need different levers</div><h2 id="uxi-h">${h}</h2><p>${p}</p>${link(`decision/${d}`, `Open ${l} →`)}</section>`).join('');
}

/* ---------- Portfolio Overview (guide §9) ---------- */
function uxOverview(op) {
  const o = OPS[op], T = opTotals(op), G = gapByHeading(op), cost = o.kind === 'cost', P = planCase(op), Pp = o.t.portfolio, M2 = o.t.portfolio_constraints;
  const budget = op === 'lakeside' ? LS.budget : M2.budget_usd_nov_dec, val = op === 'lakeside' ? P.value : op === 'harvest' ? harvestValue() : derivedPlan('metro').value;
  const gap = T.actual - T.plan, big = Object.entries({ grow: G.grow, optimize: G.optimize }).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0];
  const hl = cost ? `Charging and depot cost is ${usdW(Math.abs(gap))} ${gap > 0 ? 'over' : 'under'} target in October; all ${num(Pp.departures_met)} required departures were met, at ${usd2(Pp.cost_per_departure_actual)} each.`
    : `Contribution is ${usdW(Math.abs(gap))} ${gap < 0 ? 'below' : 'above'} target in October; ${big[0] === 'optimize' ? 'cost and efficiency explain' : 'Grow revenue explains'} ${usdW(Math.abs(big[1]))} of it.`;
  const resid = Math.abs(G.residual) > 0.005;
  const k1 = uxKpi(cost ? 'Charging and depot cost' : 'Contribution', fig(`port:${op}:actual`, usdW(T.actual)),
    [`Target ${usdW(T.plan)} · ${Math.round(T.actual / T.plan * 100)}% of target`, cost ? uxTrendCost(op) : uxTrendNA(op, 'contribution'), `${fig(`port:${op}:cov`, pct(Pp.coverage.cost_recorded_share, 1))} of cost backed by records`], uxBullet(T.actual, T.plan, `${cost ? 'Cost' : 'Contribution'} ${usdW(T.actual)} against a target of ${usdW(T.plan)}`, cost));
  const k2 = uxKpi('Gap to target', figS('gap', op, T.variance, fig(`port:${op}:variance`, usdW(T.variance, true))),
    cost ? [figS('optimize', op, G.optimize, `Optimize ${usdW(G.optimize, true)}`), uxTrendNA(op, 'gap'), resid ? `${usdW(G.residual, true)} not attributed yet: a target stated only as a bill total` : 'All of it explained']
      : [`${figS('grow', op, G.grow, `Grow ${usdW(G.grow, true)}`)} · ${figS('optimize', op, G.optimize, `Optimize ${usdW(G.optimize, true)}`)}`, uxTrendNA(op, 'gap'), resid ? `${usdW(G.residual, true)} not explained yet` : 'All of it explained']);
  const k3 = uxKpi(`Plan spend · ${periodWords()}`, `${fig(`port:${op}:spend`, usdW(P.spend))} <small>of ${usdW(budget)}</small> ${uxMark('QUOTE')}`,
    [`${num(P.visits)} of ${num(derivedPlan(op).crew_visits_limit)} ${o.crewWord}`, `${STATE_WORD[uxPlanState(op).state]}${uxPlanState(op).state === 'PROPOSED' ? ': awaiting approval' : ' in this demonstration'} · ${link('portfolio/act-first/plan', 'Review the plan')}`], uxMeterBar(P.spend, budget, `${usdW(P.spend)} of ${usdW(budget)} budget`));
  const k4 = uxKpi(PLAN_TOTAL_TITLE, `<span>${fig(`port:${op}:m12`, val === 0 ? '$0' : usdW(val, true))}${op === 'harvest' ? '' : dvTag()}</span> ${uxMark('MODELLED')}`,
    [op === 'harvest' ? 'Includes an assumed recovery share (80%) at Kirinyaga' : planRestoreNote(op) || 'Valued options only; not realised until records show it'], '', 'is-modelled');
  const n = uxDecCount(ATTN[op]);
  return `<div class="ux-overview"><p class="headline ux-headline">${hl}</p>
 <div class="heroes ux-kpis">${k1}${k2}${k3}${k4}</div>
 <div class="ux-main-aside"><section class="panel ux-queue-panel" aria-labelledby="uxq-h"><div class="panel-head"><div><h2 id="uxq-h">Decisions <span class="ux-count">${num(n)}</span> <small class="ux-split" data-ux-split>${uxStateSplit(ATTN[op].map(r => r[4]))}</small></h2><p>One row per decision, with who decides. AssetOps values the options; your team chooses.</p></div>${link('portfolio/act-first', 'Act first ›', 'ux-link')}</div>${uxQueue(op, ATTN[op].filter(r => uxMergeRows(ATTN[op]).slice(0, 6).some(m => m.d === r[4])), '', n)}${n > 6 ? `<p class="ux-more">${link('portfolio/act-first', `View all ${num(n)} in Act first`)}</p>` : n > 3 ? `<p class="ux-more ux-more-phone">${link('portfolio/act-first', `View all ${num(n)} in Act first`)}</p>` : ''}</section>
 </div>
 ${uxBridge(op)}
 ${uxCats(op)}
 <p class="ux-more-tabs">More in the tabs: ${link('portfolio/demand-and-capacity', 'where value leaks')} · ${link('portfolio/outcomes-by-site', 'outcomes by site')} · ${link('portfolio/act-first/plan', 'the plan')}</p></div>`;
}

/* ---------- Decision page header (guide §2.3, §7.2): the recommendation in one line and the primary action ---------- */

/* ---------- Site overview tiles (guide §2.3 Site row) ---------- */
function uxSiteTiles(sk) {
  const s = siteM(sk), op = SK[sk].op, o = OPS[op], t = tree(sk), decs = DEC.filter(d => d.site === sk), att = ATTN[op].filter(r => r[2] === sk);
  if (t.plan == null) return '';
  const cost = o.kind === 'cost';
  return `<div class="heroes ux-kpis">${uxKpi(cost ? 'Cost per required departure met' : 'Contribution', fig(`node:${sk}:root`, cost ? fmtU(t.actual, t.unit) : usdW(t.actual)), [`Target ${cost ? fmtU(t.plan, t.unit) : usdW(t.plan)}`, cost ? uxTrendCost(op, sk) : uxTrendNA(op, 'contribution', sk)], cost ? '' : uxBullet(t.actual, t.plan, `Contribution ${usdW(t.actual)} against a target of ${usdW(t.plan)}`))}
 ${uxKpi('Gap to target', figS('gap', sk, s.period.variance, usdW(s.period.variance, true)), [cost ? 'on cost' : 'October', uxTrendNA(op, 'gap', sk)])}
 ${(() => { const v = decs.map(d => [d, uxRec(d)]).filter(([, r]) => r && /^[+−-]?\$/.test(String(optEffect(OPT[r])[0])));
   /* review Site M1: titled by state; a chosen or released decision's value is in the plan, not "if chosen" */
   const waitingV = v.filter(([d]) => ['choose', 'none'].includes(uxDecState(d.id).key)), useV = waitingV.length ? waitingV : v, cnt = uxStateCount(decs.map(d => d.id));
   return uxKpi(!v.length ? 'Decisions at this Site' : waitingV.length ? 'Waiting for a choice: value if chosen' : 'Decisions in hand: value in the plan', useV.length ? `${wholeText(optEffect(OPT[useV[0][1]])[0])} ${uxMark(optClass(OPT[useV[0][1]]))}` : '<span class="ux-kpi-na">Not valued</span>', useV.length ? [`<span class="ux-kpi-clamp">${optLabel(useV[0][1])}, ${uxQual(useV[0][1])}</span>`, cnt] : [cnt]); })()}
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
  return out.join(' ') || '<span class="muted">No limit applies</span>';
}

/* ---------- The plan: an L1 band with the approval actions, and one line per item (review finding 6) ---------- */
function uxPlanBand(op, P, budget) {
  const o = OPS[op], S = uxPlanState(op), val = op === 'lakeside' ? P.value : op === 'harvest' ? harvestValue() : derivedPlan('metro').value, ms = crewByMonth(op, P);
  return `<section class="ux-planband" aria-label="The plan at a glance"><div class="heroes ux-kpis">
 ${uxKpi('Plan spend', `${usdW(P.spend)} <small>of ${usdW(budget)}</small> ${uxMark('QUOTE')}`, [], uxMeterBar(P.spend, budget, `${usdW(P.spend)} of ${usdW(budget)} budget`))}
 ${uxKpi(cap(o.crewWord), ms.length ? `${num(ms[0].used)} <small>of ${num(ms[0].limit)} in ${ms[0].month}</small>` : '—', ms.slice(1).map(m => `${num(m.used)} of ${num(m.limit)} in ${m.month}`))}
 ${uxKpi(PLAN_TOTAL_TITLE, `${val ? usdW(val, true) : '$0'} ${uxMark('MODELLED')}`, [planRestoreNote(op) || 'Not realised until records show it'])}
 </div><div class="ux-planact">${uxPlanStateChip(op)}${uxPlanActions(op)}<span class="ux-note">Proposed by the system on ${fdate(S.proposed)} · approver ${who(op, execOf(op))}</span></div></section>`;
}
/* the plan's state, version, who proposed it and who approves it, and the approver's two actions (one feedback pattern) */
function uxPlanStateChip(op) { const S = uxPlanState(op); return `<span class="status-pill is-${S.state === 'PROPOSED' ? 'proposed' : S.state === 'APPROVED' ? 'approved' : 'waiting'}" data-plan-state="${S.state}">${S.state === 'DRAFT' && S.by ? `Draft, sent back by ${S.by}` : `${STATE_WORD[S.state]}${S.by ? ` by ${S.by}` : ''}`} · version ${num(S.version)}</span>`; }
function uxPlanActions(op) { const S = uxPlanState(op); return S.state === 'PROPOSED' ? `${uxActButton('approve-plan', `Approve version ${num(S.version)}`, 'button primary')}${uxActButton('send-back', 'Send back')}` : `<span class="ux-note">${S.state === 'APPROVED' ? `Approved in this demonstration; its ${num(waitingSummary(op, S.ids || planItemsV1(op)).wait)} waiting Actions are released.` : `Sent back in this demonstration${S.reason ? `: “${S.reason}”` : ''}${S.giveWay ? `; ${S.giveWay} gives way` : ''}.`}</span>`;
}
const uxItemHead = () => '<div class="ux-itemh" aria-hidden="true"><span>Item</span><span>Owner</span><span>Due</span><span>One-off</span><span>Visits</span><span>Result and its period</span><span>State</span></div>';
function uxItemRow(op, id, f) {
  const it = itemOf(op, id), acts = actionsOf(op, id), due = acts.map(a => a.due).filter(Boolean).sort()[0] || it?.service_date || null;
  const st = it ? itemStateOf(op, id)?.word || '' : '';
  return `<details class="ux-item" data-row="${id}"><summary class="ux-itemrow"><span class="ux-it-main"><small>${f.site}${f.why ? ` · ${f.why}` : ''}</small><b>${f.label}</b></span><span class="ux-it-c" data-k="Owner">${it ? who(op, it.owner) : '<span class="muted">Not chosen yet</span>'}</span><span class="ux-it-c" data-k="Due">${due ? fdate(due) : '<span class="muted">No date</span>'}</span><span class="ux-it-c ux-num" data-k="One-off">${wholeText(f.cost)}</span><span class="ux-it-c ux-num" data-k="Visits">${(() => { const it2 = itemOf(op, id), c = it2?.kind === 'PROACTIVE' ? it2.crew_visits || 0 : (DOPT(id)?.crew_visits || 0); return c ? num(c) : '<span class="muted">None</span>'; })()}</span><span class="ux-it-c ux-num" data-k="Result and its period">${/of cover/.test(f.result) ? wholeText(f.result).replace(/^Protects /, '') : `${wholeText(f.result)} ${f.cls && !/^Not /.test(f.result) ? uxMark(f.cls) : ''}${f.basis ? `<small class="ux-it-basis">${f.basis}</small>` : ''}`}</span><span class="ux-it-c" data-k="State">${st ? `<span class="ux-state">${st}</span>` : ''}</span><span class="ux-disc-cue" aria-hidden="true"></span></summary><div class="ux-item-body">`;
}

/* ===== wave 2, Portfolio polish: queue controls, the row's "Why", the provenance popover, the command search, the scope
   switcher and the period menu (guide §7.1, §8). Presentation only; every list is built from the data the screen shows. ===== */
/* trend slot (guide §5, wave 2c): a sparkline of the months loaded and the change against last month. History is not loaded
   (proposal U9), so uxHistory returns null and the slot says so; nothing is ever drawn from invented months. */
/* U9 adopted (owner, 20 Nov): the history comes from the data lane's generator, evaluated like October, as
   DERIVED.history[tenant].portfolio[key] = [{ m: 'Jul', v }, …] (keys: contribution or cost, gap). Until it exists, null. */
const uxHistory = (op, key, sk) => { const h = (typeof DERIVED !== 'undefined' && DERIVED.history) || null, t = OPS[op]?.t?.tenant, b = h && h[t]; const sv = b && b.sites && (b.sites[sk] || b.sites[Object.keys(b.sites).find(k => k.split(' · ').pop() === SK[sk]?.name)]); /* history keys Sites by name (R742) */
  const s = b && (sk ? sv && sv[key] : b.portfolio && b.portfolio[key]); return Array.isArray(s) && s.length >= 2 ? s : null; }; /* series Jul–Oct; Site series keyed by the mock-up's Site keys */
function uxTrend(series, fmt = v => usdW(v, true)) {
  if (!Array.isArray(series) || series.length < 2) return '<span class="ux-trend"><span class="ux-spark-na" aria-hidden="true"></span>Trend not available yet</span>';
  const vs = series.map(p => p.v), mn = Math.min(...vs), mx = Math.max(...vs), w = 64, h = 16, X = i => (i / (vs.length - 1) * w).toFixed(1), Y = v => (h - 1 - (mx === mn ? h / 2 : (v - mn) / (mx - mn) * (h - 2))).toFixed(1);
  const d = vs.map((v, i) => `${i ? 'L' : 'M'}${X(i)} ${Y(v)}`).join(' '), ch = vs[vs.length - 1] - vs[vs.length - 2];
  return `<span class="ux-trend"><svg class="ux-spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="${series.map(p => `${p.m} ${fmt(p.v)}`).join(', ')}"><path d="${d}"/></svg>${fmt(ch)} against ${series[series.length - 2].m}</span>`;
}
const uxTrendNA = (op, key, sk) => uxTrend(op ? uxHistory(op, key, sk) : null);
/* review Site H1: monthly cost is its own measure; its line names it and says up or down, never a signed gain */
function uxTrendCost(op, sk) { const s = op ? uxHistory(op, 'cost', sk) : null; if (!Array.isArray(s) || s.length < 2) return uxTrend(null);
  const ch = Math.round(s[s.length - 1].v - s[s.length - 2].v); return `<span class="ux-trend" data-measure="monthly-cost">Monthly cost ${ch > 0 ? `up ${usdW(ch)}` : ch < 0 ? `down ${usdW(-ch)}` : 'unchanged'} against ${s[s.length - 2].m}</span>`; }

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
  return typeof IA_ROUTE_ACTIVE !== 'undefined' && IA_ROUTE_ACTIVE ? iaPaletteFilter(out) : out;
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
  name?.insertAdjacentHTML('afterend', uxScopeSwitchHtml([[`All sites · ${OPS[op].name}`, '#/portfolio', !site], ...OPS[op].sites.map(k => [SK[k].name, `#/site/${k}`, site === k])], site ? SK[site]?.name || 'All sites' : 'All sites'));
  const chip = bar.querySelector('.period-chip');
  if (chip && !chip.closest('.ux-period')) { const t = document.createElement('template'); t.innerHTML = uxPeriodMenuHtml(op, ''); const w = t.content.firstElementChild; chip.replaceWith(w); w.querySelector('summary').appendChild(chip); }
}
/* the scope switch's markup (one builder for the legacy chrome and the IA frame): entries are [label, href, current] */
function uxScopeSwitchHtml(entries, label) {
  return `<details class="ux-pop ux-scope-sw"><summary aria-label="Choose the portfolio or a site">${label} <span aria-hidden="true">▾</span></summary><div class="ux-pop-menu" role="menu"><input type="search" class="ux-sw-q" placeholder="Type a Site name" aria-label="Filter Sites" autocomplete="off">${entries.map(([l, href, cur]) => `<a role="menuitem" href="${href}"${cur ? ' aria-current="page"' : ''}>${l}</a>`).join('')}</div></details>`;
}
/* the period as a menu around the period chip; chip defaults to the operator's chip */
function uxPeriodMenuHtml(op, chip) {
  if (chip === undefined) { const sk = OPS[op].sites[0]; chip = periodChip(sk ? { site: sk } : null); }
  /* state-aware (review r2 L1): earlier months are listed from the loaded history; without it, said to be not available yet */
  const H = typeof DERIVED !== 'undefined' && DERIVED.history ? DERIVED.history[OPS[op].t.tenant] : null, past = H && Array.isArray(H.months) ? H.months.filter(m => m < '2026-10').reverse() : [];
  const mw = ym => `${MONTHS[+ym.slice(5, 7) - 1]} ${ym.slice(0, 4)}`;
  return `<details class="ux-pop ux-period"><summary aria-label="Period: October 2026. Choose a period">${chip}</summary><div class="ux-pop-menu" role="menu"><span role="menuitem" aria-current="true">October 2026 <small>current period</small></span>${past.length ? past.map(m => `<span role="menuitem" aria-disabled="true">${mw(m)} <small>shown in the trends</small></span>`).join('') : '<span role="menuitem" aria-disabled="true">September 2026 <small>not available yet</small></span>'}<span role="menuitem" aria-disabled="true">A custom range <small>not available yet</small></span></div></details>`;
}

/* ===== brand packs (guide §4.7): a configurable identity over the same tokens and components. Resolution order: the
   review-bar choice (mock tooling), then the tenant's setting (UX_BRAND_BY_TENANT, empty in the demo data), then neutral. ===== */
const UX_BRANDS = { neutral: 'Neutral', 'east-africa': 'East Africa' }; /* add 'west-africa', 'southern-africa' … as packs in brand.css */
const UX_BRAND_BY_TENANT = { 'lakeside-power': 'east-africa', 'harvest-cold': 'east-africa', 'metro-bus': 'east-africa' }; /* U10 (owner, 20 Nov): the demo operators start in East Africa; Neutral stays the product default */
function uxBrand() { let b = null; try { b = localStorage.getItem('l4-brand'); } catch (e) {} return UX_BRANDS[b] ? b : (UX_BRAND_BY_TENANT[OPS?.[LS?.op]?.t?.tenant] || 'neutral'); }
function uxApplyBrand() { const b = uxBrand(); if (b === 'neutral') document.documentElement.removeAttribute('data-brand'); else document.documentElement.setAttribute('data-brand', b); }
/* the review bar's tools (mock tooling, written by render() for every route): the D2 and D5 marks, the decision marks, the brand
   select, the developer switch (D-IA.7, D-IA.19) and what is still to be rebuilt. The order is the reviewed bar's. */
function uxReviewExtrasHtml(hash) {
  const b = uxBrand(), h = hash || '', out = [];
  if (/^#\/portfolio\/?$/.test(h) || h === '') out.push('<span class="ux-mockdev" title="RECON-1 item 2: the Grow tile shows its share of the gap; the revenue tie is in the Grow drawer">MOCK DEVIATION D2 · Grow tile</span>');
  /* MOCK DEVIATION D5, register R746: approvals and choices are kept for the browser tab only (one feedback pattern) */
  if (/^#\/(?:decision\/|portfolio\/act-first\/plan|plan(?:$|\?))/.test(h)) out.push('<span class="ux-mockdev" title="Approve, Send back and Choose show their result for this browser tab only; nothing is recorded">MOCK DEVIATION D5 · kept in this demonstration</span>');
  out.push(uxDecReviewMarks(h));
  out.push(`<span class="ux-mockdev" title="Added to the mock-up, not in the product: on-request recalculation (owner Q7)">MOCK DEVIATION D2 · Recalculate now</span><label class="ux-brand-sw">Brand <select id="ux-brand" aria-label="Brand pack (review tool)">${Object.entries(UX_BRANDS).map(([k, l]) => `<option value="${k}"${k === b ? ' selected' : ''}>${l}</option>`).join('')}</select></label>`);
  if (typeof IA_RAIL !== 'undefined') { const rest = IA_RAIL.filter(i => !IA_LANDED.has(i.unit)).map(i => i.label);
    out.push(`<label class="ux-dev-sw"><input type="checkbox" data-ia-dev${iaDev() ? ' checked' : ''}> Developer access</label>${rest.length ? `<span class="ux-rebuild">Still to be rebuilt: ${rest.join(' · ')}</span>` : ''}`); }
  return out.join('');
}
document.addEventListener('change', e => { if (!e.target.matches || !e.target.matches('[data-ia-dev]')) return; try { if (e.target.checked) sessionStorage.setItem('l4-dev', '1'); else sessionStorage.removeItem('l4-dev'); } catch (x) {} render(); });
/* the decision page's review marks live in the review bar, never in the canvas (review r1 L4; same class as wave 2c L2), with the
   control for the fourth state's fixture on a decision waiting for a choice (review r1 L2) */
function uxDecReviewMarks(hash) {
  const m = String(hash).match(/^#\/decision\/([\w-]+)/); if (!m || !decById(m[1])) return '';
  const id = m[1], st = uxDecState(id), href = `${location.pathname}${UX_NOREC ? '' : '?state=no-recommendation'}#/decision/${id}`;
  const ctl = st.key === 'choose' || UX_NOREC ? `<a class="ux-mockdev ux-rb-ctl" data-ux-norec href="${href}">${UX_NOREC ? 'Leave the preview' : 'Preview: no option recommended'}</a>` : '';
  return `<span class="ux-mockdev" title="The decision page redesigned (owner, 20 Nov)">MOCK DEVIATION D2 · decision page redesign${UX_NOREC ? ' · preview: no option recommended' : ''}</span>${ctl}`;
}
document.addEventListener('change', e => { if (e.target.id !== 'ux-brand') return; try { localStorage.setItem('l4-brand', e.target.value); } catch (x) {} uxApplyBrand(); });

document.addEventListener('input', e => { if (!e.target.classList.contains('ux-sw-q')) return; const q = e.target.value.trim().toLowerCase(); e.target.parentElement.querySelectorAll('a[role="menuitem"]').forEach(a => { a.hidden = !!q && !a.textContent.toLowerCase().includes(q); }); });

/* the top bar's search names what it searches, on every screen */
function uxSearchLabel() { const sb = document.querySelector('.topbar [data-index]'); if (!sb) return; [...sb.childNodes].filter(n => n.nodeType === 3 && n.nodeValue.trim()).forEach(n => { n.nodeValue = 'Search sites, decisions, screens'; }); sb.setAttribute('aria-label', 'Search sites, decisions and screens (Ctrl K)'); }

/* on-request recalculation (owner Q7, OD-23; MOCK DEVIATION D2, improvement): the notice turns to a neutral "requested" line, recorded under the
   signed-in person. The demo data holds no post-recalculation values, so no figure changes; the notice says so. */
const UX_RECALC_TIME = '10:00';
document.addEventListener('click', e => {
  const b = e.target.closest('[data-ux-recalc]'); if (!b) return;
  const row = b.closest('.ux-pending'), st = row?.querySelector('.snap-pending'); if (!st) return;
  const who = typeof avatarName === 'function' ? avatarName() : '', role = 'Operator executive';
  /* story time, never the wall clock: after the 09:40 invoice on the demo date */
  const rv = typeof DERIVED !== 'undefined' && DERIVED.recalc ? DERIVED.recalc[OPS[LS.op]?.t?.tenant] : null; /* filled by the data lane (3B7b); none in the demo */
  st.innerHTML = rv ? `<span class="badge">Recalculated at ${UX_RECALC_TIME}, ${fdate(AS_OF)} by ${role}${who ? ` · ${who}` : ''}: figures as of ${rv.as_of || UX_RECALC_TIME}.</span>` : `<span class="badge">Recalculation requested at ${UX_RECALC_TIME}, ${fdate(AS_OF)} by ${role}${who ? ` · ${who}` : ''}. This demo holds no recalculated values, so the figures still show 06:00.</span>`;
  st.classList.add('is-done'); b.remove();
});

/* ===== the Decision page (owner, 20 Nov: "i don't understand how 'decide' is supposed to work"); guide §2.3, §7.1-§7.3, §9b =====
   One question, one recommendation with one number and one primary choice, the options as cards with the same three numbers,
   "Why we recommend it" collapsed, evidence in a drawer, a confirmation that says what happens, and a slim status line.
   The rules stay the design's (§2.4-§2.6, decision-loop §6-§8), read by the helpers below; ruling D-2026-11-20-decision-page-rules. */

/* review fixture (guide §7.2, review r1 L2): ?state=no-recommendation shows the fourth state on a decision waiting for a choice.
   Every option that is not already rejected is shown as deferred; the review bar names the preview (never the canvas). */
const UX_NOREC = UX_STATE === 'no-recommendation';
function uxDisp(o) { const k = OPT[o]?.disposition; return UX_NOREC && k && k !== 'REJECTED' && !isNoAction(o) ? 'DEFERRED' : k; }
/* one Recommended per decision (decision-loop §6: "the Recommended option of each decision"). When the data marks a second option
   Recommended (Mto: the meter audit beside the billing fix), the first in the data's order is the recommendation and the other
   reads "Alongside the recommendation": the design lets both go ahead (worked-portfolios.md:275), but only one is the answer. */
function uxDispBadge(d, o) {
  const k = uxDisp(o);
  if (k === 'RECOMMENDED' && o !== uxRec(d)) return badge('Alongside the recommendation', 'blue');
  return k ? badge(...DISP[k]) : badge('No action (baseline)', 'outline');
}
/* a figure's own basis (review r1 H1): the second part of optEffect, the same words as the options table; never typed here */
const uxQual = o => String(optEffect(OPT[o])[1] || '');
const uxQualShort = o => uxQual(o).replace(/,? ?against (?:no action|the reference)$/, '');
const uxLcFirst = t => t ? t[0].toLowerCase() + t.slice(1) : '';
/* a figure and its basis: a money figure reads straight on ("+$672 charges restored …"), a word figure takes a colon */
const uxFigQ = (fig, q, cls) => `${fig}${/^[+−-]?\$/.test(String(fig).replace(/<[^>]+>/g, '')) ? ' ' : ': '}<span class="${cls}">${q}</span>`;

function uxDecState(id) {
  const d = decById(id); if (!d) return { key: 'choose', label: 'Waiting for a choice', btn: 'Decide' };
  const op = SK[d.site].op, D = deciderOf(id), it = D.item ? itemOf(op, D.item) : null, rec = uxRec(d);
  if (it && (it.item_state === 'RELEASED' || planReleasedItem(op, D.item))) return { key: 'released', label: 'Released: Actions under way', btn: 'Review' }; /* the one state source: the plan state shown counts (review r4 M1) */
  if (it && planIsDraft(op)) return { key: 'approval', draft: true, label: 'Chosen · the plan was sent back to draft', btn: 'Review' };
  if (it) return { key: 'approval', label: 'Chosen · awaiting approval', btn: 'Awaiting approval' };
  const mk = uxMock().chosen?.[id]; /* a choice made in this demonstration (one feedback pattern) */
  if (mk) { const p = uxReleaseFor(op, mk).path; return p === 'at' || p === 'none' ? { key: 'released', label: 'Chosen in this demonstration: Actions go ahead', btn: 'Review' } : { key: 'approval', label: 'Chosen in this demonstration · awaiting approval', btn: 'Awaiting approval' }; }
  if (!rec) return { key: 'none', label: 'No option recommended', btn: 'Review' };
  return { key: 'choose', label: 'Waiting for a choice', btn: 'Decide' };
}

/* capital (decision-loop §6 and §8, OD-17): a capital item, a new connection, a capital purchase, or a decision the executive
   chooses (an expansion). An expansion is listed beside the plan, not valued as a saving (worked-portfolios.md:582). */
const uxChooserRole = d => ((HC.decisions || []).find(x => x.id === d.id) || {}).chooser || '';
function uxCapital(op, oid) {
  const d = DEC.find(x => x.opts.includes(oid)), it = itemOf(op, oid), k = OPT[oid]?.kind;
  if (!oid || isNoAction(oid)) return '';
  if (d && uxChooserRole(d) === 'OPERATOR_EXECUTIVE') return 'expansion';
  if (it && it.capital === 'NEW_CONNECTION' || k === 'DEMAND_CONNECTION') return 'connection';
  if (it && it.capital || k === 'CAPEX') return 'capital';
  return '';
}
/* what a choice would do (decision-loop §6): its path and the words for it.
   path: 'none' (spends no shared budget or crew visit: not a plan item, its Actions go ahead once created),
         'at' (a plan item within both thresholds: released when its Actions are created, while the plan still fits),
         'wait' (a plan item above a threshold: waits for the plan's approval), 'capital' (waits for the executive's approval) */
function uxReleaseFor(op, oid) {
  const w = WF(op), x = DOPT(oid) || {}, spend = x.operator_one_off || 0, crew = x.crew_visits || 0, ex = execOf(op), cap = uxCapital(op, oid), cw = OPS[op].crewWord;
  const inPlan = planCase(op).ids.includes(oid);
  if (cap === 'expansion') return { path: 'capital', cap, inPlan: false, text: `Waits for ${who(op, ex)}’s approval of the plan version that holds it: an expansion is capital, listed beside the plan and never released when chosen` };
  if (cap) return { path: 'capital', cap, inPlan, text: `Waits for ${who(op, ex)}’s approval of the plan version that holds it: ${cap === 'connection' ? 'a new connection' : 'a capital purchase'} is capital, whatever its spend` };
  if (!spend && !crew) return { path: 'none', inPlan: false, text: `No approval needed: it spends no shared budget and no ${cw}, so it is not a plan item` };
  const overS = spend > w.spend_threshold, overC = crew > w.crew_visit_threshold;
  if (!overS && !overC) return { path: 'at', inPlan, text: `Released when its Actions are created: ${usdW(spend)} is within the ${usdW(w.spend_threshold)} spend threshold${crew ? '' : `, with no ${crewOne(op)}`}, while the plan still fits its budget and ${cw}` };
  return { path: 'wait', inPlan, text: `Waits for ${who(op, ex)}’s approval of the plan: ${overS ? `${usdW(spend)} is above the ${usdW(w.spend_threshold)} spend threshold` : ''}${overS && overC ? ' and ' : ''}${overC ? `it uses ${num(crew)} ${crew === 1 ? crewOne(op) : cw}, above the threshold of ${num(w.crew_visit_threshold)}` : ''}` };
}
/* the plan line under the recommendation, from the same path (review r1 M1: never claim a fit that was not checked) */
function uxPlanNote(op, oid) {
  const R = uxReleaseFor(op, oid), ex = execOf(op), cw = OPS[op].crewWord;
  if (R.cap === 'expansion') return `Once chosen, it waits for ${who(op, ex)}’s approval of the plan version that holds it, and its Actions are created after that approval.`;
  if (R.path === 'capital') return `${R.inPlan ? 'In the proposed plan as capital' : 'A capital choice'}: once chosen, it waits for ${who(op, ex)}’s approval of the plan.`;
  if (R.path === 'none') return `It spends no shared budget and no ${cw}, so it is not a plan item; its Actions go ahead once created.`;
  if (!R.inPlan) return `Not in the proposed plan: choosing it adds a plan item, and the plan’s budget and ${cw} are checked when its Actions are created.`;
  return '';
}
/* who creates the Actions (decision-loop §8, "Create an Action"): the finance and commercial lead creates every notice and claim
   Action and the Actions on money Findings; the Site manager creates operational Actions on the items they chose. An expansion's
   Actions are created after the executive's approval by the Site's manager (operational) and the finance lead (any notice or
   claim): the executive creates none (ruling D-2026-11-20-decision-page-rules, item 4). */
const UX_CLAIM_KINDS = ['SUPPLIER_REMEDY', 'RIGHTS_REVIEW', 'COMMERCIAL_CORRECTION'];
function uxCreators(op, d, oid) {
  const fin = personByRole(op, 'FINANCE_AND_COMMERCIAL_LEAD'), sm = personByRole(op, 'SITE_MANAGER', SK[d.site].name), k = OPT[oid]?.kind;
  if (uxCapital(op, oid) === 'expansion') return [[sm, 'the operational Actions'], [fin, 'any notice or claim']];
  if (uxChooserRole(d) === 'FINANCE_AND_COMMERCIAL_LEAD') return [[fin, 'the Actions']]; /* a money Finding's decision */
  if (k === 'STOPGAP_PLUS_CLAIM') return [[fin, 'the claim and its notice'], [sm, 'the operational Actions']];
  if (k === 'SUPPLIER_REMEDY') return [[fin, 'the claim and notice Actions'], [sm, 'any operational step']]; /* r2 L5: a remedy's operational step is the Site manager's */
  if (UX_CLAIM_KINDS.includes(k)) return [[fin, k === 'COMMERCIAL_CORRECTION' ? 'the billing Actions' : 'the claim and notice Actions']];
  return [[sm, 'the Actions']];
}
function uxCreatorText(op, d, oid) {
  const it = itemOf(op, oid), R = uxReleaseFor(op, oid), ex = execOf(op);
  if (it?.actions_after_approval?.length) return `After ${who(op, ex)}’s approval, ${who(op, it.owner)} creates: ${it.actions_after_approval.join('; ')}.`;
  const parts = uxCreators(op, d, oid).filter(([p]) => p).map(([p, what]) => `${who(op, p)} creates ${what}`);
  return `${R.path === 'capital' ? `After ${who(op, ex)}’s approval, ` : 'After the choice, '}${parts.join('; ')}.`;
}

/* the status line follows the real path (review r1 M2): a choice released at once never waited for approval; with nothing
   recommended, the first step says so */
function uxDecSteps(id, st) {
  const d = decById(id), op = SK[d.site].op, oid = deciderOf(id).item || uxMock().chosen?.[id] || uxRec(d) || d.opts.find(o => !isNoAction(o) && uxDisp(o) !== 'REJECTED'), /* r2 L2: with nothing recommended, the path of an option that can be chosen */ path = oid ? uxReleaseFor(op, oid).path : 'wait';
  const it = deciderOf(id).item ? itemOf(op, deciderOf(id).item) : null, atOnce = st.key === 'released' && it && releaseOf(op, it.item).at;
  const tail = atOnce || path === 'at' ? ['Released at once'] : path === 'none' ? ['Actions go ahead'] : ['Awaiting approval', 'Actions released'];
  const steps = [st.key === 'none' ? 'No option recommended' : 'Recommended', 'Chosen', ...tail];
  const cur = st.key === 'released' ? steps.length - 1 : st.key === 'approval' ? 2 : 0;
  return { steps, cur };
}
function uxDecStatus(id, st) {
  const { steps, cur } = uxDecSteps(id, st);
  return `<ol class="ux-dsteps" aria-label="Where this decision is">${steps.map((s, i) => `<li class="${i < cur ? 'is-done' : i === cur ? 'is-current' : ''}"${i === cur ? ' aria-current="step"' : ''}>${s}</li>`).join('')}</ol>`;
}
/* the honest reason when nothing is recommended, from the dispositions shown */
function uxNoRecReason(id) {
  const d = decById(id), op = SK[d.site].op, D = deciderOf(id), opts = d.opts.filter(o => !isNoAction(o)), n = k => opts.filter(o => uxDisp(o) === k).length;
  const rej = n('REJECTED'), def = n('DEFERRED'), other = opts.length - rej - def;
  const parts = [rej ? `${num(rej)} ${rej === 1 ? 'is' : 'are'} rejected` : '', def ? `${num(def)} ${def === 1 ? 'is' : 'are'} deferred` : '', other ? `${num(other)} ${other === 1 ? 'is' : 'are'} allowed but none does better than ${(BASIS_WORDS[decBasis(d)] || 'against the reference').replace(/^against /, '')} within the limits` : ''].filter(Boolean);
  return `No option is recommended: of ${num(opts.length)} option${opts.length === 1 ? '' : 's'}, ${parts.join(' and ')}. ${who(op, D.p)} can still choose ${rej === opts.length ? 'to do nothing' : 'one, or none'}.`;
}
/* the question is the page's title (review r1 L5): the decision's name, as a question */
const uxDecQuestion = d => `What should we do about the ${String(d.q).replace(/: (.+)$/, ' ($1)')}?`;

function uxChooseDialog(id, oid) {
  const d = decById(id), op = SK[d.site].op, D = deciderOf(id), R = uxReleaseFor(op, oid), acts = actionsOf(op, oid), [ev] = optEffect(OPT[oid]), cw = OPS[op].crewWord;
  const actHtml = acts.length ? `<ul class="list">${acts.map(a => `<li>${a.action}<small class="cellnote"> created by ${who(op, a.created_by)}${a.owner !== a.created_by ? `, owned by ${who(op, a.owner)}` : ''}, due ${fdate(a.due)}</small></li>`).join('')}</ul>`
    : `<p>${uxCreatorText(op, d, oid)}</p>`;
  const what = R.cap === 'expansion' ? `${optLabel(oid)} is an expansion: listed beside the plan, not counted in it, until ${who(op, execOf(op))} approves the plan version that holds it.`
    : R.path === 'capital' ? `${optLabel(oid)} becomes a capital plan item, held for ${who(op, execOf(op))}’s approval.`
    : R.path === 'none' ? `${optLabel(oid)} spends no shared budget and no ${cw}, so it is not a plan item. Its Actions go ahead once created.`
    : R.inPlan ? `${optLabel(oid)} becomes a plan item; it is in the proposed plan.` : `${optLabel(oid)} becomes a plan item. It is not in the proposed plan, so the plan’s budget and ${cw} are checked when its Actions are created.`;
  return uxDrawer(`uxc-${id}-${oid}`, `Choose: ${optLabel(oid)}`, `<dl class="ux-confirm"><div><dt>What happens</dt><dd>${what}</dd></div>
   <div><dt>${BASIS_LABEL[optBasis(oid)]}</dt><dd>${uxFigQ(wholeText(ev), uxQual(oid), 'ux-confirm-q')}${optContext(oid).length ? `<ul class="list ux-ctx">${optContext(oid).map(t => `<li>${t}</li>`).join('')}</ul>` : ''}</dd></div>
   <div><dt>Actions</dt><dd>${actHtml}</dd></div><div><dt>Approval</dt><dd>${R.text}.</dd></div><div><dt>Recorded under</dt><dd>${who(op, D.p)}, with the time.</dd></div></dl>
   <div class="ux-confirm-go"><button type="button" class="button primary" data-ux-act-go="choose:${id}:${oid}">Confirm the choice</button><button type="button" class="button" data-ux-close>Cancel</button></div>`);
}
/* Confirm closes the dialog with a neutral notice (review r1 L6): the demonstration records nothing */
/* Confirm the choice uses the one feedback pattern (uxActDo): toast with Undo, then the decision's state changes on the page */
function uxChooseAct(id, oid) { return { title: `Choose: ${optLabel(oid)}`, primary: 'Confirm the choice', body: '', apply: () => ({ chosen: { [id]: oid } }), toast: `${optLabel(oid)} chosen` }; }

function uxDecisionPage(id, parts) {
  const d = decById(id), op = SK[d.site].op, D = deciderOf(id), st = uxDecState(id), rec = uxRec(d), x = rec ? OPT[rec] : null, T = decText(d);
  const due = ATTN[op].filter(r => r[4] === id).map(r => uxDueIso(id, r[3])).filter(Boolean).sort()[0] || '';
  const ex = execOf(op), chosen = D.item || uxMock().chosen?.[id] || null;
  const [ev] = x ? optEffect(x) : ['—'], [cv] = x ? optCost(x) : ['—'], money = v => /^[+−-]?\$/.test(String(v));
  /* certainty said once when every valued option shares it (guide §6, U1) */
  const valued = d.opts.filter(o => money(optEffect(OPT[o])[0]) && !isNoAction(o)), classes = [...new Set(valued.map(o => optClass(OPT[o])))];
  const oneClass = classes.length === 1 ? classes[0] : null, anyDv = valued.some(o => DV_OPT[o] && String(DV_OPT[o]).startsWith(DVTEXT));
  const head = `<section class="ux-dhd" aria-label="Decision status"><p class="ux-dmeta"><span>${SK[d.site].name}</span><span>Decides: ${who(op, D.p)}</span><span>${due ? `Due ${fdate(due)}` : 'No deadline'}</span><span class="status-pill is-${st.key === 'released' ? 'approved' : st.key === 'approval' ? 'waiting' : 'proposed'}">${st.label}</span></p>
  ${uxDecStatus(id, st)}${uxOpener(`uxhow-${id}`, 'How this works', 'ux-link ux-how')}</section>`;
  const pays = x ? whoPays(x) : '—';
  const noCost = /^\$0$/.test(String(wholeText(cv)).trim());
  /* a hero without a number shows the strongest fact the data holds (UX audit C17): the cover or credit at stake */
  const SP = !money(ev) ? uxStakeParts(id) : {}, heroNote = SP.note === 'cover kept claimable' ? 'of cover, claimable only with this evidence' : SP.note;
  /* r3 L1: a hero states the strongest fact the data holds, with its marker: cover or credit at stake (not money); the opportunity in
     its own unit; else the cost and who bears it. A category ("No saving claimed") never leads in display size */
  const hero = SP.value ? `<p class="ux-drec-n"><b>${SP.value}</b> <span>${heroNote}</span> <span class="ux-chip is-neutral">At stake, not money</span></p>` : SP.wnote ? `<p class="ux-drec-n"><b>${SP.wnote}</b></p>` : !money(ev) && x && !noCost ? `<p class="ux-drec-n"><b>${wholeText(cv)}</b> <span>one-off${pays !== '—' ? `, ${uxLcFirst(pays)}` : ''}</span></p>` : '';
  const recNum = x ? `${hero}<p class="ux-drec-n${hero ? ' is-second' : ''}">${uxFigQ(hero ? wholeText(ev) : `<b>${wholeText(ev)}</b>`, uxQual(rec), 'ux-drec-q')}${money(ev) && BASIS_WORDS[optBasis(rec)] ? `<span class="ux-drec-c">, ${BASIS_WORDS[optBasis(rec)]}</span>` : ''}${money(ev) ? ` ${uxMark(optClass(x))}${DV_OPT[rec] ? ` ${dvTag(DV_OPT[rec])}` : ''}` : ''} · ${noCost ? 'no one-off cost' : `costs ${wholeText(cv)}${pays !== '—' ? `, ${uxLcFirst(pays)}` : ''}`}</p>` : '';
  let act = '';
  /* "Choose another option" only when another option can be chosen (review r2 M2 class) */
  const others = d.opts.filter(o => o !== rec && !isNoAction(o) && uxDisp(o) !== 'REJECTED' && uxDisp(o) !== 'RECOMMENDED');
  if (st.key === 'choose') act = `${uxOpener(`uxc-${id}-${rec}`, 'Choose this', 'button primary')}${others.length ? `<a class="button" href="#uxcards-${id}">Choose another option</a>` : ''}`;
  else if (st.key === 'approval') act = `<span>Chosen by ${who(op, D.p)}: ${optLabel(chosen)}. Awaiting ${who(op, ex)}’s approval of the plan.</span>${link('portfolio/act-first/plan', 'Review the plan', 'button')}`;
  else if (st.key === 'released') act = `<span>Chosen by ${who(op, D.p)}: ${optLabel(chosen)}. ${planReleasedItem(op, chosen) ? `Released when ${uxPlanState(op).by || 'the executive'} approved the plan.` : uxReleaseFor(op, chosen).text + '.'}</span>${uxOpener(`uxacts-${id}`, 'See the Actions', 'button')}`;
  else act = `<a class="button" href="#uxcards-${id}">See the options</a>`;
  const planNote = x && st.key === 'choose' ? uxPlanNote(op, rec) : '';
  const recCard = `<section class="panel ux-drec" aria-labelledby="uxdr-${id}"><div class="ux-eyebrow">${x ? 'We recommend' : 'No option recommended'}</div><h2 id="uxdr-${id}">${x ? optLabel(rec) : `Each option ${BASIS_WORDS[decBasis(d)] ? `valued ${BASIS_WORDS[decBasis(d)]}` : 'compared, not valued in money'}`}</h2>${recNum}${x ? (optContext(rec).length ? `<ul class="list ux-ctx">${optContext(rec).map(c => `<li>${c}</li>`).join('')}</ul>` : '') : `<p class="ux-note">${uxNoRecReason(id)}</p>`}${planNote ? `<p class="ux-note">${planNote}</p>` : ''}<div class="ux-dgo">${act}${uxOpener(`uxev-${id}`, 'Evidence and records', 'ux-link')}</div></section>`;
  const quals = new Set(d.opts.filter(o => !isNoAction(o)).map(uxQual)), oneQual = quals.size === 1 ? [...quals][0] : null;
  const cards = d.opts.map(o => { const y = OPT[o], [e2] = optEffect(y), [c2] = optCost(y), isRec = o === rec, isNo = isNoAction(o) && decBasis(d) !== 'RESTORE_REFERENCE', k = uxDisp(o), q2 = uxQual(o);
    const mark = money(e2) && !isNo && (!oneClass || optClass(y) !== oneClass) ? uxMark(optClass(y)) : '';
    const dv = money(e2) && !isNo && DV_OPT[o] ? dvTag(DV_OPT[o]) : '';
    const go = (st.key === 'choose' || st.key === 'none') && !isRec && !isNoAction(o) && k !== 'REJECTED' && k !== 'RECOMMENDED' ? uxOpener(`uxc-${id}-${o}`, 'Choose this instead', 'button') : '';
    const why = UX_NOREC && k !== y.disposition ? 'Deferred for now.' : (k === 'REJECTED' || k === 'DEFERRED' || (k === 'RECOMMENDED' && !isRec)) ? optWhy(y) : '';
    const result = isNo ? `The baseline${q2 && q2 !== 'baseline' ? ` <small class="ux-ocard-q">${q2}</small>` : ''}` : `${uxFigQ(wholeText(e2), q2, 'ux-ocard-q')} ${mark}${dv ? ` ${dv}` : ''}`;
    return `<article class="ux-ocard${isRec ? ' is-rec' : ''}${isNo ? ' is-base' : ''}${o === chosen ? ' is-chosen' : ''}" data-opt-card="${o}"><header><h3>${optLabel(o)}</h3>${o === chosen ? '<span class="status-pill is-approved">Chosen</span>' : isNo ? '<span class="ux-chip is-neutral">The baseline</span>' : uxDispBadge(d, o)}</header>
     <dl><div><dt>Result</dt><dd>${result}</dd></div><div><dt>One-off cost</dt><dd>${wholeText(c2)}${/^\$0$/.test(String(wholeText(c2)).trim()) ? '' : ` <small>${whoPays(y)}</small>`}</dd></div><div><dt>Limits</dt><dd>${uxOblSummary(obligations(y))}</dd></div></dl>
     ${why ? `<p class="ux-ocard-why">${why}</p>` : ''}${go}</article>`; }).join('');
  const cardsSec = `<section class="ux-ocards" id="uxcards-${id}" aria-labelledby="uxoc-${id}"><div class="ux-row-head"><h2 id="uxoc-${id}">${BASIS_CARDS[decBasis(d)]}</h2><span class="ux-note">${oneQual && /^(?:over|to) /.test(oneQual) ? `Each result ${uxLcFirst(oneQual)}` : 'Each result as stated on its card'}${anyDv ? '; † design estimates' : ''}</span></div><div class="ux-ocards-grid">${cards}</div></section>`;
  const dialogs = st.key === 'choose' || st.key === 'none' ? d.opts.filter(o => !isNoAction(o) && uxDisp(o) !== 'REJECTED').map(o => uxChooseDialog(id, o)).join('') : '';
  const evidence = uxDrawer(`uxev-${id}`, 'Evidence and records', `<ul class="list">${T.records.map(([k, l]) => `<li>${fig(k, l)}</li>`).join('')}</ul>${(d.rights || []).map(rightsPanel).join('')}`, true);
  /* answer-titled sections, one level (the long-page standard; UX audit #8): each heading says its answer while closed */
  const plain = s => String(s || '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim(), first = s => (plain(s).match(/^.*?[.!?](?=\s|$)/) || [plain(s)])[0];
  /* every closed answer is derived from the rows its section and the cards show (review r3 M1): the baseline is left out only
     where it is shown as the baseline; "cannot be checked yet" is said; the counts are the cards' */
  const isBase = o => isNoAction(o) && decBasis(d) !== 'RESTORE_REFERENCE', lim = o => { const h = obligations(OPT[o]); return /obl-fail/.test(h) ? 'fail' : /obl-unknown/.test(h) ? 'unknown' : /obl-(?:pass|cost)/.test(h) ? 'pass' : 'none'; };
  const optsShown = d.opts.filter(o => !isBase(o)), otherOpts = optsShown.filter(o => o !== rec), base = d.opts.find(isBase);
  const oFail = otherOpts.filter(o => lim(o) === 'fail').length, oUnk = otherOpts.filter(o => lim(o) === 'unknown').length, recLim = x ? lim(rec) : null;
  const limitsAns = d.opts.every(o => lim(o) === 'none') ? 'No limit applies to these options'
    : [x ? { fail: 'The recommendation breaks a limit', unknown: 'The recommendation cannot be checked against every limit yet', pass: 'The recommendation keeps every limit', none: 'No limit applies to the recommendation' }[recLim] : '',
       oFail ? `${num(oFail)} ${x ? 'other ' : ''}option${oFail === 1 ? ' breaks' : 's break'} one` : '', oUnk ? `${num(oUnk)} cannot be checked yet` : '', base && lim(base) === 'fail' ? 'doing nothing breaks one' : ''].filter(Boolean).join('; ');
  const costAns = x ? `${noCost ? 'No one-off cost' : `${wholeText(cv)} one-off`}${!noCost && pays !== '—' ? `, ${uxLcFirst(pays)}` : ''}` : 'Each option’s cost is on its card';
  const rejN = optsShown.filter(o => ['REJECTED', 'DEFERRED'].includes(uxDisp(o))).length, optN = optsShown.length;
  /* the closed "why" is the decision's own reason (WHY_PICK names which sentences of its reasoning carry it); model words are dropped */
  const sentences = plain(T.why).split(/(?<=[.!?])\s+(?=[A-Z$0-9])/), whyAns = (WHY_PICK[id] || [0]).map(i => sentences[i] || '').join(' ').trim();
  const plainAns = s => String(s).replace(/\b(\w+)-([\w-]+) (?:factor|driver)\b/g, (m, a, b) => `${a} ${b.replace(/-/g, ' ')}`).replace(/\b(factor|driver)(s?)\b/g, 'measure$2'); /* model words out of closed headings (r3 L3) */
  const limitsBody = `${parts.protective ? `<p class="prose">${parts.protective}</p>` : ''}${parts.bound || ''}${parts.capacity || ''}${parts.protect || ''}${parts.cover || ''}` || `<ul class="list">${d.opts.map(o => `<li>${optLabel(o)}: ${uxOblSummary(obligations(OPT[o]))}</li>`).join('')}</ul>`;
  const costBody = parts.costs || `<ul class="list">${d.opts.filter(o => !isBase(o)).map(o => { const [c] = optCost(OPT[o]), w = whoPays(OPT[o]); return `<li>${optLabel(o)}: ${wholeText(c)}${/^\$0$/.test(String(wholeText(c)).trim()) || w === '—' ? '' : `, ${uxLcFirst(w)}`}</li>`; }).join('')}</ul>`;
  const verifyAns = T.verify[0] ? `First check: ${uxLcFirst(plain(T.verify[0][1]))}` : 'Three separate verdicts; none given yet';
  const sections = [
    [st.key === 'none' ? 'Why no option is recommended' : 'Why we recommend it', x ? plainAns(whyAns) : `${num(rejN)} of ${num(optN)} options are rejected or deferred`, `<p class="prose">${T.why}</p><h3 class="ux-sub-h">What would change the recommendation</h3><ul class="list">${T.sens.map(s => `<li>${s}</li>`).join('')}</ul>`],
    ['What it changes', plainAns(plain(T.change).split(/(?<=[.!?])\s+(?=[A-Z$0-9])/)[0]), `${parts.anchor}${parts.cf}${parts.restore || ''}`],
    ['Limits and cover', limitsAns, limitsBody],
    ['Cost and who pays', costAns, costBody],
    ['How we will check it worked', verifyAns, parts.verify],
    ['All options in detail', `${num(optN)} option${optN === 1 ? '' : 's'}${BASIS_WORDS[decBasis(d)] ? ` ${BASIS_WORDS[decBasis(d)]}` : ''}${rejN ? `; ${num(rejN)} rejected or deferred, each with its reason` : ''}`, parts.comp]
  ];
  const why = `<div class="ux-dsecs">${sections.map(([l, a, b]) => uxSecA(l, a, b)).join('')}</div>`;
  /* how the product works lives in help, not in the decision path; who decides and approves stays on the page (meta line) */
  const howDrawer = uxDrawer(`uxhow-${id}`, 'How this works', `<div id="uxwho-${id}">${whoDecides(id)}</div>`, true);
  const actsDrawer = chosen ? uxDrawer(`uxacts-${id}`, 'The Actions', actionsOf(op, chosen).length ? `<ul class="list">${actionsOf(op, chosen).map(a => `<li>${a.action}<small class="cellnote"> created by ${who(op, a.created_by)}${a.owner === a.created_by ? ', who owns it' : `, owned by ${who(op, a.owner)}`}, due ${fdate(a.due)}</small></li>`).join('')}</ul>` : `<p>${uxCreatorText(op, d, chosen)}</p>`) : '';
  /* context that stays (the long-page standard): once the recommendation scrolls away, a slim bar keeps the title, the key figure, the
     state and the primary action; on a phone it sits at the bottom */
  const stickyAct = st.key === 'choose' ? uxOpener(`uxc-${id}-${rec}`, 'Choose this', 'button primary') : st.key === 'approval' ? link('portfolio/act-first/plan', 'Review the plan', 'button') : st.key === 'released' ? uxOpener(`uxacts-${id}`, 'See the Actions', 'button') : '';
  const sticky = `<div class="ux-dsticky" role="region" aria-label="This decision" data-ux-sticky><span class="ux-dsticky-t">${d.q}</span><span class="ux-dsticky-n">${x ? (money(ev) ? `${wholeText(ev)} <small>${uxQual(rec)}</small>` : `<small>${plain(ev)}</small>`) : ''}</span><span class="status-pill is-${st.key === 'released' ? 'approved' : st.key === 'approval' ? 'waiting' : 'proposed'}">${st.label}</span>${stickyAct}</div>`;
  return `${sticky}${head}${recCard}${cardsSec}${why}${dialogs}${evidence}${actsDrawer}${howDrawer}`;
}
/* lists are capped at 7 rows, then "Show all" (the long-page standard); option comparisons are tables and are never cut */
function uxCapLists(root) { root.querySelectorAll('ul.list').forEach((ul, i) => { if (ul.closest('.ux-drawer')) return; const li = [...ul.children].filter(x => x.tagName === 'LI'); if (li.length <= 7) return;
  if (!ul.id) ul.id = `uxcap-${i}`; li.slice(7).forEach(x => { x.hidden = true; x.dataset.uxOver = ''; }); ul.insertAdjacentHTML('afterend', uxCapNote(li.length, 7, ul.id)); }); }
/* an answer-titled section: the label and its answer, visible when closed */
const uxSecA = (label, answer, body) => `<details class="panel ux-disc ux-ans-sec"><summary><span class="ux-disc-t"><span class="ux-h2">${label}</span><span class="ux-ans">${answer}</span></span><span class="ux-disc-cue" aria-hidden="true"></span></summary><div class="ux-disc-body">${body}</div></details>`;
/* the sticky bar shows once the recommendation card has scrolled under the top bar */
function uxStickyTick() { const b = document.querySelector('[data-ux-sticky]'), r = document.querySelector('.ux-drec') || document.querySelector('.ux-kpis') || document.querySelector('[data-ux-sticky-anchor]'); if (!b || !r) { document.body.style.paddingBottom = ''; document.documentElement.style.scrollPaddingTop = ''; document.documentElement.style.scrollPaddingBottom = ''; return; } const on = r.getBoundingClientRect().bottom < Math.max(0, document.querySelector('.topbar')?.getBoundingClientRect().bottom || 0); b.classList.toggle('is-on', on); document.documentElement.classList.toggle('ux-has-sticky', on);
  /* r3 L4: the bar starts where the rail ends, measured, never typed */ const rail = document.querySelector('.rail'), rr = rail && rail.getBoundingClientRect(); const HS = document.documentElement.style; /* IA-1a (D-IA.17): the measured offsets live on <html>, outside the frame */ HS.setProperty('--ux-sticky-left', rr && rr.width > 0 && innerWidth > 600 ? `${Math.round(rr.right)}px` : '0px'); if (innerWidth > 600) HS.setProperty('--ux-sticky-top', `${Math.max(0, Math.round(document.querySelector('.reviewbar')?.getBoundingClientRect().bottom || 0))}px`); else HS.removeProperty('--ux-sticky-top');
  /* the scroll padding is the bar's measured height, so a focused control is never left under it (WCAG 2.4.11) */
  const bh = on ? Math.ceil(b.getBoundingClientRect().height) + 8 : 0, H = document.documentElement; if (innerWidth > 600) { H.style.scrollPaddingTop = bh ? `${bh}px` : ''; H.style.scrollPaddingBottom = ''; document.body.style.paddingBottom = ''; } else { H.style.scrollPaddingBottom = `${Math.max(bh, 112)}px`; H.style.scrollPaddingTop = ''; document.body.style.paddingBottom = `${Math.max(bh, 112)}px`; } } /* on a phone the page always reserves the bar's room, so its last control can scroll clear */
window.addEventListener('scroll', uxStickyTick, { passive: true }); window.addEventListener('hashchange', () => setTimeout(uxStickyTick, 50));

/* ===== empty states that name their data (placeholder audit, gap 4): a not-available state carries data-na-path; the check
   fails it when the data holds a value at that path ===== */
function uxPathValue(path) { let o = typeof DERIVED !== 'undefined' ? DERIVED : null; for (const k of String(path).split('.')) { if (o == null) return null; o = o[k]; } return o == null ? null : o; }
/* the earlier-view boards read the data where it exists (Kobo billing and target, Thika cooling energy, Ruiru's roster) and
   drop the asks a captive fleet rules out (settlement records, odometer readings, a tariff estimate) */
function uxBoardsFromData() {
  if (typeof BOARD === 'undefined' || uxBoardsFromData.done) return; uxBoardsFromData.done = true;
  const row = (b, label) => { for (const k of Object.keys(b || {})) { const c = b[k] && b[k].contrib; if (!Array.isArray(c)) continue; const r = c.find(x => x[0] === label); if (r) return [c, r]; } return [null, null]; };
  try {
    const ko = siteM('kobo').period.actual, kt = tree('kobo');
    let [, r] = row(BOARD.mini, 'Cash collected'); if (r && ko.collected != null) { r[1] = `${usd(ko.collected)} collected of ${usd(ko.revenue)} billed in October`; r[2] = 'Recorded'; }
    [, r] = row(BOARD.mini, 'Actual against plan'); if (r && kt.plan != null) { r[0] = 'Actual against target'; r[1] = `Contribution ${usd(kt.actual)} against a target of ${usd(kt.plan)}`; r[2] = 'Recorded'; }
    const th = siteM('thika').period.actual; [, r] = row(BOARD.cold, 'Cooling energy'); if (r && th.kwh != null) { r[1] = `${num(th.kwh)} kWh, ${usd(th.energy)} in October`; r[2] = 'Measured'; }
    const ru = siteM('ruiru').period.actual; [, r] = row(BOARD.ev, 'Departures against the timetable'); if (r && ru.departures_required != null) { r[1] = `${num(ru.departures_met)} of ${num(ru.departures_required)} required departures met in October`; r[2] = 'Recorded'; }
    for (const k of Object.keys(BOARD.ev || {})) { const c = BOARD.ev[k] && BOARD.ev[k].contrib; if (Array.isArray(c)) BOARD.ev[k].contrib = c.filter(x => !/^Energy billed against metered/.test(x[0])); }
    if (BOARD.ev?.cost) BOARD.ev.cost.sub = 'A captive fleet is judged on charging cost per required departure met; it earns no tariff revenue';
    if (BOARD.ev?.grow) { BOARD.ev.grow.head = 'Revenue not applicable: charging is a cost centre'; BOARD.ev.grow.st = 'na'; } /* r2 M3 */
  } catch (e) { /* the boards keep their text if a read fails */ }
}
uxBoardsFromData.done = false;
uxBoardsFromData();

/* ===== one shell model (UX audit C1, C3, C4; owner standing brief, RULES §6): the navigable product is the new model only.
   One period (the period chip), one Site name (SK), one status vocabulary per object, one Finding and Action store (the plan's),
   every surface scoped to the active operator. A v7.0 screen kept for review that is not converted leaves the navigation: the
   product never links into it (it stays in the review bar's Screen index). ===== */
const UX_SCOPED = ['sites', 'site-create-form', 'site-create-template', 'site-batch-upload', 'site-setup-history', 'assets', 'assets-warranty', 'incidents', 'maintenance', 'maintenance-preventive', 'oprecords', 'globalevidence', 'settings-policies', 'settings-tenant'];
const uxInProduct = s => !!s && s.root !== 'Simulator Lab' && !s.stub && (s.loop || s.opScoped || UX_SCOPED.includes(s.id));
/* an element's words with cell and tag boundaries kept (textContent runs "DC charger" and "Ruiru" together) */
const uxWords = e => { const out = [], tw = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); while (tw.nextNode()) out.push(tw.currentNode.nodeValue); return out.join(' '); };
const uxRouteOf = href => String(href || '').replace(/^#\//, '').split('?')[0];
function uxIsClassic(id) { const s = SCREENS.find(x => x.id === id) || (typeof ALIAS !== 'undefined' && ALIAS[id] ? SCREENS.find(x => x.id === ALIAS[id]) : null); return !!s && s.root !== 'Simulator Lab' && !uxInProduct(s); }
/* the kept v7.0 records, by key (review H3: scope by data, not by rendered names): each record, asset or vendor key names the
   Site(s) it belongs to. The v7.0 lists hold examples for one Site per operator (Kobo, Thika, Ruiru). */
const V70_KEYS = {
  kobo: ['BAT-001', 'GEN-001', 'INV-001', 'REC-305', 'REC-306', 'REC-307', 'CHG-019', 'ACT-048', 'ACT-049', 'F-104', 'F-109'],
  thika: ['CMP-003', 'GEN-CR-01', 'ATS-CR-01', 'BAT-CR-01', 'INC-203', 'WR-011', 'WR-016', 'WR-019', 'REC-311', 'REC-312', 'REC-313', 'F-118', 'F-119', 'ACT-051'],
  ruiru: ['CHG-001', 'CHG-002', 'WR-021', 'REC-320', 'REC-321', 'ACT-061', 'F-130']
};
const V70_VENDORS = { 'Northwind Storage': ['kobo', 'thika'], 'Kestrel Gensets': ['kobo', 'thika'], 'Polar Cooling Co': ['thika'], 'Ampere Charge Co': ['ruiru'] };
const V70_RECORD = /\b(?:F|ACT|WR|INC|REC|CHG|PM)-\d{2,4}\b/g;
/* the kept v7.0 lists of records (each row must carry a Site key to be shown); settings and setup forms are organisation-level */
const UX_RECORD_LISTS = ['assets', 'assets-warranty', 'incidents', 'maintenance', 'maintenance-preventive', 'oprecords', 'globalevidence'];
function uxRowSites(e) {
  const t = uxWords(e), out = new Set();
  Object.entries(V70_KEYS).forEach(([sk, keys]) => { if (keys.some(k => t.includes(k))) out.add(sk); });
  Object.entries(V70_VENDORS).forEach(([v, sks]) => { if (t.startsWith(v) || e.querySelector('td')?.textContent.trim().startsWith(v)) sks.forEach(s => out.add(s)); });
  /* a row that carries no key may name its Site in its Site cell; the name is read only against the Site register (SK) */
  if (!out.size) Object.keys(SK).forEach(sk => { if (new RegExp(`(^|[^A-Za-z])${SK[sk].name}([^A-Za-z]|$)`).test(t)) out.add(sk); });
  return [...out];
}
function uxShell(s) {
  if (!uxInProduct(s)) return;
  const c = document.querySelector('.canvas'); if (!c) return;
  if (!s.loop && !s.opScoped) {
    const op = LS.op, mine = OPS[op].sites, oname = OPS[op].name, poss = uxPoss(oname);
    /* every row gets its Site(s) as data; a row is this operator's only when all its Sites are */
    /* every row gets its Site(s) as data; a row is this operator's only when all its Sites are. On a list of records, a row or note
       that names no Site by key is not shown (default-deny, review r2 H2): it cannot be shown to be this operator's */
    const records = UX_RECORD_LISTS.includes(s.id);
    c.querySelectorAll('tbody tr, ul li, ol li, option, article, p, .notice').forEach(e => { if (e.closest('.ux-drawer, .tabs, .chips, .panel-head, .page-heading, .breadcrumbs')) return; const ss = uxRowSites(e); e.dataset.site = ss.length ? ss.join(' ') : 'all';
      if (ss.length ? !ss.every(x => mine.includes(x)) : records) e.remove(); });
    /* an asset code before its own label says nothing more (review M4); on a Site setup page an id is the form's subject */
    const setup = /^site-(?:create|batch|setup)/.test(s.id), CODE = /^[A-Z]{2,4}(?:-[A-Z]{1,3})?-[A-Z0-9]{1,3}$/;
    c.querySelectorAll('td, b, strong, code').forEach(b => { const t = b.textContent.trim(); if (!CODE.test(t)) return; if (setup) { b.dataset.subjectId = ''; return; }
      const nx = b.nextSibling; if (b.tagName !== 'TD' && nx && nx.nodeType === 3 && /^\s*·\s*/.test(nx.nodeValue)) { nx.nodeValue = nx.nodeValue.replace(/^\s*·\s*/, ''); b.remove(); } });
    /* a v7.0 record id is not this product's id (Findings and Actions read the plan's store) */
    const tw = document.createTreeWalker(c, NodeFilter.SHOW_TEXT), nodes = []; while (tw.nextNode()) nodes.push(tw.currentNode);
    const ID = '\\b(?:F|ACT|WR|INC|REC|CHG|PM)-\\d{2,4}\\b', hasId = new RegExp(ID);
    nodes.forEach(n => { let v = n.nodeValue; if (!hasId.test(v)) return;
      v = v.replace(new RegExp(`\\s*\\([^()]*${ID}[^()]*\\)`, 'g'), '');
      v = v.split(' · ').filter(seg => !hasId.test(seg)).join(' · ');
      v = v.replace(new RegExp(`[^.;]*${ID}[^.;]*[.;]?\\s*`, 'g'), '');
      v = v.replace(/^\s*[·,\/]\s*|\s*[·,\/]\s*$/g, '').replace(/\s*·\s*\/\s*/g, ' ');
      n.nodeValue = v; });
    /* a separator left between an emptied neighbour and its cell's edge goes with it */
    nodes.forEach(n => { if (!n.parentNode || !/^\s*[·\/,]\s*$/.test(n.nodeValue)) return; const empty = x => !x || !String(x.textContent).trim(); if (empty(n.previousSibling) || empty(n.nextSibling)) n.nodeValue = ' '; });
    c.querySelectorAll('td').forEach(td => { const tw2 = document.createTreeWalker(td, NodeFilter.SHOW_TEXT); let last = null; while (tw2.nextNode()) if (tw2.currentNode.nodeValue.trim()) last = tw2.currentNode; if (last) last.nodeValue = last.nodeValue.replace(/\s*[·,]\s*$/, ''); });
    /* count tiles written for the three operators together cannot be read for one; the list under them is the count */
    c.querySelectorAll('.cards, .statusbar').forEach(k => { if ((k.querySelector('.metric') || k.classList.contains('statusbar')) && !k.closest('.ux-drawer') && /\d/.test(k.textContent)) k.remove(); });
    /* a panel heading that claims every Site speaks for this operator's Sites once the list is scoped (r3 L6) */
    if (records) c.querySelectorAll('.panel-head p, .panel-head h2').forEach(h => { if (/across all sites/i.test(h.textContent)) { h.textContent = h.textContent.replace(/across all sites/i, `Across ${poss} Sites`); h.dataset.uxAdded = ''; } });
    /* copy that describes navigation the product no longer offers goes with it (review M4) */
    c.querySelectorAll('p, .panel-head p, .notice').forEach(p => { if (/moves you to its own pages|pages are shown for|in this mock-up/i.test(p.textContent) && !p.querySelector('table')) p.remove(); });
    /* an emptied list never says "None" where the plan's store has rows (review H4): it lists them, from the store */
    const store = uxStoreRows(s, op);
    const firstTb = c.querySelector('tbody');
    c.querySelectorAll('tbody').forEach(tb => { if (!tb.querySelector('tr') && tb !== firstTb && records) { (tb.closest('.panel') || tb.closest('table')).remove(); return; } });
    c.querySelectorAll('.panel').forEach(pn => { if (records && !pn.querySelector('table, ul, ol, .metric, form, input, select, button') && !pn.querySelector(':scope > :not(.panel-head)')?.textContent.trim()) pn.remove(); });
    c.querySelectorAll('tbody').forEach(tb => { if (!tb.querySelector('tr')) { const n = tb.closest('table')?.querySelectorAll('thead th').length || 1; tb.insertAdjacentHTML('beforeend', `<tr class="ux-none" data-site="all" data-ux-added><td colspan="${n}">${store || `None recorded at ${poss} Sites.`}</td></tr>`); } });
    /* the list says which Sites its records cover, from the data */
    const covered = OPS[op].sites.filter(sk => c.querySelector(`[data-site~="${sk}"]`)), rest = mine.filter(sk => !covered.includes(sk));
    if (rest.length) (c.querySelector('.page-heading') || c.querySelector('.breadcrumbs'))?.insertAdjacentHTML('afterend', `<p class="ux-scope-note" data-ux-added>${covered.length ? `These records cover ${uxAnd(covered.map(k => SK[k].name))}.` : 'No record here yet.'} For ${uxAnd(rest.map(k => SK[k].name))}, see ${link('findings', 'Findings')} and ${link('actions', 'the plan’s Actions')}.</p>`);
  }
  /* the navigation never lists a v7.0 screen kept for review only */
  document.querySelectorAll('.tabs a[href^="#/"], .ux-tabmenu a[href^="#/"]').forEach(a => { if (uxIsClassic(uxRouteOf(a.getAttribute('href')))) a.remove(); });
  if (/^decision\/|^site\/|^portfolio\/act-first\/plan$/.test(s.id)) uxCapLists(c);
  setTimeout(() => typeof uxStickyTick === 'function' && uxStickyTick(), 0);
  /* the product never navigates into a v7.0 screen kept for review only */
  c.querySelectorAll('a[href^="#/"]').forEach(a => { if (uxIsClassic(uxRouteOf(a.getAttribute('href')))) { const sp = document.createElement('span'); sp.className = 'ux-unlinked'; sp.innerHTML = a.innerHTML.replace(/\s*→\s*$/, ''); a.replaceWith(sp); } });
}
/* the possessive of a name ("Metro Bus Depots’", "Lakeside Power’s") (review L3) */
/* a list in words: "A", "A and B", "A, B and C" (review r2 L5) */
const uxAnd = a => a.length < 2 ? (a[0] || '') : `${a.slice(0, -1).join(', ')} and ${a[a.length - 1]}`;
const uxPoss = n => /s$/.test(n) ? `${n}’` : `${n}’s`;
/* the store's rows for an emptied v7.0 list: failures and limits as Findings, repairs and upkeep as the plan's Actions */
function uxStoreRows(s, op) {
  const R = s.root;
  if (R === 'Incidents') { const f = uxFindingRows(op).filter(x => x.heading === 'protect'); return f.length ? `Not recorded in this list. Open Findings on failures and limits:<ul class="list">${f.map(x => `<li data-site="${SK[Object.keys(SK).find(k => SK[k].name === x.site)] ? Object.keys(SK).find(k => SK[k].name === x.site) : 'all'}">${x.site}: ${x.text} ${x.d ? link(`decision/${x.d.id}`, 'Open decision →') : ''}</li>`).join('')}</ul>` : ''; }
  if (R === 'Maintenance') { const A = (WF(op).actions || []).filter(a => ['REPAIR', 'SUPPLIER_REMEDY', 'STOPGAP_PLUS_CLAIM'].includes(OPT[a.item]?.kind)); return A.length ? `Not recorded in this list. Repairs in the plan:<ul class="list">${A.map(a => `<li data-site="${OPT[a.item]?._site || 'all'}">${a.action} (${who(op, a.owner)}, due ${fdate(a.due)})</li>`).join('')}</ul>${link('actions', 'See the plan’s Actions →')}` : ''; }
  return '';
}

/* Findings and Actions read the one store the plan uses (UX audit C1.4): HC.findings with their issue words, and the plan's
   Actions (demo_workflow.actions) with creator, owner, due date and release state */
function uxFindingRows(op) {
  const names = OPS[op].sites.map(k => SK[k].name), siteOf = f => String(f.site).replace(/^Room [A-C] · /, '');
  return (HC.findings || []).filter(f => names.includes(siteOf(f))).map(f => {
    const r = ATTN[op].find(r => r[5] === f.id), d = f.decision && decById(f.decision), st = d ? uxDecState(d.id) : null;
    return { f, site: siteOf(f), tone: r ? r[0] : 'info', label: r ? r[1] : 'Linked', text: r ? r[3] : (d ? `${d.q}` : 'No issue text recorded'), heading: f.heading, d, st };
  });
}
function uxCapNote(n, cap, id) { return n > cap ? `<button type="button" class="ux-link ux-showall" data-ux-showall="${id}" aria-expanded="false">Show all ${num(n)}</button>` : ''; }
document.addEventListener('click', e => { const b = e.target.closest('[data-ux-showall]'); if (!b) return; const l = document.getElementById(b.dataset.uxShowall); if (!l) return; l.querySelectorAll('[data-ux-over]').forEach(x => { x.hidden = false; }); b.remove(); });
function uxFindingsScreen() {
  const op = LS.op, R = uxFindingRows(op), cap = 7, id = 'uxfl';
  const rows = R.map((x, i) => `<li class="ux-fl"${i >= cap ? ' data-ux-over hidden' : ''}><span class="ux-fl-st">${uxChip(x.tone, x.label)}</span><span class="ux-fl-site">${x.site}</span><span class="ux-fl-t">${x.text}<small>${LENS[x.heading] ? LENS[x.heading][0] : ''}</small></span><span class="ux-fl-dec">${x.d ? `<span class="status-pill is-${x.st.key === 'released' ? 'approved' : x.st.key === 'approval' ? 'waiting' : 'proposed'}">${x.st.label}</span>${link(`decision/${x.d.id}`, `Open decision<span class="vh">: ${x.d.q}</span> →`)}` : '<span class="muted">No decision yet</span>'}</span></li>`).join('');
  return `<section class="panel" aria-labelledby="uxfl-h"><div class="ux-row-head"><h2 id="uxfl-h" data-count="${R.length}" data-count-of=".ux-flist>li">${num(R.length)} Finding${R.length === 1 ? '' : 's'} at ${uxPoss(OPS[op].name)} Sites</h2><span class="ux-note">October 2026 · each with its decision</span></div>
   ${R.length ? `<ul class="ux-flist" id="${id}">${rows}</ul>${uxCapNote(R.length, cap, id)}` : '<p class="ux-empty" role="status">No Findings at this operator’s Sites.</p>'}</section>`;
}
function uxActionsScreen() {
  const op = LS.op, A = WF(op).actions || [], items = [...new Set(A.map(a => a.item))];
  const groups = items.map(it => { const d = DEC.find(x => x.opts.includes(it)); return `<section class="panel ux-act-g" aria-label="${escapeHtml(String(itemName(op, it)))}"><div class="ux-row-head"><h3>${itemName(op, it)}</h3>${d ? link(`decision/${d.id}`, `Open decision<span class="vh">: ${d.q}</span> →`) : ''}</div>${actionRows(op, A.filter(a => a.item === it))}</section>`; }).join('');
  return `<section aria-labelledby="uxal-h"><div class="ux-row-head"><h2 id="uxal-h" data-count="${A.length}" data-count-of=".action-list li:not(.action-list-head)">${num(A.length)} Action${A.length === 1 ? '' : 's'} under the plan</h2><span class="ux-note">Grouped by plan item · creator, owner, due date and release</span></div>${A.length ? groups : '<p class="ux-empty" role="status">No Actions created yet.</p>'}</section>`;
}
function uxNotFound() { return `<section class="panel ux-empty-page" role="status"><h2>This page does not exist</h2><p>The link may be out of date. ${link('portfolio', 'Go to the Portfolio →')}</p></section>`; }

/* ===== the Site page (owner, 20 Nov: "queue site and plan pages"; guide §2.3 Site row; the long-page standard).
   L1 the Site against target, its gap and its open decisions as a count with money; L2 its queue and the Actions in hand;
   L3 answer-titled sections (what drives the gap as factor rows: issues, what can be done, already in hand; where value leaks;
   how it has moved; service and assets; every factor; limits and warranties); L4 in drawers. One drill-down grammar: a driver
   row opens its drawer in place; leaving takes a named button. The Site tabs leave a slot for "Operations" (pending the owner). ===== */
const SITE_TABS_PENDING = ['Operations']; /* the owner's call (reviewer's proposal): measures and assets for the period, the same on every Site */
/* decisions counted by state, in the words of the one state source (review Site M1); "need a decision" only for the choose state */
function uxStateSplit(ids) { return uxStateCount(ids).replace(/^[^:]*: /, ''); }
function uxStateCount(ids) { ids = [...new Set(ids)]; const k = ids.map(id => uxDecState(id).key), n = s => k.filter(x => x === s).length, parts = [[n('choose') + n('none'), 'waiting for a choice'], [k.filter((x, i) => x === 'approval' && !uxDecState(ids[i]).draft).length, 'awaiting approval'], [k.filter((x, i) => x === 'approval' && uxDecState(ids[i]).draft).length, 'with the plan sent back to draft'], [n('released'), 'under way']].filter(([c]) => c);
  return ids.length ? `${num(ids.length)} decision${ids.length === 1 ? '' : 's'}: ${parts.map(([c, w]) => `${num(c)} ${w}`).join(', ')}` : 'No decision at this Site'; }
/* the Operations measures' answer is its rows: the first measure against its target, or that none is declared (review Site M4) */
function uxOpsAnswer(html) { const h = document.createElement('div'); h.innerHTML = html; const tr = [...h.querySelectorAll('tbody tr')], txt = e => (e?.textContent || '').replace(/\s+/g, ' ').trim();
  if (!tr.length) return 'No operations measure declared'; const c = tr[0].children, name = txt(c[0].querySelector('b') || c[0]), tgt = txt(c[1]), val = [...c[2].childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
  return `${name} ${val}${/not declared/.test(tgt) ? ', no target declared' : ` against a target of ${tgt.replace(/ .*$/, '')}`}${tr.length > 1 ? `; ${num(tr.length - 1)} more measure${tr.length === 2 ? '' : 's'}` : ''}`; }
function uxSiteDrivers(sk) {
  const op = SK[sk].op, M = uxGapModel(op), name = SK[sk].name;
  return M.groups.flatMap(g => g.steps.filter(s => s.st.by[sk] != null).map(s => {
    const node = s.nodes.filter(x => x.sk === sk), v = r2(node.reduce((a, x) => a + x.v, 0));
    const finds = s.finds.filter(f => String(f.site).replace(/^Room [A-C] · /, '') === name);
    const decs = s.decs.filter(dk => decById(dk).site === sk);
    const inHand = decs.filter(dk => ['approval', 'released'].includes(uxDecState(dk).key)), open = decs.filter(dk => ['choose', 'none'].includes(uxDecState(dk).key));
    return { k: g.k, s, v, node, finds, decs, inHand, open, id: `uxsdrv-${sk}-${g.k}-${s.i}` };
  })).sort((a, b) => Math.abs(b.v) - Math.abs(a.v));
}
/* the board's shown effects add to the Site's shown gap (largest remainder; review Site M2) */
function uxSiteDriversShown(sk) { const R = uxSiteDrivers(sk), vr = uxRoundTo(R.map(r => r.v), Math.round(siteM(sk).period.variance)); R.forEach((r, i) => { r.vr = vr[i]; }); return R; }
function uxSiteDriverBody(sk, r) {
  const op = SK[sk].op, issue = f => { const a = ATTN[op].find(x => x[5] === f.id); return a ? a[3] : 'No issue text recorded'; };
  return `<p class="ux-drv-amt"><b>${usdW(r.v, true)}</b> at ${SK[sk].name}, October against target</p>
   <h3 class="ux-drv-h">What is behind it</h3>${r.finds.length ? `<ul class="list">${r.finds.map(f => `<li>${issue(f)}</li>`).join('')}</ul>` : '<p class="muted">No Finding names this driver at this Site yet.</p>'}
   <h3 class="ux-drv-h">What is being done</h3>${r.decs.length ? `<ul class="list ux-drv-decs">${r.decs.map(uxDecLine).join('')}</ul>` : '<p>No decision yet.</p>'}
   <h3 class="ux-drv-h">Evidence</h3>${r.node.length ? `<ul class="list ux-drv-ev">${r.node.map(({ n, v }) => `<li data-site="${sk}" data-effect="${r2(n.eff)}">${n.label}: ${fig(n.evd || `node:${sk}:${n.id}`, usdW(v, true))} ${ec(n.cls)} <small>October’s bridge line; open the figure for its records and rule</small></li>`).join('')}</ul>` : '<p class="muted">Not available yet.</p>'}`;
}
/* the outcome board: one row per driver at this Site, with its issues, what can be done and what is already in hand */
function uxSiteBoard(sk) {
  const R = uxSiteDriversShown(sk), dl = dk => link(`decision/${dk}`, `${uxTitle(decById(dk).q, SK[sk].name)} →`);
  if (!R.length) return { html: '<p class="note">No driver moved this Site’s result in October.</p>', drawers: '', answer: 'No driver moved the result in October', n: 0 };
  const rows = R.map((r, i) => `<tr${i >= 7 ? ' data-ux-over hidden' : ''}><th scope="row">${uxOpener(r.id, `${r.s.lab}<span class="vh">: what is behind it</span>`, 'ux-link ux-board-go')}<small>${LENS[r.k][0]}</small></th><td class="num" data-board-v="${r.vr}">${usdW(r.vr, true)}</td>
    <td>${r.finds.length ? `${num(r.finds.length)} Finding${r.finds.length === 1 ? '' : 's'}` : '<span class="muted">None</span>'}</td>
    <td>${r.open.length ? r.open.map(dl).join('<br>') : '<span class="muted">No decision waiting</span>'}</td>
    <td>${r.inHand.length ? r.inHand.map(dk => `${uxDecState(dk).label}<br>${dl(dk)}`).join('<br>') : '<span class="muted">Nothing yet</span>'}</td></tr>`).join('');
  const top = R.find(r => !r.s.st.residual), resid = R.find(r => r.s.st.residual), nOpen = new Set(R.flatMap(r => r.open)).size;
  return { html: `<div class="table-wrap"><table class="ux-site-board" id="uxsb-${sk}"><thead><tr><th>Driver</th><th>Effect</th><th>Issues</th><th>What can be done</th><th>Already in hand</th></tr></thead><tbody>${rows}</tbody></table></div>${uxCapNote(R.length, 7, `uxsb-${sk}`)}`,
    drawers: R.map(r => uxDrawer(r.id, r.s.lab, uxSiteDriverBody(sk, r))).join(''),
    answer: `${top ? `${top.s.lab} ${usdW(top.vr, true)} is the largest` : 'No measured driver moved the result'}${resid ? `; ${usdW(resid.vr, true)} not attributed yet` : ''}${nOpen ? `; ${num(nOpen)} decision${nOpen === 1 ? '' : 's'} waiting on these drivers` : ''}`, n: R.length };
}
/* the Actions in hand at this Site: the plan's Actions on items chosen here */
function uxSiteActions(sk) {
  const op = SK[sk].op, A = (WF(op).actions || []).filter(a => (OPT[a.item]?._site || (itemOf(op, a.item)?.site || '').split(' · ').pop().toLowerCase()) === sk);
  /* compact rows for the side column: the Action, its owner, due date and release state; the full reason is on the plan */
  const row = a => { const [pill] = actionState(op, a, true); return `<li class="ux-sact"><span class="ux-sact-t">${a.action}</span><small>${who(op, a.owner)}<span class="ux-sact-due">Due ${fdate(a.due)}</span></small>${pill}</li>`; };
  return { n: A.length, html: A.length ? `<ul class="list ux-sacts">${A.map(row).join('')}</ul>${link('actions', 'All the plan’s Actions →')}` : '<p class="note">No Action in hand at this Site yet.</p>' };
}
/* how the Site has moved, from the loaded history (DS1); "not available yet" when there is none */
function uxSiteTrend(sk) {
  const op = SK[sk].op, cost = OPS[op].kind === 'cost', key = cost ? 'cost' : 'contribution', S = uxHistory(op, key, sk), G = uxHistory(op, 'gap', sk);
  if (!Array.isArray(S) || S.length < 2) return { answer: 'Not available yet: no earlier month is loaded', html: '<p class="muted">Not available yet: no earlier month is loaded.</p>' };
  const ch = Math.round(S[S.length - 1].v - S[S.length - 2].v), f = v => usdW(Math.round(v)); /* r1 L5 and the H1 class: whole dollars; cost moves up or down, unsigned */
  return { answer: cost ? `Monthly cost ${ch > 0 ? `up ${usdW(ch)}` : ch < 0 ? `down ${usdW(-ch)}` : 'unchanged'} against ${S[S.length - 2].m}` : `Contribution ${usdW(ch, true)} against ${S[S.length - 2].m}`, html: `<div class="table-wrap"><table><thead><tr><th>Month</th>${S.map(p => `<th>${p.m}</th>`).join('')}</tr></thead><tbody><tr><th scope="row">${cost ? 'Monthly cost' : 'Contribution'}</th>${S.map(p => `<td class="num">${f(p.v)}</td>`).join('')}</tr>${Array.isArray(G) && G.length ? `<tr><th scope="row">Gap to target</th>${G.map(p => `<td class="num">${usdW(p.v, true)}</td>`).join('')}</tr>` : ''}</tbody></table></div><p class="note">From the loaded history; October is the period shown on the page.</p>` };
}
function uxSitePage(sk, P) {
  const op = SK[sk].op, o = OPS[op], t = tree(sk), att = ATTN[op].filter(r => r[2] === sk), nd = uxDecCount(att);
  const waiting = [...new Set(att.map(r => r[4]))].filter(id => ['choose', 'none'].includes(uxDecState(id).key)), B = uxSiteBoard(sk), A = uxSiteActions(sk), T = uxSiteTrend(sk);
  const plain = s => String(s || '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  const chainFull = uxChain(op, sk), chainAns = plain((chainFull.match(/<p>([\s\S]*?)<\/p>/) || [, ''])[1]), chain = chainFull.replace(/<div class="panel-head"><div><h2 [^>]*>Where value leaks<\/h2><p>[\s\S]*?<\/p><\/div><\/div>/, '').replace(/aria-labelledby="uxv-h-[^"]*"/, 'aria-label="Where value leaks"'); /* r1 L6: the heading and answer say it once */
  /* r3 M1 class on the Site page: the answer is the rows its section shows (the measures table) */
  const evN = o.vertical === 'ev', pm = protectOf(op).filter(m => !m.stake && !m.na), pAbove = pm.filter(m => (evN && m.nov ? pnum(m.sites[sk]) + pnum(m.nov[sk]) : pnum(m.sites[sk])) > 0).length; /* the same rule as the table's State column (pstate) */
  const protAns = pm.length ? `${pAbove ? `${num(pAbove)} of ${num(pm.length)} measure${pm.length === 1 ? '' : 's'} above target` : `All ${num(pm.length)} measures at target`} in October${evN ? ' or November to date' : ''}` : 'No service measure declared';
  const sections = [
    ['What is driving the gap', B.answer, `${B.html}`],
    ['Where value leaks', chainAns, chain],
    ['How it has moved', T.answer, T.html],
    ['Service and assets', protAns, P.protect],
    ...(P.ops ? [['Operations measures', uxOpsAnswer(P.ops), P.ops]] : []),
    ['Every money line against target', t.plan != null ? `${t.label}: ${fmtU(t.actual, t.unit)} against ${fmtU(t.plan, t.unit)}` : t.label, P.breakdown],
    ['Limits and warranties', `${P.limits ? `${num(P.limits)} limit${P.limits === 1 ? '' : 's'} to keep` : 'No service limit declared'}; ${P.rights ? `${num(P.rights)} warrant${P.rights === 1 ? 'y or contract' : 'ies or contracts'}` : 'no warranty or contract open'}`, P.limitsHtml]
  ];
  const first = waiting[0], sticky = `<div class="ux-dsticky" role="region" aria-label="This Site" data-ux-sticky><span class="ux-dsticky-t">${SK[sk].name}</span><span class="ux-dsticky-n">${t.plan != null ? `${usdW(siteM(sk).period.variance, true)} <small>against target</small>` : ''}</span><span class="status-pill is-${waiting.length ? 'proposed' : 'approved'}">${waiting.length ? `${num(waiting.length)} waiting for a choice` : `${num(nd)} decision${nd === 1 ? '' : 's'} in hand`}</span>${first ? link(`decision/${first}`, 'Decide', 'button primary') : ''}</div>`;
  return `${sticky}<p class="headline ux-headline" data-ux-sticky-anchor>${P.lead}</p>${uxSiteTiles(sk)}
 <div class="ux-main-aside"><div class="ux-aside"><section class="panel ux-queue-panel" aria-labelledby="uxsq-h"><div class="panel-head"><div><h2 id="uxsq-h">Decisions at this Site <span class="ux-count">${num(nd)}</span></h2><p data-ux-split>${uxStateCount(att.map(r => r[4]))}. One row each, with who decides.</p></div></div>${uxQueue(op, att, '', nd)}</section></div>
 <div class="ux-aside"><section class="panel" aria-labelledby="uxsa-h"><div class="panel-head"><div><h2 id="uxsa-h" data-count="${A.n}" data-count-of=".ux-site-acts .ux-sacts > li">Actions in hand <span class="ux-count">${num(A.n)}</span></h2><p>The plan’s Actions at this Site, with owner, due date and release.</p></div></div><div class="ux-site-acts">${A.html}</div></section></div></div>
 <div class="ux-dsecs">${sections.map(([l, a, b]) => uxSecA(l, a, b)).join('')}</div>${B.drawers}${uxDrawer(`uxhow-site-${sk}`, P.howTitle, P.howHtml, true)}<p class="ux-help-line">${uxOpener(`uxhow-site-${sk}`, P.howTitle, 'ux-link')}</p>`;
}

/* ===== one feedback pattern for every consequential action (UX audit C6; owner, 20 Nov): a confirmation that says what happens and
   who is recorded, then a toast with Undo, then a visible state change. The demonstration keeps the change in this browser tab
   only (sessionStorage); nothing is sent. Used by Approve plan, Send back, and Confirm the choice. ===== */
const UX_MOCK_KEY = 'l4-mock';
function uxMock() { try { return JSON.parse(sessionStorage.getItem(UX_MOCK_KEY) || '{}'); } catch (e) { return {}; } }
function uxMockSet(m) { try { sessionStorage.setItem(UX_MOCK_KEY, JSON.stringify(m)); } catch (e) {} }
/* the plan's state as shown: the data's, unless an action in this demonstration changed it */
function uxPlanState(op) { const S = PSTATE(), m = uxMock().plan?.[op]; return m ? { ...S, state: m.state, by: m.by, at: m.at, reason: m.reason, giveWay: m.giveWay, version: m.version ?? S.version, ids: m.ids } : S; }
const UX_ACTS = {
  /* the dialog follows the case on screen (review r4 M4): a case that differs from the proposal is approved as the next version, with its own items and spend */
  'approve-plan': op => { const S0 = PSTATE(), ex = execOf(op), P = planCase(op), ids = planCaseIds(op), W = waitingSummary(op, ids), def = DEFAULT_CASE(op), ver = def ? S0.version : S0.version + 1, budget = op === 'lakeside' ? LS.budget : OPS[op].t.portfolio_constraints.budget_usd_nov_dec;
    return { title: `Approve version ${num(ver)} of the plan`, primary: 'Approve the plan',
      body: `<dl class="ux-confirm"><div><dt>What happens</dt><dd>${def ? `Version ${num(ver)} becomes` : `This case differs from the proposed version ${num(S0.version)}, so approving it makes version ${num(ver)}, which becomes`} the approved plan for ${periodWords()}. It releases ${num(W.wait)} waiting Action${W.wait === 1 ? '' : 's'} and ${num(W.waitItems.length)} item${W.waitItems.length === 1 ? '' : 's'}, ${usd(W.spend)} of one-off spend${W.later.length ? `. After approval, ${W.later.map(id => `${itemOf(op, id)?.owner || 'its owner'} creates the Action for ${itemProse(op, id)}`).join('; ')}` : ''}.</dd></div><div><dt>The plan</dt><dd><span data-ux-plan-spend>${usdW(P.spend)}</span> of ${usdW(budget)} budget, <span data-ux-plan-items>${num(ids.length)}</span> item${ids.length === 1 ? '' : 's'}</dd></div><div><dt>Recorded under</dt><dd>${who(op, ex)}<br><span class="ux-note">with the date and time of the approval</span></dd></div></dl>`,
      apply: () => ({ plan: { [op]: { state: 'APPROVED', by: ex?.name || '', at: 'now', version: ver, ids } } }), toast: `Version ${num(ver)} approved` }; },
  /* a reason and a trade-off are required and not prefilled (review r4 M3; guide §7.4); the plan returns to Draft (design §2.5; M2) */
  'send-back': op => { const S = uxPlanState(op), ex = execOf(op), ids = planCaseIds(op), val = () => ({ reason: (document.getElementById('ux-sb-reason')?.value || '').trim(), way: document.getElementById('ux-sb-way')?.value || '' });
    return { title: `Send version ${num(S.version)} back`, primary: 'Send it back',
      body: `<dl class="ux-confirm"><div><dt>What happens</dt><dd>The plan returns to draft. Each changed item goes back to its creator with your reason; nothing is released.</dd></div><div><dt><label for="ux-sb-reason">Your reason</label></dt><dd><textarea id="ux-sb-reason" rows="3" class="ux-reason" required placeholder="Say what is wrong with this version"></textarea></dd></div><div><dt><label for="ux-sb-way">What gives way</label></dt><dd><select id="ux-sb-way" class="ux-reason" required><option value="">Choose an item</option>${ids.map(id => `<option value="${id}">${optLabel(id)}</option>`).join('')}</select><span class="ux-note">The trade-off: the item that gives way so the budget or the ${OPS[op].crewWord} fit.</span></dd></div><div><dt>Recorded under</dt><dd>${who(op, ex)}<br><span class="ux-note">with the date and time</span></dd></div></dl><p class="ux-note" data-ux-hint role="status">Give a reason and the item that gives way to send it back.</p>`,
      valid: () => !!(val().reason && val().way),
      apply: () => ({ plan: { [op]: { state: 'DRAFT', by: ex?.name || '', at: 'now', reason: val().reason, giveWay: val().way ? optLabel(val().way) : '' } } }), toast: `Version ${num(S.version)} sent back` }; }
};
function uxActButton(key, label, cls = 'button') { return `<button type="button" class="${cls}" data-ux-act="${key}">${label}</button>`; }
/* the confirmation drawer for an action (built on demand, so every action uses the same one) */
function uxActOpen(key, from) {
  const [name, ...args] = key.split(':'), A = name === 'choose' ? uxChooseAct(...args) : UX_ACTS[name](LS.op);
  document.getElementById('uxact')?.remove();
  document.body.insertAdjacentHTML('beforeend', uxDrawer('uxact', A.title, `${A.body}<div class="ux-confirm-go"><button type="button" class="button primary" data-ux-act-go="${key}">${A.primary}</button><button type="button" class="button" data-ux-close>Cancel</button></div>`));
  uxOpen('uxact', from);
  if (A.valid) { const go = document.querySelector('#uxact [data-ux-act-go]'), hint = document.querySelector('#uxact [data-ux-hint]'), upd = () => { go.disabled = !A.valid(); if (hint) hint.hidden = !go.disabled; }; document.getElementById('uxact').addEventListener('input', upd); document.getElementById('uxact').addEventListener('change', upd); upd(); }
}
function uxActDo(key) {
  const [name, ...args] = key.split(':'), A = name === 'choose' ? uxChooseAct(...args) : UX_ACTS[name](LS.op), before = uxMock();
  if (A.valid && !A.valid()) return; /* a required answer is missing: nothing is recorded */
  const patch = A.apply();
  const next = { ...before, plan: { ...(before.plan || {}), ...(patch.plan || {}) }, chosen: { ...(before.chosen || {}), ...(patch.chosen || {}) } };
  uxMockSet(next); document.getElementById('uxact')?.remove(); document.querySelectorAll('.ux-drawer[data-open="true"]').forEach(d => uxClose(d));
  render(); uxFocusState(); uxToast(`${A.toast}. Shown in this demonstration only.`, () => { uxMockSet(before); render(); uxToast('Undone.'); uxFocusAction(key); });
}
/* focus returns (WCAG 2.4.3; review r4 M7): render() replaces the opener, so after an action focus goes to the new state, after Undo to the restored button */
function uxFocusState() { uxStickyTick(); /* render() rebuilt the bar: let it show again where the page is scrolled */ const t = document.querySelector('.ux-planband [data-plan-state], .ux-dmeta .status-pill') || document.querySelector('.page-heading h1'); if (t) { t.setAttribute('tabindex', '-1'); t.focus(); } }
function uxFocusAction(key) { uxStickyTick(); const [n, id, oid] = key.split(':'), t = [...document.querySelectorAll(n === 'choose' ? `[data-ux-drawer="uxc-${id}-${oid}"]` : `[data-ux-act="${key}"]`)].find(e => e.offsetParent !== null) || document.querySelector('.page-heading h1'); if (t) { if (!/^(BUTTON|A)$/.test(t.tagName)) t.setAttribute('tabindex', '-1'); t.focus(); } }
window.addEventListener('hashchange', () => document.querySelector('.ux-toast')?.remove()); /* a toast belongs to the page it reported on (review r4 L1) */
/* a toast that can undo what it reports (and is never the only record: the state on the page changes too) */
function uxToast(msg, undo) {
  document.querySelector('.toast')?.remove(); const e = document.createElement('div'); e.className = 'toast ux-toast'; e.setAttribute('role', 'status');
  e.innerHTML = `<span>${msg}</span>${undo ? '<button type="button" class="button" data-ux-undo>Undo</button>' : ''}`; document.body.appendChild(e);
  if (undo) e.querySelector('[data-ux-undo]').addEventListener('click', () => { e.remove(); undo(); });
  setTimeout(() => { if (e.isConnected && !e.matches(':hover, :focus-within')) e.remove(); }, 8000);
}
document.addEventListener('click', e => { const a = e.target.closest('[data-ux-act]'); if (a) { e.preventDefault(); uxActOpen(a.dataset.uxAct, a); return; }
  const g = e.target.closest('[data-ux-act-go]'); if (g) { e.preventDefault(); uxActDo(g.dataset.uxActGo); } });
/* the plan page's sections: an answer-titled section from the old (title, body, subtitle) call */
const uxSecAx = (title, body, sub = '') => uxSecA(title, sub || '', body);
/* changes since the proposed version, as a compact difference (the switches can change the items) */
function uxPlanDiff(op, P) {
  const S = uxPlanState(op), v1 = planItemsV1(op), add = P.ids.filter(id => !v1.includes(id)), drop = v1.filter(id => !P.ids.includes(id) && !isProactive(op, id));
  const line = (sign, id) => `<li class="ux-diff-${sign === '+' ? 'add' : 'drop'}"><span aria-hidden="true">${sign}</span> ${optLabel(id)} <small>${SK[OPT[id]._site].name}</small></li>`;
  const ans = add.length || drop.length ? `${add.length ? `${num(add.length)} added` : ''}${add.length && drop.length ? ', ' : ''}${drop.length ? `${num(drop.length)} left out` : ''}, under the case shown` : `No change: this is version ${num(S.version)} as proposed`;
  return uxSecA(`Changes since version ${num(S.version)}`, ans, add.length || drop.length ? `<ul class="list ux-diff">${add.map(id => line('+', id)).join('')}${drop.map(id => line('−', id)).join('')}</ul><p class="note">Approving a case that differs from the proposal makes a new version.</p>` : `<p class="prose">The items shown are version ${num(S.version)}, proposed by the system on ${fdate(S.proposed)}.</p>`);
}
/* the approver's sticky bar: the plan, its spend, its state and Approve / Send back (one feedback pattern) */
function uxPlanSticky(op, P, budget) { return `<div class="ux-dsticky" role="region" aria-label="This plan" data-ux-sticky><span class="ux-dsticky-t">The plan for ${periodWords()}</span><span class="ux-dsticky-n">${usdW(P.spend)} <small>of ${usdW(budget)}</small></span>${uxPlanStateChip(op)}${uxPlanActions(op)}</div>`; }
