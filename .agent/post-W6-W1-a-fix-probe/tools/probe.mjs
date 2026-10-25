// SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA (post-W6 W1-a fix round M1; Architect W3 closeout ruling 1 method).
// Capture-only: per width and variant, load the real mounted page, screenshot+measure the UNMODIFIED page, then in the
// same browser session replace/clone DOM rows (never persisted), assert every intended field changed, measure the
// closed panels.   node probe.mjs <out-dir> <variants.json>   variants: [{name,url,variant}]
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { session } from "./cdp.mjs";
const [OUT, VARS] = process.argv.slice(2);
const variants = JSON.parse(readFileSync(VARS, "utf8"));
mkdirSync(OUT, { recursive: true });
const COMMON = `
const base = "Synthetic layout probe text that wraps across several lines in this narrow panel and keeps going ";
const L = (n) => base.repeat(4).slice(0, n);
const panelOf = (t) => [...document.querySelectorAll("section.panel")].find((p) => (p.querySelector("h2")?.textContent ?? "").trim().startsWith(t));
const inClosed = (n, root) => { for (let e = n; e && e !== root; e = e.parentElement) { const d = e.parentElement; if (d && d.tagName === "DETAILS" && !d.open && e.tagName !== "SUMMARY") return true; } return false; };
const measure = (title, clones) => { const p = panelOf(title); const r = p.getBoundingClientRect();
  const clipped = [...p.querySelectorAll("*")].filter((e) => { if (inClosed(e, p) || !e.firstChild) return false; const s = getComputedStyle(e);
    return ((s.overflowX === "hidden" || s.overflowX === "clip" || s.textOverflow === "ellipsis") && e.scrollWidth > e.clientWidth + 1) || ((s.overflowY === "hidden" || s.overflowY === "clip") && e.scrollHeight > e.clientHeight + 2); }).map((e) => e.tagName + "." + String(e.className).slice(0, 30));
  const innerScrollX = [...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowX === "auto" || s.overflowX === "scroll") && e.clientWidth > 0 && e.scrollWidth > e.clientWidth + 1; }).map((e) => String(e.className).slice(0, 30) + ":" + e.scrollWidth + "/" + e.clientWidth);
  const vs = p.querySelector("[data-history-versions-scroll]"); const cue = p.querySelector("[data-history-scroll-cue]");
  const versionScroll = vs ? { clientH: vs.clientHeight, scrollH: vs.scrollHeight, overflowY: getComputedStyle(vs).overflowY, maxH: getComputedStyle(vs).maxHeight, cueHidden: cue ? cue.hidden : null, focusable: vs.tabIndex === 0 } : null;
  return { title, versionScroll, panelH: Math.round(r.height), rowHs: clones.map((c) => Math.round(c.getBoundingClientRect().height)), clipped, innerScrollX, docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth }; };
const allPanels = () => [...document.querySelectorAll("section.panel")].map((p) => ({ t: (p.querySelector("h2")?.textContent ?? "").trim(), h: Math.round(p.getBoundingClientRect().height) }));
`;
const BODIES = {
  baseline: `(() => ({ panels: allPanels(), docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth }))()`,
  "rel-real5": `(() => { const p = panelOf("Where to look next"); const ul = p.querySelector("[data-attention-item=related] ul.site-finding__inline"); const tmpl = ul.querySelector("li").cloneNode(true);
    const labels = ["Earlier Finding this repeats", "Later Finding that repeats this", "Finding this was split from", "Part split from this Finding", "Finding joined into this one"];
    ul.replaceChildren(); const cl = []; labels.forEach((lab) => { const c = tmpl.cloneNode(true); c.querySelector("a").textContent = lab + " →"; ul.appendChild(c); cl.push(c); });
    const verified = cl.length === 5 && cl.every((c, i) => c.textContent === labels[i] + " →") && ul.children.length === 5;
    return { synthetic: true, verified, intendedFields: 5, ...measure("Where to look next", cl) }; })()`,
  "rel-160x5": `(() => { const p = panelOf("Where to look next"); const ul = p.querySelector("[data-attention-item=related] ul.site-finding__inline"); const tmpl = ul.querySelector("li").cloneNode(true);
    ul.replaceChildren(); const cl = []; for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); c.querySelector("a").textContent = L(160); ul.appendChild(c); cl.push(c); }
    const verified = cl.length === 5 && cl.every((c) => c.querySelector("a").textContent.length === 160) && ul.children.length === 5;
    return { synthetic: true, verified, intendedFields: 5, ...measure("Where to look next", cl) }; })()`,
  "limits-160x5": `(() => { const p = panelOf("What limits"); const ul = p.querySelector("ul[data-finding-limits]"); const tmpl = ul.querySelector("li").cloneNode(true);
    ul.replaceChildren(); const cl = []; for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); c.textContent = L(160); ul.appendChild(c); cl.push(c); }
    const verified = ul.children.length === 5 && cl.every((c) => c.textContent.length === 160) && !!p.querySelector("[data-finding-limits-alternatives]");
    return { synthetic: true, verified, intendedFields: 5, ...measure("What limits", cl) }; })()`,
  "limits-real5": `(() => { const p = panelOf("What limits"); const ul = p.querySelector("ul[data-finding-limits]"); const items = [...ul.querySelectorAll(":scope > li")]; const tmpls = items.map((i) => i.cloneNode(true));
    ul.replaceChildren(); const cl = []; for (let i = 0; i < 5; i += 1) { const c = tmpls[i % tmpls.length].cloneNode(true); ul.appendChild(c); cl.push(c); }
    const verified = ul.children.length === 5 && !!p.querySelector("[data-finding-limits-alternatives]");
    return { synthetic: true, verified, intendedFields: 5, realTextChars: cl.map((c) => c.textContent.length), ...measure("What limits", cl) }; })()`,
  "history-real5-rel160": `(() => { const p = panelOf("Revision history"); const tbody = p.querySelector("[data-history-versions-scroll] > .data-table__scroll tbody"); const rows = [...tbody.querySelectorAll(":scope > tr")]; const tm = rows.map((r) => r.cloneNode(true));
    tbody.replaceChildren(); const cl = []; for (let i = 0; i < 5; i += 1) { const c = tm[i % tm.length].cloneNode(true); tbody.appendChild(c); cl.push(c); }
    let want = 0, got = 0; const lt = (el, s) => { want += 1; el.textContent = s; if (el.textContent.length === s.length) got += 1; };
    const rl = p.querySelector("[data-history-related-line]"); const spans = [...rl.querySelectorAll(":scope > span")]; const st = spans[0].cloneNode(true); spans.forEach((s) => s.remove());
    const rcl = []; for (let i = 0; i < 5; i += 1) { const s = st.cloneNode(true); lt(s.querySelector("a"), L(160)); if (i > 0) s.prepend(document.createTextNode(" · ")); rl.appendChild(s); rcl.push(s); }
    const verified = cl.length === 5 && want === 5 && got === 5 && rl.querySelectorAll("a[data-history-related]").length === 5;
    return { synthetic: true, verified, intendedFields: want, fields160: got, relatedRowHs: rcl.map((c) => Math.round(c.getBoundingClientRect().height)), ...measure("Revision history", cl), ...(() => { const pp = panelOf("Revision history"); pp.querySelectorAll("details").forEach((d) => { d.open = true; }); const o = measure("Revision history", cl); return { openedAll: { panelH: o.panelH, versionScroll: o.versionScroll, clipped: o.clipped.length, docOverflowX: o.docOverflowX } }; })() }; })()`,
  "rel-160x5-disc": `(() => { const p = panelOf("Where to look next"); const ul = p.querySelector("[data-attention-item=related] ul.site-finding__inline"); const tmpl = ul.querySelector("li").cloneNode(true);
    ul.replaceChildren(); const cl = []; for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); c.querySelector("a").textContent = L(160); ul.appendChild(c); cl.push(c); }
    const d = document.createElement("details"); d.className = "v69-show-all"; d.setAttribute("data-show-all", "finding-related"); d.innerHTML = '<summary class="v69-show-all__summary">Show all 5 related Findings</summary><div class="v69-show-all__body"></div>';
    ul.replaceWith(d); d.querySelector(".v69-show-all__body").appendChild(ul);
    const verified = cl.length === 5 && cl.every((c) => c.querySelector("a").textContent.length === 160) && ul.children.length === 5 && !d.open;
    const closed = measure("Where to look next", cl); d.open = true; const opened = measure("Where to look next", cl);
    return { synthetic: true, verified, intendedFields: 5, ...closed, openedPanelH: opened.panelH, openedClipped: opened.clipped, openedDocOverflowX: opened.docOverflowX }; })()`,
  "roles-160x5": `(() => { const first = document.querySelector("tr[data-claim-role]"); if (!first) return { synthetic: true, verified: false, reason: "no role rows on this page", panels: allPanels() };
    const tbody = first.parentElement; const host = first.closest("section.panel"); const title = (host.querySelector("h2")?.textContent ?? "").trim(); const tmpl = first.cloneNode(true);
    const leaves = (el) => { const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const a = []; while (w.nextNode()) { if (w.currentNode.textContent.trim() && !inClosed(w.currentNode.parentElement, host)) a.push(w.currentNode); } return a; };
    tbody.replaceChildren(); const cl = []; let want = 0, got = 0;
    for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); for (const cell of c.children) { const ls = leaves(cell); if (!ls.length) { cell.textContent = L(160); want += 1; got += cell.textContent.length === 160 ? 1 : 0; continue; } ls.forEach((n, k) => { n.textContent = k === 0 ? L(160) : ""; }); want += 1; if (ls[0].textContent.length === 160) got += 1; } tbody.appendChild(c); cl.push(c); }
    const verified = cl.length === 5 && tbody.children.length === 5 && want === 20 && got === 20;
    const panelsAll = allPanels(); const m = measure(title.slice(0, 20), cl);
    const dets = []; for (let e = tbody; e && e !== host; e = e.parentElement) if (e.tagName === "DETAILS") dets.push(e);
    const closedAncestors = dets.length; dets.forEach((d) => { d.open = true; }); const o = measure(title.slice(0, 20), cl);
    return { synthetic: true, verified, hostPanel: title, rowsInsideClosedDisclosure: closedAncestors > 0, intendedFields: want, fields160: got, panelsAfter: panelsAll, ...m, openedPanelH: o.panelH, openedRowHs: o.rowHs, openedClipped: o.clipped, openedInnerScrollX: o.innerScrollX, openedDocOverflowX: o.docOverflowX }; })()`,
  "hist-measure": `(() => { const p = panelOf("Revision history"); const rows = [...p.querySelectorAll("[data-history-revision]")]; const m = measure("Revision history", rows.slice(0, 5));
    p.querySelectorAll("details").forEach((d) => { d.open = true; }); const o = measure("Revision history", rows.slice(0, 5));
    return { synthetic: false, verified: true, versionRows: rows.length, ...m, openedAll: { panelH: o.panelH, versionScroll: o.versionScroll, clipped: o.clipped.length, docOverflowX: o.docOverflowX } }; })()`,
  "history-5": `(() => { const p = panelOf("Revision history"); const tbody = p.querySelector("[data-history-versions-scroll] > .data-table__scroll tbody"); const rows = [...tbody.querySelectorAll(":scope > tr")]; const tmpl = rows[0].cloneNode(true);
    tbody.replaceChildren(); const cl = []; let want = 0, got = 0; const lt = (el, s) => { want += 1; el.textContent = s; if (el.textContent.length === s.length) got += 1; };
    for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); const tds = c.querySelectorAll(":scope > td");
      lt(tds[1].querySelector("strong"), L(160)); const small = tds[1].querySelector("small"); const sn = small.firstChild; want += 1; sn.textContent = L(160) + " · "; if (sn.textContent.length === 163) got += 1;
      lt(tds[2].querySelector("p[data-history-basis-line]"), L(160)); lt(tds[2].querySelector("[data-history-cited]"), L(160)); tbody.appendChild(c); cl.push(c); }
    const rl = p.querySelector("[data-history-related-line]"); const spans = [...rl.querySelectorAll(":scope > span")]; const st = spans[0].cloneNode(true); spans.forEach((s) => s.remove());
    const rcl = []; for (let i = 0; i < 5; i += 1) { const s = st.cloneNode(true); lt(s.querySelector("a"), L(160)); if (i > 0) s.prepend(document.createTextNode(" · ")); rl.appendChild(s); rcl.push(s); }
    const verified = cl.length === 5 && want > 0 && want === got && rl.querySelectorAll("a[data-history-related]").length === 5;
    return { synthetic: true, verified, intendedFields: want, fields160: got, relatedRowHs: rcl.map((c) => Math.round(c.getBoundingClientRect().height)), ...measure("Revision history", cl), ...(() => { const pp = panelOf("Revision history"); pp.querySelectorAll("details").forEach((d) => { d.open = true; }); const o = measure("Revision history", cl); return { openedAll: { panelH: o.panelH, versionScroll: o.versionScroll, clipped: o.clipped.length, docOverflowX: o.docOverflowX } }; })() }; })()`,
};
const s = await session();
const results = [];
try {
  for (const v of variants) {
    for (const w of [1440, 390]) {
      let attempt = 0;
      for (;;) { try {
      await s.open(v.url, w, w === 1440 ? 1000 : 900);
      const real = await s.js("(() => {" + COMMON + "return " + BODIES.baseline + "})()");
      await s.shot(`${OUT}/${v.name}-baseline-${w}-app.png`); // the unmodified app screenshot first
      if (v.variant === "baseline") { results.push({ name: v.name, variant: "baseline", w, ...real }); break; }
      const r = await s.js("(() => {" + COMMON + "return " + BODIES[v.variant] + "})()");
      await s.shot(`${OUT}/${v.name}-${v.variant}-${w}-synthetic.png`);
      results.push({ name: v.name, variant: v.variant, w, baselinePanels: real.panels, ...r });
      console.log(v.name, v.variant, w, JSON.stringify({ panelH: r.panelH, verified: r.verified, clipped: r.clipped.length, doc: r.docOverflowX, rows: r.rowHs }));
      break; } catch (e) { attempt += 1; console.log("retry", v.name, v.variant, w, String(e).slice(0, 160)); if (attempt >= 3) throw e; } }
    }
  }
} finally { await s.close(); }
writeFileSync(`${OUT}/probe-results.json`, JSON.stringify(results, null, 1));
