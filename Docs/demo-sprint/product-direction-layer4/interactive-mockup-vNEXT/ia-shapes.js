/* ===== IA-1 (spec §2.3, §2.4, §2.6): the frame, the one render path and the shapes. The markup is built as a string, finished on
   a detached fragment (iaFinish) and inserted once; after insertion only listeners, focus and the sticky bar's layout tick run
   (D-IA.13, D-IA.17). ===== */
const IA_GROUP_WORD = { mini: 'Mini-grids', cold: 'Cold rooms', ev: 'EV depots' };
const iaVertical = sk => SK[sk].type === 'Mini-grid' ? 'mini' : /^Cold room/.test(SK[sk].type) ? 'cold' : 'ev';
/* the scope menu (D-IA.6): all Sites, a group (one per vertical the operator has), the Sites */
function iaScopeEntries(ctx) {
  const op = ctx.op, sites = OPS[op].sites, groups = [...new Set(sites.map(iaVertical))], here = `#/${ctx.path}`, m = iaMatch(ctx.path), route = m && m.route;
  /* IA-2b1 (spec-IA-2b §3.3): on a list, every entry keeps the list's facets, sort and search and drops show; a Site entry scopes the list */
  if (route && route.shape === 'list') { const c = { ...ctx, query: { ...ctx.query, show: '' } }, H = sc => '#/' + iaListHref(ctx.path, c, { scope: sc });
    return [['All sites', H('all'), ctx.scope.kind === 'all'], ...groups.map(g => [IA_GROUP_WORD[g], H(`group:${g}`), ctx.scope.kind === 'group' && ctx.scope.id === g]),
      ...sites.map(k => [SK[k].name, H(`site:${k}`), ctx.scope.kind === 'site' && ctx.scope.id === k])]; }
  return [['All sites', `${here}?scope=all`, ctx.scope.kind === 'all'],
    ...groups.map(g => [IA_GROUP_WORD[g], `${here}?scope=group:${g}`, ctx.scope.kind === 'group' && ctx.scope.id === g]),
    ...sites.map(k => [SK[k].name, `#/site/${k}`, ctx.scope.kind === 'site' && ctx.scope.id === k])];
}
function iaScopeLabel(ctx) {
  const s = ctx.scope, n = s.kind === 'group' ? IA_GROUP_WORD[s.id] : s.kind === 'site' && SK[s.id] ? SK[s.id].name : 'All sites';
  return `${OPS[ctx.op].name} · ${n || 'All sites'}`;
}
/* the rail (D-IA.1, D-IA.9); an unlanded item copies the live product's unavailable root (NavRail.tsx, W1-UX-07) */
function iaItemLanded(i) { return IA_LANDED.has(i.unit); }
function iaRailHtml(route) {
  const groups = [...new Set(IA_RAIL.map(i => i.group))];
  const item = i => iaItemLanded(i) ? `<a class="${route.home === i.label ? 'active' : ''}" href="#/${i.route}" title="${escapeHtml(i.label)}">${icon(i.icon)}<span class="ia-rail-link-label">${i.label}</span></a>`
    : `<span class="ia-rail-unavailable" aria-label="${escapeHtml(i.label)}, Not available yet" title="${escapeHtml(i.label)}, Not available yet" data-rail-unavailable="${escapeHtml(i.label)}">${icon(i.icon)}<span class="ia-rail-text"><span class="ia-rail-label">${i.label}</span><span class="ia-rail-status" data-rail-status="unavailable">Not available yet</span></span></span>`;
  const foot = iaDev() ? `<div class="rail-group ia-rail-foot" data-ia-footer><div class="eyebrow">Workspace</div>${link('lab', `${icon('evidence')}Simulator Lab`)}</div>` : '';
  return `<nav class="rail" aria-label="Main menu"><div class="brand"><span class="brandmark">⌁</span>AssetOps</div>${groups.map(g => `<div class="rail-group"><div class="eyebrow">${g}</div>${IA_RAIL.filter(i => i.group === g).map(item).join('')}</div>`).join('')}${foot}</nav>`;
}
/* tabs: only for a route with a tab, and only its landed tabs (spec §2.3); a group with one landed tab draws no row (spec §3.1) */
function iaTabsHtml(route, ctx) {
  const g = route.tab && IA_TAB_GROUPS[route.tabGroup || route.home]; if (!g) return '';
  const tabs = g(ctx).filter(([, id]) => { const m = iaMatch(id); return m && IA_LANDED.has(m.route.unit); });
  return tabs.length > 1 ? `<div data-ia-tabs>${uxTabs(tabs, ctx.path)}</div>` : '';
}
/* a crumb links only when its target is live (D-IA.16); an unlanded home list's crumb is text */
function iaFrame(route, ctx, body) {
  const title = route.title(ctx), sub = route.subtitle ? route.subtitle(ctx) : '';
  const crumbs = `<div class="breadcrumbs">${route.crumbs(ctx).map(([t, id]) => id && iaLive(id) ? link(id, t) : escapeHtml(t)).join('<span>›</span>')}</div>`;
  return `<div class="shell ia-frame" id="ia-root">${iaRailHtml(route)}<main class="workspace"><header class="topbar">${uxScopeSwitchHtml(iaScopeEntries(ctx), iaScopeLabel(ctx))}<div class="right"><button class="searchbox" data-index aria-label="Search Sites, decisions and Findings (Ctrl K)">${icon('search')}<span class="ia-search-t">Search Sites, decisions and Findings</span></button>${iaPeriodHtml(ctx.op)}${IA_LANDED.has('IA-1c') ? iaInboxControl(ctx.op) : ''}${themeToggle()}<span class="avatar" title="${avatarName()}, illustrative operator executive">${avatarInitial()}</span></div></header><div class="canvas"${["decision", "record", "asset"].includes(route.shape) ? ' data-ia-crumbs="keep"' : ''}>${crumbs}<div class="page-heading"><div><div class="title-row"><h1>${title}</h1></div>${sub ? `<p>${sub}</p>` : ''}</div></div>${iaTabsHtml(route, ctx)}${body}${footer()}</div>${IA_LANDED.has('IA-1c') ? iaInboxDrawer(ctx.op) : ''}</main></div>`;
}
/* D-IA.16: every link whose target is not live becomes text (its trailing arrow dropped); a tab to it is removed; a live alias
   gets its target's canonical address. Runs first, on the detached fragment. */
