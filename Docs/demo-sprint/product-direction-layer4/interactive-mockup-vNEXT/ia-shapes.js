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
  const item = i => iaItemLanded(i) ? link(i.route, `${icon(i.icon)}${i.label}`, route.home === i.label ? 'active' : '')
    : `<span class="ia-rail-unavailable" aria-label="${escapeHtml(i.label)}, Not available yet" data-rail-unavailable="${escapeHtml(i.label)}">${icon(i.icon)}<span class="ia-rail-text"><span class="ia-rail-label">${i.label}</span><span class="ia-rail-status" data-rail-status="unavailable">Not available yet</span></span></span>`;
  const foot = iaDev() ? `<div class="rail-group ia-rail-foot" data-ia-footer><div class="eyebrow">Workspace</div>${link('lab', `${icon('evidence')}Simulator Lab`)}</div>` : '';
  return `<nav class="rail" aria-label="Main menu"><div class="brand"><span class="brandmark">⌁</span>AssetOps</div>${groups.map(g => `<div class="rail-group"><div class="eyebrow">${g}</div>${IA_RAIL.filter(i => i.group === g).map(item).join('')}</div>`).join('')}${foot}</nav>`;
}
/* tabs: only for a route with a tab, and only its landed tabs (spec §2.3); IA-1b adds the hub tab groups */
const IA_TAB_GROUPS = {};
function iaTabsHtml(route, ctx) {
  const g = route.tab && IA_TAB_GROUPS[route.tabGroup || route.home]; if (!g) return '';
  const tabs = g(ctx).filter(([, id]) => { const m = iaMatch(id); return m && IA_LANDED.has(m.route.unit); });
  return tabs.length ? uxTabs(tabs, ctx.path) : '';
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
    const sp = document.createElement('span'); sp.className = 'ia-unlinked'; sp.innerHTML = a.innerHTML.replace(/\s*→\s*$/, ''); a.replaceWith(sp);
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
