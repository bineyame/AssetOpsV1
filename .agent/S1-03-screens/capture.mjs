// S1-03 side-by-side capture: drives installed Chrome over CDP (no deps).
// node .agent/S1-03-screens/capture.mjs <outDir> <name>=<url> ...
// Each target is captured at 1440x900 and 390x844, first viewport and full page.
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9341;
const [outDir, ...targets] = process.argv.slice(2);
const profile = mkdtempSync(join(tmpdir(), "s103-cdp-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "--hide-scrollbars", "--no-first-run", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
for (let i = 0; i < 50; i++) { try { const l = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json(); const p = l.find((t) => t.type === "page"); if (p) { ws = p.webSocketDebuggerUrl; break; } } catch {} await sleep(200); }
const sock = new WebSocket(ws); await new Promise((r) => sock.addEventListener("open", r));
let id = 0; const pending = new Map();
sock.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); sock.send(JSON.stringify({ id: i, method, params })); });
await send("Page.enable"); await send("Runtime.enable");
const sizes = [["1440", 1440, 900], ["390", 390, 844]];
for (const t of targets) {
  const eq = t.indexOf("="); const name = t.slice(0, eq); const url = t.slice(eq + 1);
  for (const [tag, w, h] of sizes) {
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url: "about:blank" }); await sleep(200);
    await send("Page.navigate", { url }); await sleep(Number(process.env.WAIT ?? 3500));
    const metrics = await send("Runtime.evaluate", { expression: "JSON.stringify({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,sh:document.documentElement.scrollHeight})", returnByValue: true });
    let m = JSON.parse(metrics.result.result.value);
    if (m.sw > m.cw) {
      const off = await send("Runtime.evaluate", { returnByValue: true, expression: `JSON.stringify([...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.right>document.documentElement.clientWidth+1 && !e.closest('.data-table__scroll,.sld__scroll')}).slice(0,8).map(e=>e.tagName+'.'+e.className+' '+Math.round(e.getBoundingClientRect().right)+' '+(e.textContent||'').slice(0,40)))` });
      console.log("  overflowing:", off.result.result.value);
    }
    const vp = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(outDir, `${name}-${tag}-viewport.png`), Buffer.from(vp.result.data, "base64"));
    // The operator shell can scroll inside its own frame, so the document height
    // is not the page height: grow the viewport to the tallest scroller instead.
    const tall = await send("Runtime.evaluate", { returnByValue: true, expression: "Math.max(document.documentElement.scrollHeight, ...[...document.querySelectorAll('body *')].filter(e => /(auto|scroll)/.test(getComputedStyle(e).overflowY) && e.scrollHeight > e.clientHeight).map(e => e.scrollHeight + e.getBoundingClientRect().top))" });
    const fullH = Math.min(Math.ceil(tall.result.result.value), 16000);
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: fullH, deviceScaleFactor: 1, mobile: false });
    await sleep(800);
    const full = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(outDir, `${name}-${tag}-full.png`), Buffer.from(full.result.data, "base64"));
    m.sh = fullH;
    console.log(`${name} ${tag}: scrollWidth ${m.sw} clientWidth ${m.cw} height ${m.sh}${m.sw > m.cw ? " HORIZONTAL OVERFLOW" : ""}`);
  }
}
sock.close(); chrome.kill(); await sleep(300); try { rmSync(profile, { recursive: true, force: true }); } catch {}