function iaUnlink(root) {
  root.querySelectorAll('a[href^="#/"]').forEach(a => {
    const href = a.getAttribute('href');
    if (iaLive(href)) { const c = iaCanon(href); if (c !== href) a.setAttribute('href', c); return; }
    if (a.closest('.tabs, .ux-tabs, .ux-tabmenu')) { a.remove(); return; }
    const sp = document.createElement('span'); sp.className = 'ia-unlinked'; sp.dataset.iaTo = iaParse(href).path; /* where it will lead once its unit lands */ sp.innerHTML = a.innerHTML.replace(/\s*→\s*$/, ''); a.replaceWith(sp);
  });
}
/* today's finishing passes, in today's order, on the detached fragment */
function iaFinish(root, route) {
  iaUnlink(root);
  uxCapLists(root);
  tagReplay(root);
  uxScopeLine(root, route);
  plainWords(root);
  uxDedupeUnits(root);
  uxFixSigns(root);
}
function iaRender(route, ctx) {
  const t = document.createElement('template'); t.innerHTML = iaFrame(route, ctx, route.render(ctx));
  const frag = document.importNode(t.content, true);
  iaFinish(frag, route);
  const slot = document.getElementById('ia-root'); if (!slot) return; slot.replaceWith(frag);
  const root = document.getElementById('ia-root');
  iaFitTopbar(); /* D-IA.37: measured once inserted, before the after-render guard observes the frame */
  if (typeof window.__iaInserted === 'function') window.__iaInserted(root);
  iaBind(route);
}
/* after insertion: listeners, focus and the sticky bar's layout tick only */
function iaBind(route) { setTimeout(() => typeof uxStickyTick === 'function' && uxStickyTick(), 0); }

/* ---- shapes ---- */
function shapeNotFound(ctx) { return `<section data-shape="frame">${uxNotFound()}</section>`; }

/* ---- IA-2a: the plan shape (spec §5.1.2 to §5.1.4, D-IA.43 to D-IA.47, D-IA.51) ---- */
/* the stepper (§5.1.3): pure steps and the current index; REVISED shows as Proposed; an unknown state throws */
const IA_PLAN_STEPS = ['DRAFT', 'PROPOSED', 'APPROVED', 'CLOSED'];
function iaPlanSteps(state) { const cur = state === 'REVISED' ? 1 : IA_PLAN_STEPS.indexOf(state); if (cur < 0) throw new Error(`plan state ${state} has no step`); return { steps: IA_PLAN_STEPS.map(s => STATE_WORD[s]), cur }; }
function iaPlanStepper(op) { const { steps, cur } = iaPlanSteps(uxPlanState(op).state); return `<ol class="ux-dsteps ia-plan-steps" aria-label="Where this plan is">${steps.map((s, i) => `<li class="${i < cur ? 'is-done' : i === cur ? 'is-current' : ''}"${i === cur ? ' aria-current="step"' : ''}>${s}</li>`).join('')}</ol>`; }
/* one crew tile per month with a stated limit (crewByMonth), '' when there is none */
function iaCrewTiles(op, P) { const o = OPS[op], ms = crewByMonth(op, P); return ms.map(m => uxKpi(`${cap(o.crewWord)} used${ms.length > 1 ? `, ${m.month}` : ''}`, `${num(m.used)} <small>of ${num(m.limit)}</small>`, [], uxMeterBar(m.used, m.limit, `${num(m.used)} of ${num(m.limit)} ${o.crewWord}${ms.length > 1 ? ` in ${m.month}` : ''}`))).join(''); }
function iaPlanBand(op, P, budget) { const B = uxPlanBandParts(op, P, budget); return `<section class="ux-planband" aria-label="The plan at a glance"><div class="heroes ux-kpis">${B.spend}${iaCrewTiles(op, P) || B.crew}${B.value}</div>${B.act}</section>`; }
/* D-IA.51: the case line. The Approve dialog has no case-label function, so the label is the reviewed switches' own words: each
   fieldset's legend and its checked option, from switches(op) */
function iaPlanCaseLabel(op) { const t = document.createElement('template'); t.innerHTML = switches(op); return [...t.content.querySelectorAll('fieldset')].map(f => `${f.querySelector('legend').textContent}: ${((f.querySelector('input[checked]') || {}).parentNode || { textContent: '' }).textContent.trim()}`).join('; '); }
function iaPlanCaseLine(op, here) { return DEFAULT_CASE(op) ? '' : `<p class="ia-plan-case">Showing the case you chose: ${escapeHtml(iaPlanCaseLabel(op))}. <a href="${here ? '#sw-h' : '#/plan'}">Change the case</a></p>`; }
/* D-IA.54: the part of the plan's spend that was released at creation, stated beside the waiting part so the figures add up */
function iaPlanReleased(op) { const ids = planCaseIds(op).filter(id => releaseOf(op, id).at); return ids.length ? `<p class="ia-plan-released" data-qty="plan-spend" data-qty-role="part">Already released when ${ids.length === 1 ? 'its Action was' : 'their Actions were'} created, within the release thresholds: ${ids.map(id => `${itemProse(op, id)} (${usd(releaseOf(op, id).spend)})`).join('; ')}.</p>` : ''; }
function iaPlanHead(op, p, here) { return `${iaPlanStepper(op)}${iaPlanBand(op, p.P, p.budget)}${p.ap.releases}${iaPlanReleased(op)}${p.ap.notice}${iaPlanCaseLine(op, here)}<p class="ia-plan-rules">${uxOpener('ia-plan-thresholds', 'Release thresholds', 'ux-link')}</p>`; }
/* History (§5.1.4): the act log's plan entries newest first, then the proposal and the opening (PSTATE: no act changes them) */
function iaPlanHistory(op) {
  const S = uxPlanState(op), S0 = PSTATE(), L = (uxMock().log || []).filter(e => e.op === op && (e.key === 'approve-plan' || e.key === 'send-back'));
  const rows = [...L.map((e, i) => `<li data-ia-hist="log:${i}">${e.toast} <small>${e.by} · ${hhmm(e.at) || ''}</small></li>`), `<li data-ia-hist="proposed">Version ${num(S0.version)} proposed <small>The system · ${fdate(S0.proposed)}</small></li>`, `<li data-ia-hist="opened">Opened within the executive’s limits <small>The system · ${fdate(S0.opened)}</small></li>`];
  return sec('Versions and approvals', `<ul class="list ia-plan-history">${rows.join('')}</ul><p class="note">Changes made here are shown in this demonstration only.</p>`, `Version ${num(S.version)}, ${STATE_WORD[S.state].toLowerCase()}`);
}
/* the shape (§5.1.2): L1 identical on the four tabs; Items and Left out carry the case switches in the side panel */
function shapePlan(ctx, tab) {
  const op = ctx.op, p = planParts(op), side = tab === 'items' || tab === 'left-out', lv = (n, x) => x ? `<div data-level="${n}">${x}</div>` : '';
  const l1 = `<div data-level="L1">${iaPlanHead(op, p, side)}</div>`, drawers = `<div data-ia-drawers>${uxDrawer('ia-plan-thresholds', 'Release thresholds', p.ap.thrBody)}</div>`;
  if (side) {
    const l2 = tab === 'items' ? p.l2 : uxSecA('Left out of the plan, and why', p.leftAns, p.leftBody, true), l3 = tab === 'items' ? `${p.diff}${p.paths}${p.crew}${p.cases}` : `${p.listed}${p.returned}`;
    return `<section data-shape="plan">${p.sticky}${l1}<div class="layout-main-side"><div>${lv('L2', l2)}${lv('L3', l3)}</div><aside class="side-panel" data-level="L3">${p.switches}</aside></div>${drawers}</section>`;
  }
  return `<section data-shape="plan">${p.sticky}${l1}${lv('L2', tab === 'review' ? whatChangedParts(op).review : iaPlanHistory(op))}${drawers}</section>`;
}

