// W2-06 commit 5 side-by-side capture: app vs v69 mock at 1440 and 390, same selected Site/window/cutoff.
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, REV] = process.argv;
const BASE = "http://localhost:6134";
const PORT = 9735;
const Q = "from=2026-10-06T08:00:00.000000Z&to=2026-10-06T09:05:00.000000Z&known_at=2026-10-06T09:00:00.000000Z";
const FINDING = "00000502-0000-4000-8000-00000000025b";
const SCREENS = [
  { screen: "sessions", app: `/sites/EV-LAB-001/performance/sessions?${Q}`, mock: "#/sessions" },
  { screen: "ev-finding", app: `/sites/EV-LAB-001/findings/${FINDING}?${Q}`, mock: "#/ev-finding" },
];
const SIZES = [[1440, 1000], [390, 900]];
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w206cap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let url = null;
for (let i = 0; i < 60 && !url; i++) {
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
  const panels = Array.from(document.querySelectorAll("main section.panel, .screen section.panel, section.panel")).filter((p, i, a) => a.indexOf(p) === i);
  const out = panels.map((p) => { const h = p.querySelector("h2"); const r = p.getBoundingClientRect();
    return { title: h ? h.textContent.trim() : "", x: Math.round(r.x), y: Math.round(r.y + scrollY), w: Math.round(r.width), h: Math.round(r.height) }; })
    .filter((p) => p.title);
  const table = document.querySelector("section.panel table");
  const cols = table ? Array.from(table.querySelectorAll("thead th")).map((th) => Math.round(th.getBoundingClientRect().width)) : [];
  const scroller = table ? table.parentElement : null;
  const clipped = Array.from(document.querySelectorAll("section.panel td, section.panel th, section.panel p, section.panel dd"))
    .filter((el) => el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== "visible").length;
  return { panels: out, cols, tableScroll: scroller ? { client: scroller.clientWidth, scroll: scroller.scrollWidth } : null,
    rowHeights: table ? Array.from(table.querySelectorAll("tbody tr")).map((tr) => Math.round(tr.getBoundingClientRect().height)) : [],
    overflowX: document.documentElement.scrollWidth - innerWidth, clipped, height: document.documentElement.scrollHeight };
})()`;

const pairs = [];
for (const s of SCREENS) for (const [w, h] of SIZES) {
  const pair = { screen: s.screen, case: "interrupted", viewport: `${w}x${h}`, app_url: `${BASE}${s.app}`, mock_hash: s.mock };
  for (const side of ["app", "mock"]) {
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url: side === "app" ? `${BASE}${s.app}` : `${BASE}/mockups/v69/index.html${s.mock}` });
    for (let i = 0; i < 100; i++) {
      await sleep(150);
      const ready = await evalv(side === "app"
        ? `!!document.querySelector("[data-ev-view] section.panel") && !/Loading/.test(document.querySelector("main")?.textContent ?? "")`
        : `document.querySelectorAll("section.panel").length > 0`);
      if (ready) break;
    }
    if (side === "mock") { await evalv(`(()=>{ if (location.hash !== ${JSON.stringify(s.mock)}) location.hash = ${JSON.stringify(s.mock)}; return true; })()`); await sleep(400); }
    await sleep(300);
    const m = await evalv(MEASURE);
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.height, 6000), scale: 1 } });
    const file = `${s.screen}-interrupted-${w}-${side}.png`;
    writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
    pair[`${side}_image`] = file; pair[side] = m;
  }
  pairs.push(pair);
}
writeFileSync(join(OUT, "evidence.json"), JSON.stringify({ revision: REV, captured_at: new Date().toISOString(), pairs }, null, 2));
for (const p of pairs) {
  console.log(`${p.screen} ${p.viewport} overflowX app=${p.app.overflowX} mock=${p.mock.overflowX} clipped app=${p.app.clipped} scroll=${JSON.stringify(p.app.tableScroll)} cols=${p.app.cols.join("/")} rows=${p.app.rowHeights.join("/")}`);
  for (const a of p.app.panels) { const k = p.mock.panels.find((x) => x.title === a.title); console.log(`  ${a.title}: app ${a.w}x${a.h} mock ${k ? `${k.w}x${k.h} ratio ${(a.h / k.h).toFixed(2)}` : "none"}`); }
  console.log(`  mock titles: ${p.mock.panels.map((x) => x.title).join(" | ")}`);
}
ws.close(); chrome.kill(); process.exit(0);
