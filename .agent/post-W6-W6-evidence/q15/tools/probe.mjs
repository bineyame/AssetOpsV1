// SYNTHETIC LAYOUT PROBE - not product data. cap-q15 (post-W6 W6 Q15/Q16 cap proof; W3 closeout rulings 1-2 method).
// Adapted from .agent/post-W6-W1-a-fix-probe/tools/probe.mjs (AssetOpsV1-plan2). Capture-only: per width, load the real
// mounted page, measure + screenshot the UNMODIFIED page first, then in the same browser session replace the rendered
// rows with FIVE clones of a real row (real structure/styles/links/closed disclosures kept), set every intended variable
// visible text field to exactly 160 chars, ASSERT all five rows and every intended field changed, measure the CLOSED panel,
// then open every disclosure in the panel and measure again (exempt from cap). Never persisted.
//   node probe.mjs <out-dir> <variants.json>     variants: [{name, url, kind, panel}]
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { session } from "./cdp.mjs";
const [OUT, VARS] = process.argv.slice(2);
const variants = JSON.parse(readFileSync(VARS, "utf8"));
mkdirSync(OUT, { recursive: true });
const LABEL = "SYNTHETIC LAYOUT PROBE - not product data";
const COMMON = String.raw`
const base = "Synthetic layout probe text that wraps across several lines in this narrow panel and keeps going ";
const L160 = base.repeat(3).slice(0, 160);
const TS = /^\s*\d{1,2} [A-Z][a-z]{2} \d{4}, \d{2}:\d{2}(:\d{2})? UTC\s*$/;
const panelOf = (t) => [...document.querySelectorAll("section.panel")].find((p) => (p.querySelector("h2")?.textContent ?? "").trim() === t);
const inClosed = (n, root) => { for (let e = n; e && e !== root; e = e.parentElement) { const d = e.parentElement; if (d && d.tagName === "DETAILS" && !d.open && e.tagName !== "SUMMARY") return true; } return false; };
const textIn = (n, root) => { for (let e = n.parentElement; e && e !== root; e = e.parentElement) if (e.tagName === "DETAILS" && !e.open) { const s = n.parentElement.closest("summary"); if (!s || s.parentElement !== e) return true; } return false; };
const docOX = () => document.documentElement.scrollWidth - document.documentElement.clientWidth;
const hasFull = (e) => { const cell = e.closest("td, th, .panel__body > div, li") ?? e.parentElement; return !!cell && [...cell.querySelectorAll("details")].some((d) => /^Full /.test(d.querySelector("summary")?.textContent ?? "")); };
const measure = (p, rows) => { const r = p.getBoundingClientRect();
  const clippedEls = [...p.querySelectorAll("*")].filter((e) => { if (inClosed(e, p) || !e.firstChild) return false; if (e.tagName === "SELECT" || e.tagName === "OPTION") return false; const s = getComputedStyle(e);
    if (s.overflowX === "auto" || s.overflowX === "scroll") return false;
    return ((s.overflowX === "hidden" || s.overflowX === "clip" || s.textOverflow === "ellipsis") && e.scrollWidth > e.clientWidth + 1) || ((s.overflowY === "hidden" || s.overflowY === "clip") && e.scrollHeight > e.clientHeight + 2); });
  const clipped = clippedEls.map((e) => ({ el: e.tagName + "." + String(e.className).slice(0, 40), cell: (e.closest("td,th") ? (e.closest("table")?.querySelectorAll("thead th")[e.closest("td,th").cellIndex]?.textContent.trim() ?? "") : ""), titleAttr: !!(e.title || e.querySelector("[title]")), clamp: e.classList.contains("global-work-clamp"), fullTextDisclosure: hasFull(e), sh: e.scrollHeight, ch: e.clientHeight }));
  const scrollers = [...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowX === "auto" || s.overflowX === "scroll") && e.clientWidth > 0; }).map((e) => ({ el: String(e.className).slice(0, 30), sw: e.scrollWidth, cw: e.clientWidth, scrollable: e.scrollWidth > e.clientWidth + 1, tabindex: e.tabIndex, role: e.getAttribute("role") }));
  const vScrollers = [...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowY === "auto" || s.overflowY === "scroll") && e.clientHeight > 0 && e.scrollHeight > e.clientHeight + 1; }).map((e) => ({ el: String(e.className).slice(0, 30), sh: e.scrollHeight, ch: e.clientHeight, maxH: getComputedStyle(e).maxHeight, overflowY: getComputedStyle(e).overflowY, tabindex: e.tabIndex, role: e.getAttribute("role"), label: e.getAttribute("aria-labelledby") || e.getAttribute("aria-label") }));
  return { vScrollers, panelH: Math.round(r.height), rowHs: (rows ?? []).map((c) => Math.round(c.getBoundingClientRect().height)), clipped, clippedCount: clipped.length, clippedWithoutFullText: clipped.filter((c) => !c.fullTextDisclosure).length, scrollers, docOverflowX: docOX() }; };
const allPanels = () => [...document.querySelectorAll("section.panel")].map((p) => ({ t: (p.querySelector("h2")?.textContent ?? "").trim(), h: Math.round(p.getBoundingClientRect().height) }));
const opTable = () => { const p = panelOf("Operational records"); if (!p) return null; const t = p.querySelector("table"); if (!t) return { table: false }; const sc = t.closest(".data-table__scroll") ?? t.parentElement;
  return { scrollerClass: String(sc.className), scrollW: sc.scrollWidth, clientW: sc.clientWidth, fits: sc.scrollWidth <= sc.clientWidth, overflowX: getComputedStyle(sc).overflowX, tableW: Math.round(t.getBoundingClientRect().width), tableLayout: getComputedStyle(t).tableLayout,
    cols: [...t.querySelectorAll("thead th")].map((th) => [th.textContent.trim(), Math.round(th.getBoundingClientRect().width)]), rowHs: [...t.querySelectorAll("tbody > tr")].map((r) => Math.round(r.getBoundingClientRect().height)) }; };
const tabs = () => { const ol = document.querySelector("ol.site-tabs__list"); if (!ol) return null; const vw = document.documentElement.clientWidth;
  const items = [...ol.children].map((li) => { const r = li.getBoundingClientRect(); const lab = li.querySelector("a, span") ?? li; return { text: li.textContent.trim(), left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top), inside: r.left >= 0 && r.right <= vw + 0.5, labelComplete: lab.scrollWidth <= lab.clientWidth + 1 && getComputedStyle(lab).textOverflow !== "ellipsis" || lab.scrollWidth <= lab.clientWidth + 1 }; });
  const anc = []; for (let e = ol; e && e.tagName !== "MAIN"; e = e.parentElement) { const s = getComputedStyle(e); anc.push({ el: e.tagName + "." + String(e.className).slice(0, 30), overflowX: s.overflowX, sw: e.scrollWidth, cw: e.clientWidth, innerScroller: (s.overflowX === "auto" || s.overflowX === "scroll") && e.scrollWidth > e.clientWidth + 1 }); }
  return { vw, count: items.length, items, listSW: ol.scrollWidth, listCW: ol.clientWidth, listFits: ol.scrollWidth <= ol.clientWidth, rows: new Set(items.map((i) => i.top)).size, ancestors: anc, noInnerTabScroller: anc.every((a) => !a.innerScroller), allInside: items.every((i) => i.inside && i.labelComplete) }; };
// field setter: every non-blank text node under root that is visible (not in a closed disclosure body), not a typed badge, not a timestamp.
const setFields = (root, opts = {}) => { const fields = []; const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); const nodes = []; while (w.nextNode()) nodes.push(w.currentNode);
  for (const n of nodes) { const t = n.textContent; if (!t.trim()) continue; const e = n.parentElement;
    if (e.closest("summary")) continue; if (textIn(n, root)) continue;
    if (e.closest(".w1f4-action-badge, .work-record-badge, [data-global-work-state], [data-lifecycle-step]")) continue;
    if (TS.test(t)) continue; if (opts.skip && e.closest(opts.skip)) continue; if (/^\s*[—-]\s*$/.test(t)) continue;
    const sep = / · $/.test(t) ? " · " : ""; const pre = /^ · /.test(t) ? " · " : ""; n.textContent = pre + L160 + sep; fields.push(n); }
  // closed full-text disclosure bodies mirror the field (kept closed; for the all-open measurement only)
  root.querySelectorAll("details").forEach((d) => { if (/^Full /.test(d.querySelector("summary")?.textContent ?? "")) { [...d.childNodes].forEach((c) => { if (c.nodeType === 3 && c.textContent.trim()) c.textContent = L160; }); } });
  return fields; };
const fieldOk = (n) => n.isConnected && n.textContent.replace(/^ · /, "").replace(/ · $/, "") === L160 && L160.length === 160;
`;
const KINDS = {
  baseline: `(() => ({ panels: allPanels(), docOverflowX: docOX(), opTable: opTable(), tabs: tabs() }))()`,
  // list tables: tbody rows -> five clones of the tallest real row
  rows5: (panel, tmplSel = ":scope > tr") => `(() => { const p = panelOf(${JSON.stringify(panel)}); const tb = p.querySelector("tbody"); const real = [...tb.querySelectorAll("${tmplSel}")];
    const tmpl = real.slice().sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0].cloneNode(true);
    tb.replaceChildren(); const cl = []; const perRow = []; let want = 0, got = 0; const fieldNames = [];
    for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); tb.appendChild(c); const f = setFields(c); perRow.push(f.length); want += f.length; got += f.filter(fieldOk).length; if (i === 0) f.forEach((n) => fieldNames.push(n.parentElement.tagName.toLowerCase() + [...n.parentElement.attributes].filter((a) => a.name.startsWith("data-")).map((a) => "[" + a.name + "]").join(""))); cl.push(c); }
    const extra = []; ${panel === "Operational records" ? `const fp = panelOf("Record a manual reading"); if (fp) fp.querySelectorAll("select[data-global-work-form-site] option").forEach((o) => { o.textContent = L160; extra.push(o); });` : ""}
    const verified = cl.length === 5 && tb.children.length === 5 && perRow.every((n) => n > 0 && n === perRow[0]) && want === got && extra.every((o) => o.textContent.length === 160);
    return { synthetic: true, verified, rows: tb.children.length, fieldsPerRow: perRow, intendedFields: want, fields160: got, fieldNames, extraFields160: extra.length, rowsRef: cl.length, opTable: opTable(), panelsAfter: allPanels(), ...measure(p, cl), _cl: null }; })()`,
  // WR record: five clones of the real record group (tbody) with every variable text field at 160
  recordGroups5: (panel) => `(() => { const p = panelOf(${JSON.stringify(panel)}); const t = p.querySelector("table"); const groups = [...t.querySelectorAll(":scope > tbody")];
    const tmpl = groups.slice().sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0].cloneNode(true); groups.forEach((g) => g.remove());
    const cl = []; const perRow = []; let want = 0, got = 0; const fieldNames = [];
    for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); t.appendChild(c); const f = setFields(c, { skip: "th.work-record-item" }); perRow.push(f.length); want += f.length; got += f.filter(fieldOk).length; if (i === 0) f.forEach((n) => fieldNames.push(n.parentElement.tagName.toLowerCase() + [...n.parentElement.attributes].filter((a) => a.name.startsWith("data-")).map((a) => "[" + a.name + "=" + a.value.slice(0, 16) + "]").join(""))); cl.push(c); }
    const verified = t.querySelectorAll(":scope > tbody").length === 5 && perRow.every((n) => n > 0 && n === perRow[0]) && want === got;
    return { synthetic: true, verified, rows: 5, rowUnit: "record group (tbody) incl. its item rows", fieldsPerRow: perRow, intendedFields: want, fields160: got, fieldNames, panelsAfter: allPanels(), ...measure(p, cl) }; })()`,
  // WR overview Work done: not a row table; every variable visible text field to 160 (Type is a typed enum)
  workDone: (panel) => `(() => { const p = panelOf(${JSON.stringify(panel)}); const body = p.querySelector(".panel__body"); body.querySelectorAll("dt").forEach((d) => { if (d.textContent.trim() === "Type" && d.nextElementSibling) d.nextElementSibling.setAttribute("data-q15-typed", "1"); });
    const f = setFields(body, { skip: "dt, .work-request-latest__label, [data-mock-deviation], dd[data-q15-typed]" });
    const dts = [...body.querySelectorAll("dt")].map((d) => d.textContent.trim());
    const fieldNames = f.map((n) => n.parentElement.tagName.toLowerCase() + [...n.parentElement.attributes].filter((a) => a.name.startsWith("data-")).map((a) => "[" + a.name + "=" + a.value.slice(0, 16) + "]").join(""));
    const verified = f.length > 0 && f.every(fieldOk);
    return { synthetic: true, verified, rows: 0, rowUnit: "not a row table: narrative, latest activity and dl values", dlTerms: dts, intendedFields: f.length, fields160: f.filter(fieldOk).length, fieldNames, panelsAfter: allPanels(), ...measure(p, []) }; })()`,
  asIs: (panel) => `(() => { const p = panelOf(${JSON.stringify(panel)}); return { synthetic: false, verified: true, rows: 0, rowUnit: "no variable text field: measured as-is", intendedFields: 0, fields160: 0, panelsAfter: allPanels(), ...measure(p, []) }; })()`,
  manualForm: (panel) => `(() => { const p = panelOf(${JSON.stringify(panel)}); const os = [...p.querySelectorAll("select[data-global-work-form-site] option")]; os.forEach((o) => { o.textContent = L160; });
    const verified = os.length > 0 && os.every((o) => o.textContent.length === 160);
    return { synthetic: true, verified, rows: 0, rowUnit: "form: only the scope Site option names are variable (set to 160); other text is fixed copy", intendedFields: os.length, fields160: os.filter((o) => o.textContent.length === 160).length, panelsAfter: allPanels(), ...measure(p, []) }; })()`,
};
const s = await session();
const results = [];
async function size(w, h) { await s.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 600 }); }
async function fullShot(path, w) {
  const tall = await s.js(`Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)`);
  await size(w, Math.min(Math.ceil(tall), 9000)); await new Promise((r) => setTimeout(r, 400));
  const r = await s.send("Page.captureScreenshot", { format: "png" }); writeFileSync(path, Buffer.from(r.data, "base64"));
  await size(w, w === 1440 ? 1000 : 900); await new Promise((r) => setTimeout(r, 300));
}
const banner = `(() => { const b = document.createElement("div"); b.textContent = ${JSON.stringify(LABEL)}; b.setAttribute("data-q15-label", "1"); Object.assign(b.style, { position: "fixed", top: "0", right: "0", zIndex: 99999, background: "#b00020", color: "#fff", font: "bold 12px sans-serif", padding: "4px 8px", pointerEvents: "none" }); document.body.appendChild(b); return true; })()`;
try {
  for (const v of variants) {
    for (const w of [1440, 390]) {
      let attempt = 0;
      for (;;) { try {
        await size(w, w === 1440 ? 1000 : 900);
        await s.open(v.url, w, w === 1440 ? 1000 : 900);
        await size(w, w === 1440 ? 1000 : 900); await new Promise((r) => setTimeout(r, 500));
        const real = await s.js("(() => {" + COMMON + "return " + KINDS.baseline + "})()");
        await fullShot(`${OUT}/${v.name}-${w}-app.png`, w); // unmodified app screenshot first
        if (v.kind === "baseline") { results.push({ name: v.name, url: v.url, kind: "baseline", w, synthetic: false, ...real }); console.log(v.name, w, "baseline", JSON.stringify(real.panels)); break; }
        const expr = typeof KINDS[v.kind] === "function" ? KINDS[v.kind](v.panel) : KINDS[v.kind];
        const pre = await s.js(`(() => { const p = [...document.querySelectorAll("section.panel")].find((x) => (x.querySelector("h2")?.textContent ?? "").trim() === ${JSON.stringify(v.panel)}); if (!p) return "panel absent"; if (${JSON.stringify(v.kind)} === "rows5" && !p.querySelector("tbody > tr")) return "no table rows"; if (${JSON.stringify(v.kind)} === "recordGroups5" && !p.querySelector("table > tbody")) return "no record table"; return ""; })()`);
        if (pre) { results.push({ name: v.name, url: v.url, kind: v.kind, panel: v.panel, w, skipped: pre, baselinePanels: real.panels }); console.log(v.name, w, "SKIPPED", pre, JSON.stringify(real.panels)); break; }
        const r = await s.js("(() => {" + COMMON + "return " + expr + "})()");
        await s.js(banner);
        await fullShot(`${OUT}/${v.name}-${w}-SYNTHETIC-closed.png`, w);
        const o = await s.js("(() => {" + COMMON + `const p = panelOf(${JSON.stringify(v.panel)}); p.querySelectorAll("details").forEach((d) => { d.open = true; }); const m = measure(p, []); return { vScrollers: m.vScrollers, panelH: m.panelH, clippedCount: m.clippedCount, clippedWithoutFullText: m.clippedWithoutFullText, clipped: m.clipped, docOverflowX: m.docOverflowX, details: p.querySelectorAll("details").length }; })()`);
        await fullShot(`${OUT}/${v.name}-${w}-SYNTHETIC-allopen.png`, w);
        const out = { label: LABEL, name: v.name, url: v.url, kind: v.kind, panel: v.panel, w, baselinePanels: real.panels, baselineOpTable: real.opTable, baselineTabs: real.tabs, baselineDocOverflowX: real.docOverflowX, closed: r, allOpen: o };
        results.push(out);
        console.log(v.name, w, JSON.stringify({ base: real.panels.find((x) => x.t === v.panel)?.h, panelH: r.panelH, verified: r.verified, want: r.intendedFields, got: r.fields160, rows: r.rowHs, clip: r.clippedCount, vScroll: r.vScrollers.map((x) => x.sh + "/" + x.ch + ":" + x.maxH), clipNoFull: r.clippedWithoutFullText, doc: r.docOverflowX, open: o.panelH, openClipNoFull: o.clippedWithoutFullText }));
        if (!r.verified) console.log("ASSERTION FAILED", v.name, w);
        break; } catch (e) { attempt += 1; console.log("retry", v.name, w, String(e).slice(0, 300)); if (attempt >= 3) { results.push({ name: v.name, url: v.url, kind: v.kind, panel: v.panel, w, error: String(e).slice(0, 300) }); console.log("ERROR", v.name, w); break; } } }
    }
  }
} finally { writeFileSync(`${OUT}/probe-results.json`, JSON.stringify({ label: LABEL, product: "f3da6e90", results }, null, 1)); await s.close(); }
process.exit(results.some((r) => (r.closed && !r.closed.verified) || r.error) ? 2 : 0);
