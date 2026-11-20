/* Rev 13 (M3): record which manifest strings the screen reads while rendering every route, every evidence drawer and
   the Act-first switches, for the three operators. Writes tools/rendered-manifest-strings.json (the list of manifest paths
   holding a digit-bearing string), which tools/hand_typed_scan.py scans for literal figures.
   Method: a copy of index.html in the OS temp folder wraps MANIFEST in a read-tracking Proxy; nothing in the pack changes.
   An object spread or Object.entries read counts as a read, so the list is a superset of what is shown.
   Path syntax: dotted keys; a list item is named in brackets by its tenant / site / id / driver / measure / batch field,
   else by position.  Run: CHROME=... PW=... node tools/rendered_strings.cjs */
const fs = require('fs'), path = require('path'), os = require('os');
const { chromium } = require(process.env.PW);
const root = path.resolve(__dirname, '..');
let src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const pre = `window.__ACC=new Set();function __TRACK(o,p){if(o===null||typeof o!=='object')return o;return new Proxy(o,{get(t,k,r){const v=Reflect.get(t,k,r);if(typeof k!=='string'||window.__TPL_RENDERING)return v;
let seg;if(Array.isArray(t)&&/^\\d+$/.test(k)){const it=t[+k];const nm=it&&typeof it==='object'?(it.tenant||it.site||it.id||it.driver||it.measure||it.batch||null):null;seg='['+(nm??k)+']';}else seg=(p?'.':'')+k;
const np=p+seg;if(typeof v==='string'){if(/\\d/.test(v))window.__ACC.add(np);return v;}return (v&&typeof v==='object')?__TRACK(v,np):v;}});}
`;
const i = src.indexOf('const MANIFEST = '), j = src.indexOf('\n', i);
src = src.slice(0, i) + pre + src.slice(i, j).replace('const MANIFEST = ', 'const __RAW = ') + '\nconst MANIFEST = __TRACK(__RAW,"");' + src.slice(j);
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'l4-track-')), file = path.join(dir, 'index.html');
fs.writeFileSync(file, src);
const U = 'file://' + file;
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME, args: ['--no-sandbox'] }); const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto(U); await p.waitForFunction(() => window.mockupReady); const ids = await p.evaluate(() => window.mockupManifest.map(s => s.id));
  const acc = new Set(); const grab = async () => (await p.evaluate(() => [...window.__ACC])).forEach(x => acc.add(x));
  for (const op of ['lakeside', 'harvest', 'metro']) for (const id of ids) {
    if (op !== 'lakeside' && !id.startsWith('portfolio') && id !== 'sites' && id !== 'globalfinancials') continue;
    await p.goto('about:blank'); await p.goto(U + '#/' + id); await p.waitForFunction(() => window.mockupReady); await p.selectOption('#op-switch', op); await p.waitForTimeout(40);
    const nb = await p.locator('.ev-num').count(); for (let k = 0; k < Math.min(nb, 80); k++) { try { await p.locator('.ev-num').nth(k).click({ timeout: 1000 }); await p.keyboard.press('Escape'); } catch (e) {} }
    if (id === 'portfolio/act-first/plan') { const sel = '.controls input, .controls select, .controls button'; const n = await p.locator(sel).count(); for (let k = 0; k < n; k++) { try { await p.locator(sel).nth(k).click({ timeout: 800 }); await grab(); } catch (e) {} } }
    await grab();
  }
  await b.close(); fs.rmSync(dir, { recursive: true, force: true });
  const out = [...acc].sort(); fs.writeFileSync(path.join(__dirname, 'rendered-manifest-strings.json'), JSON.stringify(out, null, 0).replace(/","/g, '",\n"'));
  console.log(`rendered manifest strings with digits: ${out.length}; page errors ${errs.length}`);
})();