/* ---- IA-1b: levels, the hub shape and its predicates (spec §3, D-IA.22, D-IA.24, D-IA.25, D-IA.27) ---- */
/* the levels: structure only ([data-level] and [data-ia-drawers] are display: contents in ia.css); an empty slot omits its region */
function iaLevels(shape, { cls = '', sticky = '', l1 = '', l2 = '', l3 = '', drawers = '' } = {}) {
  const lv = (n, x) => x ? `<div data-level="${n}">${x}</div>` : '';
  return `<section data-shape="${shape}"${cls ? ` class="${cls}"` : ''}>${sticky}${lv('L1', l1)}${lv('L2', l2)}${lv('L3', l3)}${drawers ? `<div data-ia-drawers>${drawers}</div>` : ''}</section>`;
}
function shapeHub(ctx, slots) { return iaLevels('hub', slots); }
/* the one decision set: ATTN[op]'s decision ids, first appearance first, filtered by scope (a Site key, or { kind, id }) */
function iaDecIds(op, scope) {
  const sc = typeof scope === 'string' ? { kind: 'site', id: scope } : scope || { kind: 'all' };
  const keep = r => sc.kind === 'site' ? r[2] === sc.id : sc.kind === 'group' ? iaVertical(r[2]) === sc.id : true;
  return [...new Set(ATTN[op].filter(keep).map(r => r[4]))];
}
/* the one waiting predicate: a choice is waiting, with or without a recommendation */
function iaWaiting(id) { return ['choose', 'none'].includes(uxDecState(id).key); }
/* the largest driver against target: the bridge's tone rule (a shown effect below zero), the lowest, ties in board order; else null */
function iaLargestAdverse(sk) {
  let best = null; uxSiteDriversShown(sk).forEach(r => { if (!r.s.st.residual && r.vr < 0 && (!best || r.vr < best.vr)) best = r; });
  return best;
}
/* D-IA.34: a capped queue keeps every decision waiting for a choice, then says what it leaves out. ids in reviewed order; pure */
function iaQueueCap(ids, cap) {
  if (cap === Infinity || ids.length <= cap) return { shown: ids.slice(), hidden: [] };
  const rank = [...ids.filter(iaWaiting), ...ids.filter(id => !iaWaiting(id))], keep = new Set(rank.slice(0, cap));
  return { shown: ids.filter(id => keep.has(id)), hidden: ids.filter(id => !keep.has(id)) };
}
function iaCapMore(hidden) {
  if (!hidden.length) return '';
  const inbox = IA_LANDED.has('IA-1c') && hidden.some(iaWaiting) ? ' ' + uxOpener('ia-inbox', 'Open Waiting for you', 'ux-link') : '';
  return `<p class="ux-cap-more" data-ia-more="${hidden.length}">And ${num(hidden.length)} more: ${uxStateSplit(hidden)}.${inbox}</p>`;
}
const iaMonth = () => MONTHS[+String(MANIFEST.accounting_period).split('-')[1] - 1];
/* the Outcomes scope (D-IA.27): the rows of the Sites in scope; the headline counts them (the rows are the Sites list's, IA-2b1 D-IA.64) */
function iaOutcomeScope(rows, scope) { return rows.filter(r => scope.kind === 'site' ? r.key === scope.id : scope.kind === 'group' ? r.group === scope.id : true); }
/* the Outcomes headline (spec §3.3): n counts Sites with a negative gap, m Sites with a target; pure */
function iaOutcomeHeadline(rows, cost, mo) {
  const T = rows.filter(r => r.hasTarget), n = T.filter(r => r.gap < 0).length;
  if (!T.length) return `No Site in this scope has a target in ${mo}`;
  return n ? `${num(n)} of ${num(T.length)} Sites are ${cost ? 'over' : 'below'} target in ${mo}` : `Every Site is on or ${cost ? 'under' : 'above'} target in ${mo}`;
}
/* one Outcomes row per Site of the operator, each figure through the Site page's own call. Text fields only (D-IA.76): the row is a
   link to the Site hub, where each figure keeps its "show how this is worked out" button */
