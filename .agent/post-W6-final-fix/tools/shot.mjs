// Capture-only: navigate, screenshot at 1440x1000 and 390x900, measure DOM. Never posts or mutates.
// node shot.mjs <out-dir> <targets.json>   targets: [{name, url, focus?:css, open?:css(details summary to open), evals?:{k:js}}]
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const [OUT, TF] = process.argv.slice(2);
const TARGETS = JSON.parse(readFileSync(TF, "utf8"));
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9451);
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-pwfx-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
console.log(`chrome pid ${chrome.pid}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws, seq = 0; const pend = new Map();
async function connect() {
  for (let i = 0; i < 80; i++) {
    try {
      const p = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
      if (p?.webSocketDebuggerUrl) { const s = new WebSocket(p.webSocketDebuggerUrl); await new Promise((a, b) => { s.addEventListener("open", a); s.addEventListener("error", b); }); return s; }
    } catch {}
    await sleep(250);
  }
  throw new Error("no chrome");
}
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; const t = setTimeout(() => rej(new Error("timeout " + method)), 60000); pend.set(id, (m) => { clearTimeout(t); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }); ws.send(JSON.stringify({ id, method, params })); });
const js = async (e) => { const r = await send("Runtime.evaluate", { expression: e, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) return { error: r.exceptionDetails.text + " " + (r.exceptionDetails.exception?.description ?? "").slice(0, 200) }; return r.result.value; };
const MEASURE = String.raw`(() => {
  const txt = (e) => (e?.textContent ?? "").replace(/\s+/g, " ").trim();
  const tables = [...document.querySelectorAll("main table")].map((t) => {
    const th = t.querySelector("th"); const cols = [...t.querySelectorAll("colgroup col")].map((c) => c.className);
    const sc = t.closest("[class*=scroll],[class*=table-wrap]") ; const w = t.parentElement;
    return { cls: String(t.className).slice(0, 50), cols: cols.slice(0, 3), firstTh: th ? { text: txt(th).slice(0, 30), w: Math.round(th.getBoundingClientRect().width) } : null,
      tableW: Math.round(t.getBoundingClientRect().width), wrapCls: String(w?.className).slice(0, 50), wrapOverflowX: w ? getComputedStyle(w).overflowX : null, wrapSW: w?.scrollWidth, wrapCW: w?.clientWidth };
  });
  return { h1: txt(document.querySelector("main h1")), titles: [...document.querySelectorAll("main h2")].map(txt).slice(0, 14),
    docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth, innerWidth: innerWidth, tables,
    mainText: txt(document.querySelector("main")).slice(0, 1500) };
})()`;
const sleepSettle = async () => { for (let i = 0; i < 40; i++) { const a = await js(`document.querySelector("main h1") ? document.body.innerText.length : -1`); await sleep(700); const b = await js(`document.querySelector("main h1") ? document.body.innerText.length : -1`); if (a > 0 && a === b && !(await js(`/Loading the/.test(document.querySelector("main")?.innerText??"")`))) return; } };
ws = await connect();
ws.addEventListener("message", (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
await send("Page.enable"); await send("Runtime.enable");
const results = [];
for (const t of TARGETS) {
  for (const [label, w, h] of [["1440", 1440, 1000], ["390", 390, 900]]) {
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url: t.url }); await sleep(1500); await sleepSettle();
    if (t.open) await js(`document.querySelectorAll(${JSON.stringify(t.open)}).forEach((d)=>{ d.open = true; })`);
    if (t.pre) { await js(t.pre); }
    for (let k = 0; k < (t.tab ?? 0); k++) { for (const type of ["rawKeyDown", "keyUp"]) await send("Input.dispatchKeyEvent", { type, key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 }); await sleep(200); }
    if (t.focus) { await js(`document.querySelector(${JSON.stringify(t.focus)})?.focus()`); await sleep(300); }
    const m = await js(MEASURE);
    const extra = {}; for (const [k, e] of Object.entries(t.evals ?? {})) extra[k] = await js(e);
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
    const file = `${t.name}-${label}.png`; writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
    results.push({ name: t.name, viewport: label, url: t.url, image: file, measure: m, extra });
    console.log(`${t.name} ${label}: h1=${JSON.stringify(m.h1)} docOverflowX=${m.docOverflowX}`);
  }
}
writeFileSync(join(OUT, "evidence.json"), JSON.stringify({ revision: process.env.AUDIT_REVISION, captured: new Date().toISOString(), results }, null, 1));
try { await send("Browser.close"); } catch {}
chrome.kill(); process.exit(0);
