/* ===== IA-1 (spec §2.2, D-IA.15 to D-IA.20): the route, alias and rail registry. One liveness rule (iaLive), applied before
   insertion by iaUnlink (ia-shapes.js) and by the palette. A unit adds its ID to IA_LANDED in its last commit. ===== */
const IA_LANDED = new Set(['IA-1a']);
const IA_SHAPES = ['frame', 'hub', 'list', 'decision', 'plan', 'record', 'asset', 'drawer', 'statement'];
let IA_ROUTE_ACTIVE = false;
/* the reviewed plan page's own labels (spec §2.6: the interim reuses them, no new copy) */
const iaLegacy = id => SCREENS.find(x => x.id === id);
const IA_ROUTES = [
  { id: 'plan', shape: 'plan', object: 'plan', home: 'Plan', unit: 'IA-1a', tab: null,
    title: ctx => iaLegacy('portfolio/act-first/plan').title, subtitle: ctx => iaLegacy('portfolio/act-first/plan').subtitle,
    crumbs: ctx => [['Plan']], render: ctx => shapePlanInterim(ctx) },
  { id: 'not-found', shape: 'frame', object: null, home: null, unit: 'IA-1a', tab: null, noFigures: true,
    title: ctx => iaLegacy('not-found').title, crumbs: ctx => [['Page not found']], render: ctx => shapeNotFound(ctx) }
];
/* old route -> new route; a value may be a function of the parameters. Live only once its target is a landed route. */
const iaRecDecision = route => () => { const fid = OBJ[route], d = typeof DEC !== 'undefined' && DEC.find(x => x.finding === fid); return d ? `decision/${d.id}` : null; };
const IA_ALIASES = {
  'portfolio/outcomes-by-site': 'portfolio/outcomes',
  'portfolio/act-first': () => IA_LANDED.has('IA-2b') ? 'decisions' : 'portfolio',
  'portfolio/act-first/plan': 'plan',
  'portfolio/what-changed': 'results',
  'portfolio/scope': 'evidence', globalevidence: 'evidence',
  oprecords: 'evidence/records',
  mini: 'site/kobo', cold: 'site/thika', ev: 'site/ruiru',
  'site/:site/economics': p => `site/${p.site}/financials`,
  financials: 'site/kobo/financials', 'cold-financials': 'site/thika/financials', 'ev-financials': 'site/ruiru/financials',
  recommendation: iaRecDecision('recommendation'), alternatives: iaRecDecision('alternatives'),
  'cold-recommendation': iaRecDecision('cold-recommendation'), 'ev-recommendation': iaRecDecision('ev-recommendation'),
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
/* a pattern against a path; a parameter is a known Site (:site) or decision (:dec) */
function iaPattern(pat, path) {
  const ps = pat.split('/'), xs = path.split('/'); if (ps.length !== xs.length) return null; const params = {};
  for (let i = 0; i < ps.length; i++) {
    if (ps[i] === ':site') { if (!SK[xs[i]]) return null; params.site = xs[i]; }
    else if (ps[i] === ':dec') { if (!(typeof DEC !== 'undefined' && DEC.some(d => d.id === xs[i]))) return null; params.dec = xs[i]; }
    else if (ps[i] !== xs[i]) return null;
  }
  return params;
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
/* the context every route renders from */
function iaCtx(path, params, query) {
  const q = query || {}, sc = String(q.scope || 'all'), [kind, id] = sc.includes(':') ? sc.split(':') : [sc, null];
  return { op: LS.op, scope: kind === 'group' || kind === 'site' ? { kind, id } : { kind: 'all', id: null }, site: params && params.site || null, params: params || {}, query: q, path };
}
/* resolveScreen's view of a landed route: the screen object the review bar and the legacy helpers read */
function iaScreen(route, path) {
  const ctx = iaCtx(path, iaPattern(route.id, path), iaParse(location.hash).query);
  return { id: path, ia: route, ctx, title: route.title(ctx), root: route.home || '', section: '', loop: true, opScoped: true, noFigures: !!route.noFigures, book: false, question: '', anchor: '' };
}
/* the palette lists only what is live, at its canonical address (R9) */
function iaPaletteFilter(out) { return out.filter(([, , id]) => iaLive(id)).map(([l, k, id]) => [l, k, iaCanon(id).replace(/^#\//, '')]); }
