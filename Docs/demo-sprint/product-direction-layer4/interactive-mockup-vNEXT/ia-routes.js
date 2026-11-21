/* ===== IA-1 (spec §2.2, D-IA.15 to D-IA.20): the route, alias and rail registry. One liveness rule (iaLive), applied before
   insertion by iaUnlink (ia-shapes.js) and by the palette. A unit adds its ID to IA_LANDED in its last commit. ===== */
const IA_LANDED = new Set(['IA-1a', 'IA-1b', 'IA-1c', 'IA-2a', 'IA-2b1']);
const IA_SHAPES = ['frame', 'hub', 'list', 'decision', 'plan', 'record', 'asset', 'drawer', 'statement'];
let IA_ROUTE_ACTIVE = false;
/* IA-2b1 (spec-IA-2b §3.3, D-IA.75): the list control to keep in place across the hash change its own listener wrote; null otherwise */
let IA_LIST_KEEP = null;
/* the reviewed plan page's own labels (spec §2.6: the interim reuses them, no new copy) */
const iaLegacy = id => SCREENS.find(x => x.id === id);
const IA_ROUTES = [
  /* IA-2a (spec §5.1.1, D-IA.43): the plan's four tabs; one H1 (the reviewed title), the tab in the document title */
  { id: 'plan', shape: 'plan', object: 'plan', home: 'Plan', unit: 'IA-1a', tab: 'Items', tabGroup: 'Plan',
    title: ctx => iaLegacy('portfolio/act-first/plan').title, subtitle: ctx => iaLegacy('portfolio/act-first/plan').subtitle,
    crumbs: ctx => [['Plan']], render: ctx => shapePlan(ctx, 'items') },
  ...[['plan/left-out', 'Left out', 'left-out'], ['plan/review', 'Review', 'review'], ['plan/history', 'History', 'history']].map(([id, tab, key]) => ({
    id, shape: 'plan', object: 'plan', home: 'Plan', unit: 'IA-2a', tab, tabGroup: 'Plan',
    title: ctx => iaLegacy('portfolio/act-first/plan').title, subtitle: ctx => iaLegacy('portfolio/act-first/plan').subtitle,
    docTitle: ctx => `${tab} · ${iaLegacy('portfolio/act-first/plan').title}`, crumbs: ctx => [['Plan', 'plan'], [tab]], render: ctx => shapePlan(ctx, key) })),
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
    title: ctx => SK[ctx.site].name, subtitle: ctx => iaLegacy(`site/${ctx.site}`).subtitle, crumbs: ctx => [['Sites', 'sites'], [SK[ctx.site].name]], render: ctx => shapeHubSite(ctx) },
  /* IA-1c (spec §4, D-IA.26): the decision shape, every DEC entry of the operator's Sites. The H1 is the question while the decision waits
     for a choice and its subject once chosen (C17, as reviewed); "Decisions" links to the Decisions list once IA-2b1 lands (a crumb to an unlanded route is text, iaFrame); the Site crumb is the way to the Site */
  { id: 'decision/:dec', shape: 'decision', object: 'decision', home: 'Decisions', unit: 'IA-1c', tab: null, tabGroup: null,
    title: ctx => { const d = decById(ctx.params.dec); return iaWaiting(d.id) ? uxDecQuestion(d) : d.q; },
    crumbs: ctx => { const d = decById(ctx.params.dec); return [['Decisions', 'decisions'], [SK[d.site].name, `site/${d.site}`], [d.q]]; }, render: ctx => shapeDecisionPage(ctx) },
  /* IA-2b1 (spec-IA-2b §4, D-IA.63): the four home lists, one shape and one component; H1 and document title are the menu label */
  ...[['decisions', 'decision', 'Decisions'], ['findings', 'finding', 'Findings'], ['actions', 'action', 'Actions'], ['sites', 'site', 'Sites']].map(([key, object, home]) => ({
    id: key, shape: 'list', object, home, unit: 'IA-2b1', tab: null, tabGroup: null, title: ctx => home, crumbs: ctx => [[home]], render: ctx => shapeList(ctx, key) }))
];
/* the hub tab groups (spec §3.1), keyed by route.tabGroup; only landed tabs are drawn, and a group with one landed tab draws none */
const IA_TAB_GROUPS = {
  Portfolio: ctx => [['Overview', 'portfolio'], ['Outcomes', 'portfolio/outcomes'], ['Demand & capacity', 'portfolio/demand-and-capacity']],
  Plan: ctx => [['Items', 'plan'], ['Left out', 'plan/left-out'], ['Review', 'plan/review'], ['History', 'plan/history']],
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
  'settings-policies': 'settings', 'settings-tenant': 'settings/organisation',
  /* IA-2b1 (spec-IA-2b §5, D-IA.64): the old act-first and Findings screens lead to the home lists, with their view as a query */
  'portfolio/act-first': 'decisions', 'findings-cost': 'findings?heading=optimize', 'findings-risks': 'findings?heading=protect', 'findings-opportunities': 'findings?heading=grow'
};
/* the menu (D-IA.1), in its order and with its labels; an item whose unit has not landed is an unavailable root */
const IA_RAIL = [
  { group: 'Operations', label: 'Portfolio', route: 'portfolio', unit: 'IA-1b', icon: 'grid' },
  { group: 'Operations', label: 'Sites', route: 'sites', unit: 'IA-2b1', icon: 'site' },
  { group: 'Operations', label: 'Assets & cover', route: 'assets', unit: 'IA-2c', icon: 'asset' },
  { group: 'Intelligence', label: 'Findings', route: 'findings', unit: 'IA-2b1', icon: 'finding' },
  { group: 'Work', label: 'Decisions', route: 'decisions', unit: 'IA-2b1', icon: 'finding' },
  { group: 'Work', label: 'Plan', route: 'plan', unit: 'IA-1a', icon: 'action' },
  { group: 'Work', label: 'Actions', route: 'actions', unit: 'IA-2b1', icon: 'action' },
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
/* D-IA.78: the one alias splitter. { path, query } for an alias key (a function value is called with its params first), else null */
function iaAliasTarget(path) {
  for (const [k, v] of Object.entries(IA_ALIASES)) { const p = iaPattern(k, path); if (!p) continue;
    const t = typeof v === 'function' ? v(p) : v; if (!t) return null; const i = String(t).indexOf('?');
    return { path: i < 0 ? String(t) : String(t).slice(0, i), query: i < 0 ? '' : String(t).slice(i + 1) }; }
  return null;
}
/* the alias's target path, only when that path is a landed route */
function iaLiveAlias(path) { const t = iaAliasTarget(path); return t && t.path !== 'not-found' && iaLanded(t.path) ? t.path : null; }
function iaDev() { try { return sessionStorage.getItem('l4-dev') === '1'; } catch (e) { return false; } }
/* D-IA.16: a landed route, a live alias, or the Lab under the developer switch; nothing else */
function iaLive(href) {
  const path = iaParse(href).path;
  if (path === 'lab') return iaDev();
  return !!((iaLanded(path) && path !== 'not-found') || iaLiveAlias(path));
}
/* a live alias's canonical address: the value's query, then the href's own parameters not already set (D-IA.78); a list target is
   written through iaListHref's order. An alias without a query keeps the href's query as typed */
function iaCanon(href) {
  const h = String(href).replace(/^#?\/?/, ''), i = h.indexOf('?'), src = i < 0 ? h : h.slice(0, i), own = i < 0 ? '' : h.slice(i + 1);
  if (!iaLiveAlias(src)) return String(href);
  const t = iaAliasTarget(src), m = iaMatch(t.path);
  if (m && m.route.shape === 'list' && typeof IA_LIST_DEFS !== 'undefined' && IA_LIST_DEFS[t.path]) {
    const q = Object.fromEntries(new URLSearchParams(t.query)); for (const [a, b] of new URLSearchParams(own)) if (!(a in q)) q[a] = b;
    return '#/' + iaListHref(t.path, iaCtx(t.path, m.params, q), {});
  }
  if (!t.query) return `#/${t.path}${i < 0 ? '' : h.slice(i)}`;
  const set = new Set([...new URLSearchParams(t.query)].map(([a]) => a)), rest = own.split('&').filter(x => x && !set.has(decodeURIComponent(x.split('=')[0])));
  return `#/${t.path}?${[t.query, ...rest].join('&')}`;
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
    /* IA-2a (D-IA.53): each plan tab is 2 from portfolio (plan 1, the tab strip 2) */
    const plan2 = IA_LANDED.has('IA-2a');
    if (plan2) [['Left out', 'plan/left-out'], ['Review', 'plan/review'], ['History', 'plan/history']].forEach(([t, r]) => out.push({ op, surface: `plan tab: ${t}`, route: r, limit: 2, via: 'any' }));
    OPS[op].sites.forEach(sk => out.push({ op, surface: `${SK[sk].name} Overview`, route: `site/${sk}`, limit: 2, via: 'any' }));
    OPS[op].sites.forEach(sk => { const r = iaLargestAdverse(sk);
      out.push(r ? { op, surface: `${SK[sk].name} largest driver against target (${r.s.lab})`, route: `site/${sk}#drawer=${r.id}`, limit: 3, via: 'any' }
        : { op, surface: `${SK[sk].name} largest driver against target`, route: null, limit: 3, via: 'any', na: 'no driver against target' }); });
    if (!IA_LANDED.has('IA-1c')) continue;
    /* IA-1c (spec §6): every queue decision (1, via the Overview queue), every waiting decision and the proposed plan (2, via the inbox),
       every plan item's decision (2; from IA-2a 3 and reported only, D-IA.53: plan 1, the closed item 2, the decision 3) */
    const q = d => decById(d).q;
    iaQueueCap(uxMergeRows(ATTN[op]).map(m => m.d), 6).shown.forEach(d => out.push({ op, surface: `queue: ${q(d)}`, route: `decision/${d}`, limit: 1, via: 'queue' }));
    iaDecIds(op, { kind: 'all' }).filter(iaWaiting).forEach(d => out.push({ op, surface: `waiting: ${q(d)}`, route: `decision/${d}`, limit: 2, via: 'inbox' }));
    if (uxPlanState(op).state === 'PROPOSED') out.push({ op, surface: 'the proposed plan', route: 'plan', limit: 2, via: 'inbox' });
    [...new Set(planCase(op).ids.map(id => DEC_SEE_ALSO[id] || (decOf(id) || {}).id).filter(Boolean))].forEach(d => out.push(plan2 ? { op, surface: `plan item: ${q(d)}`, route: `decision/${d}`, limit: 3, via: 'any', report: true } : { op, surface: `plan item: ${q(d)}`, route: `decision/${d}`, limit: 2, via: 'any' }));
  }
  return out;
}
/* the context every route renders from */
/* D-IA.40: the Site a route's object belongs to (a Site page's :site, a decision's Site); IA-2 adds its object parameters here */
function iaParamSite(params) { if (!params) return null; if (params.site) return params.site; if (params.dec) { const d = decById(params.dec); return d ? d.site : null; } return null; }
function iaCtx(path, params, query) {
  const q = query || {}, ps = iaParamSite(params), sc = String(q.scope || (ps ? `site:${ps}` : 'all')), /* a Site's page is scoped to that Site */ [kind, id] = sc.includes(':') ? sc.split(':') : [sc, null];
  const sites = OPS[LS.op].sites, ok = kind === 'group' ? sites.some(k => iaVertical(k) === id) : kind === 'site' ? sites.includes(id) : false; /* D-IA.35 L4: a scope that matches no Site of this operator is all */
  return { op: LS.op, scope: ok ? { kind, id } : { kind: 'all', id: null }, site: params && params.site || null, params: params || {}, query: q, path };
}
/* resolveScreen's view of a landed route: the screen object the review bar and the legacy helpers read */
function iaScreen(route, path) {
  const ctx = iaCtx(path, iaPattern(route.id, path), iaParse(location.hash).query);
  return { id: path, ia: route, ctx, title: route.title(ctx), docTitle: route.docTitle ? route.docTitle(ctx) : route.title(ctx), root: route.home || '', section: '', loop: true, opScoped: true, noFigures: !!route.noFigures, book: false, question: '', anchor: '' };
}
/* the palette lists only what is live, at its canonical address (R9) */
/* IA-2b1 (spec-IA-2b §5): from IA-2b1 the index also holds each Finding and each Action at its row's target, then Decisions and Sites */
function iaPaletteFilter(out) {
  const op = LS.op, add = !IA_LANDED.has('IA-2b1') ? [] : [
    ...uxFindingRows(op).map(x => [x.text, `Finding · ${x.site}`, x.d ? `decision/${x.d.id}` : `decision/${x.f.decision}`]),
    ...(WF(op).actions || []).map(a => { const d = iaActionDec(op, a), p = personOf(op, a.owner); return [a.action, `Action · ${p ? p.name : a.owner}`, d ? `decision/${d.id}` : 'plan']; }),
    ['Decisions', 'Go to', 'decisions'], ['Sites', 'Go to', 'sites']];
  return [...out, ...add].filter(([, , id]) => iaLive(id)).map(([l, k, id]) => [l, k, iaCanon(id).replace(/^#\//, '')]);
}

/* D-IA.36: an in-page link (#<id>) scrolls to that element on the page it is on; it is never a route */
/* the sticky decision bar is shown only once the page is scrolled past the recommendation: measure its height now, so a scroll target stops below it (top of the view, wide screens only; on a phone the bar is at the bottom). One measure, used by in-page links and by the tab switch (D-IA.36, D-IA.58) */
function iaStickyH() {
  const sb = document.querySelector('[data-ux-sticky]'); let hh = 0;
  if (sb && innerWidth > 600) { const was = sb.classList.contains('is-on'); sb.classList.add('is-on'); hh = Math.ceil(sb.getBoundingClientRect().bottom); if (!was) sb.classList.remove('is-on'); }
  return hh;
}
function iaInPage(a) {
  const href = a.getAttribute('href') || '';
  if (!href.startsWith('#') || href === '#' || href.startsWith('#/')) return false;
  let id; try { id = decodeURIComponent(href.slice(1)); } catch (e) { return false; }
  const el = document.getElementById(id), app = document.getElementById('app');
  if (!el || !app || !app.contains(el)) return false;
  const hh = iaStickyH();
  document.documentElement.style.setProperty('--ia-sticky-h', `${hh}px`);
  const calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  el.scrollIntoView({ block: 'start', behavior: calm ? 'auto' : 'smooth' });
  if (!el.matches('a[href],button,input,select,textarea,[tabindex]')) el.setAttribute('tabindex', '-1');
  el.focus({ preventScroll: true });
  return true;
}
document.addEventListener('click', e => {
  if (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
  const a = e.target && e.target.closest && e.target.closest('a[href^="#"]');
  if (a && iaInPage(a)) e.preventDefault();
}, true);
/* D-IA.37: the top bar is one row from 761 px up; controls collapse in a fixed order (search to its icon, the inbox label, the avatar) and never truncate */
function iaFitTopbar() {
  const tb = document.querySelector('.ia-frame .topbar'); if (!tb) return;
  if (innerWidth < 761) { tb.dataset.fit = '5'; return; } /* D-IA.41: the phone is the final form, keyed the same way */
  const fits = () => tb.scrollWidth <= tb.clientWidth + 1;
  tb.dataset.fit = '0'; for (let n = 1; n <= 4 && !fits(); n++) tb.dataset.fit = String(n);
  if (!fits()) tb.dataset.fit = '5'; /* 5 is final: two rows, no test */
}
(function () {
  let raf = 0; window.addEventListener('resize', () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => iaFitTopbar()); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => iaFitTopbar());
})();
/* D-IA.55, D-IA.58: a tab switch shows its tab's content. On a hash change between two routes of one tab group, in a frame after render
   (after screens.js's scrollTo(0,0)): when the content's first box starts below the fold (top > innerHeight - 48), the frame scrolls so that
   box sits just under the sticky bar (iaStickyH + var(--s2)); otherwise it stays at 0. Then, if focus is on body, the active tab takes focus.
   First load and deep links are not switches. */
function iaTabSwitch(oldURL, newURL) {
  const path = u => { const h = String(u || '').split('#')[1] || ''; return h.replace(/^\//, '').split('?')[0]; };
  const a = iaMatch(path(oldURL)), b = iaMatch(path(newURL));
  if (!a || !b || !a.route.tabGroup || a.route.tabGroup !== b.route.tabGroup) return;
  requestAnimationFrame(() => {
    const strip = document.querySelector('[data-ia-tabs]'), L2 = document.querySelector('[data-level="L2"]') || document.querySelector('[data-level]');
    if (!strip || !L2) return;
    const box = [L2, ...L2.querySelectorAll('*')].find(e => e.getClientRects().length), y = window.scrollY;
    if (box && box.getBoundingClientRect().top + y > window.innerHeight - 48) {
      const gap = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--s2')) || 8;
      window.scrollTo({ top: Math.max(0, box.getBoundingClientRect().top + y - iaStickyH() - gap), behavior: 'instant' }); }
    if (document.activeElement === document.body || !document.activeElement) { const t = [...strip.querySelectorAll('a.active, .ux-tabmenu summary')].find(e => e.getClientRects().length); if (t) t.focus({ preventScroll: true }); }
  });
}
/* a tab with no L2 (Portfolio Demand & capacity) starts at its first level box */
window.addEventListener('hashchange', e => iaTabSwitch(e.oldURL, e.newURL));
/* IA-2b1 (spec-IA-2b §3.3, D-IA.75): a list's tools write the address. A select applies on change, the search on submit (never the
   form's default). The control's place is kept by iaListRestore, keyed to the address written here */
function iaListWrite(e) {
  const t = e.target, form = t && t.closest && t.closest('form[data-ia-list-tools]'); if (!form) return;
  if (e.type === 'submit') e.preventDefault(); else if (t.tagName !== 'SELECT') return;
  const el = e.type === 'submit' ? form.querySelector('input[name="q"]') : t; if (!el) return;
  const key = form.dataset.iaListTools, P = iaParse(location.hash), h = iaListHref(key, iaCtx(P.path, P.params, P.query), { [el.name]: el.value });
  if ('#/' + h === location.hash) return;
  IA_LIST_KEEP = { hash: '#/' + h, name: el.name, top: el.getBoundingClientRect().top };
  location.hash = '#/' + h;
}
document.addEventListener('change', iaListWrite);
document.addEventListener('submit', iaListWrite);
/* registered after iaTabSwitch's listener, so after the router's render(); scrollTo(0,0): it runs in the router's task, clears the keep on
   every hash change, and applies it only to the address it was written for */
function iaListRestore() {
  const keep = IA_LIST_KEEP; IA_LIST_KEEP = null;
  if (!keep || location.hash !== keep.hash) return;
  const el = document.querySelector(`[data-ia-list-tools] [name="${keep.name}"]`); if (!el) return;
  window.scrollTo({ top: window.scrollY + el.getBoundingClientRect().top - keep.top, behavior: 'instant' });
  el.focus({ preventScroll: true });
}
window.addEventListener('hashchange', iaListRestore);
