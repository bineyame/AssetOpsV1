/* ===== IA-1 (spec §2.2, D-IA.15 to D-IA.20): the route, alias and rail registry. One liveness rule (iaLive), applied before
   insertion by iaUnlink (ia-shapes.js) and by the palette. A unit adds its ID to IA_LANDED in its last commit. ===== */
const IA_LANDED = new Set(['IA-1a', 'IA-1b', 'IA-1c']);
const IA_SHAPES = ['frame', 'hub', 'list', 'decision', 'plan', 'record', 'asset', 'drawer', 'statement'];
let IA_ROUTE_ACTIVE = false;
/* the reviewed plan page's own labels (spec §2.6: the interim reuses them, no new copy) */
const iaLegacy = id => SCREENS.find(x => x.id === id);
const IA_ROUTES = [
  { id: 'plan', shape: 'plan', object: 'plan', home: 'Plan', unit: 'IA-1a', tab: null,
    title: ctx => iaLegacy('portfolio/act-first/plan').title, subtitle: ctx => iaLegacy('portfolio/act-first/plan').subtitle,
    crumbs: ctx => [['Plan']], render: ctx => shapePlanInterim(ctx) },
  { id: 'not-found', shape: 'frame', object: null, home: null, unit: 'IA-1a', tab: null, noFigures: true,
    title: ctx => iaLegacy('not-found').title, crumbs: ctx => [['Page not found']], render: ctx => shapeNotFound(ctx) },
  /* IA-1b (spec §3, D-IA.25): the hub shape. The three Portfolio tabs and every Site's Overview; titles and subtitles are the
     reviewed screens' own */
  { id: 'portfolio', shape: 'hub', object: 'portfolio', home: 'Portfolio', unit: 'IA-1b', tab: 'Overview', tabGroup: 'Portfolio',
    title: ctx => 'Portfolio', subtitle: ctx => iaLegacy('portfolio').subtitle, crumbs: ctx => [['Portfolio']], render: ctx => shapeHubOverview(ctx) },
  { id: 'portfolio/outcomes', shape: 'hub', object: 'portfolio', home: 'Portfolio', unit: 'IA-1b', tab: 'Outcomes', tabGroup: 'Portfolio',
    title: ctx => 'Outcomes', crumbs: ctx => [['Portfolio', 'portfolio'], ['Outcomes']], render: ctx => shapeHubOutcomes(ctx) },
  { id: 'portfolio/demand-and-capacity', shape: 'hub', object: 'portfolio', home: 'Portfolio', unit: 'IA-1b', tab: 'Demand & capacity', tabGroup: 'Portfolio',
    title: ctx => 'Demand & capacity', crumbs: ctx => [['Portfolio', 'portfolio'], ['Demand & capacity']], render: ctx => shapeHubDemand(ctx) },
  { id: 'site/:site', shape: 'hub', object: 'site', home: 'Sites', unit: 'IA-1b', tab: 'Overview', tabGroup: 'Site',
    title: ctx => SK[ctx.site].name, subtitle: ctx => iaLegacy(`site/${ctx.site}`).subtitle, crumbs: ctx => [['Sites'], [SK[ctx.site].name]], render: ctx => shapeHubSite(ctx) },
  /* IA-1c (spec §4, D-IA.26): the decision shape, every DEC entry of the operator's Sites. The H1 is the question while the decision waits
     for a choice and its subject once chosen (C17, as reviewed); "Decisions" is text until IA-2b; the Site crumb is the way to the Site */
  { id: 'decision/:dec', shape: 'decision', object: 'decision', home: 'Decisions', unit: 'IA-1c', tab: null, tabGroup: null,
    title: ctx => { const d = decById(ctx.params.dec); return iaWaiting(d.id) ? uxDecQuestion(d) : d.q; },
    crumbs: ctx => { const d = decById(ctx.params.dec); return [['Decisions'], [SK[d.site].name, `site/${d.site}`], [d.q]]; }, render: ctx => shapeDecisionPage(ctx) }
];
/* the hub tab groups (spec §3.1), keyed by route.tabGroup; only landed tabs are drawn, and a group with one landed tab draws none */
const IA_TAB_GROUPS = {
  Portfolio: ctx => [['Overview', 'portfolio'], ['Outcomes', 'portfolio/outcomes'], ['Demand & capacity', 'portfolio/demand-and-capacity']],
  Site: ctx => [['Overview', `site/${ctx.site}`], ['Operations', `site/${ctx.site}/operations`], ['Performance', `site/${ctx.site}/performance`], ['Financials', `site/${ctx.site}/financials`], ['Evidence', `site/${ctx.site}/evidence`], ['Setup', `site/${ctx.site}/setup`]]
};
/* old route -> new route; a value may be a function of the parameters. Live only once its target is a landed route. An alias key never
   matches a reserved path: an IA_ROUTES pattern, an IA_RAIL route or a tab route (D-IA.28; shape_check item 7). */
