// W3-01 commit 4 app capture: the five estate roots at 1440 and 390 for one persisted state.
// Usage: node capture.mjs <out-dir> <state> <base> <screen>=<app-path> ...  -> PNGs + app-<state>.json
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, STATE, BASE, ...SHOTS] = process.argv;
const PORT = 9742;
const SIZES = [[1440, 1000], [390, 900]];
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w301cap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let url = null;
for (let i = 0; i < 80 && !url; i++) {
  try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
  if (!url) await sleep(250);
}
const ws = new WebSocket(url);
await new Promise((r) => ws.addEventListener("open", r));
let n = 0; const pending = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
await send("Page.enable"); await send("Runtime.enable");

const MEASURE = `(async () => {
  await document.fonts.ready;
  const R = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return { top: Math.round(b.top + scrollY), h: Math.round(b.height), w: Math.round(b.width) }; };
  const root = document.querySelector(".estate-page");
  const q = (s) => root.querySelector(s);
  const wrap = root.querySelector("section.panel table")?.parentElement ?? null;
  const first = root.querySelector("section.panel tbody tr td");
  const clipped = Array.from(root.querySelectorAll("section.panel td, section.panel th, section.panel p, .v69-cards *"))
    .filter((el) => el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== "visible" && !el.closest("table")).length;
  const chips = q("[data-estate-state-chips]");
  return {
    pieces: { cards: R(q("[data-estate-cards]")), chips: R(chips), lenses: R(q("[data-estate-lenses]")),
      datebar: R(q("[data-estate-date-bar]")), panel: R(q("section.panel")), limitation: R(q("[data-estate-limitation]")),
      notice: R(q("[data-estate-notice]")) },
    chipScroll: chips ? { client: chips.clientWidth, scroll: chips.scrollWidth } : null,
    lensRows: (() => { const items = Array.from(root.querySelectorAll("[data-estate-lenses] li")); return new Set(items.map((i) => Math.round(i.getBoundingClientRect().top))).size; })(),
    tableScroll: wrap ? { client: wrap.clientWidth, scroll: wrap.scrollWidth, overflowX: getComputedStyle(wrap).overflowX } : null,
    firstColumnPosition: first ? getComputedStyle(first).position : null,
    rows: root.querySelectorAll("section.panel tbody tr").length,
    text: { cutoff: q("[data-estate-cutoff]")?.textContent ?? null, historical: q("[data-estate-historical]")?.textContent ?? null,
      cards: Array.from(root.querySelectorAll("[data-estate-card]")).map((c) => c.textContent.replace(/\\s+/g, " ").trim()),
      siteStates: Array.from(root.querySelectorAll("[data-estate-site-state]")).map((c) => c.getAttribute("data-estate-site-state") + ":" + c.textContent.trim()),
      empty: q("[data-estate-empty]")?.textContent ?? null, partial: q("[data-estate-partial]")?.textContent ?? null,
      limitation: q("[data-estate-limitation]")?.textContent ?? null, refusal: q("[role=alert]")?.textContent ?? null },
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth, clipped,
    height: document.documentElement.scrollHeight };
})()`;

const results = [];
for (const shot of SHOTS) {
  const [screen, path] = [shot.slice(0, shot.indexOf("=")), shot.slice(shot.indexOf("=") + 1)];
  for (const [w, h] of SIZES) {
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
    await send("Page.navigate", { url: `${BASE}${path}` });
    let ready = false;
    for (let i = 0; i < 120 && !ready; i++) {
      await sleep(150);
      ready = await evalv(`!!document.querySelector(".estate-page") && !document.querySelector(".estate-loading")`);
    }
    await sleep(400);
    const m = await evalv(MEASURE);
    const shotPng = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.height, 6000), scale: 1 } });
    const file = `${screen}-${STATE}-${w}-app.png`;
    writeFileSync(join(OUT, file), Buffer.from(shotPng.data, "base64"));
    results.push({ screen, state: STATE, width: w, app_url: `${BASE}${path}`, image: file, ready, ...m });
  }
}
writeFileSync(join(OUT, `app-${STATE}.json`), JSON.stringify({ state: STATE, captured_at: new Date().toISOString(), results }, null, 2));
for (const r of results) {
  const p = Object.entries(r.pieces).filter(([, v]) => v).map(([k, v]) => `${k}=${v.h}`).join(" ");
  console.log(`${r.screen} ${r.width} ready=${r.ready} page=${r.height} ovX=${r.overflowX} clip=${r.clipped} rows=${r.rows} lensRows=${r.lensRows} tbl=${JSON.stringify(r.tableScroll)} sticky=${r.firstColumnPosition} chips=${JSON.stringify(r.chipScroll)} ${p}`);
}
ws.close(); chrome.kill(); process.exit(0);
