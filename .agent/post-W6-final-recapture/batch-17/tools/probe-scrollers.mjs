// CAPTURE-ONLY DOM probe: for each target URL at 1440/390 (details opened for openAll targets), list every horizontally scrolling element and whether it (or a descendant code) is a labelled focusable region.
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const TARGETS = JSON.parse(readFileSync(process.argv[2], "utf8")); const PORT = 9537;
const profile = mkdtempSync(join(tmpdir(), "assetops-probe-"));
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws, seq = 0; const pending = new Map();
for (let i = 0; i < 80 && !ws; i++) { try { const pg = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page"); if (pg) { ws = new WebSocket(pg.webSocketDebuggerUrl); await new Promise((a, b) => { ws.addEventListener("open", a); ws.addEventListener("error", b); }); } } catch { ws = undefined; await sleep(250); } }
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) pending.get(m.id)(m); });
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const js = async (x) => (await send("Runtime.evaluate", { expression: x, returnByValue: true, awaitPromise: true })).result.value;
const out = [];
for (const t of TARGETS) for (const [w, h] of [[1440, 1000], [390, 900]]) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 600 });
  await send("Page.navigate", { url: t.url }); await sleep(3500);
  if (t.openAll) { await js(`document.querySelectorAll("details").forEach(d=>d.open=true)`); await sleep(600); }
  const r = await js(`(() => { const foc = (e) => e.matches("[tabindex]:not([tabindex='-1'])") ; return [...document.querySelectorAll("main *, #root *")].filter((e) => { const s = getComputedStyle(e); return (s.overflowX === "auto" || s.overflowX === "scroll") && e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0; }).map((e) => { const c = e.querySelector("[tabindex]:not([tabindex='-1'])"); return { cls: String(e.className).slice(0, 50), tag: e.tagName, sw: e.scrollWidth, cw: e.clientWidth, focusable: foc(e), role: e.getAttribute("role"), label: (e.getAttribute("aria-label") || e.getAttribute("aria-labelledby") || "").slice(0, 60), inner: c ? { tag: c.tagName, role: c.getAttribute("role"), label: (c.getAttribute("aria-label") || "").slice(0, 60) } : null, text: e.textContent.trim().slice(0, 50) }; }); })()`);
  out.push({ id: t.id, case: t.case, width: w, scrollers: r });
  console.log(t.id, t.case, w, r.length, r.filter((x) => !(x.focusable || x.inner)).length, "unfocusable");
}
writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
try { chrome.kill(); } catch {}
process.exit(0);