function iaOutcomeRows(op) {
  const cost = OPS[op].kind === 'cost';
  return OPS[op].sites.map(sk => { const s = siteM(sk), t = tree(sk), d = t.plan != null ? iaLargestAdverse(sk) : null;
    const f = v => cost ? fmtU(v, t.unit) : usdW(v);
    return { key: sk, name: SK[sk].name, group: iaVertical(sk), hasTarget: t.plan != null, gap: s.period.variance,
      result: t.plan != null ? `${f(t.actual)} against a target of ${f(t.plan)}` : '', gapText: t.plan != null ? usdW(s.period.variance, true) : '',
      driver: d ? `${d.s.lab} ${usdW(d.vr, true)} <small>${LENS[d.k][0]}</small>` : cost ? 'No driver raises the cost' : 'No driver widens the gap',
      waiting: iaDecIds(op, sk).filter(iaWaiting).length }; });
}
function shapeHubOverview(ctx) {
  const P = uxOverviewParts(ctx.op, true);
  return shapeHub(ctx, { cls: 'ux-overview', l1: `${P.headline}\n ${P.tiles}`, l2: P.queue('', ''), l3: `${P.bridge}\n ${P.cats}` });
}
function shapeHubOutcomes(ctx) {
  const op = ctx.op, cost = OPS[op].kind === 'cost', rows = iaOutcomeScope(iaOutcomeRows(op), ctx.scope);
  return shapeHub(ctx, { l1: `<p class="headline ux-headline">${iaOutcomeHeadline(rows, cost, iaMonth())}</p>`, l2: iaListBody('sites', ctx, { tools: false, tiles: false }), l3: uxInsight(op) });
}
function shapeHubDemand(ctx) { return shapeHub(ctx, { l1: uxChain(ctx.op), l3: opportunityScreen() }); }
function shapeHubSite(ctx) {
  const sk = ctx.site, X = uxSiteParts(sk, siteOverviewP(sk), 3, true);
  return shapeHub(ctx, { sticky: X.sticky, l1: `${X.lead}${X.tiles}`, l2: X.queue, l3: `${X.secs}${X.help}`, drawers: X.drawers });
}

/* ---- IA-1c: the decision shape and the "Waiting for you" inbox (spec §4, D-IA.21, D-IA.24, D-IA.26) ---- */
function shapeDecision(ctx, slots) { return iaLevels('decision', slots); }
/* the reviewed page's slots placed in levels: the sticky first; head and recommendation L1; the option cards L2; the six answer-titled
   sections L3; the dialogs, Evidence and records, The Actions and How this works in [data-ia-drawers] */
function shapeDecisionPage(ctx) {
  const id = ctx.params.dec, S = uxDecisionSlots(id, decisionParts(id));
  return shapeDecision(ctx, { sticky: S.sticky, l1: `${S.head}${S.rec}`, l2: S.cards, l3: S.secs, drawers: S.drawers });
}
/* who decides: the executive's own items are "For you" (the plan while proposed, then every waiting decision the executive chooses);
   every other waiting decision is "In your portfolio". The badge counts "For you" (D-IA.24, OQ-IA.2) */
const iaExecChooses = id => uxChooserRole(decById(id)) === 'OPERATOR_EXECUTIVE';
function iaForYou(op) { return [...(uxPlanState(op).state === 'PROPOSED' ? ['plan'] : []), ...iaDecIds(op, { kind: 'all' }).filter(id => iaWaiting(id) && iaExecChooses(id))]; }
function iaInPortfolio(op) { return iaDecIds(op, { kind: 'all' }).filter(id => iaWaiting(id) && !iaExecChooses(id)); }
/* the control, in the top bar between the period chip and the theme toggle; the badge is absent at 0 */
function iaInboxControl(op) {
  const n = iaForYou(op).length;
  return `<button type="button" class="ia-inbox" data-ia-inbox data-ux-drawer="ia-inbox" aria-haspopup="dialog" aria-controls="ia-inbox">${icon('check')}<span class="ia-inbox-label">Waiting for you</span>${n ? `<span class="ia-badge" data-ia-badge>${num(n)}</span><span class="vh">, ${num(n)} waiting</span>` : ''}</button>`;
}
/* the drawer, rendered closed in the frame after .canvas; it opens in place (its address is IA-2d's) */
function iaInboxDrawer(op) {
  const S = uxPlanState(op), L = (uxMock().log || []).filter(e => e.op === op);
  const row = (href, key, text, small) => `<li><a href="#/${href}" data-ia-row="${key}">${text} <small>${small}</small></a></li>`;
  const item = x => { if (x === 'plan') return row('plan', 'plan', `The plan for ${periodWords()}`, `${STATE_WORD[S.state]}: awaiting approval`);
    const d = decById(x); return row(`decision/${x}`, `decision:${x}`, d.q, `${SK[d.site].name} · Decides: ${who(op, deciderOf(x).p)}`); };
  const logRow = (e, i) => { const [n, id] = String(e.key).split(':'); return row(n === 'choose' ? `decision/${id}` : 'plan', `log:${i}`, e.toast, `${e.by} · ${hhmm(e.at) || ''}`); };
  const list = (rows, empty) => rows.length ? `<ul class="list ia-inbox-rows">${rows.join('')}</ul>` : `<p class="ux-note ia-inbox-empty">${empty}</p>`;
  const sec = (k, title, body) => `<section class="ia-inbox-sec" data-ia-section="${k}" aria-labelledby="ia-inbox-${k}"><h3 id="ia-inbox-${k}">${title}</h3>${body}</section>`;
  const snap = `<p class="ux-note">${snapText(op)}</p>${snapOf(op).pending ? `<p class="ux-note">${pendingText(op)}</p>` : ''}`;
  return uxDrawer('ia-inbox', 'Waiting for you', `${sec('for-you', 'For you', list(iaForYou(op).map(item), 'Nothing is waiting for you'))}${sec('portfolio', 'In your portfolio', list(iaInPortfolio(op).map(item), 'Nothing else is waiting for a choice'))}${sec('since', 'Since you last looked', `${list(L.map(logRow), 'No change recorded in this session')}${snap}`)}`, true);
}

/* D-IA.41: the period chip split so its sentence can be hidden at fit level 4 (text content identical to periodChip) and stated in the period menu */
function iaPeriodChip(op) {
  const S = snapOf(op);
  return `<span class="period-chip" data-snapshot="${S.asOf || S.books}">${icon('clock')}October 2026<span class="ia-period-asof"> · ${snapText(op)}</span></span>${S.pending ? ` <span class="snap-pending" role="status" data-op="${op}">${badge(pendingText(op), 'amber')}</span>` : ''}`;
}
function iaPeriodHtml(op) {
  return uxPeriodMenuHtml(op, iaPeriodChip(op)).replace('<small>current period</small>', `<small>current period · ${snapText(op)}</small>`);
}

