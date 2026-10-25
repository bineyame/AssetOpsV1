// SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA (post-W6 W1-b recapture, agent B; W3 closeout ruling 1 method).
// Capture-only: per width, load the real mounted page, screenshot+measure the UNMODIFIED page, then in the same session
// clone a real row into five rows (never persisted), set every intended field to 160 chars, assert verified, measure.
//   node B-probe.mjs <out-dir> <variants.json>   variants: [{name,url,variant: "ah-160x5"|"er-160x5"}]
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { session } from "./B-cdp.mjs";
const [OUT, VARS] = process.argv.slice(2);
mkdirSync(OUT, { recursive: true });
const COMMON = String.raw`
const base = "Synthetic layout probe text that wraps across several lines in this narrow panel and keeps going ";
const L = (n) => base.repeat(4).slice(0, n);
const panelOf = (t) => [...document.querySelectorAll("section.panel")].find((p) => (p.querySelector("h2")?.textContent ?? "").trim() === t);
const inClosed = (n, root) => { for (let e = n; e && e !== root; e = e.parentElement) { const d = e.parentElement; if (d && d.tagName === "DETAILS" && !d.open && e.tagName !== "SUMMARY") return true; } return false; };
const leaves = (el, root) => { const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const a = []; while (w.nextNode()) { if (w.currentNode.textContent.trim() && !inClosed(w.currentNode.parentElement, root)) a.push(w.currentNode); } return a; };
const longest = (el, root) => leaves(el, root).sort((a, b) => b.textContent.length - a.textContent.length)[0];
const measure = (title, clones) => { const p = panelOf(title); const r = p.getBoundingClientRect();
  const clipped = [...p.querySelectorAll("*")].filter((e) => { if (inClosed(e, p) || !e.firstChild) return false; const s = getComputedStyle(e);
    return ((s.overflowX === "hidden" || s.overflowX === "clip" || s.textOverflow === "ellipsis") && e.scrollWidth > e.clientWidth + 1) || ((s.overflowY === "hidden" || s.overflowY === "clip") && e.scrollHeight > e.clientHeight + 2); }).map((e) => e.tagName + "." + String(e.className).slice(0, 30));
  const innerScrollX = [...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowX === "auto" || s.overflowX === "scroll") && e.clientWidth > 0 && e.scrollWidth > e.clientWidth + 1; }).map((e) => String(e.className).slice(0, 30) + ":" + e.scrollWidth + "/" + e.clientWidth);
  const tableScroller = [...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowX === "auto" || s.overflowX === "scroll") && e.querySelector("table"); }).map((e) => ({ cls: String(e.className).slice(0, 30), sw: e.scrollWidth, cw: e.clientWidth }));
  return { title, panelH: Math.round(r.height), rowHs: clones.map((c) => Math.round(c.getBoundingClientRect().height)), clipped, innerScrollX, tableScroller, docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth }; };
// ah-160x5: the meaning cell's prose leaf (longest text leaf outside code/a) -> 160 chars; reference codes/links kept.
// ah-160x5-cell: the whole meaning cell text -> 160 chars of prose (no reference token left).
const AH = (whole) => { const p = panelOf("Action history"); const tbody = p.querySelector("table tbody"); const rows = [...tbody.querySelectorAll(":scope > tr")];
  const tmpl = rows[0].cloneNode(true); const countsLine = !!p.querySelector("[data-action-history-truncated], [data-action-history-show-all]");
  tbody.replaceChildren(); const cl = []; let got = 0;
  for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); const cell = c.children[1];
    if (whole) { cell.textContent = L(160); if (cell.textContent.length === 160) got += 1; }
    else { const lg = leaves(cell, p).filter((n) => !n.parentElement.closest("code, a")).sort((a, b) => b.textContent.length - a.textContent.length)[0]; if (lg) { lg.textContent = L(160); if (lg.textContent.length === 160) got += 1; } }
    tbody.appendChild(c); cl.push(c); }
  const verified = cl.length === 5 && tbody.children.length === 5 && got === 5 && countsLine;
  return { synthetic: true, verified, intendedFields: 5, fields160: got, template: tmpl.getAttribute("data-action-event-kind"), countsLine, countsText: (p.querySelector("[data-action-history-truncated]")?.textContent ?? "").trim(), colW: [...cl[0].children].map((x) => Math.round(x.getBoundingClientRect().width)), ...measure("Action history", cl) }; };
// Follow-up (coordinator correction). Prose leaf of a meaning cell -> 160 chars, reference codes/links kept.
const prose160 = (cell, p) => { const lg = leaves(cell, p).filter((n) => !n.parentElement.closest("code, a, small")).sort((a, b) => b.textContent.length - a.textContent.length)[0]; if (!lg) return false; lg.textContent = L(160); return lg.textContent.length === 160; };
const HIST = async (expand) => { const p = panelOf("Action history"); const tbody = p.querySelector("table tbody");
  const truncBefore = (p.querySelector("[data-action-history-truncated]")?.textContent ?? "").trim(); const btn = p.querySelector("[data-action-history-show-all]"); const btnBefore = btn ? btn.textContent.trim() : null;
  let clicked = false; if (expand && btn && btnBefore.startsWith("Show all")) { btn.click(); clicked = true; await new Promise((r) => setTimeout(r, 800)); }
  let rows = [...tbody.querySelectorAll(":scope > tr")]; const realRows = rows.length; let clonedToFive = false;
  if (expand && rows.length < 5) { const t = rows[0]; while (tbody.children.length < 5) tbody.appendChild(t.cloneNode(true)); rows = [...tbody.querySelectorAll(":scope > tr")]; clonedToFive = true; }
  let got = 0; rows.forEach((r) => { if (prose160(r.children[1], p)) got += 1; });
  const truncAfter = (p.querySelector("[data-action-history-truncated]")?.textContent ?? "").trim(); const b2 = p.querySelector("[data-action-history-show-all]");
  const verified = got === rows.length && (expand ? clicked && rows.length >= 5 : rows.length === 3 && !!truncAfter && !!b2 && b2.textContent.trim().startsWith("Show all"));
  return { synthetic: true, verified, rowsShown: rows.length, realRows, clonedToFive, clicked, intendedFields: rows.length, fields160: got, truncation: truncAfter || null, button: b2 ? b2.textContent.trim() : null, buttonBefore: btnBefore, truncBefore, ...measure("Action history", rows) }; };
const EVREQ = () => { const p = panelOf("Evidence requirements"); const rows = [...p.querySelector("table tbody").querySelectorAll(":scope > tr")]; const changed = [];
  const set = (node, label, prefix) => { node.textContent = prefix ? " " + L(159) : L(160); changed.push({ label, len: node.textContent.length }); };
  rows.forEach((r) => { const lab = (r.querySelector("th")?.textContent ?? "").trim(); const td = r.querySelector("td");
    [...td.childNodes].filter((n) => n.nodeType === 3 && n.textContent.trim() && n.textContent.trim() !== "·").forEach((n) => set(n, lab + ": detail text", true));
    td.querySelectorAll("[data-verification-window-gaps], [data-verification-window-problems], [data-verification-target-reasons]").forEach((e) => { if (!inClosed(e, p)) set(e, lab + ": " + [...e.attributes].map((a) => a.name).filter((n) => n.startsWith("data-verification")).join(","), false); });
    td.querySelectorAll(":scope > [data-verification-requirement] > span:last-child").forEach((e) => set(e, lab + ": " + e.parentElement.getAttribute("data-verification-requirement") + " detail", false)); });
  const labels = rows.map((r) => (r.querySelector("th")?.textContent ?? "").trim()); const chips = rows.map((r) => [...r.querySelectorAll("td [class*='chip'], td .badge")].map((c) => c.textContent.trim()));
  const verified = rows.length === 4 && changed.length > 0 && changed.every((c) => c.len === 160);
  return { synthetic: true, verified, rows: rows.length, labels, chips, changedNodes: changed.map((c) => c.label), fields160: changed.filter((c) => c.len === 160).length, intendedFields: changed.length, ...measure("Evidence requirements", rows) }; };
const allPanels = () => [...document.querySelectorAll("section.panel")].map((p) => ({ t: (p.querySelector("h2")?.textContent ?? "").trim(), h: Math.round(p.getBoundingClientRect().height) }));
`;
const BODIES = {
  baseline: String.raw`(() => ({ panels: allPanels(), docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth }))()`,
  "ah-160x5": String.raw`(() => AH(false))()`,
  "ah-160x5-cell": String.raw`(() => AH(true))()`,
  "B-hist-160-default3": String.raw`HIST(false)`,
  "B-hist-160-expanded": String.raw`HIST(true)`,
  "B-evreq-real4-160": String.raw`(() => EVREQ())()`,
  "er-160x5": String.raw`(() => { const p = panelOf("Evidence requirements"); const tbody = p.querySelector("table tbody"); const rows = [...tbody.querySelectorAll(":scope > tr")]; const tmpl = rows[0].cloneNode(true);
    tbody.replaceChildren(); const cl = []; let want = 0, got = 0;
    for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); const req = c.querySelector("th") ?? c.children[0]; const st = c.querySelector("td") ?? c.children[1];
      want += 1; req.textContent = L(160); if (req.textContent.length === 160) got += 1;
      want += 1; const lg = longest(st, p); if (lg) { lg.textContent = L(160); if (lg.textContent.length === 160) got += 1; }
      tbody.appendChild(c); cl.push(c); }
    const verified = cl.length === 5 && tbody.children.length === 5 && want === 10 && got === 10;
    return { synthetic: true, verified, intendedFields: want, fields160: got, ...measure("Evidence requirements", cl) }; })()`,
};
const s = await session(); const results = [];
try {
  for (const v of JSON.parse(readFileSync(VARS, "utf8"))) for (const w of [1440, 390]) {
    await s.open(v.url, w, w === 1440 ? 1000 : 900);
    const real = await s.js("(() => {" + COMMON + "return " + BODIES.baseline + "})()");
    await s.shot(`${OUT}/B-${v.name}-baseline-${w}-app.png`);
    const r = await s.js("(() => {" + COMMON + "return " + BODIES[v.variant] + "})()");
    await s.shot(`${OUT}/B-${v.name}-${v.variant}-${w}-synthetic.png`);
    results.push({ name: v.name, variant: v.variant, w, url: v.url, baselinePanels: real.panels, baselineDocOverflowX: real.docOverflowX, ...r });
    console.log(v.name, v.variant, w, JSON.stringify({ verified: r.verified, panelH: r.panelH, rows: r.rowHs, n: r.rowsShown ?? r.rows, clipped: r.clipped.length, doc: r.docOverflowX, scroller: r.tableScroller, counts: r.countsLine }));
  }
} finally { await s.close(); }
writeFileSync(`${OUT}/B-probe-results-${process.argv[4] ?? "run"}.json`, JSON.stringify(results, null, 1));
