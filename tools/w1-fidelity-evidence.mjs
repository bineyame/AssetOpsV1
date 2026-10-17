/**
 * W1 fidelity (D-2026-10-17-mockup-layout-spec): app and v6.9 mock captured side by side at 1440
 * and 390 for each named screen, from the installed Chrome over the DevTools Protocol (the
 * tools/w1-ux-01-evidence.mjs pattern; no dependency). Shared by W1-F1..F5.
 *
 *   node tools/w1-fidelity-evidence.mjs <out-dir> <mock-id>[:<case>]=<app-url> [...]
 *   e.g. node tools/w1-fidelity-evidence.mjs %TEMP%\w1f1 foundation=http://localhost:5460/sites/KOBO-001/foundation
 *
 * The mock is read from the same origin: <origin>/mockups/v69/index.html#/<mock-id>.
 * For each target and width it saves `<id>[-<case>]-<width>-app.png` and `-mock.png`, measures both
 * pages' main-content panel titles (the panelStructure.ts rule: visible h2 in <main>, plus untitled
 * panel cards) and horizontal overflow, and writes `evidence.json` and an `index.html` that shows
 * every pair side by side. The structure test is the exact title guard; this tool records what a
 * reviewer compares: panel sequence, grid, prominence and mobile flow.
 * Environment: ASSETOPS_CDP_PORT (default 9473), W1_REVISION (recorded in evidence.json).
 *
 * Every claim is measured and printed; the run exits non-zero if any fails.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const OUT = process.argv[2];
const TARGETS = process.argv.slice(3).map((arg) => {
  const at = arg.indexOf("=");
  const [id, tag] = arg.slice(0, at).split(":");
  return { id, tag: tag ?? null, url: arg.slice(at + 1) };
});
if (!OUT || TARGETS.length === 0) {
  console.error("usage: node tools/w1-fidelity-evidence.mjs <out-dir> <mock-id>[:<case>]=<app-url> ...");
  process.exit(2);
}
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9473);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["1440", 1440, 1000],
  ["390", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-w1fidelity-cdp-"));
const chrome = spawn(
  CHROME,
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"],
  { stdio: "ignore" },
);
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
        await new Promise((res, rej) => {
          socket.addEventListener("open", res);
          socket.addEventListener("error", rej);
        });
        return socket;
      }
    } catch {
      /* not up yet */
    }
    await sleep(250);
  }
  throw new Error("Chrome did not expose a page target");
}

let ws;
let seq = 0;
const pending = new Map();
function send(method, params = {}) {
  seq += 1;
  const id = seq;
  return new Promise((res, rej) => {
    const timer = setTimeout(() => rej(new Error(`timeout ${method}`)), 60000);
    pending.set(id, (msg) => {
      clearTimeout(timer);
      msg.error ? rej(new Error(JSON.stringify(msg.error))) : res(msg.result);
    });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function js(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  return r.result.value;
}
async function waitFor(expression, ms = 30000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    if (await js(`Boolean(${expression})`)) return true;
    await sleep(150);
  }
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
  await sleep(700);
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
  await requireWidth(viewport[0], null, `capture ${file}`, { record: false });
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, file), Buffer.from(r.data, "base64"));
  await size(viewport[0], viewport[1]);
}

/** The panelStructure.ts rule, in the page: visible h2 in main plus untitled panel cards, in order. */
const PANELS = `(() => {
  const root = document.querySelector("main") ?? document.body;
  const hidden = (el) => {
    for (let n = el; n && n !== root; n = n.parentElement) {
      if (n.hidden || n.getAttribute("aria-hidden") === "true") return true;
      const p = n.parentElement;
      if (p && p.tagName === "DETAILS" && !p.open && n.tagName !== "SUMMARY") return true;
    }
    return false;
  };
  const sel = "section.panel, .panel, [data-headline-card]";
  const titles = []; const seen = new Set();
  for (const el of root.querySelectorAll("h2, " + sel)) {
    if (hidden(el)) continue;
    if (el.tagName === "H2") { const o = el.closest(sel); if (o) seen.add(o); titles.push(el.textContent.replace(/\\s+/g, " ").trim()); continue; }
    const own = [...el.querySelectorAll("h2")].find((h) => h.closest(sel) === el);
    if (!own && !seen.has(el)) titles.push("(untitled)");
  }
  const panels = [...root.querySelectorAll("section.panel")].filter((p) => !hidden(p) && !p.parentElement.closest("section.panel"))
    .map((p) => { const r = p.getBoundingClientRect(); return { title: (p.querySelector("h2")?.textContent ?? "").trim(), x: Math.round(r.x), y: Math.round(r.y + scrollY), w: Math.round(r.width), h: Math.round(r.height) }; });
  return { titles, panels, overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth };
})()`;

const evidence = { revision: process.env.W1_REVISION ?? null, captured_at: new Date().toISOString(), pairs: [] };
try {
  ws = await connect();
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  for (const target of TARGETS) {
    const name = target.tag ? `${target.id}-${target.tag}` : target.id;
    const mockUrl = `${new URL(target.url).origin}/mockups/v69/index.html#/${target.id}`;
    for (const [label, width, height] of WIDTHS) {
      await size(width, height);
      const appReady = await go(target.url, `document.querySelector("main h2, main [data-page-refusal]") && !document.body.textContent.includes("Loading")`);
      claim(`${name} ${label}: app rendered its main content`, appReady);
      const app = await js(PANELS);
      await shot(`${name}-${label}-app.png`);
      const mockReady = await go(mockUrl, `document.querySelector("main section.panel h2")`);
      claim(`${name} ${label}: mock rendered its panels`, mockReady);
      const mock = await js(PANELS);
      await shot(`${name}-${label}-mock.png`);
      claim(`${name} ${label}: app and mock render the same number of panels`, app.titles.length === mock.titles.length, {
        app: app.titles,
        mock: mock.titles,
      });
      claim(`${name} ${label}: app has no horizontal page overflow`, app.overflowX <= 0, { overflowX: app.overflowX });
      evidence.pairs.push({
        screen: target.id,
        case: target.tag,
        viewport: `${width}x${height}`,
        app_url: target.url,
        mock_hash: `#/${target.id}`,
        app_image: `${name}-${label}-app.png`,
        mock_image: `${name}-${label}-mock.png`,
        app,
        mock,
      });
    }
  }
} catch (error) {
  claim("evidence run completed", false, String(error));
} finally {
  writeFileSync(join(OUT, "evidence.json"), JSON.stringify(evidence, null, 2));
  const rows = evidence.pairs
    .map(
      (p) => `<section><h2>${p.screen}${p.case ? ` (${p.case})` : ""} · ${p.viewport}</h2>
<p>App: ${p.app.titles.join(" | ")}<br>Mock: ${p.mock.titles.join(" | ")}</p>
<div class="pair"><figure><figcaption>App ${p.app_url}</figcaption><img src="${p.app_image}"></figure>
<figure><figcaption>Mock ${p.mock_hash}</figcaption><img src="${p.mock_image}"></figure></div></section>`,
    )
    .join("\n");
  writeFileSync(
    join(OUT, "index.html"),
    `<!doctype html><meta charset="utf-8"><title>W1 fidelity pairs</title><style>body{font:13px system-ui;margin:16px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}img{width:100%;border:1px solid #ccc}figure{margin:0}</style>
<p>Revision ${evidence.revision ?? "not recorded"} · captured ${evidence.captured_at}</p>${rows}`,
  );
  ws?.close();
  chrome.kill();
}
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} claims passed; evidence in ${OUT}`);
process.exit(failed.length === 0 ? 0 : 1);
