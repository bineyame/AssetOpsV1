// W6-01b B3 (P-B3-2): the Evidence root at 1440 and 390 with its live `Preventive plan →` example, then the click
// through to the Preventive view (1440) to prove the destination query. Usage: node evidence_capture.mjs <out> <base> <path>
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const [OUT, BASE, PATH] = process.argv.slice(2);
const PORT = 9773;
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", ["--headless=new", "--disable-gpu", "--no-first-run",
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "w601b3ev-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let url = null;
for (let i = 0; i < 80 && !url; i++) { try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {} if (!url) await sleep(250); }
const ws = new WebSocket(url); await new Promise((r) => ws.addEventListener("open", r));
let n = 0; const pending = new Map(); const api = [];
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); }
  if (m.method === "Network.responseReceived" && m.params.response.url.includes("/api/")) api.push({ url: m.params.response.url.replace(/^https?:\/\/[^/]+/, ""), status: m.params.response.status }); });
const send = (method, params = {}) => new Promise((res) => { const id = ++n; pending.set(id, res); ws.send(JSON.stringify({ id, method, params })); });
const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
await send("Page.enable"); await send("Network.enable");
const results = [];
async function shot(name, w, h) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 }); await sleep(600);
  const m = await evalv(`(() => { const a = document.querySelector("[data-estate-example-live]"); const rows = Array.from(document.querySelectorAll(".global-work tbody tr"));
    return { page_height: document.documentElement.scrollHeight, doc: [document.documentElement.scrollWidth, document.documentElement.clientWidth],
      example: a ? [a.textContent, a.getAttribute("href")] : null, examples: document.querySelector("[data-estate-examples]")?.textContent ?? null,
      location: location.pathname + location.search, preventive_rows: rows.map((r) => r.querySelector("[data-global-work-title]")?.textContent ?? ""),
      status: document.querySelector("[data-global-work-status]")?.textContent ?? null }; })()`);
  const png = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.page_height, 6000), scale: 1 } });
  writeFileSync(join(OUT, `${name}-${w}.png`), Buffer.from(png.data, "base64"));
  results.push({ name, width: w, image: `${name}-${w}.png`, ...m, api: [...api] }); api.length = 0;
}
async function wait(cond) { for (let i = 0; i < 160; i++) { await sleep(150); if (await evalv(cond)) return true; } return false; }
for (const [w, h] of [[1440, 1000], [390, 900]]) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
  await send("Page.navigate", { url: `${BASE}${PATH}` });
  await wait(`!!document.querySelector("[data-estate-examples]")`);
  await shot("evidence_root", w, h);
}
await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
await evalv(`document.querySelector("[data-estate-example-live]").click(), true`);
await wait(`!!document.querySelector(".global-work") && !document.querySelector("[data-global-work-loading]")`);
await shot("evidence_to_preventive", 1440, 1000);
writeFileSync(join(OUT, "app-evidence_root.json"), JSON.stringify({ captured_at: new Date().toISOString(), results }, null, 2));
for (const r of results) console.log(r.name, r.width, JSON.stringify(r.example), r.location, JSON.stringify(r.preventive_rows), JSON.stringify(r.api.map((a) => a.status)), r.doc);
ws.close(); chrome.kill();
