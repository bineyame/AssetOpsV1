// SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA (post-W6 W1-b fix round 3, caps ruling 2 / ruling 1 recheck).
// Reuses B-probe.mjs helpers (COMMON). Capture-only: real mounted page, in-session DOM edits, never persisted.
//   node C-probe.mjs <out-dir> <variants.json> <tag>
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { session } from "./B-cdp.mjs";
const [OUT, VARS, TAG] = process.argv.slice(2);
mkdirSync(OUT, { recursive: true });
const src = readFileSync(new URL("./B-probe.mjs", import.meta.url), "utf8");
const COMMON_B = src.slice(src.indexOf("const COMMON = String.raw`") + "const COMMON = String.raw`".length, src.indexOf("`;\nconst BODIES"));
const COMMON = COMMON_B + String.raw`
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const regionState = async (p) => {
  await sleep(700);
  const reg = p.querySelector("[data-action-history-entries]"); const cue = p.querySelector("[data-action-history-scroll-cue]");
  const tbody = p.querySelector("table tbody"); const rows = [...tbody.querySelectorAll(":scope > tr")];
  const r = reg.getBoundingClientRect(); const cs = getComputedStyle(reg);
  const out = { regionRole: reg.getAttribute("role"), regionName: reg.getAttribute("aria-label"), tabIndex: reg.tabIndex, overflowY: cs.overflowY, maxHeight: cs.maxHeight,
    regionClientH: reg.clientHeight, regionScrollH: reg.scrollHeight, cueHidden: cue.hidden, cueText: cue.textContent, cueVisible: getComputedStyle(cue).display !== "none",
    rowCount: rows.length, tableHasHead: !!reg.querySelector("thead"), toggleOutside: !reg.contains(p.querySelector("[data-action-history-show-all]")) , countOutside: !reg.contains(p.querySelector("[data-action-history-truncated]")) };
  reg.focus(); out.focusable = document.activeElement === reg;
  const inner = [...reg.querySelectorAll(".data-table__scroll")][0]; out.innerScroller = inner ? { cw: inner.clientWidth, sw: inner.scrollWidth, tabIndex: inner.tabIndex, role: inner.getAttribute("role") } : null;
  if (inner) { inner.focus(); out.innerFocusable = document.activeElement === inner; inner.scrollLeft = inner.scrollWidth; out.innerScrolledX = inner.scrollLeft; inner.scrollLeft = 0; }
  reg.scrollTop = reg.scrollHeight; await sleep(100);
  const last = rows[rows.length - 1].getBoundingClientRect(); const rr = reg.getBoundingClientRect();
  out.lastRowReachable = last.bottom <= rr.bottom + 1 && last.top >= rr.top - 1; out.scrollTopAtEnd = Math.round(reg.scrollTop); reg.scrollTop = 0;
  out.rowTextLens = rows.map((r) => r.innerText.length);
  return out; };
const fullCodes = (p) => { let n = 0; const U = "0123abcd-4567-89ef-0123-456789abcdef"; p.querySelectorAll("code").forEach((c) => { if (c.closest("[data-action-history-entries]")) { c.textContent = U; n += 1; } }); return n; };
const histBase = async (mode) => { const p = panelOf("Action history"); const tbody = p.querySelector("table tbody");
  const btn = p.querySelector("[data-action-history-show-all]"); let clicked = false;
  if ((mode === "expanded" || mode === "expanded-full") && btn && btn.textContent.trim().startsWith("Show all")) { btn.click(); clicked = true; await sleep(800); }
  let rows = [...tbody.querySelectorAll(":scope > tr")]; const realRows = rows.length; let cloned = false;
  if (mode === "clone5") { const t = rows[0]; while (tbody.children.length < 5) tbody.appendChild(t.cloneNode(true)); while (tbody.children.length > 5) tbody.lastChild.remove(); cloned = true; rows = [...tbody.querySelectorAll(":scope > tr")]; }
  let got = 0; rows.forEach((r) => { const cell = r.children[1]; const lg = leaves(cell, p).filter((n) => !n.parentElement.closest("code, a, small")).sort((a, b) => b.textContent.length - a.textContent.length)[0]; if (lg) { lg.textContent = L(160); if (lg.textContent.length === 160) got += 1; } });
  let codes = 0; if (mode.endsWith("full") || mode === "narrow-full") codes = fullCodes(p);
  const reg = await regionState(p); const r = p.getBoundingClientRect();
  const m = measure("Action history", rows);
  return { synthetic: true, verified: got === rows.length && (mode !== "expanded" || clicked), clicked, realRows, cloned, fields160: got, fullCodesExpanded: codes, panelH: Math.round(r.height), rowHs: m.rowHs, clipped: m.clipped, docOverflowX: m.docOverflowX, region: reg,
    truncation: (p.querySelector("[data-action-history-truncated]")?.textContent ?? "").trim() || null, button: (p.querySelector("[data-action-history-show-all]")?.textContent ?? "").trim() || null }; };
`;
const BODIES = {
  baseline: String.raw`(async () => { const p = panelOf("Action history"); const reg = await regionState(p); return { panels: allPanels(), docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth, region: reg, panelH: Math.round(p.getBoundingClientRect().height) }; })()`,
  "baseline-panels": String.raw`(() => ({ panels: allPanels(), docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth }))()`,
  "C-hist-default3-160": String.raw`histBase("default3")`,
  "C-hist-clone5-160": String.raw`histBase("clone5")`,
  "C-hist-expanded-real-160": String.raw`histBase("expanded")`,
  "C-hist-narrow-fullcodes-default3": String.raw`histBase("narrow-full")`,
  "C-hist-narrow-fullcodes-expanded": String.raw`histBase("expanded-full")`,
  "C-evreq-real4-160": String.raw`(() => EVREQ())()`,
};
const s = await session(); const results = [];
try {
  for (const v of JSON.parse(readFileSync(VARS, "utf8"))) for (const w of [1440, 390]) {
    await s.open(v.url, w, w === 1440 ? 1000 : 900);
    const base = v.variant.startsWith("C-hist") ? "baseline" : "baseline-panels";
    const real = await s.js("(async () => {" + COMMON + "return " + BODIES[base] + "})()");
    await s.shot(`${OUT}/C-${v.name}-baseline-${w}-app.png`);
    const r = await s.js("(async () => {" + COMMON + "return " + BODIES[v.variant] + "})()");
    await s.shot(`${OUT}/C-${v.name}-${v.variant}-${w}-synthetic.png`);
    results.push({ name: v.name, variant: v.variant, w, url: v.url, baseline: real, ...r });
    console.log(v.name, v.variant, w, JSON.stringify({ verified: r.verified, panelH: r.panelH, rows: r.rowHs ?? r.rows, region: r.region && { c: r.region.regionClientH, s: r.region.regionScrollH, cue: !r.region.cueHidden, n: r.region.rowCount, focus: r.region.focusable, innerFocus: r.region.innerFocusable, last: r.region.lastRowReachable }, clipped: r.clipped?.length, doc: r.docOverflowX, base: real.panelH }));
  }
} finally { await s.close(); }
writeFileSync(`${OUT}/C-probe-results-${TAG}.json`, JSON.stringify(results, null, 1));
