/* Renders every screen of index.html in jsdom (no browser needed) for the three demo operators and records the
   user-facing text of each: the product shell and page, with the blue review bar (review tooling) and the
   review-notes drawer removed. Also opens the first evidence drawers on each loop screen. Writes
   tools/rendered-text.json: [{op, id, status, text, drawers:[text]}]. Used by tools/vocab_check.cjs.
   jsdom is resolved from JSDOM_PATH, else from the repository's frontend/node_modules.
   Run: node tools/render_text.cjs   (from the interactive-mockup-vNEXT folder) */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const candidates = [process.env.JSDOM_PATH, path.resolve(root, '../../../../frontend/node_modules/jsdom'), '/opt/assetecon/AssetOpsV1/frontend/node_modules/jsdom'].filter(Boolean);
let JSDOM, VirtualConsole; for (const c of candidates) { try { ({ JSDOM, VirtualConsole } = require(c)); break; } catch (e) {} }
if (!JSDOM) { console.error('render_text: jsdom not found (set JSDOM_PATH)'); process.exit(2); }
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const errors = [];
const ONLY = process.env.ONLY_OPS ? process.env.ONLY_OPS.split(',') : ['lakeside', 'harvest', 'metro'];

let CUR = null;
function boot(op, hash) {
  const vc = new VirtualConsole(); vc.on('jsdomError', e => errors.push({ op, id: CUR, e: String(e.message || e).slice(0, 200) })); vc.on('error', e => errors.push({ op, id: CUR, e: String(e).slice(0, 200) }));
  const dom = new JSDOM(html, { virtualConsole: vc, runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://127.0.0.1:8790/' + (hash ? '#/' + hash : ''),
    beforeParse(w) { try { w.sessionStorage.setItem('l4-op', op); } catch (e) {} w.matchMedia = w.matchMedia || (() => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} })); w.scrollTo = () => {}; w.HTMLElement.prototype.scrollIntoView = () => {}; } });
  return dom;
}
// text nodes joined by a space, so adjacent table cells never run together ("700 L" + "1,180 L")
function words(node) { const w = node.ownerDocument.defaultView, it = node.ownerDocument.createTreeWalker(node, w.NodeFilter.SHOW_TEXT); const a = []; let n; while ((n = it.nextNode())) a.push(n.nodeValue); return a.join(' '); }
function visible(doc) {
  const c = doc.querySelector('#app').cloneNode(true);
  c.querySelectorAll('.reviewbar, script, style, [hidden], .sr-only-tech').forEach(x => x.remove());
  // text plus the accessible names and titles a user meets
  const attrs = [...c.querySelectorAll('[aria-label],[title],[placeholder]')].map(e => [e.getAttribute('aria-label'), e.getAttribute('title'), e.getAttribute('placeholder')].filter(Boolean).join(' ')).join(' | ');
  const opts = [...c.querySelectorAll('option')].map(o => o.textContent).join(' | ');
  return (words(c) + ' || ' + attrs + ' || ' + opts).replace(/\s+/g, ' ');
}
/* prose segments (added for tools/copy_check.cjs): the text of each block-level leaf as the reader meets it, with the
   element's own spacing kept (no space added between inline nodes), so a doubled word or a stray space shows as it renders */
function segments(root) {
  const c = root.cloneNode(true); c.querySelectorAll('.reviewbar, script, style, [hidden], .sr-only-tech, details.tech').forEach(x => x.remove());
  c.querySelectorAll('small, br').forEach(x => x.before(' ¶ ')); /* a line break or a note under a label reads as a new line, not run-on text */
  const seen = new Set();
  for (const e of c.querySelectorAll('p, li, td, th, dd, dt, h1, h2, h3, h4, summary, figcaption, small, label')) { if (e.querySelector('.ux-drawer, select, .vh')) continue; const t = e.textContent.replace(/\s+/g, ' ').trim(); if (t) seen.add(t); }
  return [...seen];
}
const out = [];
const first = boot('lakeside', 'portfolio');
const manifest = first.window.mockupManifest || [];
first.window.close();
for (const op of ONLY) for (const s of manifest) {
  if (op !== 'lakeside' && !s.id.startsWith('portfolio') && s.id !== 'sites' && s.id !== 'globalfinancials') continue;
  CUR = s.id; const dom = boot(op, s.id); const w = dom.window, d = w.document;
  if (!d.querySelector('#app .canvas')) { errors.push({ op, id: s.id, e: 'no canvas' }); w.close(); continue; }
  const chrome = [...d.querySelectorAll('#app .rail, #app .topbar, #app footer, #app .tabs, #app .slim-banner')].map(words).join(' ').replace(/\s+/g, ' ');
  const rec = { op, id: s.id, status: s.layer4_status, loop: !!(s.loop || s.opScoped), text: visible(d), chrome, drawers: [], segments: segments(d.querySelector('#app')) };
  const nums = [...d.querySelectorAll('.ev-num')].slice(0, 4);
  for (const n of nums) { try { n.dispatchEvent(new w.MouseEvent('click', { bubbles: true })); const dr = d.querySelector('#overlay .drawer, .drawer'); if (dr) { const c = dr.cloneNode(true); c.querySelectorAll('details.tech').forEach(x => x.remove()); rec.drawers.push(words(c).replace(/\s+/g, ' ')); rec.segments.push(...segments(dr)); } d.querySelector('#overlay').innerHTML = ''; } catch (e) {} }
  out.push(rec); w.close();
}
fs.writeFileSync(path.join(__dirname, 'rendered-text.json'), JSON.stringify(out));
console.log(`rendered ${out.length} screen renders; script errors ${errors.length}`);
if (errors.length) { console.log(JSON.stringify(errors.slice(0, 10))); process.exitCode = 1; }