/* ---- IA-2b1 unit 3: the list component (spec-IA-2b §3, D-IA.62, D-IA.67, D-IA.70, D-IA.80) ----
   A def (IA_LIST_DEFS[key], unit 4) holds: key, title (tile 1's label and the H1), plural (the tools' aria-label), cols (the column
   words, the first is the title column), items(op) (the one store, read at every render), site(it) (a Site key; none ignores the scope),
   text(it) (the row's rendered text; else the row's own text), keep(it), group(it) with groupWord(g), facets [{ key, label, all,
   options() -> [[value, word]], of(it) }], sorts [{ key, word, cmp }], row(it, ctx, qk) -> { key, href, title, small, cells },
   tiles(m, ctx, qk) -> the tiles after tile 1, more(m, ctx, qk) (the hidden line; moreInline puts it in the "Show all" paragraph), none. */
const IA_LIST_CAP = 10;
const IA_LIST_DEFS = {};
/* a Site key against a scope { kind: all | group | site, id } */
function iaInScope(sk, scope) { const s = scope || { kind: 'all' }; return s.kind === 'site' ? sk === s.id : s.kind === 'group' ? !!SK[sk] && iaVertical(sk) === s.id : true; }
/* the controls grow with the list (D-IA.67): none under 3 in scope, Sort only up to the cap, then facets, sort and search */
function iaListTier(ns) { return ns < 3 ? 0 : ns <= IA_LIST_CAP ? 1 : 2; }
/* a row's text as the search reads it: tags stripped, entities read, lower case, one space */
function iaListText(html) { return String(html == null ? '' : html).replace(/<[^>]*>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim().toLowerCase(); }
function iaListRowText(def, it) { const r = def.row(it, null, ''); return [r.title, r.small, ...(r.cells || [])].filter(x => x != null && x !== '').join(' '); }
/* the model (spec §3.1), pure: scope, tier, facets, search, sort (stable), one cap ranked keep-first and shown in sort order, groups */
function iaListModel(def, items, q, scope) {
  q = q || {};
  const inScope = def.site ? items.filter(it => iaInScope(def.site(it), scope)) : items.slice(), ns = inScope.length, tier = iaListTier(ns);
  let rows = inScope;
  for (const f of def.facets || []) { const v = q[f.key]; if (v == null || v === '') continue;
    if (!f.options().some(([o]) => String(o) === String(v))) continue; rows = rows.filter(it => String(f.of(it)) === String(v)); }
  const words = String(q.q || '').toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length) rows = rows.filter(it => { const t = iaListText(def.text ? def.text(it) : iaListRowText(def, it)); return words.every(x => t.includes(x)); });
  const sort = (def.sorts || []).find(s => s.key === q.sort) || def.sorts[0];
  rows = rows.map((it, i) => [it, i]).sort(([a, i], [b, j]) => sort.cmp(a, b) || i - j).map(([it]) => it);
  const n = rows.length, rank = def.keep ? [...rows.filter(def.keep), ...rows.filter(it => !def.keep(it))] : rows;
  const top = new Set(q.show === 'all' ? rank : rank.slice(0, IA_LIST_CAP));
  let shown = rows.filter(it => top.has(it)), groups = null; const hidden = rows.filter(it => !top.has(it));
  if (def.group) { const gs = [...new Set(rows.map(def.group))];
    if (n > IA_LIST_CAP && gs.length > 1) { groups = gs.map(g => ({ g, n_g: rows.filter(it => def.group(it) === g).length })); shown = gs.flatMap(g => shown.filter(it => def.group(it) === g)); } }
  return { rows, shown, hidden, n, ns, tier, groups, sort: sort.key, inScope };
}
/* the canonical address (pure): #/<key>, then scope, the facets in def order, sort, q, show, each only when not its default; a facet
   change or a search drops show. change overrides ctx.query; change.scope is 'all', 'group:<g>' or 'site:<k>' */
function iaListHref(key, ctx, change) {
  const def = IA_LIST_DEFS[key], c = change || {}, v = { ...(ctx.query || {}), ...c }, p = [];
  if ('q' in c || (def.facets || []).some(f => f.key in c)) delete v.show;
  const s = 'scope' in c ? String(c.scope || 'all') : ctx.scope && ctx.scope.kind !== 'all' ? `${ctx.scope.kind}:${ctx.scope.id}` : 'all';
  if (s !== 'all') p.push(`scope=${s}`);
  (def.facets || []).forEach(f => { const x = v[f.key]; if (x != null && x !== '' && f.options().some(([o]) => String(o) === String(x))) p.push(`${f.key}=${encodeURIComponent(x)}`); });
  if (v.sort && (def.sorts || []).some(o => o.key === v.sort) && v.sort !== def.sorts[0].key) p.push(`sort=${encodeURIComponent(v.sort)}`);
  if (v.q && String(v.q).trim()) p.push(`q=${encodeURIComponent(String(v.q).trim())}`);
  if (v.show === 'all') p.push('show=all');
  return key + (p.length ? '?' + p.join('&') : '');
}
/* a view's figure key: the canonical query without show (spec §3.2) */
function iaListQk(key, ctx) { const h = iaListHref(key, ctx, { show: '' }), i = h.indexOf('?'); return i < 0 ? '' : h.slice(i + 1); }
/* one figure of a key (D-IA.71): counts carry data-qty-kind="count" */
function iaQty(key, role, text, count) { return `<span data-qty="${key}" data-qty-role="${role}"${count ? ' data-qty-kind="count"' : ''}>${text}</span>`; }
/* D-IA.59, D-IA.68: one form per key on a screen. The parts are the shown values as rendered (whole dollars) plus the hidden ones' sum;
   when they add to the rounded total the key is whole dollars, else every figure of the key takes cents */
