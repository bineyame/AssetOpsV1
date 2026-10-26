/**
 * Post-W6 audit batch 17 capture wrapper (copied from batch 12, itself from batch 10) (CAPTURE-ONLY). Derived from tools/w1-fidelity-evidence.mjs (same
 * Chrome-over-CDP pattern, same panelStructure.ts title rule, same width guard). It only navigates to the given
 * URLs, waits for stable content, takes screenshots and measures the DOM. It never clicks, types, posts or
 * mutates anything; it adds per-panel structure (rows, columns, chips, links, disclosures), typography, colour,
 * shell-header, tab-row, clipped-text and scroll-container measurements to each pair.
 *
 *   node capture-b17.mjs <out-dir> <targets.json>
 * targets.json: [{ "id": "<mock id>", "case": "<case>", "url": "<app url>", "mock": "<mock hash id, default id>" }]
 * Optional per-target "openAll": true opens every <details> disclosure (viewer-only DOM toggle, no request, no
 * mutation) before measuring, for the all-disclosures-open state.
 * Environment: ASSETOPS_CDP_PORT (default 9527), AUDIT_REVISION.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const { widthGuard } = await import(pathToFileURL(resolve(here, "../../../tools/evidence-checks.mjs")).href);
const OUT = process.argv[2];
const TARGETS = JSON.parse(readFileSync(process.argv[3], "utf8"));
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9527);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [["1440", 1440, 1000], ["390", 390, 900]];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-w5ev-caps-cdp-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
console.log(`chrome pid ${chrome.pid}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
function claim(name, ok, detail) {
  results.push({ name, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail === undefined ? "" : `  ${JSON.stringify(detail)}`}`);
}
async function connect() {
  for (let i = 0; i < 80; i += 1) {
    try {
      const page = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
      if (page?.webSocketDebuggerUrl) {
        const socket = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => { socket.addEventListener("open", res); socket.addEventListener("error", rej); });
        return socket;
      }
    } catch { /* not up yet */ }
    await sleep(250);
  }
  throw new Error("Chrome did not expose a page target");
}
let ws; let seq = 0; let consoleErrors = []; const pending = new Map();
function send(method, params = {}) {
  seq += 1; const id = seq;
  return new Promise((res, rej) => {
    const timer = setTimeout(() => rej(new Error(`timeout ${method}`)), 60000);
    pending.set(id, (msg) => { clearTimeout(timer); msg.error ? rej(new Error(JSON.stringify(msg.error))) : res(msg.result); });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function js(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400));
  return r.result.value;
}
async function waitFor(expression, ms = 30000) {
  const end = Date.now() + ms;
  while (Date.now() < end) { if (await js(`Boolean(${expression})`)) return true; await sleep(150); }
  return false;
}
let viewport = [1440, 1000];
const requireWidth = widthGuard({ send, claim });
async function size(width, height) {
  viewport = [width, height];
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
  await requireWidth(width, height, `resize to ${width}x${height}`, { record: false });
}
async function go(url, ready) {
  await send("Page.navigate", { url });
  const ok = await waitFor(ready);
  await sleep(1200);
  await requireWidth(viewport[0], viewport[1], `loaded ${url}`);
  return ok;
}
async function shot(file) {
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  const h = Math.min(Math.ceil(tall), 9000);
  await send("Emulation.setDeviceMetricsOverride", { width: viewport[0], height: h, deviceScaleFactor: 1, mobile: viewport[0] < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, file), Buffer.from(r.data, "base64"));
  await size(viewport[0], viewport[1]);
}// ---- CAPTURE-ONLY cap measurement: closed height of named panels, then a labelled DOM-clone stress probe
// (5 rows where a table has fewer, every variable text leaf set to 160 chars). No clicks/posts/mutation of data.
const FN = String.raw`(spec) => {
  if (spec.mode === "text") { const t = document.body.innerText; return { has: t.includes(spec.needle), old: t.includes("is being refreshed") }; }
  if (spec.mode === "refusal") {
    const a = document.querySelector("main [role=alert]"); const z = document.querySelector("main [data-ev-depth-refusal-actions]") || document.querySelector("main [role=alert]");
    if (!a) return { error: "no alert" };
    const tiles = document.querySelector("main [class*=metric]"); const top = Math.min(a.getBoundingClientRect().top, tiles ? tiles.getBoundingClientRect().top : 1e9), bottom = z.getBoundingClientRect().bottom;
    const de = document.documentElement;
    return { closed: { h: Math.round(bottom - top), docOverflowX: de.scrollWidth - de.clientWidth, scrollers: [] } };
  }
  const root = document.querySelector("main");
  const txt = (e) => (e.textContent || "").replace(/\s+/g, " ").trim();
  const panels = [...root.querySelectorAll("section.panel")].filter((p) => !p.parentElement.closest("section.panel"));
  const panel = panels.find((p) => txt(p.querySelector("h2") || p).startsWith(spec.title));
  if (!panel) return { error: "no panel", titles: panels.map((p) => txt(p.querySelector("h2") || p)) };
  const de = document.documentElement;
  const m = () => ({ h: Math.round(panel.getBoundingClientRect().height), scrollH: panel.scrollHeight, clientH: panel.clientHeight,
    docOverflowX: de.scrollWidth - de.clientWidth,
    scrollers: [...panel.querySelectorAll("*")].filter((e) => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== "visible")
      .map((e) => ({ cls: String(e.className).slice(0, 40), client: e.clientWidth, scroll: e.scrollWidth })).slice(0, 4),
    clippedY: [...panel.querySelectorAll("*")].filter((e) => getComputedStyle(e).overflowY !== "visible" && e.scrollHeight > e.clientHeight + 1 && e.clientHeight > 0).length });
  const closed = m();
  if (spec.mode === "dump") return { closed, leaves: [...panel.querySelectorAll("*")].filter((e) => e.children.length === 0 && txt(e).length > 0).map((e) => e.tagName.toLowerCase() + (e.closest("th,td") ? "@" + e.closest("th,td").tagName.toLowerCase() : "") + ":" + txt(e).slice(0, 38)) };
  if (spec.mode !== "stress") return { closed };
  const probe = ("Probe text for cap measurement with a long unbroken run alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon").slice(0, 160);
  let rowsBefore = 0, rowsAfter = 0;
  if (spec.cloneSel) {
    const rows = [...panel.querySelectorAll(spec.cloneSel)]; rowsBefore = rows.length;
    for (let i = rows.length; rows.length && i < 5; i += 1) rows[rows.length - 1].parentElement.appendChild(rows[rows.length - 1].cloneNode(true));
    rowsAfter = panel.querySelectorAll(spec.cloneSel).length;
  }
  const nodeLeaves = [];
  if (spec.labelNode) for (const e of panel.querySelectorAll(spec.labelNode)) { const t = [...e.childNodes].find((n) => n.nodeType === 3 && n.data.trim()); if (t) { t.data = probe; nodeLeaves.push(e); } }
  const leaves = [...(spec.varSel ? panel.querySelectorAll(spec.varSel) : [])].filter((e) => e.children.length === 0 && txt(e).length > 0);
  if (spec.varRegex) {
    const re = new RegExp(spec.varRegex, "g");
    for (const e of panel.querySelectorAll("*")) { if (e.children.length === 0 && re.test(e.textContent)) { re.lastIndex = 0; e.textContent = e.textContent.replace(re, probe); leaves.push(e); } }
  } else { leaves.forEach((e) => { e.textContent = probe; }); }
  const changed = leaves.length + nodeLeaves.length;
  const ok = changed > 0 && leaves.every((e) => e.textContent.includes(probe)) && nodeLeaves.every((e) => e.textContent.includes(probe));
  return { closed, stress: m(), rowsBefore, rowsAfter, fieldsChanged: changed, allSet160: ok };
}`;
const SPECS = JSON.parse(readFileSync(process.argv[3], "utf8"));
const out = [];
try {
  ws = await connect();
  ws.addEventListener("message", (event) => { const msg = JSON.parse(event.data); if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); } });
  await send("Page.enable"); await send("Runtime.enable");
  for (const s of SPECS) {
    for (const [label, width, height] of WIDTHS) {
      await size(width, height);
      const ready = await go(s.url, String.raw`document.querySelector("main h2") && ![...document.querySelectorAll("main p")].some((p) => /^Loading [^.]+\.$/.test((p.textContent ?? "").trim()))`);
      const r = await js(`(${FN})(${JSON.stringify(s)})`);
      out.push({ page: s.page, title: s.title, mode: s.mode, viewport: label, ready, ...r });
      console.log(JSON.stringify(out[out.length - 1]));
    }
  }
} catch (e) { console.log("ERR " + e); }
finally { writeFileSync(join(OUT, "caps.json"), JSON.stringify(out, null, 2)); ws?.close(); chrome.kill(); }
