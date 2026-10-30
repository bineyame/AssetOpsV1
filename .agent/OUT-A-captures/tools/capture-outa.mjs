/**
 * OUT-A A6 capture (CAPTURE-ONLY; derived from .agent/post-W6-W2-cold-recapture/tools/capture-cold.mjs, same
 * Chrome-over-CDP pattern and tools/evidence-checks.mjs width guard). Navigates, waits, screenshots full page and
 * measures the DOM. Never clicks, types or posts.
 *
 *   node capture-outa.mjs <out-dir> <targets.json>
 * targets.json: [{ "name": "...", "url": "<app url>", "mock": "<v70 hash id>", "mockDir": "v70", "producer": "...", "db": "..." }]
 * Env: ASSETOPS_CDP_PORT (default 9611), PRODUCT_SHA.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const { widthGuard } = await import(pathToFileURL(resolve(here, "../../../tools/evidence-checks.mjs")).href);
const OUT = process.argv[2];
const TARGETS = JSON.parse(readFileSync(process.argv[3], "utf8"));
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9611);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [["1440", 1440, 1000], ["390", 390, 900]];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-outa-cdp-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
console.log(`chrome pid ${chrome.pid}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
function claim(name, ok, detail) {
  results.push({ name, ok, detail });
  if (!ok) console.log(`FAIL  ${name}${detail === undefined ? "" : `  ${JSON.stringify(detail).slice(0, 300)}`}`);
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
  await sleep(1500);
  await requireWidth(viewport[0], viewport[1], `loaded ${url}`);
  return ok;
}
async function shot(file) {
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  const h = Math.min(Math.ceil(tall), 12000);
  await send("Emulation.setDeviceMetricsOverride", { width: viewport[0], height: h, deviceScaleFactor: 1, mobile: viewport[0] < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, file), Buffer.from(r.data, "base64"));
  await size(viewport[0], viewport[1]);
}
const MEASURE = String.raw`(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); if (r.width === 0 && r.height === 0) return false;
    for (let n = e; n; n = n.parentElement) { const s = getComputedStyle(n); if (s.display === "none" || s.visibility === "hidden") return false;
      const p = n.parentElement; if (p && p.tagName === "DETAILS" && !p.open && n.tagName !== "SUMMARY") return false; } return true; };
  const txt = (e) => (e?.textContent ?? "").replace(/\s+/g, " ").trim();
  const label = (e) => { const c = e.cloneNode(true); c.querySelectorAll(".visually-hidden").forEach((v) => v.remove()); return txt(c); };
  const de = document.documentElement;
  const rowOf = (w) => w.closest("tr, li, [role='row'], article, .finding-row, a") ?? w.parentElement;
  const tagRows = [...document.querySelectorAll("[data-outcome-tags], .oc-affectwrap")].filter(vis).map((w) => {
    const row = rowOf(w);
    const pills = [...w.querySelectorAll(".oc-affects")].map((p) => ({ text: label(p), solid: !p.classList.contains("quiet"), role: p.getAttribute("data-outcome-role") }));
    return { row: txt(row).slice(0, 140), rowTag: row?.tagName, pills };
  });
  const lines = [...document.querySelectorAll(".oc-affectsline")].filter(vis).map((l) => ({ text: txt(l).slice(0, 300),
    pills: [...l.querySelectorAll(".oc-pill")].map((p) => ({ text: txt(p), solid: !p.classList.contains("quiet") })) }));
  const cards = [...document.querySelectorAll("[data-portfolio-card]")].filter(vis).map((c) => ({ key: c.getAttribute("data-portfolio-card"),
    name: txt(c.querySelector("[data-portfolio-card-name]")), definition: txt(c.querySelector("[data-portfolio-card-definition]")),
    value: txt(c.querySelector("[data-portfolio-card-value]")), detail: txt(c.querySelector("[data-portfolio-card-detail]")),
    basis: txt(c.querySelector("[data-portfolio-card-basis]")), icon: !!c.querySelector("svg, .oc-icon, [class*='icon']"), href: c.getAttribute("href") }));
  const mockCards = [...document.querySelectorAll(".oc-pfcard")].filter(vis).map((c) => txt(c).slice(0, 200));
  const h1 = [...document.querySelectorAll("h1")].find(vis);
  return { scrollWidth: de.scrollWidth, clientWidth: de.clientWidth, overflowX: de.scrollWidth > de.clientWidth,
    innerWidth, pageH: de.scrollHeight, h1: txt(h1).slice(0, 120), location: location.pathname + location.search + location.hash,
    tagRows, affectsLines: lines, safeguards: lines.filter((l) => l.text.includes("Safeguards checked")).map((l) => l.text),
    cards, mockCards, mainTextLen: (document.querySelector("main") ?? document.body).innerText.length };
})()`;
const evidence = { product_sha: process.env.PRODUCT_SHA ?? null, captured_at: new Date().toISOString(), captures: [] };
const READY = String.raw`document.querySelector("main h1, main h2, main [data-page-refusal]") && ![...document.querySelectorAll("main p, main div")].some((p) => /^Loading\b/.test(p.textContent.trim()) && p.children.length === 0)`;
try {
  ws = await connect();
  ws.addEventListener("message", (event) => { const msg = JSON.parse(event.data);
    if (msg.method === "Runtime.exceptionThrown") consoleErrors.push(String(msg.params.exceptionDetails?.exception?.description ?? msg.params.exceptionDetails?.text).slice(0, 300));
    if (msg.method === "Runtime.consoleAPICalled" && msg.params.type === "error") consoleErrors.push(msg.params.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 300));
    if (msg.method === "Log.entryAdded" && msg.params.entry.level === "error") consoleErrors.push(`[log] ${msg.params.entry.text} ${msg.params.entry.url ?? ""}`.slice(0, 300));
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); } });
  await send("Page.enable"); await send("Runtime.enable"); await send("Log.enable");
  for (const t of TARGETS) {
    const mockDir = t.mockDir ?? "v70";
    const mockUrl = t.mock ? `${new URL(t.url).origin}/mockups/${mockDir}/index.html#/${t.mock}` : null;
    for (const [label, width, height] of WIDTHS) {
      await size(width, height);
      consoleErrors = [];
      const ready = await go(t.url, t.ready ?? READY);
      claim(`${t.name} ${label}: app rendered`, ready);
      const app = await js(MEASURE);
      app.consoleErrors = [...new Set(consoleErrors)];
      await shot(`${t.name}-${label}-app.png`);
      let mock = null;
      if (mockUrl) {
        consoleErrors = [];
        const mready = await go(mockUrl, `document.querySelector("main section, main h1, main h2")`);
        claim(`${t.name} ${label}: mock rendered`, mready);
        mock = await js(MEASURE);
        await shot(`${t.name}-${label}-mock-${mockDir}-${t.mock}.png`);
      }
      claim(`${t.name} ${label}: no app page overflow`, !app.overflowX, { sw: app.scrollWidth, cw: app.clientWidth });
      evidence.captures.push({ name: t.name, width, height, url: t.url, producer: t.producer, db: t.db, ready,
        app_image: `${t.name}-${label}-app.png`, mock_url: mockUrl, mock_image: mockUrl ? `${t.name}-${label}-mock-${mockDir}-${t.mock}.png` : null,
        app, mock: mock ? { tagRows: mock.tagRows, affectsLines: mock.affectsLines, mockCards: mock.mockCards, h1: mock.h1, scrollWidth: mock.scrollWidth, clientWidth: mock.clientWidth } : null });
    }
  }
} catch (error) {
  claim("capture run completed", false, String(error));
} finally {
  const file = join(OUT, "raw-evidence.json");
  const prior = existsSync(file) ? JSON.parse(readFileSync(file, "utf8")) : { runs: [] };
  prior.runs.push({ targets: process.argv[3], ...evidence, failed_claims: results.filter((r) => !r.ok) });
  writeFileSync(file, JSON.stringify(prior, null, 2));
  ws?.close(); chrome.kill();
}
const failed = results.filter((r) => !r.ok);
console.log(`${results.length - failed.length}/${results.length} claims passed; captures ${evidence.captures.length}`);
