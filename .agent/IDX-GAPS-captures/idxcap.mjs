import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { widthGuard } from "file:///C:/Users/assef/Bineyame/AssetOpsV1-idxgaps/tools/evidence-checks.mjs";
const BASE = process.argv[2];
const OUT = process.argv[3];
const PORT = 9441;
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const WIDTHS = [["desktop", 1440, 1000], ["narrow", 390, 900]];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-idxgaps-cdp-"));
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
        const sock = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => {
          sock.addEventListener("open", res);
          sock.addEventListener("error", rej);
        });
        return sock;
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
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`timeout ${method}`)), 60000);
    pending.set(id, (msg) => {
      clearTimeout(timer);
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
    });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function js(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(`page eval: ${JSON.stringify(r.exceptionDetails).slice(0, 400)}`);
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
  await sleep(400);
  await requireWidth(viewport[0], viewport[1], `loaded ${url}`);
  return ok;
}
async function shot(name) {
  const tall = await js("document.documentElement.scrollHeight");
  const [w, h] = viewport;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: Math.min(Math.ceil(tall), 7000), deviceScaleFactor: 1, mobile: w < 600 });
  await sleep(300);
  await requireWidth(viewport[0], null, `capture ${name}`, { record: false });
  const r = await send("Page.captureScreenshot", { format: "png" });
  const file = join(OUT, `${name}.png`);
  writeFileSync(file, Buffer.from(r.data, "base64"));
  await size(w, h);
  await sleep(150);
  console.log(`      screenshot ${file}`);
}

const INDEX_READY = `document.querySelector('[data-finding-index-state]') && !document.body.innerText.match(/Loading the site's findings/)`;
const FINDING_READY = `document.querySelector('[data-finding-revision]') || (document.querySelector('main') && !document.body.innerText.match(/Loading the Finding/) && document.querySelector('h2'))`;
const READ = `(() => {
  const rows = [...document.querySelectorAll('[data-finding-index-row]')];
  const text = document.body.innerText;
  return {
    href: location.pathname + location.search,
    state: document.querySelector('[data-finding-index-state]')?.getAttribute('data-finding-index-state') ?? null,
    heading: document.querySelector('#site-finding-index-heading')?.textContent ?? null,
    rows: rows.map((r) => [r.getAttribute('data-finding-index-row'), r.getAttribute('data-finding-revision')]),
    links: [...document.querySelectorAll('[data-finding-index-link]')].map((a) => a.getAttribute('href')),
    amounts: [...document.querySelectorAll('[data-finding-index-amount]')].map((c) => c.textContent),
    next: document.querySelector('[data-finding-index-next]')?.getAttribute('href') ?? null,
    token: document.querySelector('[data-finding-index-token]')?.textContent ?? null,
    emptyClaim: /No Findings in this window/.test(text),
    countClaim: /\\d+ Findings? in this window/.test(text),
    notVerdict: /not a statement that the window has no Findings/.test(text),
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  };
})()`;
const PAGE = `${BASE}/sites/KOBO-001/findings?from=2026-10-15T00%3A00%3A00Z&to=2026-10-31T00%3A00%3A00Z&domain=mini-grid-dispatch`;
const BOARD = `${BASE}/sites/KOBO-001?date=2026-10-15`;
async function main() {
  ws = await connect();
  ws.addEventListener("message", (e) => {
    const msg = JSON.parse(e.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  for (const [W, w, h] of WIDTHS) {
    await size(w, h);
    const ok = await go(PAGE, `document.querySelector('[data-site-findings="partial"]')`);
    const m = await js(`(() => { const v = document.querySelector('[data-site-findings="partial"]'); const t = document.body.innerText;
      return { present: !!v, claim: document.querySelector('[data-site-findings-claim]')?.textContent ?? null,
        rows: document.querySelectorAll('[data-finding-index-row]').length,
        gap: document.querySelector('[data-site-findings-gap-days]')?.textContent ?? null,
        provedEmpty: /No Findings in this window/.test(t), codes: /PARTIAL|UNASSESSED|STALE_PROJECTION/.test(t.split('Recorded list state')[0]),
        overflow: document.documentElement.scrollWidth - window.innerWidth }; })()`);
    claim(`${W} Findings page PARTIAL view`, ok && m.present && m.rows > 0 && !!m.gap && !m.provedEmpty && m.overflow <= 0, m);
    await shot(`idxgaps-findings-partial-${w}`);
    const okb = await go(BOARD, `document.querySelector('[data-outcome-finding-gaps]')`);
    const b = await js(`(() => { const p = document.querySelector('[data-outcome-finding-gaps]');
      const lh = p ? parseFloat(getComputedStyle(p).lineHeight) : null; const r = p?.getBoundingClientRect();
      return { text: p?.textContent ?? null, lines: p && lh ? Math.round(r.height / lh) : null, height: r?.height ?? null, lineHeight: lh,
        overflow: document.documentElement.scrollWidth - window.innerWidth }; })()`);
    const maxLines = w >= 1440 ? 1 : 2;
    claim(`${W} board gap line`, okb && !!b.text && b.lines !== null && b.lines <= maxLines && b.overflow <= 0, b);
    if (okb) await js(`document.querySelector('[data-outcome-finding-gaps]').scrollIntoView({block:'center'})`);
    await shot(`idxgaps-board-line-${w}`);
  }
  writeFileSync(join(OUT, "idxgaps-claims.json"), JSON.stringify(results, null, 2));
  const failed = results.filter((r) => !r.ok).length;
  console.log(`${results.length - failed} passed, ${failed} failed`);
  ws.close(); chrome.kill(); rmSync(profile, { recursive: true, force: true });
  process.exit(failed ? 1 : 0);
}
main().catch((e) => { console.error(e); chrome.kill(); process.exit(2); });
