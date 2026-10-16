/**
 * S6-03 browser evidence for Site > Work > Actions, at 1440 and 390 px, against the v6.9 mockup's Site Work screen.
 *
 *   node tools/s603-site-work-evidence.mjs <web-base> <api-base> <out-dir> <walkthrough.json>
 *
 * <web-base> is the frontend served over `tools/s603_site_work_walkthrough.py serve` (e.g. http://127.0.0.1:5463),
 * <api-base> that API (e.g. http://127.0.0.1:8963), <walkthrough.json> the file `prepare` wrote. Per width: the
 * positive window (rows, exact Finding-version and step links, ids), its reload, the assessed-zero window, the
 * choose-window state, one-per-page paging, the exact step link opening Action history at that step, and the
 * mockup `index.html#/sitework`. Once (desktop): a review note is recorded through the API after page one was
 * issued, so the page-two address must refuse with "This list changed" and restart at page one.
 *
 * Every claim prints PASS/FAIL with its measured value; each page checks no page-level horizontal overflow, and the
 * rows claim requires a non-empty measured row set. Writes <out>/s603-claims.json and screenshots.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2];
const API = process.argv[3];
const OUT = process.argv[4] ?? join(tmpdir(), "s603-evidence");
const MANIFEST = process.argv[5];
if (!BASE || !API || !MANIFEST) throw new Error("usage: see the header of tools/s603-site-work-evidence.mjs");
const manifest = JSON.parse(readFileSync(MANIFEST, "utf-8"));
const SITE = manifest.site;
const MOCK = new URL("../frontend/mockups/v69/index.html", import.meta.url).href;
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9463);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), "assetops-s603-cdp-"));
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
async function size(width, height) {
  viewport = [width, height];
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
}
async function go(url, ready) {
  await send("Page.navigate", { url });
  const ok = await waitFor(ready);
  await sleep(400);
  return ok;
}
async function shot(name) {
  const tall = await js("document.documentElement.scrollHeight");
  const [w, h] = viewport;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: Math.min(Math.ceil(tall), 7000), deviceScaleFactor: 1, mobile: w < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  const file = join(OUT, `${name}.png`);
  writeFileSync(file, Buffer.from(r.data, "base64"));
  await size(w, h);
  await sleep(150);
  console.log(`      screenshot ${file}`);
}


const READY = `document.querySelector('[data-site-work-state]') && !document.querySelector('[data-site-work-state="loading"]') && !document.body.innerText.match(/Loading the configured site/)`;
const READ = `(() => {
  const rows = [...document.querySelectorAll('[data-site-work-row]')];
  const text = document.body.innerText;
  return {
    href: location.pathname + location.search,
    state: document.querySelector('[data-site-work-state]')?.getAttribute('data-site-work-state') ?? null,
    heading: document.querySelector('#site-work-actions-heading')?.textContent ?? null,
    scope: document.querySelector('[data-site-work-scope]')?.textContent ?? null,
    rows: rows.map((r) => ({ id: r.getAttribute('data-site-work-row'), event: r.getAttribute('data-site-work-event'),
      revision: r.getAttribute('data-site-work-revision'), text: r.innerText.replace(/\s+/g, ' ').trim(),
      action: r.querySelector('[data-site-work-action-link]')?.getAttribute('href'),
      finding: r.querySelector('[data-site-work-finding-link]')?.getAttribute('href'),
      step: r.querySelector('[data-site-work-event-link]')?.getAttribute('href') })),
    next: document.querySelector('[data-site-work-next]')?.getAttribute('href') ?? null,
    fence: document.querySelector('[data-site-work-fence]')?.textContent ?? null,
    counts: document.querySelector('[data-site-work-fence-counts]')?.textContent ?? null,
    workTab: document.querySelector('a[aria-current="page"].site-tabs__link')?.textContent ?? null,
    zeroClaim: /No Actions created at this site/.test(text),
    countClaim: /Showing \d+ of \d+/.test(text),
    verdict: /\bVerified\b|\bOwner\b|\bDue\b/.test(text),
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  };
})()`;

const work = (w, extra = {}) => `${BASE}/sites/${SITE}/work?${new URLSearchParams({ ...w, ...extra }).toString()}`;

async function list(W, name, url) {
  const ok = await go(url, READY);
  const s = await js(READ);
  claim(`${W} ${name}: settled`, ok, s.state);
  claim(`${W} ${name}: no page-level horizontal overflow`, s.overflow <= 0, s.overflow);
  await shot(`s603-${W}-${name}`);
  return s;
}

async function main() {
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
  const record = {};
  const want = manifest.actions.map((a) => a.id);
  let changedOnce = false;
  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    const p = await list(W, "positive", work(manifest.positive));
    claim(`${W} positive: CURRENT rows newest-created first (non-empty, persisted IDs)`,
      p.state === "current-rows" && p.rows.length === 2 && JSON.stringify(p.rows.map((r) => r.id)) === JSON.stringify(want), p.rows.map((r) => r.id));
    claim(`${W} positive: Work is the current Site tab`, p.workTab === "Work", p.workTab);
    claim(`${W} positive: each row links its Action, exact Finding version and exact step`,
      p.rows.length > 0 && p.rows.every((r, i) => r.action === `/sites/${SITE}/actions/${r.id}`
        && r.finding === `/sites/${SITE}/findings/${manifest.actions[i].finding}?revision_id=${manifest.actions[i].finding_revision}`
        && r.revision === manifest.actions[i].finding_revision
        && r.step === `/sites/${SITE}/actions/${r.id}/history?event_id=${r.event}`), p.rows);
    claim(`${W} positive: no owner, due date or verdict wording`, !p.verdict, p.verdict);
    const again = await list(W, "positive-reload", work(manifest.positive));
    claim(`${W} reload: same rows, step IDs and fence`, JSON.stringify(again.rows) === JSON.stringify(p.rows) && again.fence === p.fence, again.fence);
    const z = await list(W, "zero", work(manifest.zero));
    claim(`${W} zero: explicit zero, no rows`, z.state === "current-empty" && z.rows.length === 0 && z.zeroClaim && /0 Actions, 0 recorded steps/.test(z.counts ?? ""), z.counts);
    const c = await list(W, "choose-window", `${BASE}/sites/${SITE}/work`);
    claim(`${W} no window: choose-window state, no rows, no zero claim`, c.state === "choose-window" && c.rows.length === 0 && !c.zeroClaim, c.state);
    const p1 = await list(W, "page-1", work(manifest.positive, { limit: "1" }));
    claim(`${W} page 1: one row and a Next page link`, p1.rows.length === 1 && Boolean(p1.next), p1.next);
    const p2 = await list(W, "page-2", `${BASE}${p1.next}`);
    claim(`${W} page 2 (from the address): the other row`, p2.rows.length === 1 && p2.rows[0].id === want[1], p2.rows.map((r) => r.id));
    const stepOk = await go(`${BASE}${p.rows[0].step}`, `document.querySelector('[data-action-cutoff-event]')`);
    const cutoff = await js(`document.querySelector('[data-action-cutoff-event]')?.getAttribute('data-action-cutoff-event')`);
    claim(`${W} step link opens Action history at exactly that step`, stepOk && cutoff === p.rows[0].event, { cutoff, want: p.rows[0].event });
    await shot(`s603-${W}-step-history`);
    if (!changedOnce) {
      // Record a review note after page one was issued: the page-two address must now refuse.
      const target = manifest.actions[1].id;
      const res = await fetch(`${API}/api/sites/${SITE}/actions/${target}/observations`, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ observation_code: "DEMO_REVIEW_NOTE", occurred_at: new Date(Date.now() - 60000).toISOString(),
          idempotency_key: `s603-evidence-${Date.now()}` }) });
      claim("review note recorded through the Action API", res.status === 201, res.status);
      changedOnce = true;
    }
    const changed = await list(W, "page-2-changed", `${BASE}${p1.next}`);
    claim(`${W} changed list: page 2 refuses with no rows or count`, changed.state === "basis-changed" && changed.rows.length === 0 && !changed.countClaim && !changed.zeroClaim, changed.state);
    await js(`document.querySelector('[data-site-work-restart]').click()`);
    await waitFor(`${READY} && document.querySelector('[data-site-work-state="current-rows"]')`);
    const restarted = await js(READ);
    claim(`${W} restart: page 1 reloads on the new fence`, restarted.state === "current-rows" && restarted.rows.length === 1 && restarted.fence !== p1.fence, restarted.fence);
    await shot(`s603-${W}-restarted`);
    const mockOk = await go(`${MOCK}#/sitework`, `document.body.innerText.match(/Actions at this site/)`);
    const mockOverflow = await js("document.documentElement.scrollWidth - window.innerWidth");
    claim(`${W} mockup #/sitework rendered for comparison`, mockOk, { overflow: mockOverflow });
    await shot(`s603-${W}-mockup-sitework`);
    record[W] = { p, z, c, p1, p2, changed: changed.state, restarted: restarted.fence };
  }
  writeFileSync(join(OUT, "s603-claims.json"), JSON.stringify({ results, record }, null, 2));
  const failed = results.filter((r) => !r.ok).length;
  console.log(`${results.length - failed}/${results.length} claims passed`);
  return failed;
}

let code = 1;
try {
  code = (await main()) === 0 ? 0 : 1;
} catch (error) {
  console.error(error);
} finally {
  ws?.close();
  chrome.kill();
  await sleep(500);
  try {
    rmSync(profile, { recursive: true, force: true });
  } catch {
    /* Chrome may still hold the profile */
  }
}
process.exit(code);
