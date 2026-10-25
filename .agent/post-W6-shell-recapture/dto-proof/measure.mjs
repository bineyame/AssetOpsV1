/* DTO render proof measurement (Q23). Headless Chrome CDP on 18109 against the harness Vite on 18108.
   Usage: node measure.mjs  -> results.json, console.log.json, PNGs in this folder. */
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const OUT = dirname(fileURLToPath(import.meta.url));
const PORT = 18109, BASE = "http://127.0.0.1:18108";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const profile = mkdtempSync(join(tmpdir(), "dto-proof-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
writeFileSync(join(OUT, "chrome.pid"), String(chrome.pid));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws, seq = 0; const pending = new Map(); const logs = [];
for (let i = 0; i < 80; i++) { try { const p = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page"); if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((a, b) => { ws.onopen = a; ws.onerror = b; }); break; } } catch {} await sleep(250); }
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  else if (m.method === "Runtime.exceptionThrown") logs.push({ ex: m.params.exceptionDetails.exception?.description?.slice(0, 300) });
  else if (m.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(m.params.type)) logs.push({ [m.params.type]: m.params.args.map((a) => a.value ?? a.description).join(" ").slice(0, 300) });
};
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; pending.set(id, (m) => (m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result))); ws.send(JSON.stringify({ id, method, params })); });
const js = async (e) => (await send("Runtime.evaluate", { expression: e, returnByValue: true, awaitPromise: true })).result.value;
await send("Page.enable"); await send("Runtime.enable");

const SITE = "KLG-014";
const WINDOW = "from=2026-09-22T00:00:00Z&to=2026-09-23T00:00:00Z";
const id = (n) => `3f6b2a10-0000-4000-8000-00000000000${n}`;
const EV = `/sites/${SITE}/evidence?${WINDOW}&view=analysis`;
const MINI = "Accepted records behind the conclusions";
const CASES = [
  { proof: "mini-evidence-analysis", state: "closed, record 5 opened (all five rows shown)", url: `${EV}&record=${id(5)}`, heading: MINI, caps: { 1440: 1200, 390: 1800 }, open: false, file: "mini-closed-r5" },
  { proof: "mini-evidence-analysis", state: "closed, record 1 opened (3-row preview)", url: `${EV}&record=${id(1)}`, heading: MINI, caps: { 1440: 1200, 390: 1800 }, open: false, file: "mini-closed-r1" },
  { proof: "mini-evidence-analysis", state: "all disclosures open + show all, record 5 opened (cap-exempt)", url: `${EV}&record=${id(5)}`, heading: MINI, caps: null, open: true, file: "mini-allopen-r5" },
  { proof: "foundation-identity", state: "closed (ten rows, five 160-char values)", url: `/sites/${SITE}/foundation`, heading: "Identity and operating obligations", caps: { 1440: 850, 390: 1050 }, open: false, file: "foundation-closed" },
];

