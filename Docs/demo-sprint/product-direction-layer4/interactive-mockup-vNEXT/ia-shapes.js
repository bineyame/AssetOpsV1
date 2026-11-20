/* ===== IA-1 (spec §2.3, §2.4, §2.6): the frame, the one render path and the shapes. The markup is built as a string, finished on
   a detached fragment (iaFinish) and inserted once; after insertion only listeners, focus and the sticky bar's layout tick run
   (D-IA.13, D-IA.17). ===== */
const IA_GROUP_WORD = { mini: 'Mini-grids', cold: 'Cold rooms', ev: 'EV depots' };
const iaVertical = sk => SK[sk].type === 'Mini-grid' ? 'mini' : /^Cold room/.test(SK[sk].type) ? 'cold' : 'ev';
/* the scope menu (D-IA.6): all Sites, a group (one per vertical the operator has), the Sites */
function iaScopeEntries(ctx) {
  const op = ctx.op, sites = OPS[op].sites, groups = [...new Set(sites.map(iaVertical))], here = `#/${ctx.path}`;
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
  return tabs.length > 1 ? uxTabs(tabs, ctx.path) : '';
}
function iaFrame(route, ctx, body) {
  const title = route.title(ctx), sub = route.subtitle ? route.subtitle(ctx) : '';
  const crumbs = `<div class="breadcrumbs">${route.crumbs(ctx).map(([t, id]) => id ? link(id, t) : escapeHtml(t)).join('<span>›</span>')}</div>`;
  return `<div class="shell ia-frame" id="ia-root">${iaRailHtml(route)}<main class="workspace"><header class="topbar">${uxScopeSwitchHtml(iaScopeEntries(ctx), iaScopeLabel(ctx))}<div class="right"><button class="searchbox" data-index aria-label="Search Sites, decisions and Findings (Ctrl K)">${icon('search')}Search Sites, decisions and Findings</button>${uxPeriodMenuHtml(ctx.op)}${themeToggle()}<span class="avatar" title="${avatarName()}, illustrative operator executive">${avatarInitial()}</span></div></header><div class="canvas">${crumbs}<div class="page-heading"><div><div class="title-row"><h1>${title}</h1></div>${sub ? `<p>${sub}</p>` : ''}</div></div>${iaTabsHtml(route, ctx)}${body}${footer()}</div></main></div>`;
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
  if (typeof window.__iaInserted === 'function') window.__iaInserted(root);
  iaBind(route);
}
/* after insertion: listeners, focus and the sticky bar's layout tick only */
function iaBind(route) { setTimeout(() => typeof uxStickyTick === 'function' && uxStickyTick(), 0); }

