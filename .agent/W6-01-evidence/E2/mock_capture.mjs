// W6-01e E2: the v69 mock `oprecords` screen at 1440 and 390 (file URL), for the side-by-side comparison.
// Usage: node mock_capture.mjs <out-dir> <file-url-of-index.html>
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const [OUT, INDEX] = process.argv.slice(2);
const PORT = 9782;
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", ["--headless=new", "--disable-gpu", "--no-first-run",
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "w601e2mock-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let url = null;
for (let i = 0; i < 80 && !url; i++) { try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {} if (!url) await sleep(250); }
const ws = new WebSocket(url); await new Promise((r) => ws.addEventListener("open", r));
let n = 0; const pending = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res) => { const id = ++n; pending.set(id, (m) => res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
await send("Page.enable"); await send("Runtime.enable");
const out = [];
for (const [w, h] of [[1440, 1000], [390, 900]]) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
  await send("Page.navigate", { url: `${INDEX}#/oprecords` }); await sleep(1500);
  const m = (await send("Runtime.evaluate", { returnByValue: true, expression: `(() => ({ page_height: document.documentElement.scrollHeight,
    panels: Array.from(document.querySelectorAll(".panel")).map((p) => ({ title: p.querySelector("h2")?.textContent, h: Math.round(p.getBoundingClientRect().height) })),
    chips: Math.round(document.querySelector(".chips")?.getBoundingClientRect().height ?? 0), cards: Math.round(document.querySelector(".cards")?.getBoundingClientRect().height ?? 0),
    doc: [document.documentElement.scrollWidth, document.documentElement.clientWidth] }))()` })).result.value;
  const png = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.page_height, 8000), scale: 1 } });
  writeFileSync(join(OUT, `mock-oprecords-${w}.png`), Buffer.from(png.data, "base64"));
  out.push({ width: w, ...m });
}
writeFileSync(join(OUT, "mock-oprecords.json"), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out));
ws.close(); chrome.kill();