function measure(heading, open) {
  return async function () {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    let h = null;
    for (let i = 0; i < 80 && !h; i++) { h = [...document.querySelectorAll("h2")].find((e) => e.textContent.trim() === heading); if (!h) await sleep(200); }
    if (!h) return { error: "panel heading not found", body: document.body.innerText.slice(0, 400) };
    await sleep(800);
    const panel = h.closest("section");
    if (open) {
      for (let k = 0; k < 4; k++) {
        panel.querySelectorAll("details").forEach((d) => (d.open = true));
        const t = panel.querySelector("[data-evidence-records-toggle='preview']"); if (t) t.click();
        await sleep(300);
      }
    }
    await sleep(500);
    const pr = panel.getBoundingClientRect();
    const clipped = [], innerScroll = [];
    const desc = (e) => e.tagName.toLowerCase() + (typeof e.className === "string" && e.className.trim() ? "." + e.className.trim().split(/\s+/).join(".") : "") + " " + (e.textContent || "").trim().slice(0, 50);
    const scroller = (v) => v === "auto" || v === "scroll";
    const hides = (v) => v === "hidden" || v === "clip";
    for (const e of panel.querySelectorAll("*")) {
      const r = e.getBoundingClientRect(); if (r.width <= 1 || r.height <= 1) continue;
      const cs = getComputedStyle(e);
      if (scroller(cs.overflowX) || scroller(cs.overflowY)) { if (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1) innerScroll.push({ el: desc(e), sw: e.scrollWidth, cw: e.clientWidth, sh: e.scrollHeight, ch: e.clientHeight }); }
      if ((hides(cs.overflowX) && e.scrollWidth > e.clientWidth + 1) || (hides(cs.overflowY) && e.scrollHeight > e.clientHeight + 1)) clipped.push({ el: desc(e), why: "overflow hidden", sw: e.scrollWidth, cw: e.clientWidth, sh: e.scrollHeight, ch: e.clientHeight });
      else if (cs.textOverflow === "ellipsis" && e.scrollWidth > e.clientWidth + 1) clipped.push({ el: desc(e), why: "ellipsis" });
      let inScroll = false; for (let a = e.parentElement; a && a !== panel; a = a.parentElement) { if (scroller(getComputedStyle(a).overflowX)) { inScroll = true; break; } }
      if (!inScroll && (r.right > pr.right + 1 || r.left < pr.left - 1)) clipped.push({ el: desc(e), why: "outside panel box", left: Math.round(r.left), right: Math.round(r.right), panelRight: Math.round(pr.right) });
    }
    const body = panel.querySelector(".panel__body") || panel;
    const parts = [...body.children].map((c) => ({ part: desc(c), h: Math.round(c.getBoundingClientRect().height) }));
    const rows = [...panel.querySelectorAll("tr, dl > div, li")].filter((r) => r.getBoundingClientRect().height > 0).map((r) => ({ row: (r.textContent || "").trim().slice(0, 40), h: Math.round(r.getBoundingClientRect().height) }));
    const de = document.documentElement;
    return {
      panel_h: Math.round(pr.height), overflowX: de.scrollWidth - de.clientWidth, pageH: de.scrollHeight,
      pageScrollable: de.scrollHeight > de.clientHeight && getComputedStyle(document.body).overflowY !== "hidden" && getComputedStyle(de).overflowY !== "hidden",
      openDetails: panel.querySelectorAll("details[open]").length, details: panel.querySelectorAll("details").length,
      visibleRecordRows: panel.querySelectorAll("tr[data-evidence-record]:not([hidden])").length, recordDetail: !!panel.querySelector("[data-record-detail]"),
      clipped, innerScroll, parts, rows,
      recordBody: (() => { const b = panel.querySelector(".evidence-record-view__body"); if (!b) return null;
        const cs = getComputedStyle(b); const before = b.scrollTop; b.scrollTop = 120; const moved = b.scrollTop > before; b.scrollTop = before;
        return { scrollHeight: b.scrollHeight, clientHeight: b.clientHeight, h: Math.round(b.getBoundingClientRect().height), overflowY: cs.overflowY, maxHeight: cs.maxHeight, overflowing: b.scrollHeight > b.clientHeight + 1, scrolls: moved || b.scrollHeight <= b.clientHeight + 1, tabindex: b.getAttribute("tabindex") }; })(),
      wideRows: panel.querySelectorAll("[data-key-value-wide]").length,
    };
  };
}

const results = [];
for (const c of CASES) for (const [w, hgt] of [[1440, 1000], [390, 900]]) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: hgt, deviceScaleFactor: 1, mobile: w < 500 });
  await send("Page.navigate", { url: BASE + c.url });
  await sleep(1500);
  const m = await js(`(${measure.toString()})(${JSON.stringify(c.heading)}, ${c.open})()`);
  const cap = c.caps ? c.caps[w] : null;
  const pass = m.error ? false : cap === null ? m.clipped.length === 0 && m.pageScrollable && m.overflowX <= 0 : m.panel_h <= cap && m.clipped.length === 0 && m.overflowX <= 0;
  const row = { revision: "e9b1b8d9", proof: c.proof, width: w, state: c.state, panel_h: m.panel_h ?? null, cap, pass, overflowX: m.overflowX ?? null, clipped: m.clipped ?? null, inner_scroll: m.recordBody ?? null, url: c.url, screenshot: `${c.file}-${w}.png`, detail: m };
  const lm = await send("Page.getLayoutMetrics");
  const H = Math.ceil(lm.cssContentSize.height);
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: H, scale: 1 } });
  writeFileSync(join(OUT, row.screenshot), Buffer.from(shot.data, "base64"));
  results.push(row);
  console.log(c.file, w, m.error ? m.error + " " + m.body : `h=${m.panel_h} cap=${cap} pass=${pass} ox=${m.overflowX} clipped=${m.clipped.length} scroll=${m.innerScroll.length} rows=${m.visibleRecordRows} rec=${m.recordDetail} open=${m.openDetails}/${m.details} pageScrollable=${m.pageScrollable} body=${JSON.stringify(m.recordBody)} wide=${m.wideRows}`);
}
writeFileSync(join(OUT, "results.json"), JSON.stringify({ kind: "DTO RENDER PROOF - not an app screenshot (post-W6 shell Q23/Q24)", results }, null, 1));
writeFileSync(join(OUT, "console.log.json"), JSON.stringify(logs, null, 1));
ws.close(); chrome.kill(); process.exit(0);
