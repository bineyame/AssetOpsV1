// Montage full-page PNGs into 3-column tiles (each column a 1300px vertical slice) via headless Chrome screenshot.
import { spawn } from "node:child_process";
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os"; import { join, basename } from "node:path";
import { pathToFileURL } from "node:url";
const [list, outDir] = process.argv.slice(2); const imgs = readFileSync(list, "utf8").split(/\r?\n/).filter(Boolean);
const PORT = 9611; const profile = mkdtempSync(join(tmpdir(), "tile-"));
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", ["--headless=new", "--disable-gpu", "--no-first-run", "--allow-file-access-from-files", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms)); let ws, seq = 0; const pending = new Map();
for (let i = 0; i < 80 && !ws; i++) { try { const pg = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page"); if (pg) { ws = new WebSocket(pg.webSocketDebuggerUrl); await new Promise((a, b) => { ws.addEventListener("open", a); ws.addEventListener("error", b); }); } } catch { ws = undefined; await sleep(250); } }
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) pending.get(m.id)(m); });
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const SL = 1300, GAP = 12, COLS = 3;
for (const p of imgs) {
  const b = readFileSync(p); const w = b.readUInt32BE(16), h = b.readUInt32BE(20);
  const n = Math.ceil(h / SL); const url = pathToFileURL(p).href;
  for (let t = 0; t * COLS < n; t++) {
    const cols = []; for (let c = t * COLS; c < Math.min(n, (t + 1) * COLS); c++) cols.push(c);
    const W = cols.length * w + (cols.length - 1) * GAP;
    const html = `<html><body style="margin:0;background:#f0f;display:flex;gap:${GAP}px;align-items:flex-start">` + cols.map((c) => `<div style="width:${w}px;height:${Math.min(SL, h - c * SL)}px;overflow:hidden;background:#fff"><img src="${url}" style="display:block;margin-top:${-c * SL}px"></div>`).join("") + `</body></html>`;
    const hp = join(outDir, "t.html"); writeFileSync(hp, html);
    await send("Emulation.setDeviceMetricsOverride", { width: W, height: SL, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url: pathToFileURL(hp).href }); await sleep(700);
    const r = await send("Page.captureScreenshot", { format: "png", clip: { x: 0, y: 0, width: W, height: SL, scale: 1 } });
    const tag = p.replace(/.*post-W6-final-recapture[\/]/, "").replace(/[\/]/g, "__").replace(/-app\.png$/, "");
    writeFileSync(join(outDir, `${tag}__t${t}.png`), Buffer.from(r.data, "base64"));
    console.log(tag, w, h, "tile", t, cols.join(","));
  }
}
try { chrome.kill(); } catch {} process.exit(0);