function iaListCents(shown, hidden) { const tot = [...shown, ...hidden].reduce((a, x) => a + x, 0), r = shown.reduce((a, x) => a + Math.round(x), 0) + Math.round(hidden.reduce((a, x) => a + x, 0)); return r !== Math.round(tot); }
/* the tiles (spec §3.2, §4): tile 1 is the list's count (n, the rows after filters and before the cap), then the def's own, at most 4 */
function iaListTiles(def, m, ctx) {
  const n = m.n;
  const qk = iaListQk(def.key, ctx), t1 = uxKpi(def.title, iaQty(`${def.key}:n:${qk}`, 'total', num(n), true));
  return [t1, ...(def.tiles ? def.tiles(m, ctx, qk) : [])].filter(Boolean).slice(0, 4).join('');
}
/* the view states no drawn control shows (D-IA.70), then "Clear filters" at 2 or more set */
function iaListChips(def, m, ctx, drawn) {
  const key = def.key, q = ctx.query || {}, chip = (word, href, out) => `<span class="ia-chip">${word} · <a class="ux-link" href="#/${href}">${out}</a></span>`, out = [];
  if (ctx.scope && ctx.scope.kind !== 'all') out.push(chip(ctx.scope.kind === 'group' ? IA_GROUP_WORD[ctx.scope.id] : escapeHtml(SK[ctx.scope.id].name), iaListHref(key, ctx, { scope: 'all' }), 'All sites'));
  const set = (def.facets || []).filter(f => q[f.key] != null && q[f.key] !== '' && f.options().some(([o]) => String(o) === String(q[f.key])));
  set.forEach(f => { if (!drawn.includes(f.key)) out.push(chip(f.options().find(([o]) => String(o) === String(q[f.key]))[1], iaListHref(key, ctx, { [f.key]: '' }), f.all)); });
  const qq = String(q.q || '').trim();
  if (qq && m.tier < 2) out.push(chip(`Matching “${escapeHtml(qq)}”`, iaListHref(key, ctx, { q: '' }), 'Clear search'));
  if (set.length + (qq ? 1 : 0) >= 2) out.push(`<a class="ux-link" href="#/${iaListHref(key, { ...ctx, query: {} }, {})}">Clear filters</a>`);
  return out.length ? `<p class="ia-list-chips" aria-label="In this view">${out.join(' ')}</p>` : '';
}
/* the tools by tier (D-IA.67): tier 1 Sort only; tier 2 each facet with at least 2 options present in scope, Sort, Search */
function iaListTools(def, m, ctx, drawn) {
  if (!m.tier) return '';
  const q = ctx.query || {}, opt = (v, w, cur) => `<option value="${escapeHtml(v)}"${String(cur) === String(v) ? ' selected' : ''}>${w}</option>`, plural = def.plural || def.title;
  const facets = drawn.map(k => { const f = def.facets.find(x => x.key === k), os = f.options(), cur = os.some(([o]) => String(o) === String(q[k])) ? q[k] : '';
    return `<label>${f.label} <select name="${k}">${opt('', 'All', cur)}${os.map(([v, w]) => opt(v, w, cur)).join('')}</select></label>`; }).join('');
  const sort = `<label>Sort <select name="sort">${def.sorts.map(s => opt(s.key, s.word, m.sort)).join('')}</select></label>`;
  const search = m.tier === 2 ? `<label>Search <input type="search" name="q" value="${escapeHtml(String(q.q || '').trim())}"></label><button type="submit" class="button">Search</button>` : '';
  return `<form class="ia-list-tools" data-ia-list-tools="${def.key}" role="search" aria-label="${m.tier === 2 ? 'Filter and sort' : 'Sort'} ${plural}">${m.tier === 2 ? facets : ''}${sort}${search}</form>`;
}
/* the list's L2 (spec §3.2): chips, tools, the table (or the empty state) and the More line. opts.tools false: no chips and no tools
   (the Outcomes fold, D-IA.64) */
function iaListBody(key, ctx, opts = {}, model) {
  const def = IA_LIST_DEFS[key], m = model || iaListModel(def, def.items(ctx.op), ctx.query, ctx.scope), qk = iaListQk(key, ctx), tools = opts.tools !== false;
  const present = f => new Set(m.inScope.map(it => String(f.of(it))).filter(v => f.options().some(([o]) => String(o) === v))).size;
  const drawn = m.tier === 2 ? (def.facets || []).filter(f => present(f) >= 2).map(f => f.key) : [];
  const head = tools ? `${iaListChips(def, m, ctx, drawn)}${iaListTools(def, m, ctx, drawn)}` : '';
  if (!m.ns) return `${head}<p class="ux-empty" role="status">${def.none}</p>`;
  if (!m.n) return `${head}<p class="ux-empty" role="status">Nothing matches these filters. <a class="ux-link" href="#/${iaListHref(key, { ...ctx, query: {} }, {})}">Clear filters</a></p>`;
  const cols = def.cols, row = it => { const r = def.row(it, ctx, qk);
    return `<tr data-row="${escapeHtml(r.key)}"><th scope="row"><a class="ia-row-go" href="#/${r.href}">${r.title}</a>${r.small ? ` <small>${r.small}</small>` : ''}</th>${(r.cells || []).map((c, i) => `<td data-label="${cols[i + 1]}">${c}</td>`).join('')}</tr>`; };
  const thead = `<thead><tr>${cols.map(c => `<th scope="col">${c}</th>`).join('')}</tr></thead>`, word = g => (def.groupWord ? def.groupWord(g) : IA_GROUP_WORD[g]) || g;
  const body = m.groups ? m.groups.map(({ g, n_g }) => `<tbody data-group="${g}"><tr class="ia-list-group"><th colspan="${cols.length}" scope="rowgroup">${word(g)} ${`<span class="ux-count" data-qty="${key}:n:${qk}" data-qty-role="part" data-qty-kind="count">${num(n_g)}</span>`}</th></tr>${m.shown.filter(it => def.group(it) === g).map(row).join('')}</tbody>`).join('')
    : `<tbody>${m.shown.map(row).join('')}</tbody>`;
  const pre = def.more ? def.more(m, ctx, qk) || '' : '';
  const all = `<a class="ux-link" href="#/${iaListHref(key, ctx, { show: 'all' })}" data-qty="${key}:n:${qk}" data-qty-role="total" data-qty-kind="count">Show all ${num(m.n)}</a>`;
  const more = m.hidden.length ? (def.moreInline ? `<p class="ux-more">${pre ? pre + ' ' : ''}${all}</p>` : `${pre}<p class="ux-more">${all}</p>`) : def.moreInline ? '' : pre;
  return `${head}<div class="table-wrap"><table class="ia-list ux-stack" id="ia-list-${key}">${thead}${body}</table></div>${more}`;
}
/* the list shape (spec §3.2): count tiles in L1; chips, tools, rows and More in L2 */
function shapeList(ctx, key) {
  const def = IA_LIST_DEFS[key], m = iaListModel(def, def.items(ctx.op), ctx.query, ctx.scope);
  return `<section data-shape="list" data-ia-list="${key}"><div data-level="L1"><div class="heroes ux-kpis">${iaListTiles(def, m, ctx)}</div></div><div data-level="L2">${iaListBody(key, ctx, {}, m)}</div></section>`;
}

