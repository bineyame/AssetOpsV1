/* IA-1 (spec §2.5, D-IA.16, P7): the shared jsdom boot, go(), the crawl and the href classifier for shape_check,
   click_depth_check and after_render_check. The classifier reads IA_ROUTES, IA_LANDED and IA_ALIASES from the window and
   matches hrefs with its own code; it never calls iaLive, so a fault in iaLive cannot pass its own gate. */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const candidates = [process.env.JSDOM_PATH, path.resolve(root, '../../../../frontend/node_modules/jsdom'), '/opt/assetecon/AssetOpsV1/frontend/node_modules/jsdom'].filter(Boolean);
let JSDOM, VirtualConsole; for (const c of candidates) { try { ({ JSDOM, VirtualConsole } = require(c)); break; } catch (e) {} }
if (!JSDOM) { console.error('ia_crawl: jsdom not found (set JSDOM_PATH)'); process.exit(2); }
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const OPS = ['lakeside', 'harvest', 'metro'];
const sleep = ms => new Promise(r => setTimeout(r, ms));
/* boot one operator at a hash; o.dev turns the developer switch on; o.before runs in beforeParse */
async function boot(op, hash, o = {}) {
  const errors = [], vc = new VirtualConsole(); vc.on('jsdomError', e => errors.push(String(e.message || e).slice(0, 240)));
  const dom = new JSDOM(html, { virtualConsole: vc, runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://x/' + (o.search || '') + '#/' + hash,
    beforeParse(w) { w.sessionStorage.setItem('l4-op', op); if (o.dev) w.sessionStorage.setItem('l4-dev', '1'); w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }); w.scrollTo = () => {}; if (o.before) o.before(w); } });
  const w = dom.window; await sleep(300);
  const go = async h => { if (w.location.hash === '#/' + h) w.eval('render()'); else w.location.hash = '#/' + h; await sleep(30); if (w.eval('LS.op') !== op) { w.eval(`setOp(${JSON.stringify(op)});render()`); await sleep(20); } };
  return { dom, w, doc: w.document, go, errors, opName: w.eval(`OPS[${JSON.stringify(op)}].name`) };
}
/* the classifier: good only if the href's path is a landed IA_ROUTES entry (and not not-found); an alias, a stub, a legacy
   screen, an unlanded route and not-found are bad */
function classifier(w) {
  const R = w.eval('IA_ROUTES.map(r => ({ id: r.id, unit: r.unit }))'), L = new Set(w.eval('[...IA_LANDED]')), A = w.eval('Object.keys(IA_ALIASES)');
  const sites = w.eval('Object.keys(SK)'), decs = w.eval('DEC.map(d => d.id)');
  const match = (pat, p) => { const ps = pat.split('/'), xs = p.split('/'); if (ps.length !== xs.length) return false;
    return ps.every((s, i) => s === ':site' ? sites.includes(xs[i]) : s === ':dec' ? decs.includes(xs[i]) : s === xs[i]); };
  return href => { const h = String(href).replace(/^#\//, ''), q = h.indexOf('?'), p = q < 0 ? h : h.slice(0, q);
    if (A.some(k => match(k, p))) return 'alias';
    if (p === 'not-found') return 'not-found';
    const r = R.find(x => match(x.id, p)); if (!r) return 'legacy or unknown';
    return L.has(r.unit) ? 'good' : `unlanded (${r.unit})`; };
}
/* a route's identity: its path plus its query keys, sorted */
function identity(href) { const h = String(href).replace(/^#\//, ''), q = h.indexOf('?'); if (q < 0) return h; return h.slice(0, q) + '?' + [...new URLSearchParams(h.slice(q + 1)).keys()].sort().join('&'); }
/* every live route of an operator: landed IA_ROUTES with :site over the operator's Sites and :dec over their decisions */
function liveRoutes(w, op) {
  return w.eval(`(() => { const sites = OPS[${JSON.stringify(op)}].sites, decs = DEC.filter(d => sites.includes(d.site)).map(d => d.id), out = [];
    IA_ROUTES.filter(r => IA_LANDED.has(r.unit) && r.id !== 'not-found').forEach(r => { let ids = [r.id];
      if (r.id.includes(':site')) ids = ids.flatMap(x => sites.map(s => x.replace(':site', s)));
      if (r.id.includes(':dec')) ids = ids.flatMap(x => decs.map(d => x.replace(':dec', d)));
      ids.forEach(id => out.push({ id, shape: r.shape })); }); return out; })()`);
}
/* the hrefs a crawl follows: links in #app outside the review bar and the workspace footer */
function hrefsOf(doc) { return [...doc.querySelectorAll('#app a[href^="#/"]')].filter(a => !a.closest('.reviewbar, [data-ia-footer]')).map(a => a.getAttribute('href')); }
module.exports = { boot, classifier, identity, liveRoutes, hrefsOf, OPS, sleep, html };
