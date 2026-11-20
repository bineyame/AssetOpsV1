/* One shell model (UX audit C1, C3, C4; owner standing brief, RULES §6). For each demo operator, crawl every route the product
   navigates to (rail, tabs, breadcrumbs and page links; never the review bar or the Simulator Lab) and assert on each:
   S1 one period: the top bar shows the period chip "October 2026 · Figures as of …", never an event window;
   S2 one Site name: no long form ("Kobo Mini-grid", "Thika cold room", "Ruiru depot") and no site code (KOBO-001 …) except as
      the subject of a Site setup page (batch upload, setup history, create);
   S3 operator scope: no Site of another operator is named in the page;
   S4 no second-generation wording: no "(earlier view)", "Event window", "shown together" banner, "Confidence: Low" pill;
   S5 no stub page in the navigation ("not built in this mock-up");
   S6 one store: the Findings and Actions lists name no v7.0 record ids (F-104, ACT-048 …), and their count equals the list;
   S7 no link into a screen kept for review only;
   S8 an unknown route says the page does not exist.
   Run: node tools/shell_check.cjs   Plant: SHELL_PLANT=1 (puts each fault on the Portfolio; must fail). */
const { JSDOM } = require('/opt/assetecon/AssetOpsV1/frontend/node_modules/jsdom');
const fs = require('fs'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), PLANT = !!process.env.SHELL_PLANT;
const fails = [], seenAll = {};
const LONG = /Kobo Mini-grid|Thika cold room|Ruiru depot|\b(?:KOBO-001|COLD-THIKA|EV-RUI)\b/;
const OLD = /\(earlier view\)|Event window|shown together|not built in this mock-up/i;
(async () => {
  for (const op of ['lakeside', 'harvest', 'metro']) {
    const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://x/#/portfolio', beforeParse(w) { w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.sessionStorage.setItem('l4-op', op); } });
    const w = dom.window, doc = w.document; await new Promise(r => setTimeout(r, 400));
    const go = async id => { if (w.location.hash === '#/' + id) w.eval('render()'); else w.location.hash = '#/' + id; await new Promise(r => setTimeout(r, 25)); };
    if (PLANT) w.eval(`{const p=SCREENS.find(x=>x.id==='portfolio'),_o=p.render;p.render=()=>_o()+'<p>Kobo Mini-grid · KOBO-001 · Event window 6 Oct · (earlier view) <a href="#/finding">F-104</a></p><p>Thika</p>';uxShell=function(){};}`);
    const other = w.eval(`Object.keys(SK).filter(k=>SK[k].op!==${JSON.stringify(op)}).map(k=>SK[k].name)`);
    const queue = ['portfolio'], seen = new Set(queue);
    while (queue.length) {
      const id = queue.shift(); await go(id);
      const s = w.eval('currentScreen()'); if (!s) { fails.push(`${op} ${id}: no screen`); continue; }
      if (w.eval('LS.op') !== op) { w.eval(`setOp(${JSON.stringify(op)})`); await go(id); }
      const canvas = doc.querySelector('.canvas'), top = doc.querySelector('.topbar');
      if (!canvas || !top) { fails.push(`${op} ${id}: no shell`); continue; }
      const text = (() => { const o = [], tw = doc.createTreeWalker(canvas, w.NodeFilter.SHOW_TEXT); while (tw.nextNode()) o.push(tw.currentNode.nodeValue); return o.join(' '); })(), bad = m => fails.push(`${op} #/${id}: ${m}`);
      const chip = top.querySelector('.period-chip');
      if (!chip || !/^October 2026 · Figures as of/.test(chip.textContent.trim()) || top.querySelector('#topbar-window, .range-picker, [data-range]')) bad('S1 the top bar does not show the one period chip');
      const lm = (top.textContent + (/^site-(?:batch-upload|setup-history|create-)/.test(id) ? canvas.textContent.replace(/\b(?:KOBO-001|COLD-THIKA|EV-RUI)\b/g, '') : canvas.textContent)).match(LONG); /* a setup page's subject is the site id */ if (lm) bad(`S2 long Site name or code "${lm[0]}"`);
      const om = other.find(n => new RegExp(`\\b${n}\\b`).test(text)); if (om) bad(`S3 names another operator's Site "${om}"`);
      const pm = text.match(OLD); if (pm) bad(`S4/S5 second-generation wording "${pm[0]}"`);
      if ([...canvas.querySelectorAll('.badge,.status-pill,.ux-chip,.chip')].some(b => /^Confidence/.test(b.textContent.trim()))) bad('S4 a "Confidence" pill');
      if (s.stub) bad('S5 a stub page is in the navigation');
      if (['findings', 'actions'].includes(id)) {
        const ids = text.match(/\b(?:F|ACT|WR|INC)-\d+\b/); if (ids) bad(`S6 a v7.0 record id "${ids[0]}"`);
        const n = +(canvas.querySelector('[data-count]')?.dataset.count ?? -1), shown = id === 'findings' ? canvas.querySelectorAll('.ux-flist>li').length : canvas.querySelectorAll('.action-list li:not(.action-list-head)').length;
        if (n !== shown) bad(`S6 count ${n} but ${shown} listed`);
      }
      const links = [...doc.querySelectorAll('.rail a[href^="#/"], .tabs a[href^="#/"], .ux-tabmenu a[href^="#/"], .breadcrumbs a[href^="#/"], .canvas a[href^="#/"]')].filter(a => !a.closest('.rail-footer')).map(a => a.getAttribute('href').replace(/^#\//, '').split('?')[0]);
      for (const l of links) { if (w.eval(`uxIsClassic(${JSON.stringify(l)})`)) { bad(`S7 links into a review-only screen "#/${l}"`); continue; } if (!seen.has(l) && l && !/^lab/.test(l)) { seen.add(l); queue.push(l); } }
    }
    seenAll[op] = seen.size;
    await go('no-such-page'); if (!/does not exist/.test(doc.querySelector('.canvas')?.textContent || '')) fails.push(`${op}: S8 an unknown route does not say so`);
    w.close();
  }
  const by = fails.reduce((a, f) => { const k = (f.match(/: (S\d)/) || [])[1] || '?'; a[k] = (a[k] || 0) + 1; return a; }, {});
  console.log(JSON.stringify({ planted: PLANT, routes_crawled: seenAll, fails: fails.length, by_rule: by, first: fails.slice(0, 40) }, null, 1));
  process.exit(fails.length ? 1 : 0);
})();
