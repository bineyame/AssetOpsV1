// Capture-only: load a page, put a 160-char synthetic title in the cold Findings rows (browser only), dump per-cell sizes.
import { spawn } from "node:child_process"; import { mkdtempSync } from "node:fs"; import { tmpdir } from "node:os"; import { join } from "node:path";
const [URL_, W] = process.argv.slice(2); const PORT = 9597;
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", ["--headless=new", "--disable-gpu", `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "w2coldrc-cell-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms)); let ws, seq = 0; const pend = new Map();
for (let i = 0; i < 80 && !ws; i++) { try { const p = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page"); ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((r) => ws.addEventListener("open", r)); } catch { ws = undefined; await sleep(250); } }
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const send = (method, params = {}) => new Promise((res) => { seq++; pend.set(seq, res); ws.send(JSON.stringify({ id: seq, method, params })); });
const js = async (e) => (await send("Runtime.evaluate", { expression: e, returnByValue: true, awaitPromise: true })).result.result.value;
await send("Emulation.setDeviceMetricsOverride", { width: Number(W), height: 1000, deviceScaleFactor: 1, mobile: Number(W) < 600 });
await send("Page.navigate", { url: URL_ });
for (let i = 0; i < 200; i++) { if (await js(`!!document.querySelector("tr[data-cold-finding-row]")`)) break; await sleep(150); } await sleep(1000);
console.log(JSON.stringify(await js(String.raw`(() => { const tr = document.querySelector("tr[data-cold-finding-row]");
  const real = [...tr.children].map((c) => ({ w: Math.round(c.getBoundingClientRect().width), h: Math.round(c.getBoundingClientRect().height), t: c.textContent.trim().slice(0, 50), lh: getComputedStyle(c).lineHeight, fs: getComputedStyle(c).fontSize, pad: getComputedStyle(c).paddingTop }));
  tr.children[0].querySelector("a").textContent = ("SYN " + "Synthetic layout probe text that wraps across several lines ".repeat(4)).slice(0, 160);
  const syn = [...tr.children].map((c) => ({ w: Math.round(c.getBoundingClientRect().width), h: Math.round(c.getBoundingClientRect().height), inner: [...c.children].map((k) => k.tagName + ":" + Math.round(k.getBoundingClientRect().height)).join(",") }));
  const head = [...document.querySelectorAll("table[aria-labelledby='cold-findings-heading'] thead th")].map((c) => Math.round(c.getBoundingClientRect().width));
  return { real, syn, head }; })()`)));
ws.close(); chrome.kill();
