// W3-02 commit 4 app capture: the mounted estate Financials root at 1440 and 390 (adapted from the commit-2 capture.mjs).
// Usage: node capture-financials.mjs <out-dir> <state> <base> <app-path>  -> financials-<state>-<w>-app.png + app-financials-<state>.json
// Stops only the Chrome it started (finally block), never other Chrome processes.
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, STATE, BASE, PATH] = process.argv;
const PORT = 9520;
const SIZES = [[1440, 1000], [390, 900]];
const MAX = { 1440: { status: 68, register: 293, notice: 66, aggregation: 123 }, 390: { status: 95, register: 448, notice: 102, aggregation: 187 } };
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w302fcap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
try {
  let url = null;
  for (let i = 0; i < 80 && !url; i++) {
    try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
    if (!url) await sleep(250);
  }
  ws = new WebSocket(url);
  await new Promise((r) => ws.addEventListener("open", r));
  let n = 0; const pending = new Map();
  ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
  const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
  await send("Page.enable"); await send("Runtime.enable");

  const MEASURE = `(async () => {
    await document.fonts.ready;
    const R = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return { top: Math.round(b.top + scrollY), h: Math.round(b.height), w: Math.round(b.width) }; };
    const root = document.querySelector('[data-estate-root="financials"]');
    const panels = Array.from(root.querySelectorAll("section.panel"));
    const panel = (t) => panels.find((p) => p.querySelector("h2")?.textContent.trim() === t) ?? null;
    const reg = panel("Consequence register"), agg = panel("Aggregation rule");
    const tbl = (p) => { const s = p?.querySelector(".data-table__scroll"); return s ? { client: s.clientWidth, scroll: s.scrollWidth, clientH: s.clientHeight, scrollH: s.scrollHeight, rows: s.querySelectorAll("tbody tr").length, maxH: getComputedStyle(s).maxHeight, headH: Math.round(s.querySelector("thead").getBoundingClientRect().height), rowHs: Array.from(s.querySelectorAll("tbody tr")).map((r) => Math.round(r.getBoundingClientRect().height)) } : null; };
    const list = (e) => e ? { clientH: e.clientHeight, scrollH: e.scrollHeight, items: e.children.length } : null;
    return {
      h1: document.querySelector("h1")?.textContent.trim() ?? null,
      eyebrow: document.querySelector("header.page-header .page-header__eyebrow")?.textContent ?? null,
      main: document.querySelector("main")?.getAttribute("aria-label") ?? null,
      railCurrent: document.querySelector('nav[aria-label="Operator routes"] [aria-current="page"]')?.textContent ?? null,
      pieces: { status: R(root.querySelector("[data-estate-status]")), register: R(reg), notice: R(root.querySelector("[data-estate-notice]")), aggregation: R(agg) },
      registerTable: tbl(reg), results: list(root.querySelector("[data-estate-results]")),
      panelTitles: panels.map((p) => p.querySelector("h2")?.textContent.trim()),
      notes: Array.from(root.querySelectorAll("[data-estate-note]")).map((n) => n.textContent.replace(/\\s+/g, " ").trim()),
      groupStates: Array.from(root.querySelectorAll("[data-estate-group-state]")).map((n) => n.textContent.trim()),
      docScrollW: document.documentElement.scrollWidth, docClientW: document.documentElement.clientWidth,
      refusal: root.querySelector("[role=alert]")?.textContent ?? null,
      aggSummary: (() => { const d = agg?.querySelector("[data-disclosure='estate-financials-results']"); const sm = d?.querySelector(":scope > summary"); const t = sm?.querySelector("[data-estate-summary-text]"); if (!sm) return null; const cs = getComputedStyle(sm); const tr = t.getBoundingClientRect(); return { open: d.open, text: t.textContent, name: sm.textContent.replace(/\\s+/g, " ").trim(), h: Math.round(sm.getBoundingClientRect().height), fontSize: cs.fontSize, lineHeight: cs.lineHeight, lines: Math.round(tr.height / parseFloat(cs.lineHeight)), wrapperH: Math.round(agg.querySelector("[data-estate-aggregation-summary]").getBoundingClientRect().height + parseFloat(getComputedStyle(agg.querySelector("[data-estate-aggregation-summary]")).marginTop)) }; })(),
      aggParts: agg ? (() => { const cs = getComputedStyle(agg); const hd = agg.querySelector(".panel__header") ?? agg.querySelector("h2"); const pr = agg.querySelector(".estate-financials-prose"); const pcs = getComputedStyle(pr); return { pad: cs.paddingTop + "/" + cs.paddingBottom, header: Math.round(hd.getBoundingClientRect().height), headerMb: getComputedStyle(hd).marginBottom, prose: Math.round(pr.getBoundingClientRect().height), proseLh: pcs.lineHeight, proseFs: pcs.fontSize }; })() : null,
      proseFont: agg ?getComputedStyle(agg.querySelector(".estate-financials-prose")).fontSize : null,
      reach: agg ? { groups: agg.querySelectorAll("[data-estate-group]").length, diagnostics: agg.querySelectorAll("[data-estate-diagnostic]").length, exclusions: agg.querySelectorAll("[data-estate-exclusion]").length, visible: Array.from(agg.querySelectorAll("[data-estate-group],[data-estate-diagnostic],[data-estate-exclusion],[data-estate-note]")).filter((e) => e.checkVisibility()).length, chipFont: (() => { const c = agg.querySelector(".estate-chip"); return c ? getComputedStyle(c).fontSize + "/" + getComputedStyle(c).whiteSpace : null; })() } : null,
      height: document.documentElement.scrollHeight };
  })()`;

  const results = [];
  for (const [w, h] of SIZES) {
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
    await send("Page.navigate", { url: `${BASE}${PATH}` });
    let ready = false;
    for (let i = 0; i < 160 && !ready; i++) {
      await sleep(150);
      ready = await evalv(`!!document.querySelector('[data-estate-root="financials"]') && !document.querySelector("[data-estate-loading]")`);
    }
    await sleep(500);
    const m = await evalv(MEASURE);
    const over = Object.entries(m.pieces).filter(([k, v]) => v && v.h > MAX[w][k]).map(([k, v]) => `${k} ${v.h}>${MAX[w][k]}`);
    const shotPng = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.height, 6000), scale: 1 } });
    const file = `financials-${STATE}-${w}-app.png`;
    writeFileSync(join(OUT, file), Buffer.from(shotPng.data, "base64"));
    // Ruling c4: open the results summary and every nested exclusions disclosure, then re-measure and re-shoot.
    await evalv(`(() => { const a = Array.from(document.querySelectorAll("section.panel")).find((p) => p.querySelector("h2")?.textContent.trim() === "Aggregation rule"); a?.querySelectorAll("details").forEach((d) => { d.open = true; }); return true; })()`);
    await sleep(300);
    const o = await evalv(MEASURE);
    const openShot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(o.height, 6000), scale: 1 } });
    const openFile = `financials-${STATE}-${w}-open-app.png`;
    writeFileSync(join(OUT, openFile), Buffer.from(openShot.data, "base64"));
    const opened = { image: openFile, aggregation: o.pieces.aggregation, results: o.results, aggSummary: o.aggSummary, reach: o.reach, docScrollW: o.docScrollW, docClientW: o.docClientW };
    results.push({ width: w, app_url: `${BASE}${PATH}`, image: file, ready, maxima: MAX[w], over, ...m, opened });
  }
  // Ruling c4-q3: the honest capture limitation, recorded with the capture.
  const limitation = "Three Sites are in scope; two have selected consequence lines. The mini-grid has no selected consequence revision for this window, so no mini-grid amount appears in the register. The two-row register height is not a three-row mock-density proof; the 293/448 px register maxima still apply.";
  writeFileSync(join(OUT, `app-financials-${STATE}.json`), JSON.stringify({ state: STATE, captured_at: new Date().toISOString(), limitation, results }, null, 2));
  for (const r of results) {
    const p = Object.entries(r.pieces).map(([k, v]) => `${k}=${v ? v.h : "absent"}`).join(" ");
    console.log(`${r.width} ready=${r.ready} h1=${r.h1} main=${r.main} rail=${r.railCurrent} doc=${r.docScrollW}/${r.docClientW} ${p} reg=${JSON.stringify(r.registerTable)} results=${JSON.stringify(r.results)} groups=${JSON.stringify(r.groupStates)} notes=${JSON.stringify(r.notes)} over=[${r.over}] refusal=${r.refusal}`);
    console.log(`  parts=${JSON.stringify(r.aggParts)} closed summary=${JSON.stringify(r.aggSummary)} prose=${r.proseFont} reach=${JSON.stringify(r.reach)}`);
    console.log(`  open agg=${r.opened.aggregation?.h} results=${JSON.stringify(r.opened.results)} reach=${JSON.stringify(r.opened.reach)} doc=${r.opened.docScrollW}/${r.opened.docClientW}`);
  }
} finally {
  try { ws?.close(); } catch {}
  chrome.kill();
}
process.exit(0);
