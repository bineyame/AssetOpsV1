// Capture-only CDP helper (post-W6 W1-b recapture; copied from W1-a fix probe, mobile flag per width, send exported).
// Loads the URL, waits for h1, optionally evaluates a JS file's expression, prints JSON.
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9523);
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
export async function session() {
  const profile = mkdtempSync(join(tmpdir(), "assetops-w1brc-cdp-"));
  const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  let ws;
  for (let i = 0; i < 80; i += 1) {
    try {
      const page = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
      if (page?.webSocketDebuggerUrl) { ws = new WebSocket(page.webSocketDebuggerUrl); await new Promise((a, b) => { ws.addEventListener("open", a); ws.addEventListener("error", b); }); break; }
    } catch {}
    await sleep(250);
  }
  let seq = 0; const pending = new Map();
  ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const send = (method, params = {}) => new Promise((res, rej) => { seq += 1; const id = seq; const t = setTimeout(() => rej(new Error("timeout " + method)), 60000); pending.set(id, (m) => { clearTimeout(t); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }); ws.send(JSON.stringify({ id, method, params })); });
  const js = async (expression) => { const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 600)); return r.result.value; };
  async function open(url, width, height = 1000) {
    await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
    await send("Page.navigate", { url });
    for (let i = 0; i < 120; i += 1) { await sleep(500); const ok = await js(`(() => { const h=document.querySelector('main h1, h1'); return !!h && !document.querySelector('[aria-busy=true]') && document.querySelectorAll('section.panel').length>0 && ![...document.querySelectorAll('main p')].some((p) => /^Loading [^.]+\.$/.test(p.textContent.trim())); })()`).catch(() => false); if (ok) break; }
    await sleep(1200);
  }
  async function shot(path) { const r = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true }); writeFileSync(path, Buffer.from(r.data, "base64")); }
  const close = async () => { try { await send("Browser.close"); } catch {} try { chrome.kill(); } catch {} };
  return { open, js, shot, close, send, chromePid: chrome.pid };
}