/* ---- shapes ---- */
function shapeNotFound(ctx) { return `<section data-shape="frame">${uxNotFound()}</section>`; }
/* spec §2.6 (D-IA.20): the reviewed plan page as one named interim, its parts placed in levels; it must not grow */
function shapePlanInterim(ctx) {
  const p = planParts(ctx.op);
  return `<section data-shape="plan">${p.sticky}<div data-level="L1">${p.band}</div><div class="layout-main-side"><div><div data-level="L2">${p.l2}</div><div data-level="L3">${p.l3}</div></div><aside class="side-panel" data-level="L3">${p.aside}</aside></div></section>`;
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
const iaMonth = () => MONTHS[+String(MANIFEST.accounting_period).split('-')[1] - 1];
/* the Outcomes table (D-IA.27): pure. rows { key, name, group, hasTarget, resultHtml, gapHtml, gap, driverHtml, waiting }. One row
   per Site in scope, gap ascending (most adverse first), ties in the given order, Sites without a target last; capped at 10 the way
   the Site board caps; grouped (one tbody per group, its word and count) only above 10 Sites in more than one group. */
function iaOutcomeTable(rows, { scope = { kind: 'all' }, cost = false, id = 'ia-outcomes' } = {}) {
  const inScope = rows.filter(r => scope.kind === 'site' ? r.key === scope.id : scope.kind === 'group' ? r.group === scope.id : true);
  const sorted = inScope.map((r, i) => [r, i]).sort(([a, i], [b, j]) => (a.hasTarget !== b.hasTarget ? (a.hasTarget ? -1 : 1) : a.hasTarget ? a.gap - b.gap : 0) || i - j).map(([r]) => r);
  const groups = [...new Set(sorted.map(r => r.group))], grouped = sorted.length > 10 && groups.length > 1, NA = '<span class="ux-kpi-na">Not available yet</span>';
  const word = g => IA_GROUP_WORD[g] || g;
  const row = (r, i) => `<tr data-site="${r.key}"${i >= 10 ? ' data-ux-over hidden' : ''}><th scope="row">${link(`site/${r.key}`, r.name)}</th><td>${word(r.group)}</td><td class="num">${r.hasTarget ? r.resultHtml : NA}</td><td class="num">${r.hasTarget ? r.gapHtml : NA}</td><td>${r.hasTarget ? r.driverHtml : NA}</td><td class="num">${num(r.waiting)}</td></tr>`;
  const head = `<thead><tr><th>Site</th><th>Group</th><th>${cost ? 'Cost per required departure met' : 'Contribution'}</th><th>Gap to target</th><th>Largest driver against target</th><th>Waiting for a choice</th></tr></thead>`;
  if (!grouped) return `<div class="table-wrap"><table class="ia-outcomes" id="${id}">${head}<tbody>${sorted.map(row).join('')}</tbody></table></div>${uxCapNote(sorted.length, 10, id)}`;
  return `<div class="table-wrap"><table class="ia-outcomes ia-outcomes-grouped">${head}${groups.map(g => { const R = sorted.filter(r => r.group === g), gid = `${id}-${g}`;
    return `<tbody id="${gid}" data-group="${g}"><tr class="ia-out-group"><th colspan="6" scope="rowgroup">${word(g)} <span class="ux-count">${num(R.length)}</span></th></tr>${R.map(row).join('')}${R.length > 10 ? `<tr><td colspan="6">${uxCapNote(R.length, 10, gid)}</td></tr>` : ''}</tbody>`; }).join('')}</table></div>`;
}
/* the Outcomes headline (spec §3.3): n counts Sites with a negative gap, m Sites with a target; pure */
function iaOutcomeHeadline(rows, cost, mo) {
  const T = rows.filter(r => r.hasTarget), n = T.filter(r => r.gap < 0).length;
  return n ? `${num(n)} of ${num(T.length)} Sites are ${cost ? 'over' : 'below'} target in ${mo}` : `Every Site is on or ${cost ? 'under' : 'above'} target in ${mo}`;
}
/* one Outcomes row per Site of the operator, each figure through the Site page's own call */
function iaOutcomeRows(op) {
  const cost = OPS[op].kind === 'cost';
  return OPS[op].sites.map(sk => { const s = siteM(sk), t = tree(sk), d = t.plan != null ? iaLargestAdverse(sk) : null;
    const f = v => cost ? fmtU(v, t.unit) : usdW(v);
    return { key: sk, name: SK[sk].name, group: iaVertical(sk), hasTarget: t.plan != null,
      resultHtml: t.plan != null ? `${fig(`node:${sk}:root`, f(t.actual))} against a target of ${f(t.plan)}` : '',
      gapHtml: t.plan != null ? figS('gap', sk, s.period.variance, usdW(s.period.variance, true)) : '', gap: s.period.variance,
      driverHtml: d ? `${d.s.lab} ${usdW(d.vr, true)} <small>${LENS[d.k][0]}</small>` : cost ? 'No driver raises the cost' : 'No driver widens the gap',
      waiting: iaDecIds(op, sk).filter(iaWaiting).length }; });
}
function shapeHubOverview(ctx) {
  const P = uxOverviewParts(ctx.op);
  return shapeHub(ctx, { cls: 'ux-overview', l1: `${P.headline}\n ${P.tiles}`, l2: P.queue('', ''), l3: `${P.bridge}\n ${P.cats}` });
}
function shapeHubOutcomes(ctx) {
  const op = ctx.op, cost = OPS[op].kind === 'cost', rows = iaOutcomeRows(op).filter(r => ctx.scope.kind === 'site' ? r.key === ctx.scope.id : ctx.scope.kind === 'group' ? r.group === ctx.scope.id : true);
  return shapeHub(ctx, { l1: `<p class="headline ux-headline">${iaOutcomeHeadline(rows, cost, iaMonth())}</p>`, l2: iaOutcomeTable(rows, { scope: ctx.scope, cost }), l3: uxInsight(op) });
}
function shapeHubDemand(ctx) { return shapeHub(ctx, { l1: uxChain(ctx.op), l3: opportunityScreen() }); }
function shapeHubSite(ctx) {
  const sk = ctx.site, X = uxSiteParts(sk, siteOverviewP(sk), 3);
  return shapeHub(ctx, { sticky: X.sticky, l1: `${X.lead}${X.tiles}`, l2: X.queue, l3: `${X.secs}${X.help}`, drawers: X.drawers });
}