/* ---- IA-2b1 unit 4: the three classifiers (D-IA.77) and the four lists (spec-IA-2b §4, D-IA.63). Every option, word and figure is
   read at render from the one source the hubs and the plan read (D-IA.74); items(op) is not cached ---- */
const IA_DEC_STATE_WORD = { waiting: 'Waiting for a choice', approval: 'Awaiting approval', draft: 'With the plan sent back to draft', underway: 'Under way' };
function iaDecStateKey(id) { const s = uxDecState(id); return ['choose', 'none'].includes(s.key) ? 'waiting' : s.key === 'approval' ? (s.draft ? 'draft' : 'approval') : 'underway'; }
/* actionState's rule on the same helpers: left out of the case, else released as shown, else waiting */
function iaActionStateKey(op, a) { return !planCaseIds(op).includes(a.item) ? 'returned' : releaseShown(op, a.item).at ? 'released' : 'waiting'; }
function iaFindingSite(op, x) { return OPS[op].sites.find(k => SK[k].name === x.site) || null; }
const iaPill = (key, label) => `<span class="status-pill is-${key === 'released' ? 'approved' : key === 'approval' ? 'waiting' : 'proposed'}">${label}</span>`;
const IA_NA = '<span class="ux-kpi-na">Not available yet</span>';
/* a decision's earliest due date over its issues (the queue's rule) */
const iaDecDue = id => ATTN[LS.op].filter(r => r[4] === id).map(r => uxDueIso(id, r[3])).filter(Boolean).sort()[0] || '';
const iaByDue = (a, b) => (!a) - (!b) || (a < b ? -1 : a > b ? 1 : 0);
const iaCountOf = (rows, pred) => rows.filter(pred).length;
/* an Action's Site and its one target: the decision whose options hold its item, else the plan */
const iaActionSite = (op, a) => OPT[a.item]?._site || (itemOf(op, a.item)?.site || '').split(' · ').pop().toLowerCase();
const iaActionDec = (op, a) => DEC.filter(d => OPS[op].sites.includes(d.site)).find(d => (d.opts || []).includes(a.item));
/* the Sites gap key's form on this view (spec §3.4): one model per context */
const IA_SITES_CENTS = new WeakMap();
function iaSitesCents(ctx) {
  if (!ctx) return false; if (IA_SITES_CENTS.has(ctx)) return IA_SITES_CENTS.get(ctx);
  const def = IA_LIST_DEFS.sites, m = iaListModel(def, def.items(ctx.op), ctx.query, ctx.scope), g = r => r.filter(x => x.hasTarget).map(x => x.gap);
  const c = iaListCents(g(m.shown), g(m.hidden)); IA_SITES_CENTS.set(ctx, c); return c;
}
const iaGapW = (v, cents) => cents ? usd2s(v) : usdW(v, true);
const iaCost = () => OPS[LS.op].kind === 'cost';
Object.assign(IA_LIST_DEFS, {
  decisions: { key: 'decisions', title: 'Decisions', plural: 'decisions', cols: ['Decision', 'Site', 'State', 'At stake', 'Due', 'Who decides'],
    items: op => iaDecIds(op, { kind: 'all' }), site: id => decById(id).site, keep: iaWaiting,
    facets: [{ key: 'state', label: 'State', all: 'All states', options: () => Object.entries(IA_DEC_STATE_WORD), of: iaDecStateKey },
      { key: 'due', label: 'Due', all: 'Any due date', options: () => Object.entries(UX_URG), of: id => uxUrgency(iaDecDue(id)) }],
    sorts: [{ key: 'priority', word: 'Priority', cmp: () => 0 }, { key: 'due', word: 'Due date', cmp: (a, b) => iaByDue(iaDecDue(a), iaDecDue(b)) }],
    row: id => { const d = decById(id), op = SK[d.site].op, due = iaDecDue(id), st = uxDecState(id), issues = ATTN[op].filter(r => r[4] === id).map(r => r[1]);
      return { key: id, href: `decision/${id}`, title: uxTitle(d.q, SK[d.site].name), small: [...new Set(issues)].join(' · '),
        cells: [escapeHtml(SK[d.site].name), iaPill(st.key, st.label), uxStake(id), due ? fdate(due) : UX_URG.none, who(op, deciderOf(id).p)] }; },
    tiles: (m, ctx, qk) => [uxKpi('Waiting for a choice', iaQty(`decisions:waiting:${qk}`, 'total', num(iaCountOf(m.rows, iaWaiting)), true))],
    more: m => iaCapMore(m.hidden), none: 'No decisions in this scope.' },
  findings: { key: 'findings', title: 'Findings', plural: 'Findings', cols: ['Finding', 'Site', 'Heading', 'Its decision'],
    items: op => uxFindingRows(op), site: x => iaFindingSite(LS.op, x),
    facets: [{ key: 'heading', label: 'Heading', all: 'All headings', options: () => { const hs = new Set(uxFindingRows(LS.op).map(x => x.heading)); return Object.keys(LENS).filter(k => hs.has(k)).map(k => [k, LENS[k][0]]); }, of: x => x.heading }],
    sorts: [{ key: 'priority', word: 'Priority', cmp: () => 0 }, { key: 'site', word: 'Site', cmp: (a, b) => a.site.localeCompare(b.site) }],
    row: x => ({ key: x.f.id, href: `decision/${x.d ? x.d.id : x.f.decision}`, title: x.text, small: '',
      cells: [escapeHtml(x.site), LENS[x.heading] ? LENS[x.heading][0] : '', x.st ? iaPill(x.st.key, x.st.label) : IA_NA] }),
    tiles: (m, ctx, qk) => [uxKpi('Decision waiting for a choice', iaQty(`findings:waiting:${qk}`, 'total', num(iaCountOf(m.rows, x => x.d && iaWaiting(x.d.id))), true))],
    none: 'No Findings in this scope.' },
  actions: { key: 'actions', title: 'Actions', plural: 'Actions', cols: ['Action', 'Owner', 'Due', 'State'],
    /* one row per Action; its key is {item}-{i}, i 1-based within its item's Actions in store order */
    items: op => { const n = {}; return (WF(op).actions || []).map(a => { n[a.item] = (n[a.item] || 0) + 1; return { op, a, key: `${a.item}-${n[a.item]}` }; }); },
    site: x => iaActionSite(x.op, x.a),
    facets: [{ key: 'state', label: 'State', all: 'All states', options: () => [['released', RELEASE_WORD.RELEASED], ['waiting', RELEASE_WORD.WAITING], ['returned', RELEASE_WORD.RETURNED]], of: x => iaActionStateKey(x.op, x.a) },
      { key: 'version', label: 'Plan version', all: 'All versions', options: () => { const v = uxPlanState(LS.op).version; return [[String(v), `Version ${num(v)}`]]; },
        of: x => { const S = uxPlanState(x.op), ids = S.state === 'APPROVED' ? planApprovedIds(x.op) : planItemsV1(x.op); return ids.includes(x.a.item) ? String(S.version) : null; } }],
    sorts: [{ key: 'due', word: 'Due date', cmp: (a, b) => iaByDue(a.a.due || '', b.a.due || '') },
      { key: 'item', word: 'Plan item', cmp: (a, b) => { const v = planItemsV1(a.op), i = v.indexOf(a.a.item), j = v.indexOf(b.a.item); return (i < 0) - (j < 0) || i - j; } }],
    row: x => { const { op, a } = x, d = iaActionDec(op, a), [pill] = actionState(op, a, planCaseIds(op).includes(a.item));
      return { key: x.key, href: d ? `decision/${d.id}` : 'plan', title: a.action, small: itemShort(op, a.item),
        cells: [who(op, a.owner), a.due ? `${fdate(a.due)}<small>${dueWords(a.due)}</small>` : UX_URG.none, pill] }; },
    tiles: (m, ctx, qk) => { const k = s => iaCountOf(m.rows, x => iaActionStateKey(x.op, x.a) === s), ret = k('returned'), p = (l, v) => uxKpi(l, iaQty(`actions:n:${qk}`, 'part', num(v), true));
      return [p(RELEASE_WORD.RELEASED, k('released')), p(RELEASE_WORD.WAITING, k('waiting')), ret > 0 ? p(RELEASE_WORD.RETURNED, ret) : '']; },
    none: 'No Actions in this scope.' },
  sites: { key: 'sites', title: 'Sites', plural: 'Sites',
    get cols() { return ['Site', 'Group', iaCost() ? 'Cost per required departure met' : 'Contribution', 'Gap to target', 'Largest driver against target', 'Waiting for a choice']; },
    items: op => iaOutcomeRows(op), site: r => r.key, group: r => r.group, groupWord: g => IA_GROUP_WORD[g],
    facets: [{ key: 'target', label: 'Target', get all() { return iaCost() ? 'Over and under target' : 'Above and below target'; },
      options: () => iaCost() ? [['below', 'Over target'], ['on', 'On or under target']] : [['below', 'Below target'], ['on', 'On or above target']],
      of: r => r.hasTarget ? (r.gap < 0 ? 'below' : 'on') : null }],
    /* D-IA.27's order: gap ascending (most adverse first), Sites without a target last */
    sorts: [{ key: 'gap', word: 'Gap to target', cmp: (a, b) => (a.hasTarget !== b.hasTarget ? (a.hasTarget ? -1 : 1) : a.hasTarget ? a.gap - b.gap : 0) },
      { key: 'name', word: 'Name', cmp: (a, b) => a.name.localeCompare(b.name) }],
    row: (r, ctx, qk) => ({ key: r.key, href: `site/${r.key}`, title: escapeHtml(r.name), small: '',
      cells: [IA_GROUP_WORD[r.group] || r.group, r.hasTarget ? r.result : IA_NA,
        r.hasTarget ? `<span${figA('gap', r.key, r.gap)} data-qty="sites:gap:${qk}" data-qty-role="part">${iaSitesCents(ctx) ? usd2s(r.gap) : r.gapText}</span>` : IA_NA,
        r.hasTarget ? r.driver : IA_NA, num(r.waiting)] }),
    tiles: (m, ctx, qk) => { const c = iaSitesCents(ctx), T = r => r.filter(x => x.hasTarget), sh = T(m.shown), hd = T(m.hidden), k = m.rows.length - T(m.rows).length;
      const tot = c ? [...sh, ...hd].reduce((a, x) => a + x.gap, 0) : sh.reduce((a, x) => a + Math.round(x.gap), 0) + Math.round(hd.reduce((a, x) => a + x.gap, 0));
      return [uxKpi(iaCost() ? 'Over target' : 'Below target', iaQty(`sites:below:${qk}`, 'total', num(iaCountOf(m.rows, r => r.hasTarget && r.gap < 0)), true)),
        uxKpi('Gap to target', iaQty(`sites:gap:${qk}`, 'total', iaGapW(tot, c)), [k > 0 ? `${num(k)} Sites without a target are not in this figure` : ''])]; },
    more: (m, ctx, qk) => { if (!m.hidden.length) return ''; const hd = m.hidden.filter(x => x.hasTarget).reduce((a, x) => a + x.gap, 0);
      return `Not shown: ${num(m.hidden.length)} Sites, gap to target <span data-qty="sites:gap:${qk}" data-qty-role="part">${iaGapW(iaSitesCents(ctx) ? hd : Math.round(hd), iaSitesCents(ctx))}</span>.`; },
    moreInline: true, none: 'No Sites in this scope.' }
});