const iaFirstOfGroup = g => () => { const k = OPS[LS.op].sites.find(x => iaVertical(x) === g); return k ? `site/${k}` : null; };
const IA_ALIASES = {
  'portfolio/outcomes-by-site': 'portfolio/outcomes',
  'portfolio/act-first/plan': 'plan',
  'portfolio/what-changed': 'results',
  'portfolio/scope': 'evidence', globalevidence: 'evidence',
  oprecords: 'evidence/records',
  mini: iaFirstOfGroup('mini'), cold: iaFirstOfGroup('cold'), ev: iaFirstOfGroup('ev'),
  'site/:site/economics': p => `site/${p.site}/financials`,
  'cold-financials': 'site/thika/financials', 'ev-financials': 'site/ruiru/financials',
  recommendation: 'decision/kobo-generator', alternatives: 'decision/kobo-generator',
  'cold-recommendation': 'decision/thika-backup', 'ev-recommendation': 'decision/ruiru-connector',
  globalfinancials: 'financials',
  'settings-policies': 'settings', 'settings-tenant': 'settings/organisation'
};
/* the menu (D-IA.1), in its order and with its labels; an item whose unit has not landed is an unavailable root */
const IA_RAIL = [
  { group: 'Operations', label: 'Portfolio', route: 'portfolio', unit: 'IA-1b', icon: 'grid' },
  { group: 'Operations', label: 'Sites', route: 'sites', unit: 'IA-2b', icon: 'site' },
  { group: 'Operations', label: 'Assets & cover', route: 'assets', unit: 'IA-2c', icon: 'asset' },
  { group: 'Intelligence', label: 'Findings', route: 'findings', unit: 'IA-2b', icon: 'finding' },
  { group: 'Work', label: 'Decisions', route: 'decisions', unit: 'IA-2b', icon: 'finding' },
  { group: 'Work', label: 'Plan', route: 'plan', unit: 'IA-1a', icon: 'action' },
  { group: 'Work', label: 'Actions', route: 'actions', unit: 'IA-2b', icon: 'action' },
  { group: 'Work', label: 'Incidents', route: 'incidents', unit: 'IA-2c', icon: 'incident' },
  { group: 'Work', label: 'Maintenance', route: 'maintenance', unit: 'IA-2c', icon: 'work' },
  { group: 'Assurance', label: 'Results', route: 'results', unit: 'IA-2d', icon: 'evidence' },
  { group: 'Assurance', label: 'Evidence & records', route: 'evidence', unit: 'IA-2d', icon: 'log' },
  { group: 'Business', label: 'Financials', route: 'financials', unit: 'IA-2e', icon: 'money' },
  { group: 'Admin', label: 'Settings', route: 'settings', unit: 'IA-2e', icon: 'settings' }
];
/* the address: #/route?scope=…&drawer=… (the hash); ?state= stays in location.search */
function iaParse(hash) {
  const h = String(hash || '').replace(/^#?\/?/, ''), i = h.indexOf('?'), path = i < 0 ? h : h.slice(0, i), qs = i < 0 ? '' : h.slice(i + 1);
  const m = iaMatch(path);
  return { path, params: m ? m.params : {}, query: Object.fromEntries(new URLSearchParams(qs)) };
}
/* a pattern against a path; a parameter is one of the operator's Sites (:site) or one of their decisions (:dec) (D-IA.28) */
function iaSiteOk(k) { return !!SK[k] && OPS[LS.op].sites.includes(k); }
function iaDecOk(id) { const d = typeof DEC !== 'undefined' && DEC.find(x => x.id === id); return !!d && iaSiteOk(d.site); }
function iaPattern(pat, path, any = false) {
  const ps = pat.split('/'), xs = path.split('/'); if (ps.length !== xs.length) return null; const params = {};
  for (let i = 0; i < ps.length; i++) {
    if (ps[i] === ':site') { if (!(any ? !!SK[xs[i]] : iaSiteOk(xs[i]))) return null; params.site = xs[i]; }
    else if (ps[i] === ':dec') { if (!(any ? typeof DEC !== 'undefined' && DEC.some(d => d.id === xs[i]) : iaDecOk(xs[i]))) return null; params.dec = xs[i]; }
    else if (ps[i] !== xs[i]) return null;
  }
  return params;
}
/* another operator's Site or decision typed on an IA address (site/<k>, site/<k>/..., decision/<id>): it shows not-found (D-IA.28) */
function iaForeign(path) {
  const [a, b] = String(path).split('/');
  if (a === 'site' && SK[b]) return !iaSiteOk(b);
  if (a === 'decision' && typeof DEC !== 'undefined' && DEC.some(d => d.id === b)) return !iaDecOk(b);
  return false;
}
function iaMatch(path) { for (const route of IA_ROUTES) { const params = iaPattern(route.id, path); if (params) return { route, params }; } return null; }
/* a landed route (never not-found: it is reached only by a typed address) */
function iaLanded(path) { const m = iaMatch(path); return m && IA_LANDED.has(m.route.unit) ? m : null; }
/* the alias's target, only when that target is a landed route */
function iaLiveAlias(path) {
  for (const [k, v] of Object.entries(IA_ALIASES)) { const p = iaPattern(k, path); if (!p) continue;
    const t = typeof v === 'function' ? v(p) : v; return t && iaLanded(t) && t !== 'not-found' ? t : null; }
  return null;
}
function iaDev() { try { return sessionStorage.getItem('l4-dev') === '1'; } catch (e) { return false; } }
/* D-IA.16: a landed route, a live alias, or the Lab under the developer switch; nothing else */
function iaLive(href) {
  const path = iaParse(href).path;
  if (path === 'lab') return iaDev();
  return !!((iaLanded(path) && path !== 'not-found') || iaLiveAlias(path));
}
/* a live alias's canonical address, keeping the hash query */
function iaCanon(href) {
  const h = String(href).replace(/^#?\/?/, ''), i = h.indexOf('?'), t = iaLiveAlias(i < 0 ? h : h.slice(0, i));
  return t ? `#/${t}${i < 0 ? '' : h.slice(i)}` : String(href);
}
function iaStart() { return IA_LANDED.has('IA-1b') ? 'portfolio' : 'plan'; }
/* the empty hash renders iaStart() from IA-1b (D-IA.29) */
function iaLanding() { return IA_LANDED.has('IA-1b') ? iaStart() : null; }
/* G1's surfaces per landed unit (spec §2.5, D-IA.21): { op, surface, route, limit, via }. A Site without a driver against target has no
   driver surface: it is listed with route null and printed n/a. */
function IA_G1_SURFACES() {
  const out = [];
  for (const op of Object.keys(OPS)) {
    if (!IA_LANDED.has('IA-1b')) continue;
    out.push({ op, surface: 'the plan', route: 'plan', limit: 1, via: 'any' });
    OPS[op].sites.forEach(sk => out.push({ op, surface: `${SK[sk].name} Overview`, route: `site/${sk}`, limit: 2, via: 'any' }));
    OPS[op].sites.forEach(sk => { const r = iaLargestAdverse(sk);
      out.push(r ? { op, surface: `${SK[sk].name} largest driver against target (${r.s.lab})`, route: `site/${sk}#drawer=${r.id}`, limit: 3, via: 'any' }
        : { op, surface: `${SK[sk].name} largest driver against target`, route: null, limit: 3, via: 'any', na: 'no driver against target' }); });
    if (!IA_LANDED.has('IA-1c')) continue;
    /* IA-1c (spec §6): every queue decision (1, via the Overview queue), every waiting decision and the proposed plan (2, via the inbox),
       every plan item's decision (2) */
    const q = d => decById(d).q;
    iaQueueCap(uxMergeRows(ATTN[op]).map(m => m.d), 6).shown.forEach(d => out.push({ op, surface: `queue: ${q(d)}`, route: `decision/${d}`, limit: 1, via: 'queue' }));
    iaDecIds(op, { kind: 'all' }).filter(iaWaiting).forEach(d => out.push({ op, surface: `waiting: ${q(d)}`, route: `decision/${d}`, limit: 2, via: 'inbox' }));
    if (uxPlanState(op).state === 'PROPOSED') out.push({ op, surface: 'the proposed plan', route: 'plan', limit: 2, via: 'inbox' });
    [...new Set(planCase(op).ids.map(id => DEC_SEE_ALSO[id] || (decOf(id) || {}).id).filter(Boolean))].forEach(d => out.push({ op, surface: `plan item: ${q(d)}`, route: `decision/${d}`, limit: 2, via: 'any' }));
  }
  return out;
}
/* the context every route renders from */
function iaCtx(path, params, query) {
  const q = query || {}, sc = String(q.scope || (params && params.site ? `site:${params.site}` : 'all')), /* a Site's page is scoped to that Site */ [kind, id] = sc.includes(':') ? sc.split(':') : [sc, null];
  const sites = OPS[LS.op].sites, ok = kind === 'group' ? sites.some(k => iaVertical(k) === id) : kind === 'site' ? sites.includes(id) : false; /* D-IA.35 L4: a scope that matches no Site of this operator is all */
  return { op: LS.op, scope: ok ? { kind, id } : { kind: 'all', id: null }, site: params && params.site || null, params: params || {}, query: q, path };
}
/* resolveScreen's view of a landed route: the screen object the review bar and the legacy helpers read */
function iaScreen(route, path) {
  const ctx = iaCtx(path, iaPattern(route.id, path), iaParse(location.hash).query);
  return { id: path, ia: route, ctx, title: route.title(ctx), root: route.home || '', section: '', loop: true, opScoped: true, noFigures: !!route.noFigures, book: false, question: '', anchor: '' };
}
/* the palette lists only what is live, at its canonical address (R9) */
function iaPaletteFilter(out) { return out.filter(([, , id]) => iaLive(id)).map(([l, k, id]) => [l, k, iaCanon(id).replace(/^#\//, '')]); }
